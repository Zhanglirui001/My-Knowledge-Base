from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import quote

from markdown_it import MarkdownIt


MARKDOWN = (
    MarkdownIt("commonmark", {"html": False, "linkify": False, "typographer": False})
    .enable("table")
    .enable("strikethrough")
)


def split_frontmatter(text: str) -> tuple[str, str]:
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", text, re.DOTALL)
    if not match:
        return "", text
    return match.group(1).strip(), text[match.end():]


def expand_wikilinks(text: str) -> str:
    def replacement(match: re.Match[str]) -> str:
        target = match.group(1).strip()
        label = (match.group(2) or target).strip()
        return f"[{label}](/api/wiki?title={quote(target)})"

    return re.sub(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", replacement, text)


def render_markdown(text: str) -> tuple[str, str]:
    frontmatter, body = split_frontmatter(text)
    rendered = MARKDOWN.render(expand_wikilinks(body))
    return rendered, frontmatter


def render_text_file(path: Path, text: str) -> tuple[str, str]:
    if path.suffix.lower() == ".md":
        return render_markdown(text)
    language = path.suffix.lower().lstrip(".")
    class_name = f' class="language-{html.escape(language)}"' if language else ""
    return f"<pre><code{class_name}>{html.escape(text)}</code></pre>", ""


ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


def _joined(value: object) -> str:
    if isinstance(value, list):
        return "".join(str(item) for item in value)
    return str(value or "")


def _render_outputs(outputs: list[dict]) -> str:
    blocks: list[str] = []
    for output in outputs:
        kind = output.get("output_type")
        if kind == "stream":
            blocks.append(
                f'<pre class="nb-output nb-stream"><code>{html.escape(_joined(output.get("text")))}</code></pre>'
            )
        elif kind in {"execute_result", "display_data"}:
            data = output.get("data", {})
            image = data.get("image/png")
            if image:
                source = _joined(image).strip().replace("\n", "")
                blocks.append(
                    f'<img class="nb-output nb-image" alt="notebook 输出" '
                    f'src="data:image/png;base64,{html.escape(source)}">'
                )
            else:
                # 出于安全考虑不渲染原始 text/html，回退到纯文本表示
                text = _joined(data.get("text/plain"))
                if text.strip():
                    blocks.append(f'<pre class="nb-output"><code>{html.escape(text)}</code></pre>')
        elif kind == "error":
            traceback = ANSI_ESCAPE.sub("", "\n".join(output.get("traceback", [])))
            blocks.append(
                f'<pre class="nb-output nb-error"><code>{html.escape(traceback)}</code></pre>'
            )
    return "".join(blocks)


def render_notebook(text: str) -> tuple[str, str]:
    try:
        notebook = json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        return f'<pre class="nb-error"><code>无法解析 Notebook：{html.escape(str(exc))}</code></pre>', ""
    metadata = notebook.get("metadata", {})
    language = (
        metadata.get("language_info", {}).get("name")
        or metadata.get("kernelspec", {}).get("language")
        or "python"
    )
    parts: list[str] = []
    for cell in notebook.get("cells", []):
        cell_type = cell.get("cell_type")
        source = _joined(cell.get("source"))
        if cell_type == "markdown":
            parts.append(f'<div class="nb-cell nb-md">{MARKDOWN.render(expand_wikilinks(source))}</div>')
        elif cell_type == "code":
            inner = ""
            if source.strip():
                inner += (
                    f'<pre class="nb-source"><code class="language-{html.escape(language)}">'
                    f'{html.escape(source)}</code></pre>'
                )
            inner += _render_outputs(cell.get("outputs", []))
            if inner:
                parts.append(f'<div class="nb-cell nb-code">{inner}</div>')
    body = "".join(parts) or '<p class="nb-empty">空 Notebook。</p>'
    return f'<div class="notebook">{body}</div>', ""
