"""Water heater platform for SmartVVB.

The setpoint comes from the heater's physical potentiometer, so it is shown as
the target temperature but cannot be changed: TARGET_TEMPERATURE is
deliberately left out of supported_features.
"""
from __future__ import annotations

import logging

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SmartVVBApi, SmartVVBApiError
from .const import DOMAIN, MODE_API_VALUES, MODE_HA_VALUES
from .coordinator import SmartVVBCoordinator
from .entity import SmartVVBEntity

_LOGGER = logging.getLogger(__name__)

# Away is exposed through away mode, not as an operation mode.
OPERATION_MODES = [mode for mode in MODE_API_VALUES if mode != "away"]
DEFAULT_RETURN_MODE = "auto"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    stored = hass.data[DOMAIN][entry.entry_id]
    coordinator: SmartVVBCoordinator = stored["coordinator"]
    async_add_entities(
        SmartVVBWaterHeater(coordinator, stored["api"], serial, stored["device_names"][serial])
        for serial in coordinator.serials
    )


class SmartVVBWaterHeater(SmartVVBEntity, WaterHeaterEntity):
    _attr_name = None
    _attr_translation_key = "water_heater"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_operation_list = OPERATION_MODES
    _attr_supported_features = (
        WaterHeaterEntityFeature.OPERATION_MODE | WaterHeaterEntityFeature.AWAY_MODE
    )

    def __init__(
        self, coordinator: SmartVVBCoordinator, api: SmartVVBApi, serial: int, device_name: str
    ) -> None:
        super().__init__(coordinator, serial, device_name)
        self._api = api
        self._attr_unique_id = f"{serial}_water_heater"
        # Mode to go back to when away mode is switched off.
        self._return_mode = DEFAULT_RETURN_MODE

    @property
    def _mode(self) -> str | None:
        return MODE_HA_VALUES.get(self.device_data.get("mode"))

    @property
    def current_temperature(self) -> float | None:
        return self.device_data.get("waterTemperatureEstimated")

    @property
    def target_temperature(self) -> float | None:
        return self.device_data.get("setpoint")

    @property
    def current_operation(self) -> str | None:
        mode = self._mode
        return self._return_mode if mode == "away" else mode

    @property
    def is_away_mode_on(self) -> bool:
        return self._mode == "away"

    def _handle_coordinator_update(self) -> None:
        mode = self._mode
        if mode in OPERATION_MODES and mode != "off":
            self._return_mode = mode
        super()._handle_coordinator_update()

    async def _set_mode(self, mode: str) -> None:
        try:
            await self._api.set_mode(self._serial, MODE_API_VALUES[mode])
        except SmartVVBApiError as err:
            _LOGGER.error("Failed to set SmartVVB mode: %s", err)
            raise
        await self.coordinator.async_request_refresh()

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        await self._set_mode(operation_mode)

    async def async_turn_away_mode_on(self) -> None:
        await self._set_mode("away")

    async def async_turn_away_mode_off(self) -> None:
        await self._set_mode(self._return_mode)
