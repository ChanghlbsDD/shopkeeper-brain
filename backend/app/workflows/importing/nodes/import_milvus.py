"""将向量化后的知识片段写入 Milvus。"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from math import isfinite
from pathlib import Path
from typing import Any

from pymilvus import MilvusClient

from app.clients.milvus_storage import MAX_VARCHAR_BYTES, MilvusChunkStore, MilvusStorageError
from app.core.config import get_settings
from app.workflows.importing.base import BaseNode
from app.workflows.importing.exceptions import ImportValidationError, MilvusImportError
from app.workflows.importing.state import DocumentChunk, ImportGraphState

ChunkImporter = Callable[[list[dict[str, Any]], int, str, int], list[int]]
COLLECTION_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class ImportMilvusNode(BaseNode):
    """校验混合向量，确保集合存在，批量入库并回填主键。"""

    name = "import_milvus_node"

    def __init__(
        self,
        *,
        importer: ChunkImporter | None = None,
        collection_name: str | None = None,
        insert_batch_size: int | None = None,
        backup_enabled: bool | None = None,
    ) -> None:
        super().__init__()
        self.importer = importer
        self.collection_name = collection_name
        self.insert_batch_size = insert_batch_size
        self.backup_enabled = backup_enabled

    def process(self, state: ImportGraphState) -> Mapping[str, object]:
        self.log_step("1/4", "校验 chunks、混合向量和 Milvus 配置")
        chunks, entities, dimension, collection_name, batch_size = self._validate_inputs(state)

        self.log_step("2/4", "确保 Milvus 集合、字段和索引兼容")
        try:
            chunk_ids = (self.importer or self._import_with_milvus)(
                entities,
                dimension,
                collection_name,
                batch_size,
            )
        except MilvusStorageError as exc:
            raise MilvusImportError(str(exc), node_name=self.name, cause=exc) from exc
        except Exception as exc:
            raise MilvusImportError(
                f"Milvus 写入失败：{type(exc).__name__}",
                node_name=self.name,
                cause=exc,
            ) from exc

        if len(chunk_ids) != len(chunks):
            raise MilvusImportError("Milvus 主键数量与 chunks 不一致", node_name=self.name)

        self.log_step("3/4", "把 Milvus 自动主键回填到 chunks")
        updated_chunks: list[DocumentChunk] = [
            {**chunk, "chunk_id": chunk_id}
            for chunk, chunk_id in zip(chunks, chunk_ids, strict=True)
        ]

        self.log_step("4/4", "按配置备份入库结果")
        backup_path = self._backup_chunks(state, updated_chunks)
        return {
            "chunks": updated_chunks,
            "milvus_ids": chunk_ids,
            "milvus_collection_name": collection_name,
            "milvus_chunks_path": str(backup_path) if backup_path else "",
        }

    def _validate_inputs(
        self,
        state: ImportGraphState,
    ) -> tuple[list[DocumentChunk], list[dict[str, Any]], int, str, int]:
        chunks = state.get("chunks")
        if not isinstance(chunks, list) or not chunks:
            raise ImportValidationError("Milvus 入库缺少有效 chunks", node_name=self.name)
        if not all(isinstance(chunk, dict) for chunk in chunks):
            raise ImportValidationError("chunks 中包含无效元素", node_name=self.name)

        settings = get_settings()
        collection_name = (
            settings.chunks_collection if self.collection_name is None else self.collection_name
        )
        if len(collection_name) > 255 or COLLECTION_NAME_PATTERN.fullmatch(collection_name) is None:
            raise ImportValidationError("Milvus 集合名称不合法", node_name=self.name)
        batch_size = (
            settings.milvus_insert_batch_size
            if self.insert_batch_size is None
            else self.insert_batch_size
        )
        if not 1 <= batch_size <= 1000:
            raise ImportValidationError(
                "Milvus 写入批次大小必须在 1 到 1000 之间",
                node_name=self.name,
            )

        entities: list[dict[str, Any]] = []
        dimension: int | None = None
        for index, chunk in enumerate(chunks, start=1):
            entity, chunk_dimension = self._validate_chunk(chunk, index)
            if dimension is None:
                dimension = chunk_dimension
            elif chunk_dimension != dimension:
                raise ImportValidationError(
                    "chunks 的稠密向量维度不一致",
                    node_name=self.name,
                )
            entities.append(entity)

        if dimension is None:
            raise ImportValidationError("Milvus 入库没有可用向量", node_name=self.name)
        return chunks, entities, dimension, collection_name, batch_size

    def _validate_chunk(
        self,
        chunk: DocumentChunk,
        index: int,
    ) -> tuple[dict[str, Any], int]:
        entity: dict[str, Any] = {}
        for field_name in ("content", "title", "parent_title", "file_title", "item_name"):
            value = chunk.get(field_name, "")
            if not isinstance(value, str):
                raise ImportValidationError(
                    f"第 {index} 个 chunk 的 {field_name} 必须是字符串",
                    node_name=self.name,
                )
            normalized = value.strip()
            if field_name in {"content", "file_title", "item_name"} and not normalized:
                raise ImportValidationError(
                    f"第 {index} 个 chunk 缺少 {field_name}",
                    node_name=self.name,
                )
            if len(normalized.encode("utf-8")) > MAX_VARCHAR_BYTES:
                raise ImportValidationError(
                    f"第 {index} 个 chunk 的 {field_name} 超过 Milvus 长度限制",
                    node_name=self.name,
                )
            entity[field_name] = normalized

        dense_vector = chunk.get("dense_vector")
        if not isinstance(dense_vector, list) or len(dense_vector) < 2:
            raise ImportValidationError(
                f"第 {index} 个 chunk 缺少有效稠密向量",
                node_name=self.name,
            )
        normalized_dense: list[float] = []
        for value in dense_vector:
            if isinstance(value, bool):
                raise ImportValidationError("稠密向量包含无效数值", node_name=self.name)
            try:
                numeric_value = float(value)
            except (TypeError, ValueError) as exc:
                raise ImportValidationError("稠密向量包含无效数值", node_name=self.name) from exc
            if not isfinite(numeric_value):
                raise ImportValidationError("稠密向量包含非有限数值", node_name=self.name)
            normalized_dense.append(numeric_value)
        entity["dense_vector"] = normalized_dense

        sparse_vector = chunk.get("sparse_vector")
        if not isinstance(sparse_vector, dict) or not sparse_vector:
            raise ImportValidationError(
                f"第 {index} 个 chunk 缺少有效稀疏向量",
                node_name=self.name,
            )
        normalized_sparse: dict[int, float] = {}
        for sparse_index, weight in sparse_vector.items():
            if (
                not isinstance(sparse_index, int)
                or isinstance(sparse_index, bool)
                or sparse_index < 0
            ):
                raise ImportValidationError("稀疏向量索引无效", node_name=self.name)
            if isinstance(weight, bool):
                raise ImportValidationError("稀疏向量权重无效", node_name=self.name)
            try:
                numeric_weight = float(weight)
            except (TypeError, ValueError) as exc:
                raise ImportValidationError("稀疏向量权重无效", node_name=self.name) from exc
            if not isfinite(numeric_weight):
                raise ImportValidationError("稀疏向量包含非有限数值", node_name=self.name)
            normalized_sparse[sparse_index] = numeric_weight
        entity["sparse_vector"] = normalized_sparse

        part = chunk.get("part")
        if part is not None:
            if not isinstance(part, int) or isinstance(part, bool) or part < 1:
                raise ImportValidationError("chunk 的 part 必须是正整数", node_name=self.name)
            entity["part"] = part
        return entity, len(normalized_dense)

    @staticmethod
    def _import_with_milvus(
        entities: list[dict[str, Any]],
        dimension: int,
        collection_name: str,
        batch_size: int,
    ) -> list[int]:
        settings = get_settings()
        client = MilvusClient(uri=settings.milvus_url)
        try:
            store = MilvusChunkStore(
                client,
                collection_name=collection_name,
                timeout_seconds=settings.milvus_request_timeout_seconds,
                dense_metric_type=settings.milvus_metric_type,
            )
            store.ensure_collection(dimension)
            return store.insert_entities(entities, batch_size=batch_size)
        finally:
            client.close()

    def _backup_chunks(
        self,
        state: ImportGraphState,
        chunks: list[DocumentChunk],
    ) -> Path | None:
        settings = get_settings()
        enabled = (
            settings.milvus_backup_enabled if self.backup_enabled is None else self.backup_enabled
        )
        if not enabled:
            return None

        md_path = Path(state.get("md_path", ""))
        if md_path.name:
            output_path = md_path.with_name(f"{md_path.stem}_milvus_chunks.json")
        else:
            output_directory = Path(state.get("file_dir", "") or ".")
            output_path = output_directory / "milvus_chunks.json"
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(chunks, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            self.logger.warning("Milvus chunks backup failed: %s", type(exc).__name__)
            return None
        return output_path.resolve()
