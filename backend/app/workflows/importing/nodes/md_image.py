"""上传 Markdown 本地图片并替换图片链接。"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol
from urllib.parse import unquote, urlsplit

from app.clients.minio_storage import MinioImageStorage, MinioImageStorageError
from app.workflows.importing.base import BaseNode
from app.workflows.importing.exceptions import ImportValidationError, MarkdownImageError
from app.workflows.importing.state import ImportGraphState

MARKDOWN_IMAGE_PATTERN = re.compile(
    r"!\[(?P<alt>[^\]]*)\]\("
    r"(?P<target><[^>]+>|[^\s)]+)"
    r"(?P<title>\s+(?:\"[^\"]*\"|'[^']*'))?"
    r"\)"
)
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


class ImageUploader(Protocol):
    """图片上传器所需的最小接口，便于隔离节点测试。"""

    def upload(self, image_path: Path, object_name: str) -> str: ...


class MarkdownImageNode(BaseNode):
    """只上传 Markdown 实际引用的本地图片，并生成非破坏性的处理结果。"""

    name = "md_img_node"

    def __init__(self, *, storage: ImageUploader | None = None) -> None:
        super().__init__()
        self.storage = storage

    def process(self, state: ImportGraphState) -> Mapping[str, object]:
        self.log_step("1/4", "读取并校验 Markdown")
        markdown_path = self._validate_markdown(state)
        markdown_content = self._read_markdown(markdown_path)

        self.log_step("2/4", "定位 Markdown 引用的本地图片")
        local_images = self._collect_local_images(markdown_content, markdown_path.parent)
        if not local_images:
            self.log_step("3/4", "未发现本地图片，跳过 MinIO 上传")
            self.log_step("4/4", "写回 Markdown 内容")
            return {"md_content": markdown_content, "uploaded_image_urls": {}}

        self.log_step("3/4", f"上传 {len(local_images)} 张图片到 MinIO")
        document_key = self._document_key(state, markdown_path)
        uploaded_urls = self._upload_images(local_images, markdown_path.parent, document_key)
        replaced_content = self._replace_targets(markdown_content, uploaded_urls)

        self.log_step("4/4", "保存链接替换后的 Markdown")
        processed_path = markdown_path.with_name(
            f"{markdown_path.stem}_images{markdown_path.suffix}"
        )
        try:
            processed_path.write_text(replaced_content, encoding="utf-8")
        except OSError as exc:
            raise MarkdownImageError(
                f"无法保存图片链接处理结果：{processed_path}",
                node_name=self.name,
                cause=exc,
            ) from exc

        return {
            "md_path": str(processed_path.resolve()),
            "md_content": replaced_content,
            "uploaded_image_urls": uploaded_urls,
        }

    def _validate_markdown(self, state: ImportGraphState) -> Path:
        raw_path = state.get("md_path", "").strip()
        if not raw_path:
            raise ImportValidationError("Markdown 路径不能为空", node_name=self.name)

        markdown_path = Path(raw_path).expanduser()
        if markdown_path.suffix.lower() not in {".md", ".markdown"}:
            raise ImportValidationError(
                f"图片处理节点不支持该文件类型：{markdown_path.suffix or '无扩展名'}",
                node_name=self.name,
            )
        if not markdown_path.is_file():
            raise ImportValidationError(
                f"Markdown 文件不存在：{markdown_path}",
                node_name=self.name,
            )
        return markdown_path.resolve()

    def _read_markdown(self, markdown_path: Path) -> str:
        try:
            return markdown_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise MarkdownImageError(
                f"无法读取 UTF-8 Markdown：{markdown_path}",
                node_name=self.name,
                cause=exc,
            ) from exc

    def _collect_local_images(
        self,
        markdown_content: str,
        markdown_directory: Path,
    ) -> dict[str, Path]:
        images: dict[str, Path] = {}
        base_directory = markdown_directory.resolve()

        for match in MARKDOWN_IMAGE_PATTERN.finditer(markdown_content):
            raw_target = match.group("target")
            target = unquote(raw_target.strip("<>"))
            if self._is_remote_target(target):
                continue
            candidate = Path(target)
            if candidate.is_absolute():
                raise MarkdownImageError(
                    f"不允许上传 Markdown 目录外的绝对路径：{target}",
                    node_name=self.name,
                )

            image_path = (base_directory / candidate).resolve()
            try:
                image_path.relative_to(base_directory)
            except ValueError as exc:
                raise MarkdownImageError(
                    f"图片路径超出 Markdown 目录：{target}",
                    node_name=self.name,
                    cause=exc,
                ) from exc

            if image_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
                raise MarkdownImageError(
                    f"不支持的本地图片格式：{target}",
                    node_name=self.name,
                )
            if not image_path.is_file():
                raise MarkdownImageError(
                    f"Markdown 引用的图片不存在：{target}",
                    node_name=self.name,
                )
            images.setdefault(raw_target, image_path)

        return images

    @staticmethod
    def _is_remote_target(target: str) -> bool:
        if re.match(r"^[A-Za-z]:[\\/]", target):
            return False
        parsed = urlsplit(target)
        return bool(parsed.scheme or parsed.netloc or target.startswith(("//", "#")))

    def _upload_images(
        self,
        local_images: dict[str, Path],
        markdown_directory: Path,
        document_key: str,
    ) -> dict[str, str]:
        storage = self.storage or MinioImageStorage()
        uploaded_by_path: dict[Path, str] = {}
        uploaded_urls: dict[str, str] = {}

        for target, image_path in local_images.items():
            if image_path not in uploaded_by_path:
                relative_path = image_path.relative_to(markdown_directory).as_posix()
                object_name = f"documents/{document_key}/{relative_path}"
                try:
                    uploaded_by_path[image_path] = storage.upload(image_path, object_name)
                except MinioImageStorageError as exc:
                    raise MarkdownImageError(
                        str(exc),
                        node_name=self.name,
                        cause=exc,
                    ) from exc
            uploaded_urls[target] = uploaded_by_path[image_path]

        return uploaded_urls

    @staticmethod
    def _replace_targets(markdown_content: str, uploaded_urls: dict[str, str]) -> str:
        def replace(match: re.Match[str]) -> str:
            target = match.group("target")
            if target not in uploaded_urls:
                return match.group(0)
            title = match.group("title") or ""
            return f"![{match.group('alt')}]({uploaded_urls[target]}{title})"

        return MARKDOWN_IMAGE_PATTERN.sub(replace, markdown_content)

    @staticmethod
    def _document_key(state: ImportGraphState, markdown_path: Path) -> str:
        title = state.get("file_title", "").strip() or markdown_path.stem
        safe_title = re.sub(r"[^\w.-]+", "-", title, flags=re.UNICODE).strip("-._")
        digest = hashlib.sha256(str(markdown_path).encode("utf-8")).hexdigest()[:10]
        return f"{safe_title[:80] or 'document'}-{digest}"
