"""DataUpdateCoordinator for SmartVVB."""
from __future__ import annotations

from datetime import timedelta
import logging
import time

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SmartVVBApi, SmartVVBApiError
from .const import DEVICE_LIST_REFRESH_SECONDS, DOMAIN, POLL_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class SmartVVBCoordinator(DataUpdateCoordinator[dict[int, dict]]):
    """Polls GetDeviceInstantData for every device on one SmartVVB account.

    Each poll is a full refresh (data[serial] is replaced outright, matching
    what the REST endpoint returns — every field, always).
    """

    def __init__(self, hass: HomeAssistant, api: SmartVVBApi, devices: list[dict]) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=POLL_INTERVAL_SECONDS),
        )
        self.api = api
        self.serials = [device["serial"] for device in devices]
        self._devices = {device["serial"]: device for device in devices}
        self._devices_fetched_at = time.monotonic()

    async def _async_update_data(self) -> dict[int, dict]:
        data: dict[int, dict] = {}
        try:
            if time.monotonic() - self._devices_fetched_at > DEVICE_LIST_REFRESH_SECONDS:
                self._devices = {
                    device["serial"]: device for device in await self.api.get_devices()
                }
                self._devices_fetched_at = time.monotonic()
            for serial in self.serials:
                data[serial] = await self.api.get_instant_data(serial)
                # setpoint/volume only come from GetUserDevices, so merge them in.
                device = self._devices.get(serial, {})
                for key in ("setpoint", "volume"):
                    if device.get(key) is not None:
                        data[serial][key] = device[key]
                _LOGGER.debug("SmartVVB poll %s: %s", serial, data[serial])
        except SmartVVBApiError as err:
            raise UpdateFailed(f"Error fetching SmartVVB data: {err}") from err
        return data
