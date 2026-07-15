from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.urdb.const import DOMAIN
from custom_components.urdb.frontend import (
    CARD_URL,
    async_register_card,
    async_unregister_card,
)


pytestmark = pytest.mark.asyncio


async def test_card_is_registered_once_and_unregistered_after_last_entry() -> None:
    hass = MagicMock()
    hass.data = {}
    hass.http.async_register_static_paths = AsyncMock()

    with (
        patch("custom_components.urdb.frontend.frontend.add_extra_js_url") as add,
        patch("custom_components.urdb.frontend.frontend.remove_extra_js_url") as remove,
    ):
        await async_register_card(hass)
        await async_register_card(hass)

        hass.http.async_register_static_paths.assert_awaited_once()
        add.assert_called_once_with(hass, CARD_URL)

        async_unregister_card(hass)
        remove.assert_not_called()
        async_unregister_card(hass)
        remove.assert_called_once_with(hass, CARD_URL)

        await async_register_card(hass)
        hass.http.async_register_static_paths.assert_awaited_once()
        assert add.call_count == 2

    assert hass.data[DOMAIN]["card_users"] == 1


def test_card_asset_has_visual_editor_actions_progress_and_theme_support() -> None:
    source = (
        Path(__file__).parents[2]
        / "custom_components"
        / "urdb"
        / "frontend"
        / "urdb-card.js"
    ).read_text(encoding="utf-8")

    assert 'customElements.define("urdb-card"' in source
    assert 'customElements.define("urdb-card-editor"' in source
    assert "window.customCards.push" in source
    assert 'data-action="check"' in source
    assert 'data-action="update"' in source
    assert 'data-action="restart"' in source
    assert 'class="progress"' in source
    assert "--primary-text-color" in source
    assert "--ha-card-background" in source
