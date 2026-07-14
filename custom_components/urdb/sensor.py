"""URDB status and release-change sensors."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import URDBConfigEntry
from .entity import URDBEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: URDBConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(
        [
            URDBStatusSensor(entry.runtime_data, entry.entry_id),
            URDBChangesSensor(entry.runtime_data, entry.entry_id),
        ]
    )


class URDBStatusSensor(URDBEntity, SensorEntity):
    _attr_translation_key = "status"
    _attr_icon = "mdi:routes"

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_status"
        self._attr_suggested_object_id = "urdb_status"

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data["status"].get("health")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            key: value
            for key, value in self.coordinator.data["status"].items()
            if key != "health"
        }


class URDBChangesSensor(URDBEntity, SensorEntity):
    _attr_translation_key = "changes"
    _attr_icon = "mdi:format-list-bulleted"

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_changes"
        self._attr_suggested_object_id = "urdb_changes"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data["changes"].get("changes", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.coordinator.data["changes"]
