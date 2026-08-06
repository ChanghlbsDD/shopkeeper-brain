"""文档导入入口节点。"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from app.workflows.importing.base import BaseNode
from app.workflows.importing.exceptions import ImportValidationError
from app.workflows.importing.state import ImportGraphState


class EntryNode(BaseNode):
    """校验输入文件并决定 PDF 或 Markdown 分支。"""

    name = "entry_node"

    def process(self, state: ImportGraphState) -> Mapping[str, object]:
        self.log_step("1/3", "读取导入路径")
        raw_path = state.get("import_file_path", "").strip()
        if not raw_path:
            raise ImportValidationError("导入文件路径不能为空", node_name=self.name)

        source_path = Path(raw_path).expanduser()
        self.log_step("2/3", "检查文件是否存在")
        if not source_path.is_file():
            raise ImportValidationError(
                f"导入文件不存在：{source_path}",
                node_name=self.name,
            )

        suffix = source_path.suffix.lower()
        self.log_step("3/3", "识别 PDF 或 Markdown 类型")
        if suffix == ".pdf":
            source_kind = "pdf"
            pdf_path = str(source_path.resolve())
            md_path = ""
        elif suffix in {".md", ".markdown"}:
            source_kind = "md"
            pdf_path = ""
            md_path = str(source_path.resolve())
        else:
            raise ImportValidationError(
                f"不支持的文件类型：{suffix or '无扩展名'}",
                node_name=self.name,
            )

        file_dir = state.get("file_dir", "").strip()
        output_directory = Path(file_dir).expanduser() if file_dir else source_path.parent

        return {
            "import_file_path": str(source_path.resolve()),
            "file_dir": str(output_directory.resolve()),
            "source_kind": source_kind,
            "is_pdf_read_enabled": source_kind == "pdf",
            "is_md_read_enabled": source_kind == "md",
            "pdf_path": pdf_path,
            "md_path": md_path,
            "file_title": source_path.stem,
        }
