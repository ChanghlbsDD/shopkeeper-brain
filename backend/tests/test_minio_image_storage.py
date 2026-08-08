import json
from pathlib import Path

import pytest

from app.clients.minio_storage import MinioImageStorage, MinioImageStorageError
from app.core.config import Settings


class FakeMinioClient:
    def __init__(self, *, bucket_exists: bool = False) -> None:
        self.existing_bucket = bucket_exists
        self.made_buckets: list[str] = []
        self.policies: list[tuple[str, str]] = []
        self.uploads: list[tuple[str, str, str, str]] = []

    def bucket_exists(self, bucket_name: str) -> bool:
        return self.existing_bucket

    def make_bucket(self, bucket_name: str) -> None:
        self.made_buckets.append(bucket_name)
        self.existing_bucket = True

    def set_bucket_policy(self, bucket_name: str, policy: str) -> None:
        self.policies.append((bucket_name, policy))

    def fput_object(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str,
        *,
        content_type: str,
    ) -> None:
        self.uploads.append((bucket_name, object_name, file_path, content_type))


def create_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "minio_image_bucket_name": "test-images",
        "minio_public_base_url": "https://assets.example.com/",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_upload_creates_public_read_bucket_and_returns_encoded_url(tmp_path: Path) -> None:
    image_path = tmp_path / "商品 图.png"
    image_path.write_bytes(b"png")
    client = FakeMinioClient()
    storage = MinioImageStorage(create_settings(), client=client)

    url = storage.upload(image_path, "documents/商品手册/商品 图.png")

    assert client.made_buckets == ["test-images"]
    assert len(client.policies) == 1
    policy = json.loads(client.policies[0][1])
    assert policy["Statement"][0]["Action"] == ["s3:GetObject"]
    assert client.uploads == [
        (
            "test-images",
            "documents/商品手册/商品 图.png",
            str(image_path),
            "image/png",
        )
    ]
    assert url == (
        "https://assets.example.com/test-images/"
        "documents/%E5%95%86%E5%93%81%E6%89%8B%E5%86%8C/"
        "%E5%95%86%E5%93%81%20%E5%9B%BE.png"
    )


def test_bucket_is_initialized_only_once_for_multiple_uploads(tmp_path: Path) -> None:
    first = tmp_path / "first.jpg"
    second = tmp_path / "second.jpg"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    client = FakeMinioClient(bucket_exists=True)
    storage = MinioImageStorage(create_settings(), client=client)

    storage.upload(first, "documents/manual/first.jpg")
    storage.upload(second, "documents/manual/second.jpg")

    assert client.made_buckets == []
    assert len(client.policies) == 1
    assert len(client.uploads) == 2


def test_private_bucket_skips_public_policy(tmp_path: Path) -> None:
    image_path = tmp_path / "private.webp"
    image_path.write_bytes(b"webp")
    client = FakeMinioClient(bucket_exists=True)
    settings = create_settings(minio_image_public_read=False)

    MinioImageStorage(settings, client=client).upload(image_path, "private.webp")

    assert client.policies == []


def test_upload_wraps_minio_failure(tmp_path: Path) -> None:
    image_path = tmp_path / "failed.png"
    image_path.write_bytes(b"png")
    client = FakeMinioClient(bucket_exists=True)

    def failed_upload(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("connection failed")

    client.fput_object = failed_upload  # type: ignore[method-assign]

    with pytest.raises(MinioImageStorageError, match="上传图片到 MinIO 失败"):
        MinioImageStorage(create_settings(), client=client).upload(image_path, "failed.png")
