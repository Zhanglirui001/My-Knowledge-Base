from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import kb

ROOT = kb.ROOT
INBOX = kb.INBOX
NOTES = kb.NOTES
MOCS = kb.MOCS
RESOURCES = kb.RESOURCES
SYSTEM = kb.SYSTEM
OUTPUTS = ROOT / "60_Outputs"
AGENT_DIR = SYSTEM / "Agent"
DB_PATH = AGENT_DIR / "kb_search.sqlite3"
LINK_REPORT = AGENT_DIR / "双链建议.md"
HEALTH_REPORT = AGENT_DIR / "Agent健康报告.md"
ASK_REPORT = AGENT_DIR / "问答记录.md"

STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "into", "when", "where", "what",
    "how", "why", "are", "was", "were", "been", "have", "has", "not", "but", "you", "your",
    "一个", "一种", "这个", "那个", "以及", "因为", "所以", "如果", "可以", "进行", "通过", "实现",
    "相关", "内容", "资料", "笔记", "问题", "方法", "系统", "知识", "文件", "索引",
}

CODE_EXTENSIONS = kb.CODE_EXTENSIONS
RESOURCE_EXTENSIONS = set(kb.RESOURCE_TARGETS.keys()) | CODE_EXTENSIONS


@dataclass
class Document:
    path: Path
    title: str
    kind: str
    tags: list[str]
    text: str


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def note_id() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_+-]{1,}|[\u4e00-\u9fff]{2,}", text.lower())
    tokens: list[str] = []
    for word in words:
        if word in STOPWORDS:
            continue
        if re.fullmatch(r"[\u4e00-\u9fff]{8,}", word):
            tokens.extend(word[i:i + 4] for i in range(0, len(word) - 3, 2))
            continue
        tokens.append(word)
    return tokens


def top_terms(text: str, limit: int = 12) -> list[str]:
    counter = Counter(tokenize(text))
    return [term for term, _ in counter.most_common(limit)]


def extract_title(text: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return fallback


def md_text(path: Path) -> str:
    text = kb.read_text(path)
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
    return text.strip()


def extract_pdf_text(path: Path, max_pages: int = 8) -> tuple[str, str]:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except Exception:
            return "", "未安装 pypdf/PyPDF2，暂时只能建立资料索引，不能抽取 PDF 正文。"
    try:
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages[:max_pages]:
            pages.append(page.extract_text() or "")
        text = "\n".join(pages).strip()
        return text, f"已抽取前 {min(len(reader.pages), max_pages)} 页文本。"
    except Exception as exc:
        return "", f"PDF 文本抽取失败：{exc}"


def extract_drawio_text(path: Path) -> tuple[str, str]:
    raw = kb.read_text(path)
    labels: list[str] = []
    try:
        root = ET.fromstring(raw)
        for cell in root.iter("mxCell"):
            value = cell.attrib.get("value", "")
            value = re.sub(r"<[^>]+>", " ", value)
            value = re.sub(r"\s+", " ", value).strip()
            if value:
                labels.append(value)
    except Exception:
        labels = re.findall(r"value=\"([^\"]+)\"", raw)
    text = "\n".join(labels[:200])
    return text, f"抽取到 {len(labels)} 个 drawio 文本标签。"


def extract_code_text(path: Path, max_chars: int = 20000) -> tuple[str, str]:
    text = kb.read_text(path)[:max_chars]
    return text, "已抽取代码文本。"


def extract_resource_text(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf_text(path)
    if suffix == ".drawio":
        return extract_drawio_text(path)
    if suffix in CODE_EXTENSIONS or suffix in {".txt", ".md"}:
        return extract_code_text(path)
    return "", "该类型暂不抽取正文，只建立索引。"


def summarize_text(text: str, fallback_title: str) -> tuple[str, list[str], list[str]]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[。！？.!?])\s+|\n+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) >= 12]
    summary = "\n".join(f"- {s[:180]}" for s in sentences[:5])
    if not summary and cleaned:
        summary = f"- {cleaned[:240]}"
    if not summary:
        summary = "- 暂无可自动抽取摘要，需要人工补充。"
    terms = top_terms(text or fallback_title, 10)
    questions = [
        f"{fallback_title} 解决的核心问题是什么？",
        f"这些内容能沉淀为哪些可复用方法或检查清单？",
        f"它应该挂到哪个 MOC，和哪些既有笔记互相连接？",
    ]
    return summary, terms, questions


