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


def test_mineru_timeout_and_model_version_are_validated() -> None:
    settings = Settings(_env_file=None, mineru_task_timeout_seconds=60)

    assert settings.mineru_model_version == "vlm"
    assert settings.mineru_task_timeout_seconds == 60

    with pytest.raises(ValidationError):
        Settings(_env_file=None, mineru_task_timeout_seconds=0)

    with pytest.raises(ValidationError):
        Settings(_env_file=None, mineru_model_version="unsupported")


def test_minio_images_use_a_separate_public_bucket() -> None:
    settings = Settings(_env_file=None)

    assert settings.minio_image_bucket_name == "shopkeeper-images"
    assert settings.minio_public_base_url == "http://localhost:9000"
    assert settings.minio_image_public_read is True


def test_document_chunk_lengths_are_validated() -> None:
    settings = Settings(
        _env_file=None,
        document_chunk_max_length=1000,
        document_chunk_min_length=200,
    )

    assert settings.document_chunk_backup_enabled is True

    with pytest.raises(ValidationError, match="MAX_LENGTH"):
        Settings(
            _env_file=None,
            document_chunk_max_length=200,
            document_chunk_min_length=200,
        )
