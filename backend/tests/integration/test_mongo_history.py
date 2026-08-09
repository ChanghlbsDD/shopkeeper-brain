"""真实 MongoDB 会话历史读写与清理测试。"""

import os
from uuid import uuid4

import pytest

from app.clients.mongo_history import MongoHistoryStore

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INTEGRATION_TESTS") != "1",
        reason="set RUN_INTEGRATION_TESTS=1 to use the local MongoDB container",
    ),
]


def test_mongo_history_round_trip() -> None:
    store = MongoHistoryStore()
    session_id = f"integration-{uuid4().hex}"
    try:
        store.append(
            session_id,
            role="user",
            content="RS-12 怎么测量电压？",
            item_names=["RS-12 数字万用表"],
        )
        store.append(session_id, role="assistant", content="请确认具体型号。")

        messages = store.get_recent(session_id, limit=10)

        assert [message["role"] for message in messages] == ["user", "assistant"]
        assert messages[0]["item_names"] == ["RS-12 数字万用表"]
    finally:
        store.delete_session(session_id)