def infer_resource_tags(path: Path, text: str) -> list[str]:
    tags = ["资料"]
    suffix = path.suffix.lower().lstrip(".") or "file"
    tags.append(suffix)
    name_text = f"{path.stem} {text}".lower()
    mapping = {
        "RAG": ["rag", "retrieval", "embedding", "向量", "检索增强"],
        "AI": ["llm", "agent", "model", "prompt", "人工智能", "模型"],
        "代码": ["def ", "class ", "function", "import ", "const ", "代码"],
        "架构图": ["drawio", "architecture", "架构", "流程", "系统"],
        "排障": ["error", "exception", "traceback", "故障", "报错", "排障"],
    }
    for tag, needles in mapping.items():
        if any(needle in name_text for needle in needles):
            tags.append(tag)
    return list(dict.fromkeys(tags))


def draft_note_for_resource(resource: Path, text: str, message: str, apply: bool) -> Path:
    title = kb.safe_filename(resource.stem)
    summary, terms, questions = summarize_text(text, title)
    tags = infer_resource_tags(resource, text)
    path = kb.unique_path(NOTES / f"{note_id()}-{title}-阅读笔记草案.md")
    rel_resource = rel(resource)
    content = f"""---
id: {note_id()}
type: note
status: draft
tags:
{kb.yaml_list(tags)}
source:
  - {rel_resource}
related:
moc:
created: {kb.today()}
updated: {kb.today()}
---

# {title} 阅读笔记草案

## 自动处理状态

- 资源路径：`{rel_resource}`
- 处理说明：{message}

## 自动摘要

{summary}

## 关键词

{chr(10).join(f'- `{term}`' for term in terms) if terms else '- 暂无'}

## 可提炼原子笔记

{chr(10).join(f'- {question}' for question in questions)}

## 人工复核

- 这份资料是否值得保留：
- 应挂载到哪个 MOC：
- 应拆出哪些永久笔记：

"""
    if apply:
        write(path, content)
    return path


def index_content(path: Path, text: str, message: str) -> str:
    title = kb.safe_filename(path.stem)
    summary, terms, _ = summarize_text(text, title)
    tags = infer_resource_tags(path, text)
    return f"""---
type: resource-index
status: draft
tags:
{kb.yaml_list(tags)}
resource_path: {rel(path)}
source_url:
related:
moc:
created: {kb.today()}
updated: {kb.today()}
---

# {title}

## 资料信息

- 类型：{path.suffix.lower().lstrip('.') or 'file'}
- 本地路径：`{rel(path)}`
- 自动处理：{message}

## 自动摘要

{summary}

## 自动关键词

{chr(10).join(f'- `{term}`' for term in terms) if terms else '- 暂无'}

## 可提炼笔记

- 待人工复核后拆分。

## 相关链接


"""


