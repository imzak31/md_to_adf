"""HTTP client for Confluence Cloud API."""

import json
import time
import urllib.request
import urllib.error

from md_to_adf.cli.errors import AuthError, AccessError, NotFoundError, NetworkError


class ConfluenceClient:
    """Confluence Cloud API client with v2/v1 fallback and retry."""

    def __init__(self, domain, auth_header, timeout=30, max_retries=3):
        self.domain = domain
        self.auth_header = auth_header
        self.timeout = timeout
        self.max_retries = max_retries
        self._headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(self, method, path, payload=None):
        """Make an HTTP request with retry for 429/5xx."""
        url = f"https://{self.domain}{path}"
        data = json.dumps(payload).encode("utf-8") if payload else None
        last_error = None

        for attempt in range(self.max_retries):
            req = urllib.request.Request(url, data=data, headers=self._headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode())
            except urllib.error.HTTPError as e:
                last_error = e
                if e.code == 429 or e.code >= 500:
                    time.sleep(2 ** attempt)
                    continue
                # Map non-retryable HTTP errors to typed exceptions immediately
                if e.code == 401:
                    raise AuthError(
                        "Authentication failed",
                        hint="Check your API token at ~/.md-to-adf/config.toml",
                    ) from e
                if e.code == 403:
                    raise AccessError(
                        "Insufficient permissions",
                        hint="Verify your token has write access to this space",
                    ) from e
                if e.code == 404:
                    raise NotFoundError(
                        "Resource not found",
                        hint="Check the space key or page ID",
                    ) from e
                raise

        # Retries exhausted — map retryable errors to typed exceptions
        if last_error.code == 429:
            raise NetworkError(
                "Rate limited by Confluence",
                hint="Wait a moment and try again",
            ) from last_error
        if last_error.code >= 500:
            raise NetworkError(
                f"Confluence server error ({last_error.code})",
                hint="Check status.atlassian.com",
            ) from last_error
        raise last_error

    def _get(self, path):
        return self._request("GET", path)

    def _post(self, path, payload):
        return self._request("POST", path, payload)

    def _put(self, path, payload):
        return self._request("PUT", path, payload)

    def get_space_id(self, space_key):
        """Get space ID from space key. Raises NotFoundError if not found."""
        data = self._get(f"/wiki/api/v2/spaces?keys={space_key}")
        if not data.get("results"):
            raise NotFoundError(
                f"Space '{space_key}' not found",
                hint="Check the space key or page ID",
            )
        return data["results"][0]["id"]

    def get_page(self, page_id):
        return self._get(f"/wiki/api/v2/pages/{page_id}")

    def create_page(self, adf_doc, space_key, title, parent_id=None):
        """Create a new Confluence page. Falls back to v1 API on v2 failure."""
        space_id = self.get_space_id(space_key)
        adf_string = json.dumps(adf_doc)

        payload = {
            "spaceId": space_id,
            "status": "current",
            "title": title,
            "body": {"representation": "atlas_doc_format", "value": adf_string},
        }
        if parent_id:
            payload["parentId"] = parent_id

        try:
            return self._post("/wiki/api/v2/pages", payload)
        except urllib.error.HTTPError as e:
            try:
                v2_error = e.read().decode()
            except Exception:
                v2_error = str(e)
            v2_code = e.code

            v1_payload = {
                "type": "page",
                "title": title,
                "space": {"key": space_key},
                "body": {
                    "atlas_doc_format": {
                        "value": adf_string,
                        "representation": "atlas_doc_format",
                    }
                },
            }
            try:
                return self._post("/wiki/rest/api/content", v1_payload)
            except (urllib.error.HTTPError, Exception) as e2:
                http_code = getattr(e2, "code", None)
                if http_code == 401:
                    raise AuthError(
                        "Authentication failed",
                        hint="Check your API token at ~/.md-to-adf/config.toml",
                    ) from e2
                if http_code == 403:
                    raise AccessError(
                        "Insufficient permissions",
                        hint="Verify your token has write access to this space",
                    ) from e2
                if http_code == 404:
                    raise NotFoundError(
                        "Resource not found",
                        hint="Check the space key or page ID",
                    ) from e2
                if http_code == 429:
                    raise NetworkError(
                        "Rate limited by Confluence",
                        hint="Wait a moment and try again",
                    ) from e2
                if http_code is not None and http_code >= 500:
                    raise NetworkError(
                        f"Confluence server error ({http_code})",
                        hint="Check status.atlassian.com",
                    ) from e2
                try:
                    v1_error = e2.read().decode() if hasattr(e2, "read") else str(e2)
                except Exception:
                    v1_error = str(e2)
                raise NetworkError(
                    f"Both APIs failed (v2={v2_code}): {v1_error}",
                    hint="Check status.atlassian.com",
                ) from e2

    def update_page(self, adf_doc, page_id, title):
        current = self._get(f"/wiki/api/v2/pages/{page_id}")
        version = current["version"]["number"]
        adf_string = json.dumps(adf_doc)

        payload = {
            "id": page_id,
            "status": "current",
            "title": title,
            "body": {"representation": "atlas_doc_format", "value": adf_string},
            "version": {"number": version + 1, "message": "Updated via md-to-adf"},
        }
        return self._put(f"/wiki/api/v2/pages/{page_id}", payload)

    def list_spaces(self, limit=25):
        return self._get(f"/wiki/api/v2/spaces?limit={limit}")

    def attach_file(self, page_id, file_path, filename, content_type="image/png"):
        """Upload a file attachment to a page."""
        boundary = "----md-to-adf-boundary"
        with open(file_path, "rb") as f:
            file_data = f.read()

        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()

        headers = {
            "Authorization": self.auth_header,
            "X-Atlassian-Token": "nocheck",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }
        url = f"https://{self.domain}/wiki/rest/api/content/{page_id}/child/attachment"
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode())
