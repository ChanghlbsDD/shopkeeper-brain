from app.clients.dashscope_embedding import TextEmbedding
from app.core.config import Settings
from app.workflows.querying.nodes import HydeSearchNode, WebSearchNode
from app.workflows.querying.state import create_query_state


def confirmed_state():
    state = create_query_state("怎么测电压？", search_limit=4)
    state.update(
        {
            "query_status": "confirmed",
            "rewritten_query": "RS-12 数字万用表怎么测电压？",
            "item_names": ["RS-12 数字万用表"],
        }
    )
    return state


def test_hyde_search_generates_embeds_and_searches() -> None:
    captured: dict[str, object] = {}

    def generate(query: str, names: list[str]) -> str:
        captured.update(query=query, names=names)
        return "这是一段假设的产品手册答案。"

    def embed(text: str) -> TextEmbedding:
        captured["embedding_text"] = text
        return TextEmbedding([0.3, 0.4], {9: 0.6})

    def search(dense, sparse, names, limit):
        captured.update(dense=dense, sparse=sparse, search_names=names, limit=limit)
        return []

    result = HydeSearchNode(
        settings=Settings(_env_file=None, query_hyde_enabled=True),
        document_generator=generate,
        embedder=embed,
        searcher=search,
    )(confirmed_state())

    assert result["hyde_status"] == "succeeded"
    assert "假设的产品手册" in str(captured["embedding_text"])
    assert captured["search_names"] == ["RS-12 数字万用表"]
    assert captured["limit"] == 4


def test_hyde_failure_does_not_raise() -> None:
    result = HydeSearchNode(
        settings=Settings(_env_file=None, query_hyde_enabled=True),
        document_generator=lambda _query, _names: (_ for _ in ()).throw(RuntimeError("down")),
    )(confirmed_state())

    assert result["hyde_status"] == "failed"
    assert result["hyde_search_results"] == []


def test_web_search_is_disabled_without_calling_client() -> None:
    result = WebSearchNode(
        settings=Settings(_env_file=None, web_search_enabled=False),
        searcher=lambda _query, _count: (_ for _ in ()).throw(AssertionError("must not call")),
    )(confirmed_state())

    assert result["web_search_status"] == "disabled"
    assert result["web_search_results"] == []


def test_web_search_passes_rewritten_query_and_count() -> None:
    captured: dict[str, object] = {}

    def search(query: str, count: int):
        captured.update(query=query, count=count)
        return [{"title": "教程", "url": "https://example.com", "snippet": "步骤"}]

    result = WebSearchNode(
        settings=Settings(_env_file=None, web_search_enabled=True, web_search_count=2),
        searcher=search,
    )(confirmed_state())

    assert result["web_search_status"] == "succeeded"
    assert result["web_search_results"][0]["url"] == "https://example.com"
    assert captured == {"query": "RS-12 数字万用表怎么测电压？", "count": 2}
