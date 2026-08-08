import subprocess
from pathlib import Path

import pytest

from app.core.config import REPOSITORY_ROOT
from app.workflows.importing.exceptions import ImportValidationError, PdfConversionError
from app.workflows.importing.nodes import EntryNode, PdfToMarkdownNode
from app.workflows.importing.state import create_import_state


def create_pdf_state(tmp_path: Path):
    pdf_path = tmp_path / "商品说明.pdf"
    pdf_path.write_bytes(b"%PDF test fixture")
    output_directory = tmp_path / "output"
    state = EntryNode()(create_import_state(str(pdf_path), file_dir=str(output_directory)))
    return pdf_path, output_directory, state


def test_pdf_to_markdown_runs_pipeline_and_updates_state(tmp_path: Path) -> None:
    pdf_path, output_directory, state = create_pdf_state(tmp_path)
    calls = []

    def successful_runner(command, environment, timeout):
        calls.append((list(command), dict(environment), timeout))
        markdown_path = output_directory / pdf_path.stem / "auto" / f"{pdf_path.stem}.md"
        markdown_path.parent.mkdir(parents=True)
        markdown_path.write_text("# 商品说明", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "converted", "")

    result = PdfToMarkdownNode(
        runner=successful_runner,
        executable="mineru-test",
    )(state)

    command, environment, timeout = calls[0]
    assert command == [
        "mineru-test",
        "-p",
        str(pdf_path.resolve()),
        "-o",
        str(output_directory.resolve()),
        "-b",
        "pipeline",
    ]
    assert environment["MINERU_MODEL_SOURCE"] == "modelscope"
    assert Path(environment["MODELSCOPE_CACHE"]) == (REPOSITORY_ROOT / "models/modelscope")
    assert Path(environment["HF_HOME"]) == (REPOSITORY_ROOT / "models/huggingface")
    assert timeout == 1800
    assert result["md_path"] == str(
        (output_directory / pdf_path.stem / "auto" / f"{pdf_path.stem}.md").resolve()
    )
    assert result["is_md_read_enabled"] is True
    assert result["completed_nodes"][-1] == "pdf_to_md_node"


def test_pdf_to_markdown_accepts_changed_output_subdirectory(tmp_path: Path) -> None:
    pdf_path, output_directory, state = create_pdf_state(tmp_path)

    def successful_runner(command, _environment, _timeout):
        markdown_path = output_directory / pdf_path.stem / "custom" / f"{pdf_path.stem}.md"
        markdown_path.parent.mkdir(parents=True)
        markdown_path.write_text("# Converted", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    result = PdfToMarkdownNode(runner=successful_runner, executable="mineru-test")(state)

    assert Path(result["md_path"]).parent.name == "custom"


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
        PdfToMarkdownNode(executable="mineru-test")(state)


def test_pdf_to_markdown_rejects_file_as_output_directory(tmp_path: Path) -> None:
    pdf_path = tmp_path / "manual.pdf"
    pdf_path.write_bytes(b"%PDF test fixture")
    output_path = tmp_path / "not-a-directory"
    output_path.write_text("file", encoding="utf-8")

    with pytest.raises(ImportValidationError, match="输出路径不是目录"):
        PdfToMarkdownNode(executable="mineru-test")(
            {"pdf_path": str(pdf_path), "file_dir": str(output_path)}
        )


def test_pdf_to_markdown_reports_nonzero_exit(tmp_path: Path) -> None:
    _pdf_path, _output_directory, state = create_pdf_state(tmp_path)

    def failed_runner(command, _environment, _timeout):
        return subprocess.CompletedProcess(command, 2, "", "model failed")

    with pytest.raises(PdfConversionError, match="退出码 2.*model failed"):
        PdfToMarkdownNode(runner=failed_runner, executable="mineru-test")(state)


def test_pdf_to_markdown_reports_missing_output(tmp_path: Path) -> None:
    _pdf_path, _output_directory, state = create_pdf_state(tmp_path)

    def no_output_runner(command, _environment, _timeout):
        return subprocess.CompletedProcess(command, 0, "done", "")

    with pytest.raises(PdfConversionError, match="没有找到生成的 Markdown"):
        PdfToMarkdownNode(runner=no_output_runner, executable="mineru-test")(state)


def test_pdf_to_markdown_reports_timeout(tmp_path: Path) -> None:
    _pdf_path, _output_directory, state = create_pdf_state(tmp_path)

    def timeout_runner(command, _environment, timeout):
        raise subprocess.TimeoutExpired(command, timeout)

    with pytest.raises(PdfConversionError, match="转换超过 1800 秒"):
        PdfToMarkdownNode(runner=timeout_runner, executable="mineru-test")(state)
