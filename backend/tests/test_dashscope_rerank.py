import json

import httpx
import pytest

from app.clients.dashscope_rerank import DashScopeRerankClient, DashScopeRerankError


def test_gte_rerank_request_and_index_order_restoration() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers["Authorization"]
        captured["body"] = json.loads(request.read())
        return httpx.Response(
            200,
            json={
                "output": {
                    "results": [
                        {"index": 1, "relevance_score": 0.2},
                        {"index": 0, "relevance_score": 0.9},
                    ]
                }
            },
        )

    client = DashScopeRerankClient(
        base_url="https://dashscope.example.com/api/v1/",
        api_key="test-key",
        model="gte-rerank-v2",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    scores = client.rerank("怎么测电压？", ["相关文档", "无关文档"])

    assert scores == [0.9, 0.2]
    assert captured["url"] == (
        "https://dashscope.example.com/api/v1/services/rerank/text-rerank/text-rerank"
    )
    assert captured["authorization"] == "Bearer test-key"
    assert captured["body"] == {
        "model": "gte-rerank-v2",
        "input": {"query": "怎么测电压？", "documents": ["相关文档", "无关文档"]},
        "parameters": {"return_documents": False, "top_n": 2},
    }


def test_qwen3_rerank_uses_compatible_endpoint_shape() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.read())
        assert str(request.url) == "https://workspace.example.com/compatible-api/v1/reranks"
        assert body["query"] == "问题"
        assert "input" not in body
        return httpx.Response(
            200,
            json={"results": [{"index": 0, "relevance_score": 0.8}]},
        )

    client = DashScopeRerankClient(
        base_url="https://workspace.example.com/compatible-api/v1",
        api_key="test-key",
        model="qwen3-rerank",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert client.rerank("问题", ["文档"]) == [0.8]


@pytest.mark.parametrize(
    "payload",
    [
        {"output": {"results": [{"index": 0, "relevance_score": 1.2}]}},
        {"output": {"results": [{"index": 2, "relevance_score": 0.5}]}},
        {"output": {"results": []}},
    ],
)
def test_rerank_rejects_invalid_or_incomplete_scores(payload: object) -> None:
    client = DashScopeRerankClient(
        base_url="https://dashscope.example.com/api/v1",
        api_key="test-key",
        model="gte-rerank-v2",
        client=httpx.Client(
            transport=httpx.MockTransport(lambda _request: httpx.Response(200, json=payload))
        ),
    )

    with pytest.raises(DashScopeRerankError):
        client.rerank("问题", ["文档"])
