"""Tests for Confluence authentication."""

import base64
from md_to_adf.confluence.auth import build_token_auth_header, AuthMethod


def test_build_token_auth_header():
    header = build_token_auth_header("user@example.com", "my-token")
    expected = base64.b64encode(b"user@example.com:my-token").decode()
    assert header == f"Basic {expected}"


def test_auth_method_enum():
    assert AuthMethod.TOKEN.value == "token"
    assert AuthMethod.OAUTH.value == "oauth"
