"""Tests for block-level markdown parser."""

from md_to_adf.core.parser import convert


def test_convert_returns_doc_structure():
    doc = convert("# Hello")
    assert doc["type"] == "doc"
    assert doc["version"] == 1
    assert isinstance(doc["content"], list)


def test_heading_h1():
    doc = convert("# Hello")
    assert doc["content"][0]["type"] == "heading"
    assert doc["content"][0]["attrs"]["level"] == 1


def test_heading_h3():
    doc = convert("### Sub")
    assert doc["content"][0]["attrs"]["level"] == 3


def test_paragraph():
    doc = convert("Just some text")
    assert doc["content"][0]["type"] == "paragraph"


def test_horizontal_rule():
    doc = convert("---")
    assert doc["content"][0]["type"] == "rule"


def test_horizontal_rule_stars():
    doc = convert("***")
    assert doc["content"][0]["type"] == "rule"


def test_code_block():
    md = "```python\nprint('hi')\n```"
    doc = convert(md)
    block = doc["content"][0]
    assert block["type"] == "codeBlock"
    assert block["attrs"]["language"] == "python"
    assert block["content"][0]["text"] == "print('hi')"


def test_code_block_no_language():
    md = "```\ncode\n```"
    doc = convert(md)
    assert doc["content"][0]["type"] == "codeBlock"


def test_bullet_list():
    md = "- item one\n- item two"
    doc = convert(md)
    assert doc["content"][0]["type"] == "bulletList"
    assert len(doc["content"][0]["content"]) == 2


def test_ordered_list():
    md = "1. first\n2. second"
    doc = convert(md)
    assert doc["content"][0]["type"] == "orderedList"
    assert len(doc["content"][0]["content"]) == 2


def test_nested_list():
    md = "- parent\n  - child"
    doc = convert(md)
    parent_items = doc["content"][0]["content"]
    assert len(parent_items) == 1
    parent_item_content = parent_items[0]["content"]
    assert any(c.get("type") == "bulletList" for c in parent_item_content)


def test_task_list():
    md = "- [ ] todo\n- [x] done"
    doc = convert(md)
    tl = doc["content"][0]
    assert tl["type"] == "taskList"
    assert tl["content"][0]["attrs"]["state"] == "TODO"
    assert tl["content"][1]["attrs"]["state"] == "DONE"


def test_table():
    md = "| A | B |\n|---|---|\n| 1 | 2 |"
    doc = convert(md)
    t = doc["content"][0]
    assert t["type"] == "table"
    assert t["content"][0]["content"][0]["type"] == "tableHeader"
    assert t["content"][1]["content"][0]["type"] == "tableCell"


def test_blockquote_plain():
    md = "> quoted text"
    doc = convert(md)
    assert doc["content"][0]["type"] == "blockquote"


def test_blockquote_note_panel():
    md = "> **Note:** important"
    doc = convert(md)
    assert doc["content"][0]["type"] == "panel"
    assert doc["content"][0]["attrs"]["panelType"] == "note"


def test_blockquote_warning_panel():
    md = "> **Warning:** careful"
    doc = convert(md)
    assert doc["content"][0]["attrs"]["panelType"] == "warning"


def test_blockquote_tip_panel():
    md = "> **Tip:** helpful hint"
    doc = convert(md)
    assert doc["content"][0]["attrs"]["panelType"] == "tip"


def test_blockquote_table_hoisted_from_panel():
    md = "> **Note:** info\n>\n> | A | B |\n> |---|---|\n> | 1 | 2 |"
    doc = convert(md)
    types = [n["type"] for n in doc["content"]]
    assert "panel" in types
    assert "table" in types


def test_details_expand():
    md = "<details>\n<summary>Click me</summary>\nContent here\n</details>"
    doc = convert(md)
    assert doc["content"][0]["type"] == "expand"
    assert doc["content"][0]["attrs"]["title"] == "Click me"


def test_empty_input():
    doc = convert("")
    assert doc["content"] == []


def test_multiple_blocks():
    md = "# Heading\n\nParagraph\n\n- item"
    doc = convert(md)
    types = [n["type"] for n in doc["content"]]
    assert types == ["heading", "paragraph", "bulletList"]


def test_multiline_paragraph():
    md = "line one\nline two"
    doc = convert(md)
    assert doc["content"][0]["type"] == "paragraph"
    assert "line one line two" in doc["content"][0]["content"][0]["text"]
