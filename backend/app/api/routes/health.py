import platform
from typing import Annotated

from fastapi import APIRouter, Depends

from app.clients.infrastructure import InfrastructureClients, get_infrastructure_clients
from app.core.config import Settings, get_settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
    clients: Annotated[InfrastructureClients, Depends(get_infrastructure_clients)],
) -> HealthResponse:
    """检查应用及三个业务基础设施连接。"""

    components = clients.check_all()
    status = "ok" if all(item.status == "up" for item in components.values()) else "degraded"

    return HealthResponse(
        status=status,
        app=settings.app_name,
        environment=settings.app_env,
        python=platform.python_version(),
        components=components,
    )
