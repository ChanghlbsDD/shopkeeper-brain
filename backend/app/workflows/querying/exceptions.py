"""知识查询工作流异常。"""

from __future__ import annotations


class QueryWorkflowError(Exception):
    """查询流程可识别异常的基类。"""

    def __init__(
        self,
        message: str,
        *,
        node_name: str = "",
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.node_name = node_name
        self.cause = cause

    def __str__(self) -> str:
        prefix = f"[{self.node_name}] " if self.node_name else ""
        return f"{prefix}{self.message}"


class QueryValidationError(QueryWorkflowError):
    """请求或图状态不符合查询要求。"""


class QueryNodeError(QueryWorkflowError):
    """节点执行时发生未预期错误。"""


class ItemNameConfirmError(QueryWorkflowError):
    """通义千问无法确认查询中的商品名称。"""


class QueryEmbeddingError(QueryWorkflowError):
    """百炼无法为查询生成混合向量。"""


class QuerySearchError(QueryWorkflowError):
    """Milvus 无法完成知识片段召回。"""
