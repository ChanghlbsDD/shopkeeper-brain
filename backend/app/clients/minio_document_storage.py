"""把用户上传的原始文档归档到私有 MinIO 桶。"""

from __future__ import annotations

import mimetypes
from pathlib import Path
from threading import Lock
from typing import Any

from minio import Minio

from app.core.config import Settings, get_settings


class MinioDocumentStorageError(Exception):
    """原始文档桶初始化或上传失败。"""


class MinioDocumentStorage:
    """将原始 PDF/Markdown 文件归档到默认私有知识桶。"""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        client: Any | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.bucket_name = self.settings.minio_bucket_name
        self.client = client or Minio(
            endpoint=self.settings.minio_endpoint,
            access_key=self.settings.minio_access_key,
            secret_key=self.settings.minio_secret_key,
            secure=self.settings.minio_secure,
        )
        self._bucket_ready = False
        self._bucket_lock = Lock()

    def upload(self, source_path: Path, object_name: str) -> str:
        """上传原始文档并返回桶内对象名，不生成公开访问地址。"""

        if not source_path.is_file():
            raise MinioDocumentStorageError(f"待归档文档不存在：{source_path.name}")

        normalized_name = object_name.replace("\\", "/").lstrip("/")
        if not normalized_name or ".." in normalized_name.split("/"):
            raise MinioDocumentStorageError("MinIO 文档对象名称不合法")

        try:
            self._ensure_bucket()
            content_type = {
                ".md": "text/markdown",
                ".markdown": "text/markdown",
                ".pdf": "application/pdf",
            }.get(source_path.suffix.lower())
            content_type = content_type or mimetypes.guess_type(source_path.name)[0]
            content_type = content_type or "application/octet-stream"
            self.client.fput_object(
                self.bucket_name,
                normalized_name,
                str(source_path),
                content_type=content_type,
            )
        except MinioDocumentStorageError:
            raise
        except Exception as exc:
            raise MinioDocumentStorageError(f"归档原始文档失败：{source_path.name}") from exc
        return normalized_name

    def _ensure_bucket(self) -> None:
        if self._bucket_ready:
            return
        with self._bucket_lock:
            if self._bucket_ready:
                return
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
            self._bucket_ready = True
