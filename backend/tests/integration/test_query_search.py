"""真实通义千问、百炼向量和 Milvus 的可选查询链路测试。"""

import os

import pytest

from app.core.config import get_settings
from app.workflows.querying import run_query_workflow

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INTEGRATION_TESTS") != "1",
        reason="set RUN_INTEGRATION_TESTS=1 to use external AI APIs and local Milvus",
    ),
]


def test_query_search_returns_imported_knowledge() -> None:
    settings = get_settings()
    if not settings.dashscope_api_key:
        pytest.skip("DASHSCOPE_API_KEY is not configured")

    result = run_query_workflow(
        "RS-12 数字万用表如何测量直流电压？",
        search_limit=3,
    )

    assert result["completed_nodes"] == [
        "item_name_confirm_node",
        "query_embedding_node",
        "vector_search_node",
    ]
    assert result["rewritten_query"]
    assert result["item_names"]
    assert result["search_results"]
    assert all(hit["content"] for hit in result["search_results"])
