"""Internal client for the privileged updater sidecar."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class UpdaterClientError(RuntimeError):
    """Raised when the updater sidecar rejects or cannot accept an operation."""


class UpdaterClient:
    def __init__(self, base_url: str, token: str, *, timeout: float = 5.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout

    def update(self) -> dict[str, object]:
        return self._post("/update")

    def restart(self) -> dict[str, object]:
        return self._post("/restart")

    def _post(self, path: str) -> dict[str, object]:
        request = Request(
            self._base_url + path,
            method="POST",
            headers={"Authorization": f"Bearer {self._token}"},
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                payload = json.load(response)
        except (HTTPError, URLError, OSError, ValueError) as error:
            raise UpdaterClientError(f"updater request failed: {error}") from error
        if not isinstance(payload, dict):
            raise UpdaterClientError("updater returned an invalid response")
        return payload
