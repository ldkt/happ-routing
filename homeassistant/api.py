"""Build the Home Assistant-facing URDB status response."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Callable, Protocol


LOGGER = logging.getLogger("urdb.homeassistant")


class ReleaseClient(Protocol):
    """Minimal Orchestrator contract required by the status API."""

    def check_updates(self) -> dict[str, object]: ...

    def get_release_info(self) -> dict[str, object]: ...


class UpdateController(Protocol):
    """Privileged operations delegated to the updater sidecar."""

    def update(self) -> dict[str, object]: ...

    def restart(self) -> dict[str, object]: ...


class StatusAPIError(RuntimeError):
    """Raised when Orchestrator data cannot form a consistent status."""


class StatusService:
    """Translate read-only Orchestrator data into the REST status model."""

    def __init__(
        self,
        client: ReleaseClient,
        *,
        clock: Callable[[], datetime] | None = None,
        updater: UpdateController | None = None,
    ) -> None:
        self._client = client
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._updater = updater

    def get_status(self) -> dict[str, object]:
        update = self._client.check_updates()
        current_version = _string(update, "current_version")
        latest_version = _string(update, "latest_version")
        has_update = update.get("has_update")
        if not isinstance(has_update, bool):
            raise StatusAPIError("Orchestrator returned invalid has_update")

        changes: list[str] = []
        if has_update:
            release = self._client.get_release_info()
            if _string(release, "version") != latest_version:
                raise StatusAPIError("Orchestrator release changed during status check")
            notes = release.get("notes")
            if not isinstance(notes, str):
                raise StatusAPIError("Orchestrator returned invalid release notes")
            changes = extract_changes(notes)

        checked_at = self._clock()
        if checked_at.tzinfo is None:
            raise StatusAPIError("status clock must return a timezone-aware datetime")
        return {
            "current_version": current_version,
            "latest_version": latest_version,
            "has_update": has_update,
            "changes": changes,
            "checked_at": checked_at.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "health": "ok",
        }

    def get_changes(self) -> dict[str, object]:
        """Return changes from the latest release's explicit changes section."""

        release = self._client.get_release_info()
        version = _string(release, "version")
        notes = release.get("notes")
        if not isinstance(notes, str):
            raise StatusAPIError("Orchestrator returned invalid release notes")
        return {"version": version, "changes": extract_changes(notes)}

    def check_now(self) -> dict[str, object]:
        """Run an immediate release check and return the existing status model."""

        return self.get_status()

    def request_update(self) -> dict[str, object]:
        """Check for a release and delegate the safe rollout to the sidecar."""

        update = self._client.check_updates()
        current_version = _string(update, "current_version")
        latest_version = _string(update, "latest_version")
        has_update = update.get("has_update")
        if not isinstance(has_update, bool):
            raise StatusAPIError("Orchestrator returned invalid has_update")
        LOGGER.info(
            "Update requested: current_version=%s latest_version=%s has_update=%s",
            current_version,
            latest_version,
            has_update,
        )
        if not has_update:
            return {"accepted": True, "message": "Already up to date"}
        if self._updater is None:
            raise StatusAPIError("updater is not configured")
        return self._updater.update()

    def request_restart(self) -> dict[str, object]:
        """Delegate an API-container restart to the sidecar."""

        if self._updater is None:
            raise StatusAPIError("updater is not configured")
        LOGGER.info("Container restart requested")
        return self._updater.restart()


def extract_changes(notes: str) -> list[str]:
    """Extract bullet items from an explicit Changes release-note section."""

    changes: list[str] = []
    in_changes = False
    for raw_line in notes.splitlines():
        line = raw_line.strip()
        if line.startswith("#"):
            heading = line.lstrip("#").strip().casefold()
            in_changes = heading in {"changes", "изменения"}
            continue
        if not in_changes or not line:
            continue
        if line.startswith(("- ", "* ")):
            value = line[2:].strip()
            if value and value not in changes:
                changes.append(value)
    return changes


def _string(value: dict[str, object], field: str) -> str:
    result = value.get(field)
    if not isinstance(result, str) or not result:
        raise StatusAPIError(f"Orchestrator returned invalid {field}")
    return result
