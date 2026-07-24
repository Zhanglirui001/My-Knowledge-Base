from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import threading
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import change_manager, semantic_store
from .config import settings
from .markdown_service import render_notebook, render_text_file
from .task_manager import tasks


ROOT = settings.root
SCRIPTS = ROOT / "scripts"
WEB_DIR = ROOT / "web"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import kb  # noqa: E402
import kb_agent  # noqa: E402


app = FastAPI(
    title="My Knowledge Base",
    version="0.2.0",
    docs_url="/api/docs",
    redoc_url=None,
)
WRITE_LOCK = threading.Lock()
ACTION_LOG = kb_agent.AGENT_DIR / "Web操作日志.jsonl"
VISIBLE_ROOTS = (
    kb.INBOX,
    kb.PROJECTS,
    ROOT / "20_Areas",
    kb.RESOURCES,
    kb.NOTES,
    kb.MOCS,
    ROOT / "60_Outputs",
    ROOT / "90_Archive",
    kb.SYSTEM,
)
UPLOAD_ROOTS = (
    kb.INBOX,
    kb.PROJECTS,
    ROOT / "20_Areas",
    kb.RESOURCES,
    kb.NOTES,
    kb.MOCS,
    ROOT / "60_Outputs",
    ROOT / "_assets",
)
PREVIEW_EXTENSIONS = {
    ".md", ".txt", ".py", ".js", ".ts", ".tsx", ".jsx", ".json",
    ".yaml", ".yml", ".css", ".html", ".xml", ".drawio", ".csv",
    ".ipynb",
}
# 可通过 /api/raw 直接在浏览器内嵌查看的二进制类型
EMBED_EXTENSIONS = {".pdf"}
# 支持整文件在线编辑的文本类型（.ipynb 走按单元编辑的专用端点）
TEXT_EDITABLE_EXTENSIONS = PREVIEW_EXTENSIONS - {".ipynb"}
UPLOAD_EXTENSIONS = PREVIEW_EXTENSIONS | {
    ".pdf", ".epub", ".mobi", ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ".webp", ".docx", ".pptx", ".xlsx", ".java", ".go", ".rs", ".cpp",
    ".c", ".h", ".hpp", ".sql", ".sh", ".ps1", ".ipynb",
}


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=300)
    limit: int = Field(default=12, ge=1, le=50)
    mode: Literal["hybrid", "keyword", "semantic"] = "hybrid"


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    limit: int = Field(default=8, ge=1, le=20)


class OutlinePreviewRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=160)
    kind: Literal["roadmap", "report", "article"] = "roadmap"
    limit: int = Field(default=8, ge=1, le=20)


class ConfirmRequest(BaseModel):
    confirmed: bool = False


class SaveFileRequest(BaseModel):
    path: str = Field(min_length=1)
    content: str
    confirmed: bool = False
    expected_mtime: str | None = None
    rebuild_indexes: bool = True


class NotebookCellUpdate(BaseModel):
    index: int = Field(ge=0)
    source: str


class SaveNotebookRequest(BaseModel):
    path: str = Field(min_length=1)
    cells: list[NotebookCellUpdate]
    confirmed: bool = False
    expected_mtime: str | None = None
    rebuild_indexes: bool = True


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def safe_path(value: str) -> Path:
    candidate = (ROOT / value).resolve()
    try:
        candidate.relative_to(ROOT)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="路径不在知识库范围内") from exc
    return candidate


def upload_directory(value: str) -> Path:
    candidate = safe_path(value)
    if not candidate.is_dir():
        raise HTTPException(status_code=400, detail="目标目录不存在")
    if not any(candidate == root or candidate.is_relative_to(root) for root in UPLOAD_ROOTS):
        raise HTTPException(status_code=403, detail="该目录不允许上传")
    return candidate


def require_confirmation(confirmed: bool) -> None:
    if not confirmed:
        raise HTTPException(status_code=409, detail="该操作会写入知识库，需要明确确认")


