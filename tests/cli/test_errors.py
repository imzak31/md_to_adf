"""Tests for the typed error hierarchy."""

import pytest
from md_to_adf.cli.errors import (
    MdToAdfError,
    AuthError,
    NetworkError,
    NotFoundError,
    ValidationError,
    ConfigError,
    AccessError,
)


# --- MdToAdfError (base) ---

def test_base_error_message():
    err = MdToAdfError("something went wrong")
    assert err.message == "something went wrong"
    assert str(err) == "something went wrong"


def test_base_error_hint_default_none():
    err = MdToAdfError("oops")
    assert err.hint is None


def test_base_error_hint_set():
    err = MdToAdfError("oops", hint="try this")
    assert err.hint == "try this"


def test_base_error_is_exception():
    err = MdToAdfError("msg")
    assert isinstance(err, Exception)


# --- AuthError ---

def test_auth_error_message():
    err = AuthError("Authentication failed")
    assert err.message == "Authentication failed"
    assert str(err) == "Authentication failed"


def test_auth_error_hint():
    err = AuthError("Authentication failed", hint="Check your API token")
    assert err.hint == "Check your API token"


def test_auth_error_isinstance():
    err = AuthError("Authentication failed")
    assert isinstance(err, MdToAdfError)
    assert isinstance(err, AuthError)
    assert isinstance(err, Exception)


def test_auth_error_no_hint():
    err = AuthError("Authentication failed")
    assert err.hint is None


# --- NetworkError ---

def test_network_error_message():
    err = NetworkError("Rate limited by Confluence")
    assert err.message == "Rate limited by Confluence"
    assert str(err) == "Rate limited by Confluence"


def test_network_error_hint():
    err = NetworkError("Rate limited", hint="Wait a moment and try again")
    assert err.hint == "Wait a moment and try again"


def test_network_error_isinstance():
    err = NetworkError("timeout")
    assert isinstance(err, MdToAdfError)
    assert isinstance(err, NetworkError)
    assert isinstance(err, Exception)


# --- NotFoundError ---

def test_not_found_error_message():
    err = NotFoundError("Resource not found")
    assert err.message == "Resource not found"
    assert str(err) == "Resource not found"


def test_not_found_error_hint():
    err = NotFoundError("Resource not found", hint="Check the space key or page ID")
    assert err.hint == "Check the space key or page ID"


def test_not_found_error_isinstance():
    err = NotFoundError("Resource not found")
    assert isinstance(err, MdToAdfError)
    assert isinstance(err, NotFoundError)
    assert isinstance(err, Exception)


# --- ValidationError ---

def test_validation_error_message():
    err = ValidationError("ADF validation failed")
    assert err.message == "ADF validation failed"
    assert str(err) == "ADF validation failed"


def test_validation_error_hint():
    err = ValidationError("ADF validation failed", hint="Check node types")
    assert err.hint == "Check node types"


def test_validation_error_isinstance():
    err = ValidationError("ADF validation failed")
    assert isinstance(err, MdToAdfError)
    assert isinstance(err, ValidationError)
    assert isinstance(err, Exception)


# --- ConfigError ---

def test_config_error_message():
    err = ConfigError("Configuration file missing")
    assert err.message == "Configuration file missing"
    assert str(err) == "Configuration file missing"


def test_config_error_hint():
    err = ConfigError("Config missing", hint="Run md-to-adf init")
    assert err.hint == "Run md-to-adf init"


def test_config_error_isinstance():
    err = ConfigError("Config missing")
    assert isinstance(err, MdToAdfError)
    assert isinstance(err, ConfigError)
    assert isinstance(err, Exception)


# --- AccessError ---

def test_access_error_message():
    err = AccessError("Insufficient permissions")
    assert err.message == "Insufficient permissions"
    assert str(err) == "Insufficient permissions"


def test_access_error_hint():
    err = AccessError("Insufficient permissions", hint="Verify your token has write access")
    assert err.hint == "Verify your token has write access"


def test_access_error_isinstance():
    err = AccessError("Insufficient permissions")
    assert isinstance(err, MdToAdfError)
    assert isinstance(err, AccessError)
    assert isinstance(err, Exception)


# --- Cross-type isolation (errors are not siblings of each other) ---

def test_auth_error_not_network():
    err = AuthError("auth")
    assert not isinstance(err, NetworkError)


def test_network_error_not_auth():
    err = NetworkError("net")
    assert not isinstance(err, AuthError)


def test_not_found_not_access():
    err = NotFoundError("nf")
    assert not isinstance(err, AccessError)


# --- Raising and catching ---

def test_raise_and_catch_base():
    with pytest.raises(MdToAdfError) as exc_info:
        raise AuthError("bad token", hint="renew it")
    assert exc_info.value.hint == "renew it"


def test_raise_and_catch_specific():
    with pytest.raises(AuthError):
        raise AuthError("bad token")


def test_raise_config_error():
    with pytest.raises(ConfigError) as exc_info:
        raise ConfigError("no config", hint="run init")
    assert "no config" in str(exc_info.value)
    assert exc_info.value.hint == "run init"
