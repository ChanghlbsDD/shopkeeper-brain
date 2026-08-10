"""使用 HyDE 假设文档扩展问题并召回知识片段。"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from app.clients.dashscope_embedding import (
    DashScopeEmbeddingClient,
    DashScopeEmbeddingError,
    TextEmbedding,
)
from app.clients.milvus_search import MilvusHybridSearcher, MilvusSearchError, MilvusSearchHit
from app.clients.qwen_chat import QwenChatClient, QwenChatError
from app.core.config import Settings, get_settings
from app.workflows.querying.base import BaseQueryNode
from app.workflows.querying.exceptions import QueryValidationError
from app.workflows.querying.state import QueryGraphState

HydeDocumentGenerator = Callable[[str, list[str]], str]
HydeEmbedder = Callable[[str], TextEmbedding]
HydeSearcher = Callable[
    [list[float], dict[int, float], list[str], int],
    list[MilvusSearchHit],
]


class HydeSearchNode(BaseQueryNode):
    """生成像技术手册的假设答案，再用它执行第二路 Milvus 检索。"""

    name = "hyde_search_node"

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        document_generator: HydeDocumentGenerator | None = None,
        embedder: HydeEmbedder | None = None,
        searcher: HydeSearcher | None = None,
    ) -> None:
        super().__init__()
        self.settings = settings or get_settings()
        self.document_generator = document_generator
        self.embedder = embedder
        self.searcher = searcher

    def process(self, state: QueryGraphState) -> Mapping[str, object]:
        if not self.settings.query_hyde_enabled:
            return {"hyde_status": "disabled", "hyde_search_results": []}

        rewritten_query = state.get("rewritten_query")
        item_names = state.get("item_names")
        limit = state.get("search_limit", self.settings.query_search_limit)
        if not isinstance(rewritten_query, str) or not rewritten_query.strip():
            raise QueryValidationError("HyDE 检索缺少有效问题", node_name=self.name)
        if (
            not isinstance(item_names, list)
            or not item_names
            or not all(isinstance(name, str) and name.strip() for name in item_names)
        ):
            raise QueryValidationError("HyDE 检索缺少有效商品名", node_name=self.name)
        if not isinstance(limit, int) or isinstance(limit, bool):
            raise QueryValidationError("HyDE 检索结果数量无效", node_name=self.name)

        try:
            document = (self.document_generator or self._generate_with_qwen)(
                rewritten_query.strip(), item_names
            ).strip()
            if not document:
                raise QwenChatError("HyDE 没有生成有效假设文档")
            embedding_text = f"{rewritten_query.strip()}\n{document}"
            embedding = (self.embedder or self._embed_with_dashscope)(embedding_text)
            if self.searcher is not None:
                results = self.searcher(
                    embedding.dense_vector,
                    embedding.sparse_vector,
                    item_names,
                    limit,
                )
            else:
                results = MilvusHybridSearcher(self.settings).search(
                    embedding.dense_vector,
                    embedding.sparse_vector,
                    item_names=item_names,
                    limit=limit,
                )
        except (QwenChatError, DashScopeEmbeddingError, MilvusSearchError) as exc:
            self.logger.warning("HyDE retrieval unavailable: %s", exc)
            return {
                "hyde_status": "failed",
                "hyde_document": "",
                "hyde_search_results": [],
            }
        except Exception as exc:
            self.logger.warning("HyDE retrieval failed unexpectedly", exc_info=exc)
            return {
                "hyde_status": "failed",
                "hyde_document": "",
                "hyde_search_results": [],
            }
        return {
            "hyde_status": "succeeded",
            "hyde_document": document,
            "hyde_search_results": results,
        }

    def _generate_with_qwen(self, query: str, item_names: list[str]) -> str:
        client = QwenChatClient(
            base_url=self.settings.openai_api_base,
            api_key=self.settings.dashscope_api_key,
            model=self.settings.query_hyde_model,
            temperature=self.settings.llm_default_temperature,
            max_tokens=self.settings.query_hyde_max_output_tokens,
            timeout_seconds=self.settings.qwen_request_timeout_seconds,
        )
        return client.create_text_completion(
            system_prompt=(
                f"你是 {', '.join(item_names)} 的技术文档专家，擅长编写准确、清晰的操作手册。"
            ),
            user_prompt=(
                "请根据下面的问题写一段 200 至 300 字的假设性技术文档。"
                "直接给出可能出现在产品手册中的答案，不要解释 HyDE，不要添加无关内容。\n"
                f"问题：{query}"
            ),
        )

    def _embed_with_dashscope(self, text: str) -> TextEmbedding:
        client = DashScopeEmbeddingClient(
            base_url=self.settings.dashscope_api_base,
            api_key=self.settings.dashscope_api_key,
            model=self.settings.embedding_model,
            dimension=self.settings.embedding_dimension,
            max_batch_size=self.settings.embedding_batch_size,
            timeout_seconds=self.settings.embedding_request_timeout_seconds,
        )
        return client.embed_queries([text])[0]