def log_action(action: str, detail: str, outputs: list[str] | None = None) -> None:
    kb_agent.AGENT_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "action": action,
        "detail": detail,
        "outputs": outputs or [],
    }
    with ACTION_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def file_item(path: Path) -> dict[str, object]:
    return {
        "name": path.name,
        "path": rel(path),
        "kind": "directory" if path.is_dir() else path.suffix.lower().lstrip(".") or "file",
        "size": path.stat().st_size if path.is_file() else None,
        "updated": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="minutes"),
    }


def tree_node(path: Path, depth: int = 0) -> dict[str, object]:
    node = file_item(path)
    if path.is_dir() and depth < 5:
        children = [
            child for child in path.iterdir()
            if not child.name.startswith(".") and child.name != "__pycache__"
        ]
        children.sort(key=lambda child: (not child.is_dir(), child.name.lower()))
        node["children"] = [tree_node(child, depth + 1) for child in children]
    return node


def directory_options() -> list[dict[str, str]]:
    root_labels = {
        "00_Inbox": "收件箱 · 待处理",
        "10_Projects": "项目",
        "20_Areas": "长期领域",
        "30_Resources": "资料库",
        "40_Notes": "原子笔记",
        "50_MOCs": "内容地图",
        "60_Outputs": "输出成果",
        "_assets": "附件资源",
    }
    child_labels = {
        "PDFs": "PDF 文档",
        "Books": "电子书",
        "Code": "代码资料",
        "Drawio": "Drawio 图表",
        "Text": "文本资料",
        "Documents": "Office 文档",
    }

    def label(path: Path) -> str:
        path_text = rel(path)
        parts = Path(path_text).parts
        names = [root_labels.get(parts[0], parts[0])]
        names.extend(child_labels.get(part, part) for part in parts[1:])
        return f"{' / '.join(names)}（{path_text}）"

    result: list[dict[str, str]] = []
    for root in UPLOAD_ROOTS:
        if not root.exists():
            continue
        directories = [root] + [
            path
            for path in root.rglob("*")
            if path.is_dir()
            and not path.name.startswith(".")
            and len(path.relative_to(root).parts) <= 3
        ]
        result.extend({"path": rel(path), "label": label(path)} for path in directories)
    return sorted(result, key=lambda item: item["path"].lower())


def inbox_target(path: Path) -> tuple[Path | None, bool]:
    suffix = path.suffix.lower()
    if suffix == ".md":
        return kb.NOTES, False
    if suffix in {".txt", ".csv", ".json", ".yaml", ".yml"}:
        return kb.RESOURCES / "Text", True
    if suffix in {".docx", ".pptx", ".xlsx"}:
        return kb.RESOURCES / "Documents", True
    return kb.target_for(path), True


def index_document_count() -> int:
    if not kb_agent.DB_PATH.exists():
        return 0
    try:
        with closing(sqlite3.connect(kb_agent.DB_PATH)) as connection:
            return int(connection.execute("SELECT count(*) FROM docs").fetchone()[0])
    except (sqlite3.Error, TypeError):
        return 0


def recent_files(limit: int = 8) -> list[dict[str, str]]:
    files = [
        path
        for path in kb.iter_markdown()
        if "90_System/Templates" not in path.as_posix()
    ]
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return [
        {
            "path": rel(path),
            "name": path.stem,
            "updated": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="minutes"),
        }
        for path in files[:limit]
    ]


def read_payload(target: Path) -> dict[str, str]:
    if not target.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    if target.suffix.lower() not in PREVIEW_EXTENSIONS:
        raise HTTPException(status_code=415, detail="该文件类型暂不支持在线预览")
    content = kb.read_text(target)
    suffix = target.suffix.lower()
    if suffix == ".ipynb":
        rendered, frontmatter = render_notebook(content)
        fmt = "notebook"
    else:
        rendered, frontmatter = render_text_file(target, content)
        fmt = "markdown" if suffix == ".md" else "code"
    return {
        "path": rel(target),
        "name": target.name,
        "content": content,
        "html": rendered,
        "frontmatter": frontmatter,
        "format": fmt,
        "mtime": str(target.stat().st_mtime_ns),
    }


