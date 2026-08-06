"""尚未实现业务的流程占位节点。"""

from __future__ import annotations

from collections.abc import Mapping

from app.workflows.importing.base import BaseNode
from app.workflows.importing.state import ImportGraphState


class PendingNode(BaseNode):
    """保持状态不变，同时让完整流程能够被编译和验证。"""

    def __init__(self, name: str, future_responsibility: str) -> None:
        self.name = name
        self.future_responsibility = future_responsibility
        super().__init__()

    def process(self, _state: ImportGraphState) -> Mapping[str, object]:
        self.log_step("pending", self.future_responsibility)
        return {}
