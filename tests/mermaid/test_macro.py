"""Tests for mermaid macro ADF node generation."""

from md_to_adf.mermaid.macro import mermaid_to_macro_node
from md_to_adf.mermaid import process_mermaid_blocks
from md_to_adf.core.parser import convert


def test_macro_node_structure():
    node = mermaid_to_macro_node("graph TD\nA-->B")
    assert node["type"] == "bodiedExtension"
    assert "extensionKey" in node["attrs"]


def test_macro_node_contains_source():
    source = "graph TD\nA-->B"
    node = mermaid_to_macro_node(source)
    body_text = node["content"][0]["content"][0]["text"]
    assert source in body_text


def test_process_mermaid_auto_replaces_with_macro():
    md = "```mermaid\ngraph TD\nA-->B\n```"
    doc = convert(md)
    doc = process_mermaid_blocks(doc, strategy="auto")
    assert doc["content"][0]["type"] == "bodiedExtension"


def test_process_mermaid_code_strategy_noop():
    md = "```mermaid\ngraph TD\nA-->B\n```"
    doc = convert(md)
    doc = process_mermaid_blocks(doc, strategy="code")
    assert doc["content"][0]["type"] == "codeBlock"
    assert doc["content"][0]["attrs"]["language"] == "mermaid"
