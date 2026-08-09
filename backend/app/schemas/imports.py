"""文档导入 HTTP API 数据契约。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.services.import_tasks import ImportTaskRecord, ImportTaskStatus


class ImportAcceptedResponse(BaseModel):
    message: str
    task_id: str
    status: ImportTaskStatus
    filename: str
    status_url: str


class ImportTaskErrorResponse(BaseModel):
    node: str | None = None
    message: str


class ImportTaskResponse(BaseModel):
    task_id: str
    filename: str
    status: ImportTaskStatus
    done_nodes: list[str] = Field(default_factory=list)
    running_node: str | None = None
    node_durations_ms: dict[str, float] = Field(default_factory=dict)
    chunk_count: int = Field(default=0, ge=0)
    item_name: str = ""
    milvus_collection_name: str = ""
    error: ImportTaskErrorResponse | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_record(cls, record: ImportTaskRecord) -> ImportTaskResponse:
        error = None
        if record.error_message is not None:
            error = ImportTaskErrorResponse(
                node=record.error_node,
                message=record.error_message,
            )
        return cls(
            task_id=record.task_id,
            filename=record.filename,
            status=record.status,
            done_nodes=list(record.done_nodes),
            running_node=record.running_node,
            node_durations_ms=record.node_durations_ms,
            chunk_count=record.chunk_count,
            item_name=record.item_name,
            milvus_collection_name=record.milvus_collection_name,
            error=error,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
