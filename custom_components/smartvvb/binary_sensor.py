"""Binary sensor platform for SmartVVB."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SmartVVBCoordinator
from .entity import SmartVVBEntity


@dataclass(frozen=True, kw_only=True)
class SmartVVBBinarySensorDescription(BinarySensorEntityDescription):
    is_on_fn: Callable[[dict], bool | None]


def _heating(data: dict) -> bool | None:
    try:
        return float(data["power"]) > 0
    except (KeyError, TypeError, ValueError):
        return None


def _water_unsafe(data: dict) -> bool | None:
    # SAFETY device class: on means unsafe. "Unknown" stays unknown.
    safe = data.get("waterSafe")
    if safe not in ("Yes", "No"):
        return None
    return safe == "No"


BINARY_SENSOR_DESCRIPTIONS: tuple[SmartVVBBinarySensorDescription, ...] = (
    SmartVVBBinarySensorDescription(
        key="heating",
        translation_key="heating",
        # No device class: HEAT would show "Hot"/"Normal"; this shows On/Off.
        icon="mdi:fire",
        is_on_fn=_heating,
    ),
    SmartVVBBinarySensorDescription(
        key="water_safety",
        translation_key="water_safety",
        device_class=BinarySensorDeviceClass.SAFETY,
        is_on_fn=_water_unsafe,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    stored = hass.data[DOMAIN][entry.entry_id]
    coordinator: SmartVVBCoordinator = stored["coordinator"]
    async_add_entities(
        SmartVVBBinarySensor(coordinator, serial, stored["device_names"][serial], description)
        for serial in coordinator.serials
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class SmartVVBBinarySensor(SmartVVBEntity, BinarySensorEntity):
    entity_description: SmartVVBBinarySensorDescription

    def __init__(
        self,
        coordinator: SmartVVBCoordinator,
        serial: int,
        device_name: str,
        description: SmartVVBBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator, serial, device_name)
        self.entity_description = description
        self._attr_unique_id = f"{serial}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.is_on_fn(self.device_data)
