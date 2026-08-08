"""使用 MinerU 云端 API 把 PDF 转换为 Markdown。"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

from app.clients.mineru_api import MinerUApiClient, MinerUApiError
from app.core.config import get_settings
from app.workflows.importing.base import BaseNode
from app.workflows.importing.exceptions import ImportValidationError, PdfConversionError
from app.workflows.importing.state import ImportGraphState

PdfConverter = Callable[[Path, Path], Path]


class PdfToMarkdownNode(BaseNode):
    """校验 PDF 和输出目录，调用 MinerU API 并返回 Markdown 路径。"""

    name = "pdf_to_md_node"

    def __init__(
        self,
        *,
        converter: PdfConverter | None = None,
    ) -> None:
        super().__init__()
        self.converter = converter

    def process(self, state: ImportGraphState) -> Mapping[str, object]:
        self.log_step("1/4", "校验 PDF 与输出目录")
        pdf_path = self._validate_pdf(state)
        output_directory = self._prepare_output_directory(state)

        self.log_step("2/4", "上传 PDF 到 MinerU API")
        try:
            markdown_path = (self.converter or self._create_api_client().convert)(
                pdf_path,
                output_directory,
            )
        except MinerUApiError as exc:
            raise PdfConversionError(
                str(exc),
                node_name=self.name,
                cause=exc,
            ) from exc

        self.log_step("3/4", "下载并解压 MinerU 结果")
        if not markdown_path.is_file():
            raise PdfConversionError("MinerU API 没有生成 Markdown 文件", node_name=self.name)
        self.log_step("4/4", "写回 Markdown 路径")
        return {
            "md_path": str(markdown_path.resolve()),
            "is_md_read_enabled": True,
        }

    def _validate_pdf(self, state: ImportGraphState) -> Path:
        raw_path = state.get("pdf_path", "").strip()
        if not raw_path:
            raise ImportValidationError("PDF 路径不能为空", node_name=self.name)

        pdf_path = Path(raw_path).expanduser()
        if pdf_path.suffix.lower() != ".pdf":
            raise ImportValidationError(
                f"PDF 转换节点不支持该文件类型：{pdf_path.suffix or '无扩展名'}",
                node_name=self.name,
            )
        if not pdf_path.is_file():
            raise ImportValidationError(
                f"PDF 文件不存在：{pdf_path}",
                node_name=self.name,
            )
        return pdf_path.resolve()

    def _prepare_output_directory(self, state: ImportGraphState) -> Path:
        raw_directory = state.get("file_dir", "").strip()
        if not raw_directory:
            raise ImportValidationError("MinerU 输出目录不能为空", node_name=self.name)

        output_directory = Path(raw_directory).expanduser()
        if output_directory.exists() and not output_directory.is_dir():
            raise ImportValidationError(
                f"MinerU 输出路径不是目录：{output_directory}",
                node_name=self.name,
            )
        output_directory.mkdir(parents=True, exist_ok=True)
        return output_directory.resolve()

    def _create_api_client(self) -> MinerUApiClient:
        settings = get_settings()
        return MinerUApiClient(
            base_url=settings.mineru_base_url,
            token=settings.mineru_api_token,
            model_version=settings.mineru_model_version,
            request_timeout_seconds=settings.mineru_request_timeout_seconds,
            poll_interval_seconds=settings.mineru_poll_interval_seconds,
            task_timeout_seconds=settings.mineru_task_timeout_seconds,
        )
