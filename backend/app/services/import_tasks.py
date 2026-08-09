"""线程安全的进程内文档导入任务状态。"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Literal

from app.workflows.importing.state import ImportGraphState

ImportTaskStatus = Literal["queued", "processing", "completed", "failed"]
TERMINAL_STATUSES = {"completed", "failed"}


class ImportTaskStoreError(Exception):
    """任务不存在、重复或任务表容量不足。"""


@dataclass(frozen=True, slots=True)
class ImportTaskRecord:
    task_id: str
    filename: str
    file_path: Path
    file_dir: Path
    status: ImportTaskStatus = "queued"
    source_object_name: str = ""
    done_nodes: tuple[str, ...] = field(default_factory=tuple)
    running_node: str | None = None
    node_durations_ms: dict[str, float] = field(default_factory=dict)
    chunk_count: int = 0
    item_name: str = ""
    milvus_collection_name: str = ""
    error_node: str | None = None
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ImportTaskStore:
    """保存任务摘要；不保存正文和向量，避免内存随文档增大。"""

    def __init__(self, *, max_tasks: int = 1000) -> None:
        if max_tasks < 1:
            raise ValueError("max_tasks 必须大于 0")
        self.max_tasks = max_tasks
        self._tasks: OrderedDict[str, ImportTaskRecord] = OrderedDict()
        self._lock = RLock()

    def create(self, task_id: str, filename: str, file_path: Path) -> ImportTaskRecord:
        with self._lock:
            if task_id in self._tasks:
                raise ImportTaskStoreError("任务 ID 已存在")
            self._make_room()
            record = ImportTaskRecord(
                task_id=task_id,
                filename=filename,
                file_path=file_path,
                file_dir=file_path.parent,
            )
            self._tasks[task_id] = record
            return self._copy(record)

    def delete(self, task_id: str) -> None:
        with self._lock:
            self._tasks.pop(task_id, None)

    def mark_upload_completed(self, task_id: str, source_object_name: str) -> None:
        self._update(
            task_id,
            source_object_name=source_object_name,
            done_nodes=("upload_file",),
        )

    def mark_processing(self, task_id: str) -> None:
        self._update(task_id, status="processing", running_node=None)

    def mark_node_started(self, task_id: str, node_name: str) -> None:
        self._update(task_id, running_node=node_name)

    def mark_node_completed(self, task_id: str, node_name: str, duration_ms: float) -> None:
        with self._lock:
            current = self._require(task_id)
            done_nodes = current.done_nodes
            if node_name not in done_nodes:
                done_nodes = (*done_nodes, node_name)
            durations = dict(current.node_durations_ms)
            durations[node_name] = duration_ms
            self._replace(
                current,
                done_nodes=done_nodes,
                running_node=None,
                node_durations_ms=durations,
            )

    def mark_completed(self, task_id: str, state: ImportGraphState) -> None:
        chunks = state.get("chunks", [])
        self._update(
            task_id,
            status="completed",
            running_node=None,
            chunk_count=len(chunks) if isinstance(chunks, list) else 0,
            item_name=state.get("item_name", ""),
            milvus_collection_name=state.get("milvus_collection_name", ""),
            error_node=None,
            error_message=None,
        )

    def mark_failed(self, task_id: str, *, node_name: str | None, message: str) -> None:
        self._update(
            task_id,
            status="failed",
            running_node=None,
            error_node=node_name or None,
            error_message=message,
        )

    def get(self, task_id: str) -> ImportTaskRecord:
        with self._lock:
            return self._copy(self._require(task_id))

    def _update(self, task_id: str, **changes: object) -> None:
        with self._lock:
            self._replace(self._require(task_id), **changes)

    def _replace(self, current: ImportTaskRecord, **changes: object) -> None:
        updated = replace(current, updated_at=datetime.now(timezone.utc), **changes)
        self._tasks[current.task_id] = updated

    def _require(self, task_id: str) -> ImportTaskRecord:
        try:
            return self._tasks[task_id]
        except KeyError as exc:
            raise ImportTaskStoreError("导入任务不存在") from exc

    def _make_room(self) -> None:
        while len(self._tasks) >= self.max_tasks:
            terminal_id = next(
                (
                    task_id
                    for task_id, task in self._tasks.items()
                    if task.status in TERMINAL_STATUSES
                ),
                None,
            )
            if terminal_id is None:
                raise ImportTaskStoreError("当前正在处理的导入任务过多")
            del self._tasks[terminal_id]

    @staticmethod
    def _copy(record: ImportTaskRecord) -> ImportTaskRecord:
        return replace(record, node_durations_ms=dict(record.node_durations_ms))
