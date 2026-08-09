"""MongoDB 查询会话历史存取。"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Literal, TypedDict
from uuid import uuid4

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import PyMongoError

from app.core.config import Settings, get_settings


class MongoHistoryError(Exception):
    """MongoDB 会话历史连接、写入或返回格式异常。"""


class StoredChatMessage(TypedDict):
    """服务内部使用的标准会话消息。"""

    message_id: str
    session_id: str
    role: Literal["user", "assistant"]
    content: str
    rewritten_query: str
    item_names: list[str]
    created_at: datetime


class MongoHistoryStore:
    """按会话保存消息，并按时间顺序返回最近上下文。"""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        collection: Any | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.collection = collection
        self._indexes_ready = False
        self._index_lock = Lock()

    def get_recent(self, session_id: str, *, limit: int) -> list[StoredChatMessage]:
        """读取最近消息，并从旧到新返回给提示词。"""

        self._validate_session_and_limit(session_id, limit)
        try:
            with self._open_collection() as collection:
                self._ensure_indexes(collection)
                cursor = (
                    collection.find(
                        {"session_id": session_id},
                        {
                            "_id": 0,
                            "message_id": 1,
                            "session_id": 1,
                            "role": 1,
                            "content": 1,
                            "rewritten_query": 1,
                            "item_names": 1,
                            "created_at": 1,
                        },
                    )
                    .sort("created_at", DESCENDING)
                    .limit(limit)
                )
                messages = [self._parse_message(document) for document in cursor]
        except MongoHistoryError:
            raise
        except (PyMongoError, TypeError, ValueError) as exc:
            raise MongoHistoryError("MongoDB 会话历史读取失败") from exc
        messages.reverse()
        return messages

    def append(
        self,
        session_id: str,
        *,
        role: Literal["user", "assistant"],
        content: str,
        rewritten_query: str = "",
        item_names: list[str] | None = None,
    ) -> StoredChatMessage:
        """写入一条用户或助手消息。"""

        self._validate_session_and_limit(session_id, 1)
        if role not in {"user", "assistant"}:
            raise MongoHistoryError("会话消息角色无效")
        normalized_content = content.strip() if isinstance(content, str) else ""
        if not normalized_content or len(normalized_content) > 4000:
            raise MongoHistoryError("会话消息内容无效")
        normalized_rewritten = rewritten_query.strip() if isinstance(rewritten_query, str) else ""
        normalized_names = self._normalize_item_names(item_names or [])
        message: StoredChatMessage = {
            "message_id": uuid4().hex,
            "session_id": session_id,
            "role": role,
            "content": normalized_content,
            "rewritten_query": normalized_rewritten,
            "item_names": normalized_names,
            "created_at": datetime.now(timezone.utc),
        }
        try:
            with self._open_collection() as collection:
                self._ensure_indexes(collection)
                collection.insert_one(dict(message))
        except MongoHistoryError:
            raise
        except (PyMongoError, TypeError, ValueError) as exc:
            raise MongoHistoryError("MongoDB 会话历史写入失败") from exc
        return message

    def delete_session(self, session_id: str) -> int:
        """删除一个明确会话，用于测试或后续清空历史接口。"""

        self._validate_session_and_limit(session_id, 1)
        try:
            with self._open_collection() as collection:
                result = collection.delete_many({"session_id": session_id})
                return int(result.deleted_count)
        except (PyMongoError, TypeError, ValueError) as exc:
            raise MongoHistoryError("MongoDB 会话历史删除失败") from exc

    @contextmanager
    def _open_collection(self) -> Iterator[Any]:
        if self.collection is not None:
            yield self.collection
            return

        timeout_ms = int(self.settings.mongo_request_timeout_seconds * 1000)
        client: MongoClient = MongoClient(
            self.settings.mongo_url,
            serverSelectionTimeoutMS=timeout_ms,
            connectTimeoutMS=timeout_ms,
            socketTimeoutMS=timeout_ms,
            tz_aware=True,
        )
        try:
            yield client[self.settings.mongo_db_name][self.settings.mongo_chat_collection]
        finally:
            client.close()

    def _ensure_indexes(self, collection: Any) -> None:
        if self._indexes_ready:
            return
        with self._index_lock:
            if self._indexes_ready:
                return
            collection.create_index(
                [("message_id", ASCENDING)],
                unique=True,
                name="message_id_unique",
            )
            collection.create_index(
                [("session_id", ASCENDING), ("created_at", DESCENDING)],
                name="session_recent_messages",
            )
            self._indexes_ready = True

    @staticmethod
    def _parse_message(document: object) -> StoredChatMessage:
        if not isinstance(document, dict):
            raise MongoHistoryError("MongoDB 会话消息格式无效")
        message_id = document.get("message_id")
        session_id = document.get("session_id")
        role = document.get("role")
        content = document.get("content")
        rewritten_query = document.get("rewritten_query", "")
        item_names = document.get("item_names", [])
        created_at = document.get("created_at")
        if (
            not isinstance(message_id, str)
            or not isinstance(session_id, str)
            or role not in {"user", "assistant"}
            or not isinstance(content, str)
            or not isinstance(rewritten_query, str)
            or not isinstance(item_names, list)
            or not isinstance(created_at, datetime)
        ):
            raise MongoHistoryError("MongoDB 会话消息字段无效")
        return {
            "message_id": message_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "rewritten_query": rewritten_query,
            "item_names": MongoHistoryStore._normalize_item_names(item_names),
            "created_at": created_at,
        }

    @staticmethod
    def _normalize_item_names(item_names: list[Any]) -> list[str]:
        normalized: list[str] = []
        for item_name in item_names:
            if not isinstance(item_name, str) or not item_name.strip():
                raise MongoHistoryError("会话消息商品名称无效")
            name = item_name.strip()
            if name.casefold() not in {value.casefold() for value in normalized}:
                normalized.append(name)
        return normalized

    @staticmethod
    def _validate_session_and_limit(session_id: str, limit: int) -> None:
        if not isinstance(session_id, str) or not session_id.strip() or len(session_id) > 64:
            raise MongoHistoryError("会话 ID 无效")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 50:
            raise MongoHistoryError("会话历史数量必须在 1 到 50 之间")
