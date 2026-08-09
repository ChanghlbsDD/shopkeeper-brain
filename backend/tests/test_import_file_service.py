from io import BytesIO
from pathlib import Path

import pytest
from fastapi import UploadFile

from app.clients.minio_document_storage import MinioDocumentStorageError
from app.core.config import Settings
from app.core.exceptions import AppError
from app.services.import_files import ImportFileService
from app.services.import_tasks import ImportTaskStore, ImportTaskStoreError
from app.workflows.importing.exceptions import ImportValidationError
from app.workflows.importing.state import ImportGraphState, ImportProgressCallback


def upload(filename: str, content: bytes) -> UploadFile:
    return UploadFile(file=BytesIO(content), filename=filename)


def settings(tmp_path: Path, **overrides: object) -> Settings:
    values: dict[str, object] = {
        "import_storage_dir": tmp_path / "imports",
        "import_source_archive_enabled": False,
    }
    values.update(overrides)
    return Settings(
        _env_file=None,
        **values,
    )


def successful_runner(
    _import_file_path: str,
    *,
    file_dir: str = "",
    task_id: str = "",
    progress_callback: ImportProgressCallback | None = None,
) -> ImportGraphState:
    assert file_dir
    assert task_id
    if progress_callback is not None:
        progress_callback("started", "entry_node", None)
        progress_callback("completed", "entry_node", 3.5)
    return {
        "chunks": [{"chunk_id": 100, "content": "test"}],
        "item_name": "RS-12 数字万用表",
        "milvus_collection_name": "knowledge_chunks",
    }


def test_accept_upload_saves_safe_markdown_and_marks_upload_done(tmp_path: Path) -> None:
    store = ImportTaskStore(max_tasks=10)
    service = ImportFileService(settings(tmp_path), task_store=store)

    task = service.accept_upload(upload("../../产品手册.MD", "# 产品手册".encode()))

    assert task.filename == "产品手册.MD"
    assert task.file_path.name == "source.md"
    assert task.file_path.read_text(encoding="utf-8") == "# 产品手册"
    assert task.file_path.is_relative_to(tmp_path / "imports")
    assert task.done_nodes == ("upload_file",)
    assert task.status == "queued"


def test_accept_upload_archives_to_task_scoped_private_object(tmp_path: Path) -> None:
    archived: list[tuple[Path, str]] = []

    def archiver(source_path: Path, object_name: str) -> str:
        archived.append((source_path, object_name))
        return object_name

    service = ImportFileService(
        settings(tmp_path, import_source_archive_enabled=True),
        task_store=ImportTaskStore(max_tasks=10),
        archiver=archiver,
    )

    task = service.accept_upload(upload("manual.pdf", b"%PDF-1.7 test"))

    assert archived[0][0] == task.file_path
    assert archived[0][1].endswith(f"/{task.task_id}/source.pdf")
    assert task.source_object_name == archived[0][1]


@pytest.mark.parametrize(
    ("filename", "content", "code"),
    [
        ("manual.txt", b"text", "UNSUPPORTED_IMPORT_FILE"),
        ("manual.md", b"", "EMPTY_IMPORT_FILE"),
        ("manual.pdf", b"not a pdf", "INVALID_PDF_FILE"),
        ("manual.md", b"\xff\xfe", "INVALID_MARKDOWN_ENCODING"),
        ("manual.md", b"text\x00binary", "INVALID_MARKDOWN_ENCODING"),
    ],
)
def test_accept_upload_rejects_invalid_files(
    tmp_path: Path,
    filename: str,
    content: bytes,
    code: str,
) -> None:
    service = ImportFileService(
        settings(tmp_path),
        task_store=ImportTaskStore(max_tasks=10),
    )

    with pytest.raises(AppError) as captured:
        service.accept_upload(upload(filename, content))

    assert captured.value.code == code
    assert list((tmp_path / "imports").rglob("source.*")) == []


