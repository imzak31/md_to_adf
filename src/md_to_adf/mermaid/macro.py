"""Generate Confluence Mermaid macro ADF nodes."""


def mermaid_to_macro_node(source):
    return {
        "type": "bodiedExtension",
        "attrs": {
            "extensionType": "com.atlassian.confluence.macro.core",
            "extensionKey": "mermaid",
            "layout": "default",
        },
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": source}],
            }
        ],
    }
