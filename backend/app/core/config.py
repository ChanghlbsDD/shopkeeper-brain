from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

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
    minio_secure: bool = False

    milvus_url: str = "http://localhost:19530"

    mongo_url: str = (
        "mongodb://shopkeeper:shopkeeper-mongo-change-me@localhost:27017/?authSource=admin"
    )
    mongo_db_name: str = "shopkeeper_brain"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
