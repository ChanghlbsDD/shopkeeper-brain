"""文档上传、原件归档和后台导入工作流编排。"""

from __future__ import annotations

import codecs
import logging
import shutil
from collections.abc import Callable
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from fastapi import UploadFile

from app.clients.minio_document_storage import (
    MinioDocumentStorage,
    MinioDocumentStorageError,
)
from app.core.config import REPOSITORY_ROOT, Settings, get_settings
from app.core.exceptions import AppError
from app.services.import_tasks import (
    ImportTaskRecord,
    ImportTaskStore,
    ImportTaskStoreError,
)
from app.workflows.importing import run_import_workflow
from app.workflows.importing.exceptions import ImportWorkflowError
from app.workflows.importing.state import (
    ImportGraphState,
    ImportProgressCallback,
    ImportProgressEvent,
)

logger = logging.getLogger(__name__)
ALLOWED_IMPORT_SUFFIXES = {".pdf", ".md", ".markdown"}
COPY_CHUNK_SIZE = 1024 * 1024


class ImportWorkflowRunner(Protocol):
    def __call__(
        self,
        import_file_path: str,
        *,
        file_dir: str = "",
        task_id: str = "",
        progress_callback: ImportProgressCallback | None = None,
    ) -> ImportGraphState: ...


DocumentArchiver = Callable[[Path, str], str]