def agent_ingest(args: argparse.Namespace) -> list[str]:
    actions: list[str] = []
    for item in sorted(INBOX.iterdir()):
        if item.name.lower() == "readme.md" or item.name.startswith(".") or item.is_dir():
            continue
        target_dir = kb.target_for(item)
        if not target_dir:
            actions.append(f"REVIEW `{rel(item)}`：未知类型，保留在 Inbox。")
            continue
        dest = kb.unique_path(target_dir / item.name)
        text, message = extract_resource_text(item)
        index_path = kb.unique_path(dest.with_suffix(".md"))
        draft_path = NOTES / f"{note_id()}-{kb.safe_filename(item.stem)}-阅读笔记草案.md"
        actions.append(f"MOVE `{rel(item)}` -> `{rel(dest)}`")
        actions.append(f"INDEX `{rel(index_path)}`")
        if args.drafts:
            actions.append(f"DRAFT `{rel(draft_path)}`")
        if args.apply:
            target_dir.mkdir(parents=True, exist_ok=True)
            item.replace(dest)
            text, message = extract_resource_text(dest)
            write(index_path, index_content(dest, text, message))
            if args.drafts:
                created = draft_note_for_resource(dest, text, message, True)
                actions[-1] = f"DRAFT `{rel(created)}`"
    if not args.apply:
        actions.insert(0, "DRY RUN：加 `--apply` 才会移动文件、建索引和生成草案。")
    write(AGENT_DIR / "Agent摄取报告.md", agent_report("Agent 摄取报告", actions, ["自动化", "摄取"]))
    return actions


def agent_report(title: str, lines: list[str], tags: list[str]) -> str:
    return f"""---
type: system-report
status: active
tags:
{kb.yaml_list(tags)}
updated: {kb.today()}
---

# {title}

生成时间：{now_stamp()}

""" + "\n".join(f"- {line}" for line in lines)


def load_documents(include_resources: bool = True) -> list[Document]:
    docs: list[Document] = []
    for md in kb.iter_markdown():
        text = kb.read_text(md)
        meta = kb.frontmatter(text)
        body = md_text(md)
        docs.append(Document(md, extract_title(body, md.stem), str(meta.get("type") or "markdown"), kb.as_list(meta.get("tags")), body))
    if include_resources:
        for path in RESOURCES.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in RESOURCE_EXTENSIONS or path.suffix.lower() == ".md":
                continue
            text, _ = extract_resource_text(path)
            if text:
                docs.append(Document(path, path.stem, path.suffix.lower().lstrip("."), infer_resource_tags(path, text), text))
    return docs


def build_index(args: argparse.Namespace) -> Path:
    AGENT_DIR.mkdir(parents=True, exist_ok=True)
    docs = load_documents(include_resources=args.resources)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS docs")
    conn.execute("CREATE VIRTUAL TABLE docs USING fts5(path, title, kind, tags, content)")
    conn.executemany(
        "INSERT INTO docs(path, title, kind, tags, content) VALUES (?, ?, ?, ?, ?)",
        [(rel(doc.path), doc.title, doc.kind, ",".join(doc.tags), doc.text) for doc in docs],
    )
    conn.commit()
    conn.close()
    write(AGENT_DIR / "检索索引说明.md", agent_report("检索索引说明", [
        f"索引文件：`{rel(DB_PATH)}`",
        f"索引文档数：{len(docs)}",
        "检索方式：SQLite FTS5，本地关键词/近似语义检索。",
    ], ["自动化", "检索"]))
    return DB_PATH


def ensure_index() -> None:
    if not DB_PATH.exists():
        class Args:
            resources = True
        build_index(Args())


def search_docs(query: str, limit: int = 8) -> list[tuple[str, str, str, str]]:
    ensure_index()
    conn = sqlite3.connect(DB_PATH)
    safe_query = " OR ".join(tokenize(query)[:8]) or query
    try:
        rows = conn.execute(
            "SELECT path, title, kind, snippet(docs, 4, '[', ']', '...', 12) FROM docs WHERE docs MATCH ? LIMIT ?",
            (safe_query, limit),
        ).fetchall()
    except sqlite3.OperationalError:
        rows = conn.execute(
            "SELECT path, title, kind, substr(content, 1, 160) FROM docs WHERE content LIKE ? LIMIT ?",
            (f"%{query}%", limit),
        ).fetchall()
    conn.close()
    return [(str(a), str(b), str(c), str(d)) for a, b, c, d in rows]