def public_plan(plan: dict[str, Any]) -> dict[str, Any]:
    result = {key: value for key, value in plan.items() if key != "operations"}
    result["operations"] = [
        {key: value for key, value in operation.items() if key != "content"}
        for operation in plan.get("operations", [])
    ]
    return result


def outline_content(topic: str, kind: str, limit: int) -> str:
    rows = kb_agent.search_docs(topic, limit)
    kind_name = {"roadmap": "学习路线", "report": "报告大纲", "article": "文章大纲"}[kind]
    lines = [
        "---",
        f"type: {kind}",
        "status: draft",
        "tags:",
        "  - 自动化",
        f"  - {topic}",
        f"created: {kb.today()}",
        f"updated: {kb.today()}",
        "---",
        "",
        f"# {topic} {kind_name}",
        "",
        "## 目标",
        "",
        f"围绕 `{topic}` 形成可执行的学习、研究或输出路径。",
        "",
        "## 已有材料",
        "",
    ]
    if rows:
        lines.extend(
            f"- [[{Path(path).stem}]] `{path}`：{snippet}"
            for path, _, _, snippet in rows
        )
    else:
        lines.append("- 暂无，需要先收集资料。")
    structures = {
        "roadmap": ["概念入门", "核心机制", "实践案例", "常见问题", "项目化练习", "输出复盘"],
        "report": ["背景与问题", "现状与已有资料", "核心发现", "风险与缺口", "行动建议", "后续计划"],
        "article": ["引入问题", "核心观点", "例子或案例", "方法框架", "总结与下一步"],
    }
    lines.extend(["", "## 建议结构", ""])
    lines.extend(f"{index}. {item}" for index, item in enumerate(structures[kind], 1))
    lines.extend(
        ["", "## 待补充", "", "- 补充关键概念笔记。", "- 补充资料索引。", "- 补充实践案例和输出结论。"]
    )
    return "\n".join(lines)


def rebuild_work(report: Any) -> dict[str, object]:
    with WRITE_LOCK:
        report(5, "正在重建关键词索引")
        keyword_path = kb_agent.build_index(argparse.Namespace(resources=True))
        report(20, "正在加载可检索文档")
        vector_result = semantic_store.build(
            kb_agent.load_documents(include_resources=True), report
        )
        log_action(
            "maintenance.rebuild-all-indexes",
            "重建关键词和向量索引",
            [rel(keyword_path), str(vector_result["path"])],
        )
    return {
        "keyword_index": rel(keyword_path),
        "keyword_documents": index_document_count(),
        "vector_index": vector_result,
    }


def health_work(report: Any) -> dict[str, object]:
    with WRITE_LOCK:
        report(5, "正在运行知识库体检")
        health_path = kb_agent.health(
            argparse.Namespace(large_note_words=1200, threshold=0.18, limit=5)
        )
        report(25, "正在更新向量索引")
        vector_result = semantic_store.build(
            kb_agent.load_documents(include_resources=True), report
        )
        log_action(
            "maintenance.health",
            "运行完整体检并更新向量索引",
            [rel(health_path), str(vector_result["path"])],
        )
    return {"health_report": rel(health_path), "vector_index": vector_result}


def apply_inbox_plan(plan: dict[str, Any]) -> list[str]:
    if plan.get("status") != "pending":
        raise RuntimeError("该变更计划已经处理")
    outputs: list[str] = []
    for operation in plan.get("operations", []):
        source = safe_path(str(operation["source"]))
        target = safe_path(str(operation["target"]))
        signature = operation.get("signature", {})
        if not source.exists():
            raise RuntimeError(f"源文件已不存在：{operation['source']}")
        if (
            source.stat().st_size != signature.get("size")
            or source.stat().st_mtime_ns != signature.get("mtime_ns")
        ):
            raise RuntimeError(f"文件在审批期间已变化：{operation['source']}")
        target.parent.mkdir(parents=True, exist_ok=True)
        source.replace(target)
        outputs.append(rel(target))
        if not operation.get("generate_notes", True):
            continue
        text, message = kb_agent.extract_resource_text(target)
        index_target = safe_path(str(operation["index_target"]))
        kb_agent.write(index_target, kb_agent.index_content(target, text, message))
        draft = kb_agent.draft_note_for_resource(target, text, message, True)
        outputs.extend([rel(index_target), rel(draft)])
    plan["status"] = "applied"
    plan["applied_at"] = datetime.now().isoformat(timespec="seconds")
    change_manager.save_plan(plan)
    return outputs


