from __future__ import annotations

import html
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
