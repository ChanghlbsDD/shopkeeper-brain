"""知识查询 API 与 LangGraph 工作流之间的服务层。"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Protocol

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.schemas.queries import QuerySearchRequest, QuerySearchResponse
from app.workflows.querying import run_query_workflow
from app.workflows.querying.exceptions import (
    ItemNameConfirmError,
    QueryEmbeddingError,
    QuerySearchError,
    QueryValidationError,
    QueryWorkflowError,
)
from app.workflows.querying.state import QueryGraphState, QueryHistoryMessage

logger = logging.getLogger(__name__)


class QueryWorkflowRunner(Protocol):
    def __call__(
        self,
        original_query: str,
        *,
        history: list[QueryHistoryMessage] | None = None,
        search_limit: int = 5,
    ) -> QueryGraphState: ...


class QueryService:
    """校验 API 模型、运行同步召回并统一映射可预期错误。"""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        runner: QueryWorkflowRunner = run_query_workflow,
    ) -> None:
        self.settings = settings or get_settings()
        self.runner = runner

    def search(self, request: QuerySearchRequest) -> QuerySearchResponse:
        history: list[QueryHistoryMessage] = [
            {"role": message.role, "content": message.content} for message in request.history
        ]
        try:
            state = self.runner(
                request.query,
                history=history,
                search_limit=(
                    self.settings.query_search_limit if request.limit is None else request.limit
                ),
            )
        except QueryValidationError as exc:
            raise AppError(exc.message, code="INVALID_QUERY", status_code=400) from exc
        except (ItemNameConfirmError, QueryEmbeddingError) as exc:
            logger.warning("Query AI service failed at %s", exc.node_name, exc_info=exc)
            if "未配置" in exc.message:
                raise AppError(
                    "知识查询所需的通义千问 Token 尚未配置",
                    code="QUERY_AI_NOT_CONFIGURED",
                    status_code=503,
                ) from exc
            raise AppError(
                "商品识别或查询向量服务暂时不可用",
                code="QUERY_AI_SERVICE_ERROR",
                status_code=502,
            ) from exc
        except QuerySearchError as exc:
            logger.warning("Query search failed at %s", exc.node_name, exc_info=exc)
            if "集合不存在" in exc.message:
                raise AppError(
                    "知识库中还没有可检索文档，请先导入文档",
                    code="QUERY_KNOWLEDGE_EMPTY",
                    status_code=409,
                ) from exc
            raise AppError(
                "知识检索服务暂时不可用",
                code="QUERY_SEARCH_UNAVAILABLE",
                status_code=503,
            ) from exc
        except QueryWorkflowError as exc:
            logger.exception("Query workflow failed at %s", exc.node_name)
            raise AppError(
                "知识查询处理失败",
                code="QUERY_PROCESSING_ERROR",
                status_code=500,
            ) from exc
        return QuerySearchResponse.from_state(state)


@lru_cache(maxsize=1)
def get_query_service() -> QueryService:
    return QueryService()
