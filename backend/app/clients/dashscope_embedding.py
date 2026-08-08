"""阿里云百炼原生文本向量 HTTP 客户端。"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

import httpx


class DashScopeEmbeddingError(Exception):
    """百炼向量配置、网络或响应格式异常。"""


@dataclass(frozen=True)
class TextEmbedding:
    """一段文本对应的稠密向量和稀疏向量。"""

    dense_vector: list[float]
    sparse_vector: dict[int, float]


class DashScopeEmbeddingClient:
    """批量获取文本的稠密和稀疏向量，不在本机加载 AI 模型。"""

    endpoint_path = "/services/embeddings/text-embedding/text-embedding"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        dimension: int = 1024,
        max_batch_size: int = 10,
        timeout_seconds: float = 60,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key.strip()
        self.model = model.strip()
        self.dimension = dimension
        self.max_batch_size = max_batch_size
        self.timeout_seconds = timeout_seconds
        self.client = client

    def embed_documents(self, texts: list[str]) -> list[TextEmbedding]:
        """以 document 类型向量化一批底库文本。"""

        normalized_texts = self._validate_inputs(texts)
        request_body = {
            "model": self.model,
            "input": {"texts": normalized_texts},
            "parameters": {
                "text_type": "document",
                "dimension": self.dimension,
                "output_type": "dense&sparse",
            },
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        owns_client = self.client is None
        client = self.client or httpx.Client(timeout=self.timeout_seconds)
        try:
            response = client.post(
                f"{self.base_url}{self.endpoint_path}",
                headers=headers,
                json=request_body,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise DashScopeEmbeddingError("百炼向量请求超时") from exc
        except httpx.HTTPStatusError as exc:
            raise DashScopeEmbeddingError(
                f"百炼向量接口返回 HTTP {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise DashScopeEmbeddingError("无法连接百炼向量 API") from exc
        finally:
            if owns_client:
                client.close()

        try:
            payload = response.json()
        except ValueError as exc:
            raise DashScopeEmbeddingError("百炼向量接口没有返回有效 JSON") from exc
        return self._parse_embeddings(payload, expected_count=len(normalized_texts))

    def _validate_inputs(self, texts: list[str]) -> list[str]:
        if not self.api_key:
            raise DashScopeEmbeddingError("DASHSCOPE_API_KEY 未配置")
        if not self.base_url.startswith(("https://", "http://")):
            raise DashScopeEmbeddingError("DASHSCOPE_API_BASE 配置无效")
        if not self.model:
            raise DashScopeEmbeddingError("EMBEDDING_MODEL 未配置")
        if self.dimension <= 0:
            raise DashScopeEmbeddingError("EMBEDDING_DIMENSION 必须大于零")
        if self.max_batch_size <= 0:
            raise DashScopeEmbeddingError("EMBEDDING_BATCH_SIZE 必须大于零")
        if not isinstance(texts, list) or not texts:
            raise DashScopeEmbeddingError("向量化文本不能为空")
        if len(texts) > self.max_batch_size:
            raise DashScopeEmbeddingError(
                f"单批文本数不能超过 EMBEDDING_BATCH_SIZE={self.max_batch_size}"
            )

        normalized: list[str] = []
        for text in texts:
            if not isinstance(text, str) or not text.strip():
                raise DashScopeEmbeddingError("向量化文本必须是非空字符串")
            normalized.append(text.strip())
        return normalized

    def _parse_embeddings(
        self,
        payload: Any,
        *,
        expected_count: int,
    ) -> list[TextEmbedding]:
        try:
            raw_embeddings = payload["output"]["embeddings"]
        except (KeyError, TypeError) as exc:
            raise DashScopeEmbeddingError("百炼向量响应结构不完整") from exc
        if not isinstance(raw_embeddings, list) or len(raw_embeddings) != expected_count:
            raise DashScopeEmbeddingError("百炼向量数量与输入文本数量不一致")

        ordered: list[TextEmbedding | None] = [None] * expected_count
        for raw_embedding in raw_embeddings:
            if not isinstance(raw_embedding, dict):
                raise DashScopeEmbeddingError("百炼向量响应包含无效元素")
            text_index = raw_embedding.get("text_index")
            if (
                not isinstance(text_index, int)
                or isinstance(text_index, bool)
                or not 0 <= text_index < expected_count
                or ordered[text_index] is not None
            ):
                raise DashScopeEmbeddingError("百炼向量响应中的 text_index 无效")

            dense_vector = self._parse_dense_vector(raw_embedding.get("embedding"))
            sparse_vector = self._parse_sparse_vector(raw_embedding.get("sparse_embedding"))
            ordered[text_index] = TextEmbedding(dense_vector, sparse_vector)

        if any(embedding is None for embedding in ordered):
            raise DashScopeEmbeddingError("百炼向量响应缺少输入文本对应结果")
        return [embedding for embedding in ordered if embedding is not None]

    def _parse_dense_vector(self, raw_vector: Any) -> list[float]:
        if not isinstance(raw_vector, list) or len(raw_vector) != self.dimension:
            raise DashScopeEmbeddingError(f"百炼稠密向量维度不是配置值 {self.dimension}")
        try:
            vector = [float(value) for value in raw_vector]
        except (TypeError, ValueError) as exc:
            raise DashScopeEmbeddingError("百炼稠密向量包含无效数值") from exc
        if not all(isfinite(value) for value in vector):
            raise DashScopeEmbeddingError("百炼稠密向量包含非有限数值")
        return vector

    @staticmethod
    def _parse_sparse_vector(raw_vector: Any) -> dict[int, float]:
        if not isinstance(raw_vector, list) or not raw_vector:
            raise DashScopeEmbeddingError("百炼没有返回稀疏向量")

        vector: dict[int, float] = {}
        for item in raw_vector:
            if not isinstance(item, dict):
                raise DashScopeEmbeddingError("百炼稀疏向量包含无效元素")
            index = item.get("index")
            value = item.get("value")
            if (
                not isinstance(index, int)
                or isinstance(index, bool)
                or index < 0
                or index in vector
            ):
                raise DashScopeEmbeddingError("百炼稀疏向量索引无效")
            try:
                numeric_value = float(value)
            except (TypeError, ValueError) as exc:
                raise DashScopeEmbeddingError("百炼稀疏向量权重无效") from exc
            if not isfinite(numeric_value):
                raise DashScopeEmbeddingError("百炼稀疏向量包含非有限数值")
            vector[index] = numeric_value
        return vector
