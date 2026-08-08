from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """从仓库根目录 `.env` 和系统环境变量加载配置。"""

    model_config = SettingsConfigDict(
        env_file=REPOSITORY_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "掌柜智库"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    import_api_port: int = 8000
    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"
    infra_health_timeout_seconds: float = Field(default=3.0, gt=0, le=30)

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "shopkeeper"
    minio_secret_key: str = "shopkeeper-minio-change-me"
    minio_bucket_name: str = "shopkeeper-knowledge"
    minio_image_bucket_name: str = "shopkeeper-images"
    minio_public_base_url: str = "http://localhost:9000"
    minio_image_public_read: bool = True
    minio_secure: bool = False

    milvus_url: str = "http://localhost:19530"

    mongo_url: str = (
        "mongodb://shopkeeper:shopkeeper-mongo-change-me@localhost:27017/?authSource=admin"
    )
    mongo_db_name: str = "shopkeeper_brain"

    mineru_api_token: str = ""
    mineru_base_url: str = "https://mineru.net/api/v4"
    mineru_model_version: Literal["pipeline", "vlm"] = "vlm"
    mineru_request_timeout_seconds: float = Field(default=120, gt=0, le=600)
    mineru_poll_interval_seconds: float = Field(default=2, gt=0, le=60)
    mineru_task_timeout_seconds: int = Field(default=1800, gt=0, le=7200)

    document_chunk_max_length: int = Field(default=1000, ge=64, le=100_000)
    document_chunk_min_length: int = Field(default=200, ge=1, le=99_999)
    document_chunk_backup_enabled: bool = True

    openai_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    dashscope_api_key: str = ""
    item_model: str = "qwen-flash"
    llm_default_temperature: float = Field(default=0, ge=0, le=2)
    qwen_request_timeout_seconds: float = Field(default=60, gt=0, le=600)
    item_name_max_output_tokens: int = Field(default=128, ge=16, le=1024)
    item_name_chunk_count: int = Field(default=3, ge=1, le=20)
    item_name_context_max_length: int = Field(default=2500, ge=100, le=100_000)
    item_name_backup_enabled: bool = True

    @model_validator(mode="after")
    def validate_document_chunk_lengths(self) -> Self:
        if self.document_chunk_max_length <= self.document_chunk_min_length:
            raise ValueError("DOCUMENT_CHUNK_MAX_LENGTH 必须大于 DOCUMENT_CHUNK_MIN_LENGTH")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
