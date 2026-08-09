"""从当前问题和历史消息中确认商品名称。"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from app.clients.qwen_chat import QwenChatClient, QwenChatError
from app.core.config import Settings, get_settings
from app.workflows.querying.base import BaseQueryNode
from app.workflows.querying.exceptions import ItemNameConfirmError, QueryValidationError
from app.workflows.querying.prompts import (
    ITEM_NAME_CONFIRM_SYSTEM_PROMPT,
    ITEM_NAME_CONFIRM_USER_PROMPT,
)
from app.workflows.querying.state import QueryGraphState, QueryHistoryMessage

ItemNameExtractor = Callable[[str, str], dict[str, Any]]


class ItemNameConfirmNode(BaseQueryNode):
    """调用通义千问提取商品名，并生成独立可检索问题。"""

    name = "item_name_confirm_node"

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        extractor: ItemNameExtractor | None = None,
    ) -> None:
        super().__init__()
        self.settings = settings or get_settings()
        self.extractor = extractor

    def process(self, state: QueryGraphState) -> Mapping[str, object]:
        original_query = state.get("original_query")
        if not isinstance(original_query, str) or not original_query.strip():
            raise QueryValidationError("用户问题不能为空", node_name=self.name)
        query = original_query.strip()
        history = state.get("history", [])
        history_text = self._format_history(history)

        try:
            raw_result = (self.extractor or self._extract_with_qwen)(query, history_text)
        except ItemNameConfirmError:
            raise
        except QwenChatError as exc:
            raise ItemNameConfirmError(
                str(exc),
                node_name=self.name,
                cause=exc,
            ) from exc
        except Exception as exc:
            raise ItemNameConfirmError(
                "商品名称确认服务调用失败",
                node_name=self.name,
                cause=exc,
            ) from exc

        return self._normalize_result(raw_result, fallback_query=query)

    def _extract_with_qwen(self, query: str, history_text: str) -> dict[str, Any]:
        client = QwenChatClient(
            base_url=self.settings.openai_api_base,
            api_key=self.settings.dashscope_api_key,
            model=self.settings.item_model,
            temperature=self.settings.llm_default_temperature,
            max_tokens=self.settings.query_item_name_max_output_tokens,
            timeout_seconds=self.settings.qwen_request_timeout_seconds,
        )
        return client.create_json_completion(
            system_prompt=ITEM_NAME_CONFIRM_SYSTEM_PROMPT,
            user_prompt=ITEM_NAME_CONFIRM_USER_PROMPT.format(
                history_text=history_text,
                query=query,
            ),
        )

    def _format_history(self, history: object) -> str:
        if not isinstance(history, list):
            raise QueryValidationError("历史消息格式无效", node_name=self.name)
        max_messages = self.settings.query_history_max_messages
        selected = history[-max_messages:] if max_messages else []
        lines: list[str] = []
        for message in selected:
            if not isinstance(message, dict):
                raise QueryValidationError("历史消息格式无效", node_name=self.name)
            typed_message: QueryHistoryMessage = message
            role = typed_message.get("role")
            content = typed_message.get("content")
            if role not in {"user", "assistant"} or not isinstance(content, str):
                raise QueryValidationError("历史消息字段无效", node_name=self.name)
            normalized_content = content.strip()
            if normalized_content:
                label = "用户" if role == "user" else "助手"
                lines.append(f"{label}：{normalized_content}")
        history_text = "\n".join(lines) or "（无）"
        return history_text[-self.settings.query_history_context_max_length :]

    def _normalize_result(
        self,
        result: object,
        *,
        fallback_query: str,
    ) -> dict[str, object]:
        if not isinstance(result, dict):
            raise ItemNameConfirmError("商品名称确认结果不是 JSON 对象", node_name=self.name)
        raw_names = result.get("item_names", [])
        if not isinstance(raw_names, list):
            raise ItemNameConfirmError("item_names 必须是数组", node_name=self.name)

        item_names: list[str] = []
        seen: set[str] = set()
        for raw_name in raw_names:
            if not isinstance(raw_name, str):
                continue
            name = raw_name.strip()
            key = name.casefold()
            if not name or key in seen:
                continue
            if len(name) > 200:
                raise ItemNameConfirmError("商品名称长度超过限制", node_name=self.name)
            seen.add(key)
            item_names.append(name)
            if len(item_names) >= self.settings.query_item_name_max_count:
                break

        raw_rewritten_query = result.get("rewritten_query")
        rewritten_query = (
            raw_rewritten_query.strip()
            if isinstance(raw_rewritten_query, str) and raw_rewritten_query.strip()
            else fallback_query
        )
        if len(rewritten_query) > 2000:
            raise ItemNameConfirmError("改写后的问题长度超过限制", node_name=self.name)
        return {
            "item_names": item_names,
            "rewritten_query": rewritten_query,
        }
