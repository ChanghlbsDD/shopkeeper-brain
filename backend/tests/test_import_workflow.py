from pathlib import Path

import pytest

from app.workflows.importing.graph import (
    create_import_workflow,
    route_import_file,
)
from app.workflows.importing.nodes import ItemNameRecognitionNode, PdfToMarkdownNode
from app.workflows.importing.state import create_import_state


def successful_mineru(pdf_path: Path, output_directory: Path) -> Path:
    markdown_path = output_directory / pdf_path.stem / "auto" / "full.md"
    markdown_path.parent.mkdir(parents=True)
    markdown_path.write_text("# Converted", encoding="utf-8")
    return markdown_path


def successful_item_recognizer(_file_title: str, _context: str) -> str:
    return "测试设备"


def test_pdf_workflow_visits_all_nodes(tmp_path: Path) -> None:
    source = tmp_path / "manual.pdf"
    source.write_bytes(b"%PDF test fixture")

    workflow = create_import_workflow(
        pdf_to_md_node=PdfToMarkdownNode(converter=successful_mineru),
        item_name_node=ItemNameRecognitionNode(
            recognizer=successful_item_recognizer,
            backup_enabled=False,
        ),
    )
    result = workflow.invoke(create_import_state(str(source), task_id="pdf-task"))

    assert result["completed_nodes"] == [
        "entry_node",
        "pdf_to_md_node",
        "md_img_node",
        "document_split_node",
        "item_name_recognition_node",
        "bge_embedding_node",
        "import_milvus_node",
    ]
    assert result["task_id"] == "pdf-task"
    assert Path(result["md_path"]).is_file()
    assert result["chunks"][0]["content"] == "# Converted"
    assert result["item_name"] == "测试设备"


def test_markdown_workflow_skips_pdf_conversion(tmp_path: Path) -> None:
    source = tmp_path / "manual.md"
    source.write_text("# Manual", encoding="utf-8")

    workflow = create_import_workflow(
        item_name_node=ItemNameRecognitionNode(
            recognizer=successful_item_recognizer,
            backup_enabled=False,
        )
    )
    result = workflow.invoke(create_import_state(str(source)))

    assert result["completed_nodes"] == [
        "entry_node",
        "md_img_node",
        "document_split_node",
        "item_name_recognition_node",
        "bge_embedding_node",
        "import_milvus_node",
    ]
    assert "pdf_to_md_node" not in result["node_durations_ms"]
    assert result["chunks"][0]["content"] == "# Manual"
    assert result["item_name"] == "测试设备"


def test_router_rejects_state_without_file_type() -> None:
    with pytest.raises(ValueError, match="没有设置可用的文件类型"):
        route_import_file(create_import_state("manual.md"))
