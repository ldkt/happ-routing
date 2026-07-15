"""Read and download immutable URDB releases from GitHub."""

from __future__ import annotations

import json
import os
from pathlib import Path, PurePath
import shutil
import tempfile
import threading
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_REPOSITORY = "ldkt/happ-routing"
DEFAULT_CURRENT_VERSION = "development"
DEFAULT_CACHE_TTL = 600.0


class OrchestratorError(RuntimeError):
    """Raised when release metadata or an asset cannot be retrieved safely."""


class GitHubRequestError(OrchestratorError):
    """Raised when GitHub cannot currently serve a request."""

    def __init__(self, message: str, *, status: str = "unavailable") -> None:
        super().__init__(message)
        self.github_status = status


class GitHubReleaseClient:
    """Read-only client for one repository's latest GitHub Release."""

    def __init__(
        self,
        repository: str = DEFAULT_REPOSITORY,
        current_version: str = DEFAULT_CURRENT_VERSION,
        *,
        token: str | None = None,
        opener: Callable[..., Any] = urlopen,
        clock: Callable[[], float] = time.monotonic,
        cache_ttl: float = DEFAULT_CACHE_TTL,
    ) -> None:
        if repository.count("/") != 1 or any(
            not part.strip() for part in repository.split("/")
        ):
            raise ValueError("repository must use owner/name format")
        if not current_version.strip():
            raise ValueError("current_version must not be empty")
        if cache_ttl <= 0:
            raise ValueError("cache_ttl must be positive")
        self.repository = repository
        self.current_version = current_version
        self._token = token if token is not None else token_from_environment()
        self._opener = opener
        self._clock = clock
        self._cache_ttl = cache_ttl
        self._release_cache: dict[str, Any] | None = None
        self._release_info_cache: dict[str, object] | None = None
        self._last_attempt_at: float | None = None
        self._last_error: OrchestratorError | None = None
        self._cache_lock = threading.RLock()

    def check_updates(self) -> dict[str, object]:
        """Return current/latest versions and whether they differ."""

        try:
            release = self._latest_release()
        except OrchestratorError as error:
            with self._cache_lock:
                release = self._release_cache
            latest = (
                _required_string(release, "tag_name") if release is not None else None
            )
            release_url = (
                _required_string(release, "html_url") if release is not None else None
            )
            return {
                "current_version": self.current_version,
                "latest_version": latest,
                "has_update": False,
                "release_url": release_url,
                "github_status": getattr(error, "github_status", "unavailable"),
                "github_error": str(error),
            }
        latest = _required_string(release, "tag_name")
        return {
            "current_version": self.current_version,
            "latest_version": latest,
            "has_update": self.current_version != latest,
            "release_url": _required_string(release, "html_url"),
        }

    def get_release_info(self) -> dict[str, object]:
        """Return normalized JSON-compatible metadata for the latest release."""

        release = self._latest_release()
        with self._cache_lock:
            if self._release_info_cache is not None:
                return dict(self._release_info_cache)
        assets = self._assets(release)
        checksum_asset = next(
            (asset for asset in assets if asset["name"] == "SHA256SUMS"), None
        )
        checksums: dict[str, str] = {}
        if checksum_asset is not None:
            content = self._request_bytes(str(checksum_asset["url"]))
            checksums = _parse_checksums(content.decode("utf-8"))
        result: dict[str, object] = {
            "version": _required_string(release, "tag_name"),
            "date": _required_string(release, "published_at"),
            "artifacts": assets,
            "checksum": checksums,
            "notes": str(release.get("body") or ""),
        }
        with self._cache_lock:
            self._release_info_cache = result
        return dict(result)

    def get_release_changes(self) -> dict[str, object]:
        """Return release notes with the same resilient cache as update checks."""

        try:
            release = self._latest_release()
        except OrchestratorError as error:
            with self._cache_lock:
                release = self._release_cache
            return {
                "version": _optional_string(release, "tag_name"),
                "notes": str(release.get("body") or "") if release else "",
                "github_status": getattr(error, "github_status", "unavailable"),
                "github_error": str(error),
            }
        return {
            "version": _required_string(release, "tag_name"),
            "notes": str(release.get("body") or ""),
        }

    def download_release(self) -> Path:
        """Download latest release assets into a new temporary directory.

        The method never installs, extracts, executes, or moves downloaded files
        outside the returned temporary directory.
        """

        release = self._latest_release()
        assets = self._assets(release)
        destination = Path(tempfile.mkdtemp(prefix="urdb-release-"))
        try:
            seen: set[str] = set()
            for asset in assets:
                name = str(asset["name"])
                if not _safe_asset_name(name):
                    raise OrchestratorError(f"unsafe release asset name: {name!r}")
                if name in seen:
                    raise OrchestratorError(f"duplicate release asset name: {name}")
                seen.add(name)
                (destination / name).write_bytes(
                    self._request_bytes(str(asset["url"]))
                )
            return destination
        except Exception:
            shutil.rmtree(destination, ignore_errors=True)
            raise

    def _latest_release(self) -> dict[str, Any]:
        with self._cache_lock:
            now = self._clock()
            if (
                self._last_attempt_at is not None
                and now - self._last_attempt_at < self._cache_ttl
            ):
                if self._last_error is not None:
                    raise self._last_error
                if self._release_cache is None:
                    raise OrchestratorError("GitHub release cache is empty")
                return self._release_cache

            url = f"https://api.github.com/repos/{self.repository}/releases/latest"
            try:
                value = json.loads(self._request_bytes(url))
            except (json.JSONDecodeError, UnicodeDecodeError) as error:
                failure = OrchestratorError("GitHub returned invalid release JSON")
                self._last_attempt_at = now
                self._last_error = failure
                raise failure from error
            except OrchestratorError as error:
                self._last_attempt_at = now
                self._last_error = error
                raise
            if not isinstance(value, dict):
                failure = OrchestratorError(
                    "GitHub release response must be a JSON object"
                )
                self._last_attempt_at = now
                self._last_error = failure
                raise failure
            self._release_cache = value
            self._release_info_cache = None
            self._last_attempt_at = now
            self._last_error = None
            return value

    def _assets(self, release: dict[str, Any]) -> list[dict[str, object]]:
        raw_assets = release.get("assets")
        if not isinstance(raw_assets, list):
            raise OrchestratorError("GitHub release response lacks an assets list")
        assets: list[dict[str, object]] = []
        for raw in raw_assets:
            if not isinstance(raw, dict):
                raise OrchestratorError("GitHub release contains an invalid asset")
            name = _required_string(raw, "name")
            url = _required_string(raw, "browser_download_url")
            size = raw.get("size")
            if not isinstance(size, int) or isinstance(size, bool) or size < 0:
                raise OrchestratorError(f"release asset {name!r} has invalid size")
            assets.append({"name": name, "size": size, "url": url})
        return assets

    def _request_bytes(self, url: str) -> bytes:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "urdb-orchestrator",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        request = Request(url, headers=headers)
        try:
            with self._opener(request, timeout=30) as response:
                content = response.read()
        except HTTPError as error:
            rate_limited = error.code == 429 or (
                error.code == 403
                and (
                    "rate limit" in str(error).casefold()
                    or (error.headers or {}).get("X-RateLimit-Remaining") == "0"
                )
            )
            detail = (
                f"GitHub API {error.code} rate limit exceeded: {error.reason}"
                if rate_limited
                else str(error)
            )
            raise GitHubRequestError(
                f"cannot retrieve {url}: {detail}",
                status="rate_limited" if rate_limited else "unavailable",
            ) from error
        except (URLError, OSError) as error:
            raise GitHubRequestError(f"cannot retrieve {url}: {error}") from error
        if not isinstance(content, bytes):
            raise OrchestratorError(f"invalid response body from {url}")
        return content


