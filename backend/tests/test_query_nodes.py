from typing import Any

import pytest

from app.clients.dashscope_embedding import TextEmbedding
from app.core.config import Settings
from app.workflows.querying.exceptions import (
    ItemNameConfirmError,
    QueryValidationError,
)
from app.workflows.querying.nodes import (
    ItemNameConfirmNode,
    QueryEmbeddingNode,
    VectorSearchNode,
)
from app.workflows.querying.state import create_query_state


def test_item_name_node_uses_recent_history_and_normalizes_result() -> None:
    captured: dict[str, str] = {}

    def extractor(query: str, history_text: str) -> dict[str, Any]:
        captured["query"] = query
        captured["history"] = history_text
        return {
            "item_names": [" RS-12 数字万用表 ", "rs-12 数字万用表", ""],
            "rewritten_query": " RS-12 数字万用表如何测量直流电压？ ",
        }

    node = ItemNameConfirmNode(
        settings=Settings(
            _env_file=None,
            query_history_max_messages=2,
            query_history_context_max_length=500,
        ),
        extractor=extractor,
    )
    state = create_query_state(
        "它怎么测直流电压？",
        history=[
            {"role": "user", "content": "较早消息"},
            {"role": "assistant", "content": "这是 RS-12 数字万用表。"},
            {"role": "user", "content": "好的。"},
        ],
    )

    result = node(state)

    assert captured["query"] == "它怎么测直流电压？"
    assert "较早消息" not in captured["history"]
    assert "RS-12 数字万用表" in captured["history"]
    assert result["item_names"] == ["RS-12 数字万用表"]
    assert result["rewritten_query"] == "RS-12 数字万用表如何测量直流电压？"
    assert result["completed_nodes"] == ["item_name_confirm_node"]


def test_item_name_node_falls_back_to_original_query() -> None:
    node = ItemNameConfirmNode(
        settings=Settings(_env_file=None),
        extractor=lambda _query, _history: {
            "item_names": [],
            "rewritten_query": " ",
        },
    )

    result = node(create_query_state("万用表怎么测量电压？"))

    assert result["item_names"] == []
    assert result["rewritten_query"] == "万用表怎么测量电压？"


def test_item_name_node_rejects_invalid_llm_shape() -> None:
    node = ItemNameConfirmNode(
        settings=Settings(_env_file=None),
        extractor=lambda _query, _history: {"item_names": "RS-12"},
    )

    with pytest.raises(ItemNameConfirmError, match="必须是数组"):
        node(create_query_state("问题"))


def test_query_embedding_node_uses_rewritten_query() -> None:
    captured: list[str] = []

    def embedder(query: str) -> TextEmbedding:
        captured.append(query)
        return TextEmbedding([0.1, 0.2], {7: 0.8})

    state = create_query_state("原始问题")
    state["rewritten_query"] = "RS-12 如何测量电压？"

    result = QueryEmbeddingNode(embedder=embedder)(state)

    assert captured == ["RS-12 如何测量电压？"]
    assert result["query_dense_vector"] == [0.1, 0.2]
    assert result["query_sparse_vector"] == {7: 0.8}


def test_query_embedding_node_requires_rewritten_query() -> None:
    with pytest.raises(QueryValidationError, match="有效问题"):
        QueryEmbeddingNode(embedder=lambda _query: TextEmbedding([], {}))(
            create_query_state("原始问题")
        )


def test_vector_search_node_passes_vectors_names_and_limit() -> None:
    captured: dict[str, object] = {}

    def searcher(
        dense: list[float],
        sparse: dict[int, float],
        names: list[str],
        limit: int,
    ) -> list[dict[str, object]]:
        captured.update(dense=dense, sparse=sparse, names=names, limit=limit)
        return [
            {
                "chunk_id": 42,
                "score": 0.9,
                "content": "测量步骤",
                "title": "直流电压",
                "parent_title": "测量",
                "file_title": "RS-12 手册",
                "item_name": "RS-12 数字万用表",
                "part": 1,
            }
        ]

    state = create_query_state("问题", search_limit=3)
    state.update(
        {
            "item_names": ["RS-12 数字万用表"],
            "query_dense_vector": [0.1, 0.2],
            "query_sparse_vector": {7: 0.8},
        }
    )

    result = VectorSearchNode(searcher=searcher)(state)  # type: ignore[arg-type]

    assert captured == {
        "dense": [0.1, 0.2],
        "sparse": {7: 0.8},
        "names": ["RS-12 数字万用表"],
        "limit": 3,
    }
    assert result["search_results"][0]["chunk_id"] == 42
