"""知识查询流程共享状态。"""

from __future__ import annotations

from copy import deepcopy
from typing import Literal, TypedDict

from app.clients.milvus_search import MilvusSearchHit


class QueryHistoryMessage(TypedDict):
    """参与商品指代消解的一条历史消息。"""

    role: Literal["user", "assistant"]
    content: str


class QueryGraphState(TypedDict, total=False):
    """在商品名确认、向量化和召回节点之间传递的数据。"""

    original_query: str
    history: list[QueryHistoryMessage]
    search_limit: int
    item_names: list[str]
    rewritten_query: str
    query_dense_vector: list[float]
    query_sparse_vector: dict[int, float]
    search_results: list[MilvusSearchHit]
    completed_nodes: list[str]
    node_durations_ms: dict[str, float]


DEFAULT_QUERY_STATE: QueryGraphState = {
    "original_query": "",
    "history": [],
    "search_limit": 5,
    "item_names": [],
    "rewritten_query": "",
    "query_dense_vector": [],
    "query_sparse_vector": {},
    "search_results": [],
    "completed_nodes": [],
    "node_durations_ms": {},
}


def create_query_state(
    original_query: str,
    *,
    history: list[QueryHistoryMessage] | None = None,
    search_limit: int = 5,
) -> QueryGraphState:
    """创建彼此隔离的查询初始状态。"""

    state = deepcopy(DEFAULT_QUERY_STATE)
    state.update(
        {
            "original_query": original_query,
            "history": deepcopy(history or []),
            "search_limit": search_limit,
        }
    )
    return state
