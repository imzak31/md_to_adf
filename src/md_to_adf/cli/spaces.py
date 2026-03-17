"""Multi-space selection: named spaces, recent tracking, interactive picker."""

_MAX_RECENT = 5


def get_named_spaces(config):
    """Return list of named space dicts from config [spaces.*] sections."""
    spaces_section = config.get("spaces", {})
    result = []
    for name, info in spaces_section.items():
        if isinstance(info, dict) and "key" in info:
            result.append(info)
    return result


def get_recent_spaces(config):
    """Return list of recent space keys."""
    return config.get("recent_spaces", {}).get("keys", [])


def update_recent_spaces(config, space_key):
    """Push space_key to front of recent list, dedup, cap at 5, exclude named."""
    named_keys = {s["key"] for s in get_named_spaces(config)}
    if space_key in named_keys:
        return

    if "recent_spaces" not in config:
        config["recent_spaces"] = {"keys": []}

    recents = config["recent_spaces"]["keys"]
    if space_key in recents:
        recents.remove(space_key)
    recents.insert(0, space_key)
    config["recent_spaces"]["keys"] = recents[:_MAX_RECENT]


def resolve_space_key(config, cli_space=None):
    """Resolve space key: CLI flag > single named > default config > None.
    Returns the space key string, or None if ambiguous (caller should prompt).
    """
    if cli_space:
        return cli_space

    default = config.get("confluence", {}).get("space_key")
    named = get_named_spaces(config)
    recents = get_recent_spaces(config)

    # Unambiguous: only one option
    if len(named) == 1 and not recents and not default:
        return named[0]["key"]
    if not named and not recents and default:
        return default

    # Ambiguous — return None so caller can prompt
    if named or recents:
        return None

    return default or None


def format_space_picker(config):
    """Build the space picker menu. Returns (choices, keys) for display."""
    named = get_named_spaces(config)
    recents = get_recent_spaces(config)
    named_keys = {s["key"] for s in named}

    choices = []
    keys = []

    for s in named:
        choices.append(f"{s['key']} — {s.get('name', '')}")
        keys.append(s["key"])

    for rk in recents:
        if rk not in named_keys:
            choices.append(rk)
            keys.append(rk)

    return choices, keys
