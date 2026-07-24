from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    root: Path = ROOT
    embedding_url: str = os.getenv(
        "KB_EMBEDDING_URL", "http://192.168.70.249:8000/v1"
    ).rstrip("/")
    embedding_model: str = os.getenv(
        "KB_EMBEDDING_MODEL", "./models/Qwen3-VL-Embedding-2B"
    )
    embedding_api_key: str = os.getenv("KB_EMBEDDING_API_KEY", "")
    upload_limit_mb: int = int(os.getenv("KB_UPLOAD_LIMIT_MB", "100"))
    vector_batch_size: int = int(os.getenv("KB_VECTOR_BATCH_SIZE", "16"))
    vector_chunk_chars: int = int(os.getenv("KB_VECTOR_CHUNK_CHARS", "1800"))
    vector_chunk_overlap: int = int(os.getenv("KB_VECTOR_CHUNK_OVERLAP", "240"))


settings = Settings()
