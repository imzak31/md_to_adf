"""CLI command implementations for md-to-adf."""

import json
import sys
from pathlib import Path

from md_to_adf.core.parser import convert
from md_to_adf.core.validator import validate
from md_to_adf.mermaid import process_mermaid_blocks
from md_to_adf.cli.errors import ConfigError, MdToAdfError, NotFoundError
from md_to_adf.cli.discovery import discover_markdown_files, extract_title
from md_to_adf.cli.spaces import (
    format_space_picker,
    resolve_space_key,
    update_recent_spaces,
)


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
    config,
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
    dry_run=False,
    recursive=False,
):
    """Convert and upload one or more Markdown files to Confluence."""
    # 1. Discover files
    files = discover_markdown_files(input_path, recursive=recursive)
    if not files:
        raise NotFoundError(
            f"No markdown files found in '{input_path}'",
            hint="Check the path or use --recursive",
        )

    # 2. Validate single-file-only flags
    if len(files) > 1:
        if title:
            raise ConfigError(
                "--title cannot be used with multiple files",
                hint="Titles are auto-extracted from each file's H1 heading",
            )
        if page_id:
            raise ConfigError(
                "--page-id cannot be used with multiple files",
                hint="Update pages one at a time",
            )

    # 3. Build file→title mapping
    file_titles = []
    for f in files:
        content = _read_file(f)
        extracted = title if (title and len(files) == 1) else extract_title(content, f)
        file_titles.append((f, extracted))

    # 4. Resolve space
    _require_credentials(domain, email, token)
    resolved_space = resolve_space_key(config, cli_space=space_key)
    if resolved_space is None:
        # Interactive space picker
        choices, keys = format_space_picker(config)
        if choices:
            print("\n  Select a space:", file=sys.stderr)
            for i, c in enumerate(choices):
                print(f"    {i + 1}) {c}", file=sys.stderr)
            print(f"    {len(choices) + 1}) Other (enter space key)", file=sys.stderr)
            raw = input(f"  Choice [1-{len(choices) + 1}]: ").strip()
            try:
                idx = int(raw) - 1
                if 0 <= idx < len(keys):
                    resolved_space = keys[idx]
                else:
                    resolved_space = input("  Space key: ").strip()
            except ValueError:
                resolved_space = raw  # treat as space key
        else:
            resolved_space = input("  Space key: ").strip()
        if not resolved_space:
            raise ConfigError(
                "Space key is required",
                hint="Pass --space or configure named spaces",
            )

    # 5. Dry run
    if dry_run:
        print(f"\nDry run — {len(file_titles)} file(s) → space {resolved_space}\n")
        for f, t in file_titles:
            print(f"  {Path(f).name:40s} → \"{t}\"")
        return 0

    # 6. Upload
    client = _build_client(domain, email, token)
    successes = 0
    failures = []

    for f, t in file_titles:
        try:
            adf_doc = _convert_md(f, mermaid_strategy, mermaid_format, mermaid_theme)
            errors = validate(adf_doc)
            if errors:
                failures.append((f, f"Validation: {errors[0]}"))
                continue

            if page_id:
                result = client.update_page(adf_doc, page_id, t)
                action = "updated"
            else:
                result = client.create_page(adf_doc, resolved_space, t, parent_id=parent_id)
                action = "created"

            web_link = result.get("_links", {}).get("webui", "")
            url = f"https://{domain}/wiki{web_link}" if web_link else ""
            print(f"  ✓ {Path(f).name} → \"{t}\" ({action}) {url}")
            successes += 1
        except MdToAdfError as e:
            failures.append((f, e.message))
            print(f"  ✗ {Path(f).name} → {e.message}")
        except Exception as e:
            failures.append((f, str(e)))
            print(f"  ✗ {Path(f).name} → {e}")

    # 7. Summary
    if len(file_titles) > 1:
        print(f"\nDone: {successes} uploaded, {len(failures)} failed")

    # 8. Update recent spaces
    if successes > 0:
        from md_to_adf.cli.config import save_config
        update_recent_spaces(config, resolved_space)
        save_config(config)

    return 1 if failures else 0


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
