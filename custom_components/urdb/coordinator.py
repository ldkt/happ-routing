"""Shared polling coordinator for URDB entities."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import URDBAPIClient, URDBAPIError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN


LOGGER = logging.getLogger(__name__)


class URDBCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, client: URDBAPIClient) -> None:
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            status = await self.client.status()
            changes = await self.client.changes()
        except URDBAPIError as error:
            raise UpdateFailed(str(error)) from error
        return {"status": status, "changes": changes}
