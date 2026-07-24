from __future__ import annotations

import argparse
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "00_Inbox"
NOTES = ROOT / "40_Notes"
MOCS = ROOT / "50_MOCs"
PROJECTS = ROOT / "10_Projects"
RESOURCES = ROOT / "30_Resources"
SYSTEM = ROOT / "90_System"
REPORT_PATH = SYSTEM / "知识库体检报告.md"
AUTO_INDEX_PATH = MOCS / "自动索引 MOC.md"

RESOURCE_TARGETS = {
    ".pdf": RESOURCES / "PDFs",
    ".epub": RESOURCES / "Books",
    ".mobi": RESOURCES / "Books",
    ".drawio": RESOURCES / "Drawio",
    ".png": ROOT / "_assets",
    ".jpg": ROOT / "_assets",
    ".jpeg": ROOT / "_assets",
    ".gif": ROOT / "_assets",
    ".svg": ROOT / "_assets",
    ".webp": ROOT / "_assets",
}

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".cpp", ".c",
    ".h", ".hpp", ".cs", ".php", ".rb", ".sh", ".ps1", ".bat", ".sql", ".yaml",
    ".yml", ".json", ".toml", ".ini", ".dockerfile",
}

SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__"}


def now_id() -> str:
    return datetime.now().strftime("%Y%m%d%H%M")


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def safe_filename(title: str) -> str:
    title = title.strip()
    title = re.sub(r"[\\/:*?\"<>|]", "-", title)
    title = re.sub(r"\s+", " ", title)
    return title[:80].strip(" .") or "未命名"


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    parent = path.parent
    index = 2
    while True:
        candidate = parent / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def yaml_list(items: list[str] | None, indent: int = 2) -> str:
    if not items:
        return ""
    spaces = " " * indent
    return "\n".join(f"{spaces}- {item}" for item in items)


def parse_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def frontmatter(text: str) -> dict[str, object]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    block = text[4:end].splitlines()
    data: dict[str, object] = {}
    current_key: str | None = None
    for raw_line in block:
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if line.startswith("  - ") and current_key:
            data.setdefault(current_key, [])
            value = line[4:].strip()
            if isinstance(data[current_key], list):
                data[current_key].append(value)
            continue
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_key = key
            data[key] = value if value else []
    return data


def iter_markdown() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*.md"):
        if path.name.lower() == "readme.md":
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def wikilink(path: Path) -> str:
    return f"[[{path.stem}]]"


def create_note(args: argparse.Namespace) -> Path:
    note_id = now_id()
    title = safe_filename(args.title)
    tags = parse_csv(args.tags) or ["待分类"]
    mocs = parse_csv(args.moc)
    related = parse_csv(args.related)
    path = unique_path(NOTES / f"{note_id}-{title}.md")
    content = f"""---
id: {note_id}
type: note
status: draft
tags:
{yaml_list(tags)}
source:
related:
{yaml_list(related)}
moc:
{yaml_list(mocs)}
created: {today()}
updated: {today()}
---

# {title}

## 一句话总结


## 内容


## 例子


## 与其他知识的关系


## 可复用场景


"""
    write_text(path, content)
    return path


def create_moc(args: argparse.Namespace) -> Path:
    title = safe_filename(args.title)
    name = title if title.endswith("MOC") else f"{title} MOC"
    tags = ["MOC"] + parse_csv(args.tags)
    path = unique_path(MOCS / f"{name}.md")
    content = f"""---
type: moc
status: active
tags:
{yaml_list(tags)}
created: {today()}
updated: {today()}
---

# {name}

## 核心问题


## 入门路径


## 核心概念


## 关键笔记


## 相关资料


## 可输出主题


## 待完善


"""
    write_text(path, content)
    return path


def create_project(args: argparse.Namespace) -> Path:
    title = safe_filename(args.title)
    project_dir = unique_path(PROJECTS / title)
    project_dir.mkdir(parents=True, exist_ok=True)
    path = project_dir / "README.md"
    content = f"""---
type: project
status: active
tags:
  - 项目
created: {today()}
updated: {today()}
---

# {title}

## 背景


## 目标


## 关键资料


## 任务


## 决策记录


## 风险


## 复盘


## 可沉淀为原子笔记的内容


"""
    write_text(path, content)
    return path


