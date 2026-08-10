"""把 LLM 提取名称与知识库标准商品名称进行候选对齐。"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import TypedDict

from app.clients.dashscope_embedding import (
    DashScopeEmbeddingClient,
    DashScopeEmbeddingError,
)
from app.clients.milvus_item_names import (
    ItemNameCandidate,
    MilvusItemNameSearcher,
    MilvusItemNameSearchError,
)
from app.core.config import Settings, get_settings
from app.workflows.querying.exceptions import ItemNameConfirmError, QuerySearchError


class ExtractedItemMatches(TypedDict):
    """一个提取名称对应的一组知识库候选。"""

    extracted_name: str
    matches: list[ItemNameCandidate]


ItemNameMatcher = Callable[[list[str]], list[ExtractedItemMatches]]


class ItemNameAligner:
    """按精确命中、置信区间和头部分差决定确认或澄清。"""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        matcher: ItemNameMatcher | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.matcher = matcher

    def align(self, item_names: list[str]) -> tuple[list[str], list[str]]:
        """返回已经确认的标准名称和需要用户选择的候选名称。"""

        if not item_names:
            return [], []
        try:
            search_results = (self.matcher or self._match_with_services)(item_names)
        except (ItemNameConfirmError, QuerySearchError):
            raise
        except DashScopeEmbeddingError as exc:
            raise ItemNameConfirmError("商品名称向量生成失败", cause=exc) from exc
        except MilvusItemNameSearchError as exc:
            raise QuerySearchError(str(exc), cause=exc) from exc
        except Exception as exc:
            raise ItemNameConfirmError("商品名称候选对齐失败", cause=exc) from exc
        return self._score_candidates(search_results)

    def _match_with_services(self, item_names: list[str]) -> list[ExtractedItemMatches]:
        embedding_client = DashScopeEmbeddingClient(
            base_url=self.settings.dashscope_api_base,
            api_key=self.settings.dashscope_api_key,
            model=self.settings.embedding_model,
            dimension=self.settings.embedding_dimension,
            max_batch_size=self.settings.embedding_batch_size,
            timeout_seconds=self.settings.embedding_request_timeout_seconds,
        )
        embeddings = []
        for start in range(0, len(item_names), self.settings.embedding_batch_size):
            embeddings.extend(
                embedding_client.embed_queries(
                    item_names[start : start + self.settings.embedding_batch_size]
                )
            )

        searcher = MilvusItemNameSearcher(self.settings)
        return [
            {
                "extracted_name": item_name,
                "matches": searcher.search(
                    embedding.dense_vector,
                    embedding.sparse_vector,
                    limit=self.settings.query_item_name_candidate_limit,
                ),
            }
            for item_name, embedding in zip(item_names, embeddings, strict=True)
        ]

    def _score_candidates(
        self,
        search_results: list[ExtractedItemMatches],
    ) -> tuple[list[str], list[str]]:
        confirmed: list[str] = []
        options: list[str] = []

        for search_result in search_results:
            extracted_name = search_result.get("extracted_name")
            matches = search_result.get("matches")
            if not isinstance(extracted_name, str) or not isinstance(matches, list):
                raise ItemNameConfirmError("商品名称候选结果格式无效")
            ordered = sorted(matches, key=lambda candidate: candidate["score"], reverse=True)

            exact = next(
                (
                    candidate
                    for candidate in ordered
                    if candidate["item_name"].casefold() == extracted_name.casefold()
                ),
                None,
            )
            if exact is not None:
                self._append_unique(confirmed, exact["item_name"])
                continue

            if len(ordered) == 1 and self._shares_model_identifier(
                extracted_name,
                ordered[0]["item_name"],
            ):
                self._append_unique(confirmed, ordered[0]["item_name"])
                continue

            high = [
                candidate
                for candidate in ordered
                if candidate["score"] >= self.settings.query_item_name_high_confidence
            ]
            if len(high) == 1:
                self._append_unique(confirmed, high[0]["item_name"])
                continue
            if len(high) > 1:
                if high[0]["score"] - high[1]["score"] >= self.settings.query_item_name_score_gap:
                    self._append_unique(confirmed, high[0]["item_name"])
                else:
                    for candidate in high:
                        self._append_unique(options, candidate["item_name"])
                continue

            middle = [
                candidate
                for candidate in ordered
                if candidate["score"] >= self.settings.query_item_name_mid_confidence
            ]
            for candidate in middle:
                self._append_unique(options, candidate["item_name"])

        confirmed_keys = {name.casefold() for name in confirmed}
        filtered_options = [name for name in options if name.casefold() not in confirmed_keys][
            : self.settings.query_item_name_candidate_limit
        ]
        return confirmed, filtered_options

    @staticmethod
    def _append_unique(values: list[str], value: str) -> None:
        if value.casefold() not in {existing.casefold() for existing in values}:
            values.append(value)

    @staticmethod
    def _shares_model_identifier(extracted_name: str, candidate_name: str) -> bool:
        """识别 RS-12 这类低分但唯一的精确型号别名。"""

        def identifiers(value: str) -> set[str]:
            tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9_.-]*", value)
            normalized: set[str] = set()
            for token in tokens:
                identifier = re.sub(r"[^a-z0-9]", "", token.casefold())
                if (
                    len(identifier) >= 3
                    and any(character.isalpha() for character in identifier)
                    and any(character.isdigit() for character in identifier)
                ):
                    normalized.add(identifier)
            return normalized

        return bool(identifiers(extracted_name) & identifiers(candidate_name))
