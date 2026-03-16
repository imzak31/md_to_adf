"""Configuration management — TOML file + env var layering."""

import os
import stat
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

import tomli_w

DEFAULT_CONFIG_DIR = Path.home() / ".md-to-adf"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.toml"

DEFAULT_CONFIG = {
    "confluence": {
        "domain": "",
        "email": "",
        "token": "",
        "space_key": "",
        "auth_method": "token",
    },
    "mermaid": {
        "strategy": "auto",
        "format": "png",
        "theme": "default",
    },
}

_ENV_MAP = {
    ("confluence", "domain"): "MD_TO_ADF_DOMAIN",
    ("confluence", "email"): "MD_TO_ADF_EMAIL",
    ("confluence", "token"): "MD_TO_ADF_TOKEN",
    ("confluence", "space_key"): "MD_TO_ADF_SPACE",
    ("mermaid", "strategy"): "MD_TO_ADF_MERMAID",
}


def load_config(config_path=None):
    """Load config from TOML file. Returns DEFAULT_CONFIG if file doesn't exist."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        return dict(DEFAULT_CONFIG)


def save_config(config, config_path=None):
    """Save config to TOML file with restrictive permissions (600)."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        tomli_w.dump(config, f)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def get_config_value(config, section, key, cli_value=None):
    """Get a config value with priority: CLI flag > env var > config file > None."""
    if cli_value is not None:
        return cli_value
    env_key = _ENV_MAP.get((section, key))
    if env_key:
        env_val = os.environ.get(env_key)
        if env_val:
            return env_val
    return config.get(section, {}).get(key) or None
