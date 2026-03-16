"""Tests for inline markdown parser."""

from md_to_adf.core.inline import parse_inline


def test_plain_text():
    nodes = parse_inline("hello world")
    assert len(nodes) == 1
    assert nodes[0] == {"type": "text", "text": "hello world"}


def test_empty_string():
    assert parse_inline("") == []


def test_bold_double_star():
    nodes = parse_inline("some **bold** text")
    assert len(nodes) == 3
    assert nodes[1]["marks"] == [{"type": "strong"}]
    assert nodes[1]["text"] == "bold"


def test_bold_double_underscore():
    nodes = parse_inline("some __bold__ text")
    assert nodes[1]["marks"] == [{"type": "strong"}]


def test_italic_star():
    nodes = parse_inline("some *italic* text")
    assert nodes[1]["marks"] == [{"type": "em"}]
    assert nodes[1]["text"] == "italic"


def test_italic_underscore():
    nodes = parse_inline("some _italic_ text")
    assert nodes[1]["marks"] == [{"type": "em"}]


def test_bold_italic():
    nodes = parse_inline("***both***")
    assert {"type": "strong"} in nodes[0]["marks"]
    assert {"type": "em"} in nodes[0]["marks"]


def test_strikethrough():
    nodes = parse_inline("some ~~struck~~ text")
    assert nodes[1]["marks"] == [{"type": "strike"}]
    assert nodes[1]["text"] == "struck"


def test_inline_code():
    nodes = parse_inline("some `code` text")
    assert nodes[1]["marks"] == [{"type": "code"}]
    assert nodes[1]["text"] == "code"


def test_link():
    nodes = parse_inline("click [here](https://example.com)")
    link_node = nodes[1]
    assert link_node["text"] == "here"
    assert {"type": "link", "attrs": {"href": "https://example.com"}} in link_node["marks"]


def test_image_becomes_link_text():
    nodes = parse_inline("an ![alt text](https://img.png) image")
    img_node = nodes[1]
    assert img_node["text"] == "[alt text]"
    assert {"type": "link", "attrs": {"href": "https://img.png"}} in img_node["marks"]


def test_nested_bold_in_italic():
    nodes = parse_inline("*this is **nested** italic*")
    found_nested = False
    for n in nodes:
        if n.get("text") == "nested":
            assert {"type": "em"} in n["marks"]
            assert {"type": "strong"} in n["marks"]
            found_nested = True
    assert found_nested


def test_multiple_inline_elements():
    nodes = parse_inline("**bold** and *italic* and `code`")
    texts = [n["text"] for n in nodes]
    assert "bold" in texts
    assert "italic" in texts
    assert "code" in texts
