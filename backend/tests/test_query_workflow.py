import pytest

from app.clients.dashscope_embedding import TextEmbedding
from app.workflows.querying.graph import create_query_workflow, route_after_item_name
from app.workflows.querying.nodes import (
    ItemNameConfirmNode,
    QueryEmbeddingNode,
    VectorSearchNode,
)
from app.workflows.querying.state import create_query_state


def test_query_workflow_runs_confirmation_embedding_and_search_in_order() -> None:
    workflow = create_query_workflow(
        item_name_node=ItemNameConfirmNode(
            extractor=lambda _query, _history: {
                "item_names": ["RS-12 数字万用表"],
                "rewritten_query": "RS-12 数字万用表如何测量直流电压？",
            },
            aligner=lambda _names: (["RS-12 数字万用表"], []),
        ),
        embedding_node=QueryEmbeddingNode(
            embedder=lambda _query: TextEmbedding([0.1, 0.2], {7: 0.8})
        ),
        search_node=VectorSearchNode(
            searcher=lambda _dense, _sparse, _names, _limit: [
                {
                    "chunk_id": 42,
                    "score": 0.91,
                    "content": "将量程旋钮转到直流电压档。",
                    "title": "直流电压测量",
                    "parent_title": "测量",
                    "file_title": "RS-12 手册",
                    "item_name": "RS-12 数字万用表",
                    "part": 1,
                }
            ]
        ),  # type: ignore[arg-type]
    )

    result = workflow.invoke(create_query_state("它怎么测直流电压？", search_limit=3))

    assert result["completed_nodes"] == [
        "item_name_confirm_node",
        "query_embedding_node",
        "vector_search_node",
    ]
    assert result["item_names"] == ["RS-12 数字万用表"]
    assert result["query_status"] == "confirmed"
    assert result["query_dense_vector"] == [0.1, 0.2]
    assert result["search_results"][0]["chunk_id"] == 42
    assert set(result["node_durations_ms"]) == set(result["completed_nodes"])


def test_query_workflow_stops_before_embedding_when_name_needs_clarification() -> None:
    workflow = create_query_workflow(
        item_name_node=ItemNameConfirmNode(
            extractor=lambda _query, _history: {
                "item_names": ["RS 万用表"],
                "rewritten_query": "RS 万用表如何测量电压？",
            },
            aligner=lambda _names: (
                [],
                ["RS-12 数字万用表", "RS-13 数字万用表"],
            ),
        ),
        embedding_node=QueryEmbeddingNode(
            embedder=lambda _query: (_ for _ in ()).throw(
                AssertionError("clarification must skip embedding")
            )
        ),
    )

    result = workflow.invoke(create_query_state("RS 万用表怎么测电压？"))

    assert result["query_status"] == "needs_clarification"
    assert result["item_name_options"] == [
        "RS-12 数字万用表",
        "RS-13 数字万用表",
    ]
    assert result["completed_nodes"] == ["item_name_confirm_node"]
    assert result["query_dense_vector"] == []
    assert result["search_results"] == []


def test_route_rejects_missing_decision_status() -> None:
    with pytest.raises(ValueError, match="有效查询状态"):
        route_after_item_name(create_query_state("问题"))
