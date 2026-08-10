import pytest

from app.core.config import Settings
from app.workflows.querying.nodes import RrfNode
from app.workflows.querying.state import create_query_state


def hit(chunk_id: int, content: str):
    return {
        "chunk_id": chunk_id,
        "score": 0.9,
        "content": content,
        "title": f"标题 {chunk_id}",
        "parent_title": "父标题",
        "file_title": "手册",
        "item_name": "RS-12 数字万用表",
        "part": 1,
    }


def test_rrf_promotes_chunks_found_by_both_paths() -> None:
    state = create_query_state("问题")
    state["search_results"] = [hit(1, "直接一"), hit(2, "直接二"), hit(3, "直接三")]
    state["hyde_search_results"] = [hit(2, "HyDE 二"), hit(1, "HyDE 一"), hit(4, "HyDE 四")]

    result = RrfNode(settings=Settings(_env_file=None))(state)

    fused = result["rrf_results"]
    assert [item["chunk_id"] for item in fused] == [1, 2, 3, 4]
    assert fused[0]["source_paths"] == ["vector", "hyde"]
    assert fused[0]["content"] == "直接一"
    assert fused[0]["rrf_score"] == pytest.approx(1 / 61 + 1 / 62)
    assert fused[1]["rrf_score"] == pytest.approx(1 / 62 + 1 / 61)


def test_rrf_uses_weights_limit_and_deterministic_ties() -> None:
    state = create_query_state("问题")
    state["search_results"] = [hit(1, "直接一"), hit(2, "直接二")]
    state["hyde_search_results"] = [hit(3, "HyDE 三"), hit(4, "HyDE 四")]
    node = RrfNode(
        settings=Settings(
            _env_file=None,
            query_rrf_k=10,
            query_rrf_max_results=3,
            query_rrf_vector_weight=2,
            query_rrf_hyde_weight=1,
        )
    )

    result = node(state)

    assert [item["chunk_id"] for item in result["rrf_results"]] == [1, 2, 3]
    assert result["rrf_results"][0]["rrf_score"] == pytest.approx(2 / 11)


def test_rrf_does_not_count_duplicate_chunk_twice_in_one_path() -> None:
    fused = RrfNode.fuse(
        [
            ("vector", [hit(1, "首次"), hit(1, "重复"), hit(2, "第二")], 1.0),
            ("hyde", [], 1.0),
        ],
        k=60,
        max_results=10,
    )

    assert [item["chunk_id"] for item in fused] == [1, 2]
    assert fused[0]["rrf_score"] == pytest.approx(1 / 61)
    assert fused[1]["rrf_score"] == pytest.approx(1 / 62)


def test_rrf_ignores_invalid_entries_and_zero_weight_path() -> None:
    fused = RrfNode.fuse(
        [
            ("vector", [None, {"chunk_id": True}, hit(0, "零号")], 1.0),  # type: ignore[list-item]
            ("hyde", [hit(2, "关闭的路线")], 0.0),
        ],
        k=60,
        max_results=10,
    )

    assert [item["chunk_id"] for item in fused] == [0]
