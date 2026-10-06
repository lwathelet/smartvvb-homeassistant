"""Diagnostics support for SmartVVB."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import DOMAIN

TO_REDACT = {"token", CONF_USERNAME, "ssid", "ip", "mac"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    stored = hass.data[DOMAIN][entry.entry_id]
    coordinator = stored["coordinator"]
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "devices": {
            str(serial): {
                "name": stored["device_names"].get(serial),
                "instant_data": async_redact_data(data, TO_REDACT),
            }
            for serial, data in (coordinator.data or {}).items()
        },
    }
