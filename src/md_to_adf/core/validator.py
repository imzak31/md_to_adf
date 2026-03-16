"""ADF document validator — zero external dependencies."""

_PANEL_ALLOWED = {"paragraph", "heading", "bulletList", "orderedList", "blockCard",
                  "mediaGroup", "mediaSingle", "codeBlock", "taskList", "rule",
                  "decisionList", "extension"}

_STATUS_COLORS = {"neutral", "purple", "blue", "red", "yellow", "green"}


def validate(doc):
    """
    Validate an ADF document dict. Returns list of error strings.
    Empty list = valid.
    """
    errors = []
    _validate_node(doc, "root", errors)
    return errors


def _validate_node(node, path, errors):
    if not isinstance(node, dict):
        return

    t = node.get("type")

    # Doc root checks
    if t == "doc":
        if node.get("version") != 1:
            errors.append(f"{path}: doc version must be 1")
        if not isinstance(node.get("content"), list):
            errors.append(f"{path}: doc content must be array")

    # Panel: content restrictions + type validation
    if t == "panel":
        pt = node.get("attrs", {}).get("panelType")
        valid_types = {"info", "note", "tip", "warning", "error", "success", "custom"}
        if pt not in valid_types:
            errors.append(f"{path}: invalid panelType '{pt}'")
        for ci, child in enumerate(node.get("content", [])):
            if isinstance(child, dict):
                ct = child.get("type")
                if ct == "table":
                    errors.append(f"{path}.content[{ci}]: TABLE INSIDE PANEL — not allowed")
                if ct and ct not in _PANEL_ALLOWED:
                    errors.append(f"{path}.content[{ci}]: {ct} not allowed inside panel")

    # No paragraphs inside taskItems
    if t == "taskItem":
        for ci, child in enumerate(node.get("content", [])):
            if isinstance(child, dict) and child.get("type") == "paragraph":
                errors.append(f"{path}.content[{ci}]: PARAGRAPH INSIDE TASKITEM — use inline nodes")
        attrs = node.get("attrs", {})
        if "localId" not in attrs:
            errors.append(f"{path}: taskItem missing localId")
        if "state" not in attrs:
            errors.append(f"{path}: taskItem missing state")

    # taskList needs localId
    if t == "taskList":
        if "localId" not in node.get("attrs", {}):
            errors.append(f"{path}: taskList missing localId")

    # Text nodes must have content
    if t == "text":
        if not node.get("text"):
            errors.append(f"{path}: empty text node")

    # Heading level 1-6
    if t == "heading":
        level = node.get("attrs", {}).get("level")
        if not level or level < 1 or level > 6:
            errors.append(f"{path}: heading level must be 1-6, got {level}")

    # Status node validation
    if t == "status":
        attrs = node.get("attrs", {})
        if not attrs.get("text"):
            errors.append(f"{path}: status missing text")
        if attrs.get("color") not in _STATUS_COLORS:
            errors.append(f"{path}: invalid status color '{attrs.get('color')}'")

    # Expand must have content
    if t == "expand":
        if not node.get("content"):
            errors.append(f"{path}: expand has no content")

    # Recurse
    for key, val in node.items():
        if isinstance(val, list):
            for i, item in enumerate(val):
                _validate_node(item, f"{path}.{key}[{i}]", errors)
        elif isinstance(val, dict) and key != "attrs":
            _validate_node(val, f"{path}.{key}", errors)
