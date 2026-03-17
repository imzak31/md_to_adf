"""Interactive setup wizard for md-to-adf."""

import getpass
import sys

from md_to_adf.cli.config import save_config, DEFAULT_CONFIG, DEFAULT_CONFIG_PATH
from md_to_adf.cli.errors import MdToAdfError


def _prompt(label, default=None, secret=False):
    """Prompt for input with optional default."""
    suffix = f" [{default}]" if default else ""
    prompt_str = f"  {label}{suffix}: "
    if secret:
        value = getpass.getpass(prompt_str)
    else:
        value = input(prompt_str)
    return value.strip() or default or ""


def _prompt_choice(label, choices, default_index=None):
    """Prompt user to pick from a numbered list."""
    print(f"\n  {label}")
    for i, choice in enumerate(choices):
        marker = " (*)" if i == default_index else ""
        print(f"    {i + 1}) {choice}{marker}")
    while True:
        raw = input(f"  Choice [1-{len(choices)}]: ").strip()
        if not raw and default_index is not None:
            return choices[default_index]
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            pass
        print(f"  Please enter a number between 1 and {len(choices)}")


def _mask_token(token):
    """Mask a token for display."""
    if len(token) <= 4:
        return "*" * len(token)
    return token[:4] + "*" * (len(token) - 4)


def run_wizard(token_mode=False, oauth_mode=False):
    """Run the interactive setup wizard."""
    print("\nWelcome to md-to-adf! Let's get you set up.\n")

    config = dict(DEFAULT_CONFIG)
    config["confluence"] = dict(config["confluence"])
    config["mermaid"] = dict(config["mermaid"])

    # Auth method
    if token_mode:
        auth_method = "token"
    elif oauth_mode:
        auth_method = "oauth"
    else:
        choice = _prompt_choice(
            "How would you like to authenticate with Confluence?",
            ["API Token (quick — you'll need your email + token)",
             "OAuth (browser-based — no token management)"],
            default_index=0,
        )
        auth_method = "token" if "Token" in choice else "oauth"

    config["confluence"]["auth_method"] = auth_method

    # Domain
    config["confluence"]["domain"] = _prompt(
        "Your Confluence domain (e.g., mycompany.atlassian.net)"
    )

    if auth_method == "token":
        config["confluence"]["email"] = _prompt("Your email")
        config["confluence"]["token"] = _prompt("Your Atlassian API token", secret=True)
    else:
        print("\n  OAuth setup requires registering an app in the Atlassian Developer Console.")
        print("  Visit: https://developer.atlassian.com/console/myapps/")
        print("  Create an OAuth 2.0 (3LO) app with redirect URI: http://localhost:9876/callback")
        print("  Required scopes: read:confluence-space.summary, write:confluence-content, read:confluence-content.all\n")
        client_id = _prompt("Your Atlassian app Client ID")
        config.setdefault("oauth", {})
        config["oauth"]["client_id"] = client_id
        print("\n  OAuth browser flow will launch on first upload.")

    # Default space
    config["confluence"]["space_key"] = _prompt(
        "Default space key (optional, can be overridden per command)"
    )

    # Mermaid strategy
    mermaid_choice = _prompt_choice(
        "Mermaid diagram strategy:",
        ["auto (macro -> image -> code block)",
         "macro (Confluence plugin required)",
         "image (local mermaid-cli required)",
         "code (keep as code blocks)"],
        default_index=0,
    )
    for key in ("auto", "macro", "image", "code"):
        if key in mermaid_choice:
            config["mermaid"]["strategy"] = key
            break

    # Save
    save_config(config)
    print(f"\n  Configuration saved to {DEFAULT_CONFIG_PATH}")

    # Validate connection
    if auth_method == "token" and config["confluence"]["domain"] and config["confluence"]["token"]:
        print("  Verifying connection...", end=" ")
        try:
            from md_to_adf.confluence.auth import build_token_auth_header
            from md_to_adf.confluence.client import ConfluenceClient

            auth_header = build_token_auth_header(
                config["confluence"]["email"],
                config["confluence"]["token"],
            )
            client = ConfluenceClient(config["confluence"]["domain"], auth_header)
            if config["confluence"]["space_key"]:
                space_id = client.get_space_id(config["confluence"]["space_key"])
                print(f"found space (ID: {space_id})")
            else:
                spaces = client.list_spaces()
                count = len(spaces.get("results", []))
                print(f"connected ({count} spaces available)")
        except MdToAdfError as e:
            print(f"failed ({e.message})")
            if e.hint:
                print(f"  Hint: {e.hint}")
        except Exception as e:
            print(f"failed ({e})")
            print("  You can fix settings in ~/.md-to-adf/config.toml")

    print(f"\n  Ready to go! Try: md-to-adf convert README.md\n")
    return 0
