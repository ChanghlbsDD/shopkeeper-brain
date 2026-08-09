from typing import Any

import pytest

from app.clients.milvus_item_names import (
    MilvusItemNameSearcher,
    MilvusItemNameSearchError,
)
from app.core.config import Settings

DENSE_VECTOR = [0.1] * 64


class FakeItemNameClient:
    def __init__(self, *, exists: bool = True) -> None:
        self.exists = exists
        self.loaded: list[str] = []
        self.search_kwargs: dict[str, Any] | None = None
        self.results: Any = [
            [
                {
                    "id": 1,
                    "distance": 0.82,
                    "entity": {"item_name": "RS-12 数字万用表"},
                },
                {
                    "id": 2,
                    "distance": 0.78,
                    "entity": {"item_name": "RS-12 数字万用表"},
                },
                {
                    "id": 3,
                    "distance": 0.68,
                    "entity": {"item_name": "RS-13 数字万用表"},
                },
            ]
        ]

    def has_collection(self, **_kwargs: object) -> bool:
        return self.exists

    def load_collection(self, *, collection_name: str, **_kwargs: object) -> None:
        self.loaded.append(collection_name)

    def hybrid_search(self, **kwargs: Any) -> Any:
        self.search_kwargs = kwargs
        return self.results


def create_searcher(client: FakeItemNameClient) -> MilvusItemNameSearcher:
    return MilvusItemNameSearcher(
        Settings(_env_file=None, embedding_dimension=64),
        client=client,  # type: ignore[arg-type]
    )


def test_groups_chunk_results_by_item_name_and_deduplicates_candidates() -> None:
    client = FakeItemNameClient()

    candidates = create_searcher(client).search(DENSE_VECTOR, {7: 0.8}, limit=5)

    assert client.loaded == ["knowledge_chunks"]
    assert client.search_kwargs is not None
    assert client.search_kwargs["group_by_field"] == "item_name"
    assert client.search_kwargs["group_size"] == 1
    assert client.search_kwargs["strict_group_size"] is False
    assert client.search_kwargs["output_fields"] == ["item_name"]
    assert [request._limit for request in client.search_kwargs["reqs"]] == [50, 50]  # noqa: SLF001
    assert candidates == [
        {"item_name": "RS-12 数字万用表", "score": 0.82},
        {"item_name": "RS-13 数字万用表", "score": 0.68},
    ]


def test_reports_missing_chunk_collection() -> None:
    with pytest.raises(MilvusItemNameSearchError, match="先导入文档"):
        create_searcher(FakeItemNameClient(exists=False)).search(
            DENSE_VECTOR,
            {7: 0.8},
        )


@pytest.mark.parametrize(
    ("dense", "sparse", "limit", "message"),
    [
        ([0.1], {7: 0.8}, 5, "维度"),
        (DENSE_VECTOR, {}, 5, "稀疏向量"),
        (DENSE_VECTOR, {7: 0.8}, 0, "1 到 20"),
    ],
)
def test_rejects_invalid_candidate_search_inputs(
    dense: list[float],
    sparse: dict[int, float],
    limit: int,
    message: str,
) -> None:
    with pytest.raises(MilvusItemNameSearchError, match=message):
        create_searcher(FakeItemNameClient()).search(dense, sparse, limit=limit)


def test_rejects_candidate_without_item_name() -> None:
    client = FakeItemNameClient()
    client.results = [[{"id": 1, "distance": 0.8, "entity": {}}]]

    with pytest.raises(MilvusItemNameSearchError, match="缺少名称"):
        create_searcher(client).search(DENSE_VECTOR, {7: 0.8})