@app.get("/api/status")
def get_status() -> dict[str, object]:
    markdown = kb.iter_markdown()
    inbox = [
        item for item in kb.INBOX.iterdir()
        if item.name.lower() != "readme.md" and not item.name.startswith(".")
    ]
    vector = semantic_store.status()
    return {
        "name": "My Knowledge Base",
        "root": str(ROOT),
        "markdown_count": len(markdown),
        "note_count": sum(path.is_relative_to(kb.NOTES) for path in markdown),
        "moc_count": sum(path.is_relative_to(kb.MOCS) for path in markdown),
        "inbox_count": len(inbox),
        "indexed_count": index_document_count(),
        "index_updated": (
            datetime.fromtimestamp(kb_agent.DB_PATH.stat().st_mtime).isoformat(timespec="minutes")
            if kb_agent.DB_PATH.exists()
            else None
        ),
        "vector_indexed_count": vector["indexed_documents"],
        "vector_updated": vector["updated_at"],
        "recent_files": recent_files(),
    }


@app.post("/api/search")
def search(request: SearchRequest) -> dict[str, object]:
    query = request.query.strip()
    keyword_rows = kb_agent.search_docs(query, max(request.limit * 2, 20))
    warning = None
    if request.mode == "keyword":
        results = [
            {
                "path": path,
                "title": title,
                "kind": kind,
                "snippet": snippet,
                "source": "keyword",
            }
            for path, title, kind, snippet in keyword_rows[:request.limit]
        ]
    elif request.mode == "semantic":
        results = semantic_store.search(query, request.limit)
    else:
        try:
            results = semantic_store.hybrid(query, keyword_rows, request.limit)
        except Exception as exc:
            warning = f"向量检索暂不可用，已回退关键词检索：{exc}"
            results = [
                {
                    "path": path,
                    "title": title,
                    "kind": kind,
                    "snippet": snippet,
                    "source": "keyword",
                }
                for path, title, kind, snippet in keyword_rows[:request.limit]
            ]
    return {
        "query": request.query,
        "mode": request.mode,
        "count": len(results),
        "warning": warning,
        "results": results,
    }


@app.get("/api/files")
def list_files() -> dict[str, object]:
    return {"roots": [tree_node(path) for path in VISIBLE_ROOTS if path.exists()]}


@app.get("/api/directories")
def list_directories() -> dict[str, object]:
    return {"directories": directory_options()}


@app.get("/api/file")
def read_file(path: str = Query(min_length=1)) -> dict[str, str]:
    return read_payload(safe_path(path))


@app.get("/api/raw")
def read_raw(path: str = Query(min_length=1)) -> FileResponse:
    target = safe_path(path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    if target.suffix.lower() not in EMBED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="该文件类型不支持内嵌预览")
    return FileResponse(target, filename=target.name, content_disposition_type="inline")


def guard_mtime(target: Path, expected: str | None) -> None:
    if expected is not None and str(target.stat().st_mtime_ns) != expected:
        raise HTTPException(status_code=409, detail="文件已被其他修改，请关闭后重新打开再编辑")


def submit_index_task(rebuild: bool) -> dict[str, object] | None:
    if not rebuild:
        return None
    return tasks.submit("index", "更新全文与向量索引", rebuild_work)


def notebook_cell_source(cell: dict[str, Any]) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(str(item) for item in source)
    return str(source or "")


