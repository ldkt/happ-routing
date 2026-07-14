"""Constants for the URDB integration."""

from homeassistant.const import Platform

DOMAIN = "urdb"
CONF_API_URL = "api_url"
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]
DEFAULT_SCAN_INTERVAL = 60
