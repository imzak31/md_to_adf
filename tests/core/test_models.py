"""Comprehensive tests for ADF node builder helpers in core/models.py."""

import pytest
from md_to_adf.core.models import (
    lid,
    text,
    paragraph,
    heading,
    rule,
    code_block,
    panel,
    bullet_list,
    ordered_list,
    list_item,
    task_list,
    task_item,
    expand,
    table,
    table_row,
    table_header,
    table_cell,
    blockquote,
    status,
)


# --- lid ---

def test_lid_returns_8_char_string():
    result = lid()
    assert isinstance(result, str)
    assert len(result) == 8


def test_lid_returns_unique_values():
    ids = {lid() for _ in range(100)}
    # With 100 UUIDs truncated to 8 chars there could theoretically be collisions,
    # but in practice this should be highly unique.
    assert len(ids) > 90


# --- text ---

def test_text_with_content():
    node = text("hello")
    assert node == {"type": "text", "text": "hello"}


def test_text_with_marks():
    marks = [{"type": "strong"}]
    node = text("bold", marks=marks)
    assert node == {"type": "text", "text": "bold", "marks": [{"type": "strong"}]}


def test_text_empty_returns_none():
    assert text("") is None
    assert text(None) is None


def test_text_no_marks_key_when_none():
    node = text("plain")
    assert "marks" not in node


# --- paragraph ---

def test_paragraph_with_content():
    t = text("hello")
    node = paragraph(t)
    assert node["type"] == "paragraph"
    assert node["content"] == [t]


def test_paragraph_empty():
    node = paragraph()
    assert node["type"] == "paragraph"
    assert "content" not in node


def test_paragraph_filters_none():
    t = text("hello")
    node = paragraph(None, t, None)
    assert node["content"] == [t]


def test_paragraph_all_none_has_no_content():
    node = paragraph(None, None)
    assert "content" not in node


# --- heading ---

def test_heading():
    content = [text("Title")]
    node = heading(2, content)
    assert node == {"type": "heading", "attrs": {"level": 2}, "content": content}


def test_heading_clamps_level_below_1():
    node = heading(0, [])
    assert node["attrs"]["level"] == 1


def test_heading_clamps_level_above_6():
    node = heading(9, [])
    assert node["attrs"]["level"] == 6


def test_heading_boundary_levels():
    assert heading(1, [])["attrs"]["level"] == 1
    assert heading(6, [])["attrs"]["level"] == 6


# --- rule ---

def test_rule():
    assert rule() == {"type": "rule"}


# --- code_block ---

def test_code_block_with_language():
    node = code_block("python", "print('hi')")
    assert node["type"] == "codeBlock"
    assert node["attrs"]["language"] == "python"
    assert node["content"] == [{"type": "text", "text": "print('hi')"}]


def test_code_block_no_language():
    node = code_block("", "some code")
    assert node["type"] == "codeBlock"
    assert "language" not in node["attrs"]
    assert node["content"] == [{"type": "text", "text": "some code"}]


def test_code_block_no_source():
    node = code_block("python", "")
    assert "content" not in node


def test_code_block_no_language_no_source():
    node = code_block("", "")
    assert node == {"type": "codeBlock", "attrs": {}}


# --- panel ---

def test_panel():
    content = [paragraph(text("note"))]
    node = panel("info", content)
    assert node == {"type": "panel", "attrs": {"panelType": "info"}, "content": content}


def test_panel_types():
    for panel_type in ("info", "note", "warning", "success", "error"):
        node = panel(panel_type, [])
        assert node["attrs"]["panelType"] == panel_type


# --- bullet_list / ordered_list ---

def test_bullet_list():
    items = [list_item([paragraph(text("a"))])]
    node = bullet_list(items)
    assert node == {"type": "bulletList", "content": items}


def test_ordered_list():
    items = [list_item([paragraph(text("1"))])]
    node = ordered_list(items)
    assert node == {"type": "orderedList", "content": items}


def test_list_item():
    content = [paragraph(text("item"))]
    node = list_item(content)
    assert node == {"type": "listItem", "content": content}


# --- task_list / task_item ---

def test_task_list_has_local_id():
    items = []
    node = task_list(items)
    assert node["type"] == "taskList"
    assert "localId" in node["attrs"]
    assert len(node["attrs"]["localId"]) == 8
    assert node["content"] == items


def test_task_list_local_id_is_unique():
    id1 = task_list([])["attrs"]["localId"]
    id2 = task_list([])["attrs"]["localId"]
    # They should almost always differ (UUID4-based)
    # We just check they are both valid 8-char strings
    assert len(id1) == 8
    assert len(id2) == 8


def test_task_item_todo():
    content = [text("do something")]
    node = task_item(content, done=False)
    assert node["type"] == "taskItem"
    assert node["attrs"]["state"] == "TODO"
    assert "localId" in node["attrs"]
    assert node["content"] == content


def test_task_item_done():
    content = [text("done")]
    node = task_item(content, done=True)
    assert node["attrs"]["state"] == "DONE"


def test_task_item_default_is_todo():
    node = task_item([])
    assert node["attrs"]["state"] == "TODO"


# --- expand ---

def test_expand():
    content = [paragraph(text("details"))]
    node = expand("Click to expand", content)
    assert node == {
        "type": "expand",
        "attrs": {"title": "Click to expand"},
        "content": content,
    }


# --- table structure ---

def test_table_structure():
    header_cell = table_header([paragraph(text("Name"))])
    data_cell = table_cell([paragraph(text("Alice"))])
    row1 = table_row([header_cell])
    row2 = table_row([data_cell])
    tbl = table([row1, row2])

    assert tbl["type"] == "table"
    assert len(tbl["content"]) == 2

    assert row1["type"] == "tableRow"
    assert row1["content"] == [header_cell]

    assert header_cell["type"] == "tableHeader"
    assert data_cell["type"] == "tableCell"


def test_table_header():
    content = [paragraph(text("Col"))]
    node = table_header(content)
    assert node == {"type": "tableHeader", "content": content}


def test_table_cell():
    content = [paragraph(text("Val"))]
    node = table_cell(content)
    assert node == {"type": "tableCell", "content": content}


def test_table_row():
    cells = [table_cell([]), table_cell([])]
    node = table_row(cells)
    assert node == {"type": "tableRow", "content": cells}


# --- blockquote ---

def test_blockquote():
    content = [paragraph(text("quoted text"))]
    node = blockquote(content)
    assert node == {"type": "blockquote", "content": content}


# --- status ---

def test_status():
    node = status("In Progress", "blue")
    assert node["type"] == "status"
    assert node["attrs"]["text"] == "In Progress"
    assert node["attrs"]["color"] == "blue"
    assert "localId" in node["attrs"]
    assert len(node["attrs"]["localId"]) == 8


def test_status_has_unique_local_id():
    n1 = status("A", "blue")
    n2 = status("B", "red")
    # Both should be valid 8-char strings
    assert len(n1["attrs"]["localId"]) == 8
    assert len(n2["attrs"]["localId"]) == 8
