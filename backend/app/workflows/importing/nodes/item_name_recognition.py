"""使用通义千问识别文档描述的商品或设备名称。"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path

from app.clients.qwen_chat import QwenChatClient, QwenChatError
from app.core.config import get_settings
from app.workflows.importing.base import BaseNode
from app.workflows.importing.exceptions import ImportValidationError, ItemNameRecognitionError
from app.workflows.importing.prompts import ITEM_NAME_SYSTEM_PROMPT, ITEM_NAME_USER_PROMPT_TEMPLATE
from app.workflows.importing.state import DocumentChunk, ImportGraphState

ItemNameRecognizer = Callable[[str, str], str]
MAX_ITEM_NAME_LENGTH = 200


class ItemNameRecognitionNode(BaseNode):
    """选取少量前置 chunk 识别商品名，并无副作用地回填所有 chunk。"""

    name = "item_name_recognition_node"

    def __init__(
        self,
        *,
        recognizer: ItemNameRecognizer | None = None,
        chunk_count: int | None = None,
        context_max_length: int | None = None,
        backup_enabled: bool | None = None,
    ) -> None:
        super().__init__()
        self.recognizer = recognizer
        self.chunk_count = chunk_count
        self.context_max_length = context_max_length
        self.backup_enabled = backup_enabled

    def process(self, state: ImportGraphState) -> Mapping[str, object]:
        self.log_step("1/5", "校验文档标题、chunks 和上下文配置")
        file_title, chunks, chunk_count, context_max_length = self._validate_inputs(state)

        self.log_step("2/5", "从前置 chunks 构建有限长度上下文")
        context = self._prepare_context(chunks, chunk_count, context_max_length)

        self.log_step("3/5", "调用通义千问识别商品名称")
        try:
            item_name = (self.recognizer or self._recognize_with_qwen)(file_title, context)
        except QwenChatError as exc:
            raise ItemNameRecognitionError(
                str(exc),
                node_name=self.name,
                cause=exc,
            ) from exc

        item_name = self._normalize_item_name(item_name)
        if item_name.upper() == "UNKNOWN":
            item_name = file_title
            item_name_source = "file_title_fallback"
        else:
            item_name_source = "qwen"

        self.log_step("4/5", "把商品名称回填到所有 chunks")
        updated_chunks: list[DocumentChunk] = [
            {**chunk, "item_name": item_name} for chunk in chunks
        ]

        self.log_step("5/5", "按配置备份识别结果")
        backup_path = self._backup_chunks(state, updated_chunks)
        return {
            "item_name": item_name,
            "item_name_source": item_name_source,
            "item_name_chunks_path": str(backup_path) if backup_path else "",
            "chunks": updated_chunks,
        }

    def _validate_inputs(
        self,
        state: ImportGraphState,
    ) -> tuple[str, list[DocumentChunk], int, int]:
        file_title = state.get("file_title", "").strip()
        if not file_title:
            raise ImportValidationError("商品名识别缺少文档名称", node_name=self.name)

        chunks = state.get("chunks")
        if not isinstance(chunks, list) or not chunks:
            raise ImportValidationError("商品名识别缺少有效 chunks", node_name=self.name)
        if not all(isinstance(chunk, dict) for chunk in chunks):
            raise ImportValidationError("chunks 中包含无效元素", node_name=self.name)

        settings = get_settings()
        chunk_count = (
            settings.item_name_chunk_count if self.chunk_count is None else self.chunk_count
        )
        context_max_length = (
            settings.item_name_context_max_length
            if self.context_max_length is None
            else self.context_max_length
        )
        if chunk_count <= 0 or context_max_length < 32:
            raise ImportValidationError(
                "商品名上下文配置必须满足 chunk_count > 0 且 max_length >= 32",
                node_name=self.name,
            )
        return file_title, chunks, chunk_count, context_max_length

    def _prepare_context(
        self,
        chunks: list[DocumentChunk],
        chunk_count: int,
        max_length: int,
    ) -> str:
        blocks: list[str] = []
        used_length = 0
        for index, chunk in enumerate(chunks[:chunk_count], start=1):
            content = chunk.get("content", "")
            if not isinstance(content, str) or not content.strip():
                continue
            separator_length = 2 if blocks else 0
            prefix = f"【切片 {index}】\n"
            remaining = max_length - used_length - separator_length - len(prefix)
            if remaining <= 0:
                break
            block = prefix + content.strip()[:remaining]
            blocks.append(block)
            used_length += separator_length + len(block)
            if used_length >= max_length:
                break

        context = "\n\n".join(blocks)
        if not context:
            raise ImportValidationError("chunks 中没有可用于识别的正文", node_name=self.name)
        return context

    def _recognize_with_qwen(self, file_title: str, context: str) -> str:
        settings = get_settings()
        client = QwenChatClient(
            base_url=settings.openai_api_base,
            api_key=settings.dashscope_api_key,
            model=settings.item_model,
            temperature=settings.llm_default_temperature,
            max_tokens=settings.item_name_max_output_tokens,
            timeout_seconds=settings.qwen_request_timeout_seconds,
        )
        result = client.create_json_completion(
            system_prompt=ITEM_NAME_SYSTEM_PROMPT,
            user_prompt=ITEM_NAME_USER_PROMPT_TEMPLATE.format(
                file_title=file_title,
                context=context,
            ),
        )
        item_name = result.get("item_name")
        if not isinstance(item_name, str):
            raise QwenChatError("通义千问 JSON 缺少字符串字段 item_name")
        return item_name

    def _normalize_item_name(self, item_name: str) -> str:
        if not isinstance(item_name, str):
            raise ItemNameRecognitionError(
                "商品名称必须是字符串",
                node_name=self.name,
            )
        normalized = " ".join(item_name.strip().split())
        if not normalized:
            raise ItemNameRecognitionError("商品名称不能为空", node_name=self.name)
        if len(normalized) > MAX_ITEM_NAME_LENGTH:
            raise ItemNameRecognitionError(
                f"商品名称超过 {MAX_ITEM_NAME_LENGTH} 字符",
                node_name=self.name,
            )
        return normalized

    def _backup_chunks(
        self,
        state: ImportGraphState,
        chunks: list[DocumentChunk],
    ) -> Path | None:
        settings = get_settings()
        enabled = (
            settings.item_name_backup_enabled
            if self.backup_enabled is None
            else self.backup_enabled
        )
        if not enabled:
            return None

        md_path = Path(state.get("md_path", ""))
        if md_path.name:
            output_path = md_path.with_name(f"{md_path.stem}_item_name_chunks.json")
        else:
            output_directory = Path(state.get("file_dir", "") or ".")
            output_path = output_directory / "item_name_chunks.json"
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(chunks, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            self.logger.warning("Item name chunks backup failed: %s", type(exc).__name__)
            return None
        return output_path.resolve()
