"""Tests for Confluence client."""

import json
from unittest.mock import patch, MagicMock
from md_to_adf.confluence.client import ConfluenceClient


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
        assert False, "Should have raised ValueError"
    except ValueError as e:
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
