"""商品名确认、查询向量和 Milvus 召回 LangGraph 流程。"""

from __future__ import annotations

from typing import cast

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
    graph.add_edge(ITEM_NAME_CONFIRM_NODE, QUERY_EMBEDDING_NODE)
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
