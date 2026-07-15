from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components import frontend
from homeassistant.setup import async_setup_component

from custom_components.urdb.const import DOMAIN
import custom_components.urdb.frontend as urdb_frontend
from custom_components.urdb import async_setup
from custom_components.urdb.frontend import (
    CARD_URL,
    async_register_card,
)

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


@pytest.mark.asyncio
async def test_card_resource_is_loaded_and_served_by_home_assistant(
    hass, hass_client
) -> None:
    assert await async_setup_component(hass, DOMAIN, {})

    assert CARD_URL in hass.data[frontend.DATA_EXTRA_MODULE_URL].urls

    client = await hass_client()
    response = await client.get(CARD_URL)
    assert response.status == 200
    source = await response.text()
    assert 'customElements.define("urdb-card"' in source
    assert 'type: "urdb-card"' in source
    assert 'name: "Universal Routing Database"' in source


@pytest.mark.asyncio
async def test_integration_setup_registers_card_before_config_entries() -> None:
    hass = MagicMock()

    with patch(
        "custom_components.urdb.async_register_card", new=AsyncMock()
    ) as register:
        assert await async_setup(hass, {})

    register.assert_awaited_once_with(hass)


@pytest.mark.asyncio
async def test_card_is_registered_once_for_the_integration_lifetime() -> None:
    hass = MagicMock()
    hass.data = {frontend.DATA_EXTRA_MODULE_URL: MagicMock()}
    hass.http.async_register_static_paths = AsyncMock()

    with (
        patch("custom_components.urdb.frontend.frontend.add_extra_js_url") as add,
    ):
        await async_register_card(hass)
        await async_register_card(hass)

        hass.http.async_register_static_paths.assert_awaited_once()
        add.assert_called_once_with(hass, CARD_URL)

    assert hass.data[DOMAIN]["card_loaded"] is True


def test_card_asset_has_visual_editor_actions_progress_and_theme_support() -> None:
    source = (
        Path(urdb_frontend.__file__).parent
        / "frontend"
        / "src"
        / "urdb-card.js"
    ).read_text(encoding="utf-8")

    assert 'customElements.define("urdb-card"' in source
    assert 'customElements.define("urdb-card-editor"' in source
    assert "window.customCards.push" in source
    assert "class URDBCard extends LitElement" in source
    assert "class URDBCardEditor extends LitElement" in source
    assert "render()" in source
    assert "innerHTML" not in source
    assert 'button.check' in source
    assert 'button.update' in source
    assert 'button.restart' in source
    assert '@click=${() => this._run(action)}' in source
    assert 'class="progress"' in source
    assert "INTEGRATION_VERSION" in source
    assert "rate_limited" in source
    assert "ha-linear-progress" in source
    assert "System is up to date" in source
    assert "--primary-text-color" in source
    assert "--ha-card-background" in source
