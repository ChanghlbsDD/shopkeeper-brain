"""直接向量与 HyDE 检索结果的倒数排名融合。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Literal, cast

from app.clients.milvus_search import MilvusSearchHit
from app.core.config import Settings, get_settings
from app.workflows.querying.base import BaseQueryNode
from app.workflows.querying.exceptions import QueryValidationError
from app.workflows.querying.state import QueryGraphState, RrfSearchHit

RrfSource = Literal["vector", "hyde"]


class RrfNode(BaseQueryNode):
    """按 ``weight / (k + rank)`` 融合两路本地召回并按 chunk 去重。"""

    name = "rrf_node"

    def __init__(self, *, settings: Settings | None = None) -> None:
        super().__init__()
        self.settings = settings or get_settings()

    def process(self, state: QueryGraphState) -> Mapping[str, object]:
        vector_results = state.get("search_results", [])
        hyde_results = state.get("hyde_search_results", [])
        if not isinstance(vector_results, list) or not isinstance(hyde_results, list):
            raise QueryValidationError("RRF 输入必须是检索结果列表", node_name=self.name)

        fused = self.fuse(
            [
                ("vector", vector_results, self.settings.query_rrf_vector_weight),
                ("hyde", hyde_results, self.settings.query_rrf_hyde_weight),
            ],
            k=self.settings.query_rrf_k,
            max_results=self.settings.query_rrf_max_results,
        )
        self.logger.info("RRF fusion completed with %d results", len(fused))
        return {"rrf_results": fused}

    @staticmethod
    def fuse(
        sources: Sequence[tuple[RrfSource, list[MilvusSearchHit], float]],
        *,
        k: int,
        max_results: int,
    ) -> list[RrfSearchHit]:
        """融合多路有序结果；同一路重复 chunk 只计分一次。"""

        scores: dict[int, float] = {}
        documents: dict[int, MilvusSearchHit] = {}
        source_paths: dict[int, list[RrfSource]] = {}
        first_seen_order: dict[int, int] = {}

        for source_name, raw_results, weight in sources:
            seen_in_source: set[int] = set()
            normalized_rank = 0
            for raw_hit in raw_results:
                if not isinstance(raw_hit, Mapping):
                    continue
                chunk_id = raw_hit.get("chunk_id")
                if (
                    not isinstance(chunk_id, int)
                    or isinstance(chunk_id, bool)
                    or chunk_id < 0
                    or chunk_id in seen_in_source
                ):
                    continue
                seen_in_source.add(chunk_id)
                normalized_rank += 1
                if weight <= 0:
                    continue
                scores[chunk_id] = scores.get(chunk_id, 0.0) + weight / (k + normalized_rank)
                if chunk_id not in documents:
                    documents[chunk_id] = cast(MilvusSearchHit, raw_hit)
                    first_seen_order[chunk_id] = len(first_seen_order)
                paths = source_paths.setdefault(chunk_id, [])
                if source_name not in paths:
                    paths.append(source_name)

        sorted_ids = sorted(
            scores,
            key=lambda chunk_id: (-scores[chunk_id], first_seen_order[chunk_id]),
        )
        results: list[RrfSearchHit] = []
        for chunk_id in sorted_ids[:max_results]:
            document = documents[chunk_id]
            results.append(
                {
                    "chunk_id": chunk_id,
                    "rrf_score": scores[chunk_id],
                    "source_paths": source_paths[chunk_id],
                    "content": document.get("content", ""),
                    "title": document.get("title", ""),
                    "parent_title": document.get("parent_title", ""),
                    "file_title": document.get("file_title", ""),
                    "item_name": document.get("item_name", ""),
                    "part": document.get("part"),
                }
            )
        return results
