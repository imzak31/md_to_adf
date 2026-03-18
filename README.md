# md-to-adf

Convert Markdown to Atlassian Document Format (ADF) and publish to Confluence Cloud.

[![Tests](https://github.com/imzak31/md-to-adf/actions/workflows/test.yml/badge.svg)](https://github.com/imzak31/md-to-adf/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/md-to-adf)](https://pypi.org/project/md-to-adf/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Install

```bash
pip install md-to-adf          # Python
npm install -g md2adf           # Node (wraps the Python package)
brew tap imzak31/md-to-adf && brew install md-to-adf  # macOS
```

## Quick start

```bash
# 1. Set up your Confluence credentials (one-time)
md-to-adf init

# 2. Preview what will be uploaded
md-to-adf upload docs/ --dry-run

# 3. Push to Confluence
md-to-adf upload docs/ --space ENG
```

Titles are auto-extracted from each file's first `# Heading`. No `--title` flag needed.

## CLI Commands

### `init` — Set up credentials

```bash
md-to-adf init
```

Interactive wizard that saves your Confluence domain, email, and API token to `~/.md-to-adf/config.toml`. Generate a token at https://id.atlassian.com/manage-profile/security/api-tokens.

### `upload` — Push markdown to Confluence

```bash
md-to-adf upload <file|directory|glob> [options]
```

| Option | Description |
|--------|-------------|
| `--space KEY` | Target Confluence space |
| `--title TEXT` | Override auto-extracted title (single file only) |
| `--page-id ID` | Update an existing page (single file only) |
| `--parent-id ID` | Create under a parent page |
| `--dry-run` | Preview files and titles without uploading |
| `--recursive` | Include markdown in subdirectories |
| `--mermaid STRATEGY` | Diagram handling: `auto`, `macro`, `image`, `code` |

```bash
# Single file
md-to-adf upload docs/architecture.md --space ENG

# Entire directory
md-to-adf upload docs/ --space ENG

# Glob pattern
md-to-adf upload "docs/*.md" --space ENG

# Preview first
md-to-adf upload docs/ --dry-run

# Update an existing page
md-to-adf upload docs/guide.md --page-id 12345
```

Batch uploads process each file independently — failures don't stop the rest. A summary is printed at the end.

### `convert` — Generate ADF JSON

```bash
md-to-adf convert <file> [options]
```

| Option | Description |
|--------|-------------|
| `--output FILE` | Write to file instead of stdout |
| `--validate` | Check ADF validity after conversion |
| `--compact` | Minified JSON output |
| `--mermaid STRATEGY` | Diagram handling strategy |

### `validate` — Check ADF validity

```bash
md-to-adf validate docs/my-page.md
md-to-adf validate output.adf.json
```

### `spaces` — List available spaces

```bash
md-to-adf spaces
```

## Configuration

Config file: `~/.md-to-adf/config.toml`

```toml
[confluence]
domain = "myorg.atlassian.net"
email = "me@example.com"
token = "my-api-token"
space_key = "ENG"

[mermaid]
strategy = "auto"
```

Settings can also be provided via environment variables or CLI flags:

| Setting | Config key | Env var | CLI flag |
|---------|------------|---------|----------|
| Domain | `confluence.domain` | `MD_TO_ADF_DOMAIN` | `--domain` |
| Email | `confluence.email` | `MD_TO_ADF_EMAIL` | `--email` |
| Token | `confluence.token` | `MD_TO_ADF_TOKEN` | `--token` |
| Space | `confluence.space_key` | `MD_TO_ADF_SPACE` | `--space` |
| Mermaid | `mermaid.strategy` | `MD_TO_ADF_MERMAID` | `--mermaid` |

**Priority:** CLI flags > env vars > config file > defaults

Use `--debug` on any command to see full error details.

### Named spaces

For teams that publish to multiple spaces, add shortcuts to your config:

```toml
[spaces.eng]
key = "ENG"
name = "Engineering"
parent_id = "12345"

[spaces.product]
key = "PROD"
name = "Product Docs"
```

When uploading without `--space`, a picker appears if multiple spaces are configured. Recent spaces are tracked automatically.

## Mermaid diagrams

Fenced `mermaid` code blocks are converted according to the selected strategy:

| Strategy | Description |
|----------|-------------|
| `auto` | Confluence macro if available, otherwise code block |
| `macro` | Confluence Mermaid macro (requires the Mermaid app) |
| `image` | Render to PNG locally via `mmdc` and attach |
| `code` | Keep as a code block |

## Claude Code integration

Install the `/md-to-confluence` skill to push markdown from Claude Code:

```bash
curl -sL https://raw.githubusercontent.com/imzak31/md_to_adf/main/skill/md-to-confluence.md \
  -o ~/.claude/skills/md-to-confluence.md
```

Then use `/md-to-confluence` in any conversation. The skill runs `--dry-run` first to preview, then uploads on confirmation.

## Python API

```python
from md_to_adf import convert, validate

adf = convert("# Hello\n\nThis is **bold** text.")
errors = validate(adf)  # [] if valid
```

```python
from md_to_adf.confluence.auth import build_token_auth_header
from md_to_adf.confluence.client import ConfluenceClient

auth = build_token_auth_header("me@example.com", "my-api-token")
client = ConfluenceClient("myorg.atlassian.net", auth)
result = client.create_page(adf, space_key="ENG", title="My Page")
```

## Contributing

1. Fork and create a feature branch
2. `pip install -e ".[dev]"`
3. `pytest tests/ -v`
4. Open a pull request

## License

MIT — see [LICENSE](LICENSE).
