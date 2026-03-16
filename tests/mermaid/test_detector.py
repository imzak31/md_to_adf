"""Tests for mermaid block detection in ADF."""

from md_to_adf.core.parser import convert
from md_to_adf.mermaid.detector import find_mermaid_blocks


def test_find_mermaid_blocks():
    md = "```mermaid\ngraph TD\nA-->B\n```"
    doc = convert(md)
    blocks = find_mermaid_blocks(doc)
    assert len(blocks) == 1
    assert blocks[0]["source"] == "graph TD\nA-->B"


def test_no_mermaid_blocks():
    md = "```python\nprint('hi')\n```"
    doc = convert(md)
    blocks = find_mermaid_blocks(doc)
    assert len(blocks) == 0


def test_multiple_mermaid_blocks():
    md = "```mermaid\ngraph TD\nA-->B\n```\n\nSome text\n\n```mermaid\nsequenceDiagram\nA->>B: Hi\n```"
    doc = convert(md)
    blocks = find_mermaid_blocks(doc)
    assert len(blocks) == 2
