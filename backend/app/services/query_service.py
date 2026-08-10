"""知识查询 API 与 LangGraph 工作流之间的服务层。"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Protocol
from uuid import uuid4

from app.clients.mongo_history import (
    MongoHistoryError,
    MongoHistoryStore,
    StoredChatMessage,
)
from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.schemas.queries import QuerySearchRequest, QuerySearchResponse
from app.workflows.querying import run_query_workflow
from app.workflows.querying.exceptions import (
    ItemNameConfirmError,
    QueryAnswerError,
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


class QueryHistoryStore(Protocol):
    def get_recent(self, session_id: str, *, limit: int) -> list[StoredChatMessage]: ...

    def append(
        self,
        session_id: str,
        *,
        role: str,
        content: str,
        rewritten_query: str = "",
        item_names: list[str] | None = None,
    ) -> StoredChatMessage: ...


class QueryService:
    """校验 API 模型、运行同步召回并统一映射可预期错误。"""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        runner: QueryWorkflowRunner = run_query_workflow,
        history_store: QueryHistoryStore | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.runner = runner
        self.history_store = history_store or MongoHistoryStore(self.settings)

    def search(self, request: QuerySearchRequest) -> QuerySearchResponse:
        session_id = request.session_id or uuid4().hex
        history, history_available = self._load_history(session_id, request)
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
        except QueryAnswerError as exc:
            logger.warning("Query answer generation failed", exc_info=exc)
            if "未配置" in exc.message:
                raise AppError(
                    "答案生成所需的通义千问 Token 尚未配置",
                    code="QUERY_ANSWER_NOT_CONFIGURED",
                    status_code=503,
                ) from exc
            raise AppError(
                "答案生成服务暂时不可用",
                code="QUERY_ANSWER_UNAVAILABLE",
                status_code=502,
            ) from exc
        except QueryWorkflowError as exc:
            logger.exception("Query workflow failed at %s", exc.node_name)
            raise AppError(
                "知识查询处理失败",
                code="QUERY_PROCESSING_ERROR",
                status_code=500,
            ) from exc
        history_persisted = history_available and self._record_messages(session_id, request, state)
        return QuerySearchResponse.from_state(
            state,
            session_id=session_id,
            history_persisted=history_persisted,
        )

    def _load_history(
        self,
        session_id: str,
        request: QuerySearchRequest,
    ) -> tuple[list[QueryHistoryMessage], bool]:
        supplied_history: list[QueryHistoryMessage] = [
            {"role": message.role, "content": message.content} for message in request.history
        ]
        try:
            stored = self.history_store.get_recent(
                session_id,
                limit=self.settings.query_history_max_messages,
            )
        except MongoHistoryError as exc:
            logger.warning("Query history read failed", exc_info=exc)
            if request.session_id is not None and not supplied_history:
                raise AppError(
                    "会话历史暂时不可用，请稍后重试",
                    code="QUERY_HISTORY_UNAVAILABLE",
                    status_code=503,
                ) from exc
            return supplied_history, False

        if stored:
            return [
                {"role": message["role"], "content": message["content"]} for message in stored
            ], True
        return supplied_history, True

    def _record_messages(
        self,
        session_id: str,
        request: QuerySearchRequest,
        state: QueryGraphState,
    ) -> bool:
        try:
            self.history_store.append(
                session_id,
                role="user",
                content=request.query,
                rewritten_query=state.get("rewritten_query", ""),
                item_names=list(state.get("item_names", [])),
            )
            assistant_answer = state.get("answer", "") or state.get("clarification", "")
            if assistant_answer:
                self.history_store.append(
                    session_id,
                    role="assistant",
                    content=assistant_answer,
                    rewritten_query=state.get("rewritten_query", ""),
                    item_names=list(state.get("item_names", [])),
                )
        except MongoHistoryError as exc:
            logger.warning("Query history write failed", exc_info=exc)
            return False
        return True


@lru_cache(maxsize=1)
def get_query_service() -> QueryService:
    return QueryService()
