from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app
from app.services.import_files import ImportFileService, get_import_file_service
from app.services.import_tasks import ImportTaskStore
from app.workflows.importing.state import ImportGraphState, ImportProgressCallback


def api_runner(
    _import_file_path: str,
    *,
    file_dir: str = "",
    task_id: str = "",
    progress_callback: ImportProgressCallback | None = None,
) -> ImportGraphState:
    assert file_dir and task_id
    if progress_callback is not None:
        progress_callback("started", "entry_node", None)
        progress_callback("completed", "entry_node", 1.25)
        progress_callback("started", "import_milvus_node", None)
        progress_callback("completed", "import_milvus_node", 2.75)
    return {
        "chunks": [{"chunk_id": 42, "dense_vector": [0.1, 0.2]}],
        "item_name": "RS-12 数字万用表",
        "milvus_collection_name": "knowledge_chunks",
    }


@pytest.fixture
def import_service(tmp_path: Path) -> ImportFileService:
    return ImportFileService(
        Settings(
            _env_file=None,
            import_storage_dir=tmp_path / "imports",
            import_source_archive_enabled=False,
        ),
        task_store=ImportTaskStore(max_tasks=10),
        runner=api_runner,
    )


def test_upload_returns_202_and_status_endpoint_returns_summary(
    import_service: ImportFileService,
) -> None:
    app.dependency_overrides[get_import_file_service] = lambda: import_service
    try:
        with TestClient(app) as client:
            upload_response = client.post(
                "/api/imports",
                files={"file": ("产品手册.md", "# 产品手册".encode(), "text/markdown")},
            )
            task_id = upload_response.json()["task_id"]
            status_response = client.get(f"/api/imports/{task_id}")
    finally:
        app.dependency_overrides.pop(get_import_file_service, None)

    assert upload_response.status_code == 202
    assert upload_response.json() == {
        "message": "文件已接收，正在后台导入",
        "task_id": task_id,
        "status": "queued",
        "filename": "产品手册.md",
        "status_url": f"/api/imports/{task_id}",
    }
    assert status_response.status_code == 200
    payload = status_response.json()
    assert payload["status"] == "completed"
    assert payload["done_nodes"] == ["upload_file", "entry_node", "import_milvus_node"]
    assert payload["node_durations_ms"] == {
        "entry_node": 1.25,
        "import_milvus_node": 2.75,
    }
    assert payload["chunk_count"] == 1
    assert payload["item_name"] == "RS-12 数字万用表"
    assert payload["milvus_collection_name"] == "knowledge_chunks"
    assert "file_path" not in payload
    assert "chunks" not in payload


def test_upload_rejects_unsupported_file_with_unified_error(
    import_service: ImportFileService,
) -> None:
    app.dependency_overrides[get_import_file_service] = lambda: import_service
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/imports",
                files={"file": ("manual.exe", b"binary", "application/octet-stream")},
            )
    finally:
        app.dependency_overrides.pop(get_import_file_service, None)

    assert response.status_code == 415
    assert response.json() == {
        "error": {
            "code": "UNSUPPORTED_IMPORT_FILE",
            "message": "只支持 PDF、MD 或 Markdown 文件",
        }
    }


def test_unknown_import_task_returns_404(import_service: ImportFileService) -> None:
    app.dependency_overrides[get_import_file_service] = lambda: import_service
    try:
        with TestClient(app) as client:
            response = client.get("/api/imports/not-found")
    finally:
        app.dependency_overrides.pop(get_import_file_service, None)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "IMPORT_TASK_NOT_FOUND"


def test_openapi_describes_multipart_upload_and_task_status() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    upload = schema["paths"]["/api/imports"]["post"]
    assert "multipart/form-data" in upload["requestBody"]["content"]
    assert "202" in upload["responses"]
    assert "/api/imports/{task_id}" in schema["paths"]
