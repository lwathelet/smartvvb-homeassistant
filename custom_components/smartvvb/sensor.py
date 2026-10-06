"""Sensor platform for SmartVVB."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfTemperature, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SmartVVBCoordinator


@dataclass(frozen=True, kw_only=True)
class SmartVVBSensorDescription(SensorEntityDescription):
    """Adds a value_fn to pull this sensor's value out of the instant-data dict."""

    value_fn: Callable[[dict], object] = lambda data: None


# GetDeviceInstantData's field names on the left, matched against the same
# fields the Homey app (device.js's applyInstantData) reads.
SENSOR_DESCRIPTIONS: tuple[SmartVVBSensorDescription, ...] = (
    SmartVVBSensorDescription(
        key="waterTemperatureEstimated",
        translation_key="water_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("waterTemperatureEstimated"),
    ),
    SmartVVBSensorDescription(
        key="power",
        translation_key="power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("power"),
    ),
    SmartVVBSensorDescription(
        key="dayEnergy",
        translation_key="day_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.get("dayEnergy"),
    ),
    SmartVVBSensorDescription(
        key="rssi",
        translation_key="signal_strength",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement="dBm",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("rssi"),
    ),
    SmartVVBSensorDescription(
        key="dayCost",
        translation_key="day_cost",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="NOK",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("dayCost"),
    ),
    SmartVVBSensorDescription(
        key="waterAvailable",
        translation_key="water_available",
        icon="mdi:water",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("waterAvailable"),
    ),
    SmartVVBSensorDescription(
        key="waterConsumption",
        translation_key="water_used_today",
        icon="mdi:shower",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.get("waterConsumption"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    stored = hass.data[DOMAIN][entry.entry_id]
    coordinator: SmartVVBCoordinator = stored["coordinator"]
    device_names: dict[int, str] = stored["device_names"]

    entities = [
        SmartVVBSensor(coordinator, serial, device_names[serial], description)
        for serial in coordinator.serials
        for description in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)


class SmartVVBSensor(CoordinatorEntity[SmartVVBCoordinator], SensorEntity):
    """A single SmartVVB instant-data field, for one device."""

    entity_description: SmartVVBSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SmartVVBCoordinator,
        serial: int,
        device_name: str,
        description: SmartVVBSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._serial = serial
        self._attr_unique_id = f"{serial}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(serial))},
            name=device_name,
            manufacturer="Wattlet AS",
            model="SmartVVB",
        )

    @property
    def native_value(self):
        data = self.coordinator.data.get(self._serial, {})
        return self.entity_description.value_fn(data)