def test_accept_upload_enforces_streamed_size_limit(tmp_path: Path) -> None:
    service = ImportFileService(
        settings(tmp_path, import_max_file_size_mb=1),
        task_store=ImportTaskStore(max_tasks=10),
    )

    with pytest.raises(AppError) as captured:
        service.accept_upload(upload("large.md", b"a" * (1024 * 1024 + 1)))

    assert captured.value.status_code == 413
    assert captured.value.code == "IMPORT_FILE_TOO_LARGE"


def test_accept_upload_cleans_local_task_when_archive_fails(tmp_path: Path) -> None:
    store = ImportTaskStore(max_tasks=10)

    def broken_archiver(_source_path: Path, _object_name: str) -> str:
        raise MinioDocumentStorageError("offline")

    service = ImportFileService(
        settings(tmp_path, import_source_archive_enabled=True),
        task_store=store,
        archiver=broken_archiver,
    )

    with pytest.raises(AppError) as captured:
        service.accept_upload(upload("manual.md", b"# Manual"))

    assert captured.value.code == "IMPORT_STORAGE_ERROR"
    assert list((tmp_path / "imports").rglob("source.*")) == []


def test_run_task_tracks_nodes_and_only_keeps_result_summary(tmp_path: Path) -> None:
    store = ImportTaskStore(max_tasks=10)
    service = ImportFileService(
        settings(tmp_path),
        task_store=store,
        runner=successful_runner,
    )
    accepted = service.accept_upload(upload("manual.md", b"# Manual"))

    service.run_task(accepted.task_id)
    task = service.get_task(accepted.task_id)

    assert task.status == "completed"
    assert task.done_nodes == ("upload_file", "entry_node")
    assert task.node_durations_ms == {"entry_node": 3.5}
    assert task.chunk_count == 1
    assert task.item_name == "RS-12 数字万用表"
    assert task.milvus_collection_name == "knowledge_chunks"


def test_run_task_exposes_known_workflow_error_without_cause(tmp_path: Path) -> None:
    def broken_runner(
        _path: str,
        **_kwargs: object,
    ) -> ImportGraphState:
        raise ImportValidationError("文档没有有效内容", node_name="document_split_node")

    service = ImportFileService(
        settings(tmp_path),
        task_store=ImportTaskStore(max_tasks=10),
        runner=broken_runner,
    )
    accepted = service.accept_upload(upload("manual.md", b"# Manual"))

    service.run_task(accepted.task_id)
    task = service.get_task(accepted.task_id)

    assert task.status == "failed"
    assert task.error_node == "document_split_node"
    assert task.error_message == "文档没有有效内容"


def test_run_task_hides_unexpected_exception_details(tmp_path: Path) -> None:
    def broken_runner(_path: str, **_kwargs: object) -> ImportGraphState:
        raise RuntimeError("secret internal path")

    service = ImportFileService(
        settings(tmp_path),
        task_store=ImportTaskStore(max_tasks=10),
        runner=broken_runner,
    )
    accepted = service.accept_upload(upload("manual.md", b"# Manual"))

    service.run_task(accepted.task_id)
    task = service.get_task(accepted.task_id)

    assert task.status == "failed"
    assert task.error_message == "导入处理失败，请查看服务日志"
    assert "secret" not in task.error_message


def test_get_task_maps_missing_record_to_not_found(tmp_path: Path) -> None:
    service = ImportFileService(
        settings(tmp_path),
        task_store=ImportTaskStore(max_tasks=10),
    )

    with pytest.raises(AppError) as captured:
        service.get_task("missing")

    assert captured.value.status_code == 404
    assert captured.value.code == "IMPORT_TASK_NOT_FOUND"


def test_run_task_ignores_record_removed_before_background_execution(tmp_path: Path) -> None:
    store = ImportTaskStore(max_tasks=10)
    service = ImportFileService(settings(tmp_path), task_store=store)

    service.run_task("missing")

    with pytest.raises(ImportTaskStoreError):
        store.get("missing")
