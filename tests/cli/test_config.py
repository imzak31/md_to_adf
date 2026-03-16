"""Tests for config module."""

import os
from md_to_adf.cli.config import load_config, save_config, get_config_value, DEFAULT_CONFIG


def test_default_config():
    assert "confluence" in DEFAULT_CONFIG
    assert "mermaid" in DEFAULT_CONFIG


def test_save_and_load_config(tmp_path):
    config_path = tmp_path / "config.toml"
    config = {
        "confluence": {
            "domain": "test.atlassian.net",
            "email": "test@example.com",
            "token": "secret",
            "space_key": "TS",
            "auth_method": "token",
        },
        "mermaid": {
            "strategy": "auto",
            "format": "png",
            "theme": "default",
        },
    }
    save_config(config, config_path)
    loaded = load_config(config_path)
    assert loaded["confluence"]["domain"] == "test.atlassian.net"
    assert loaded["confluence"]["token"] == "secret"
    assert loaded["mermaid"]["strategy"] == "auto"


def test_load_nonexistent_returns_defaults(tmp_path):
    config_path = tmp_path / "nonexistent.toml"
    config = load_config(config_path)
    assert config == DEFAULT_CONFIG


def test_config_file_permissions(tmp_path):
    config_path = tmp_path / "config.toml"
    save_config(DEFAULT_CONFIG, config_path)
    st = os.stat(config_path)
    assert oct(st.st_mode)[-3:] == "600"


def test_env_var_override(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config = {
        "confluence": {
            "domain": "file.atlassian.net",
            "email": "file@example.com",
            "token": "file-token",
            "space_key": "FK",
            "auth_method": "token",
        },
        "mermaid": DEFAULT_CONFIG["mermaid"],
    }
    save_config(config, config_path)

    monkeypatch.setenv("MD_TO_ADF_DOMAIN", "env.atlassian.net")
    monkeypatch.setenv("MD_TO_ADF_EMAIL", "env@example.com")

    loaded = load_config(config_path)
    assert get_config_value(loaded, "confluence", "domain") == "env.atlassian.net"
    assert get_config_value(loaded, "confluence", "email") == "env@example.com"
    assert get_config_value(loaded, "confluence", "token") == "file-token"


def test_get_config_value_with_cli_override():
    config = {"confluence": {"domain": "file.atlassian.net"}}
    result = get_config_value(config, "confluence", "domain", cli_value="cli.atlassian.net")
    assert result == "cli.atlassian.net"


def test_get_config_value_returns_none_when_missing():
    config = {"confluence": {}}
    result = get_config_value(config, "confluence", "token")
    assert result is None
