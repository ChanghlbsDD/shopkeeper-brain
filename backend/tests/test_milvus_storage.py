from typing import Any

import pytest
from pymilvus import DataType

from app.clients.milvus_storage import (
    DENSE_INDEX_NAME,
    DENSE_VECTOR_FIELD,
    SPARSE_INDEX_NAME,
    SPARSE_VECTOR_FIELD,
    MilvusChunkStore,
    MilvusStorageError,
)


class FakeSchema:
    def __init__(self, **kwargs: object) -> None:
        self.options = kwargs
        self.fields: list[dict[str, object]] = []

    def add_field(self, **kwargs: object) -> None:
        self.fields.append(kwargs)


class FakeIndexParams:
    def __init__(self) -> None:
        self.indexes: list[dict[str, object]] = []

    def add_index(self, **kwargs: object) -> None:
        self.indexes.append(kwargs)


class FakeMilvusClient:
    def __init__(self, *, collection_exists: bool = False) -> None:
        self.collection_exists = collection_exists
        self.schema: FakeSchema | None = None
        self.created_collection: dict[str, object] | None = None
        self.created_indexes: list[dict[str, object]] = []
        self.insert_batches: list[list[dict[str, Any]]] = []
        self.flush_calls: list[str] = []
        self.deleted_ids: list[int] = []
        self.next_id = 100
        self.fail_insert_call: int | None = None
        self.invalid_result_call: int | None = None
        self.existing_description = compatible_description()
        self.existing_indexes: dict[str, dict[str, object]] = {
            DENSE_INDEX_NAME: {
                "field_name": DENSE_VECTOR_FIELD,
                "metric_type": "COSINE",
            },
            SPARSE_INDEX_NAME: {
                "field_name": SPARSE_VECTOR_FIELD,
                "metric_type": "IP",
            },
        }

    def has_collection(self, **_kwargs: object) -> bool:
        return self.collection_exists

    def create_schema(self, **kwargs: object) -> FakeSchema:
        self.schema = FakeSchema(**kwargs)
        return self.schema

    def prepare_index_params(self) -> FakeIndexParams:
        return FakeIndexParams()

    def create_collection(self, **kwargs: object) -> None:
        self.created_collection = kwargs

    def describe_collection(self, **_kwargs: object) -> dict[str, object]:
        return self.existing_description

    def list_indexes(self, **_kwargs: object) -> list[str]:
        return list(self.existing_indexes)

    def describe_index(self, *, index_name: str, **_kwargs: object) -> dict[str, object]:
        return self.existing_indexes[index_name]

    def create_index(self, **kwargs: object) -> None:
        params = kwargs["index_params"]
        self.created_indexes.extend(params.indexes)  # type: ignore[union-attr]

    def insert(self, *, data: list[dict[str, Any]], **_kwargs: object) -> dict[str, object]:
        call_number = len(self.insert_batches) + 1
        if self.fail_insert_call == call_number:
            raise RuntimeError("insert failed")
        self.insert_batches.append(data)
        if self.invalid_result_call == call_number:
            return {"insert_count": 0, "ids": []}
        ids = list(range(self.next_id, self.next_id + len(data)))
        self.next_id += len(data)
        return {"insert_count": len(data), "ids": ids}

    def flush(self, *, collection_name: str, **_kwargs: object) -> None:
        self.flush_calls.append(collection_name)

    def delete(self, *, ids: list[int], **_kwargs: object) -> None:
        self.deleted_ids.extend(ids)


def compatible_description(dimension: int = 4) -> dict[str, object]:
    fields = [
        {"name": "chunk_id", "type": DataType.INT64, "params": {}},
        {"name": "dense_vector", "type": DataType.FLOAT_VECTOR, "params": {"dim": dimension}},
        {"name": "sparse_vector", "type": DataType.SPARSE_FLOAT_VECTOR, "params": {}},
        {"name": "part", "type": DataType.INT64, "params": {}},
    ]
    fields.extend(
        {"name": name, "type": DataType.VARCHAR, "params": {"max_length": 65_535}}
        for name in ("content", "title", "parent_title", "file_title", "item_name")
    )
    return {
        "auto_id": True,
        "enable_dynamic_field": False,
        "fields": fields,
    }


