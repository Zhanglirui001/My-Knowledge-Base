from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
WEB_DIR = ROOT / "web"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import kb  # noqa: E402
import kb_agent  # noqa: E402

app = FastAPI(title="My Knowledge Base", version="0.1.0", docs_url="/api/docs", redoc_url=None)
WRITE_LOCK = threading.Lock()
ACTION_LOG = kb_agent.AGENT_DIR / "Web操作日志.jsonl"
VISIBLE_ROOTS = (kb.INBOX, kb.PROJECTS, ROOT / "20_Areas", kb.RESOURCES, kb.NOTES, kb.MOCS, ROOT / "60_Outputs", ROOT / "90_Archive", kb.SYSTEM)
PREVIEW_EXTENSIONS = {".md", ".txt", ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml", ".css", ".html", ".xml", ".drawio"}


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=300)
    limit: int = Field(default=12, ge=1, le=50)


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    limit: int = Field(default=8, ge=1, le=20)


class OutlineRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=160)
    kind: Literal["roadmap", "report", "article"] = "roadmap"
    limit: int = Field(default=8, ge=1, le=20)
    confirmed: bool = False


class ConfirmRequest(BaseModel):
    confirmed: bool = False


def safe_path(value: str) -> Path:
    candidate = (ROOT / value).resolve()
    try:
        candidate.relative_to(ROOT)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="路径不在知识库范围内") from exc
    return candidate


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def require_confirmation(confirmed: bool) -> None:
    if not confirmed:
        raise HTTPException(status_code=409, detail="该操作会写入知识库，需要明确确认")


def log_action(action: str, detail: str, outputs: list[str] | None = None) -> None:
    kb_agent.AGENT_DIR.mkdir(parents=True, exist_ok=True)
    record = {"timestamp": datetime.now().isoformat(timespec="seconds"), "action": action, "detail": detail, "outputs": outputs or []}
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


def tree_node(path: Path, depth: int = 0, max_depth: int = 4) -> dict[str, object]:
    node = file_item(path)
    if path.is_dir() and depth < max_depth:
        children = [child for child in path.iterdir() if not child.name.startswith(".") and child.name != "__pycache__"]
        children.sort(key=lambda child: (not child.is_dir(), child.name.lower()))
        node["children"] = [tree_node(child, depth + 1, max_depth) for child in children]
    return node


def index_document_count() -> int:
    if not kb_agent.DB_PATH.exists():
        return 0
    try:
        with sqlite3.connect(kb_agent.DB_PATH) as connection:
            return int(connection.execute("SELECT count(*) FROM docs").fetchone()[0])
    except (sqlite3.Error, TypeError):
        return 0


def recent_files(limit: int = 8) -> list[dict[str, str]]:
    candidates = [path for path in kb.iter_markdown() if "90_System/Templates" not in path.as_posix()]
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return [{"path": rel(path), "name": path.stem, "updated": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="minutes")} for path in candidates[:limit]]


@app.get("/api/status")
def get_status() -> dict[str, object]:
    markdown = kb.iter_markdown()
    inbox_items = [item for item in kb.INBOX.iterdir() if item.name.lower() != "readme.md" and not item.name.startswith(".")]
    index_updated = datetime.fromtimestamp(kb_agent.DB_PATH.stat().st_mtime).isoformat(timespec="minutes") if kb_agent.DB_PATH.exists() else None
    return {
        "name": "My Knowledge Base",
        "root": str(ROOT),
        "markdown_count": len(markdown),
        "note_count": sum(path.is_relative_to(kb.NOTES) for path in markdown),
        "moc_count": sum(path.is_relative_to(kb.MOCS) for path in markdown),
        "inbox_count": len(inbox_items),
        "indexed_count": index_document_count(),
        "index_updated": index_updated,
        "recent_files": recent_files(),
    }


@app.post("/api/search")
def search(request: SearchRequest) -> dict[str, object]:
    rows = kb_agent.search_docs(request.query.strip(), request.limit)
    return {"query": request.query, "count": len(rows), "results": [{"path": path, "title": title, "kind": kind, "snippet": snippet} for path, title, kind, snippet in rows]}


