"""可关闭的阿里云百炼网页搜索分支。"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from app.clients.dashscope_web_search import (
    DashScopeWebSearchClient,
    DashScopeWebSearchError,
    WebSearchResult,
)
from app.core.config import Settings, get_settings
from app.workflows.querying.base import BaseQueryNode
from app.workflows.querying.exceptions import QueryValidationError
from app.workflows.querying.state import QueryGraphState

WebSearcher = Callable[[str, int], list[WebSearchResult]]


class WebSearchNode(BaseQueryNode):
    """按开关调用 WebSearch MCP；失败时保留本地两路召回。"""

    name = "web_search_node"

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        searcher: WebSearcher | None = None,
    ) -> None:
        super().__init__()
        self.settings = settings or get_settings()
        self.searcher = searcher

    def process(self, state: QueryGraphState) -> Mapping[str, object]:
        if not self.settings.web_search_enabled:
            return {"web_search_status": "disabled", "web_search_results": []}

        rewritten_query = state.get("rewritten_query")
        if not isinstance(rewritten_query, str) or not rewritten_query.strip():
            raise QueryValidationError("网页检索缺少有效问题", node_name=self.name)
        try:
            if self.searcher is not None:
                results = self.searcher(rewritten_query.strip(), self.settings.web_search_count)
            else:
                results = DashScopeWebSearchClient(
                    endpoint=self.settings.mcp_dashscope_base_url,
                    api_key=self.settings.dashscope_api_key,
                    timeout_seconds=self.settings.web_search_timeout_seconds,
                ).search(rewritten_query.strip(), count=self.settings.web_search_count)
        except DashScopeWebSearchError as exc:
            self.logger.warning("Web retrieval unavailable: %s", exc)
            return {"web_search_status": "failed", "web_search_results": []}
        except Exception as exc:
            self.logger.warning("Web retrieval failed unexpectedly", exc_info=exc)
            return {"web_search_status": "failed", "web_search_results": []}
        return {"web_search_status": "succeeded", "web_search_results": results}