def create_store(client: FakeMilvusClient) -> MilvusChunkStore:
    return MilvusChunkStore(
        client,  # type: ignore[arg-type]
        collection_name="knowledge_chunks",
        timeout_seconds=10,
    )


def test_creates_explicit_schema_and_hybrid_indexes() -> None:
    client = FakeMilvusClient()

    create_store(client).ensure_collection(4)

    assert client.schema is not None
    assert client.schema.options == {"auto_id": True, "enable_dynamic_field": False}
    fields = {str(field["field_name"]): field for field in client.schema.fields}
    assert fields["chunk_id"]["is_primary"] is True
    assert fields["chunk_id"]["auto_id"] is True
    assert fields["dense_vector"]["dim"] == 4
    assert fields["sparse_vector"]["datatype"] == DataType.SPARSE_FLOAT_VECTOR
    assert fields["part"]["nullable"] is True

    assert client.created_collection is not None
    assert client.created_collection["collection_name"] == "knowledge_chunks"
    assert client.created_collection["consistency_level"] == "Session"
    indexes = client.created_collection["index_params"].indexes  # type: ignore[union-attr]
    assert indexes[0]["metric_type"] == "COSINE"
    assert indexes[1]["metric_type"] == "IP"
    assert indexes[1]["params"] == {"inverted_index_algo": "DAAT_MAXSCORE"}


def test_reuses_compatible_collection_and_creates_missing_index() -> None:
    client = FakeMilvusClient(collection_exists=True)
    client.existing_indexes.pop(SPARSE_INDEX_NAME)

    create_store(client).ensure_collection(4)

    assert client.created_collection is None
    assert len(client.created_indexes) == 1
    assert client.created_indexes[0]["index_name"] == SPARSE_INDEX_NAME


def test_rejects_incompatible_existing_dimension() -> None:
    client = FakeMilvusClient(collection_exists=True)
    client.existing_description = compatible_description(dimension=8)

    with pytest.raises(MilvusStorageError, match="维度为 8"):
        create_store(client).ensure_collection(4)


def test_rejects_incompatible_existing_index() -> None:
    client = FakeMilvusClient(collection_exists=True)
    client.existing_indexes[DENSE_INDEX_NAME]["metric_type"] = "L2"

    with pytest.raises(MilvusStorageError, match="索引"):
        create_store(client).ensure_collection(4)


def test_inserts_in_batches_returns_ids_and_flushes() -> None:
    client = FakeMilvusClient()
    entities = [{"content": str(index)} for index in range(5)]

    ids = create_store(client).insert_entities(entities, batch_size=2)

    assert [len(batch) for batch in client.insert_batches] == [2, 2, 1]
    assert ids == [100, 101, 102, 103, 104]
    assert client.flush_calls == ["knowledge_chunks"]


def test_rolls_back_previous_batches_when_later_insert_fails() -> None:
    client = FakeMilvusClient()
    client.fail_insert_call = 2
    entities = [{"content": str(index)} for index in range(3)]

    with pytest.raises(RuntimeError, match="insert failed"):
        create_store(client).insert_entities(entities, batch_size=2)

    assert client.deleted_ids == [100, 101]
    assert client.flush_calls == ["knowledge_chunks"]


def test_rejects_invalid_insert_response_and_rolls_back_previous_batch() -> None:
    client = FakeMilvusClient()
    client.invalid_result_call = 2
    entities = [{"content": str(index)} for index in range(3)]

    with pytest.raises(MilvusStorageError, match="写入数量"):
        create_store(client).insert_entities(entities, batch_size=2)

    assert client.deleted_ids == [100, 101]
