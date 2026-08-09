from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any

import pytest

from app.clients.mongo_history import MongoHistoryError, MongoHistoryStore
from app.core.config import Settings


class FakeCursor:
    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self.documents = list(documents)

    def sort(self, field_name: str, direction: int) -> FakeCursor:
        self.documents.sort(
            key=lambda document: document[field_name],
            reverse=direction < 0,
        )
        return self

    def limit(self, count: int) -> FakeCursor:
        self.documents = self.documents[:count]
        return self

    def __iter__(self):
        return iter(self.documents)


class FakeHistoryCollection:
    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []
        self.indexes: list[dict[str, Any]] = []

    def create_index(self, fields: list[tuple[str, int]], **kwargs: Any) -> str:
        self.indexes.append({"fields": fields, **kwargs})
        return str(kwargs["name"])

    def insert_one(self, document: dict[str, Any]) -> SimpleNamespace:
        self.documents.append(dict(document))
        return SimpleNamespace(inserted_id=document["message_id"])

    def find(
        self,
        query: dict[str, object],
        _projection: dict[str, int],
    ) -> FakeCursor:
        return FakeCursor(
            [
                document
                for document in self.documents
                if document["session_id"] == query["session_id"]
            ]
        )

    def delete_many(self, query: dict[str, object]) -> SimpleNamespace:
        before = len(self.documents)
        self.documents = [
            document for document in self.documents if document["session_id"] != query["session_id"]
        ]
        return SimpleNamespace(deleted_count=before - len(self.documents))


def create_store(collection: FakeHistoryCollection) -> MongoHistoryStore:
    return MongoHistoryStore(
        Settings(_env_file=None),
        collection=collection,
    )


def test_appends_metadata_and_creates_required_indexes_once() -> None:
    collection = FakeHistoryCollection()
    store = create_store(collection)

    message = store.append(
        "session-1",
        role="user",
        content=" RS-12 怎么测量电压？ ",
        rewritten_query="RS-12 数字万用表如何测量电压？",
        item_names=["RS-12 数字万用表"],
    )
    store.append("session-1", role="assistant", content="请确认商品。")

    assert message["content"] == "RS-12 怎么测量电压？"
    assert message["item_names"] == ["RS-12 数字万用表"]
    assert message["created_at"].tzinfo is not None
    assert [index["name"] for index in collection.indexes] == [
        "message_id_unique",
        "session_recent_messages",
    ]


def test_get_recent_returns_limited_messages_in_chronological_order() -> None:
    collection = FakeHistoryCollection()
    now = datetime.now(timezone.utc)
    for index in range(3):
        collection.documents.append(
            {
                "message_id": f"message-{index}",
                "session_id": "session-1",
                "role": "user",
                "content": f"消息 {index}",
                "rewritten_query": "",
                "item_names": [],
                "created_at": now + timedelta(seconds=index),
            }
        )

    messages = create_store(collection).get_recent("session-1", limit=2)

    assert [message["content"] for message in messages] == ["消息 1", "消息 2"]


def test_delete_session_only_removes_selected_session() -> None:
    collection = FakeHistoryCollection()
    store = create_store(collection)
    store.append("session-1", role="user", content="问题一")
    store.append("session-2", role="user", content="问题二")

    deleted = store.delete_session("session-1")

    assert deleted == 1
    assert [document["session_id"] for document in collection.documents] == ["session-2"]


@pytest.mark.parametrize(
    ("session_id", "content", "message"),
    [
        ("", "问题", "会话 ID"),
        ("session-1", "  ", "内容"),
    ],
)
def test_rejects_invalid_history_message(
    session_id: str,
    content: str,
    message: str,
) -> None:
    with pytest.raises(MongoHistoryError, match=message):
        create_store(FakeHistoryCollection()).append(
            session_id,
            role="user",
            content=content,
        )


def test_rejects_malformed_stored_message() -> None:
    collection = FakeHistoryCollection()
    collection.documents.append(
        {
            "message_id": "message-1",
            "session_id": "session-1",
            "role": "system",
            "content": "invalid",
            "rewritten_query": "",
            "item_names": [],
            "created_at": datetime.now(timezone.utc),
        }
    )

    with pytest.raises(MongoHistoryError, match="字段无效"):
        create_store(collection).get_recent("session-1", limit=10)
