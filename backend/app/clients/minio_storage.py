"""MinIO 图片对象存储客户端。"""

from __future__ import annotations

import json
import mimetypes
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.parse import quote

from minio import Minio

from app.core.config import Settings, get_settings


class MinioImageStorageError(Exception):
    """MinIO 图片桶初始化或上传失败。"""


class MinioImageStorage:
    """把文档图片上传到独立的、只允许公开读取的 MinIO 桶。"""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        client: Any | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.bucket_name = self.settings.minio_image_bucket_name
        self.public_base_url = self.settings.minio_public_base_url.rstrip("/")
        self.client = client or Minio(
            endpoint=self.settings.minio_endpoint,
            access_key=self.settings.minio_access_key,
            secret_key=self.settings.minio_secret_key,
            secure=self.settings.minio_secure,
        )
        self._bucket_ready = False
        self._bucket_lock = Lock()

    def upload(self, image_path: Path, object_name: str) -> str:
        """上传一张图片并返回可以写入 Markdown 的公开 URL。"""

        if not image_path.is_file():
            raise MinioImageStorageError(f"待上传图片不存在：{image_path}")

        normalized_object_name = object_name.replace("\\", "/").lstrip("/")
        if not normalized_object_name or ".." in normalized_object_name.split("/"):
            raise MinioImageStorageError("MinIO 对象名称不合法")

        try:
            self._ensure_bucket()
            content_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
            self.client.fput_object(
                self.bucket_name,
                normalized_object_name,
                str(image_path),
                content_type=content_type,
            )
        except MinioImageStorageError:
            raise
        except Exception as exc:
            raise MinioImageStorageError(f"上传图片到 MinIO 失败：{image_path.name}") from exc

        bucket = quote(self.bucket_name, safe="")
        object_path = quote(normalized_object_name, safe="/")
        return f"{self.public_base_url}/{bucket}/{object_path}"

    def _ensure_bucket(self) -> None:
        if self._bucket_ready:
            return

        with self._bucket_lock:
            if self._bucket_ready:
                return
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
            if self.settings.minio_image_public_read:
                self.client.set_bucket_policy(
                    self.bucket_name,
                    json.dumps(self._public_read_policy(), ensure_ascii=False),
                )
            self._bucket_ready = True

    def _public_read_policy(self) -> dict[str, object]:
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{self.bucket_name}/*"],
                }
            ],
        }
