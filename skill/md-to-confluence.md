---
name: md-to-confluence
description: Convert Markdown files to Atlassian Document Format (ADF) and upload to Confluence
---

# Markdown to Confluence

Convert Markdown files (including AI-generated content with Mermaid diagrams) to ADF and upload to Confluence.

## Prerequisites Check

First, check if md-to-adf is installed:

```bash
md-to-adf --version
```

If not installed, guide the user:
```bash
pip install md-to-adf
md-to-adf init
```

## Workflow

1. **Identify the target file(s)** — ask the user which markdown file(s) to push, or detect from context
2. **Check configuration** — verify `~/.md-to-adf/config.toml` exists via `md-to-adf spaces` (validates connection)
3. **Preview** — optionally show the user what will be converted: `md-to-adf convert <file> --validate`
4. **Get page details** — ask for:
   - Title (suggest one based on the markdown content)
   - Space key (use default from config if set)
   - New page or update existing (if updating, need page ID or URL)
   - Parent page (optional)
5. **Upload** — run the upload command:
   ```bash
   md-to-adf upload <file> --title "Page Title" --space <KEY>
   ```
6. **Report** — show the URL of the created/updated page

## Batch Mode

For multiple files:
```bash
for f in docs/*.md; do
  title=$(head -1 "$f" | sed 's/^#\+ //')
  md-to-adf upload "$f" --title "$title" --space <KEY>
done
```

## Convert Only (No Upload)

```bash
md-to-adf convert <file> -o <output.adf.json>
md-to-adf convert <file> --validate
```

## Tips

- Claude can help edit/improve the markdown before converting
- Use `--mermaid auto` (default) for best diagram handling
- Use `md-to-adf validate` to check ADF output before uploading
- The tool reads config from `~/.md-to-adf/config.toml` — run `md-to-adf init` to set up
