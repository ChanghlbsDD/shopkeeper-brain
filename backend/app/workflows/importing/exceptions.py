"""文档导入工作流异常。"""

from __future__ import annotations


class ImportWorkflowError(Exception):
    """导入流程可识别异常的基类。"""

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


class ImportValidationError(ImportWorkflowError):
    """导入文件或状态参数不符合要求。"""


class ImportNodeError(ImportWorkflowError):
    """节点执行时发生未预期错误。"""


class PdfConversionError(ImportWorkflowError):
    """MinerU 无法把 PDF 转换为 Markdown。"""


class MarkdownImageError(ImportWorkflowError):
    """Markdown 图片路径校验、上传或链接替换失败。"""


class DocumentSplitError(ImportWorkflowError):
    """Markdown 文档无法切分为有效知识片段。"""


class ItemNameRecognitionError(ImportWorkflowError):
    """通义千问无法从文档片段中识别有效商品名称。"""


class EmbeddingError(ImportWorkflowError):
    """百炼无法为文档片段生成有效混合向量。"""
