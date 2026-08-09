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


class QueryHistoryMessageRequest(BaseModel):
    """用于商品指代消解的一条客户端历史消息。"""

    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: NonEmptyHistoryContent


class QuerySearchRequest(BaseModel):
    """当前阶段的同步知识召回请求。"""

    model_config = ConfigDict(extra="forbid")

    query: NonEmptyQuery
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

    original_query: str
    rewritten_query: str
    item_names: list[str]
    matches: list[QuerySearchHitResponse]
    completed_nodes: list[str]
    node_durations_ms: dict[str, float]

    @classmethod
    def from_state(cls, state: QueryGraphState) -> QuerySearchResponse:
        return cls(
            original_query=state.get("original_query", ""),
            rewritten_query=state.get("rewritten_query", ""),
            item_names=list(state.get("item_names", [])),
            matches=[
                QuerySearchHitResponse.model_validate(hit)
                for hit in state.get("search_results", [])
            ],
            completed_nodes=list(state.get("completed_nodes", [])),
            node_durations_ms=dict(state.get("node_durations_ms", {})),
        )