@app.post("/api/file/save")
def save_file(request: SaveFileRequest) -> dict[str, object]:
    require_confirmation(request.confirmed)
    target = safe_path(request.path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    if target.suffix.lower() not in TEXT_EDITABLE_EXTENSIONS:
        raise HTTPException(status_code=415, detail="该文件类型不支持在线编辑")
    with WRITE_LOCK:
        guard_mtime(target, request.expected_mtime)
        target.write_text(request.content.rstrip() + "\n", encoding="utf-8")
        log_action("edit.save", rel(target), [rel(target)])
        new_mtime = str(target.stat().st_mtime_ns)
    task = submit_index_task(request.rebuild_indexes)
    return {"saved": rel(target), "mtime": new_mtime, "task": task, "message": "已保存修改"}


@app.get("/api/notebook")
def read_notebook(path: str = Query(min_length=1)) -> dict[str, object]:
    target = safe_path(path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    if target.suffix.lower() != ".ipynb":
        raise HTTPException(status_code=415, detail="该文件不是 Notebook")
    try:
        notebook = json.loads(kb.read_text(target))
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"无法解析 Notebook：{exc}") from exc
    cells = [
        {"index": index, "cell_type": cell.get("cell_type"), "source": notebook_cell_source(cell)}
        for index, cell in enumerate(notebook.get("cells", []))
        if cell.get("cell_type") in {"markdown", "code"}
    ]
    return {
        "path": rel(target),
        "name": target.name,
        "mtime": str(target.stat().st_mtime_ns),
        "cells": cells,
    }


@app.post("/api/notebook/save")
def save_notebook(request: SaveNotebookRequest) -> dict[str, object]:
    require_confirmation(request.confirmed)
    target = safe_path(request.path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    if target.suffix.lower() != ".ipynb":
        raise HTTPException(status_code=415, detail="该文件不是 Notebook")
    with WRITE_LOCK:
        guard_mtime(target, request.expected_mtime)
        try:
            notebook = json.loads(kb.read_text(target))
        except (json.JSONDecodeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=f"无法解析 Notebook：{exc}") from exc
        cells = notebook.get("cells", [])
        for update in request.cells:
            if update.index >= len(cells):
                raise HTTPException(status_code=422, detail=f"单元下标越界：{update.index}")
            cell = cells[update.index]
            if cell.get("cell_type") not in {"markdown", "code"}:
                raise HTTPException(status_code=422, detail=f"单元 {update.index} 不可编辑")
            if notebook_cell_source(cell) == update.source:
                continue
            cell["source"] = update.source.splitlines(keepends=True)
            if cell.get("cell_type") == "code":
                cell["outputs"] = []
                cell["execution_count"] = None
        with target.open("w", encoding="utf-8") as handle:
            json.dump(notebook, handle, ensure_ascii=False, indent=1)
            handle.write("\n")
        log_action("edit.save-notebook", rel(target), [rel(target)])
        new_mtime = str(target.stat().st_mtime_ns)
    task = submit_index_task(request.rebuild_indexes)
    return {"saved": rel(target), "mtime": new_mtime, "task": task, "message": "已保存 Notebook 修改"}


@app.get("/api/wiki")
def read_wiki(title: str = Query(min_length=1)) -> dict[str, str]:
    matches = [
        path for path in kb.iter_markdown()
        if path.stem.lower() == title.strip().lower()
    ]
    if not matches:
        raise HTTPException(status_code=404, detail=f"未找到双链目标：{title}")
    return read_payload(matches[0])


@app.post("/api/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    target_dir: str = Form(...),
    confirmed: bool = Form(False),
    rebuild_indexes: bool = Form(True),
) -> dict[str, object]:
    require_confirmation(confirmed)
    destination = upload_directory(target_dir)
    if not files:
        raise HTTPException(status_code=400, detail="没有选择文件")
    maximum = settings.upload_limit_mb * 1024 * 1024
    saved_paths: list[Path] = []
    try:
        with WRITE_LOCK:
            for upload in files:
                filename = Path(upload.filename or "").name.strip()
                if not filename or filename in {".", ".."}:
                    raise HTTPException(status_code=400, detail="文件名无效")
                if Path(filename).suffix.lower() not in UPLOAD_EXTENSIONS:
                    raise HTTPException(status_code=415, detail=f"不支持上传该类型：{filename}")
                target = kb.unique_path(destination / filename)
                temporary = target.with_name(f".{target.name}.uploading")
                size = 0
                try:
                    with temporary.open("wb") as handle:
                        while chunk := await upload.read(1024 * 1024):
                            size += len(chunk)
                            if size > maximum:
                                raise HTTPException(
                                    status_code=413,
                                    detail=f"{filename} 超过 {settings.upload_limit_mb} MB",
                                )
                            handle.write(chunk)
                    temporary.replace(target)
                    saved_paths.append(target)
                finally:
                    await upload.close()
                    if temporary.exists():
                        temporary.unlink()
            saved = [rel(path) for path in saved_paths]
            log_action("upload", f"上传到 {rel(destination)}", saved)
    except Exception:
        for path in saved_paths:
            if path.exists():
                path.unlink()
        raise
    task = (
        tasks.submit("index", "更新全文与向量索引", rebuild_work)
        if rebuild_indexes
        else None
    )
    return {
        "saved": [rel(path) for path in saved_paths],
        "target_dir": rel(destination),
        "task": task,
        "message": f"已上传 {len(saved_paths)} 个文件",
    }


@app.get("/api/inbox")
def get_inbox() -> dict[str, object]:
    items = [
        file_item(path)
        for path in sorted(kb.INBOX.iterdir(), key=lambda item: item.name.lower())
        if path.name.lower() != "readme.md" and not path.name.startswith(".")
    ]
    return {"count": len(items), "items": items}


@app.post("/api/inbox/preview")
def preview_inbox() -> dict[str, object]:
    operations: list[dict[str, Any]] = []
    for item in sorted(kb.INBOX.iterdir()):
        if item.name.lower() == "readme.md" or item.name.startswith(".") or item.is_dir():
            continue
        target_dir, generate_notes = inbox_target(item)
        if not target_dir:
            continue
        target = kb.unique_path(target_dir / item.name)
        index_target = (
            kb.unique_path(target.with_suffix(".md"))
            if target.suffix.lower() != ".md"
            else kb.unique_path(target.with_name(f"{target.stem}-资料索引.md"))
        )
        diff = f"MOVE {rel(item)}\n  -> {rel(target)}"
        if generate_notes:
            diff += (
                f"\nCREATE {rel(index_target)}\n"
                f"CREATE 40_Notes/<timestamp>-{item.stem}-阅读笔记草案.md"
            )
        operations.append(
            {
                "type": "move",
                "source": rel(item),
                "target": rel(target),
                "index_target": rel(index_target),
                "generate_notes": generate_notes,
                "signature": {
                    "size": item.stat().st_size,
                    "mtime_ns": item.stat().st_mtime_ns,
                },
                "diff": diff,
            }
        )
    plan = change_manager.create_plan(
        "inbox-ingest",
        "Inbox 归档计划",
        f"移动 {len(operations)} 个文件，并生成资料索引和阅读笔记草案。",
        operations,
    )
    log_action("inbox.preview", "创建 Inbox Diff 审批计划", [str(plan["id"])])
    return {"plan": public_plan(plan)}


@app.post("/api/agent/ask")
def ask_agent(request: AskRequest) -> dict[str, object]:
    result = search(
        SearchRequest(query=request.question, limit=request.limit, mode="hybrid")
    )
    lines = [
        "# 知识库回答",
        "",
        f"问题：{request.question}",
        "",
        "## 已有材料",
        "",
    ]
    if result["results"]:
        lines.extend(
            f"- [[{Path(str(item['path'])).stem}]] `{item['path']}`：{item['snippet']}"
            for item in result["results"]
        )
    else:
        lines.append("- 暂时没有检索到强相关材料。")
    lines.extend(["", "## 可能缺口", ""])
    lines.extend(
        f"- `{term}` 是否已有概念笔记、实践记录和权威资料？"
        for term in kb_agent.top_terms(request.question, 5)
    )
    content = "\n".join(lines)
    with WRITE_LOCK:
        kb_agent.write(kb_agent.ASK_REPORT, content)
        log_action("agent.ask", request.question, [rel(kb_agent.ASK_REPORT)])
    rendered, _ = render_text_file(kb_agent.ASK_REPORT, content)
    return {
        "question": request.question,
        "content": content,
        "html": rendered,
        "sources": result["results"],
        "warning": result.get("warning"),
        "report": rel(kb_agent.ASK_REPORT),
    }


@app.post("/api/agent/outline/preview")
def preview_outline(request: OutlinePreviewRequest) -> dict[str, object]:
    kind_name = {"roadmap": "学习路线", "report": "报告大纲", "article": "文章大纲"}[request.kind]
    target = kb.unique_path(
        ROOT / "60_Outputs"
        / f"{datetime.now().strftime('%Y%m%d')}-{kb.safe_filename(request.topic)}-{kind_name}.md"
    )
    plan = change_manager.create_text_plan(
        target,
        outline_content(request.topic.strip(), request.kind, request.limit),
        f"生成 {request.topic} {kind_name}",
        f"将在 {rel(target)} 创建 Markdown 草案。",
    )
    log_action("agent.outline.preview", request.topic, [str(plan["id"])])
    return {"plan": public_plan(plan)}


@app.get("/api/changes")
def list_changes() -> dict[str, object]:
    return {"plans": [public_plan(plan) for plan in change_manager.list_plans()]}


@app.get("/api/changes/{plan_id}")
def get_change(plan_id: str) -> dict[str, object]:
    try:
        return {"plan": public_plan(change_manager.get_plan(plan_id))}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="变更计划不存在") from exc


@app.post("/api/changes/{plan_id}/apply")
def apply_change(plan_id: str, request: ConfirmRequest) -> dict[str, object]:
    require_confirmation(request.confirmed)
    try:
        plan = change_manager.get_plan(plan_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="变更计划不存在") from exc
    with WRITE_LOCK:
        if plan["kind"] == "text-write":
            outputs = change_manager.apply_text_plan(plan)
        elif plan["kind"] == "inbox-ingest":
            outputs = apply_inbox_plan(plan)
        else:
            raise HTTPException(status_code=400, detail="不支持该变更计划类型")
        log_action("changes.apply", str(plan["title"]), outputs)
    task = tasks.submit("index", "同步审批后的检索索引", rebuild_work)
    return {"outputs": outputs, "task": task, "message": "变更已应用"}


@app.post("/api/changes/{plan_id}/reject")
def reject_change(plan_id: str, request: ConfirmRequest) -> dict[str, object]:
    require_confirmation(request.confirmed)
    try:
        plan = change_manager.get_plan(plan_id)
        change_manager.reject_plan(plan)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="变更计划不存在") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    log_action("changes.reject", str(plan["title"]), [plan_id])
    return {"message": "变更已拒绝，不会写入知识库"}

