import json

import httpx
import pytest

from app.clients.dashscope_web_search import (
    DashScopeWebSearchClient,
    DashScopeWebSearchError,
)


def test_web_search_runs_mcp_handshake_and_parses_pages() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "DELETE":
            return httpx.Response(204)
        body = json.loads(request.read())
        if body["method"] == "initialize":
            return httpx.Response(
                200,
                headers={"Mcp-Session-Id": "session-1"},
                json={"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}},
            )
        if body["method"] == "notifications/initialized":
            return httpx.Response(202)
        assert body["params"] == {
            "name": "bailian_web_search",
            "arguments": {"query": "RS-12 怎么测电压？", "count": 3},
        }
        tool_text = json.dumps(
            {
                "pages": [
                    {
                        "title": "万用表教程",
                        "url": "https://example.com/tutorial",
                        "snippet": "测量前先选择正确档位。",
                    }
                ]
            },
            ensure_ascii=False,
        )
        return httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "result": {"content": [{"type": "text", "text": tool_text}]},
            },
        )

    client = DashScopeWebSearchClient(
        endpoint="https://dashscope.example.com/mcp",
        api_key="test-key",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = client.search("RS-12 怎么测电压？", count=3)

    assert result == [
        {
            "title": "万用表教程",
            "url": "https://example.com/tutorial",
            "snippet": "测量前先选择正确档位。",
        }
    ]
    assert [request.method for request in requests] == ["POST", "POST", "POST", "DELETE"]
    assert requests[2].headers["Mcp-Session-Id"] == "session-1"
    assert requests[2].headers["Mcp-Method"] == "tools/call"
    assert requests[2].headers["Mcp-Name"] == "bailian_web_search"


def test_web_search_parses_sse_json_rpc_response() -> None:
    payload = {"jsonrpc": "2.0", "id": 2, "result": {"content": []}}
    response = httpx.Response(
        200,
        headers={"content-type": "text/event-stream"},
        text=f"event: message\ndata: {json.dumps(payload)}\n\n",
    )

    result = DashScopeWebSearchClient._parse_json_rpc(response, expected_id=2)

    assert result == {"content": []}


def test_web_search_rejects_missing_token_before_network() -> None:
    client = DashScopeWebSearchClient(
        endpoint="https://dashscope.example.com/mcp",
        api_key="",
        client=httpx.Client(
            transport=httpx.MockTransport(
                lambda _request: (_ for _ in ()).throw(AssertionError("must not request"))
            )
        ),
    )

    with pytest.raises(DashScopeWebSearchError, match="DASHSCOPE_API_KEY"):
        client.search("问题")
