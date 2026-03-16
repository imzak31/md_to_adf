"""Block-level markdown parser — converts markdown text to ADF document."""

import re

from md_to_adf.core.models import (
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
    paragraph,
)
from md_to_adf.core.inline import parse_inline, inline_to_paragraph


def convert(md_text):
    """
    Convert a markdown string to an ADF document dict.

    Returns: {"version": 1, "type": "doc", "content": [...]}
    """
    lines = md_text.split('\n')
    blocks = _parse_blocks(lines)
    return {"version": 1, "type": "doc", "content": blocks}


def _parse_blocks(lines):
    """Parse lines into a list of ADF block nodes."""
    nodes = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # ── Empty line → skip
        if not line.strip():
            i += 1
            continue

        # ── HTML <details> → expand
        if line.strip().lower().startswith('<details>') or line.strip().lower().startswith('<details '):
            block, i = _parse_details(lines, i)
            if block:
                nodes.append(block)
            continue

        # ── Closing HTML tags we might encounter → skip
        if re.match(r'^\s*</(details|summary|div)>\s*$', line.strip(), re.I):
            i += 1
            continue

        # ── Horizontal rule
        if re.match(r'^(\s*[-*_]\s*){3,}$', line):
            nodes.append(rule())
            i += 1
            continue

        # ── Heading
        m = re.match(r'^(#{1,6})\s+(.+?)(?:\s+#+\s*)?$', line)
        if m:
            level = len(m.group(1))
            content = parse_inline(m.group(2).strip())
            nodes.append(heading(level, content))
            i += 1
            continue

        # ── Code block (fenced)
        m = re.match(r'^```(\w*)\s*$', line)
        if m:
            lang = m.group(1) or ""
            block, i = _parse_code_block(lines, i, lang)
            nodes.append(block)
            continue

        # ── Table
        if '|' in line and i + 1 < len(lines) and re.match(r'^[\s|:-]+$', lines[i + 1]):
            block, i = _parse_table(lines, i)
            if block:
                nodes.append(block)
            continue

        # ── Blockquote → panel with type detection
        if line.startswith('>'):
            block_nodes, i = _parse_blockquote(lines, i)
            nodes.extend(block_nodes)
            continue

        # ── Task list (- [ ] or - [x])
        if re.match(r'^[\s]*[-*]\s+\[([ xX])\]\s', line):
            block, i = _parse_task_list(lines, i)
            nodes.append(block)
            continue

        # ── Unordered list
        if re.match(r'^[\s]*[-*+]\s+', line):
            block, i = _parse_list(lines, i, ordered=False)
            nodes.append(block)
            continue

        # ── Ordered list
        if re.match(r'^[\s]*\d+[.)]\s+', line):
            block, i = _parse_list(lines, i, ordered=True)
            nodes.append(block)
            continue

        # ── Paragraph (default)
        block, i = _parse_paragraph(lines, i)
        if block:
            nodes.append(block)

    return nodes


def _parse_code_block(lines, start, lang):
    """Parse a fenced code block starting at `start`."""
    i = start + 1
    code_lines = []
    while i < len(lines):
        if lines[i].strip() == '```':
            i += 1
            break
        code_lines.append(lines[i])
        i += 1
    source = '\n'.join(code_lines)
    return code_block(lang, source), i


def _parse_table(lines, start):
    """Parse a markdown table starting at `start`."""
    rows = []

    # Header row
    header_cells = _split_table_row(lines[start])
    header = table_row([table_header([inline_to_paragraph(c)]) for c in header_cells])
    rows.append(header)

    # Skip separator row
    i = start + 2

    # Data rows
    while i < len(lines) and '|' in lines[i] and lines[i].strip():
        cells = _split_table_row(lines[i])
        # Pad/trim to match header length
        while len(cells) < len(header_cells):
            cells.append("")
        cells = cells[:len(header_cells)]
        row = table_row([table_cell([inline_to_paragraph(c)]) for c in cells])
        rows.append(row)
        i += 1

    return table(rows), i


def _split_table_row(line):
    """Split a markdown table row into cell strings."""
    line = line.strip()
    if line.startswith('|'):
        line = line[1:]
    if line.endswith('|'):
        line = line[:-1]
    return [cell.strip() for cell in line.split('|')]


