"""CLI command implementations for md-to-adf."""

import json
import sys

from md_to_adf.core.parser import convert
from md_to_adf.core.validator import validate
from md_to_adf.mermaid import process_mermaid_blocks


def _read_file(path):
    """Read a file and return its contents, or print an error and return None."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        print(f"Error reading file '{path}': {e}", file=sys.stderr)
        return None


def _convert_md(input_path, mermaid_strategy="auto", mermaid_format="png", mermaid_theme="default"):
    """Read a markdown file, convert to ADF, and process mermaid blocks. Returns (adf_doc, exit_code)."""
    content = _read_file(input_path)
    if content is None:
        return None, 1

    adf_doc = convert(content)
    adf_doc = process_mermaid_blocks(
        adf_doc,
        strategy=mermaid_strategy,
        output_format=mermaid_format,
        theme=mermaid_theme,
    )
    return adf_doc, 0


def _require_credentials(domain, email, token):
    """Check that Confluence credentials are provided. Returns 1 on error, None if OK."""
    if not domain:
        print("Error: Confluence domain is required (--domain or MD_TO_ADF_DOMAIN).", file=sys.stderr)
        return 1
    if not email:
        print("Error: Confluence email is required (--email or MD_TO_ADF_EMAIL).", file=sys.stderr)
        return 1
    if not token:
        print("Error: Confluence API token is required (--token or MD_TO_ADF_TOKEN).", file=sys.stderr)
        return 1
    return None


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
    adf_doc, err = _convert_md(input_path, mermaid_strategy, mermaid_format, mermaid_theme)
    if err:
        return err

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
    if content is None:
        return 1

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
    adf_doc, err = _convert_md(input_path, mermaid_strategy, mermaid_format, mermaid_theme)
    if err:
        return err

    errors = validate(adf_doc)
    if errors:
        print("Validation errors found — aborting upload:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    cred_err = _require_credentials(domain, email, token)
    if cred_err:
        return cred_err
    if not title:
        print("Error: Page title is required (--title).", file=sys.stderr)
        return 1

    client = _build_client(domain, email, token)

    try:
        if page_id:
            result = client.update_page(adf_doc, page_id, title)
            action = "updated"
        else:
            if not space_key:
                print("Error: Space key is required when creating a new page (--space).", file=sys.stderr)
                return 1
            result = client.create_page(adf_doc, space_key, title, parent_id=parent_id)
            action = "created"
    except Exception as e:
        print(f"Error uploading to Confluence: {e}", file=sys.stderr)
        return 1

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
    cred_err = _require_credentials(domain, email, token)
    if cred_err:
        return cred_err

    client = _build_client(domain, email, token)

    try:
        data = client.list_spaces()
    except Exception as e:
        print(f"Error listing spaces: {e}", file=sys.stderr)
        return 1

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
