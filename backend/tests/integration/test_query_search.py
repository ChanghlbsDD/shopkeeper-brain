"""真实通义千问、百炼向量和 Milvus 的可选查询链路测试。"""

import os
from pathlib import Path
from shutil import copyfile

import pytest
from pymilvus import MilvusClient

from app.core.config import get_settings
from app.workflows.importing import run_import_workflow
from app.workflows.querying import run_query_workflow

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "rs12_e2e_manual.md"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INTEGRATION_TESTS") != "1",
        reason="set RUN_INTEGRATION_TESTS=1 to use external AI APIs and local Milvus",
    ),
]


def test_query_search_returns_imported_knowledge(tmp_path: Path) -> None:
    settings = get_settings()
    if not settings.dashscope_api_key:
        pytest.skip("DASHSCOPE_API_KEY is not configured")
    source_path = tmp_path / FIXTURE_PATH.name
    copyfile(FIXTURE_PATH, source_path)
    imported = run_import_workflow(str(source_path), file_dir=str(tmp_path))
    inserted_ids = imported["milvus_ids"]
    client = MilvusClient(uri=settings.milvus_url)

    try:
        result = run_query_workflow(
            "RS-12 数字万用表如何测量直流电压？",
            search_limit=3,
        )

        assert imported["item_name"] == "RS-12 数字万用表"
        assert imported["chunks"]
        assert inserted_ids
        assert set(result["completed_nodes"]) == {
            "item_name_confirm_node",
            "query_embedding_node",
            "vector_search_node",
            "hyde_search_node",
            "web_search_node",
            "rrf_node",
            "rerank_node",
            "answer_generation_node",
        }
        assert result["query_status"] == "confirmed"
        assert result["rewritten_query"]
        assert result["item_names"]
        assert result["search_results"]
        assert all(hit["content"] for hit in result["search_results"])
        assert result["hyde_status"] == "succeeded"
        assert result["rrf_results"]
        assert result["rerank_status"] == "succeeded"
        assert result["reranked_documents"]
        assert result["answer"]
        assert result["answer_references"]
    finally:
        if inserted_ids:
            client.delete(
                collection_name=settings.chunks_collection,
                ids=inserted_ids,
            )
            client.flush(collection_name=settings.chunks_collection)
        client.close()
