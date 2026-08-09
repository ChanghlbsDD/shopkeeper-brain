import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from minio import Minio

from app.core.config import Settings
from app.main import app
from app.services.import_files import ImportFileService, get_import_file_service
from app.services.import_tasks import ImportTaskStore
from app.workflows.importing.state import ImportGraphState, ImportProgressCallback

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INTEGRATION_TESTS") != "1",
        reason="set RUN_INTEGRATION_TESTS=1 to use the local Docker infrastructure",
    ),
]


def test_real_http_upload_archives_private_source_in_minio(tmp_path: Path) -> None:
    settings = Settings(import_storage_dir=tmp_path / "imports")
    store = ImportTaskStore(max_tasks=10)

    def runner(
        _path: str,
        *,
        file_dir: str = "",
        task_id: str = "",
        progress_callback: ImportProgressCallback | None = None,
    ) -> ImportGraphState:
        assert file_dir and task_id
        if progress_callback is not None:
            progress_callback("started", "entry_node", None)
            progress_callback("completed", "entry_node", 1.0)
        return {
            "chunks": [{"chunk_id": 1}],
            "item_name": "集成测试设备",
            "milvus_collection_name": "knowledge_chunks",
        }

    service = ImportFileService(settings, task_store=store, runner=runner)
    minio_client = Minio(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )
    task_id = ""
    app.dependency_overrides[get_import_file_service] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/imports",
                files={
                    "file": (
                        "integration-manual.md",
                        b"# Integration manual\n\nSynthetic content only.",
                        "text/markdown",
                    )
                },
            )
            task_id = response.json()["task_id"]
            status_response = client.get(f"/api/imports/{task_id}")

        task = store.get(task_id)
        metadata = minio_client.stat_object(
            settings.minio_bucket_name,
            task.source_object_name,
        )

        assert response.status_code == 202
        assert status_response.json()["status"] == "completed"
        assert metadata.size == len(b"# Integration manual\n\nSynthetic content only.")
    finally:
        app.dependency_overrides.pop(get_import_file_service, None)
        if task_id:
            task = store.get(task_id)
            if task.source_object_name:
                minio_client.remove_object(
                    settings.minio_bucket_name,
                    task.source_object_name,
                )
