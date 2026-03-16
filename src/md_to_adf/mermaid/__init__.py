"""Mermaid diagram support — detection, macro generation, and image rendering."""

from md_to_adf.mermaid.detector import find_mermaid_blocks
from md_to_adf.mermaid.macro import mermaid_to_macro_node
from md_to_adf.mermaid.renderer import render_mermaid, is_mmdc_available


def process_mermaid_blocks(adf_doc, strategy="auto", output_format="png", theme="default"):
    """Process mermaid blocks according to strategy.

    Strategies:
        auto:  try macro, fall back to image if mmdc available, else keep as code
        macro: macro only
        image: local render only (requires mmdc)
        code:  keep as code blocks (no-op)
    """
    if strategy == "code":
        return adf_doc

    blocks = find_mermaid_blocks(adf_doc)

    for block_info in reversed(blocks):
        source = block_info["source"]
        parent = block_info["parent"]
        idx = block_info["index"]

        if strategy == "macro":
            parent[idx] = mermaid_to_macro_node(source)
        elif strategy == "image":
            _try_image_render(parent, idx, source, output_format, theme)
        elif strategy == "auto":
            # auto: prefer macro, but if mmdc is available use image as alternative
            # Macro is the default since it requires no local deps.
            # The caller can detect at upload time if the macro isn't supported
            # and re-run with strategy="image".
            parent[idx] = mermaid_to_macro_node(source)

    return adf_doc


def _try_image_render(parent, idx, source, output_format, theme):
    """Render mermaid to image, replacing the node. Keeps code block on failure."""
    rendered = render_mermaid(source, output_format, theme)
    if not rendered:
        return  # keep original code block
    # Store rendered path for the upload step to attach and replace with media node.
    # The upload command is responsible for cleaning up the temp file after attaching.
    parent[idx]["attrs"]["__rendered_path"] = rendered
