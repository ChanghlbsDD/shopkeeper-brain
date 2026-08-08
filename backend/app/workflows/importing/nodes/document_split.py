"""按 Markdown 标题结构生成可检索知识片段。"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import TypedDict

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.workflows.importing.base import BaseNode
from app.workflows.importing.exceptions import DocumentSplitError, ImportValidationError
from app.workflows.importing.markdown_tables import MarkdownTableLinearizer
from app.workflows.importing.state import DocumentChunk, ImportGraphState

HEADING_PATTERN = re.compile(r"^\s*(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
FENCE_PATTERN = re.compile(r"^\s*(`{3,}|~{3,})")
TEXT_SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", ".", "!", "?", ";", " ", ""]
TITLE_MAX_LENGTH = 50


class Section(TypedDict, total=False):
    title: str
    parent_title: str
    file_title: str
    body: str
    part: int
    merged: bool


class DocumentSplitNode(BaseNode):
    """标题优先切分，长块递归拆分，短块在相同父标题下合并。"""

    name = "document_split_node"

    def __init__(
        self,
        *,
        max_content_length: int | None = None,
        min_content_length: int | None = None,
        backup_enabled: bool | None = None,
    ) -> None:
        super().__init__()
        self.max_content_length = max_content_length
        self.min_content_length = min_content_length
        self.backup_enabled = backup_enabled

    def process(self, state: ImportGraphState) -> Mapping[str, object]:
        self.log_step("1/6", "校验正文、标题和切分阈值")
        content, file_title, max_length, min_length = self._validate_inputs(state)

        self.log_step("2/6", "按照 Markdown 标题结构初切")
        sections = self._split_by_headings(content, file_title)
        if not sections:
            raise DocumentSplitError("Markdown 没有可切分内容", node_name=self.name)

        self.log_step("3/6", "线性化表格并拆分超长章节")
        split_sections = [
            part for section in sections for part in self._split_long_section(section, max_length)
        ]

        self.log_step("4/6", "合并同一父标题下的短片段")
        final_sections = self._merge_short_sections(split_sections, min_length, max_length)

        self.log_step("5/6", "组装最终知识片段")
        chunks = self._assemble_chunks(final_sections)
        self._log_summary(content, chunks, max_length)

        self.log_step("6/6", "备份切分结果")
        chunks_path = self._backup_chunks(state, chunks)
        return {
            "chunks": chunks,
            "chunks_path": str(chunks_path) if chunks_path is not None else "",
        }

    def _validate_inputs(self, state: ImportGraphState) -> tuple[str, str, int, int]:
        raw_content = state.get("md_content")
        if not isinstance(raw_content, str) or not raw_content.strip():
            raise ImportValidationError("切分的 Markdown 内容不能为空", node_name=self.name)

        file_title = state.get("file_title", "").strip()
        if not file_title:
            raise ImportValidationError("切分的文档名称不能为空", node_name=self.name)

        settings = get_settings()
        max_length = (
            settings.document_chunk_max_length
            if self.max_content_length is None
            else self.max_content_length
        )
        min_length = (
            settings.document_chunk_min_length
            if self.min_content_length is None
            else self.min_content_length
        )
        if max_length < 64 or min_length <= 0 or max_length <= min_length:
            raise ImportValidationError(
                "切分阈值必须满足 max >= 64 且 0 < min < max",
                node_name=self.name,
            )

        content = raw_content.replace("\r\n", "\n").replace("\r", "\n")
        return content, file_title, max_length, min_length

    def _split_by_headings(self, content: str, file_title: str) -> list[Section]:
        sections: list[Section] = []
        hierarchy = [""] * 7
        body_lines: list[str] = []
        current_title = ""
        current_level = 0
        active_fence: tuple[str, int] | None = None
        first_heading = ""

        def flush() -> None:
            body = "\n".join(body_lines).strip()
            if not body:
                return
            title = current_title or file_title
            parent_title = next(
                (hierarchy[level] for level in range(current_level - 1, 0, -1) if hierarchy[level]),
                title,
            )
            sections.append(
                {
                    "title": title,
                    "parent_title": parent_title,
                    "file_title": file_title,
                    "body": body,
                }
            )

        for line in content.split("\n"):
            fence_match = FENCE_PATTERN.match(line)
            if fence_match:
                marker = fence_match.group(1)
                if active_fence is None:
                    active_fence = (marker[0], len(marker))
                elif marker[0] == active_fence[0] and len(marker) >= active_fence[1]:
                    active_fence = None
                body_lines.append(line)
                continue

            heading_match = HEADING_PATTERN.match(line) if active_fence is None else None
            if heading_match:
                flush()
                hashes, heading_text = heading_match.groups()
                current_level = len(hashes)
                current_title = f"{hashes} {heading_text.strip()}"
                first_heading = first_heading or current_title
                hierarchy[current_level] = current_title
                for level in range(current_level + 1, 7):
                    hierarchy[level] = ""
                body_lines = []
                continue

            body_lines.append(line)

        flush()
        if not sections and first_heading:
            sections.append(
                {
                    "title": first_heading,
                    "parent_title": first_heading,
                    "file_title": file_title,
                    "body": "",
                }
            )
        return sections

    def _split_long_section(self, section: Section, max_length: int) -> list[Section]:
        title = section["title"][:TITLE_MAX_LENGTH].rstrip()
        body = MarkdownTableLinearizer.process(section["body"]).strip()
        normalized: Section = {**section, "title": title, "body": body}
        if len(self._section_content(normalized)) <= max_length:
            return [normalized]

        body_length = max_length - len(title) - 2
        if body_length <= 0:
            raise DocumentSplitError(
                f"标题过长，无法在最大长度内切分：{title}",
                node_name=self.name,
            )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=body_length,
            chunk_overlap=0,
            keep_separator="end",
            separators=TEXT_SEPARATORS,
        )
        texts = splitter.split_text(body)
        if not texts:
            return [normalized]
        return [
            {**normalized, "body": text, "part": index} for index, text in enumerate(texts, start=1)
        ]

    def _merge_short_sections(
        self,
        sections: list[Section],
        min_length: int,
        max_length: int,
    ) -> list[Section]:
        if not sections:
            return []

        result: list[Section] = []
        current = sections[0]
        for following in sections[1:]:
            candidate = self._merge_pair(current, following)
            should_merge = (
                current["parent_title"] == following["parent_title"]
                and len(current["body"]) < min_length
                and len(self._section_content(candidate)) <= max_length
            )
            if should_merge:
                current = candidate
            else:
                result.append(current)
                current = following
        result.append(current)
        return result

    @classmethod
    def _merge_pair(cls, left: Section, right: Section) -> Section:
        if left["title"] == right["title"]:
            body = f"{left['body'].rstrip()}\n\n{right['body'].lstrip()}".strip()
            title = left["title"]
        else:
            left_content = left["body"] if left.get("merged") else cls._section_content(left)
            right_content = right["body"] if right.get("merged") else cls._section_content(right)
            body = f"{left_content.rstrip()}\n\n{right_content.lstrip()}".strip()
            title = left["parent_title"]
        return {
            "title": title,
            "parent_title": left["parent_title"],
            "file_title": left["file_title"],
            "body": body,
            "merged": True,
        }

    @staticmethod
    def _section_content(section: Section) -> str:
        body = section["body"].strip()
        return f"{section['title']}\n\n{body}" if body else section["title"]

    def _assemble_chunks(self, sections: list[Section]) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        for section in sections:
            chunk: DocumentChunk = {
                "title": section["title"],
                "parent_title": section["parent_title"],
                "file_title": section["file_title"],
                "content": self._section_content(section),
            }
            if "part" in section:
                chunk["part"] = section["part"]
            chunks.append(chunk)
        return chunks

    def _log_summary(
        self,
        raw_content: str,
        chunks: list[DocumentChunk],
        max_length: int,
    ) -> None:
        self.logger.info(
            "Document split summary: lines=%d chunks=%d max_length=%d",
            raw_content.count("\n") + 1,
            len(chunks),
            max_length,
        )

    def _backup_chunks(
        self,
        state: ImportGraphState,
        chunks: list[DocumentChunk],
    ) -> Path | None:
        settings = get_settings()
        enabled = (
            settings.document_chunk_backup_enabled
            if self.backup_enabled is None
            else self.backup_enabled
        )
        if not enabled:
            return None

        md_path = Path(state.get("md_path", ""))
        if md_path.name:
            output_path = md_path.with_name(f"{md_path.stem}_chunks.json")
        else:
            output_directory = Path(state.get("file_dir", "") or ".")
            output_path = output_directory / f"{state.get('file_title', 'document')}_chunks.json"

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(chunks, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            self.logger.warning("Chunks backup failed: %s", type(exc).__name__)
            return None
        return output_path.resolve()
