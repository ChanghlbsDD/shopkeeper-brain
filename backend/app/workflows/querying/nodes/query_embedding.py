"""为独立查询生成稠密和稀疏向量。"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from app.clients.dashscope_embedding import (
    DashScopeEmbeddingClient,
    DashScopeEmbeddingError,
    TextEmbedding,
)
from app.core.config import Settings, get_settings
from app.workflows.querying.base import BaseQueryNode
from app.workflows.querying.exceptions import QueryEmbeddingError, QueryValidationError
from app.workflows.querying.state import QueryGraphState

QueryEmbedder = Callable[[str], TextEmbedding]


class QueryEmbeddingNode(BaseQueryNode):
    """使用百炼 query 模式生成与底库同维度的混合向量。"""

    name = "query_embedding_node"

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        embedder: QueryEmbedder | None = None,
    ) -> None:
        super().__init__()
        self.settings = settings or get_settings()
        self.embedder = embedder

    def process(self, state: QueryGraphState) -> Mapping[str, object]:
        rewritten_query = state.get("rewritten_query")
        if not isinstance(rewritten_query, str) or not rewritten_query.strip():
            raise QueryValidationError("查询向量化缺少有效问题", node_name=self.name)
        query = rewritten_query.strip()
        try:
            embedding = (self.embedder or self._embed_with_dashscope)(query)
        except QueryEmbeddingError:
            raise
        except DashScopeEmbeddingError as exc:
            raise QueryEmbeddingError(str(exc), node_name=self.name, cause=exc) from exc
        except Exception as exc:
            raise QueryEmbeddingError(
                "查询向量生成失败",
                node_name=self.name,
                cause=exc,
            ) from exc
        return {
            "query_dense_vector": embedding.dense_vector,
            "query_sparse_vector": embedding.sparse_vector,
        }

    def _embed_with_dashscope(self, query: str) -> TextEmbedding:
        client = DashScopeEmbeddingClient(
            base_url=self.settings.dashscope_api_base,
            api_key=self.settings.dashscope_api_key,
            model=self.settings.embedding_model,
            dimension=self.settings.embedding_dimension,
            max_batch_size=self.settings.embedding_batch_size,
            timeout_seconds=self.settings.embedding_request_timeout_seconds,
        )
        return client.embed_queries([query])[0]
