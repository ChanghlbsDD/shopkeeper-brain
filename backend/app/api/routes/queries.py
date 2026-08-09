"""知识查询与混合召回接口。"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.queries import QuerySearchRequest, QuerySearchResponse
from app.services.query_service import QueryService, get_query_service

router = APIRouter(prefix="/queries", tags=["queries"])


@router.post("/search", response_model=QuerySearchResponse)
def search_knowledge(
    request: QuerySearchRequest,
    service: Annotated[QueryService, Depends(get_query_service)],
) -> QuerySearchResponse:
    """确认商品名、生成查询向量并从 Milvus 返回相关知识片段。"""

    return service.search(request)
