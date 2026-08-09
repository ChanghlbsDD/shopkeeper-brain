from collections.abc import Mapping
from pathlib import Path

import pytest

from app.workflows.importing.base import BaseNode
from app.workflows.importing.exceptions import ImportNodeError, ImportValidationError
from app.workflows.importing.nodes import EntryNode
from app.workflows.importing.state import ImportGraphState, create_import_state


class BrokenNode(BaseNode):
    name = "broken_node"

    def process(self, _state: ImportGraphState) -> Mapping[str, object]:
        raise RuntimeError("internal failure")


def test_entry_node_selects_pdf_branch(tmp_path: Path) -> None:
    source = tmp_path / "product-manual.PDF"
    source.write_bytes(b"%PDF test fixture")

    result = EntryNode()(create_import_state(str(source)))

    assert result["source_kind"] == "pdf"
    assert result["is_pdf_read_enabled"] is True
    assert result["is_md_read_enabled"] is False
    assert result["pdf_path"] == str(source.resolve())
    assert result["file_title"] == "product-manual"
    assert result["completed_nodes"] == ["entry_node"]
    assert "entry_node" in result["node_durations_ms"]


def test_entry_node_selects_markdown_branch(tmp_path: Path) -> None:
    source = tmp_path / "repair-guide.markdown"
    source.write_text("# Repair guide", encoding="utf-8")

    result = EntryNode()(create_import_state(str(source)))

    assert result["source_kind"] == "md"
    assert result["is_pdf_read_enabled"] is False
    assert result["is_md_read_enabled"] is True
    assert result["md_path"] == str(source.resolve())


@pytest.mark.parametrize("filename", ["missing.pdf", "manual.txt"])
def test_entry_node_rejects_missing_or_unsupported_files(tmp_path: Path, filename: str) -> None:
    source = tmp_path / filename
    if source.suffix == ".txt":
        source.write_text("unsupported", encoding="utf-8")

    with pytest.raises(ImportValidationError):
        EntryNode()(create_import_state(str(source)))


def test_entry_node_rejects_empty_path() -> None:
    with pytest.raises(ImportValidationError, match="导入文件路径不能为空"):
        EntryNode()(create_import_state(""))


def test_base_node_wraps_unexpected_errors() -> None:
    with pytest.raises(ImportNodeError) as captured:
        BrokenNode()(create_import_state("manual.md"))

    assert captured.value.node_name == "broken_node"
    assert isinstance(captured.value.cause, RuntimeError)
    assert str(captured.value) == "[broken_node] 节点执行失败"


def test_base_node_reports_started_and_completed_progress(tmp_path: Path) -> None:
    source = tmp_path / "manual.md"
    source.write_text("# Manual", encoding="utf-8")
    events: list[tuple[str, str, float | None]] = []
    state = create_import_state(
        str(source),
        progress_callback=lambda event, node, duration: events.append((event, node, duration)),
    )

    EntryNode()(state)

    assert events[0] == ("started", "entry_node", None)
    assert events[1][0:2] == ("completed", "entry_node")
    assert isinstance(events[1][2], float)
