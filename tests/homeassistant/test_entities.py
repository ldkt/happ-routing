from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.urdb.const import CONF_API_URL, DOMAIN


pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.usefixtures("enable_custom_integrations"),
]


STATUS = {
    "current_version": "routing-1",
    "latest_version": "routing-2",
    "has_update": True,
    "changes": ["YouTube"],
    "checked_at": "2026-07-15T00:00:00Z",
    "health": "ok",
}
CHANGES = {"version": "routing-2", "changes": ["YouTube"]}


async def test_config_entry_creates_all_entities_on_one_device(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="URDB",
        unique_id="http://urdb.example",
        data={CONF_API_URL: "http://urdb.example"},
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.urdb.api.URDBAPIClient.status",
            new=AsyncMock(return_value=STATUS),
        ),
        patch(
            "custom_components.urdb.api.URDBAPIClient.changes",
            new=AsyncMock(return_value=CHANGES),
        ),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    expected_entity_ids = {
        "sensor.urdb_status",
        "sensor.urdb_changes",
        "button.check",
        "button.update",
        "button.restart",
    }
    assert expected_entity_ids <= set(hass.states.async_entity_ids())

    entity_registry = er.async_get(hass)
    entries = {
        entity_id: entity_registry.async_get(entity_id)
        for entity_id in expected_entity_ids
    }
    assert all(registry_entry is not None for registry_entry in entries.values())
    device_ids = {registry_entry.device_id for registry_entry in entries.values()}
    assert len(device_ids) == 1
    device_id = device_ids.pop()
    assert device_id is not None

    device = dr.async_get(hass).async_get(device_id)
    assert device is not None
    assert device.name == "URDB"
    assert (DOMAIN, entry.entry_id) in device.identifiers
