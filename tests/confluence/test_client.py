"""Tests for Confluence client."""

import json
import urllib.error
from unittest.mock import patch, MagicMock
from md_to_adf.confluence.client import ConfluenceClient
from md_to_adf.cli.errors import AuthError, AccessError, NotFoundError, NetworkError


def _mock_response(data, status=200):
    resp = MagicMock()
    resp.read.return_value = json.dumps(data).encode()
    resp.status = status
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def test_client_init():
    client = ConfluenceClient("test.atlassian.net", auth_header="Basic abc123")
    assert client.domain == "test.atlassian.net"


@patch("urllib.request.urlopen")
def test_get_space_id(mock_urlopen):
    mock_urlopen.return_value = _mock_response({
        "results": [{"id": "12345", "name": "Test Space"}]
    })
    client = ConfluenceClient("test.atlassian.net", auth_header="Basic abc")
    space_id = client.get_space_id("TS")
    assert space_id == "12345"


@patch("urllib.request.urlopen")
def test_get_space_id_not_found(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"results": []})
    client = ConfluenceClient("test.atlassian.net", auth_header="Basic abc")
    try:
        client.get_space_id("NOPE")
        assert False, "Should have raised NotFoundError"
    except NotFoundError as e:
        assert "not found" in str(e).lower()


@patch("urllib.request.urlopen")
def test_create_page(mock_urlopen):
    mock_urlopen.side_effect = [
        _mock_response({"results": [{"id": "100"}]}),
        _mock_response({"id": "999", "title": "My Page", "_links": {"webui": "/wiki/page"}}),
    ]
    client = ConfluenceClient("test.atlassian.net", auth_header="Basic abc")
    result = client.create_page(
        adf_doc={"version": 1, "type": "doc", "content": []},
        space_key="TS",
        title="My Page",
    )
    assert result["id"] == "999"


@patch("urllib.request.urlopen")
def test_update_page(mock_urlopen):
    mock_urlopen.side_effect = [
        _mock_response({"version": {"number": 3}}),
        _mock_response({"id": "999", "title": "Updated"}),
    ]
    client = ConfluenceClient("test.atlassian.net", auth_header="Basic abc")
    result = client.update_page(
        adf_doc={"version": 1, "type": "doc", "content": []},
        page_id="999",
        title="Updated",
    )
    assert result["title"] == "Updated"


# --- HTTP error mapping tests ---

def _make_http_error(code):
    """Create a urllib.error.HTTPError with the given status code."""
    import io
    return urllib.error.HTTPError(
        url="https://test.atlassian.net/wiki/api/v2/pages",
        code=code,
        msg=f"HTTP Error {code}",
        hdrs={},
        fp=io.BytesIO(b"error body"),
    )


@patch("urllib.request.urlopen")
def test_request_401_raises_auth_error(mock_urlopen):
    mock_urlopen.side_effect = _make_http_error(401)
    client = ConfluenceClient("test.atlassian.net", auth_header="Basic bad", max_retries=1)
    try:
        client._get("/wiki/api/v2/spaces?keys=TS")
        assert False, "Should have raised AuthError"
    except AuthError as e:
        assert "authentication failed" in e.message.lower()
        assert e.hint is not None


@patch("urllib.request.urlopen")
def test_request_403_raises_access_error(mock_urlopen):
    mock_urlopen.side_effect = _make_http_error(403)
    client = ConfluenceClient("test.atlassian.net", auth_header="Basic ok", max_retries=1)
    try:
        client._get("/wiki/api/v2/pages/123")
        assert False, "Should have raised AccessError"
    except AccessError as e:
        assert "permissions" in e.message.lower()
        assert e.hint is not None


@patch("urllib.request.urlopen")
def test_request_404_raises_not_found_error(mock_urlopen):
    mock_urlopen.side_effect = _make_http_error(404)
    client = ConfluenceClient("test.atlassian.net", auth_header="Basic ok", max_retries=1)
    try:
        client._get("/wiki/api/v2/pages/999")
        assert False, "Should have raised NotFoundError"
    except NotFoundError as e:
        assert "not found" in e.message.lower()
        assert e.hint is not None


@patch("urllib.request.urlopen")
@patch("time.sleep")
def test_request_429_after_retries_raises_network_error(mock_sleep, mock_urlopen):
    mock_urlopen.side_effect = _make_http_error(429)
    client = ConfluenceClient("test.atlassian.net", auth_header="Basic ok", max_retries=2)
    try:
        client._get("/wiki/api/v2/spaces?keys=TS")
        assert False, "Should have raised NetworkError"
    except NetworkError as e:
        assert "rate limited" in e.message.lower()
        assert e.hint is not None


@patch("urllib.request.urlopen")
@patch("time.sleep")
def test_request_500_after_retries_raises_network_error(mock_sleep, mock_urlopen):
    mock_urlopen.side_effect = _make_http_error(500)
    client = ConfluenceClient("test.atlassian.net", auth_header="Basic ok", max_retries=2)
    try:
        client._get("/wiki/api/v2/spaces?keys=TS")
        assert False, "Should have raised NetworkError"
    except NetworkError as e:
        assert "500" in e.message
        assert e.hint is not None


@patch("urllib.request.urlopen")
def test_get_space_id_raises_not_found_error(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"results": []})
    client = ConfluenceClient("test.atlassian.net", auth_header="Basic abc")
    try:
        client.get_space_id("MISSING")
        assert False, "Should have raised NotFoundError"
    except NotFoundError as e:
        assert "MISSING" in e.message
        assert e.hint is not None
