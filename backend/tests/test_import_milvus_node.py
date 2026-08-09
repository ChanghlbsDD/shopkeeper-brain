import json
from pathlib import Path
from typing import Any

import pytest

from app.clients.milvus_storage import MilvusStorageError
from app.workflows.importing.exceptions import ImportValidationError, MilvusImportError
from app.workflows.importing.nodes import ImportMilvusNode
from app.workflows.importing.state import ImportGraphState, create_import_state


def create_milvus_state(tmp_path: Path, *, chunk_count: int = 3) -> ImportGraphState:
    markdown_path = tmp_path / "manual.md"
    markdown_path.write_text("# RS-12 使用说明", encoding="utf-8")
    state = create_import_state(str(markdown_path))
    state.update(
        {
            "md_path": str(markdown_path),
            "file_dir": str(tmp_path),
            "chunks": [
                {
                    "title": f"## 章节 {index}",
                    "parent_title": "# RS-12",
                    "file_title": "RS-12 使用说明",
                    "content": f"第 {index} 个测量说明。",
                    "item_name": "RS-12 数字万用表",
                    "dense_vector": [0.1, 0.2, float(index), 0.4],
                    "sparse_vector": {index: 0.5},
                    **({"part": index} if index > 1 else {}),
                }
                for index in range(1, chunk_count + 1)
            ],
        }
    )
    return state


def test_imports_entities_and_fills_ids_without_mutating_input(tmp_path: Path) -> None:
    state = create_milvus_state(tmp_path)
    original_chunks = state["chunks"]
    captured: dict[str, Any] = {}

    def importer(
        entities: list[dict[str, Any]],
        dimension: int,
        collection_name: str,
        batch_size: int,
    ) -> list[int]:
        captured.update(
            {
                "entities": entities,
                "dimension": dimension,
                "collection_name": collection_name,
                "batch_size": batch_size,
            }
        )
        return [501, 502, 503]

    result = ImportMilvusNode(importer=importer, insert_batch_size=2)(state)

    assert captured["dimension"] == 4
    assert captured["collection_name"] == "knowledge_chunks"
    assert captured["batch_size"] == 2
    assert captured["entities"][0] == {
        "content": "第 1 个测量说明。",
        "title": "## 章节 1",
        "parent_title": "# RS-12",
        "file_title": "RS-12 使用说明",
        "item_name": "RS-12 数字万用表",
        "dense_vector": [0.1, 0.2, 1.0, 0.4],
        "sparse_vector": {1: 0.5},
    }
    assert "chunk_id" not in original_chunks[0]
    assert result["milvus_ids"] == [501, 502, 503]
    assert result["chunks"][2]["chunk_id"] == 503
    assert result["milvus_collection_name"] == "knowledge_chunks"

    backup_path = Path(result["milvus_chunks_path"])
    assert backup_path.name == "manual_milvus_chunks.json"
    assert json.loads(backup_path.read_text(encoding="utf-8"))[0]["chunk_id"] == 501


def test_can_disable_backup(tmp_path: Path) -> None:
    result = ImportMilvusNode(
        importer=lambda _entities, _dimension, _collection, _batch: [1],
        backup_enabled=False,
    )(create_milvus_state(tmp_path, chunk_count=1))

    assert result["milvus_chunks_path"] == ""


@pytest.mark.parametrize(
    ("state_updates", "message"),
    [
        ({"chunks": []}, "缺少有效 chunks"),
        ({"chunks": ["invalid"]}, "包含无效元素"),
        ({"chunks": [{"content": "正文"}]}, "缺少 file_title"),
    ],
)
def test_rejects_invalid_state(
    tmp_path: Path,
    state_updates: dict[str, object],
    message: str,
) -> None:
    state = create_milvus_state(tmp_path)
    state.update(state_updates)  # type: ignore[typeddict-item]

    with pytest.raises(ImportValidationError, match=message):
        ImportMilvusNode(importer=lambda *_args: [])(state)


def test_rejects_inconsistent_dense_dimensions(tmp_path: Path) -> None:
    state = create_milvus_state(tmp_path)
    state["chunks"][1]["dense_vector"] = [0.1, 0.2]

    with pytest.raises(ImportValidationError, match="维度不一致"):
        ImportMilvusNode(importer=lambda *_args: [])(state)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("dense_vector", [0.1, float("nan")], "非有限"),
        ("sparse_vector", {}, "稀疏向量"),
        ("sparse_vector", {-1: 0.5}, "索引无效"),
        ("sparse_vector", {1: float("inf")}, "非有限"),
        ("part", 0, "正整数"),
    ],
)
def test_rejects_invalid_chunk_values(
    tmp_path: Path,
    field: str,
    value: object,
    message: str,
) -> None:
    state = create_milvus_state(tmp_path, chunk_count=1)
    state["chunks"][0][field] = value  # type: ignore[literal-required]

    with pytest.raises(ImportValidationError, match=message):
        ImportMilvusNode(importer=lambda *_args: [])(state)


@pytest.mark.parametrize("collection_name", ["", "1-invalid", "包含中文"])
def test_rejects_invalid_collection_name(tmp_path: Path, collection_name: str) -> None:
    with pytest.raises(ImportValidationError, match="集合名称"):
        ImportMilvusNode(
            importer=lambda *_args: [],
            collection_name=collection_name,
        )(create_milvus_state(tmp_path))


@pytest.mark.parametrize("batch_size", [0, 1001])
def test_rejects_invalid_batch_size(tmp_path: Path, batch_size: int) -> None:
    with pytest.raises(ImportValidationError, match="批次大小"):
        ImportMilvusNode(
            importer=lambda *_args: [],
            insert_batch_size=batch_size,
        )(create_milvus_state(tmp_path))


def test_wraps_storage_error(tmp_path: Path) -> None:
    def failed_importer(*_args: object) -> list[int]:
        raise MilvusStorageError("已有集合不兼容")

    with pytest.raises(MilvusImportError, match="已有集合不兼容") as captured:
        ImportMilvusNode(importer=failed_importer)(create_milvus_state(tmp_path))

    assert captured.value.node_name == "import_milvus_node"


def test_wraps_unexpected_client_error_without_details(tmp_path: Path) -> None:
    def failed_importer(*_args: object) -> list[int]:
        raise RuntimeError("sensitive connection details")

    with pytest.raises(MilvusImportError, match="RuntimeError") as captured:
        ImportMilvusNode(importer=failed_importer)(create_milvus_state(tmp_path))

    assert "sensitive connection details" not in str(captured.value)


def test_rejects_mismatched_returned_id_count(tmp_path: Path) -> None:
    with pytest.raises(MilvusImportError, match="主键数量"):
        ImportMilvusNode(importer=lambda *_args: [1])(create_milvus_state(tmp_path))
