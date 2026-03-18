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


def test_debug_flag_exists():
    from md_to_adf.cli.main import _build_parser
    parser = _build_parser()
    args = parser.parse_args(["--debug", "convert", "test.md"])
    assert args.debug is True


def test_debug_flag_default_false():
    from md_to_adf.cli.main import _build_parser
    parser = _build_parser()
    args = parser.parse_args(["convert", "test.md"])
    assert args.debug is False


def test_dry_run_shows_files(tmp_path, capsys):
    (tmp_path / "a.md").write_text("# Alpha\nContent")
    (tmp_path / "b.md").write_text("# Beta\nContent")
    from md_to_adf.cli.commands import cmd_upload
    result = cmd_upload(
        input_path=str(tmp_path),
        config={},
        domain="test.atlassian.net",
        email="test@example.com",
        token="tok",
        space_key="TS",
        dry_run=True,
    )
    assert result == 0
    captured = capsys.readouterr()
    assert "Alpha" in captured.out
    assert "Beta" in captured.out
    assert "Dry run" in captured.out


def test_title_with_multiple_files_raises(tmp_path):
    (tmp_path / "a.md").write_text("# A")
    (tmp_path / "b.md").write_text("# B")
    from md_to_adf.cli.commands import cmd_upload
    from md_to_adf.cli.errors import ConfigError
    import pytest
    with pytest.raises(ConfigError, match="--title cannot be used"):
        cmd_upload(
            input_path=str(tmp_path),
            config={},
            domain="test.atlassian.net",
            email="test@example.com",
            token="tok",
            space_key="TS",
            title="Override",
        )


def test_auto_title_extraction(tmp_path, capsys):
    (tmp_path / "my-doc.md").write_text("# Auto Title\nBody")
    from md_to_adf.cli.commands import cmd_upload
    result = cmd_upload(
        input_path=str(tmp_path / "my-doc.md"),
        config={},
        domain="test.atlassian.net",
        email="test@example.com",
        token="tok",
        space_key="TS",
        dry_run=True,
    )
    assert result == 0
    captured = capsys.readouterr()
    assert "Auto Title" in captured.out
