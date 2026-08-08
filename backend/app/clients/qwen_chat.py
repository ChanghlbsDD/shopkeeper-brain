"""通义千问 OpenAI 兼容 Chat Completions 客户端。"""

from __future__ import annotations

import json
from typing import Any

import httpx


class QwenChatError(Exception):
    """通义千问配置、网络或响应格式异常。"""


class QwenChatClient:
    """发送结构化 JSON 请求，不依赖完整 OpenAI 或 LangChain 客户端。"""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        temperature: float = 0,
        max_tokens: int = 128,
        timeout_seconds: float = 60,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key.strip()
        self.model = model.strip()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.client = client

    def create_json_completion(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """调用 JSON mode，并把首个回答解析为字典。"""

        self._validate_configuration()
        request_body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        owns_client = self.client is None
        client = self.client or httpx.Client(timeout=self.timeout_seconds)
        try:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=request_body,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise QwenChatError("通义千问请求超时") from exc
        except httpx.HTTPStatusError as exc:
            raise QwenChatError(f"通义千问返回 HTTP {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise QwenChatError("无法连接通义千问 API") from exc
        finally:
            if owns_client:
                client.close()

        try:
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise QwenChatError("通义千问响应结构不完整") from exc
        if not isinstance(content, str) or not content.strip():
            raise QwenChatError("通义千问没有返回有效内容")

        normalized_content = self._strip_code_fence(content)
        try:
            result = json.loads(normalized_content)
        except json.JSONDecodeError as exc:
            raise QwenChatError("通义千问没有返回有效 JSON") from exc
        if not isinstance(result, dict):
            raise QwenChatError("通义千问 JSON 顶层必须是对象")
        return result

    def _validate_configuration(self) -> None:
        if not self.api_key:
            raise QwenChatError("DASHSCOPE_API_KEY 未配置")
        if not self.base_url.startswith(("https://", "http://")):
            raise QwenChatError("OPENAI_API_BASE 配置无效")
        if not self.model:
            raise QwenChatError("ITEM_MODEL 未配置")
        if self.max_tokens <= 0:
            raise QwenChatError("max_tokens 必须大于零")

    @staticmethod
    def _strip_code_fence(content: str) -> str:
        stripped = content.strip()
        if not stripped.startswith("```"):
            return stripped
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
