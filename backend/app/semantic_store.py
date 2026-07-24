from __future__ import annotations

import math
import os
import sqlite3
from array import array
from contextlib import closing
from datetime import datetime
from typing import Callable, Iterable

import httpx

from .config import settings


VECTOR_DB_PATH = settings.root / "90_System" / "Agent" / "kb_vectors.sqlite3"
ProgressReporter = Callable[[int, str], None]


def headers() -> dict[str, str]:
    result = {"Content-Type": "application/json"}
    if settings.embedding_api_key:
        result["Authorization"] = f"Bearer {settings.embedding_api_key}"
    return result


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    with httpx.Client(timeout=120, trust_env=False) as client:
        response = client.post(
            f"{settings.embedding_url}/embeddings",
            headers=headers(),
            json={
                "model": settings.embedding_model,
                "input": texts,
                "encoding_format": "float",
            },
        )
        response.raise_for_status()
        payload = response.json()
    rows = sorted(payload.get("data", []), key=lambda item: item.get("index", 0))
    vectors = [row.get("embedding", []) for row in rows]
    if len(vectors) != len(texts) or not all(vectors):
        raise RuntimeError("Embedding 服务返回的数据数量或维度不正确")
    return [[float(value) for value in vector] for vector in vectors]


def status(probe: bool = False) -> dict[str, object]:
    result: dict[str, object] = {
        "url": settings.embedding_url,
        "model": settings.embedding_model,
        "available": None,
        "indexed_chunks": 0,
        "indexed_documents": 0,
        "dimension": None,
        "updated_at": None,
    }
    if VECTOR_DB_PATH.exists():
        try:
            with closing(sqlite3.connect(VECTOR_DB_PATH)) as connection:
                metadata = dict(connection.execute("SELECT key, value FROM metadata"))
                result.update(
                    indexed_chunks=int(
                        connection.execute("SELECT count(*) FROM chunks").fetchone()[0]
                    ),
                    indexed_documents=int(
                        connection.execute(
                            "SELECT count(DISTINCT path) FROM chunks"
                        ).fetchone()[0]
                    ),
                    dimension=int(metadata.get("dimension", "0")) or None,
                    updated_at=metadata.get("updated_at"),
                )
        except sqlite3.Error:
            pass
    if probe:
        try:
            embed_texts(["知识库向量服务连通性检查"])
            result["available"] = True
        except Exception as exc:
            result["available"] = False
            result["error"] = str(exc)
    return result


