from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import AppError, register_exception_handlers


def create_error_test_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/business-error")
    def business_error() -> None:
        raise AppError("文件类型不支持", code="UNSUPPORTED_FILE", status_code=415)

    @app.get("/unexpected-error")
    def unexpected_error() -> None:
        raise RuntimeError("internal details must not be exposed")

    return app


def test_app_error_uses_the_standard_error_shape() -> None:
    with TestClient(create_error_test_app()) as client:
        response = client.get("/business-error")

    assert response.status_code == 415
    assert response.json() == {"error": {"code": "UNSUPPORTED_FILE", "message": "文件类型不支持"}}


def test_unexpected_error_does_not_leak_internal_details() -> None:
    with TestClient(create_error_test_app(), raise_server_exceptions=False) as client:
        response = client.get("/unexpected-error")

    assert response.status_code == 500
    assert response.json()["error"] == {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "服务暂时不可用，请稍后重试",
    }
    assert "internal details" not in response.text
