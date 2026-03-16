"""Inline markdown parser — converts inline markdown to ADF text nodes with marks."""

import re
from md_to_adf.core.models import text, paragraph

_INLINE_PATTERNS = [
    (re.compile(r'!\[([^\]]*)\]\(([^)]+)\)'), 'image'),
    (re.compile(r'\[([^\]]+)\]\(([^)]+)\)'), 'link'),
    (re.compile(r'\*\*\*(.+?)\*\*\*|___(.+?)___'), 'bold_italic'),
    (re.compile(r'\*\*(.+?)\*\*|__(.+?)__'), 'bold'),
    (re.compile(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)|(?<!\w)_(.+?)_(?!\w)'), 'italic'),
    (re.compile(r'~~(.+?)~~'), 'strike'),
    (re.compile(r'`([^`]+)`'), 'code'),
]


def parse_inline(text_str):
    """Parse inline markdown and return list of ADF inline nodes."""
    if not text_str:
        return []
    nodes = []
    _parse_inline_recursive(text_str, [], nodes)
    return [n for n in nodes if n is not None]


def inline_to_paragraph(text_str):
    """Convert inline markdown text to a paragraph node."""
    nodes = parse_inline(text_str)
    if not nodes:
        return paragraph()
    return paragraph(*nodes)


def _parse_inline_recursive(text_str, inherited_marks, out_nodes):
    if not text_str:
        return

    best_match = None
    best_start = len(text_str)
    best_pattern_type = None

    for pattern, ptype in _INLINE_PATTERNS:
        m = pattern.search(text_str)
        if m and m.start() < best_start:
            best_match = m
            best_start = m.start()
            best_pattern_type = ptype

    if best_match is None:
        node = text(text_str, inherited_marks if inherited_marks else None)
        if node:
            out_nodes.append(node)
        return

    before = text_str[:best_start]
    if before:
        node = text(before, inherited_marks if inherited_marks else None)
        if node:
            out_nodes.append(node)

    if best_pattern_type == 'code':
        inner = best_match.group(1)
        marks = [{"type": "code"}]
        node = text(inner, marks)
        if node:
            out_nodes.append(node)
    elif best_pattern_type == 'bold':
        inner = best_match.group(1) or best_match.group(2)
        _parse_inline_recursive(inner, inherited_marks + [{"type": "strong"}], out_nodes)
    elif best_pattern_type == 'italic':
        inner = best_match.group(1) or best_match.group(2)
        _parse_inline_recursive(inner, inherited_marks + [{"type": "em"}], out_nodes)
    elif best_pattern_type == 'bold_italic':
        inner = best_match.group(1) or best_match.group(2)
        _parse_inline_recursive(inner, inherited_marks + [{"type": "strong"}, {"type": "em"}], out_nodes)
    elif best_pattern_type == 'strike':
        inner = best_match.group(1)
        _parse_inline_recursive(inner, inherited_marks + [{"type": "strike"}], out_nodes)
    elif best_pattern_type == 'link':
        link_text = best_match.group(1)
        link_url = best_match.group(2)
        new_marks = inherited_marks + [{"type": "link", "attrs": {"href": link_url}}]
        node = text(link_text, new_marks)
        if node:
            out_nodes.append(node)
    elif best_pattern_type == 'image':
        alt = best_match.group(1) or "image"
        url = best_match.group(2)
        marks = inherited_marks + [{"type": "link", "attrs": {"href": url}}]
        node = text(f"[{alt}]", marks)
        if node:
            out_nodes.append(node)

    after = text_str[best_match.end():]
    if after:
        _parse_inline_recursive(after, inherited_marks, out_nodes)
