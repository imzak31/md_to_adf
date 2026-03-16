"""Tests for CLI commands."""

import json
import tempfile
from md_to_adf.cli.commands import cmd_convert, cmd_validate


def test_cmd_convert_to_stdout(capsys):
    md_file = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
    md_file.write("# Hello\n\nWorld")
    md_file.close()

    cmd_convert(input_path=md_file.name, output_path=None, validate_output=False,
                compact=False, mermaid_strategy="code")
    captured = capsys.readouterr()
    doc = json.loads(captured.out)
    assert doc["type"] == "doc"
    assert doc["content"][0]["type"] == "heading"


def test_cmd_convert_to_file():
    md_file = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
    md_file.write("# Test")
    md_file.close()

    out_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    out_file.close()

    cmd_convert(input_path=md_file.name, output_path=out_file.name,
                validate_output=False, compact=False, mermaid_strategy="code")

    with open(out_file.name) as f:
        doc = json.load(f)
    assert doc["type"] == "doc"


def test_cmd_convert_compact(capsys):
    md_file = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
    md_file.write("# Hello")
    md_file.close()

    cmd_convert(input_path=md_file.name, output_path=None, validate_output=False,
                compact=True, mermaid_strategy="code")
    captured = capsys.readouterr()
    assert "\n" not in captured.out.strip()


def test_cmd_validate_valid():
    md_file = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
    md_file.write("# Valid\n\nParagraph")
    md_file.close()
    result = cmd_validate(md_file.name)
    assert result == 0


def test_cmd_validate_detects_issues():
    bad_doc = {"version": 2, "type": "doc", "content": []}
    adf_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(bad_doc, adf_file)
    adf_file.close()
    result = cmd_validate(adf_file.name, is_adf=True)
    assert result != 0
