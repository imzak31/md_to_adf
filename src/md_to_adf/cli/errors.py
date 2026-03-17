"""Typed error hierarchy for clean CLI error messages."""


class MdToAdfError(Exception):
    """Base error with user-friendly message and optional hint."""
    def __init__(self, message, hint=None):
        super().__init__(message)
        self.message = message
        self.hint = hint


class AuthError(MdToAdfError):
    """Authentication failed (401)."""
    pass

class NetworkError(MdToAdfError):
    """Network or server error (timeout, DNS, 429, 5xx)."""
    pass

class NotFoundError(MdToAdfError):
    """Resource not found (404, missing space/page)."""
    pass

class ValidationError(MdToAdfError):
    """ADF validation failures."""
    pass

class ConfigError(MdToAdfError):
    """Configuration file missing or malformed."""
    pass

class AccessError(MdToAdfError):
    """Insufficient permissions (403)."""
    pass
