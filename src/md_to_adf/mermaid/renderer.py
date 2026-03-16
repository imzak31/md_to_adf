"""Render mermaid diagrams to images using mermaid-cli (mmdc)."""

import os
import shutil
import subprocess
import tempfile


def is_mmdc_available():
    return shutil.which("mmdc") is not None


def render_mermaid(source, output_format="png", theme="default"):
    if not is_mmdc_available():
        return None

    with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as src_file:
        src_file.write(source)
        src_path = src_file.name

    out_path = src_path.replace(".mmd", f".{output_format}")

    try:
        cmd = ["mmdc", "-i", src_path, "-o", out_path, "-t", theme, "-b", "transparent"]
        subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        return out_path if os.path.exists(out_path) else None
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return None
    finally:
        if os.path.exists(src_path):
            os.unlink(src_path)
