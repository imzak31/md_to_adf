# md-to-adf

Convert Markdown to Atlassian Document Format (ADF) and publish to Confluence Cloud.

[![Tests](https://github.com/imzak31/md-to-adf/actions/workflows/test.yml/badge.svg)](https://github.com/imzak31/md-to-adf/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/md-to-adf)](https://pypi.org/project/md-to-adf/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## What it does

`md-to-adf` takes a Markdown file and converts it to the JSON-based Atlassian Document Format (ADF) that Confluence Cloud requires for its REST API. It handles headings, paragraphs, bold/italic/code inline formatting, fenced code blocks, bullet and ordered lists, blockquotes, horizontal rules, tables, and Mermaid diagrams. Once converted, the built-in upload command creates or updates a Confluence page in a single step, so you can keep documentation in version control and push it to Confluence with one command.

## Install

**pip**
```bash
pip install md-to-adf
```

**npm** (installs the Python package via pip automatically)
```bash
npm install -g md2adf
```

**Homebrew**
```bash
brew tap imzak31/md-to-adf
brew install md-to-adf
```

## Quick start

**Convert a Markdown file to ADF JSON:**
```bash
md-to-adf convert docs/my-page.md
```

**Convert and write to a file:**
```bash
md-to-adf convert docs/my-page.md --output my-page.adf.json
```

**Convert and validate the output:**
```bash
md-to-adf convert docs/my-page.md --validate
```

**Upload to Confluence:**
```bash
md-to-adf upload docs/my-page.md \
  --title "My Page" \
  --space ENG \
  --parent 12345
```

**Upload using environment variables (no flags needed after setup):**
```bash
export MD_TO_ADF_DOMAIN=myorg.atlassian.net
export MD_TO_ADF_EMAIL=me@example.com
export MD_TO_ADF_TOKEN=my-api-token
export MD_TO_ADF_SPACE=ENG

md-to-adf upload docs/my-page.md --title "My Page"
```

**Upload a directory of markdown files:**
```bash
# Upload a directory of markdown files
md-to-adf upload docs/ --space ENG

# Preview what would be uploaded (dry run)
md-to-adf upload docs/ --dry-run

# Upload with recursive directory scan
md-to-adf upload docs/ --recursive --space ENG
```

## Setup

Run the interactive wizard to store your Confluence credentials once:

```bash
md-to-adf init
```

The wizard prompts for your Confluence domain, email address, and API token, then writes them to `~/.md-to-adf/config.toml`. After running `init`, the `upload` command works without any flags.

To generate a Confluence API token, visit:
https://id.atlassian.com/manage-profile/security/api-tokens

## Configuration

Config file location: `~/.md-to-adf/config.toml`

Example config file:
```toml
[confluence]
domain = "myorg.atlassian.net"
email = "me@example.com"
token = "my-api-token"
space_key = "ENG"

[mermaid]
strategy = "auto"
```

### Settings reference

| Setting | Config key | Env var | CLI flag |
|---------|------------|---------|----------|
| Domain | `confluence.domain` | `MD_TO_ADF_DOMAIN` | `--domain` |
| Email | `confluence.email` | `MD_TO_ADF_EMAIL` | `--email` |
| Token | `confluence.token` | `MD_TO_ADF_TOKEN` | `--token` |
| Space | `confluence.space_key` | `MD_TO_ADF_SPACE` | `--space` |
| Mermaid | `mermaid.strategy` | `MD_TO_ADF_MERMAID` | `--mermaid` |

**Priority:** CLI flags > env vars > config file > defaults

Use `--debug` on any command to see full error tracebacks.

## CLI Commands

### `init` — Interactive setup wizard

```bash
md-to-adf init
```

Prompts for Confluence credentials and writes `~/.md-to-adf/config.toml`.

---

### `convert` — Convert Markdown to ADF

```bash
md-to-adf convert <file> [options]
```

| Option | Description |
|--------|-------------|
| `--output FILE` | Write ADF JSON to FILE instead of stdout |
| `--validate` | Validate the ADF output after conversion |
| `--mermaid STRATEGY` | Mermaid handling: `auto`, `macro`, `image`, `code` |

Examples:
```bash
# Print ADF JSON to stdout
md-to-adf convert README.md

# Save to file and validate
md-to-adf convert docs/guide.md --output guide.adf.json --validate
```

---

### `upload` — Upload to Confluence

```bash
md-to-adf upload <file> [options]
```

| Option | Description |
|--------|-------------|
| `--title TEXT` | Page title override (optional — auto-extracted from H1) |
| `--space KEY` | Confluence space key |
| `--parent ID` | Parent page ID |
| `--domain HOST` | Confluence domain |
| `--email EMAIL` | Atlassian account email |
| `--token TOKEN` | Atlassian API token |
| `--mermaid STRATEGY` | Mermaid handling strategy |
| `--dry-run` | Show what would be uploaded without uploading |
| `--recursive` | Scan directories recursively for .md files |

Examples:
```bash
# Upload using config file credentials
md-to-adf upload docs/architecture.md --title "Architecture Overview"

# Upload to a specific space with a parent page
md-to-adf upload docs/guide.md \
  --title "User Guide" \
  --space ENG \
  --parent 98765
```

---

### `validate` — Validate ADF JSON

```bash
md-to-adf validate <file>
```

Validates a Markdown file (by converting first) or a raw ADF JSON file against the ADF schema.

```bash
md-to-adf validate docs/my-page.md
md-to-adf validate output.adf.json
```

---

### `spaces` — List Confluence spaces

```bash
md-to-adf spaces
```

Lists all spaces accessible with your configured credentials. Useful for finding space keys.

## Batch Upload

Upload a directory or glob pattern of markdown files in one command:

```bash
# Upload all markdown files in a directory
md-to-adf upload docs/ --space ENG

# Use a glob pattern
md-to-adf upload "docs/*.md" --space ENG

# Preview first, then upload
md-to-adf upload docs/ --dry-run
md-to-adf upload docs/ --space ENG
```

Titles are auto-extracted from each file's first H1 heading. If no H1 is found, the filename is used (e.g., `api-reference.md` becomes "Api Reference").

Failures in batch mode don't stop the upload — each file is processed independently and a summary is printed at the end.

## Named Spaces

Configure frequently-used spaces in `~/.md-to-adf/config.toml` for quick selection:

```toml
[spaces.eng]
key = "ENG"
name = "Engineering"
parent_id = "12345"    # optional default parent page

[spaces.product]
key = "PROD"
name = "Product Docs"
```

When uploading without `--space`, the tool shows a picker if multiple spaces are configured. Recent spaces are tracked automatically.

## Mermaid Support

Mermaid diagrams in fenced code blocks (` ```mermaid `) are handled according to the selected strategy:

| Strategy | Description |
|----------|-------------|
| `auto` | Use `macro` if the Mermaid for Confluence app is installed, otherwise fall back to `code` |
| `macro` | Render as a Confluence Mermaid macro (requires the Mermaid app) |
| `image` | Render the diagram to a PNG and attach it to the page |
| `code` | Preserve the diagram source as a code block |

Set the strategy in config, env var, or per-command:
```bash
md-to-adf upload diagram.md --mermaid image
```

## Claude Code Skill

`md-to-adf` ships a Claude Code skill for uploading markdown to Confluence directly from your editor.

**Install the skill:**
```bash
curl -sL https://raw.githubusercontent.com/imzak31/md_to_adf/main/skill/md-to-confluence.md \
  -o ~/.claude/skills/md-to-confluence.md
```

**Use it:**
```
/md-to-confluence
```

The skill guides Claude through a preview-first workflow: identify files, dry-run to verify titles and space, then upload.

## Python Library API

You can use `md-to-adf` as a library in your own Python projects:

```python
from md_to_adf import convert, validate

# Convert Markdown string to ADF dict
markdown = "# Hello\n\nThis is **bold** text."
adf = convert(markdown)
print(adf)  # {"version": 1, "type": "doc", "content": [...]}

# Validate an ADF dict
errors = validate(adf)
if errors:
    print("Validation errors:", errors)
else:
    print("Valid ADF document")
```

**Upload programmatically:**
```python
from md_to_adf import convert
from md_to_adf.confluence.auth import build_token_auth_header
from md_to_adf.confluence.client import ConfluenceClient

adf = convert(open("docs/page.md").read())

auth = build_token_auth_header("me@example.com", "my-api-token")
client = ConfluenceClient("myorg.atlassian.net", auth)

result = client.create_page(adf, space_key="ENG", title="My Page")
print(f"Published: https://myorg.atlassian.net/wiki{result['_links']['webui']}")
```

## Contributing

1. Fork the repository and create a feature branch.
2. Install development dependencies: `pip install -e ".[dev]"`
3. Run the test suite: `pytest tests/ -v`
4. Ensure all tests pass and add tests for new functionality.
5. Open a pull request with a clear description of the change.

The test suite covers the converter, validator, CLI, and Confluence client (with mocked HTTP). New features should include unit tests.

## License

MIT — see [LICENSE](LICENSE).
