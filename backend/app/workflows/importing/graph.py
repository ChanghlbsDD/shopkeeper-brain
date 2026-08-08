"""文档导入 LangGraph 流程。"""

from __future__ import annotations

from typing import Literal, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.workflows.importing.base import BaseNode
from app.workflows.importing.nodes import (
    DocumentSplitNode,
    EntryNode,
    MarkdownImageNode,
    PdfToMarkdownNode,
    PendingNode,
)
from app.workflows.importing.state import ImportGraphState, create_import_state

ENTRY_NODE = "entry_node"
PDF_TO_MD_NODE = "pdf_to_md_node"
MD_IMAGE_NODE = "md_img_node"
DOCUMENT_SPLIT_NODE = "document_split_node"
ITEM_NAME_NODE = "item_name_recognition_node"
EMBEDDING_NODE = "bge_embedding_node"
MILVUS_NODE = "import_milvus_node"


def route_import_file(state: ImportGraphState) -> Literal["pdf", "md"]:
    """根据入口节点识别的文件类型选择分支。"""

    if state.get("is_pdf_read_enabled"):
        return "pdf"
    if state.get("is_md_read_enabled"):
        return "md"
    raise ValueError("入口节点没有设置可用的文件类型")


def create_import_workflow(
    *,
    pdf_to_md_node: BaseNode | None = None,
    md_image_node: BaseNode | None = None,
    document_split_node: BaseNode | None = None,
) -> CompiledStateGraph:
    """创建并编译文档导入流程骨架。"""

    graph = StateGraph(ImportGraphState)
    graph.add_node(ENTRY_NODE, EntryNode())
    graph.add_node(PDF_TO_MD_NODE, pdf_to_md_node or PdfToMarkdownNode())
    graph.add_node(MD_IMAGE_NODE, md_image_node or MarkdownImageNode())
    graph.add_node(DOCUMENT_SPLIT_NODE, document_split_node or DocumentSplitNode())
    graph.add_node(
        ITEM_NAME_NODE,
        PendingNode(ITEM_NAME_NODE, "后续识别文档中的商品名称"),
    )
    graph.add_node(
        EMBEDDING_NODE,
        PendingNode(EMBEDDING_NODE, "后续生成 BGE-M3 稠密和稀疏向量"),
    )
    graph.add_node(
        MILVUS_NODE,
        PendingNode(MILVUS_NODE, "后续将文档片段和向量写入 Milvus"),
    )

    graph.add_edge(START, ENTRY_NODE)
    graph.add_conditional_edges(
        ENTRY_NODE,
        route_import_file,
        {"pdf": PDF_TO_MD_NODE, "md": MD_IMAGE_NODE},
    )
    graph.add_edge(PDF_TO_MD_NODE, MD_IMAGE_NODE)
    graph.add_edge(MD_IMAGE_NODE, DOCUMENT_SPLIT_NODE)
    graph.add_edge(DOCUMENT_SPLIT_NODE, ITEM_NAME_NODE)
    graph.add_edge(ITEM_NAME_NODE, EMBEDDING_NODE)
    graph.add_edge(EMBEDDING_NODE, MILVUS_NODE)
    graph.add_edge(MILVUS_NODE, END)
    return graph.compile()


import_workflow = create_import_workflow()


def run_import_workflow(
    import_file_path: str,
    *,
    file_dir: str = "",
    task_id: str = "",
) -> ImportGraphState:
    """以初始状态运行一次导入流程骨架。"""

    initial_state = create_import_state(
        import_file_path,
        file_dir=file_dir,
        task_id=task_id,
    )
    return cast(ImportGraphState, import_workflow.invoke(initial_state))