def suggest_links(args: argparse.Namespace) -> Path:
    docs = [doc for doc in load_documents(include_resources=False) if doc.path.is_relative_to(NOTES) or doc.path.is_relative_to(MOCS)]
    vectors = {doc.path: Counter(tokenize(doc.title + "\n" + doc.text)) for doc in docs}
    suggestions: list[str] = []
    for doc in docs:
        scores: list[tuple[float, Path]] = []
        v1 = vectors[doc.path]
        if not v1:
            continue
        norm1 = sum(v * v for v in v1.values()) ** 0.5
        for other in docs:
            if other.path == doc.path:
                continue
            v2 = vectors[other.path]
            shared = set(v1) & set(v2)
            if not shared:
                continue
            dot = sum(v1[t] * v2[t] for t in shared)
            norm2 = sum(v * v for v in v2.values()) ** 0.5
            score = dot / (norm1 * norm2) if norm1 and norm2 else 0
            if score >= args.threshold:
                scores.append((score, other.path))
        if scores:
            suggestions.append(f"## {doc.path.stem}\n")
            for score, path in sorted(scores, reverse=True)[:args.limit]:
                suggestions.append(f"- 建议关联 [[{path.stem}]]，相似度 {score:.2f}，路径 `{rel(path)}`")
            suggestions.append("")
    content = f"""---
type: system-report
status: active
tags:
  - 自动化
  - 双链
updated: {kb.today()}
---

# 双链建议

生成时间：{now_stamp()}

这些只是建议，默认不自动写回笔记 frontmatter。

""" + ("\n".join(suggestions) if suggestions else "- 暂无明显双链建议。")
    write(LINK_REPORT, content)
    return LINK_REPORT


def ask(args: argparse.Namespace) -> str:
    rows = search_docs(args.question, args.limit)
    terms = top_terms(args.question, 8)
    lines = [
        "---",
        "type: system-report",
        "status: active",
        "tags:",
        "  - 自动化",
        "  - 问答",
        f"updated: {kb.today()}",
        "---",
        "",
        "# 问答记录",
        "",
        f"问题：{args.question}",
        "",
        "## 初步回答",
        "",
    ]
    if rows:
        lines.append("知识库中已有相关材料。可以优先从下面这些文件切入：")
        lines.append("")
        for path, title, kind, snippet in rows:
            lines.append(f"- [[{Path(path).stem}]] `{path}`：{snippet}")
    else:
        lines.append("暂时没有检索到强相关材料。建议先创建一个 MOC 或收集资料。")
    lines.extend(["", "## 可能缺口", ""])
    if terms:
        lines.extend(f"- `{term}` 是否已有概念笔记、实践笔记和资料索引？" for term in terms[:5])
    else:
        lines.append("- 问题太短，建议补充主题、场景或目标。")
    content = "\n".join(lines)
    write(ASK_REPORT, content)
    return content


def generate_outline(args: argparse.Namespace) -> Path:
    rows = search_docs(args.topic, args.limit)
    kind_name = {"roadmap": "学习路线", "report": "报告大纲", "article": "文章大纲"}.get(args.kind, args.kind)
    path = kb.unique_path(OUTPUTS / f"{datetime.now().strftime('%Y%m%d')}-{kb.safe_filename(args.topic)}-{kind_name}.md")
    lines = [
        "---",
        f"type: {args.kind}",
        "status: draft",
        "tags:",
        "  - 自动化",
        f"  - {args.topic}",
        f"created: {kb.today()}",
        f"updated: {kb.today()}",
        "---",
        "",
        f"# {args.topic} {kind_name}",
        "",
        "## 目标",
        "",
        f"围绕 `{args.topic}` 形成可执行的学习、研究或输出路径。",
        "",
        "## 已有材料",
        "",
    ]
    lines.extend(f"- [[{Path(path_).stem}]] `{path_}`：{snippet}" for path_, title, kind, snippet in rows) if rows else lines.append("- 暂无，需要先收集资料。")
    lines.extend(["", "## 建议结构", ""])
    if args.kind == "roadmap":
        lines.extend(["1. 概念入门", "2. 核心机制", "3. 实践案例", "4. 常见问题", "5. 项目化练习", "6. 输出复盘"])
    elif args.kind == "report":
        lines.extend(["1. 背景与问题", "2. 现状与已有资料", "3. 核心发现", "4. 风险与缺口", "5. 行动建议", "6. 后续计划"])
    else:
        lines.extend(["1. 引入问题", "2. 核心观点", "3. 例子或案例", "4. 方法框架", "5. 总结与下一步"])
    lines.extend(["", "## 待补充", "", "- 补充关键概念笔记。", "- 补充资料索引。", "- 补充实践案例和输出结论。"])
    write(path, "\n".join(lines))
    return path


