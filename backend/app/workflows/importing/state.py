"""文档导入流程共享状态。"""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Literal, TypedDict

ImportProgressEvent = Literal["started", "completed"]
ImportProgressCallback = Callable[[ImportProgressEvent, str, float | None], None]


class DocumentChunk(TypedDict, total=False):
    """标题切分后交给识别、向量化和入库节点的知识片段。"""

    title: str
    parent_title: str
    file_title: str
    content: str
    part: int
    item_name: str
    dense_vector: list[float]
    sparse_vector: dict[int, float]
    chunk_id: int


class ImportGraphState(TypedDict, total=False):
    """在文档导入节点之间传递的数据。"""

    task_id: str
    import_file_path: str
    file_dir: str
    source_kind: Literal["pdf", "md"]
    is_pdf_read_enabled: bool
    is_md_read_enabled: bool
    pdf_path: str
    md_path: str
    file_title: str
    md_content: str
    uploaded_image_urls: dict[str, str]
    chunks: list[DocumentChunk]
    chunks_path: str
    item_name: str
    item_name_source: Literal["", "qwen", "file_title_fallback"]
    item_name_chunks_path: str
    embeddings: list[list[float]]
    embedding_chunks_path: str
    milvus_ids: list[int]
    milvus_collection_name: str
    milvus_chunks_path: str
    completed_nodes: list[str]
    node_durations_ms: dict[str, float]
    _progress_callback: ImportProgressCallback


DEFAULT_IMPORT_STATE: ImportGraphState = {
    "task_id": "",
    "import_file_path": "",
    "file_dir": "",
    "is_pdf_read_enabled": False,
    "is_md_read_enabled": False,
    "pdf_path": "",
    "md_path": "",
    "file_title": "",
    "md_content": "",
    "uploaded_image_urls": {},
    "chunks": [],
    "chunks_path": "",
    "item_name": "",
    "item_name_source": "",
    "item_name_chunks_path": "",
    "embeddings": [],
    "embedding_chunks_path": "",
    "milvus_ids": [],
    "milvus_collection_name": "",
    "milvus_chunks_path": "",
    "completed_nodes": [],
    "node_durations_ms": {},
}


def create_import_state(
    import_file_path: str,
    *,
    file_dir: str = "",
    task_id: str = "",
    progress_callback: ImportProgressCallback | None = None,
) -> ImportGraphState:
    """创建相互隔离的导入初始状态。"""

    state = deepcopy(DEFAULT_IMPORT_STATE)
    state.update(
        {
            "task_id": task_id,
            "import_file_path": import_file_path,
            "file_dir": file_dir,
        }
    )
    if progress_callback is not None:
        state["_progress_callback"] = progress_callback
    return state
