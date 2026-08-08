from app.workflows.importing.markdown_tables import MarkdownTableLinearizer


def test_linearizes_markdown_table() -> None:
    content = (
        "参数如下：\n\n"
        "| 参数 | 值 | 单位 |\n"
        "| :--- | ---: | --- |\n"
        "| 电压 | 220 | V |\n"
        "| 频率 | 50 | Hz |\n"
    )

    result = MarkdownTableLinearizer.process(content)

    assert "| :--- |" not in result
    assert "【电压】（参数）：值为220，单位为V。" in result
    assert "【频率】（参数）：值为50，单位为Hz。" in result


def test_linearizes_two_column_html_as_key_value_items() -> None:
    content = (
        "<table><tr><td>型号</td><td>SK-1</td></tr><tr><td>额定电压</td><td>220V</td></tr></table>"
    )

    result = MarkdownTableLinearizer.process(content)

    assert "<table>" not in result
    assert "【型号】：SK-1。" in result
    assert "【额定电压】：220V。" in result


def test_expands_html_rowspan_before_linearizing() -> None:
    content = (
        "<table>"
        "<tr><th>类型</th><th>电压</th></tr>"
        '<tr><td rowspan="2">交流</td><td>220V</td></tr>'
        "<tr><td>110V</td></tr>"
        "</table>"
    )

    result = MarkdownTableLinearizer.process(content)

    assert "【交流】（类型）：电压为220V。" in result
    assert "【交流】（类型）：电压为110V。" in result


def test_non_table_content_is_unchanged() -> None:
    content = "# 标题\n\n普通正文，没有表格。"

    assert MarkdownTableLinearizer.process(content) == content