@app.get("/api/files")
def list_files() -> dict[str, object]:
    return {"roots": [tree_node(path) for path in VISIBLE_ROOTS if path.exists()]}


@app.get("/api/file")
def read_file(path: str = Query(min_length=1)) -> dict[str, str]:
    target = safe_path(path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    if target.suffix.lower() not in PREVIEW_EXTENSIONS:
        raise HTTPException(status_code=415, detail="该文件类型暂不支持在线预览")
    return {"path": rel(target), "name": target.name, "content": kb.read_text(target)}


@app.get("/api/inbox")
def get_inbox() -> dict[str, object]:
    items = [file_item(path) for path in sorted(kb.INBOX.iterdir(), key=lambda item: item.name.lower()) if path.name.lower() != "readme.md" and not path.name.startswith(".")]
    return {"count": len(items), "items": items}


@app.post("/api/inbox/preview")
def preview_inbox() -> dict[str, object]:
    with WRITE_LOCK:
        actions = kb_agent.agent_ingest(argparse.Namespace(apply=False, drafts=True))
        log_action("inbox.preview", "预览 Inbox 分流", [rel(kb_agent.AGENT_DIR / "Agent摄取报告.md")])
    return {"actions": actions, "report": rel(kb_agent.AGENT_DIR / "Agent摄取报告.md")}


@app.post("/api/inbox/apply")
def apply_inbox(request: ConfirmRequest) -> dict[str, object]:
    require_confirmation(request.confirmed)
    with WRITE_LOCK:
        actions = kb_agent.agent_ingest(argparse.Namespace(apply=True, drafts=True))
        kb_agent.build_index(argparse.Namespace(resources=True))
        log_action("inbox.apply", "归档 Inbox 并生成阅读笔记草案", actions)
    return {"actions": actions, "message": "Inbox 已归档，检索索引已更新"}


@app.post("/api/agent/ask")
def ask_agent(request: AskRequest) -> dict[str, object]:
    with WRITE_LOCK:
        content = kb_agent.ask(argparse.Namespace(question=request.question.strip(), limit=request.limit))
        log_action("agent.ask", request.question, [rel(kb_agent.ASK_REPORT)])
    return {"question": request.question, "content": content, "report": rel(kb_agent.ASK_REPORT)}


@app.post("/api/agent/outline")
def create_outline(request: OutlineRequest) -> dict[str, object]:
    require_confirmation(request.confirmed)
    with WRITE_LOCK:
        path = kb_agent.generate_outline(argparse.Namespace(topic=request.topic.strip(), kind=request.kind, limit=request.limit))
        log_action("agent.outline", f"{request.kind}: {request.topic}", [rel(path)])
    return {"path": rel(path), "message": "大纲草案已生成"}


@app.post("/api/maintenance/rebuild-index")
def rebuild_index(request: ConfirmRequest) -> dict[str, object]:
    require_confirmation(request.confirmed)
    with WRITE_LOCK:
        path = kb_agent.build_index(argparse.Namespace(resources=True))
        count = index_document_count()
        log_action("maintenance.rebuild-index", "重建全文检索索引", [rel(path)])
    return {"path": rel(path), "indexed_count": count, "message": f"索引已重建，共 {count} 项"}


@app.post("/api/maintenance/health")
def run_health(request: ConfirmRequest) -> dict[str, object]:
    require_confirmation(request.confirmed)
    with WRITE_LOCK:
        path = kb_agent.health(argparse.Namespace(large_note_words=1200, threshold=0.18, limit=5))
        log_action("maintenance.health", "运行知识库体检、双链建议与索引重建", [rel(path), rel(kb.REPORT_PATH), rel(kb_agent.LINK_REPORT)])
    return {"path": rel(path), "message": "健康检查已完成"}


@app.get("/api/reports")
def get_reports() -> dict[str, object]:
    report_paths = [kb_agent.HEALTH_REPORT, kb.REPORT_PATH, kb_agent.LINK_REPORT, kb_agent.AGENT_DIR / "Agent摄取报告.md", kb_agent.ASK_REPORT]
    reports = [{**file_item(path), "title": path.stem, "content": kb.read_text(path)} for path in report_paths if path.exists()]
    return {"reports": reports}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