@app.get("/api/tasks")
def list_tasks() -> dict[str, object]:
    return {"tasks": tasks.list()}


@app.get("/api/tasks/{task_id}")
def get_task(task_id: str) -> dict[str, object]:
    try:
        return {"task": tasks.get(task_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="任务不存在") from exc


@app.get("/api/vector/status")
def vector_status(probe: bool = False) -> dict[str, object]:
    return semantic_store.status(probe=probe)


@app.post("/api/maintenance/rebuild-indexes")
def rebuild_indexes(request: ConfirmRequest) -> dict[str, object]:
    require_confirmation(request.confirmed)
    task = tasks.submit("index", "重建全文与向量索引", rebuild_work)
    return {"task": task, "message": "索引任务已进入队列"}


@app.post("/api/maintenance/health")
def run_health(request: ConfirmRequest) -> dict[str, object]:
    require_confirmation(request.confirmed)
    task = tasks.submit("health", "运行完整知识库体检", health_work)
    return {"task": task, "message": "体检任务已进入队列"}


@app.get("/api/reports")
def get_reports() -> dict[str, object]:
    report_paths = [
        kb_agent.HEALTH_REPORT,
        kb.REPORT_PATH,
        kb_agent.LINK_REPORT,
        kb_agent.AGENT_DIR / "Agent摄取报告.md",
        kb_agent.ASK_REPORT,
    ]
    return {
        "reports": [
            {
                **file_item(path),
                "title": path.stem,
                "content": kb.read_text(path),
            }
            for path in report_paths
            if path.exists()
        ]
    }


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


