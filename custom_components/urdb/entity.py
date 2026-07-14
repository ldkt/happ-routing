"""Base entity shared by URDB platforms."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import URDBCoordinator


class URDBEntity(CoordinatorEntity[URDBCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: URDBCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="URDB",
            manufacturer="URDB",
            model="Routing Orchestrator",
            configuration_url=coordinator.client.base_url,
        )
