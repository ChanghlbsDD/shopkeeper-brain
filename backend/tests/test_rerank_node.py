from app.core.config import Settings
from app.workflows.querying.nodes import RerankNode
from app.workflows.querying.state import create_query_state


def local_result(chunk_id: int, content: str):
    return {
        "chunk_id": chunk_id,
        "rrf_score": 0.03,
        "source_paths": ["vector", "hyde"],
        "content": content,
        "title": f"本地 {chunk_id}",
        "parent_title": "",
        "file_title": "手册",
        "item_name": "RS-12 数字万用表",
        "part": 1,
    }


def rerank_state():
    state = create_query_state("怎么测电压？")
    state["rewritten_query"] = "RS-12 数字万用表怎么测电压？"
    state["rrf_results"] = [
        local_result(1, "相关本地文档"),
        local_result(2, "一般本地文档"),
        local_result(3, "较弱本地文档"),
    ]
    state["web_search_results"] = [
        {"title": "网页教程", "url": "https://example.com/guide", "snippet": "无关网页"}
    ]
    return state


def test_rerank_merges_sources_sorts_and_applies_largest_cliff() -> None:
    captured: dict[str, object] = {}

    def reranker(query: str, documents: list[str]) -> list[float]:
        captured.update(query=query, documents=documents)
        return [0.98, 0.91, 0.86, 0.1]

    node = RerankNode(
        settings=Settings(
            _env_file=None,
            rerank_min_top_k=2,
            rerank_max_top_k=4,
            rerank_gap_abs=0.15,
        ),
        reranker=reranker,
    )

    result = node(rerank_state())

    assert result["rerank_status"] == "succeeded"
    assert [document["chunk_id"] for document in result["reranked_documents"]] == [1, 2, 3]
    assert captured["query"] == "RS-12 数字万用表怎么测电压？"
    assert captured["documents"] == ["相关本地文档", "一般本地文档", "较弱本地文档", "无关网页"]


def test_rerank_can_promote_web_result() -> None:
    result = RerankNode(
        settings=Settings(_env_file=None, rerank_min_top_k=1),
        reranker=lambda _query, _documents: [0.3, 0.2, 0.1, 0.99],
    )(rerank_state())

    assert result["reranked_documents"][0]["source"] == "web"
    assert result["reranked_documents"][0]["url"] == "https://example.com/guide"


def test_rerank_failure_preserves_original_candidate_order() -> None:
    result = RerankNode(
        settings=Settings(_env_file=None),
        reranker=lambda _query, _documents: (_ for _ in ()).throw(RuntimeError("down")),
    )(rerank_state())

    assert result["rerank_status"] == "failed"
    assert [document["chunk_id"] for document in result["reranked_documents"][:3]] == [
        1,
        2,
        3,
    ]
    assert result["reranked_documents"][0]["rerank_score"] is None


def test_rerank_disabled_does_not_call_api() -> None:
    result = RerankNode(
        settings=Settings(_env_file=None, rerank_enabled=False),
        reranker=lambda _query, _documents: (_ for _ in ()).throw(AssertionError("must not call")),
    )(rerank_state())

    assert result["rerank_status"] == "disabled"
