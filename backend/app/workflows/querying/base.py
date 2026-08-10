"""知识查询节点基类。"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Mapping
from time import perf_counter

from app.workflows.querying.exceptions import QueryNodeError, QueryWorkflowError
from app.workflows.querying.state import QueryGraphState


class BaseQueryNode(ABC):
    """为查询节点提供统一日志、耗时统计和异常边界。"""

    name = "base_query_node"

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"app.workflows.querying.{self.name}")

    def __call__(self, state: QueryGraphState) -> QueryGraphState:
        started_at = perf_counter()
        self.logger.info("Query node started: %s", self.name)
        try:
            updates = self.process(state)
        except QueryWorkflowError:
            self.logger.exception("Query node failed: %s", self.name)
            raise
        except Exception as exc:
            self.logger.exception("Query node failed unexpectedly: %s", self.name)
            raise QueryNodeError(
                "查询节点执行失败",
                node_name=self.name,
                cause=exc,
            ) from exc

        duration_ms = round((perf_counter() - started_at) * 1000, 3)
        result: QueryGraphState = dict(updates)
        result["completed_nodes"] = [self.name]
        result["node_durations_ms"] = {self.name: duration_ms}
        event_handler = state.get("event_handler")
        if callable(event_handler):
            try:
                event_handler(
                    "progress",
                    {"node": self.name, "duration_ms": duration_ms},
                )
            except Exception:
                self.logger.warning("Query event handler failed", exc_info=True)
        self.logger.info("Query node completed: %s (%.3f ms)", self.name, duration_ms)
        return result

    @abstractmethod
    def process(self, state: QueryGraphState) -> Mapping[str, object]:
        """执行节点业务并返回状态增量。"""
