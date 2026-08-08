import json
from pathlib import Path

import pytest

from app.workflows.importing.exceptions import ImportValidationError
from app.workflows.importing.nodes import DocumentSplitNode
from app.workflows.importing.state import ImportGraphState, create_import_state


def create_split_state(
    tmp_path: Path,
    content: str,
    *,
    file_title: str = "产品手册",
) -> ImportGraphState:
    markdown_path = tmp_path / "manual.md"
    markdown_path.write_text(content, encoding="utf-8")
    state = create_import_state(str(markdown_path))
    state.update(
        {
            "md_path": str(markdown_path),
            "md_content": content,
            "file_title": file_title,
            "file_dir": str(tmp_path),
        }
    )
    return state


def test_splits_by_heading_and_keeps_parent_hierarchy(tmp_path: Path) -> None:
    content = "前言内容。\r\n\r\n# 使用手册\r\n\r\n总体介绍。\r\n\r\n## 安全\r\n\r\n安全说明。"
    node = DocumentSplitNode(max_content_length=500, min_content_length=1)

    result = node(create_split_state(tmp_path, content))

    assert [chunk["title"] for chunk in result["chunks"]] == [
        "产品手册",
        "# 使用手册",
        "## 安全",
    ]
    assert result["chunks"][0]["parent_title"] == "产品手册"
    assert result["chunks"][2]["parent_title"] == "# 使用手册"
    assert "\r" not in result["chunks"][0]["content"]
    chunks_path = Path(result["chunks_path"])
    assert chunks_path.name == "manual_chunks.json"
    assert json.loads(chunks_path.read_text(encoding="utf-8")) == result["chunks"]


def test_does_not_treat_heading_inside_code_fence_as_section(tmp_path: Path) -> None:
    content = (
        "# 示例\n\n"
        "```python\n"
        "# 这是 Python 注释，不是标题\n"
        "print('hello')\n"
        "```\n\n"
        "示例正文。\n\n"
        "## 真正标题\n\n"
        "第二部分。"
    )

    result = DocumentSplitNode(max_content_length=500, min_content_length=1)(
        create_split_state(tmp_path, content)
    )

    assert len(result["chunks"]) == 2
    assert "# 这是 Python 注释，不是标题" in result["chunks"][0]["content"]
    assert result["chunks"][1]["title"] == "## 真正标题"


def test_heading_only_document_still_produces_one_chunk(tmp_path: Path) -> None:
    result = DocumentSplitNode(max_content_length=500, min_content_length=1)(
        create_split_state(tmp_path, "# 只有标题")
    )

    assert result["chunks"] == [
        {
            "title": "# 只有标题",
            "parent_title": "# 只有标题",
            "file_title": "产品手册",
            "content": "# 只有标题",
        }
    ]


def test_long_section_is_split_without_exceeding_max_length(tmp_path: Path) -> None:
    body = "这是需要保留标点的产品说明。" * 30
    result = DocumentSplitNode(max_content_length=100, min_content_length=1)(
        create_split_state(tmp_path, f"# 规格\n\n{body}")
    )

    assert len(result["chunks"]) > 1
    assert [chunk["part"] for chunk in result["chunks"]] == list(
        range(1, len(result["chunks"]) + 1)
    )
    assert all(len(chunk["content"]) <= 100 for chunk in result["chunks"])
    assert all("。" in chunk["content"] for chunk in result["chunks"])


def test_merges_short_siblings_under_same_parent(tmp_path: Path) -> None:
    content = "# 操作指南\n\n## 开机\n\n按下开关。\n\n## 关机\n\n关闭电源。"
    result = DocumentSplitNode(max_content_length=200, min_content_length=50)(
        create_split_state(tmp_path, content)
    )

    assert len(result["chunks"]) == 1
    chunk = result["chunks"][0]
    assert chunk["title"] == "# 操作指南"
    assert "## 开机" in chunk["content"]
    assert "## 关机" in chunk["content"]


def test_does_not_merge_different_parents_or_exceed_max_length(tmp_path: Path) -> None:
    different_parents = "# 第一章\n\n很短。\n\n# 第二章\n\n也很短。"
    result = DocumentSplitNode(max_content_length=100, min_content_length=50)(
        create_split_state(tmp_path, different_parents)
    )
    assert len(result["chunks"]) == 2

    oversized_merge = f"# 根\n\n## A\n\n{'甲' * 50}\n\n## B\n\n{'乙' * 40}"
    result = DocumentSplitNode(max_content_length=80, min_content_length=60)(
        create_split_state(tmp_path, oversized_merge)
    )
    assert len(result["chunks"]) == 2
    assert all(len(chunk["content"]) <= 80 for chunk in result["chunks"])


def test_linearizes_table_before_creating_chunk(tmp_path: Path) -> None:
    content = "# 参数\n\n| 属性 | 值 |\n| --- | --- |\n| 电压 | 220V |"

    result = DocumentSplitNode(max_content_length=500, min_content_length=1)(
        create_split_state(tmp_path, content)
    )

    assert "| --- |" not in result["chunks"][0]["content"]
    assert "【电压】（属性）：值为220V。" in result["chunks"][0]["content"]


@pytest.mark.parametrize(
    ("content", "title", "max_length", "min_length", "message"),
    [
        ("   ", "手册", 500, 100, "内容不能为空"),
        ("正文", "", 500, 100, "文档名称不能为空"),
        ("正文", "手册", 63, 10, "切分阈值"),
        ("正文", "手册", 100, 100, "切分阈值"),
    ],
)
def test_rejects_invalid_inputs(
    tmp_path: Path,
    content: str,
    title: str,
    max_length: int,
    min_length: int,
    message: str,
) -> None:
    state = create_split_state(tmp_path, content, file_title=title)

    with pytest.raises(ImportValidationError, match=message):
        DocumentSplitNode(
            max_content_length=max_length,
            min_content_length=min_length,
        )(state)


def test_can_disable_chunks_backup(tmp_path: Path) -> None:
    state = create_split_state(tmp_path, "没有标题的正文。")

    result = DocumentSplitNode(
        max_content_length=500,
        min_content_length=1,
        backup_enabled=False,
    )(state)

    assert len(result["chunks"]) == 1
    assert result["chunks_path"] == ""
    assert not (tmp_path / "manual_chunks.json").exists()
