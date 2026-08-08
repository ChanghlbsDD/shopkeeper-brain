import httpx
import pytest

from app.clients.qwen_chat import QwenChatClient, QwenChatError


def create_client(handler, **overrides: object) -> QwenChatClient:
    values: dict[str, object] = {
        "base_url": "https://dashscope.example.com/compatible-mode/v1/",
        "api_key": "test-api-key",
        "model": "qwen-flash",
        "client": httpx.Client(transport=httpx.MockTransport(handler)),
    }
    values.update(overrides)
    return QwenChatClient(**values)


def test_sends_openai_compatible_json_request() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers["Authorization"]
        captured["body"] = request.read().decode("utf-8")
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"item_name":"RS-12 数字万用表"}'}}]},
        )

    result = create_client(handler).create_json_completion(
        system_prompt="请输出 JSON",
        user_prompt="识别商品",
    )

    assert result == {"item_name": "RS-12 数字万用表"}
    assert captured["url"] == ("https://dashscope.example.com/compatible-mode/v1/chat/completions")
    assert captured["authorization"] == "Bearer test-api-key"
    body = str(captured["body"])
    assert '"model":"qwen-flash"' in body
    assert '"max_tokens":128' in body
    assert '"response_format":{"type":"json_object"}' in body


def test_accepts_json_wrapped_in_markdown_fence() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '```json\n{"item_name":"示波器"}\n```'}}]},
        )

    result = create_client(handler).create_json_completion(
        system_prompt="JSON",
        user_prompt="识别",
    )

    assert result["item_name"] == "示波器"


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"api_key": ""}, "DASHSCOPE_API_KEY"),
        ({"base_url": "dashscope.example.com"}, "OPENAI_API_BASE"),
        ({"model": ""}, "ITEM_MODEL"),
        ({"max_tokens": 0}, "max_tokens"),
    ],
)
def test_rejects_missing_or_invalid_configuration(
    overrides: dict[str, object],
    message: str,
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("invalid configuration must not send a request")

    with pytest.raises(QwenChatError, match=message):
        create_client(handler, **overrides).create_json_completion(
            system_prompt="JSON",
            user_prompt="识别",
        )


def test_wraps_http_status_without_exposing_response_body() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "sensitive upstream details"})

    with pytest.raises(QwenChatError, match="HTTP 401") as captured:
        create_client(handler).create_json_completion(
            system_prompt="JSON",
            user_prompt="识别",
        )

    assert "sensitive upstream details" not in str(captured.value)


@pytest.mark.parametrize(
    ("response_json", "message"),
    [
        ({"choices": []}, "响应结构不完整"),
        ({"choices": [{"message": {"content": "not-json"}}]}, "有效 JSON"),
        ({"choices": [{"message": {"content": "[]"}}]}, "顶层必须是对象"),
        ({"choices": [{"message": {"content": ""}}]}, "没有返回有效内容"),
    ],
)
def test_rejects_invalid_api_response(response_json: object, message: str) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=response_json)

    with pytest.raises(QwenChatError, match=message):
        create_client(handler).create_json_completion(
            system_prompt="JSON",
            user_prompt="识别",
        )


def test_wraps_network_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    with pytest.raises(QwenChatError, match="请求超时"):
        create_client(handler).create_json_completion(
            system_prompt="JSON",
            user_prompt="识别",
        )