def _parse_blockquote(lines, start):
    """
    Parse blockquote lines. Detects panel type from first line keywords.

    Panel type detection:
      > **Note:** ...      → note panel
      > **Warning:** ...   → warning panel
      > **Tip:** ...       → tip panel
      > **Info:** ...      → info panel
      > **Error:** ...     → error panel
      > **Success:** ...   → success panel
      > **Purpose:** ...   → info panel
      > (default)          → info panel (or blockquote if no keyword)

    Returns (nodes_list, next_index) — may return multiple nodes if tables
    need to be hoisted out of panels.
    """
    bq_lines = []
    i = start
    while i < len(lines):
        raw = lines[i]
        if raw.startswith('>'):
            if raw.startswith('> '):
                bq_lines.append(raw[2:])
            else:
                bq_lines.append(raw[1:])
            i += 1
        elif raw.strip() == '' and bq_lines:
            # Blank line inside a blockquote — only continue if next non-blank
            # line is a continuation (starts with >) AND is not a new panel-type
            # blockquote (which should be its own block)
            if i + 1 < len(lines) and lines[i + 1].startswith('>'):
                # Check if the next > line starts a new panel keyword
                next_content = lines[i + 1].lstrip('>').strip()
                m = re.match(r'^\*\*(\w+)(?::?\s*)\*\*', next_content, re.I)
                if m and m.group(1).lower() in ('note', 'warning', 'tip', 'info',
                        'error', 'success', 'purpose', 'important', 'caution'):
                    # New panel-type blockquote — stop here
                    break
                bq_lines.append('')
                i += 1
            else:
                break
        else:
            break

    # Detect panel type from first non-empty line
    panel_type = None
    first_line = ''
    for bl in bq_lines:
        if bl.strip():
            first_line = bl.strip()
            break

    type_map = {
        'note': 'note', 'warning': 'warning', 'tip': 'tip',
        'info': 'info', 'error': 'error', 'success': 'success',
        'purpose': 'info', 'important': 'warning', 'caution': 'warning',
    }

    m = re.match(r'^\*\*(\w+)(?::?\s*)\*\*', first_line, re.I)
    if m:
        keyword = m.group(1).lower()
        if keyword in type_map:
            panel_type = type_map[keyword]

    # Parse inner content
    inner_blocks = _parse_blocks(bq_lines)

    if not inner_blocks:
        return [], i

    if panel_type:
        # ADF LESSON: No tables inside panels — hoist them out
        panel_content = []
        hoisted = []
        for block in inner_blocks:
            if block.get("type") == "table":
                hoisted.append(block)
            else:
                panel_content.append(block)

        result = []
        if panel_content:
            result.append(panel(panel_type, panel_content))
        result.extend(hoisted)
        return result, i
    else:
        # Plain blockquote
        # Filter to allowed blockquote content
        allowed = {"paragraph", "orderedList", "bulletList", "codeBlock", "mediaSingle", "mediaGroup"}
        bq_content = []
        extra = []
        for block in inner_blocks:
            if block.get("type") in allowed:
                bq_content.append(block)
            else:
                extra.append(block)
        result = []
        if bq_content:
            result.append(blockquote(bq_content))
        result.extend(extra)
        return result, i