class ImportFileService:
    """接收上传文件，并在响应返回后运行耗时导入流程。"""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        task_store: ImportTaskStore | None = None,
        runner: ImportWorkflowRunner = run_import_workflow,
        archiver: DocumentArchiver | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.task_store = task_store or ImportTaskStore(
            max_tasks=self.settings.import_task_retention
        )
        self.runner = runner
        self.archiver = archiver

    def accept_upload(self, upload: UploadFile) -> ImportTaskRecord:
        """校验上传、分块落盘并按配置归档到私有 MinIO。"""

        filename, suffix = self._validate_filename(upload.filename)
        task_id = uuid4().hex
        date_segment = datetime.now(timezone.utc).strftime("%Y%m%d")
        task_dir = self._storage_root() / date_segment / task_id
        source_path = task_dir / f"source{suffix}"

        try:
            self.task_store.create(task_id, filename, source_path)
        except ImportTaskStoreError as exc:
            raise AppError(
                "当前导入任务过多，请稍后重试",
                code="IMPORT_TASK_CAPACITY_REACHED",
                status_code=503,
            ) from exc

        source_object_name = ""
        try:
            task_dir.mkdir(parents=True, exist_ok=False)
            self._copy_and_validate(upload, source_path, suffix)
            if self.settings.import_source_archive_enabled:
                object_name = f"imports/{date_segment}/{task_id}/source{suffix}"
                source_object_name = self._archive(source_path, object_name)
            self.task_store.mark_upload_completed(task_id, source_object_name)
            return self.task_store.get(task_id)
        except AppError:
            self.task_store.delete(task_id)
            shutil.rmtree(task_dir, ignore_errors=True)
            raise
        except (OSError, MinioDocumentStorageError) as exc:
            self.task_store.delete(task_id)
            shutil.rmtree(task_dir, ignore_errors=True)
            logger.exception("Import upload storage failed: %s", task_id)
            raise AppError(
                "文件保存或原件归档失败",
                code="IMPORT_STORAGE_ERROR",
                status_code=503,
            ) from exc

    def run_task(self, task_id: str) -> None:
        """由 FastAPI 后台任务调用，并把节点进度写入任务表。"""

        try:
            task = self.task_store.get(task_id)
            self.task_store.mark_processing(task_id)
        except ImportTaskStoreError:
            logger.error("Import task disappeared before execution: %s", task_id)
            return

        def progress(
            event: ImportProgressEvent,
            node_name: str,
            duration_ms: float | None,
        ) -> None:
            if event == "started":
                self.task_store.mark_node_started(task_id, node_name)
            else:
                self.task_store.mark_node_completed(task_id, node_name, duration_ms or 0.0)

        try:
            state = self.runner(
                str(task.file_path),
                file_dir=str(task.file_dir),
                task_id=task_id,
                progress_callback=progress,
            )
        except ImportWorkflowError as exc:
            logger.exception("Import workflow failed: %s", task_id)
            self.task_store.mark_failed(
                task_id,
                node_name=exc.node_name,
                message=exc.message,
            )
        except Exception:
            logger.exception("Import workflow failed unexpectedly: %s", task_id)
            self.task_store.mark_failed(
                task_id,
                node_name=None,
                message="导入处理失败，请查看服务日志",
            )
        else:
            self.task_store.mark_completed(task_id, state)

    def get_task(self, task_id: str) -> ImportTaskRecord:
        try:
            return self.task_store.get(task_id)
        except ImportTaskStoreError as exc:
            raise AppError(
                "导入任务不存在或已过期",
                code="IMPORT_TASK_NOT_FOUND",
                status_code=404,
            ) from exc

    def _storage_root(self) -> Path:
        root = self.settings.import_storage_dir
        if not root.is_absolute():
            root = REPOSITORY_ROOT / root
        return root.resolve()

    def _archive(self, source_path: Path, object_name: str) -> str:
        if self.archiver is not None:
            return self.archiver(source_path, object_name)
        storage = MinioDocumentStorage(self.settings)
        return storage.upload(source_path, object_name)

    def _copy_and_validate(self, upload: UploadFile, target: Path, suffix: str) -> None:
        max_bytes = self.settings.import_max_file_size_mb * 1024 * 1024
        total_bytes = 0
        prefix = bytearray()
        decoder = codecs.getincrementaldecoder("utf-8")() if suffix != ".pdf" else None

        try:
            upload.file.seek(0)
            with target.open("xb") as output:
                while chunk := upload.file.read(COPY_CHUNK_SIZE):
                    if not isinstance(chunk, bytes):
                        raise AppError(
                            "上传内容格式无效",
                            code="INVALID_IMPORT_FILE",
                            status_code=400,
                        )
                    total_bytes += len(chunk)
                    if total_bytes > max_bytes:
                        raise AppError(
                            f"文件不能超过 {self.settings.import_max_file_size_mb} MB",
                            code="IMPORT_FILE_TOO_LARGE",
                            status_code=413,
                        )
                    if len(prefix) < 5:
                        prefix.extend(chunk[: 5 - len(prefix)])
                    if decoder is not None:
                        if b"\x00" in chunk:
                            raise UnicodeError("Markdown contains NUL")
                        decoder.decode(chunk)
                    output.write(chunk)
                if decoder is not None:
                    decoder.decode(b"", final=True)
        except UnicodeError as exc:
            raise AppError(
                "Markdown 文件必须是 UTF-8 纯文本",
                code="INVALID_MARKDOWN_ENCODING",
                status_code=400,
            ) from exc

        if total_bytes == 0:
            raise AppError("上传文件不能为空", code="EMPTY_IMPORT_FILE", status_code=400)
        if suffix == ".pdf" and not bytes(prefix).startswith(b"%PDF-"):
            raise AppError(
                "文件扩展名是 PDF，但内容不是有效 PDF",
                code="INVALID_PDF_FILE",
                status_code=400,
            )

    @staticmethod
    def _validate_filename(raw_filename: str | None) -> tuple[str, str]:
        filename = (raw_filename or "").replace("\\", "/").rsplit("/", 1)[-1].strip()
        if not filename or len(filename) > 255 or any(ord(char) < 32 for char in filename):
            raise AppError("上传文件名无效", code="INVALID_IMPORT_FILENAME", status_code=400)
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_IMPORT_SUFFIXES:
            raise AppError(
                "只支持 PDF、MD 或 Markdown 文件",
                code="UNSUPPORTED_IMPORT_FILE",
                status_code=415,
            )
        return filename, suffix


@lru_cache(maxsize=1)
def get_import_task_store() -> ImportTaskStore:
    settings = get_settings()
    return ImportTaskStore(max_tasks=settings.import_task_retention)


@lru_cache(maxsize=1)
def get_import_file_service() -> ImportFileService:
    return ImportFileService(task_store=get_import_task_store())