def target_for(path: Path) -> Path | None:
    suffix = path.suffix.lower()
    if suffix in CODE_EXTENSIONS:
        return RESOURCES / "Code"
    return RESOURCE_TARGETS.get(suffix)


def resource_index_content(resource_path: Path) -> str:
    rel = resource_path.relative_to(ROOT).as_posix()
    suffix = resource_path.suffix.lower().lstrip(".") or "file"
    return f"""---
type: resource-index
status: draft
tags:
  - 资料
  - {suffix}
resource_path: {rel}
source_url:
related:
moc:
created: {today()}
updated: {today()}
---

# {resource_path.stem}

## 资料信息

- 类型：{suffix}
- 作者/来源：
- 时间：
- 本地路径：`{rel}`

## 为什么保留


## 核心摘要


## 可提炼笔记


## 相关链接


"""


def ingest_inbox(args: argparse.Namespace) -> list[str]:
    actions: list[str] = []
    for item in sorted(INBOX.iterdir()):
        if item.name.lower() == "readme.md" or item.name.startswith("."):
            continue
        if item.is_dir():
            actions.append(f"SKIP directory: {item.relative_to(ROOT)}")
            continue
        target_dir = target_for(item)
        if not target_dir:
            actions.append(f"REVIEW manually: {item.relative_to(ROOT)}")
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        dest = unique_path(target_dir / item.name)
        actions.append(f"MOVE {item.relative_to(ROOT)} -> {dest.relative_to(ROOT)}")
        index_path = unique_path(dest.with_suffix(".md"))
        actions.append(f"CREATE index: {index_path.relative_to(ROOT)}")
        if args.apply:
            shutil.move(str(item), str(dest))
            write_text(index_path, resource_index_content(dest))
    if not args.apply:
        actions.insert(0, "DRY RUN: add --apply to move files and create indexes.")
    report = SYSTEM / "Inbox分流报告.md"
    write_text(report, f"""---
type: system-report
status: active
tags:
  - 自动化
  - inbox
created: {today()}
updated: {today()}
---

# Inbox 分流报告

""" + "\n".join(f"- {line}" for line in actions))
    return actions


@dataclass
class MdFile:
    path: Path
    meta: dict[str, object]
    text: str


def load_md_files() -> list[MdFile]:
    result: list[MdFile] = []
    for path in iter_markdown():
        text = read_text(path)
        result.append(MdFile(path=path, meta=frontmatter(text), text=text))
    return result


def as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def audit(args: argparse.Namespace) -> str:
    files = load_md_files()
    missing_frontmatter: list[Path] = []
    missing_tags: list[Path] = []
    missing_status: list[Path] = []
    notes_without_moc: list[Path] = []
    orphan_notes: list[Path] = []
    oversized_notes: list[tuple[Path, int]] = []
    tag_counter: Counter[str] = Counter()

    for item in files:
        rel = item.path.relative_to(ROOT)
        meta = item.meta
        if not meta:
            missing_frontmatter.append(rel)
        tags = as_list(meta.get("tags"))
        if not tags and "90_System/Templates" not in rel.as_posix():
            missing_tags.append(rel)
        for tag in tags:
            tag_counter[tag] += 1
        if not meta.get("status") and "90_System/Templates" not in rel.as_posix():
            missing_status.append(rel)
        if item.path.is_relative_to(NOTES):
            moc = as_list(meta.get("moc"))
            related = as_list(meta.get("related"))
            if not moc:
                notes_without_moc.append(rel)
            if not moc and not related:
                orphan_notes.append(rel)
            word_count = len(re.findall(r"\S+", item.text))
            if word_count > args.large_note_words:
                oversized_notes.append((rel, word_count))

    lines = [
        "---",
        "type: system-report",
        "status: active",
        "tags:",
        "  - 自动化",
        "  - 体检",
        f"updated: {today()}",
        "---",
        "",
        "# 知识库体检报告",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 总览",
        "",
        f"- Markdown 文件数：{len(files)}",
        f"- 标签数：{len(tag_counter)}",
        f"- 缺少 frontmatter：{len(missing_frontmatter)}",
        f"- 缺少 tags：{len(missing_tags)}",
        f"- 缺少 status：{len(missing_status)}",
        f"- 未挂 MOC 的原子笔记：{len(notes_without_moc)}",
        f"- 孤立原子笔记：{len(orphan_notes)}",
        "",
        "## 高频标签",
        "",
    ]
    lines.extend(f"- `{tag}`：{count}" for tag, count in tag_counter.most_common(30))
    sections = [
        ("缺少 frontmatter", missing_frontmatter),
        ("缺少 tags", missing_tags),
        ("缺少 status", missing_status),
        ("未挂 MOC 的原子笔记", notes_without_moc),
        ("孤立原子笔记", orphan_notes),
    ]
    for title, paths in sections:
        lines.extend(["", f"## {title}", ""])
        if paths:
            lines.extend(f"- `{path.as_posix()}`" for path in paths)
        else:
            lines.append("- 暂无")
    lines.extend(["", "## 可能过大的原子笔记", ""])
    if oversized_notes:
        lines.extend(f"- `{path.as_posix()}`：{count} words" for path, count in oversized_notes)
    else:
        lines.append("- 暂无")
    content = "\n".join(lines)
    write_text(REPORT_PATH, content)
    return content


