"""Diagnostics support for URDB config entries."""

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import URDBConfigEntry
from .const import CONF_API_URL


TO_REDACT = {CONF_API_URL}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: URDBConfigEntry
) -> dict:
    return {
        "config_entry": async_redact_data(dict(entry.data), TO_REDACT),
        "coordinator": entry.runtime_data.data,
    }
