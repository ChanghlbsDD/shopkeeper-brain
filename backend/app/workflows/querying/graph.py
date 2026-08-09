"""商品名确认、查询向量和 Milvus 召回 LangGraph 流程。"""

from __future__ import annotations

from typing import Literal, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.workflows.querying.base import BaseQueryNode
from app.workflows.querying.nodes import (
    ItemNameConfirmNode,
    QueryEmbeddingNode,
    VectorSearchNode,
)
from app.workflows.querying.state import (
    QueryGraphState,
    QueryHistoryMessage,
    create_query_state,
)

ITEM_NAME_CONFIRM_NODE = "item_name_confirm_node"
QUERY_EMBEDDING_NODE = "query_embedding_node"
VECTOR_SEARCH_NODE = "vector_search_node"


def route_after_item_name(
    state: QueryGraphState,
) -> Literal["search", "stop"]:
    """商品名已确认才继续检索，否则直接返回澄清或无法识别提示。"""

    status = state.get("query_status")
    if status == "confirmed":
        return "search"
    if status in {"needs_clarification", "unrecognized"}:
        return "stop"
    raise ValueError("商品名称确认节点没有设置有效查询状态")


def create_query_workflow(
    *,
    item_name_node: BaseQueryNode | None = None,
    embedding_node: BaseQueryNode | None = None,
    search_node: BaseQueryNode | None = None,
) -> CompiledStateGraph:
    """创建并编译当前阶段的顺序查询流程。"""

    graph = StateGraph(QueryGraphState)
    graph.add_node(ITEM_NAME_CONFIRM_NODE, item_name_node or ItemNameConfirmNode())
    graph.add_node(QUERY_EMBEDDING_NODE, embedding_node or QueryEmbeddingNode())
    graph.add_node(VECTOR_SEARCH_NODE, search_node or VectorSearchNode())
    graph.add_edge(START, ITEM_NAME_CONFIRM_NODE)
    graph.add_conditional_edges(
        ITEM_NAME_CONFIRM_NODE,
        route_after_item_name,
        {"search": QUERY_EMBEDDING_NODE, "stop": END},
    )
    graph.add_edge(QUERY_EMBEDDING_NODE, VECTOR_SEARCH_NODE)
    graph.add_edge(VECTOR_SEARCH_NODE, END)
    return graph.compile()


query_workflow = create_query_workflow()


def run_query_workflow(
    original_query: str,
    *,
    history: list[QueryHistoryMessage] | None = None,
    search_limit: int = 5,
) -> QueryGraphState:
    """运行一次同步知识召回流程。"""

    initial_state = create_query_state(
        original_query,
        history=history,
        search_limit=search_limit,
    )
    return cast(QueryGraphState, query_workflow.invoke(initial_state))
