"""The SmartVVB integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    HomeAssistantError,
)
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

from .api import SmartVVBApi, SmartVVBApiError, SmartVVBAuthError
from .const import DOMAIN
from .coordinator import SmartVVBCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.WATER_HEATER,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SERVICE_SET_MAX_ENERGY_SCHEDULE = "set_max_energy_schedule"
SET_MAX_ENERGY_SCHEDULE_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
        vol.Required("hours"): vol.All(
            [vol.All(vol.Coerce(int), vol.Range(min=0, max=3500))],
            vol.Length(min=24, max=24),
        ),
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    async def handle_set_max_energy_schedule(call: ServiceCall) -> None:
        device = dr.async_get(hass).async_get(call.data["device_id"])
        if device is None:
            raise HomeAssistantError("Unknown device")
        serial = next(
            (int(ident) for domain, ident in device.identifiers if domain == DOMAIN), None
        )
        for entry_id in device.config_entries:
            stored = hass.data.get(DOMAIN, {}).get(entry_id)
            if stored and serial in stored["coordinator"].serials:
                try:
                    await stored["api"].set_max_energy_schedule(serial, call.data["hours"])
                except SmartVVBApiError as err:
                    raise HomeAssistantError(f"Failed to set schedule: {err}") from err
                return
        raise HomeAssistantError("Device is not a loaded SmartVVB device")

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_MAX_ENERGY_SCHEDULE,
        handle_set_max_energy_schedule,
        schema=SET_MAX_ENERGY_SCHEDULE_SCHEMA,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Versions up to 0.3.0 stored webhook keys in the entry; updates are now
    # polling only, so drop them.
    if any(key.startswith("webhook_") for key in entry.data):
        hass.config_entries.async_update_entry(
            entry,
            data={k: v for k, v in entry.data.items() if not k.startswith("webhook_")},
        )

    session = aiohttp_client.async_get_clientsession(hass)
    api = SmartVVBApi(session)
    api.restore_session(entry.data["token"], entry.data[CONF_USERNAME])

    try:
        devices = await api.get_devices()
    except SmartVVBAuthError as err:
        raise ConfigEntryAuthFailed from err
    except SmartVVBApiError as err:
        raise ConfigEntryNotReady(f"Error communicating with SmartVVB: {err}") from err

    device_names = {device["serial"]: device["name"] for device in devices}

    coordinator = SmartVVBCoordinator(hass, api, devices)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "device_names": device_names,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
