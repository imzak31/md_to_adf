"""CLI command implementations for md-to-adf."""

import json
import sys

from md_to_adf.core.parser import convert
from md_to_adf.core.validator import validate
from md_to_adf.mermaid import process_mermaid_blocks
from md_to_adf.cli.errors import ConfigError, NotFoundError


def _read_file(path):
    """Read a file and return its contents, raising on error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise NotFoundError(f"File not found: {path}", hint="Check the file path")
    except OSError as e:
        raise ConfigError(f"Cannot read file '{path}': {e}")


def _convert_md(input_path, mermaid_strategy="auto", mermaid_format="png", mermaid_theme="default"):
    """Read a markdown file, convert to ADF, and process mermaid blocks. Returns adf_doc."""
    content = _read_file(input_path)

    adf_doc = convert(content)
    adf_doc = process_mermaid_blocks(
        adf_doc,
        strategy=mermaid_strategy,
        output_format=mermaid_format,
        theme=mermaid_theme,
    )
    return adf_doc


def _require_credentials(domain, email, token):
    """Check that Confluence credentials are provided. Raises ConfigError if any are missing."""
    if not domain:
        raise ConfigError("Confluence domain is required", hint="Set --domain, MD_TO_ADF_DOMAIN, or run 'md-to-adf init'")
    if not email:
        raise ConfigError("Confluence email is required", hint="Set --email, MD_TO_ADF_EMAIL, or run 'md-to-adf init'")
    if not token:
        raise ConfigError("Confluence API token is required", hint="Set --token, MD_TO_ADF_TOKEN, or run 'md-to-adf init'")


def _build_client(domain, email, token):
    """Build a ConfluenceClient from credentials."""
    from md_to_adf.confluence.auth import build_token_auth_header
    from md_to_adf.confluence.client import ConfluenceClient

    auth_header = build_token_auth_header(email, token)
    return ConfluenceClient(domain, auth_header)


def cmd_convert(
    input_path,
    output_path=None,
    validate_output=False,
    compact=False,
    mermaid_strategy="auto",
    mermaid_format="png",
    mermaid_theme="default",
):
    """Read a Markdown file, convert to ADF, and write JSON to file or stdout."""
    adf_doc = _convert_md(input_path, mermaid_strategy, mermaid_format, mermaid_theme)

    if validate_output:
        errors = validate(adf_doc)
        if errors:
            print("Validation warnings:", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)

    indent = None if compact else 2
    json_output = json.dumps(adf_doc, indent=indent)

    if output_path:
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json_output)
                if not compact:
                    f.write("\n")
        except OSError as e:
            print(f"Error writing output to '{output_path}': {e}", file=sys.stderr)
            return 1
    else:
        print(json_output)

    return 0


def cmd_validate(input_path, is_adf=False):
    """Validate a Markdown or ADF JSON file."""
    treat_as_adf = is_adf or input_path.endswith(".json")

    content = _read_file(input_path)

    if treat_as_adf:
        try:
            adf_doc = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON in '{input_path}': {e}", file=sys.stderr)
            return 1
    else:
        adf_doc = convert(content)

    errors = validate(adf_doc)

    if errors:
        print(f"Validation failed for '{input_path}':", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"'{input_path}' is valid ADF.")
    return 0


def cmd_upload(
    input_path,
    domain,
    email,
    token,
    space_key=None,
    title=None,
    parent_id=None,
    page_id=None,
    mermaid_strategy="auto",
    mermaid_format="png",
    mermaid_theme="default",
):
    """Convert and upload a Markdown file to Confluence."""
    adf_doc = _convert_md(input_path, mermaid_strategy, mermaid_format, mermaid_theme)

    errors = validate(adf_doc)
    if errors:
        print("Validation errors found — aborting upload:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    _require_credentials(domain, email, token)
    if not title:
        raise ConfigError("Page title is required", hint="Pass --title")

    client = _build_client(domain, email, token)

    if page_id:
        result = client.update_page(adf_doc, page_id, title)
        action = "updated"
    else:
        if not space_key:
            raise ConfigError("Space key is required when creating a new page", hint="Pass --space")
        result = client.create_page(adf_doc, space_key, title, parent_id=parent_id)
        action = "created"

    # Prefer the webui link from the API response; fall back to constructed URL
    web_link = result.get("_links", {}).get("webui", "")
    if web_link:
        page_url = f"https://{domain}/wiki{web_link}"
    else:
        page_url = f"https://{domain}/wiki/pages/{result.get('id', '')}"
    print(f"Page {action} successfully: {page_url}")
    return 0


def cmd_spaces(domain, email, token):
    """List available Confluence spaces."""
    _require_credentials(domain, email, token)

    client = _build_client(domain, email, token)

    data = client.list_spaces()

    results = data.get("results", [])
    if not results:
        print("No spaces found.")
        return 0

    print(f"{'KEY':<20} {'NAME'}")
    print("-" * 50)
    for space in results:
        key = space.get("key", "")
        name = space.get("name", "")
        print(f"{key:<20} {name}")

    return 0
