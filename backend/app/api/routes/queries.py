"""知识查询、流式回答与会话历史接口。"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request
from fastapi.responses import StreamingResponse

from app.core.exceptions import AppError
from app.schemas.queries import (
    QueryHistoryDeleteResponse,
    QueryHistoryResponse,
    QuerySearchRequest,
    QuerySearchResponse,
)
from app.services.query_service import QueryService, get_query_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/queries", tags=["queries"])


@router.post("/search", response_model=QuerySearchResponse)
def search_knowledge(
    request: QuerySearchRequest,
    service: Annotated[QueryService, Depends(get_query_service)],
) -> QuerySearchResponse:
    """确认商品名、生成查询向量并从 Milvus 返回相关知识片段。"""

    return service.search(request)


def _format_sse(event: str, payload: dict[str, object]) -> str:
    """把一个事件编码成浏览器可解析的 SSE 帧。"""

    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {data}\n\n"


@router.post("/stream", response_class=StreamingResponse)
async def stream_knowledge(
    request_body: QuerySearchRequest,
    request: Request,
    service: Annotated[QueryService, Depends(get_query_service)],
) -> StreamingResponse:
    """以 progress、delta、final 或 error 事件流式返回一次查询。"""

    async def event_stream() -> AsyncIterator[str]:
        loop = asyncio.get_running_loop()
        events: asyncio.Queue[tuple[str, dict[str, object]] | None] = asyncio.Queue()

        def handle_event(event: str, payload: dict[str, object]) -> None:
            loop.call_soon_threadsafe(events.put_nowait, (event, payload))

        async def execute_query() -> None:
            try:
                response = await asyncio.to_thread(
                    service.search,
                    request_body,
                    event_handler=handle_event,
                )
            except AppError as exc:
                await events.put(
                    (
                        "error",
                        {
                            "code": exc.code,
                            "message": exc.message,
                            "status_code": exc.status_code,
                        },
                    )
                )
            except Exception as exc:  # pragma: no cover - 最后的安全边界
                logger.exception("Unhandled streaming query error", exc_info=exc)
                await events.put(
                    (
                        "error",
                        {
                            "code": "INTERNAL_SERVER_ERROR",
                            "message": "服务暂时不可用，请稍后重试",
                            "status_code": 500,
                        },
                    )
                )
            else:
                await events.put(("final", response.model_dump(mode="json")))
            finally:
                await events.put(None)

        task = asyncio.create_task(execute_query())
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(events.get(), timeout=15)
                except TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                if event is None:
                    break
                event_name, payload = event
                yield _format_sse(event_name, payload)
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history/{session_id}", response_model=QueryHistoryResponse)
def get_query_history(
    session_id: Annotated[
        str,
        Path(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$"),
    ],
    service: Annotated[QueryService, Depends(get_query_service)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> QueryHistoryResponse:
    """返回一个会话最近的消息，结果按时间从旧到新排列。"""

    return service.get_history(session_id, limit=limit)


@router.delete("/history/{session_id}", response_model=QueryHistoryDeleteResponse)
def delete_query_history(
    session_id: Annotated[
        str,
        Path(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$"),
    ],
    service: Annotated[QueryService, Depends(get_query_service)],
) -> QueryHistoryDeleteResponse:
    """清空一个明确指定的会话，不影响其他会话。"""

    return service.clear_history(session_id)
