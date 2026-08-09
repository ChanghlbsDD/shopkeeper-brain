import os
from uuid import uuid4

import pytest
from pymilvus import MilvusClient

from app.core.config import Settings
from app.workflows.importing.nodes import ImportMilvusNode
from app.workflows.importing.state import create_import_state

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INTEGRATION_TESTS") != "1",
        reason="set RUN_INTEGRATION_TESTS=1 to use the local Docker infrastructure",
    ),
]


def test_real_milvus_collection_insert_and_id_fill() -> None:
    settings = Settings()
    collection_name = f"test_import_{uuid4().hex}"
    state = create_import_state("manual.md")
    state.update(
        {
            "file_title": "RS-12 使用说明",
            "item_name": "RS-12 数字万用表",
            "chunks": [
                {
                    "title": "# 产品介绍",
                    "parent_title": "",
                    "file_title": "RS-12 使用说明",
                    "content": "RS-12 可以测量电压和电阻。",
                    "item_name": "RS-12 数字万用表",
                    "dense_vector": [0.1, 0.2, 0.3, 0.4],
                    "sparse_vector": {7: 0.8, 11: 0.5},
                },
                {
                    "title": "## 安全说明",
                    "parent_title": "# 产品介绍",
                    "file_title": "RS-12 使用说明",
                    "content": "测量前检查表笔和量程。",
                    "item_name": "RS-12 数字万用表",
                    "dense_vector": [0.4, 0.3, 0.2, 0.1],
                    "sparse_vector": {13: 0.9},
                    "part": 1,
                },
            ],
        }
    )

    client = MilvusClient(uri=settings.milvus_url)
    try:
        result = ImportMilvusNode(
            collection_name=collection_name,
            insert_batch_size=1,
            backup_enabled=False,
        )(state)

        assert len(result["milvus_ids"]) == 2
        assert result["chunks"][0]["chunk_id"] == result["milvus_ids"][0]
        assert set(client.list_indexes(collection_name=collection_name)) == {
            "dense_vector_index",
            "sparse_vector_index",
        }

        stored = client.get(
            collection_name=collection_name,
            ids=result["milvus_ids"],
            output_fields=["content", "item_name", "part"],
        )
        assert len(stored) == 2
        assert {entity["content"] for entity in stored} == {
            "RS-12 可以测量电压和电阻。",
            "测量前检查表笔和量程。",
        }
        assert all(entity["item_name"] == "RS-12 数字万用表" for entity in stored)
    finally:
        if client.has_collection(collection_name=collection_name):
            client.drop_collection(collection_name=collection_name)
        client.close()
