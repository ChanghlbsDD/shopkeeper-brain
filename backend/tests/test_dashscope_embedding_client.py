import json
from math import nan

import httpx
import pytest

from app.clients.dashscope_embedding import (
    DashScopeEmbeddingClient,
    DashScopeEmbeddingError,
)


def create_client(handler, **overrides: object) -> DashScopeEmbeddingClient:
    values: dict[str, object] = {
        "base_url": "https://dashscope.example.com/api/v1/",
        "api_key": "test-api-key",
        "model": "text-embedding-v4",
        "dimension": 3,
        "max_batch_size": 10,
        "client": httpx.Client(transport=httpx.MockTransport(handler)),
    }
    values.update(overrides)
    return DashScopeEmbeddingClient(**values)


def embedding_payload(*, reverse: bool = False) -> dict[str, object]:
    embeddings = [
        {
            "text_index": 0,
            "embedding": [0.1, 0.2, 0.3],
            "sparse_embedding": [
                {"index": 7, "value": 0.8, "token": "万用表"},
            ],
        },
        {
            "text_index": 1,
            "embedding": [0.4, 0.5, 0.6],
            "sparse_embedding": [
                {"index": 9, "value": 1.2, "token": "测量"},
            ],
        },
    ]
    if reverse:
        embeddings.reverse()
    return {"output": {"embeddings": embeddings}, "usage": {"total_tokens": 8}}


def test_sends_dense_and_sparse_document_embedding_request() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers["Authorization"]
        captured["body"] = json.loads(request.read())
        return httpx.Response(200, json=embedding_payload(reverse=True))

    result = create_client(handler).embed_documents(["商品一", "商品二"])

    assert captured["url"] == (
        "https://dashscope.example.com/api/v1/services/embeddings/text-embedding/text-embedding"
    )
    assert captured["authorization"] == "Bearer test-api-key"
    assert captured["body"] == {
        "model": "text-embedding-v4",
        "input": {"texts": ["商品一", "商品二"]},
        "parameters": {
            "text_type": "document",
            "dimension": 3,
            "output_type": "dense&sparse",
        },
    }
    assert result[0].dense_vector == [0.1, 0.2, 0.3]
    assert result[0].sparse_vector == {7: 0.8}
    assert result[1].dense_vector == [0.4, 0.5, 0.6]


def test_query_embedding_uses_query_text_type() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.read())
        payload = embedding_payload()
        payload["output"]["embeddings"] = payload["output"]["embeddings"][:1]  # type: ignore[index]
        return httpx.Response(200, json=payload)

    result = create_client(handler).embed_queries(["怎么测量直流电压？"])

    body = captured["body"]
    assert isinstance(body, dict)
    assert body["parameters"]["text_type"] == "query"
    assert result[0].dense_vector == [0.1, 0.2, 0.3]


@pytest.mark.parametrize(
    ("overrides", "texts", "message"),
    [
        ({"api_key": ""}, ["文本"], "DASHSCOPE_API_KEY"),
        ({"base_url": "dashscope.example.com"}, ["文本"], "DASHSCOPE_API_BASE"),
        ({"model": ""}, ["文本"], "EMBEDDING_MODEL"),
        ({"dimension": 0}, ["文本"], "EMBEDDING_DIMENSION"),
        ({"max_batch_size": 0}, ["文本"], "EMBEDDING_BATCH_SIZE"),
        ({}, [], "不能为空"),
        ({"max_batch_size": 1}, ["一", "二"], "单批文本数"),
        ({}, ["  "], "非空字符串"),
    ],
)
def test_rejects_invalid_configuration_or_input(
    overrides: dict[str, object],
    texts: list[str],
    message: str,
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("invalid input must not send a request")

    with pytest.raises(DashScopeEmbeddingError, match=message):
        create_client(handler, **overrides).embed_documents(texts)


def test_wraps_http_status_without_exposing_response_body() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "sensitive upstream details"})

    with pytest.raises(DashScopeEmbeddingError, match="HTTP 401") as captured:
        create_client(handler).embed_documents(["文本"])

    assert "sensitive upstream details" not in str(captured.value)


def test_wraps_network_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    with pytest.raises(DashScopeEmbeddingError, match="请求超时"):
        create_client(handler).embed_documents(["文本"])


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({}, "响应结构不完整"),
        ({"output": {"embeddings": []}}, "数量"),
        (
            {
                "output": {
                    "embeddings": [
                        {
                            "text_index": 0,
                            "embedding": [0.1],
                            "sparse_embedding": [{"index": 1, "value": 0.5}],
                        }
                    ]
                }
            },
            "维度",
        ),
        (
            {
                "output": {
                    "embeddings": [
                        {
                            "text_index": 0,
                            "embedding": [0.1, 0.2, nan],
                            "sparse_embedding": [{"index": 1, "value": 0.5}],
                        }
                    ]
                }
            },
            "非有限",
        ),
        (
            {
                "output": {
                    "embeddings": [
                        {
                            "text_index": 0,
                            "embedding": [0.1, 0.2, 0.3],
                            "sparse_embedding": [],
                        }
                    ]
                }
            },
            "没有返回稀疏向量",
        ),
        (
            {
                "output": {
                    "embeddings": [
                        {
                            "text_index": 2,
                            "embedding": [0.1, 0.2, 0.3],
                            "sparse_embedding": [{"index": 1, "value": 0.5}],
                        }
                    ]
                }
            },
            "text_index",
        ),
    ],
)
def test_rejects_invalid_embedding_response(payload: object, message: str) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

    with pytest.raises(DashScopeEmbeddingError, match=message):
        create_client(handler).embed_documents(["文本"])


def test_rejects_non_json_response() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not-json")

    with pytest.raises(DashScopeEmbeddingError, match="有效 JSON"):
        create_client(handler).embed_documents(["文本"])
