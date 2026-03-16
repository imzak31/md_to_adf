"""Tests for ADF validator."""

from md_to_adf.core.validator import validate
from md_to_adf.core.models import (
    text, paragraph, heading, panel, table, table_row, table_cell,
    task_list, task_item, expand,
)


def _doc(*content):
    return {"version": 1, "type": "doc", "content": list(content)}


def test_valid_doc():
    doc = _doc(paragraph(text("hello")))
    assert validate(doc) == []


def test_doc_wrong_version():
    doc = {"version": 2, "type": "doc", "content": []}
    errors = validate(doc)
    assert any("version must be 1" in e for e in errors)


def test_doc_no_content():
    doc = {"version": 1, "type": "doc"}
    errors = validate(doc)
    assert any("content must be array" in e for e in errors)


def test_table_inside_panel():
    t = table([table_row([table_cell([paragraph(text("x"))])])])
    p = panel("info", [t])
    doc = _doc(p)
    errors = validate(doc)
    assert any("TABLE INSIDE PANEL" in e for e in errors)


def test_paragraph_inside_task_item():
    ti = {"type": "taskItem", "attrs": {"localId": "abc", "state": "TODO"},
          "content": [paragraph(text("bad"))]}
    tl = task_list([ti])
    doc = _doc(tl)
    errors = validate(doc)
    assert any("PARAGRAPH INSIDE TASKITEM" in e for e in errors)


def test_task_item_missing_local_id():
    ti = {"type": "taskItem", "attrs": {"state": "TODO"}, "content": []}
    tl = task_list([ti])
    doc = _doc(tl)
    errors = validate(doc)
    assert any("missing localId" in e for e in errors)


def test_task_list_missing_local_id():
    tl = {"type": "taskList", "attrs": {}, "content": []}
    doc = _doc(tl)
    errors = validate(doc)
    assert any("missing localId" in e for e in errors)


def test_empty_text_node():
    doc = _doc(paragraph({"type": "text", "text": ""}))
    errors = validate(doc)
    assert any("empty text" in e for e in errors)


def test_heading_invalid_level():
    h = {"type": "heading", "attrs": {"level": 0}, "content": []}
    doc = _doc(h)
    errors = validate(doc)
    assert any("level must be 1-6" in e for e in errors)


def test_panel_invalid_type():
    p = {"type": "panel", "attrs": {"panelType": "invalid"}, "content": []}
    doc = _doc(p)
    errors = validate(doc)
    assert any("invalid panelType" in e for e in errors)


def test_expand_no_content():
    e = {"type": "expand", "attrs": {"title": "test"}}
    doc = _doc(e)
    errors = validate(doc)
    assert any("expand has no content" in err for err in errors)


def test_valid_panel_types():
    for pt in ["info", "note", "tip", "warning", "error", "success", "custom"]:
        p = panel(pt, [paragraph(text("ok"))])
        doc = _doc(p)
        assert validate(doc) == [], f"Panel type '{pt}' should be valid"


def test_backward_compat_convert():
    import warnings
    from md_to_adf import markdown_to_adf
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        doc = markdown_to_adf("# Test")
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
    assert doc["type"] == "doc"


def test_backward_compat_validate():
    import warnings
    from md_to_adf import validate_adf
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        errors = validate_adf({"version": 1, "type": "doc", "content": []})
        assert len(w) == 1
    assert errors == []
