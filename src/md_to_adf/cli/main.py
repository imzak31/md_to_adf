"""CLI entry point for md-to-adf."""

import argparse
import sys
import traceback

from md_to_adf import __version__
from md_to_adf.cli.config import load_config, get_config_value
from md_to_adf.cli.errors import MdToAdfError


def _add_mermaid_arg(parser):
    """Add the --mermaid argument to a subparser."""
    parser.add_argument(
        "--mermaid",
        metavar="STRATEGY",
        default=None,
        choices=["auto", "code", "macro", "image"],
        help="Mermaid diagram strategy: auto, code, macro, image (default: auto)",
    )


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="md-to-adf",
        description="Convert Markdown to Atlassian Document Format (ADF).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument("--debug", action="store_true", help="Show full tracebacks on error")

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # ── init ────────────────────────────────────────────────────────────────
    init_parser = subparsers.add_parser(
        "init",
        help="Run the interactive setup wizard to configure md-to-adf.",
    )
    auth_group = init_parser.add_mutually_exclusive_group()
    auth_group.add_argument(
        "--token",
        action="store_true",
        help="Configure API token authentication (default).",
    )
    auth_group.add_argument(
        "--oauth",
        action="store_true",
        help="Configure OAuth authentication.",
    )

    # ── convert ─────────────────────────────────────────────────────────────
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert a Markdown file to ADF JSON.",
    )
    convert_parser.add_argument(
        "input",
        metavar="INPUT",
        help="Path to the input Markdown file.",
    )
    convert_parser.add_argument(
        "-o", "--output",
        metavar="OUTPUT",
        default=None,
        help="Path to write the ADF JSON output (default: stdout).",
    )
    convert_parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate output and print any warnings.",
    )
    output_format_group = convert_parser.add_mutually_exclusive_group()
    output_format_group.add_argument(
        "--pretty",
        action="store_true",
        default=False,
        help="Pretty-print JSON with indentation (default).",
    )
    output_format_group.add_argument(
        "--compact",
        action="store_true",
        default=False,
        help="Output minified (compact) JSON.",
    )
    _add_mermaid_arg(convert_parser)

    # ── upload ──────────────────────────────────────────────────────────────
    upload_parser = subparsers.add_parser(
        "upload",
        help="Convert and upload a Markdown file to Confluence.",
    )
    upload_parser.add_argument(
        "input",
        metavar="INPUT",
        help="Path to markdown file, directory, or glob pattern.",
    )
    upload_parser.add_argument(
        "--title",
        required=False,
        default=None,
        metavar="TITLE",
        help="Title for the Confluence page (required).",
    )
    upload_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be uploaded without uploading.",
    )
    upload_parser.add_argument(
        "--recursive",
        action="store_true",
        help="Scan directories recursively.",
    )
    upload_parser.add_argument(
        "--domain",
        metavar="DOMAIN",
        default=None,
        help="Confluence domain (e.g. yourcompany.atlassian.net).",
    )
    upload_parser.add_argument(
        "--email",
        metavar="EMAIL",
        default=None,
        help="Atlassian account email.",
    )
    upload_parser.add_argument(
        "--token",
        metavar="TOKEN",
        default=None,
        help="Atlassian API token.",
    )
    upload_parser.add_argument(
        "--space",
        metavar="SPACE_KEY",
        default=None,
        help="Confluence space key.",
    )
    upload_parser.add_argument(
        "--page-id",
        metavar="PAGE_ID",
        default=None,
        help="Existing page ID to update instead of creating a new page.",
    )
    upload_parser.add_argument(
        "--parent-id",
        metavar="PARENT_ID",
        default=None,
        help="Parent page ID for new pages.",
    )
    _add_mermaid_arg(upload_parser)

    # ── validate ─────────────────────────────────────────────────────────────
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a Markdown or ADF JSON file.",
    )
    validate_parser.add_argument(
        "input",
        metavar="INPUT",
        help="Path to the Markdown or ADF JSON file to validate.",
    )

    # ── spaces ───────────────────────────────────────────────────────────────
    spaces_parser = subparsers.add_parser(
        "spaces",
        help="List available Confluence spaces.",
    )
    spaces_parser.add_argument(
        "--domain",
        metavar="DOMAIN",
        default=None,
        help="Confluence domain.",
    )
    spaces_parser.add_argument(
        "--email",
        metavar="EMAIL",
        default=None,
        help="Atlassian account email.",
    )
    spaces_parser.add_argument(
        "--token",
        metavar="TOKEN",
        default=None,
        help="Atlassian API token.",
    )

    return parser


def main():
    """Main CLI entry point. Returns an exit code (0 = success)."""
    parser = _build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    debug = getattr(args, "debug", False)
    config = load_config()

    try:
        # ── init ────────────────────────────────────────────────────────────────
        if args.command == "init":
            try:
                from md_to_adf.cli.wizard import run_wizard  # noqa: F401 — Task 9
            except ImportError:
                print(
                    "Error: The setup wizard is not yet available. "
                    "Please configure ~/.md-to-adf/config.toml manually.",
                    file=sys.stderr,
                )
                return 1
            return run_wizard(token_mode=args.token, oauth_mode=args.oauth) or 0

        # ── convert ─────────────────────────────────────────────────────────────
        if args.command == "convert":
            from md_to_adf.cli.commands import cmd_convert

            mermaid_strategy = get_config_value(
                config, "mermaid", "strategy", cli_value=args.mermaid
            ) or "auto"

            return cmd_convert(
                input_path=args.input,
                output_path=args.output,
                validate_output=args.validate,
                compact=args.compact,
                mermaid_strategy=mermaid_strategy,
            ) or 0

        # ── upload ──────────────────────────────────────────────────────────────
        if args.command == "upload":
            from md_to_adf.cli.commands import cmd_upload

            domain = get_config_value(config, "confluence", "domain", cli_value=args.domain)
            email = get_config_value(config, "confluence", "email", cli_value=args.email)
            token = get_config_value(config, "confluence", "token", cli_value=args.token)
            space_key = get_config_value(config, "confluence", "space_key", cli_value=args.space)
            mermaid_strategy = get_config_value(
                config, "mermaid", "strategy", cli_value=args.mermaid
            ) or "auto"

            return cmd_upload(
                input_path=args.input,
                config=config,
                domain=domain,
                email=email,
                token=token,
                space_key=space_key,
                title=args.title,
                parent_id=args.parent_id,
                page_id=args.page_id,
                mermaid_strategy=mermaid_strategy,
                dry_run=args.dry_run,
                recursive=args.recursive,
            ) or 0

        # ── validate ─────────────────────────────────────────────────────────────
        if args.command == "validate":
            from md_to_adf.cli.commands import cmd_validate

            return cmd_validate(args.input) or 0

        # ── spaces ───────────────────────────────────────────────────────────────
        if args.command == "spaces":
            from md_to_adf.cli.commands import cmd_spaces

            domain = get_config_value(config, "confluence", "domain", cli_value=args.domain)
            email = get_config_value(config, "confluence", "email", cli_value=args.email)
            token = get_config_value(config, "confluence", "token", cli_value=args.token)

            return cmd_spaces(domain=domain, email=email, token=token) or 0

        parser.print_help()
        return 0

    except MdToAdfError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        if e.hint:
            print(f"  Hint: {e.hint}", file=sys.stderr)
        if debug:
            traceback.print_exc()
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if debug:
            traceback.print_exc()
        else:
            print("  Run with --debug for details", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main() or 0)