def _parse_list(lines, start, ordered=False):
    """Parse a bullet or ordered list, handling nesting via indentation."""
    items = []
    i = start
    if ordered:
        item_pattern = re.compile(r'^(\s*)\d+[.)]\s+(.*)')
    else:
        item_pattern = re.compile(r'^(\s*)[-*+]\s+(.*)')

    base_indent = len(re.match(r'^(\s*)', lines[start]).group(1))

    while i < len(lines):
        line = lines[i]

        # Empty line might end list or be a gap between items
        if not line.strip():
            # Check if list continues after blank line
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                next_m = item_pattern.match(next_line)
                if next_m:
                    i += 1
                    continue
                # Check for continuation with indented content
                next_indent = len(re.match(r'^(\s*)', next_line).group(1))
                if next_indent > base_indent and next_line.strip():
                    i += 1
                    continue
            break

        m = item_pattern.match(line)
        if m:
            indent = len(m.group(1))
            if indent < base_indent:
                break
            if indent > base_indent:
                # Nested list — let parent handle it
                break

            item_text = m.group(2)
            i += 1

            # Collect continuation lines (indented more than the item marker)
            sub_lines = []
            item_marker_width = base_indent + len(re.match(r'^(\s*(?:[-*+]|\d+[.)])\s+)', line).group(1)) - base_indent
            while i < len(lines):
                if not lines[i].strip():
                    # Blank line — check if list continues
                    if i + 1 < len(lines):
                        peek = lines[i + 1]
                        peek_indent = len(re.match(r'^(\s*)', peek).group(1))
                        if peek_indent >= base_indent + 2 or item_pattern.match(peek):
                            sub_lines.append('')
                            i += 1
                            continue
                    break
                curr_indent = len(re.match(r'^(\s*)', lines[i]).group(1))
                if curr_indent >= base_indent + 2:
                    sub_lines.append(lines[i][min(base_indent + 2, len(lines[i])):])
                    i += 1
                elif item_pattern.match(lines[i]) and curr_indent == base_indent:
                    break
                else:
                    break

            # Build item content
            item_content = [inline_to_paragraph(item_text)]

            # Parse sub-content (nested lists, paragraphs, etc.)
            if sub_lines:
                sub_blocks = _parse_blocks(sub_lines)
                item_content.extend(sub_blocks)

            items.append(list_item(item_content))
        else:
            break

    if ordered:
        return ordered_list(items), i
    else:
        return bullet_list(items), i


def _parse_task_list(lines, start):
    """Parse a task list (- [ ] or - [x] items)."""
    items = []
    i = start
    pattern = re.compile(r'^[\s]*[-*]\s+\[([ xX])\]\s+(.*)')

    while i < len(lines):
        m = pattern.match(lines[i])
        if not m:
            break
        done = m.group(1).lower() == 'x'
        text_content = m.group(2)
        # ADF LESSON: taskItem content must be inline nodes, NOT paragraphs
        inline_nodes = parse_inline(text_content)
        items.append(task_item(inline_nodes, done=done))
        i += 1

    return task_list(items), i


def _parse_paragraph(lines, start):
    """Parse a paragraph (one or more non-blank lines until a block boundary)."""
    para_lines = []
    i = start

    while i < len(lines):
        line = lines[i]

        # Stop on blank line
        if not line.strip():
            break

        # Stop on block-level element
        if re.match(r'^#{1,6}\s', line):
            break
        if re.match(r'^```', line):
            break
        if re.match(r'^(\s*[-*_]\s*){3,}$', line):
            break
        if re.match(r'^[\s]*[-*+]\s+', line) and not para_lines:
            break
        if re.match(r'^[\s]*\d+[.)]\s+', line) and not para_lines:
            break
        if line.startswith('>') and not para_lines:
            break
        if '|' in line and i + 1 < len(lines) and re.match(r'^[\s|:-]+$', lines[i + 1]):
            break
        if line.strip().lower().startswith('<details'):
            break

        para_lines.append(line)
        i += 1

    if not para_lines:
        # Safety: advance past the line to avoid infinite loop.
        # This branch only triggers if a line isn't matched by any block pattern
        # in _parse_blocks (should not happen in practice).
        return None, i + 1

    text = ' '.join(para_lines)
    return inline_to_paragraph(text), i


def _parse_details(lines, start):
    """Parse HTML <details><summary>Title</summary>...</details> into ADF expand."""
    i = start
    title = ""

    # Look for summary on same line or next lines
    first_line = lines[i].strip()
    # Check for <details><summary>Title</summary> on one line
    m = re.match(r'<details[^>]*>\s*<summary>(.*?)</summary>', first_line, re.I)
    if m:
        title = m.group(1).strip()
        i += 1
    else:
        i += 1
        # Look for <summary> tag
        while i < len(lines):
            line = lines[i].strip()
            m = re.match(r'<summary>(.*?)</summary>', line, re.I)
            if m:
                title = m.group(1).strip()
                i += 1
                break
            elif line and not line.startswith('<'):
                # No summary tag, use first content line as title
                title = line
                i += 1
                break
            else:
                i += 1
                break

    # Collect content until </details>
    content_lines = []
    while i < len(lines):
        line = lines[i].strip()
        if line.lower() == '</details>':
            i += 1
            break
        content_lines.append(lines[i])
        i += 1

    # Parse inner content
    inner_blocks = _parse_blocks(content_lines)

    if not inner_blocks:
        inner_blocks = [paragraph()]

    return expand(title, inner_blocks), i
