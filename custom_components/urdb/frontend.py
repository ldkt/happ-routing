"""Register the URDB Lovelace card with the Home Assistant frontend."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN

CARD_URL = "/urdb/frontend/urdb-card.js"
_CARD_PATH = Path(__file__).parent / "frontend" / "urdb-card.js"
_DATA_STATIC_REGISTERED = "card_static_registered"
_DATA_CARD_LOADED = "card_loaded"


async def async_register_card(hass: HomeAssistant) -> None:
    """Serve and load the URDB dashboard card once."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if not domain_data.get(_DATA_STATIC_REGISTERED):
        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_URL, str(_CARD_PATH), False)]
        )
        domain_data[_DATA_STATIC_REGISTERED] = True
    # Headless test and recovery environments may run without the frontend.
    # In normal Home Assistant installations, after_dependencies guarantees
    # frontend has had the opportunity to initialize before URDB.
    if frontend.DATA_EXTRA_MODULE_URL not in hass.data:
        return
    if not domain_data.get(_DATA_CARD_LOADED):
        frontend.add_extra_js_url(hass, CARD_URL)
        domain_data[_DATA_CARD_LOADED] = True
