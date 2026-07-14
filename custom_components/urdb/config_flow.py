"""UI configuration flow for URDB."""

from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import URDBAPIClient, URDBAPIError
from .const import CONF_API_URL, DOMAIN


class URDBConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                api_url = _normalize_url(user_input[CONF_API_URL])
                await URDBAPIClient(
                    api_url, async_get_clientsession(self.hass)
                ).status()
            except ValueError:
                errors["base"] = "invalid_url"
            except URDBAPIError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(api_url.casefold())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="URDB", data={CONF_API_URL: api_url}
                )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_API_URL): str}
            ),
            errors=errors,
        )


def _normalize_url(value: str) -> str:
    parts = urlsplit(value.strip())
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        raise ValueError("URL must use HTTP or HTTPS")
    if parts.query or parts.fragment:
        raise ValueError("URL must not contain query or fragment")
    path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme, parts.netloc, path, "", ""))
