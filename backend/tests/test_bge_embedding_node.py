import json
from pathlib import Path

import pytest

from app.clients.dashscope_embedding import DashScopeEmbeddingError, TextEmbedding
from app.workflows.importing.exceptions import EmbeddingError, ImportValidationError
from app.workflows.importing.nodes import BgeEmbeddingNode
from app.workflows.importing.state import ImportGraphState, create_import_state


def create_embedding_state(tmp_path: Path, *, chunk_count: int = 3) -> ImportGraphState:
    markdown_path = tmp_path / "manual.md"
    markdown_path.write_text("# RS-12 使用说明", encoding="utf-8")
    state = create_import_state(str(markdown_path))
    state.update(
        {
            "md_path": str(markdown_path),
            "file_dir": str(tmp_path),
            "item_name": "RS-12 数字万用表",
            "chunks": [
                {
                    "title": f"## 章节 {index}",
                    "parent_title": "# RS-12",
                    "file_title": "RS-12 使用说明",
                    "content": f"第 {index} 个测量说明。",
                    "item_name": "RS-12 数字万用表",
                }
                for index in range(1, chunk_count + 1)
            ],
        }
    )
    return state


def fake_embedding(index: int) -> TextEmbedding:
    return TextEmbedding(
        dense_vector=[float(index), float(index) + 0.5],
        sparse_vector={index: float(index) / 10},
    )


def test_batches_embeddings_and_fills_every_chunk_without_mutating_input(
    tmp_path: Path,
) -> None:
    state = create_embedding_state(tmp_path, chunk_count=5)
    original_chunks = state["chunks"]
    batches: list[list[str]] = []
    next_index = 1

    def embedder(texts: list[str]) -> list[TextEmbedding]:
        nonlocal next_index
        batches.append(texts)
        result = [fake_embedding(index) for index in range(next_index, next_index + len(texts))]
        next_index += len(texts)
        return result

    result = BgeEmbeddingNode(embedder=embedder, batch_size=2)(state)

    assert [len(batch) for batch in batches] == [2, 2, 1]
    assert batches[0][0] == "RS-12 数字万用表\n第 1 个测量说明。"
    assert "dense_vector" not in original_chunks[0]
    assert result["chunks"][0]["dense_vector"] == [1.0, 1.5]
    assert result["chunks"][4]["sparse_vector"] == {5: 0.5}
    assert len(result["embeddings"]) == 5

    backup_path = Path(result["embedding_chunks_path"])
    assert backup_path.name == "manual_vectors.json"
    assert json.loads(backup_path.read_text(encoding="utf-8"))[0]["sparse_vector"] == {"1": 0.1}


def test_can_disable_vector_backup(tmp_path: Path) -> None:
    result = BgeEmbeddingNode(
        embedder=lambda _texts: [fake_embedding(1)],
        backup_enabled=False,
    )(create_embedding_state(tmp_path, chunk_count=1))

    assert result["embedding_chunks_path"] == ""
    assert not (tmp_path / "manual_vectors.json").exists()


def test_wraps_embedding_client_error(tmp_path: Path) -> None:
    def failed_embedder(_texts: list[str]) -> list[TextEmbedding]:
        raise DashScopeEmbeddingError("百炼向量服务不可用")

    with pytest.raises(EmbeddingError, match="百炼向量服务不可用") as captured:
        BgeEmbeddingNode(embedder=failed_embedder)(create_embedding_state(tmp_path))

    assert captured.value.node_name == "bge_embedding_node"


def test_rejects_mismatched_embedding_count(tmp_path: Path) -> None:
    with pytest.raises(EmbeddingError, match="向量数量"):
        BgeEmbeddingNode(embedder=lambda _texts: [])(create_embedding_state(tmp_path))


@pytest.mark.parametrize(
    ("state_updates", "message"),
    [
        ({"chunks": []}, "缺少有效 chunks"),
        ({"chunks": ["invalid"]}, "包含无效元素"),
        ({"chunks": [{"content": "正文", "item_name": ""}]}, "缺少商品名称"),
        ({"chunks": [{"content": "", "item_name": "商品"}]}, "缺少正文"),
    ],
)
def test_rejects_invalid_state(
    tmp_path: Path,
    state_updates: dict[str, object],
    message: str,
) -> None:
    state = create_embedding_state(tmp_path)
    state.update(state_updates)  # type: ignore[typeddict-item]

    with pytest.raises(ImportValidationError, match=message):
        BgeEmbeddingNode(embedder=lambda _texts: [])(state)


@pytest.mark.parametrize("batch_size", [0, 11])
def test_rejects_batch_size_outside_api_limit(tmp_path: Path, batch_size: int) -> None:
    with pytest.raises(ImportValidationError, match="1 到 10"):
        BgeEmbeddingNode(embedder=lambda _texts: [], batch_size=batch_size)(
            create_embedding_state(tmp_path)
        )
