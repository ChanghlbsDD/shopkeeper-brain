import json
from pathlib import Path

import pytest

from app.clients.qwen_chat import QwenChatError
from app.workflows.importing.exceptions import ImportValidationError, ItemNameRecognitionError
from app.workflows.importing.nodes import ItemNameRecognitionNode
from app.workflows.importing.state import ImportGraphState, create_import_state


def create_item_state(tmp_path: Path) -> ImportGraphState:
    markdown_path = tmp_path / "manual.md"
    markdown_path.write_text("# RS-12 使用说明", encoding="utf-8")
    state = create_import_state(str(markdown_path))
    state.update(
        {
            "md_path": str(markdown_path),
            "file_dir": str(tmp_path),
            "file_title": "RS-12 使用说明",
            "chunks": [
                {
                    "title": "# 产品介绍",
                    "parent_title": "# 产品介绍",
                    "file_title": "RS-12 使用说明",
                    "content": "# 产品介绍\n\nRS-12 是一款数字万用表。",
                },
                {
                    "title": "## 安全",
                    "parent_title": "# 产品介绍",
                    "file_title": "RS-12 使用说明",
                    "content": "## 安全\n\n测量前请检查表笔。",
                },
            ],
        }
    )
    return state


def test_recognizes_item_name_and_fills_every_chunk(tmp_path: Path) -> None:
    state = create_item_state(tmp_path)
    original_chunks = state["chunks"]
    captured: dict[str, str] = {}

    def recognizer(file_title: str, context: str) -> str:
        captured.update({"file_title": file_title, "context": context})
        return "  优利德   RS-12  数字万用表  "

    result = ItemNameRecognitionNode(recognizer=recognizer)(state)

    assert result["item_name"] == "优利德 RS-12 数字万用表"
    assert result["item_name_source"] == "qwen"
    assert all(chunk["item_name"] == result["item_name"] for chunk in result["chunks"])
    assert "item_name" not in original_chunks[0]
    assert captured["file_title"] == "RS-12 使用说明"
    assert "【切片 1】" in captured["context"]
    assert "【切片 2】" in captured["context"]

    backup_path = Path(result["item_name_chunks_path"])
    assert backup_path.name == "manual_item_name_chunks.json"
    assert json.loads(backup_path.read_text(encoding="utf-8")) == result["chunks"]


def test_limits_context_by_chunk_count_and_total_length(tmp_path: Path) -> None:
    state = create_item_state(tmp_path)
    state["chunks"].append(
        {
            "title": "## 第三块",
            "parent_title": "# 产品介绍",
            "file_title": "RS-12 使用说明",
            "content": "第三块不应进入上下文。",
        }
    )
    captured_context = ""

    def recognizer(_file_title: str, context: str) -> str:
        nonlocal captured_context
        captured_context = context
        return "数字万用表"

    ItemNameRecognitionNode(
        recognizer=recognizer,
        chunk_count=2,
        context_max_length=60,
        backup_enabled=False,
    )(state)

    assert len(captured_context) <= 60
    assert "【切片 1】" in captured_context
    assert "切片 3" not in captured_context
    assert "第三块不应进入上下文" not in captured_context


def test_unknown_result_falls_back_to_file_title(tmp_path: Path) -> None:
    result = ItemNameRecognitionNode(
        recognizer=lambda _title, _context: "UNKNOWN",
        backup_enabled=False,
    )(create_item_state(tmp_path))

    assert result["item_name"] == "RS-12 使用说明"
    assert result["item_name_source"] == "file_title_fallback"
    assert result["item_name_chunks_path"] == ""


def test_wraps_qwen_client_error(tmp_path: Path) -> None:
    def failed_recognizer(_title: str, _context: str) -> str:
        raise QwenChatError("通义千问不可用")

    with pytest.raises(ItemNameRecognitionError, match="通义千问不可用") as captured:
        ItemNameRecognitionNode(recognizer=failed_recognizer)(create_item_state(tmp_path))

    assert captured.value.node_name == "item_name_recognition_node"


@pytest.mark.parametrize("result", ["", "   ", "商品" * 101])
def test_rejects_invalid_recognized_name(tmp_path: Path, result: str) -> None:
    with pytest.raises(ItemNameRecognitionError):
        ItemNameRecognitionNode(
            recognizer=lambda _title, _context: result,
            backup_enabled=False,
        )(create_item_state(tmp_path))


@pytest.mark.parametrize(
    ("state_updates", "message"),
    [
        ({"file_title": ""}, "缺少文档名称"),
        ({"chunks": []}, "缺少有效 chunks"),
        ({"chunks": ["invalid"]}, "包含无效元素"),
        ({"chunks": [{"content": ""}]}, "没有可用于识别的正文"),
    ],
)
def test_rejects_invalid_state(
    tmp_path: Path,
    state_updates: dict[str, object],
    message: str,
) -> None:
    state = create_item_state(tmp_path)
    state.update(state_updates)  # type: ignore[typeddict-item]

    with pytest.raises(ImportValidationError, match=message):
        ItemNameRecognitionNode(
            recognizer=lambda _title, _context: "数字万用表",
            backup_enabled=False,
        )(state)


@pytest.mark.parametrize(
    ("chunk_count", "max_length"),
    [(0, 100), (1, 31)],
)
def test_rejects_invalid_context_configuration(
    tmp_path: Path,
    chunk_count: int,
    max_length: int,
) -> None:
    with pytest.raises(ImportValidationError, match="上下文配置"):
        ItemNameRecognitionNode(
            recognizer=lambda _title, _context: "数字万用表",
            chunk_count=chunk_count,
            context_max_length=max_length,
            backup_enabled=False,
        )(create_item_state(tmp_path))
