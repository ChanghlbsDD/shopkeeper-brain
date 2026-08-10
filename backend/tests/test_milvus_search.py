from typing import Any

import pytest

from app.clients.milvus_search import (
    SEARCH_OUTPUT_FIELDS,
    MilvusHybridSearcher,
    MilvusSearchError,
)
from app.core.config import Settings

DENSE_VECTOR = [0.1] * 64


class FakeMilvusSearchClient:
    def __init__(self, *, exists: bool = True) -> None:
        self.exists = exists
        self.loaded: list[str] = []
        self.search_kwargs: dict[str, Any] | None = None
        self.results: Any = [
            [
                {
                    "chunk_id": 42,
                    "distance": 0.87,
                    "entity": {
                        "content": "将量程旋钮转到直流电压档。",
                        "title": "测量直流电压",
                        "parent_title": "基本测量",
                        "file_title": "RS-12 用户手册",
                        "item_name": "RS-12 数字万用表",
                        "part": 1,
                    },
                }
            ]
        ]

    def has_collection(self, **_kwargs: object) -> bool:
        return self.exists

    def load_collection(self, *, collection_name: str, **_kwargs: object) -> None:
        self.loaded.append(collection_name)

    def hybrid_search(self, **kwargs: Any) -> Any:
        self.search_kwargs = kwargs
        return self.results


def create_searcher(client: FakeMilvusSearchClient) -> MilvusHybridSearcher:
    return MilvusHybridSearcher(
        Settings(
            _env_file=None,
            embedding_dimension=64,
            query_dense_weight=0.7,
            query_sparse_weight=0.3,
        ),
        client=client,  # type: ignore[arg-type]
    )


def test_runs_parameterized_dense_and_sparse_hybrid_search() -> None:
    client = FakeMilvusSearchClient()

    hits = create_searcher(client).search(
        DENSE_VECTOR,
        {7: 0.8},
        item_names=["RS-12 数字万用表"],
        limit=4,
    )

    assert client.loaded == ["knowledge_chunks"]
    assert client.search_kwargs is not None
    requests = client.search_kwargs["reqs"]
    assert [request._anns_field for request in requests] == [  # noqa: SLF001
        "dense_vector",
        "sparse_vector",
    ]
    assert all(request._expr == "item_name in {item_names}" for request in requests)  # noqa: SLF001
    assert all(  # noqa: SLF001
        request._expr_params == {"item_names": ["RS-12 数字万用表"]} for request in requests
    )
    assert client.search_kwargs["output_fields"] == SEARCH_OUTPUT_FIELDS
    assert client.search_kwargs["limit"] == 4
    assert hits == [
        {
            "chunk_id": 42,
            "score": 0.87,
            "content": "将量程旋钮转到直流电压档。",
            "title": "测量直流电压",
            "parent_title": "基本测量",
            "file_title": "RS-12 用户手册",
            "item_name": "RS-12 数字万用表",
            "part": 1,
        }
    ]


def test_search_without_item_name_does_not_add_scalar_filter() -> None:
    client = FakeMilvusSearchClient()

    create_searcher(client).search(DENSE_VECTOR, {7: 0.8})

    assert client.search_kwargs is not None
    assert all(request._expr is None for request in client.search_kwargs["reqs"])  # noqa: SLF001


def test_accepts_legacy_generic_id_key_from_milvus_mapping() -> None:
    client = FakeMilvusSearchClient()
    client.results[0][0]["id"] = client.results[0][0].pop("chunk_id")

    hits = create_searcher(client).search(DENSE_VECTOR, {7: 0.8})

    assert hits[0]["chunk_id"] == 42


def test_reports_empty_knowledge_collection() -> None:
    client = FakeMilvusSearchClient(exists=False)

    with pytest.raises(MilvusSearchError, match="先导入文档"):
        create_searcher(client).search(DENSE_VECTOR, {7: 0.8})


@pytest.mark.parametrize(
    ("dense", "sparse", "limit", "message"),
    [
        ([], {1: 0.2}, 5, "稠密向量"),
        (DENSE_VECTOR, {}, 5, "稀疏向量"),
        (DENSE_VECTOR, {1: 0.2}, 0, "1 到 20"),
    ],
)
def test_rejects_invalid_search_inputs(
    dense: list[float],
    sparse: dict[int, float],
    limit: int,
    message: str,
) -> None:
    with pytest.raises(MilvusSearchError, match=message):
        create_searcher(FakeMilvusSearchClient()).search(dense, sparse, limit=limit)


def test_rejects_malformed_milvus_result() -> None:
    client = FakeMilvusSearchClient()
    client.results = [[{"id": 42, "distance": 0.8, "entity": {"content": ""}}]]

    with pytest.raises(MilvusSearchError, match="正文"):
        create_searcher(client).search(DENSE_VECTOR, {7: 0.8})