def health(args: argparse.Namespace) -> Path:
    class AuditArgs:
        large_note_words = args.large_note_words
    kb.audit(AuditArgs())
    class LinkArgs:
        threshold = args.threshold
        limit = args.limit
    suggest_links(LinkArgs())
    build_index(argparse.Namespace(resources=True))
    lines = [
        f"基础体检：`{rel(kb.REPORT_PATH)}`",
        f"双链建议：`{rel(LINK_REPORT)}`",
        f"检索索引：`{rel(DB_PATH)}`",
        "建议每周运行一次：`python scripts/kb_agent.py health`。",
    ]
    write(HEALTH_REPORT, agent_report("Agent 健康报告", lines, ["自动化", "健康报告"]))
    return HEALTH_REPORT


def main() -> None:
    parser = argparse.ArgumentParser(description="Local Knowledge Base Agent")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ingest", help="识别 Inbox、归档、建索引、可选生成阅读笔记草案")
    p.add_argument("--apply", action="store_true", help="真正写入；默认只预览")
    p.add_argument("--drafts", action="store_true", help="为资源生成阅读笔记草案")
    p.set_defaults(func=agent_ingest)

    p = sub.add_parser("build-index", help="构建本地 SQLite FTS 检索索引")
    p.add_argument("--no-resources", dest="resources", action="store_false", help="只索引 Markdown")
    p.set_defaults(resources=True, func=build_index)

    p = sub.add_parser("search", help="检索知识库")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=8)
    p.set_defaults(func=lambda a: "\n".join(f"- {path} | {title} | {kind} | {snippet}" for path, title, kind, snippet in search_docs(a.query, a.limit)))

    p = sub.add_parser("ask", help="基于本地检索回答一个知识库问题")
    p.add_argument("question")
    p.add_argument("--limit", type=int, default=8)
    p.set_defaults(func=ask)

    p = sub.add_parser("suggest-links", help="生成双链建议报告")
    p.add_argument("--threshold", type=float, default=0.18)
    p.add_argument("--limit", type=int, default=5)
    p.set_defaults(func=suggest_links)

    p = sub.add_parser("outline", help="为主题生成学习路线、报告或文章大纲")
    p.add_argument("topic")
    p.add_argument("--kind", choices=["roadmap", "report", "article"], default="roadmap")
    p.add_argument("--limit", type=int, default=8)
    p.set_defaults(func=generate_outline)

    p = sub.add_parser("health", help="生成 Agent 健康报告并刷新索引/双链建议")
    p.add_argument("--large-note-words", type=int, default=1200)
    p.add_argument("--threshold", type=float, default=0.18)
    p.add_argument("--limit", type=int, default=5)
    p.set_defaults(func=health)

    args = parser.parse_args()
    result = args.func(args)
    if isinstance(result, Path):
        print(rel(result))
    elif isinstance(result, list):
        print("\n".join(result))
    else:
        print(result)


if __name__ == "__main__":
    main()
