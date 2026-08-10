"""合并 RRF 本地候选和网页摘要，并使用百炼 API 精排。"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from app.clients.dashscope_rerank import DashScopeRerankClient, DashScopeRerankError
from app.core.config import Settings, get_settings
from app.workflows.querying.base import BaseQueryNode
from app.workflows.querying.exceptions import QueryValidationError
from app.workflows.querying.state import QueryGraphState, RerankDocument

Reranker = Callable[[str, list[str]], list[float]]


class RerankNode(BaseQueryNode):
    """统一本地与网页文档、云端打分，并按最大相关性断崖动态截取。"""

    name = "rerank_node"

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        reranker: Reranker | None = None,
    ) -> None:
        super().__init__()
        self.settings = settings or get_settings()
        self.reranker = reranker

    def process(self, state: QueryGraphState) -> Mapping[str, object]:
        query = state.get("rewritten_query") or state.get("original_query")
        if not isinstance(query, str) or not query.strip():
            raise QueryValidationError("重排缺少有效问题", node_name=self.name)
        documents = self._merge_documents(state)
        if not documents:
            return {"rerank_status": "skipped", "reranked_documents": []}
        if not self.settings.rerank_enabled:
            return {
                "rerank_status": "disabled",
                "reranked_documents": documents[: self.settings.rerank_max_top_k],
            }

        contents = [document["content"] for document in documents]
        try:
            scores = (
                self.reranker(query.strip(), contents)
                if self.reranker is not None
                else self._rerank_with_dashscope(query.strip(), contents)
            )
            if len(scores) != len(documents):
                raise DashScopeRerankError("百炼重排分数数量与文档数量不一致")
            scored = [
                {**document, "rerank_score": float(score)}
                for document, score in zip(documents, scores, strict=True)
            ]
            scored.sort(
                key=lambda document: (
                    -float(document["rerank_score"] or 0),
                    0 if document["source"] == "local" else 1,
                )
            )
            cutoff = self._dynamic_cliff_cutoff(scored)
        except (DashScopeRerankError, TypeError, ValueError) as exc:
            self.logger.warning("Rerank unavailable: %s", exc)
            return {
                "rerank_status": "failed",
                "reranked_documents": documents[: self.settings.rerank_max_top_k],
            }
        except Exception as exc:
            self.logger.warning("Rerank failed unexpectedly", exc_info=exc)
            return {
                "rerank_status": "failed",
                "reranked_documents": documents[: self.settings.rerank_max_top_k],
            }
        return {"rerank_status": "succeeded", "reranked_documents": cutoff}

    def _merge_documents(self, state: QueryGraphState) -> list[RerankDocument]:
        local_results = state.get("rrf_results", [])
        web_results = state.get("web_search_results", [])
        if not isinstance(local_results, list) or not isinstance(web_results, list):
            raise QueryValidationError("重排输入必须是结果列表", node_name=self.name)

        documents: list[RerankDocument] = []
        for result in local_results:
            if not isinstance(result, Mapping):
                continue
            content = result.get("content", "")
            chunk_id = result.get("chunk_id")
            if not isinstance(content, str) or not content.strip() or not isinstance(chunk_id, int):
                continue
            source_paths = result.get("source_paths", [])
            documents.append(
                {
                    "source": "local",
                    "content": content.strip()[: self.settings.rerank_document_max_length],
                    "title": self._text(result.get("title")),
                    "chunk_id": chunk_id,
                    "url": "",
                    "item_name": self._text(result.get("item_name")),
                    "source_paths": [path for path in source_paths if path in {"vector", "hyde"}]
                    if isinstance(source_paths, list)
                    else [],
                    "rerank_score": None,
                }
            )
        seen_urls: set[str] = set()
        for result in web_results:
            if not isinstance(result, Mapping):
                continue
            snippet = result.get("snippet", "")
            url = result.get("url", "")
            if (
                not isinstance(snippet, str)
                or not snippet.strip()
                or not isinstance(url, str)
                or not url.startswith(("https://", "http://"))
                or url in seen_urls
            ):
                continue
            seen_urls.add(url)
            documents.append(
                {
                    "source": "web",
                    "content": snippet.strip()[: self.settings.rerank_document_max_length],
                    "title": self._text(result.get("title")),
                    "chunk_id": None,
                    "url": url,
                    "item_name": "",
                    "source_paths": [],
                    "rerank_score": None,
                }
            )
        return documents

    def _rerank_with_dashscope(self, query: str, documents: list[str]) -> list[float]:
        return DashScopeRerankClient(
            base_url=self.settings.rerank_api_base,
            api_key=self.settings.dashscope_api_key,
            model=self.settings.rerank_model,
            timeout_seconds=self.settings.rerank_request_timeout_seconds,
        ).rerank(query, documents)

    def _dynamic_cliff_cutoff(self, documents: list[RerankDocument]) -> list[RerankDocument]:
        upper_bound = min(self.settings.rerank_max_top_k, len(documents))
        lower_bound = min(self.settings.rerank_min_top_k, upper_bound)
        if upper_bound <= lower_bound:
            return documents[:upper_bound]

        cutoff = upper_bound
        max_gap = 0.0
        for index in range(upper_bound - 1):
            current = documents[index]["rerank_score"]
            following = documents[index + 1]["rerank_score"]
            if current is None or following is None:
                continue
            gap = current - following
            if gap > self.settings.rerank_gap_abs and gap > max_gap:
                max_gap = gap
                cutoff = index + 1
        return documents[: max(cutoff, lower_bound)]

    @staticmethod
    def _text(value: object) -> str:
        return value.strip() if isinstance(value, str) else ""
