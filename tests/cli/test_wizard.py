"""Tests for setup wizard."""

from md_to_adf.cli.wizard import _prompt, _prompt_choice, _mask_token


def test_mask_token():
    assert _mask_token("abcdefghij") == "abcd******"
    assert _mask_token("abc") == "***"
    assert _mask_token("") == ""


def test_prompt_with_default(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "")
    result = _prompt("Domain", default="test.atlassian.net")
    assert result == "test.atlassian.net"


def test_prompt_with_input(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "custom.atlassian.net")
    result = _prompt("Domain")
    assert result == "custom.atlassian.net"


def test_prompt_choice(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "2")
    result = _prompt_choice("Pick one", ["alpha", "beta", "gamma"])
    assert result == "beta"


def test_prompt_choice_default(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "")
    result = _prompt_choice("Pick one", ["alpha", "beta"], default_index=0)
    assert result == "alpha"