def chunk_text(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    size = settings.vector_chunk_chars
    overlap = min(settings.vector_chunk_overlap, size // 2)
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            boundary = max(
                text.rfind("\n", start + size // 2, end),
                text.rfind("。", start + size // 2, end),
            )
            if boundary > start:
                end = boundary + 1
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return [chunk for chunk in chunks if chunk]


def normalize(vector: Iterable[float]) -> list[float]:
    values = [float(value) for value in vector]
    norm = math.sqrt(sum(value * value for value in values))
    return values if not norm else [value / norm for value in values]


def to_blob(vector: list[float]) -> bytes:
    return array("f", normalize(vector)).tobytes()


def from_blob(blob: bytes) -> array:
    values = array("f")
    values.frombytes(blob)
    return values


def build(documents: Iterable[object], report: ProgressReporter) -> dict[str, object]:
    docs = list(documents)
    chunks: list[dict[str, object]] = []
    for doc_index, document in enumerate(docs):
        for chunk_index, content in enumerate(chunk_text(str(getattr(document, "text")))):
            chunks.append(
                {
                    "path": getattr(document, "path").relative_to(settings.root).as_posix(),
                    "title": str(getattr(document, "title")),
                    "kind": str(getattr(document, "kind")),
                    "chunk_index": chunk_index,
                    "content": content,
                }
            )
        report(
            min(20, int((doc_index + 1) / max(1, len(docs)) * 20)),
            f"正在切分文档 {doc_index + 1}/{len(docs)}",
        )
    if not chunks:
        raise RuntimeError("没有可建立向量索引的文本内容")

    vectors: list[list[float]] = []
    batch_size = max(1, settings.vector_batch_size)
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]
        vectors.extend(embed_texts([str(row["content"]) for row in batch]))
        complete = min(len(chunks), start + len(batch))
        report(
            20 + int(complete / len(chunks) * 70),
            f"正在生成向量 {complete}/{len(chunks)}",
        )

    VECTOR_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = VECTOR_DB_PATH.with_suffix(".tmp.sqlite3")
    if temporary.exists():
        temporary.unlink()
    with closing(sqlite3.connect(temporary)) as connection:
        connection.execute(
            "CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        connection.execute(
            """
            CREATE TABLE chunks (
                id INTEGER PRIMARY KEY,
                path TEXT NOT NULL,
                title TEXT NOT NULL,
                kind TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding BLOB NOT NULL
            )
            """
        )
        connection.execute("CREATE INDEX chunks_path_idx ON chunks(path)")
        connection.executemany(
            """
            INSERT INTO chunks(path, title, kind, chunk_index, content, embedding)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["path"],
                    row["title"],
                    row["kind"],
                    row["chunk_index"],
                    row["content"],
                    to_blob(vector),
                )
                for row, vector in zip(chunks, vectors, strict=True)
            ],
        )
        metadata = {
            "model": settings.embedding_model,
            "url": settings.embedding_url,
            "dimension": str(len(vectors[0])),
            "updated_at": datetime.now().isoformat(timespec="minutes"),
        }
        connection.executemany(
            "INSERT INTO metadata(key, value) VALUES (?, ?)", metadata.items()
        )
        connection.commit()
    os.replace(temporary, VECTOR_DB_PATH)
    report(98, "正在提交向量索引")
    return {
        "path": VECTOR_DB_PATH.relative_to(settings.root).as_posix(),
        "documents": len({str(row["path"]) for row in chunks}),
        "chunks": len(chunks),
        "dimension": len(vectors[0]),
        "model": settings.embedding_model,
    }


def search(query: str, limit: int = 12) -> list[dict[str, object]]:
    if not VECTOR_DB_PATH.exists():
        raise RuntimeError("尚未建立向量索引")
    query_vector = normalize(embed_texts([query])[0])
    with closing(sqlite3.connect(VECTOR_DB_PATH)) as connection:
        rows = connection.execute(
            "SELECT path, title, kind, chunk_index, content, embedding FROM chunks"
        ).fetchall()
    scored: list[dict[str, object]] = []
    for path, title, kind, chunk_index, content, blob in rows:
        score = sum(
            left * right for left, right in zip(query_vector, from_blob(blob))
        )
        scored.append(
            {
                "path": str(path),
                "title": str(title),
                "kind": str(kind),
                "chunk_index": int(chunk_index),
                "snippet": str(content)[:420],
                "score": round(float(score), 4),
                "source": "semantic",
            }
        )
    scored.sort(key=lambda item: float(item["score"]), reverse=True)
    result: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in scored:
        path = str(item["path"])
        if path in seen:
            continue
        seen.add(path)
        result.append(item)
        if len(result) >= limit:
            break
    return result


def hybrid(
    query: str,
    keyword_rows: list[tuple[str, str, str, str]],
    limit: int,
) -> list[dict[str, object]]:
    semantic_rows = search(query, max(limit * 2, 20))
    merged: dict[str, dict[str, object]] = {}
    for rank, (path, title, kind, snippet) in enumerate(keyword_rows):
        merged[path] = {
            "path": path,
            "title": title,
            "kind": kind,
            "snippet": snippet,
            "score": 1 / (60 + rank),
            "source": "keyword",
        }
    for rank, item in enumerate(semantic_rows):
        path = str(item["path"])
        reciprocal = 1 / (60 + rank)
        if path in merged:
            merged[path]["score"] = float(merged[path]["score"]) + reciprocal
            merged[path]["source"] = "hybrid"
            merged[path]["semantic_score"] = item["score"]
        else:
            merged[path] = {
                **item,
                "score": reciprocal,
                "semantic_score": item["score"],
            }
    return sorted(
        merged.values(), key=lambda item: float(item["score"]), reverse=True
    )[:limit]
