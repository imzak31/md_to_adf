"""Detect mermaid code blocks in ADF documents."""


def find_mermaid_blocks(adf_doc):
    results = []
    _walk(adf_doc.get("content", []), results)
    return results


def _walk(nodes, results):
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            continue
        if (node.get("type") == "codeBlock"
                and node.get("attrs", {}).get("language") == "mermaid"):
            source = ""
            for content_node in node.get("content", []):
                if content_node.get("type") == "text":
                    source += content_node.get("text", "")
            results.append({"index": i, "parent": nodes, "source": source})
        if "content" in node:
            _walk(node["content"], results)
