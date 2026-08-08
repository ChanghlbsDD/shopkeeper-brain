import subprocess
from pathlib import Path

import pytest

from app.workflows.importing.graph import (
    create_import_workflow,
    route_import_file,
    run_import_workflow,
)
from app.workflows.importing.nodes import PdfToMarkdownNode
from app.workflows.importing.state import create_import_state


def successful_mineru(command, _environment, _timeout):
    pdf_path = Path(command[command.index("-p") + 1])
    output_directory = Path(command[command.index("-o") + 1])
    markdown_path = output_directory / pdf_path.stem / "auto" / f"{pdf_path.stem}.md"
    markdown_path.parent.mkdir(parents=True)
    markdown_path.write_text("# Converted", encoding="utf-8")
    return subprocess.CompletedProcess(command, 0, "done", "")


def test_pdf_workflow_visits_all_nodes(tmp_path: Path) -> None:
    source = tmp_path / "manual.pdf"
    source.write_bytes(b"%PDF test fixture")

    workflow = create_import_workflow(pdf_to_md_node=PdfToMarkdownNode(runner=successful_mineru))
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


def test_markdown_workflow_skips_pdf_conversion(tmp_path: Path) -> None:
    source = tmp_path / "manual.md"
    source.write_text("# Manual", encoding="utf-8")

    result = run_import_workflow(str(source))

    assert result["completed_nodes"] == [
        "entry_node",
        "md_img_node",
        "document_split_node",
        "item_name_recognition_node",
        "bge_embedding_node",
        "import_milvus_node",
    ]
    assert "pdf_to_md_node" not in result["node_durations_ms"]


def test_router_rejects_state_without_file_type() -> None:
    with pytest.raises(ValueError, match="没有设置可用的文件类型"):
        route_import_file(create_import_state("manual.md"))
