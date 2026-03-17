"""Tests for file discovery and title extraction."""

from pathlib import Path
from md_to_adf.cli.discovery import discover_markdown_files, extract_title, parse_selection
from md_to_adf.cli.errors import NotFoundError
import pytest


def test_discover_single_file(tmp_path):
    f = tmp_path / "doc.md"
    f.write_text("# Hello")
    result = discover_markdown_files(str(f))
    assert result == [str(f)]


def test_discover_non_md_file_raises(tmp_path):
    f = tmp_path / "doc.txt"
    f.write_text("hello")
    with pytest.raises(NotFoundError):
        discover_markdown_files(str(f))


def test_discover_directory(tmp_path):
    (tmp_path / "a.md").write_text("# A")
    (tmp_path / "b.md").write_text("# B")
    (tmp_path / "c.txt").write_text("not markdown")
    result = discover_markdown_files(str(tmp_path))
    assert len(result) == 2
    assert all(r.endswith(".md") for r in result)


def test_discover_directory_skips_hidden(tmp_path):
    hidden = tmp_path / ".hidden"
    hidden.mkdir()
    (hidden / "secret.md").write_text("# Secret")
    (tmp_path / "visible.md").write_text("# Visible")
    result = discover_markdown_files(str(tmp_path))
    assert len(result) == 1


def test_discover_glob(tmp_path):
    (tmp_path / "a.md").write_text("# A")
    (tmp_path / "b.md").write_text("# B")
    result = discover_markdown_files(str(tmp_path / "*.md"))
    assert len(result) == 2


def test_discover_empty_directory(tmp_path):
    result = discover_markdown_files(str(tmp_path))
    assert result == []


def test_discover_nonexistent_raises():
    with pytest.raises(NotFoundError):
        discover_markdown_files("/nonexistent/path.md")


def test_discover_recursive(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (tmp_path / "top.md").write_text("# Top")
    (sub / "nested.md").write_text("# Nested")
    non_recursive = discover_markdown_files(str(tmp_path), recursive=False)
    assert len(non_recursive) == 1
    recursive = discover_markdown_files(str(tmp_path), recursive=True)
    assert len(recursive) == 2


def test_discover_markdown_extension(tmp_path):
    (tmp_path / "doc.markdown").write_text("# Doc")
    result = discover_markdown_files(str(tmp_path))
    assert len(result) == 1


def test_extract_title_from_h1():
    assert extract_title("# My Title\n\nBody", "file.md") == "My Title"


def test_extract_title_fallback_to_filename():
    assert extract_title("No heading here", "my-great-doc.md") == "My Great Doc"


def test_extract_title_underscores():
    assert extract_title("No heading", "api_reference.md") == "Api Reference"


def test_extract_title_h1_with_formatting():
    assert extract_title("# **Bold Title**\n\nBody", "file.md") == "**Bold Title**"


def test_extract_title_skips_h2():
    assert extract_title("## Not H1\nBody", "fallback.md") == "Fallback"


def test_parse_selection_single():
    assert parse_selection("3", 5) == [2]


def test_parse_selection_multiple():
    assert parse_selection("1,3,5", 5) == [0, 2, 4]


def test_parse_selection_range():
    assert parse_selection("2-4", 5) == [1, 2, 3]


def test_parse_selection_all():
    assert parse_selection("all", 5) == [0, 1, 2, 3, 4]


def test_parse_selection_mixed():
    assert parse_selection("1,3-5", 6) == [0, 2, 3, 4]


def test_parse_selection_out_of_range():
    assert parse_selection("10", 5) == []


def test_parse_selection_deduplicates():
    assert parse_selection("1,1,1", 5) == [0]
