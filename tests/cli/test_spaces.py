"""Tests for multi-space selection and recent tracking."""

from md_to_adf.cli.spaces import (
    get_named_spaces, get_recent_spaces, update_recent_spaces,
    resolve_space_key, format_space_picker,
)


def test_get_named_spaces_from_config():
    config = {
        "spaces": {
            "eng": {"key": "ENG", "name": "Engineering"},
            "product": {"key": "PROD", "name": "Product Docs"},
        }
    }
    result = get_named_spaces(config)
    assert len(result) == 2


def test_get_named_spaces_empty():
    assert get_named_spaces({}) == []
    assert get_named_spaces({"confluence": {}}) == []


def test_get_recent_spaces():
    config = {"recent_spaces": {"keys": ["ENG", "PROD", "MKT"]}}
    assert get_recent_spaces(config) == ["ENG", "PROD", "MKT"]


def test_get_recent_spaces_empty():
    assert get_recent_spaces({}) == []


def test_update_recent_spaces_adds_to_front():
    config = {"recent_spaces": {"keys": ["OLD"]}}
    update_recent_spaces(config, "NEW")
    assert config["recent_spaces"]["keys"][0] == "NEW"


def test_update_recent_spaces_deduplicates():
    config = {"recent_spaces": {"keys": ["A", "B", "C"]}}
    update_recent_spaces(config, "B")
    assert config["recent_spaces"]["keys"] == ["B", "A", "C"]


def test_update_recent_spaces_caps_at_5():
    config = {"recent_spaces": {"keys": ["A", "B", "C", "D", "E"]}}
    update_recent_spaces(config, "F")
    assert len(config["recent_spaces"]["keys"]) == 5
    assert "E" not in config["recent_spaces"]["keys"]


def test_update_recent_spaces_excludes_named():
    config = {
        "spaces": {"eng": {"key": "ENG", "name": "Engineering"}},
        "recent_spaces": {"keys": ["OLD"]},
    }
    update_recent_spaces(config, "ENG")
    assert "ENG" not in config["recent_spaces"]["keys"]


def test_update_recent_spaces_creates_section():
    config = {}
    update_recent_spaces(config, "NEW")
    assert config["recent_spaces"]["keys"] == ["NEW"]


def test_resolve_space_key_from_cli_flag():
    assert resolve_space_key({}, cli_space="CLI") == "CLI"


def test_resolve_space_key_from_default():
    config = {"confluence": {"space_key": "DEFAULT"}}
    assert resolve_space_key(config) == "DEFAULT"


def test_resolve_space_key_single_named():
    config = {"spaces": {"eng": {"key": "ENG", "name": "Engineering"}}}
    assert resolve_space_key(config) == "ENG"


def test_resolve_space_key_ambiguous_returns_none():
    config = {
        "spaces": {
            "eng": {"key": "ENG", "name": "Engineering"},
            "prod": {"key": "PROD", "name": "Product"},
        }
    }
    assert resolve_space_key(config) is None


def test_resolve_space_key_no_config():
    assert resolve_space_key({}) is None


def test_format_space_picker_named_and_recent():
    config = {
        "spaces": {"eng": {"key": "ENG", "name": "Engineering"}},
        "recent_spaces": {"keys": ["MKT", "ENG"]},  # ENG should be excluded (it's named)
    }
    choices, keys = format_space_picker(config)
    assert len(choices) == 2  # ENG (named) + MKT (recent, not named)
    assert keys == ["ENG", "MKT"]


def test_format_space_picker_empty():
    choices, keys = format_space_picker({})
    assert choices == []
    assert keys == []
