---
name: md-to-confluence
description: Convert Markdown files to ADF and upload to Confluence
---

# Markdown to Confluence

Push Markdown files to Confluence as formatted pages.

## Step 1: Check tool availability

Run: `md-to-adf --version`

If not installed, tell the user:
- pip: `pip install md-to-adf`
- brew: `brew tap imzak31/md-to-adf && brew install md-to-adf`
- npm: `npm install -g md2adf`

Then run: `md-to-adf init` to configure credentials.

## Step 2: Identify the target file(s)

Ask the user which markdown file(s) to push. They will typically
reference files with @ — filter suggestions to .md files only.

If no file is specified, suggest scanning the current directory:
`md-to-adf upload . --dry-run`

## Step 3: Preview before uploading

Run: `md-to-adf upload <file-or-dir> --dry-run`

This shows the extracted title and target space without uploading.
Confirm with the user that the title and space look correct.

## Step 4: Upload

For a single file:
`md-to-adf upload <file>`

For multiple files or a directory:
`md-to-adf upload <dir-or-glob>`

If the user needs a specific space, add `--space <KEY>`.
If updating an existing page, add `--page-id <ID>`.
To override the auto-extracted title: `--title "Custom Title"` (single file only).

## Step 5: Report

Show the Confluence URL from the output.
If batch mode, summarize successes and failures.

## Key behaviors

- Title is auto-extracted from the first H1 heading, or the filename.
  Only suggest --title if the user wants to override.
- Space is auto-selected from config. Only ask if multiple spaces
  are configured and the user hasn't specified one.
- Always use --dry-run first when the user seems uncertain.
- If upload fails, the error message includes a hint. Read it
  and suggest the fix before retrying.
- For batch uploads of many files, show the --dry-run output first
  so the user can review titles before committing.
- Use --recursive to include markdown files in subdirectories.
