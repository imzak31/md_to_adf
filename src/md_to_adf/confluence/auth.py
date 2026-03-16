"""Authentication methods for Confluence Cloud."""

import base64
from enum import Enum


class AuthMethod(Enum):
    TOKEN = "token"
    OAUTH = "oauth"


def build_token_auth_header(email, token):
    """Build Basic auth header from email + API token."""
    creds = base64.b64encode(f"{email}:{token}".encode()).decode()
    return f"Basic {creds}"
