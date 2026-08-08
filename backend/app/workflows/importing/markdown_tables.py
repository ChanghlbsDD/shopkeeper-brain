"""把 Markdown 和 HTML 表格转换为适合检索的线性文本。"""

from __future__ import annotations

import re
from collections.abc import Sequence

from bs4 import BeautifulSoup, Tag

HTML_TABLE_PATTERN = re.compile(r"<table\b[^>]*>.*?</table>", re.IGNORECASE | re.DOTALL)
MARKDOWN_SEPARATOR_PATTERN = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
MAX_TABLE_SPAN = 100


class MarkdownTableLinearizer:
    """保留表格行列关系，同时输出可直接向量化的自然语言。"""

    @classmethod
    def process(cls, content: str) -> str:
        if not content:
            return content

        processed = HTML_TABLE_PATTERN.sub(cls._replace_html_table, content)
        return cls._replace_markdown_tables(processed)

    @classmethod
    def _replace_html_table(cls, match: re.Match[str]) -> str:
        html = match.group(0)
        table = BeautifulSoup(html, "html.parser").find("table")
        if not isinstance(table, Tag):
            return html

        rows = table.find_all("tr")
        if not rows:
            return html

        grid: list[list[str | None]] = [[] for _ in rows]
        for row_index, row in enumerate(rows):
            column_index = 0
            cells = row.find_all(["td", "th"], recursive=False)
            for cell in cells:
                while (
                    column_index < len(grid[row_index])
                    and grid[row_index][column_index] is not None
                ):
                    column_index += 1

                rowspan = cls._safe_span(cell.get("rowspan"))
                colspan = cls._safe_span(cell.get("colspan"))
                text = cell.get_text(separator=" ", strip=True)
                required_rows = row_index + rowspan
                while len(grid) < required_rows:
                    grid.append([])

                for target_row in range(row_index, required_rows):
                    required_columns = column_index + colspan
                    while len(grid[target_row]) < required_columns:
                        grid[target_row].append(None)
                    for target_column in range(column_index, required_columns):
                        grid[target_row][target_column] = text
                column_index += colspan

        normalized_grid = [[cell or "" for cell in row] for row in grid]
        return cls._grid_to_text(normalized_grid, has_header=table.find("th") is not None)

    @classmethod
    def _replace_markdown_tables(cls, content: str) -> str:
        lines = content.split("\n")
        output: list[str] = []
        index = 0

        while index < len(lines):
            if (
                index + 1 < len(lines)
                and "|" in lines[index]
                and MARKDOWN_SEPARATOR_PATTERN.match(lines[index + 1])
            ):
                table_lines = [lines[index]]
                index += 2
                while index < len(lines) and "|" in lines[index] and lines[index].strip():
                    table_lines.append(lines[index])
                    index += 1

                grid = [cls._parse_markdown_row(line) for line in table_lines]
                output.extend(cls._grid_to_text(grid, has_header=True).split("\n"))
                continue

            output.append(lines[index])
            index += 1

        return "\n".join(output)

    @staticmethod
    def _parse_markdown_row(line: str) -> list[str]:
        stripped = line.strip()
        if stripped.startswith("|"):
            stripped = stripped[1:]
        if stripped.endswith("|") and not stripped.endswith("\\|"):
            stripped = stripped[:-1]
        return [cell.replace("\\|", "|").strip() for cell in re.split(r"(?<!\\)\|", stripped)]

    @staticmethod
    def _safe_span(raw_value: object) -> int:
        try:
            value = int(str(raw_value or 1))
        except ValueError:
            return 1
        return max(1, min(value, MAX_TABLE_SPAN))

    @classmethod
    def _grid_to_text(cls, grid: Sequence[Sequence[str]], *, has_header: bool) -> str:
        if not grid:
            return ""

        column_count = max((len(row) for row in grid), default=0)
        if column_count == 0:
            return ""

        rows = [list(row) + [""] * (column_count - len(row)) for row in grid]
        if not has_header and column_count == 2:
            items = [
                f"- 【{key or '未知属性'}】：{value or '无'}。"
                for key, value in rows
                if key or value
            ]
            return "\n".join(items)

        headers = rows[0]
        items: list[str] = []
        for row in rows[1:]:
            if not any(row):
                continue
            subject = row[0] or "未知项目"
            subject_header = headers[0]
            properties = [
                f"{headers[index] or f'属性{index}'}为{value}"
                for index, value in enumerate(row[1:], start=1)
                if value and value not in {"-", "/", "\\", "无"}
            ]
            relation = f"（{subject_header}）" if subject_header else ""
            if properties:
                items.append(f"- 【{subject}】{relation}：{'，'.join(properties)}。")
            elif subject != "未知项目":
                items.append(f"- 【{subject}】")
        return "\n".join(items)
