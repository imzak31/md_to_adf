"""ADF node builder helpers."""

import uuid


def lid():
    """Generate a short local ID."""
    return str(uuid.uuid4())[:8]


def text(t, marks=None):
    """Create an ADF text node. Returns None if t is empty."""
    if not t:
        return None
    node = {"type": "text", "text": t}
    if marks:
        node["marks"] = marks
    return node


def paragraph(*content):
    filtered = [n for n in content if n is not None]
    node = {"type": "paragraph"}
    if filtered:
        node["content"] = filtered
    return node


def heading(level, content):
    return {"type": "heading", "attrs": {"level": min(max(level, 1), 6)}, "content": content}


def rule():
    return {"type": "rule"}


def code_block(language, source):
    node = {"type": "codeBlock", "attrs": {}}
    if language:
        node["attrs"]["language"] = language
    if source:
        node["content"] = [{"type": "text", "text": source}]
    return node


def panel(panel_type, content):
    return {"type": "panel", "attrs": {"panelType": panel_type}, "content": content}


def bullet_list(items):
    return {"type": "bulletList", "content": items}


def ordered_list(items):
    return {"type": "orderedList", "content": items}


def list_item(content):
    return {"type": "listItem", "content": content}


def task_list(items):
    return {"type": "taskList", "attrs": {"localId": lid()}, "content": items}


def task_item(content, done=False):
    return {
        "type": "taskItem",
        "attrs": {"localId": lid(), "state": "DONE" if done else "TODO"},
        "content": content,
    }


def expand(title, content):
    return {"type": "expand", "attrs": {"title": title}, "content": content}


def table(rows):
    return {"type": "table", "content": rows}


def table_row(cells):
    return {"type": "tableRow", "content": cells}


def table_header(content):
    return {"type": "tableHeader", "content": content}


def table_cell(content):
    return {"type": "tableCell", "content": content}


def blockquote(content):
    return {"type": "blockquote", "content": content}


def status(label, color):
    return {"type": "status", "attrs": {"text": label, "color": color, "localId": lid()}}
