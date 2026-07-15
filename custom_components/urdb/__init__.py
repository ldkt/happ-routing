"""Universal Routing Database integration."""

from __future__ import annotations

from typing import TypeAlias

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import URDBAPIClient
from .const import CONF_API_URL, PLATFORMS
from .coordinator import URDBCoordinator
from .frontend import async_register_card, async_unregister_card


URDBConfigEntry: TypeAlias = ConfigEntry[URDBCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: URDBConfigEntry) -> bool:
    client = URDBAPIClient(
        entry.data[CONF_API_URL], async_get_clientsession(hass)
    )
    coordinator = URDBCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()
    await async_register_card(hass)
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: URDBConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        async_unregister_card(hass)
    return unloaded
