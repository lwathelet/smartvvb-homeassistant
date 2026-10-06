"""Number platform for SmartVVB (max energy per hour)."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SmartVVBApi, SmartVVBApiError
from .const import DOMAIN
from .coordinator import SmartVVBCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    stored = hass.data[DOMAIN][entry.entry_id]
    coordinator: SmartVVBCoordinator = stored["coordinator"]
    api: SmartVVBApi = stored["api"]
    device_names: dict[int, str] = stored["device_names"]

    async_add_entities(
        SmartVVBMaxEnergyNumber(api, serial, device_names[serial])
        for serial in coordinator.serials
    )


class SmartVVBMaxEnergyNumber(NumberEntity):
    """Caps the heater's power draw, uniformly across all 24 hours of the day.

    /SetMaxEnergy requires the full 24-hour table in every call — any hour
    left out gets reset to 0 by the backend — so this applies the chosen
    value to every hour rather than a single one (same reasoning as the
    Homey app's set-max-energy-per-hour flow action).

    Write-only: there's no field in GetDeviceInstantData exposing the current
    cap, so this just remembers the last value *this* integration set rather
    than reading it back from the backend.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "max_energy_per_hour"
    _attr_native_min_value = 0
    _attr_native_max_value = 3500
    _attr_native_step = 100
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_mode = NumberMode.BOX
    _attr_entity_registry_enabled_default = False

    def __init__(self, api: SmartVVBApi, serial: int, device_name: str) -> None:
        self._api = api
        self._serial = serial
        self._attr_unique_id = f"{serial}_max_energy_per_hour"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(serial))},
            name=device_name,
            manufacturer="Wattlet AS",
            model="SmartVVB",
        )
        self._attr_native_value: float | None = None

    async def async_set_native_value(self, value: float) -> None:
        try:
            await self._api.set_max_energy_per_hour(self._serial, int(value))
        except SmartVVBApiError as err:
            _LOGGER.error("Failed to set SmartVVB max energy per hour: %s", err)
            raise
        self._attr_native_value = value
        self.async_write_ha_state()
