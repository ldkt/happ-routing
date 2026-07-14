"""Async client for the URDB HTTP API."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientSession


class URDBAPIError(RuntimeError):
    """Raised when the URDB API is unavailable or returns invalid data."""


class URDBAPIClient:
    def __init__(self, base_url: str, session: ClientSession) -> None:
        self.base_url = base_url.rstrip("/")
        self._session = session

    async def status(self) -> dict[str, Any]:
        data = await self._request("GET", "/api/status")
        if data.get("health") != "ok":
            raise URDBAPIError("URDB API health is not ok")
        return data

    async def changes(self) -> dict[str, Any]:
        return await self._request("GET", "/api/changes")

    async def check(self) -> dict[str, Any]:
        return await self._request("POST", "/api/check")

    async def update(self) -> dict[str, Any]:
        return await self._request("POST", "/api/update")

    async def restart(self) -> dict[str, Any]:
        return await self._request("POST", "/api/restart")

    async def _request(self, method: str, path: str) -> dict[str, Any]:
        try:
            async with self._session.request(
                method, f"{self.base_url}{path}", timeout=30
            ) as response:
                response.raise_for_status()
                data = await response.json()
        except (ClientError, TimeoutError, ValueError) as error:
            raise URDBAPIError(f"URDB request failed: {error}") from error
        if not isinstance(data, dict):
            raise URDBAPIError("URDB returned a non-object response")
        return data
