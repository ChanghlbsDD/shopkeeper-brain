from fastapi.testclient import TestClient

from app.clients.infrastructure import get_infrastructure_clients
from app.main import app
from app.schemas.health import ComponentHealth


class HealthyInfrastructure:
    def check_all(self) -> dict[str, ComponentHealth]:
        return {
            "minio": ComponentHealth(status="up", latency_ms=1.0),
            "milvus": ComponentHealth(status="up", latency_ms=2.0),
            "mongodb": ComponentHealth(status="up", latency_ms=3.0),
        }


class DegradedInfrastructure:
    def check_all(self) -> dict[str, ComponentHealth]:
        return {
            "minio": ComponentHealth(status="up", latency_ms=1.0),
            "milvus": ComponentHealth(status="down", latency_ms=2.0, detail="ConnectionError"),
            "mongodb": ComponentHealth(status="up", latency_ms=3.0),
        }


def test_root_returns_application_metadata() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json()["health"] == "/api/health"


def test_health_returns_ok_when_all_dependencies_are_up() -> None:
    app.dependency_overrides[get_infrastructure_clients] = HealthyInfrastructure
    try:
        with TestClient(app) as client:
            response = client.get("/api/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["python"].startswith("3.10.")
    assert set(payload["components"]) == {"minio", "milvus", "mongodb"}


def test_health_returns_degraded_when_a_dependency_is_down() -> None:
    app.dependency_overrides[get_infrastructure_clients] = DegradedInfrastructure
    try:
        with TestClient(app) as client:
            response = client.get("/api/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
