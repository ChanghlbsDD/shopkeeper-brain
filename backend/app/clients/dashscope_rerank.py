"""阿里云百炼文本重排 HTTP 客户端。"""

from __future__ import annotations

from collections.abc import Mapping
from math import isfinite
from typing import Any

import httpx


class DashScopeRerankError(Exception):
    """百炼重排配置、网络或响应结构异常。"""


class DashScopeRerankClient:
    """调用 gte-rerank-v2 或 qwen3-rerank，并恢复为输入顺序的分数列表。"""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 60,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key.strip()
        self.model = model.strip()
        self.timeout_seconds = timeout_seconds
        self.client = client

    def rerank(self, query: str, documents: list[str]) -> list[float]:
        """返回与输入 documents 一一对应的相关性分数。"""

        normalized_query = query.strip()
        normalized_documents = [document.strip() for document in documents]
        self._validate(normalized_query, normalized_documents)
        if self.model == "qwen3-rerank":
            endpoint = f"{self.base_url}/reranks"
            body: dict[str, Any] = {
                "model": self.model,
                "query": normalized_query,
                "documents": normalized_documents,
                "top_n": len(normalized_documents),
            }
        else:
            endpoint = f"{self.base_url}/services/rerank/text-rerank/text-rerank"
            body = {
                "model": self.model,
                "input": {"query": normalized_query, "documents": normalized_documents},
                "parameters": {
                    "return_documents": False,
                    "top_n": len(normalized_documents),
                },
            }
        owns_client = self.client is None
        client = self.client or httpx.Client(timeout=self.timeout_seconds)
        try:
            response = client.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise DashScopeRerankError("百炼重排请求超时") from exc
        except httpx.HTTPStatusError as exc:
            raise DashScopeRerankError(f"百炼重排返回 HTTP {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise DashScopeRerankError("无法连接百炼重排 API") from exc
        finally:
            if owns_client:
                client.close()
        try:
            payload = response.json()
        except ValueError as exc:
            raise DashScopeRerankError("百炼重排返回了无效 JSON") from exc
        return self._parse_scores(payload, document_count=len(normalized_documents))

    def _validate(self, query: str, documents: list[str]) -> None:
        if not self.api_key:
            raise DashScopeRerankError("DASHSCOPE_API_KEY 未配置")
        if not self.base_url.startswith(("https://", "http://")):
            raise DashScopeRerankError("RERANK_API_BASE 配置无效")
        if not self.model:
            raise DashScopeRerankError("RERANK_MODEL 未配置")
        if not query:
            raise DashScopeRerankError("重排问题不能为空")
        if not documents or any(not document for document in documents):
            raise DashScopeRerankError("重排文档不能为空")
        if len(documents) > 500:
            raise DashScopeRerankError("重排文档数量超过 500")

    @staticmethod
    def _parse_scores(payload: object, *, document_count: int) -> list[float]:
        if not isinstance(payload, Mapping):
            raise DashScopeRerankError("百炼重排响应结构不完整")
        raw_results = payload.get("results")
        if raw_results is None:
            output = payload.get("output")
            raw_results = output.get("results") if isinstance(output, Mapping) else None
        if not isinstance(raw_results, list):
            raise DashScopeRerankError("百炼重排响应缺少 results")

        scores: list[float | None] = [None] * document_count
        for raw_result in raw_results:
            if not isinstance(raw_result, Mapping):
                raise DashScopeRerankError("百炼重排结果格式无效")
            index = raw_result.get("index")
            score = raw_result.get("relevance_score")
            if (
                not isinstance(index, int)
                or isinstance(index, bool)
                or not 0 <= index < document_count
                or scores[index] is not None
            ):
                raise DashScopeRerankError("百炼重排结果索引无效")
            try:
                numeric_score = float(score)
            except (TypeError, ValueError) as exc:
                raise DashScopeRerankError("百炼重排分数无效") from exc
            if not isfinite(numeric_score) or not 0 <= numeric_score <= 1:
                raise DashScopeRerankError("百炼重排分数超出范围")
            scores[index] = numeric_score
        if any(score is None for score in scores):
            raise DashScopeRerankError("百炼重排没有返回全部文档分数")
        return [float(score) for score in scores]
