"""Milvus 稠密、稀疏向量混合检索封装。"""

from __future__ import annotations

from collections.abc import Mapping
from math import isfinite
from typing import Any, TypedDict

from pymilvus import AnnSearchRequest, MilvusClient, WeightedRanker

from app.clients.milvus_storage import DENSE_VECTOR_FIELD, SPARSE_VECTOR_FIELD
from app.core.config import Settings, get_settings

SEARCH_OUTPUT_FIELDS = [
    "content",
    "title",
    "parent_title",
    "file_title",
    "item_name",
    "part",
]


class MilvusSearchError(Exception):
    """Milvus 查询配置、连接或返回数据异常。"""


class MilvusSearchHit(TypedDict):
    """经过安全解析的单个知识片段召回结果。"""

    chunk_id: int
    score: float
    content: str
    title: str
    parent_title: str
    file_title: str
    item_name: str
    part: int | None


class MilvusHybridSearcher:
    """使用 WeightedRanker 合并稠密和稀疏向量召回。"""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        client: MilvusClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.client = client

    def search(
        self,
        dense_vector: list[float],
        sparse_vector: dict[int, float],
        *,
        item_names: list[str] | None = None,
        limit: int | None = None,
    ) -> list[MilvusSearchHit]:
        """查询知识片段，并在识别到商品名时使用参数化标量过滤。"""

        dense, sparse, normalized_names, result_limit = self._validate_inputs(
            dense_vector,
            sparse_vector,
            item_names or [],
            self.settings.query_search_limit if limit is None else limit,
        )
        expression = "item_name in {item_names}" if normalized_names else None
        expression_params = {"item_names": normalized_names} if normalized_names else None
        requests = [
            AnnSearchRequest(
                data=[dense],
                anns_field=DENSE_VECTOR_FIELD,
                param={"metric_type": self.settings.milvus_metric_type, "params": {}},
                limit=result_limit,
                expr=expression,
                expr_params=expression_params,
            ),
            AnnSearchRequest(
                data=[sparse],
                anns_field=SPARSE_VECTOR_FIELD,
                param={"metric_type": "IP", "params": {}},
                limit=result_limit,
                expr=expression,
                expr_params=expression_params,
            ),
        ]
        ranker = WeightedRanker(
            self.settings.query_dense_weight,
            self.settings.query_sparse_weight,
            norm_score=True,
        )

        owns_client = self.client is None
        client: MilvusClient | None = self.client
        try:
            if client is None:
                client = MilvusClient(uri=self.settings.milvus_url)
            if not client.has_collection(
                collection_name=self.settings.chunks_collection,
                timeout=self.settings.milvus_request_timeout_seconds,
            ):
                raise MilvusSearchError("知识片段集合不存在，请先导入文档")
            client.load_collection(
                collection_name=self.settings.chunks_collection,
                timeout=self.settings.milvus_request_timeout_seconds,
            )
            raw_results = client.hybrid_search(
                collection_name=self.settings.chunks_collection,
                reqs=requests,
                ranker=ranker,
                limit=result_limit,
                output_fields=SEARCH_OUTPUT_FIELDS,
                timeout=self.settings.milvus_request_timeout_seconds,
            )
        except MilvusSearchError:
            raise
        except Exception as exc:
            raise MilvusSearchError("Milvus 混合检索失败") from exc
        finally:
            if owns_client and client is not None:
                client.close()

        return self._parse_results(raw_results)

    def _validate_inputs(
        self,
        dense_vector: list[float],
        sparse_vector: dict[int, float],
        item_names: list[str],
        limit: int,
    ) -> tuple[list[float], dict[int, float], list[str], int]:
        if not isinstance(dense_vector, list) or not dense_vector:
            raise MilvusSearchError("查询缺少稠密向量")
        try:
            dense = [float(value) for value in dense_vector]
        except (TypeError, ValueError) as exc:
            raise MilvusSearchError("查询稠密向量包含无效数值") from exc
        if not all(isfinite(value) for value in dense):
            raise MilvusSearchError("查询稠密向量包含非有限数值")
        if len(dense) != self.settings.embedding_dimension:
            raise MilvusSearchError(
                f"查询稠密向量维度不是配置值 {self.settings.embedding_dimension}"
            )

        if not isinstance(sparse_vector, dict) or not sparse_vector:
            raise MilvusSearchError("查询缺少稀疏向量")
        sparse: dict[int, float] = {}
        for index, value in sparse_vector.items():
            if not isinstance(index, int) or isinstance(index, bool) or index < 0:
                raise MilvusSearchError("查询稀疏向量索引无效")
            try:
                weight = float(value)
            except (TypeError, ValueError) as exc:
                raise MilvusSearchError("查询稀疏向量权重无效") from exc
            if not isfinite(weight):
                raise MilvusSearchError("查询稀疏向量包含非有限数值")
            sparse[index] = weight

        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 20:
            raise MilvusSearchError("查询结果数量必须在 1 到 20 之间")
        normalized_names: list[str] = []
        for item_name in item_names:
            if not isinstance(item_name, str) or not item_name.strip():
                raise MilvusSearchError("商品名称过滤条件无效")
            normalized_name = item_name.strip()
            if len(normalized_name) > 200:
                raise MilvusSearchError("商品名称过滤条件超过长度限制")
            normalized_names.append(normalized_name)
        if len(normalized_names) > self.settings.query_item_name_max_count:
            raise MilvusSearchError("商品名称过滤条件数量超过限制")
        return dense, sparse, normalized_names, limit

    @classmethod
    def _parse_results(cls, raw_results: Any) -> list[MilvusSearchHit]:
        if not isinstance(raw_results, list) or len(raw_results) != 1:
            raise MilvusSearchError("Milvus 混合检索响应结构不完整")
        raw_hits = raw_results[0]
        if not isinstance(raw_hits, list):
            raise MilvusSearchError("Milvus 混合检索结果格式无效")

        hits: list[MilvusSearchHit] = []
        for raw_hit in raw_hits:
            hit = cls._as_mapping(raw_hit)
            entity = cls._as_mapping(hit.get("entity", {}))
            chunk_id = hit.get("id")
            score = hit.get("distance")
            if not isinstance(chunk_id, int) or isinstance(chunk_id, bool):
                raise MilvusSearchError("Milvus 结果缺少有效 chunk_id")
            try:
                numeric_score = float(score)
            except (TypeError, ValueError) as exc:
                raise MilvusSearchError("Milvus 结果缺少有效分数") from exc
            if not isfinite(numeric_score):
                raise MilvusSearchError("Milvus 结果分数不是有限数值")

            content = entity.get("content", "")
            if not isinstance(content, str) or not content.strip():
                raise MilvusSearchError("Milvus 结果缺少知识片段正文")
            part = entity.get("part")
            if part is not None and (
                not isinstance(part, int) or isinstance(part, bool) or part < 1
            ):
                raise MilvusSearchError("Milvus 结果 part 字段无效")
            hits.append(
                {
                    "chunk_id": chunk_id,
                    "score": numeric_score,
                    "content": content,
                    "title": cls._text_field(entity, "title"),
                    "parent_title": cls._text_field(entity, "parent_title"),
                    "file_title": cls._text_field(entity, "file_title"),
                    "item_name": cls._text_field(entity, "item_name"),
                    "part": part,
                }
            )
        return hits

    @staticmethod
    def _as_mapping(value: Any) -> Mapping[str, Any]:
        if isinstance(value, Mapping):
            return value
        raise MilvusSearchError("Milvus 混合检索结果元素格式无效")

    @staticmethod
    def _text_field(entity: Mapping[str, Any], field_name: str) -> str:
        value = entity.get(field_name, "")
        if not isinstance(value, str):
            raise MilvusSearchError(f"Milvus 结果 {field_name} 字段无效")
        return value
