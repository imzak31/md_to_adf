"""File discovery, title extraction, and interactive picker for markdown files."""

import glob
import os
import re
import subprocess
from pathlib import Path

from md_to_adf.cli.errors import NotFoundError

_MD_EXTENSIONS = {".md", ".markdown"}


def discover_markdown_files(path, recursive=False):
    """Discover markdown files from a file path, directory, or glob pattern.
    Returns a sorted list of file paths.
    Raises NotFoundError if path doesn't exist and isn't a glob.
    """
    if "*" in path or "?" in path:
        pattern = path
        if recursive and "**" not in pattern:
            pass  # user's glob is explicit
        matches = glob.glob(pattern, recursive=recursive)
        return sorted(f for f in matches if Path(f).suffix.lower() in _MD_EXTENSIONS)

    p = Path(path)

    if p.is_file():
        if p.suffix.lower() not in _MD_EXTENSIONS:
            raise NotFoundError(f"'{path}' is not a markdown file", hint="Provide a .md or .markdown file")
        return [str(p)]

    if p.is_dir():
        return sorted(_scan_directory(p, recursive))

    raise NotFoundError(f"Path not found: {path}", hint="Check the file or directory path")


def _scan_directory(directory, recursive):
    """Scan directory for markdown files, respecting .gitignore when possible."""
    git_files = _git_ls_files(directory)
    if git_files is not None:
        return [f for f in git_files if Path(f).suffix.lower() in _MD_EXTENSIONS]

    results = []
    if recursive:
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for f in files:
                if Path(f).suffix.lower() in _MD_EXTENSIONS:
                    results.append(os.path.join(root, f))
    else:
        for entry in os.scandir(directory):
            if entry.is_file() and Path(entry.name).suffix.lower() in _MD_EXTENSIONS:
                results.append(entry.path)
    return results


def _git_ls_files(directory):
    """Use git to list files respecting .gitignore. Returns None if not in a git repo."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=str(directory), capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return None
        files = []
        for line in result.stdout.strip().splitlines():
            if line:
                full = os.path.join(str(directory), line)
                if os.path.isfile(full):
                    files.append(full)
        return files
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def extract_title(md_content, filename):
    """Return the first H1 heading, or filename stem titlecased as fallback."""
    for line in md_content.splitlines():
        m = re.match(r"^#\s+(.+)", line)
        if m:
            return m.group(1).strip()
    stem = Path(filename).stem
    return stem.replace("-", " ").replace("_", " ").title()


def parse_selection(input_str, total):
    """Parse selection string like '1,3,5' or '2-4' or 'all' into zero-based indices."""
    input_str = input_str.strip().lower()
    if input_str == "all":
        return list(range(total))

    indices = []
    for part in input_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            for i in range(int(start) - 1, int(end)):
                if 0 <= i < total:
                    indices.append(i)
        else:
            idx = int(part) - 1
            if 0 <= idx < total:
                indices.append(idx)
    return sorted(set(indices))


def format_file_list(files):
    """Format files with extracted titles for display. Returns list of (path, title)."""
    entries = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                content = fh.read(1024)
        except OSError:
            content = ""
        title = extract_title(content, f)
        entries.append((f, title))
    return entries
