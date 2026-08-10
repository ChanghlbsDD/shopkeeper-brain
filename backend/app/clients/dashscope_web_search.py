"""阿里云百炼 WebSearch MCP 的轻量 Streamable HTTP 客户端。"""

from __future__ import annotations

import json
from collections.abc import Mapping
from contextlib import suppress
from typing import Any, TypedDict

import httpx


class WebSearchResult(TypedDict):
    """网页检索返回给查询工作流的安全字段。"""

    title: str
    url: str
    snippet: str


class DashScopeWebSearchError(Exception):
    """WebSearch MCP 配置、连接或响应格式异常。"""


class DashScopeWebSearchClient:
    """通过 MCP Streamable HTTP 调用 ``bailian_web_search``。"""

    protocol_version = "2025-06-18"

    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str,
        timeout_seconds: float = 60,
        client: httpx.Client | None = None,
    ) -> None:
        self.endpoint = endpoint.strip()
        self.api_key = api_key.strip()
        self.timeout_seconds = timeout_seconds
        self.client = client

    def search(self, query: str, *, count: int = 3) -> list[WebSearchResult]:
        """建立短 MCP 会话、执行网页搜索并关闭会话。"""

        normalized_query = query.strip()
        self._validate_configuration(normalized_query, count)
        owns_client = self.client is None
        client = self.client or httpx.Client(timeout=self.timeout_seconds)
        session_id = ""
        try:
            initialize_response = self._post(
                client,
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": self.protocol_version,
                        "capabilities": {},
                        "clientInfo": {"name": "shopkeeper-brain", "version": "0.1.0"},
                    },
                },
            )
            session_id = initialize_response.headers.get("Mcp-Session-Id", "")
            self._parse_json_rpc(initialize_response, expected_id=1)
            self._post_notification(
                client,
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                session_id=session_id,
            )
            tool_response = self._post(
                client,
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "bailian_web_search",
                        "arguments": {"query": normalized_query, "count": count},
                    },
                },
                session_id=session_id,
            )
            payload = self._parse_json_rpc(tool_response, expected_id=2)
            return self._parse_search_results(payload)
        except DashScopeWebSearchError:
            raise
        except httpx.TimeoutException as exc:
            raise DashScopeWebSearchError("网页检索请求超时") from exc
        except httpx.HTTPStatusError as exc:
            raise DashScopeWebSearchError(
                f"网页检索服务返回 HTTP {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise DashScopeWebSearchError("无法连接网页检索服务") from exc
        finally:
            if session_id:
                with suppress(httpx.HTTPError):
                    client.delete(self.endpoint, headers=self._headers(session_id=session_id))
            if owns_client:
                client.close()

    def _post(
        self,
        client: httpx.Client,
        body: dict[str, Any],
        *,
        session_id: str = "",
    ) -> httpx.Response:
        response = client.post(
            self.endpoint,
            headers=self._headers(body=body, session_id=session_id),
            json=body,
        )
        response.raise_for_status()
        return response

    def _post_notification(
        self,
        client: httpx.Client,
        body: dict[str, Any],
        *,
        session_id: str,
    ) -> None:
        response = self._post(client, body, session_id=session_id)
        if response.content:
            self._parse_json_rpc(response)

    def _headers(
        self,
        *,
        body: Mapping[str, Any] | None = None,
        session_id: str = "",
    ) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "MCP-Protocol-Version": self.protocol_version,
        }
        if session_id:
            headers["Mcp-Session-Id"] = session_id
        if body and isinstance(body.get("method"), str):
            headers["Mcp-Method"] = str(body["method"])
            params = body.get("params")
            if body["method"] == "tools/call" and isinstance(params, Mapping):
                name = params.get("name")
                if isinstance(name, str):
                    headers["Mcp-Name"] = name
        return headers

    @classmethod
    def _parse_json_rpc(
        cls,
        response: httpx.Response,
        *,
        expected_id: int | None = None,
    ) -> Mapping[str, Any]:
        try:
            if "text/event-stream" in response.headers.get("content-type", ""):
                messages = []
                for line in response.text.splitlines():
                    if line.startswith("data:"):
                        messages.append(json.loads(line[5:].strip()))
                payload = next(
                    (
                        message
                        for message in messages
                        if expected_id is None or message.get("id") == expected_id
                    ),
                    None,
                )
            else:
                payload = response.json()
        except (ValueError, json.JSONDecodeError) as exc:
            raise DashScopeWebSearchError("网页检索返回了无效 JSON") from exc
        if not isinstance(payload, Mapping):
            raise DashScopeWebSearchError("网页检索 MCP 响应结构不完整")
        if expected_id is not None and payload.get("id") != expected_id:
            raise DashScopeWebSearchError("网页检索 MCP 响应 ID 不匹配")
        if payload.get("error"):
            raise DashScopeWebSearchError("网页检索 MCP 调用失败")
        result = payload.get("result", {})
        if not isinstance(result, Mapping):
            raise DashScopeWebSearchError("网页检索 MCP 结果结构不完整")
        return result

    @staticmethod
    def _parse_search_results(result: Mapping[str, Any]) -> list[WebSearchResult]:
        if result.get("isError") is True:
            raise DashScopeWebSearchError("网页检索工具执行失败")
        content = result.get("content")
        if not isinstance(content, list) or not content:
            return []
        first = content[0]
        if not isinstance(first, Mapping) or not isinstance(first.get("text"), str):
            raise DashScopeWebSearchError("网页检索工具响应缺少文本")
        try:
            tool_payload = json.loads(first["text"])
        except json.JSONDecodeError as exc:
            raise DashScopeWebSearchError("网页检索工具文本不是有效 JSON") from exc
        pages = tool_payload.get("pages", []) if isinstance(tool_payload, Mapping) else []
        if not isinstance(pages, list):
            raise DashScopeWebSearchError("网页检索 pages 字段格式无效")

        results: list[WebSearchResult] = []
        for page in pages:
            if not isinstance(page, Mapping):
                continue
            title = page.get("title", "")
            url = page.get("url", "")
            snippet = page.get("snippet", "")
            if not all(isinstance(value, str) for value in (title, url, snippet)):
                continue
            if not url.startswith(("https://", "http://")):
                continue
            results.append({"title": title.strip(), "url": url.strip(), "snippet": snippet.strip()})
        return results

    def _validate_configuration(self, query: str, count: int) -> None:
        if not self.api_key:
            raise DashScopeWebSearchError("DASHSCOPE_API_KEY 未配置")
        if not self.endpoint.startswith(("https://", "http://")):
            raise DashScopeWebSearchError("MCP_DASHSCOPE_BASE_URL 配置无效")
        if not query:
            raise DashScopeWebSearchError("网页检索问题不能为空")
        if not 1 <= count <= 10:
            raise DashScopeWebSearchError("网页检索数量必须在 1 到 10 之间")
