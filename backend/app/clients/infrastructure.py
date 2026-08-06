from __future__ import annotations

import logging
from collections.abc import Callable
from functools import lru_cache
from time import perf_counter

from minio import Minio
from pymilvus import MilvusClient
from pymongo import MongoClient
from urllib3 import PoolManager, Timeout

from app.core.config import Settings, get_settings
from app.schemas.health import ComponentHealth

logger = logging.getLogger(__name__)


class InfrastructureClients:
    """按需创建基础设施客户端，并提供轻量连接检查。"""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def check_minio(self) -> ComponentHealth:
        def operation() -> None:
            timeout = self._settings.infra_health_timeout_seconds
            http_client = PoolManager(timeout=Timeout(connect=timeout, read=timeout))
            client = Minio(
                endpoint=self._settings.minio_endpoint,
                access_key=self._settings.minio_access_key,
                secret_key=self._settings.minio_secret_key,
                secure=self._settings.minio_secure,
                http_client=http_client,
            )
            try:
                client.list_buckets()
            finally:
                http_client.clear()

        return self._measure("minio", operation)

    def check_milvus(self) -> ComponentHealth:
        def operation() -> None:
            client = MilvusClient(uri=self._settings.milvus_url)
            try:
                client.list_collections(timeout=self._settings.infra_health_timeout_seconds)
            finally:
                client.close()

        return self._measure("milvus", operation)

    def check_mongodb(self) -> ComponentHealth:
        def operation() -> None:
            timeout_ms = int(self._settings.infra_health_timeout_seconds * 1000)
            client: MongoClient = MongoClient(
                self._settings.mongo_url,
                serverSelectionTimeoutMS=timeout_ms,
                connectTimeoutMS=timeout_ms,
            )
            try:
                client.admin.command("ping")
            finally:
                client.close()

        return self._measure("mongodb", operation)

    def check_all(self) -> dict[str, ComponentHealth]:
        return {
            "minio": self.check_minio(),
            "milvus": self.check_milvus(),
            "mongodb": self.check_mongodb(),
        }

    @staticmethod
    def _measure(name: str, operation: Callable[[], None]) -> ComponentHealth:
        started_at = perf_counter()
        try:
            operation()
        except Exception as exc:  # 各 SDK 异常类型不同，在边界统一降级
            latency_ms = round((perf_counter() - started_at) * 1000, 2)
            logger.warning("%s health check failed: %s", name, type(exc).__name__)
            return ComponentHealth(
                status="down",
                latency_ms=latency_ms,
                detail=type(exc).__name__,
            )

        latency_ms = round((perf_counter() - started_at) * 1000, 2)
        return ComponentHealth(status="up", latency_ms=latency_ms)


@lru_cache(maxsize=1)
def get_infrastructure_clients() -> InfrastructureClients:
    return InfrastructureClients(get_settings())
