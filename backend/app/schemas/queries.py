"""知识查询 HTTP API 数据契约。"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.workflows.querying.state import QueryGraphState

NonEmptyQuery = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=2000),
]
NonEmptyHistoryContent = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=2000),
]
SessionId = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
    ),
]


class QueryHistoryMessageRequest(BaseModel):
    """用于商品指代消解的一条客户端历史消息。"""

    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: NonEmptyHistoryContent


class QuerySearchRequest(BaseModel):
    """当前阶段的同步知识召回请求。"""

    model_config = ConfigDict(extra="forbid")

    query: NonEmptyQuery
    session_id: SessionId | None = None
    history: list[QueryHistoryMessageRequest] = Field(default_factory=list, max_length=10)
    limit: int | None = Field(default=None, ge=1, le=20)


class QuerySearchHitResponse(BaseModel):
    """可安全返回给前端的知识片段摘要。"""

    chunk_id: int
    score: float
    content: str
    title: str
    parent_title: str
    file_title: str
    item_name: str
    part: int | None = None


class QuerySearchResponse(BaseModel):
    """商品名确认、问题改写和混合召回结果。"""

    session_id: str
    status: Literal["retrieved", "needs_clarification", "unrecognized"]
    history_persisted: bool
    original_query: str
    rewritten_query: str
    extracted_item_names: list[str]
    item_names: list[str]
    item_name_options: list[str]
    clarification: str
    matches: list[QuerySearchHitResponse]
    completed_nodes: list[str]
    node_durations_ms: dict[str, float]

    @classmethod
    def from_state(
        cls,
        state: QueryGraphState,
        *,
        session_id: str,
        history_persisted: bool,
    ) -> QuerySearchResponse:
        query_status = state.get("query_status")
        if query_status == "confirmed":
            response_status = "retrieved"
        elif query_status in {"needs_clarification", "unrecognized"}:
            response_status = query_status
        else:
            raise ValueError("查询工作流没有返回有效状态")
        return cls(
            session_id=session_id,
            status=response_status,
            history_persisted=history_persisted,
            original_query=state.get("original_query", ""),
            rewritten_query=state.get("rewritten_query", ""),
            extracted_item_names=list(state.get("extracted_item_names", [])),
            item_names=list(state.get("item_names", [])),
            item_name_options=list(state.get("item_name_options", [])),
            clarification=state.get("clarification", ""),
            matches=[
                QuerySearchHitResponse.model_validate(hit)
                for hit in state.get("search_results", [])
            ],
            completed_nodes=list(state.get("completed_nodes", [])),
            node_durations_ms=dict(state.get("node_durations_ms", {})),
        )
