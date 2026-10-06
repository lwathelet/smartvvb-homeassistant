"""Select platform for SmartVVB (operating mode)."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import SmartVVBApi, SmartVVBApiError
from .const import DOMAIN, MODE_API_VALUES, MODE_HA_VALUES
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
        SmartVVBModeSelect(coordinator, api, serial, device_names[serial])
        for serial in coordinator.serials
    )


class SmartVVBModeSelect(CoordinatorEntity[SmartVVBCoordinator], SelectEntity):
    """Operating mode: Off / Away / Economy / Standard / Comfort / Auto / Always on.

    Unlike the Homey app's picker capability, a plain HA select only fires
    async_select_option() on a genuine user choice — there's no equivalent of
    the wheel-picker "opens and fires a phantom first value" quirk that
    device.js works around on the Homey side, so that mitigation isn't needed
    here.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "mode"
    _attr_options = list(MODE_API_VALUES.keys())

    def __init__(
        self,
        coordinator: SmartVVBCoordinator,
        api: SmartVVBApi,
        serial: int,
        device_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._api = api
        self._serial = serial
        self._attr_unique_id = f"{serial}_mode"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(serial))},
            name=device_name,
            manufacturer="Wattlet AS",
            model="SmartVVB",
        )

    @property
    def current_option(self) -> str | None:
        mode = self.coordinator.data.get(self._serial, {}).get("mode")
        return MODE_HA_VALUES.get(mode)

    async def async_select_option(self, option: str) -> None:
        api_mode = MODE_API_VALUES[option]
        try:
            await self._api.set_mode(self._serial, api_mode)
        except SmartVVBApiError as err:
            _LOGGER.error("Failed to set SmartVVB mode: %s", err)
            raise
        await self.coordinator.async_request_refresh()
