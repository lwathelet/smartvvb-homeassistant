"""Shared base entity for SmartVVB."""
from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SmartVVBCoordinator


class SmartVVBEntity(CoordinatorEntity[SmartVVBCoordinator]):
    """One entity on one SmartVVB device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SmartVVBCoordinator, serial: int, device_name: str) -> None:
        super().__init__(coordinator)
        self._serial = serial
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(serial))},
            name=device_name,
            manufacturer="Wattlet AS",
            model="SmartVVB",
        )

    @property
    def device_data(self) -> dict:
        return self.coordinator.data.get(self._serial, {})
