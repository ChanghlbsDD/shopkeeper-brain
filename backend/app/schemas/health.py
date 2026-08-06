from typing import Literal

from pydantic import BaseModel, Field


class ComponentHealth(BaseModel):
    status: Literal["up", "down"]
    latency_ms: float = Field(ge=0)
    detail: str | None = None


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    app: str
    environment: str
    python: str
    components: dict[str, ComponentHealth]
