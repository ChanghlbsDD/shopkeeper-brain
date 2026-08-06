import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_cors_origins_are_split_and_trimmed() -> None:
    settings = Settings(
        _env_file=None,
        cors_origins="http://localhost:5173, http://127.0.0.1:5173",
    )

    assert settings.cors_origin_list == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


def test_health_timeout_must_be_positive() -> None:
    settings = Settings(_env_file=None, infra_health_timeout_seconds=1.5)

    assert settings.infra_health_timeout_seconds == 1.5

    with pytest.raises(ValidationError):
        Settings(_env_file=None, infra_health_timeout_seconds=0)
