import os

import pytest

from app.clients.infrastructure import InfrastructureClients
from app.core.config import Settings

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INTEGRATION_TESTS") != "1",
        reason="set RUN_INTEGRATION_TESTS=1 to use the local Docker infrastructure",
    ),
]


def test_all_infrastructure_services_are_reachable() -> None:
    results = InfrastructureClients(Settings()).check_all()

    assert {name: result.status for name, result in results.items()} == {
        "minio": "up",
        "milvus": "up",
        "mongodb": "up",
    }
