#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="${HOME}/.claude/skills"
SKILL_URL="https://raw.githubusercontent.com/imzak31/md-to-adf/main/skill/md-to-confluence.md"

mkdir -p "$SKILL_DIR"
curl -sL "$SKILL_URL" -o "${SKILL_DIR}/md-to-confluence.md"

echo "Skill installed to ${SKILL_DIR}/md-to-confluence.md"
echo "Use /md-to-confluence in Claude Code to get started."