def check_updates(
    current_version: str = DEFAULT_CURRENT_VERSION,
    repository: str = DEFAULT_REPOSITORY,
    *,
    token: str | None = None,
) -> dict[str, object]:
    """Convenience API for :meth:`GitHubReleaseClient.check_updates`."""

    return GitHubReleaseClient(repository, current_version, token=token).check_updates()


def get_release_info(
    repository: str = DEFAULT_REPOSITORY, *, token: str | None = None
) -> dict[str, object]:
    """Convenience API for :meth:`GitHubReleaseClient.get_release_info`."""

    return GitHubReleaseClient(repository, token=token).get_release_info()


def download_release(
    repository: str = DEFAULT_REPOSITORY, *, token: str | None = None
) -> Path:
    """Convenience API for :meth:`GitHubReleaseClient.download_release`."""

    return GitHubReleaseClient(repository, token=token).download_release()


def _required_string(mapping: dict[str, Any], field: str) -> str:
    value = mapping.get(field)
    if not isinstance(value, str) or not value.strip():
        raise OrchestratorError(f"GitHub release response lacks {field}")
    return value


def _optional_string(mapping: dict[str, Any] | None, field: str) -> str | None:
    if mapping is None:
        return None
    value = mapping.get(field)
    return value if isinstance(value, str) and value.strip() else None


def _parse_checksums(content: str) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for line_number, line in enumerate(content.splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            raise OrchestratorError(
                f"invalid SHA256SUMS entry on line {line_number}"
            )
        checksum, name = parts
        name = name.lstrip("*")
        if len(checksum) != 64 or any(
            character not in "0123456789abcdefABCDEF" for character in checksum
        ):
            raise OrchestratorError(
                f"invalid SHA256 digest on line {line_number}"
            )
        if not _safe_asset_name(name) or name in checksums:
            raise OrchestratorError(
                f"invalid SHA256SUMS filename on line {line_number}: {name!r}"
            )
        checksums[name] = checksum.lower()
    return checksums


def _safe_asset_name(name: str) -> bool:
    path = PurePath(name)
    return (
        bool(name)
        and "/" not in name
        and "\\" not in name
        and path.name == name
        and name not in {".", ".."}
    )


def token_from_environment() -> str | None:
    """Return a GitHub token without requiring it for public releases."""

    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
