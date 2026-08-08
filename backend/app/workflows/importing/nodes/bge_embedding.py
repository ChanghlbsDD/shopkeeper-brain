"""使用百炼云端 API 为文档片段生成混合向量。"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path

from app.clients.dashscope_embedding import (
    DashScopeEmbeddingClient,
    DashScopeEmbeddingError,
    TextEmbedding,
)
from app.core.config import get_settings
from app.workflows.importing.base import BaseNode
from app.workflows.importing.exceptions import EmbeddingError, ImportValidationError
from app.workflows.importing.state import DocumentChunk, ImportGraphState

DocumentEmbedder = Callable[[list[str]], list[TextEmbedding]]


class BgeEmbeddingNode(BaseNode):
    """保留课程节点名，实际用云端模型生成稠密和稀疏向量。"""

    name = "bge_embedding_node"

    def __init__(
        self,
        *,
        embedder: DocumentEmbedder | None = None,
        batch_size: int | None = None,
        backup_enabled: bool | None = None,
    ) -> None:
        super().__init__()
        self.embedder = embedder
        self.batch_size = batch_size
        self.backup_enabled = backup_enabled

    def process(self, state: ImportGraphState) -> Mapping[str, object]:
        self.log_step("1/4", "校验 chunks、商品名称和批量配置")
        chunks, batch_size = self._validate_inputs(state)

        self.log_step("2/4", "拼接商品名称与切片正文")
        embedding_texts = [self._build_embedding_text(chunk) for chunk in chunks]

        self.log_step("3/4", "分批调用百炼生成稠密和稀疏向量")
        embeddings: list[TextEmbedding] = []
        embedder = self.embedder or self._embed_with_dashscope
        try:
            for start in range(0, len(embedding_texts), batch_size):
                batch = embedding_texts[start : start + batch_size]
                batch_embeddings = embedder(batch)
                if len(batch_embeddings) != len(batch):
                    raise DashScopeEmbeddingError("向量数量与当前批次文本数量不一致")
                embeddings.extend(batch_embeddings)
        except DashScopeEmbeddingError as exc:
            raise EmbeddingError(str(exc), node_name=self.name, cause=exc) from exc

        updated_chunks: list[DocumentChunk] = []
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            updated_chunks.append(
                {
                    **chunk,
                    "dense_vector": embedding.dense_vector,
                    "sparse_vector": embedding.sparse_vector,
                }
            )

        self.log_step("4/4", "写回混合向量并按配置备份")
        backup_path = self._backup_chunks(state, updated_chunks)
        return {
            "chunks": updated_chunks,
            "embeddings": [embedding.dense_vector for embedding in embeddings],
            "embedding_chunks_path": str(backup_path) if backup_path else "",
        }

    def _validate_inputs(
        self,
        state: ImportGraphState,
    ) -> tuple[list[DocumentChunk], int]:
        chunks = state.get("chunks")
        if not isinstance(chunks, list) or not chunks:
            raise ImportValidationError("向量化缺少有效 chunks", node_name=self.name)
        if not all(isinstance(chunk, dict) for chunk in chunks):
            raise ImportValidationError("chunks 中包含无效元素", node_name=self.name)

        settings = get_settings()
        batch_size = settings.embedding_batch_size if self.batch_size is None else self.batch_size
        if not 1 <= batch_size <= 10:
            raise ImportValidationError(
                "向量化批次大小必须在 1 到 10 之间",
                node_name=self.name,
            )
        return chunks, batch_size

    def _build_embedding_text(self, chunk: DocumentChunk) -> str:
        item_name = chunk.get("item_name", "")
        content = chunk.get("content", "")
        if not isinstance(item_name, str) or not item_name.strip():
            raise ImportValidationError("chunk 缺少商品名称", node_name=self.name)
        if not isinstance(content, str) or not content.strip():
            raise ImportValidationError("chunk 缺少正文", node_name=self.name)
        return f"{item_name.strip()}\n{content.strip()}"

    @staticmethod
    def _embed_with_dashscope(texts: list[str]) -> list[TextEmbedding]:
        settings = get_settings()
        client = DashScopeEmbeddingClient(
            base_url=settings.dashscope_api_base,
            api_key=settings.dashscope_api_key,
            model=settings.embedding_model,
            dimension=settings.embedding_dimension,
            max_batch_size=10,
            timeout_seconds=settings.embedding_request_timeout_seconds,
        )
        return client.embed_documents(texts)

    def _backup_chunks(
        self,
        state: ImportGraphState,
        chunks: list[DocumentChunk],
    ) -> Path | None:
        settings = get_settings()
        enabled = (
            settings.embedding_backup_enabled
            if self.backup_enabled is None
            else self.backup_enabled
        )
        if not enabled:
            return None

        md_path = Path(state.get("md_path", ""))
        if md_path.name:
            output_path = md_path.with_name(f"{md_path.stem}_vectors.json")
        else:
            output_directory = Path(state.get("file_dir", "") or ".")
            output_path = output_directory / "chunks_vectors.json"
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(chunks, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            self.logger.warning("Embedding chunks backup failed: %s", type(exc).__name__)
            return None
        return output_path.resolve()
