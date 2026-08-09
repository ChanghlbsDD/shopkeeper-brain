"""使用查询混合向量召回 Milvus 知识片段。"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from app.clients.milvus_search import (
    MilvusHybridSearcher,
    MilvusSearchError,
    MilvusSearchHit,
)
from app.core.config import Settings, get_settings
from app.workflows.querying.base import BaseQueryNode
from app.workflows.querying.exceptions import QuerySearchError, QueryValidationError
from app.workflows.querying.state import QueryGraphState

VectorSearcher = Callable[
    [list[float], dict[int, float], list[str], int],
    list[MilvusSearchHit],
]


class VectorSearchNode(BaseQueryNode):
    """按商品名过滤，并融合语义相似度与关键词相似度。"""

    name = "vector_search_node"

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        searcher: VectorSearcher | None = None,
    ) -> None:
        super().__init__()
        self.settings = settings or get_settings()
        self.searcher = searcher

    def process(self, state: QueryGraphState) -> Mapping[str, object]:
        dense_vector = state.get("query_dense_vector")
        sparse_vector = state.get("query_sparse_vector")
        item_names = state.get("item_names", [])
        limit = state.get("search_limit", self.settings.query_search_limit)
        if not isinstance(dense_vector, list) or not dense_vector:
            raise QueryValidationError("向量检索缺少稠密向量", node_name=self.name)
        if not isinstance(sparse_vector, dict) or not sparse_vector:
            raise QueryValidationError("向量检索缺少稀疏向量", node_name=self.name)
        if not isinstance(item_names, list) or not all(
            isinstance(name, str) for name in item_names
        ):
            raise QueryValidationError("向量检索商品名称格式无效", node_name=self.name)
        if not isinstance(limit, int) or isinstance(limit, bool):
            raise QueryValidationError("向量检索结果数量无效", node_name=self.name)

        try:
            if self.searcher is not None:
                results = self.searcher(dense_vector, sparse_vector, item_names, limit)
            else:
                results = MilvusHybridSearcher(self.settings).search(
                    dense_vector,
                    sparse_vector,
                    item_names=item_names,
                    limit=limit,
                )
        except QuerySearchError:
            raise
        except MilvusSearchError as exc:
            raise QuerySearchError(str(exc), node_name=self.name, cause=exc) from exc
        except Exception as exc:
            raise QuerySearchError(
                "知识片段检索失败",
                node_name=self.name,
                cause=exc,
            ) from exc
        return {"search_results": results}
