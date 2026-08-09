"""从知识片段集合中按商品名称分组召回候选。"""

from __future__ import annotations

from collections.abc import Mapping
from math import isfinite
from typing import Any, TypedDict

from pymilvus import AnnSearchRequest, MilvusClient, WeightedRanker

from app.clients.milvus_storage import DENSE_VECTOR_FIELD, SPARSE_VECTOR_FIELD
from app.core.config import Settings, get_settings


class MilvusItemNameSearchError(Exception):
    """商品名称候选检索配置、连接或响应异常。"""


class ItemNameCandidate(TypedDict):
    """知识库中的标准商品名称及其融合相似度。"""

    item_name: str
    score: float


class MilvusItemNameSearcher:
    """复用知识片段向量，并按 item_name 分组保证候选多样性。"""

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
        limit: int | None = None,
    ) -> list[ItemNameCandidate]:
        """以商品名查询向量召回互不重复的标准商品名称。"""

        result_limit = self.settings.query_item_name_candidate_limit if limit is None else limit
        dense, sparse = self._validate_inputs(dense_vector, sparse_vector, result_limit)
        candidate_pool_limit = min(result_limit * 10, 200)
        requests = [
            AnnSearchRequest(
                data=[dense],
                anns_field=DENSE_VECTOR_FIELD,
                param={"metric_type": self.settings.milvus_metric_type, "params": {}},
                limit=candidate_pool_limit,
            ),
            AnnSearchRequest(
                data=[sparse],
                anns_field=SPARSE_VECTOR_FIELD,
                param={"metric_type": "IP", "params": {}},
                limit=candidate_pool_limit,
            ),
        ]
        ranker = WeightedRanker(
            self.settings.query_item_name_dense_weight,
            self.settings.query_item_name_sparse_weight,
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
                raise MilvusItemNameSearchError("知识片段集合不存在，请先导入文档")
            client.load_collection(
                collection_name=self.settings.chunks_collection,
                timeout=self.settings.milvus_request_timeout_seconds,
            )
            raw_results = client.hybrid_search(
                collection_name=self.settings.chunks_collection,
                reqs=requests,
                ranker=ranker,
                limit=result_limit,
                output_fields=["item_name"],
                timeout=self.settings.milvus_request_timeout_seconds,
                group_by_field="item_name",
                group_size=1,
                strict_group_size=False,
            )
        except MilvusItemNameSearchError:
            raise
        except Exception as exc:
            raise MilvusItemNameSearchError("Milvus 商品名称候选检索失败") from exc
        finally:
            if owns_client and client is not None:
                client.close()

        return self._parse_results(raw_results, result_limit)

    def _validate_inputs(
        self,
        dense_vector: list[float],
        sparse_vector: dict[int, float],
        limit: int,
    ) -> tuple[list[float], dict[int, float]]:
        if not isinstance(dense_vector, list) or not dense_vector:
            raise MilvusItemNameSearchError("商品名查询缺少稠密向量")
        try:
            dense = [float(value) for value in dense_vector]
        except (TypeError, ValueError) as exc:
            raise MilvusItemNameSearchError("商品名稠密向量包含无效数值") from exc
        if len(dense) != self.settings.embedding_dimension:
            raise MilvusItemNameSearchError(
                f"商品名稠密向量维度不是配置值 {self.settings.embedding_dimension}"
            )
        if not all(isfinite(value) for value in dense):
            raise MilvusItemNameSearchError("商品名稠密向量包含非有限数值")

        if not isinstance(sparse_vector, dict) or not sparse_vector:
            raise MilvusItemNameSearchError("商品名查询缺少稀疏向量")
        sparse: dict[int, float] = {}
        for index, value in sparse_vector.items():
            if not isinstance(index, int) or isinstance(index, bool) or index < 0:
                raise MilvusItemNameSearchError("商品名稀疏向量索引无效")
            try:
                weight = float(value)
            except (TypeError, ValueError) as exc:
                raise MilvusItemNameSearchError("商品名稀疏向量权重无效") from exc
            if not isfinite(weight):
                raise MilvusItemNameSearchError("商品名稀疏向量包含非有限数值")
            sparse[index] = weight
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 20:
            raise MilvusItemNameSearchError("商品名称候选数量必须在 1 到 20 之间")
        return dense, sparse

    @staticmethod
    def _parse_results(raw_results: Any, limit: int) -> list[ItemNameCandidate]:
        if not isinstance(raw_results, list) or len(raw_results) != 1:
            raise MilvusItemNameSearchError("Milvus 商品名称响应结构不完整")
        raw_hits = raw_results[0]
        if not isinstance(raw_hits, list):
            raise MilvusItemNameSearchError("Milvus 商品名称结果格式无效")

        candidates_by_key: dict[str, ItemNameCandidate] = {}
        for raw_hit in raw_hits:
            if not isinstance(raw_hit, Mapping):
                raise MilvusItemNameSearchError("Milvus 商品名称结果元素无效")
            entity = raw_hit.get("entity", {})
            if not isinstance(entity, Mapping):
                raise MilvusItemNameSearchError("Milvus 商品名称实体格式无效")
            item_name = entity.get("item_name")
            if not isinstance(item_name, str) or not item_name.strip():
                raise MilvusItemNameSearchError("Milvus 商品名称结果缺少名称")
            try:
                score = float(raw_hit.get("distance"))
            except (TypeError, ValueError) as exc:
                raise MilvusItemNameSearchError("Milvus 商品名称结果缺少分数") from exc
            if not isfinite(score):
                raise MilvusItemNameSearchError("Milvus 商品名称分数不是有限数值")

            normalized_name = item_name.strip()
            key = normalized_name.casefold()
            previous = candidates_by_key.get(key)
            if previous is None or score > previous["score"]:
                candidates_by_key[key] = {"item_name": normalized_name, "score": score}
        return sorted(
            candidates_by_key.values(),
            key=lambda candidate: candidate["score"],
            reverse=True,
        )[:limit]
