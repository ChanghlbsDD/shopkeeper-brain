"""Milvus 知识片段集合、索引和批量写入封装。"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pymilvus import DataType, MilvusClient
from pymilvus.orm.schema import CollectionSchema

CHUNK_ID_FIELD = "chunk_id"
DENSE_VECTOR_FIELD = "dense_vector"
SPARSE_VECTOR_FIELD = "sparse_vector"
DENSE_INDEX_NAME = "dense_vector_index"
SPARSE_INDEX_NAME = "sparse_vector_index"
MAX_VARCHAR_BYTES = 65_535

SCALAR_TEXT_FIELDS: tuple[str, ...] = (
    "content",
    "title",
    "parent_title",
    "file_title",
    "item_name",
)


class MilvusStorageError(Exception):
    """Milvus 集合不兼容或写入响应不完整。"""


class MilvusChunkStore:
    """确保知识片段集合可用，并以可回滚批次写入数据。"""

    def __init__(
        self,
        client: MilvusClient,
        *,
        collection_name: str,
        timeout_seconds: float,
        dense_metric_type: str = "COSINE",
    ) -> None:
        self.client = client
        self.collection_name = collection_name
        self.timeout_seconds = timeout_seconds
        self.dense_metric_type = dense_metric_type

    def ensure_collection(self, dimension: int) -> None:
        """创建集合和索引，或确认已有集合与当前向量兼容。"""

        if self.client.has_collection(
            collection_name=self.collection_name,
            timeout=self.timeout_seconds,
        ):
            description = self.client.describe_collection(
                collection_name=self.collection_name,
                timeout=self.timeout_seconds,
            )
            self._validate_collection(description, dimension)
            self._ensure_existing_indexes()
            return

        schema = self._build_schema(dimension)
        index_params = self._build_index_params(
            include_dense=True,
            include_sparse=True,
        )
        self.client.create_collection(
            collection_name=self.collection_name,
            schema=schema,
            index_params=index_params,
            consistency_level="Session",
            timeout=self.timeout_seconds,
        )

    def insert_entities(
        self,
        entities: list[dict[str, Any]],
        *,
        batch_size: int,
    ) -> list[int]:
        """分批插入实体；后续批次失败时尽力删除已写入的批次。"""

        inserted_ids: list[int] = []
        try:
            for start in range(0, len(entities), batch_size):
                batch = entities[start : start + batch_size]
                result = self.client.insert(
                    collection_name=self.collection_name,
                    data=batch,
                    timeout=self.timeout_seconds,
                )
                inserted_ids.extend(self._validate_insert_result(result, len(batch)))
        except Exception:
            self._rollback(inserted_ids)
            raise

        self.client.flush(
            collection_name=self.collection_name,
            timeout=self.timeout_seconds,
        )
        return inserted_ids

    def _build_schema(self, dimension: int) -> CollectionSchema:
        schema = self.client.create_schema(
            auto_id=True,
            enable_dynamic_field=False,
        )
        schema.add_field(
            field_name=CHUNK_ID_FIELD,
            datatype=DataType.INT64,
            is_primary=True,
            auto_id=True,
        )
        schema.add_field(
            field_name=DENSE_VECTOR_FIELD,
            datatype=DataType.FLOAT_VECTOR,
            dim=dimension,
        )
        schema.add_field(
            field_name=SPARSE_VECTOR_FIELD,
            datatype=DataType.SPARSE_FLOAT_VECTOR,
        )
        for field_name in SCALAR_TEXT_FIELDS:
            schema.add_field(
                field_name=field_name,
                datatype=DataType.VARCHAR,
                max_length=MAX_VARCHAR_BYTES,
            )
        schema.add_field(
            field_name="part",
            datatype=DataType.INT64,
            nullable=True,
        )
        return schema

    def _build_index_params(
        self,
        *,
        include_dense: bool,
        include_sparse: bool,
    ) -> Any:
        index_params = self.client.prepare_index_params()
        if include_dense:
            index_params.add_index(
                field_name=DENSE_VECTOR_FIELD,
                index_name=DENSE_INDEX_NAME,
                index_type="AUTOINDEX",
                metric_type=self.dense_metric_type,
            )
        if include_sparse:
            index_params.add_index(
                field_name=SPARSE_VECTOR_FIELD,
                index_name=SPARSE_INDEX_NAME,
                index_type="SPARSE_INVERTED_INDEX",
                metric_type="IP",
                params={"inverted_index_algo": "DAAT_MAXSCORE"},
            )
        return index_params

    def _validate_collection(self, description: Any, dimension: int) -> None:
        if not isinstance(description, dict):
            raise MilvusStorageError("Milvus 集合描述格式无效")
        if description.get("auto_id") is not True:
            raise MilvusStorageError("已有 Milvus 集合没有启用自动主键")

        raw_fields = description.get("fields")
        if not isinstance(raw_fields, list):
            raise MilvusStorageError("已有 Milvus 集合缺少字段描述")
        fields = {
            field.get("name"): field
            for field in raw_fields
            if isinstance(field, dict) and isinstance(field.get("name"), str)
        }

        expected_types = {
            CHUNK_ID_FIELD: DataType.INT64,
            DENSE_VECTOR_FIELD: DataType.FLOAT_VECTOR,
            SPARSE_VECTOR_FIELD: DataType.SPARSE_FLOAT_VECTOR,
            **{field_name: DataType.VARCHAR for field_name in SCALAR_TEXT_FIELDS},
        }
        for field_name, expected_type in expected_types.items():
            field = fields.get(field_name)
            if field is None:
                raise MilvusStorageError(f"已有 Milvus 集合缺少字段 {field_name}")
            if field.get("type") != expected_type:
                raise MilvusStorageError(f"已有 Milvus 集合字段 {field_name} 类型不兼容")

        dense_params = fields[DENSE_VECTOR_FIELD].get("params", {})
        try:
            existing_dimension = int(dense_params.get("dim"))
        except (TypeError, ValueError) as exc:
            raise MilvusStorageError("已有 Milvus 集合缺少稠密向量维度") from exc
        if existing_dimension != dimension:
            raise MilvusStorageError(
                f"已有 Milvus 集合维度为 {existing_dimension}，当前向量维度为 {dimension}"
            )

        part_field = fields.get("part")
        dynamic_enabled = description.get("enable_dynamic_field") is True
        if part_field is None and not dynamic_enabled:
            raise MilvusStorageError("已有 Milvus 集合缺少可选字段 part")
        if part_field is not None and part_field.get("type") != DataType.INT64:
            raise MilvusStorageError("已有 Milvus 集合字段 part 类型不兼容")

    def _ensure_existing_indexes(self) -> None:
        existing_names = set(
            self.client.list_indexes(
                collection_name=self.collection_name,
                timeout=self.timeout_seconds,
            )
        )
        expected = {
            DENSE_INDEX_NAME: (DENSE_VECTOR_FIELD, self.dense_metric_type),
            SPARSE_INDEX_NAME: (SPARSE_VECTOR_FIELD, "IP"),
        }
        for index_name in existing_names & expected.keys():
            description = self.client.describe_index(
                collection_name=self.collection_name,
                index_name=index_name,
                timeout=self.timeout_seconds,
            )
            expected_field, expected_metric = expected[index_name]
            if (
                not isinstance(description, dict)
                or description.get("field_name") != expected_field
                or description.get("metric_type") != expected_metric
            ):
                raise MilvusStorageError(f"已有 Milvus 索引 {index_name} 配置不兼容")

        missing_dense = DENSE_INDEX_NAME not in existing_names
        missing_sparse = SPARSE_INDEX_NAME not in existing_names
        if missing_dense or missing_sparse:
            index_params = self._build_index_params(
                include_dense=missing_dense,
                include_sparse=missing_sparse,
            )
            self.client.create_index(
                collection_name=self.collection_name,
                index_params=index_params,
                timeout=self.timeout_seconds,
            )

    @staticmethod
    def _validate_insert_result(result: Any, expected_count: int) -> list[int]:
        if not isinstance(result, dict) or result.get("insert_count") != expected_count:
            raise MilvusStorageError("Milvus 返回的写入数量不正确")
        raw_ids = result.get("ids")
        if not isinstance(raw_ids, Sequence) or isinstance(raw_ids, (str, bytes)):
            raise MilvusStorageError("Milvus 没有返回自动生成的主键")
        ids = list(raw_ids)
        if len(ids) != expected_count or any(
            not isinstance(item_id, int) or isinstance(item_id, bool) for item_id in ids
        ):
            raise MilvusStorageError("Milvus 返回的主键数量或类型不正确")
        return ids

    def _rollback(self, inserted_ids: list[int]) -> None:
        if not inserted_ids:
            return
        try:
            self.client.delete(
                collection_name=self.collection_name,
                ids=inserted_ids,
                timeout=self.timeout_seconds,
            )
            self.client.flush(
                collection_name=self.collection_name,
                timeout=self.timeout_seconds,
            )
        except Exception:
            # 回滚失败不能覆盖触发回滚的原始异常。
            return
