from __future__ import annotations

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable


ProgressReporter = Callable[[int, str], None]
TaskWork = Callable[[ProgressReporter], Any]


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass
class TaskRecord:
    id: str
    kind: str
    title: str
    status: str = "queued"
    progress: int = 0
    message: str = "等待执行"
    created_at: str = field(default_factory=now)
    started_at: str | None = None
    finished_at: str | None = None
    result: Any = None
    error: str | None = None


class TaskManager:
    def __init__(self, workers: int = 2) -> None:
        self._records: dict[str, TaskRecord] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="kb-task")

    def submit(self, kind: str, title: str, work: TaskWork) -> dict[str, Any]:
        task = TaskRecord(id=uuid.uuid4().hex[:12], kind=kind, title=title)
        with self._lock:
            self._records[task.id] = task
        self._executor.submit(self._run, task.id, work)
        return self.get(task.id)

    def _run(self, task_id: str, work: TaskWork) -> None:
        self._update(task_id, status="running", started_at=now(), message="正在开始")

        def report(progress: int, message: str) -> None:
            self._update(task_id, progress=max(0, min(99, progress)), message=message)

        try:
            result = work(report)
            self._update(
                task_id,
                status="completed",
                progress=100,
                message="已完成",
                result=result,
                finished_at=now(),
            )
        except Exception as exc:
            self._update(
                task_id,
                status="failed",
                message="执行失败",
                error=str(exc),
                finished_at=now(),
            )

    def _update(self, task_id: str, **values: Any) -> None:
        with self._lock:
            task = self._records[task_id]
            for key, value in values.items():
                setattr(task, key, value)

    def get(self, task_id: str) -> dict[str, Any]:
        with self._lock:
            task = self._records.get(task_id)
            if not task:
                raise KeyError(task_id)
            return asdict(task)

    def list(self, limit: int = 30) -> list[dict[str, Any]]:
        with self._lock:
            tasks = sorted(
                self._records.values(), key=lambda item: item.created_at, reverse=True
            )
            return [asdict(task) for task in tasks[:limit]]


tasks = TaskManager()