def update_index(args: argparse.Namespace) -> Path:
    files = load_md_files()
    by_type: defaultdict[str, list[MdFile]] = defaultdict(list)
    tag_counter: Counter[str] = Counter()
    for item in files:
        rel = item.path.relative_to(ROOT).as_posix()
        if rel.startswith("90_System/Templates/"):
            continue
        kind = str(item.meta.get("type") or "unknown")
        by_type[kind].append(item)
        for tag in as_list(item.meta.get("tags")):
            tag_counter[tag] += 1

    def links(items: list[MdFile], limit: int | None = None) -> list[str]:
        selected = sorted(items, key=lambda x: x.path.as_posix())
        if limit:
            selected = selected[:limit]
        return [f"- [[{item.path.stem}]] `({item.path.relative_to(ROOT).as_posix()})`" for item in selected]

    lines = [
        "---",
        "type: moc",
        "status: active",
        "tags:",
        "  - MOC",
        "  - 自动索引",
        f"updated: {today()}",
        "---",
        "",
        "# 自动索引 MOC",
        "",
        "此文件由 `python scripts/kb.py update-index` 生成。可以手工阅读，但建议不要手工维护列表内容。",
        "",
        "## MOC",
        "",
    ]
    lines.extend(links(by_type.get("moc", [])) or ["- 暂无"])
    lines.extend(["", "## 原子笔记", ""])
    lines.extend(links(by_type.get("note", [])) or ["- 暂无"])
    lines.extend(["", "## 资料索引", ""])
    lines.extend(links(by_type.get("resource-index", [])) or ["- 暂无"])
    lines.extend(["", "## 项目", ""])
    lines.extend(links(by_type.get("project", [])) or ["- 暂无"])
    lines.extend(["", "## 高频标签", ""])
    lines.extend(f"- `{tag}`：{count}" for tag, count in tag_counter.most_common(50))
    write_text(AUTO_INDEX_PATH, "\n".join(lines))
    return AUTO_INDEX_PATH


def main() -> None:
    parser = argparse.ArgumentParser(description="My Knowledge Base automation")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("new-note", help="创建原子笔记")
    p.add_argument("title")
    p.add_argument("--tags", default="")
    p.add_argument("--moc", default="")
    p.add_argument("--related", default="")
    p.set_defaults(func=create_note)

    p = sub.add_parser("new-moc", help="创建 MOC")
    p.add_argument("title")
    p.add_argument("--tags", default="")
    p.set_defaults(func=create_moc)

    p = sub.add_parser("new-project", help="创建项目首页")
    p.add_argument("title")
    p.set_defaults(func=create_project)

    p = sub.add_parser("ingest-inbox", help="分流 Inbox 中的资源文件")
    p.add_argument("--apply", action="store_true", help="真正移动文件并创建资料索引；默认只生成预览报告")
    p.set_defaults(func=ingest_inbox)

    p = sub.add_parser("audit", help="生成知识库体检报告")
    p.add_argument("--large-note-words", type=int, default=1200)
    p.set_defaults(func=audit)

    p = sub.add_parser("update-index", help="更新自动索引 MOC")
    p.set_defaults(func=update_index)

    args = parser.parse_args()
    result = args.func(args)
    if isinstance(result, Path):
        print(result.relative_to(ROOT))
    elif isinstance(result, list):
        print("\n".join(result))
    else:
        print(result)


if __name__ == "__main__":
    main()




