"""文档导入节点基类。"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Mapping
from time import perf_counter

from app.workflows.importing.exceptions import ImportNodeError, ImportWorkflowError
from app.workflows.importing.state import ImportGraphState


class BaseNode(ABC):
    """为所有导入节点提供统一调用、日志、耗时和异常边界。"""

    name = "base_node"

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"app.workflows.importing.{self.name}")

    def __call__(self, state: ImportGraphState) -> ImportGraphState:
        started_at = perf_counter()
        self.logger.info("Import node started: %s", self.name)

        try:
            updates = self.process(state)
        except ImportWorkflowError:
            self.logger.exception("Import node failed: %s", self.name)
            raise
        except Exception as exc:
            self.logger.exception("Import node failed unexpectedly: %s", self.name)
            raise ImportNodeError(
                "节点执行失败",
                node_name=self.name,
                cause=exc,
            ) from exc

        duration_ms = round((perf_counter() - started_at) * 1000, 3)
        result: ImportGraphState = dict(state)
        result.update(updates)

        completed_nodes = list(result.get("completed_nodes", []))
        completed_nodes.append(self.name)
        result["completed_nodes"] = completed_nodes

        node_durations = dict(result.get("node_durations_ms", {}))
        node_durations[self.name] = duration_ms
        result["node_durations_ms"] = node_durations

        self.logger.info("Import node completed: %s (%.3f ms)", self.name, duration_ms)
        return result

    @abstractmethod
    def process(self, state: ImportGraphState) -> Mapping[str, object]:
        """执行节点自己的业务并返回状态更新。"""

    def log_step(self, step: str, message: str) -> None:
        self.logger.info("[%s] %s", step, message)
