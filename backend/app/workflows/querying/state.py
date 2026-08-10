"""知识查询流程共享状态。"""

from __future__ import annotations

import operator
from copy import deepcopy
from typing import Annotated, Literal, TypedDict

from app.clients.dashscope_web_search import WebSearchResult
from app.clients.milvus_search import MilvusSearchHit


def merge_node_durations(left: dict[str, float], right: dict[str, float]) -> dict[str, float]:
    """合并并行节点各自写入的耗时。"""

    return {**left, **right}


class QueryHistoryMessage(TypedDict):
    """参与商品指代消解的一条历史消息。"""

    role: Literal["user", "assistant"]
    content: str


class RrfSearchHit(TypedDict):
    """直接检索与 HyDE 按名次融合后的本地知识片段。"""

    chunk_id: int
    rrf_score: float
    source_paths: list[Literal["vector", "hyde"]]
    content: str
    title: str
    parent_title: str
    file_title: str
    item_name: str
    part: int | None


class QueryGraphState(TypedDict, total=False):
    """在商品名确认、向量化和三路召回节点之间传递的数据。"""

    original_query: str
    history: list[QueryHistoryMessage]
    search_limit: int
    query_status: Literal["pending", "confirmed", "needs_clarification", "unrecognized"]
    extracted_item_names: list[str]
    item_names: list[str]
    item_name_options: list[str]
    clarification: str
    rewritten_query: str
    query_dense_vector: list[float]
    query_sparse_vector: dict[int, float]
    search_results: list[MilvusSearchHit]
    hyde_status: Literal["pending", "disabled", "succeeded", "failed"]
    hyde_document: str
    hyde_search_results: list[MilvusSearchHit]
    rrf_results: list[RrfSearchHit]
    web_search_status: Literal["pending", "disabled", "succeeded", "failed"]
    web_search_results: list[WebSearchResult]
    completed_nodes: Annotated[list[str], operator.add]
    node_durations_ms: Annotated[dict[str, float], merge_node_durations]


DEFAULT_QUERY_STATE: QueryGraphState = {
    "original_query": "",
    "history": [],
    "search_limit": 5,
    "query_status": "pending",
    "extracted_item_names": [],
    "item_names": [],
    "item_name_options": [],
    "clarification": "",
    "rewritten_query": "",
    "query_dense_vector": [],
    "query_sparse_vector": {},
    "search_results": [],
    "hyde_status": "pending",
    "hyde_document": "",
    "hyde_search_results": [],
    "rrf_results": [],
    "web_search_status": "pending",
    "web_search_results": [],
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
