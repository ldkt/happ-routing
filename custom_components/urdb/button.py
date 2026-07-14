"""URDB lifecycle action buttons."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.exceptions import HomeAssistantError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import URDBConfigEntry
from .api import URDBAPIError
from .entity import URDBEntity


@dataclass(frozen=True, kw_only=True)
class URDBButtonDescription(ButtonEntityDescription):
    action: str


BUTTONS = (
    URDBButtonDescription(
        key="check",
        translation_key="check_updates",
        icon="mdi:refresh",
        action="check",
    ),
    URDBButtonDescription(
        key="update", translation_key="update", icon="mdi:download", action="update"
    ),
    URDBButtonDescription(
        key="restart", translation_key="restart", icon="mdi:restart", action="restart"
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: URDBConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([
        URDBButton(entry.runtime_data, entry.entry_id, description)
        for description in BUTTONS
    ])


class URDBButton(URDBEntity, ButtonEntity):
    entity_description: URDBButtonDescription

    def __init__(
        self, coordinator, entry_id: str, description: URDBButtonDescription
    ) -> None:
        super().__init__(coordinator, entry_id)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_suggested_object_id = description.key

    async def async_press(self) -> None:
        action: Callable[[], Awaitable[dict]] = getattr(
            self.coordinator.client, self.entity_description.action
        )
        try:
            await action()
        except URDBAPIError as error:
            raise HomeAssistantError(
                f"URDB {self.entity_description.action} request failed"
            ) from error
        if self.entity_description.action == "check":
            await self.coordinator.async_request_refresh()
