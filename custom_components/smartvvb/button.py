"""Button platform for SmartVVB (force on / force off)."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SmartVVBApi, SmartVVBApiError
from .const import DOMAIN, FORCE_OFF, FORCE_ON
from .coordinator import SmartVVBCoordinator

_LOGGER = logging.getLogger(__name__)

BUTTON_DESCRIPTIONS = (
    ButtonEntityDescription(key="force_on", translation_key="force_on", icon="mdi:power-plug"),
    ButtonEntityDescription(key="force_off", translation_key="force_off", icon="mdi:power-plug-off"),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    stored = hass.data[DOMAIN][entry.entry_id]
    coordinator: SmartVVBCoordinator = stored["coordinator"]
    api: SmartVVBApi = stored["api"]
    device_names: dict[int, str] = stored["device_names"]

    entities = [
        SmartVVBForceButton(api, serial, device_names[serial], description)
        for serial in coordinator.serials
        for description in BUTTON_DESCRIPTIONS
    ]
    async_add_entities(entities)


class SmartVVBForceButton(ButtonEntity):
    """Force the heater on or off.

    /ForceDevice is documented as "force device for 2 hours" — a temporary
    override on top of whatever mode is active, not a persistent on/off
    switch, which is why this is a button rather than a switch entity (same
    reasoning as the Homey app's smartvvb_force_on/off capabilities).
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        api: SmartVVBApi,
        serial: int,
        device_name: str,
        description: ButtonEntityDescription,
    ) -> None:
        self.entity_description = description
        self._api = api
        self._serial = serial
        self._attr_unique_id = f"{serial}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(serial))},
            name=device_name,
            manufacturer="Wattlet AS",
            model="SmartVVB",
        )

    async def async_press(self) -> None:
        state = FORCE_ON if self.entity_description.key == "force_on" else FORCE_OFF
        try:
            await self._api.force_device(self._serial, state)
        except SmartVVBApiError as err:
            _LOGGER.error("Failed to force SmartVVB %s: %s", state, err)
            raise
