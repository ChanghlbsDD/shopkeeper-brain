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
        result: QueryGraphState = dict(state)
        result.update(updates)

        completed_nodes = list(result.get("completed_nodes", []))
        completed_nodes.append(self.name)
        result["completed_nodes"] = completed_nodes

        node_durations = dict(result.get("node_durations_ms", {}))
        node_durations[self.name] = duration_ms
        result["node_durations_ms"] = node_durations
        self.logger.info("Query node completed: %s (%.3f ms)", self.name, duration_ms)
        return result

    @abstractmethod
    def process(self, state: QueryGraphState) -> Mapping[str, object]:
        """执行节点业务并返回状态更新。"""
