from pathlib import Path

import pytest

from app.clients.mineru_api import MinerUApiError
from app.workflows.importing.exceptions import ImportValidationError, PdfConversionError
from app.workflows.importing.nodes import EntryNode, PdfToMarkdownNode
from app.workflows.importing.state import create_import_state


def create_pdf_state(tmp_path: Path):
    pdf_path = tmp_path / "商品说明.pdf"
    pdf_path.write_bytes(b"%PDF test fixture")
    output_directory = tmp_path / "output"
    state = EntryNode()(create_import_state(str(pdf_path), file_dir=str(output_directory)))
    return pdf_path, output_directory, state


def test_pdf_to_markdown_calls_api_converter_and_updates_state(tmp_path: Path) -> None:
    pdf_path, output_directory, state = create_pdf_state(tmp_path)
    calls = []

    def successful_converter(source: Path, destination: Path) -> Path:
        calls.append((source, destination))
        markdown_path = destination / source.stem / "auto" / "full.md"
        markdown_path.parent.mkdir(parents=True)
        markdown_path.write_text("# 商品说明", encoding="utf-8")
        return markdown_path

    result = PdfToMarkdownNode(converter=successful_converter)(state)

    assert calls == [(pdf_path.resolve(), output_directory.resolve())]
    assert result["md_path"] == str(
        (output_directory / pdf_path.stem / "auto" / "full.md").resolve()
    )
    assert result["is_md_read_enabled"] is True
    assert result["completed_nodes"][-1] == "pdf_to_md_node"


@pytest.mark.parametrize(
    ("state", "message"),
    [
        ({"pdf_path": "", "file_dir": "output"}, "PDF 路径不能为空"),
        ({"pdf_path": "manual.txt", "file_dir": "output"}, "不支持该文件类型"),
        ({"pdf_path": "missing.pdf", "file_dir": "output"}, "PDF 文件不存在"),
    ],
)
def test_pdf_to_markdown_rejects_invalid_pdf_state(state, message: str) -> None:
    with pytest.raises(ImportValidationError, match=message):
        PdfToMarkdownNode()(state)


def test_pdf_to_markdown_rejects_file_as_output_directory(tmp_path: Path) -> None:
    pdf_path = tmp_path / "manual.pdf"
    pdf_path.write_bytes(b"%PDF test fixture")
    output_path = tmp_path / "not-a-directory"
    output_path.write_text("file", encoding="utf-8")

    with pytest.raises(ImportValidationError, match="输出路径不是目录"):
        PdfToMarkdownNode()({"pdf_path": str(pdf_path), "file_dir": str(output_path)})


def test_pdf_to_markdown_wraps_api_error(tmp_path: Path) -> None:
    _pdf_path, _output_directory, state = create_pdf_state(tmp_path)

    def failed_converter(_source: Path, _destination: Path) -> Path:
        raise MinerUApiError("远程服务繁忙")

    with pytest.raises(PdfConversionError, match="远程服务繁忙"):
        PdfToMarkdownNode(converter=failed_converter)(state)


def test_pdf_to_markdown_rejects_missing_api_output(tmp_path: Path) -> None:
    _pdf_path, output_directory, state = create_pdf_state(tmp_path)

    def missing_output_converter(_source: Path, _destination: Path) -> Path:
        return output_directory / "missing.md"

    with pytest.raises(PdfConversionError, match="没有生成 Markdown"):
        PdfToMarkdownNode(converter=missing_output_converter)(state)
