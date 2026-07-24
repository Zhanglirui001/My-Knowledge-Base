from __future__ import annotations

import difflib
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import settings


CHANGES_DIR = settings.root / "90_System" / "Agent" / "changes"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _plan_path(plan_id: str) -> Path:
    return CHANGES_DIR / f"{plan_id}.json"


def create_plan(
    kind: str,
    title: str,
    summary: str,
    operations: list[dict[str, Any]],
) -> dict[str, Any]:
    CHANGES_DIR.mkdir(parents=True, exist_ok=True)
    plan = {
        "id": uuid.uuid4().hex[:12],
        "kind": kind,
        "title": title,
        "summary": summary,
        "status": "pending",
        "created_at": _now(),
        "applied_at": None,
        "operations": operations,
    }
    _plan_path(str(plan["id"])).write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return plan


def create_text_plan(target: Path, content: str, title: str, summary: str) -> dict[str, Any]:
    before = target.read_text(encoding="utf-8", errors="replace") if target.exists() else ""
    diff = "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            content.splitlines(keepends=True),
            fromfile=f"a/{target.relative_to(settings.root).as_posix()}",
            tofile=f"b/{target.relative_to(settings.root).as_posix()}",
        )
    )
    operation = {
        "type": "write",
        "target": target.relative_to(settings.root).as_posix(),
        "content": content,
        "diff": diff,
        "expected_mtime_ns": target.stat().st_mtime_ns if target.exists() else None,
    }
    return create_plan("text-write", title, summary, [operation])


def get_plan(plan_id: str) -> dict[str, Any]:
    path = _plan_path(plan_id)
    if not path.exists():
        raise KeyError(plan_id)
    return json.loads(path.read_text(encoding="utf-8"))


def save_plan(plan: dict[str, Any]) -> None:
    _plan_path(str(plan["id"])).write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def reject_plan(plan: dict[str, Any]) -> None:
    if plan.get("status") != "pending":
        raise RuntimeError("该变更计划已经处理")
    plan["status"] = "rejected"
    plan["rejected_at"] = _now()
    save_plan(plan)

def list_plans(limit: int = 30) -> list[dict[str, Any]]:
    if not CHANGES_DIR.exists():
        return []
    plans = []
    for path in sorted(
        CHANGES_DIR.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True
    )[:limit]:
        try:
            plans.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return plans


def apply_text_plan(plan: dict[str, Any]) -> list[str]:
    if plan.get("status") != "pending":
        raise RuntimeError("该变更计划已经处理")
    outputs: list[str] = []
    for operation in plan.get("operations", []):
        if operation.get("type") != "write":
            raise RuntimeError("计划包含不支持的操作")
        target = (settings.root / str(operation["target"])).resolve()
        target.relative_to(settings.root)
        expected = operation.get("expected_mtime_ns")
        current = target.stat().st_mtime_ns if target.exists() else None
        if current != expected:
            raise RuntimeError(f"目标文件在审批期间已变化：{operation['target']}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(operation["content"]).rstrip() + "\n", encoding="utf-8")
        outputs.append(str(operation["target"]))
    plan["status"] = "applied"
    plan["applied_at"] = _now()
    save_plan(plan)
    return outputs

