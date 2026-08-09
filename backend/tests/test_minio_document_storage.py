from pathlib import Path

import pytest

from app.clients.minio_document_storage import (
    MinioDocumentStorage,
    MinioDocumentStorageError,
)
from app.core.config import Settings


class FakeMinioClient:
    def __init__(self, *, bucket_exists: bool = False, fail_upload: bool = False) -> None:
        self._bucket_exists = bucket_exists
        self.fail_upload = fail_upload
        self.made_buckets: list[str] = []
        self.uploads: list[tuple[str, str, str, str]] = []

    def bucket_exists(self, _bucket_name: str) -> bool:
        return self._bucket_exists

    def make_bucket(self, bucket_name: str) -> None:
        self.made_buckets.append(bucket_name)

    def fput_object(
        self,
        bucket_name: str,
        object_name: str,
        source_path: str,
        *,
        content_type: str,
    ) -> None:
        if self.fail_upload:
            raise RuntimeError("storage unavailable")
        self.uploads.append((bucket_name, object_name, source_path, content_type))


def test_document_storage_creates_private_bucket_and_uploads(tmp_path: Path) -> None:
    source = tmp_path / "manual.md"
    source.write_text("# Manual", encoding="utf-8")
    client = FakeMinioClient()
    storage = MinioDocumentStorage(Settings(_env_file=None), client=client)

    result = storage.upload(source, "imports/20260809/task/source.md")

    assert result == "imports/20260809/task/source.md"
    assert client.made_buckets == ["shopkeeper-knowledge"]
    assert client.uploads == [
        (
            "shopkeeper-knowledge",
            "imports/20260809/task/source.md",
            str(source),
            "text/markdown",
        )
    ]
    assert not hasattr(client, "set_bucket_policy")


@pytest.mark.parametrize("object_name", ["", "../manual.md", "imports/../manual.md"])
def test_document_storage_rejects_invalid_object_name(
    tmp_path: Path,
    object_name: str,
) -> None:
    source = tmp_path / "manual.md"
    source.write_text("# Manual", encoding="utf-8")
    storage = MinioDocumentStorage(Settings(_env_file=None), client=FakeMinioClient())

    with pytest.raises(MinioDocumentStorageError):
        storage.upload(source, object_name)


def test_document_storage_wraps_upload_errors(tmp_path: Path) -> None:
    source = tmp_path / "manual.pdf"
    source.write_bytes(b"%PDF-test")
    storage = MinioDocumentStorage(
        Settings(_env_file=None),
        client=FakeMinioClient(fail_upload=True),
    )

    with pytest.raises(MinioDocumentStorageError, match="归档原始文档失败"):
        storage.upload(source, "imports/task/source.pdf")
