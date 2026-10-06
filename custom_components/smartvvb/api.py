"""Async client for the SmartVVB REST API."""
from __future__ import annotations

import json
import logging
from typing import Any

import aiohttp

from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)


class SmartVVBApiError(Exception):
    """Raised when the SmartVVB API returns an error or is unreachable."""


class SmartVVBAuthError(SmartVVBApiError):
    """Raised when authentication fails or a token is required but missing."""


class SmartVVBApi:
    """Thin async wrapper around the SmartVVB REST API.

    Mirrors lib/SmartVVBApi.js from the SmartVVB Homey app, so behaviour
    (endpoints, payload shapes, error handling) stays consistent between the
    two integrations.
    """

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self.token: str | None = None
        self.username: str | None = None

    def restore_session(self, token: str, username: str) -> None:
        """Restore a previously obtained (non-expiring) token."""
        self.token = token
        self.username = username

    async def login(self, username: str, password: str) -> dict[str, Any]:
        """Log in and store the resulting bearer token."""
        response = await self._request(
            "POST",
            "/GetToken",
            json_body={"username": username, "password": password},
            authenticated=False,
        )
        token = (
            response.get("token")
            or response.get("accessToken")
            or response.get("access_token")
            or response.get("Token")
        )
        if not token:
            raise SmartVVBAuthError("Login succeeded but no token was returned")

        self.token = token
        self.username = username
        return response

    async def get_devices(self) -> list[dict[str, Any]]:
        """Return the devices bound to the logged-in account."""
        response = await self._request(
            "GET", "/GetUserDevices", params={"userName": self.username}
        )
        devices = response.get("devices") or response.get("Devices") or []
        if not isinstance(devices, list):
            raise SmartVVBApiError("SmartVVB API returned an invalid GetUserDevices response")

        result = []
        for device in devices:
            serial = device.get("serial")
            result.append(
                {
                    "serial": serial,
                    # Falls back to the serial itself when no friendly name is
                    # set on the backend — never a hardcoded placeholder.
                    "name": device.get("friendlyName") or str(serial),
                    # Only GetUserDevices carries these, never GetDeviceInstantData.
                    "setpoint": device.get("setpoint"),
                    "volume": device.get("volume"),
                }
            )
        return result

    async def get_instant_data(self, serial: int) -> dict[str, Any]:
        """Return the full instant-data snapshot for one device."""
        data = await self._request(
            "GET", "/GetDeviceInstantData", params={"serial": serial}
        )
        if isinstance(data, list):
            return data[0] if data else {}
        return data

    async def set_mode(self, serial: int, mode: str) -> dict[str, Any]:
        return await self._request(
            "PUT", "/SetDeviceMode", json_body={"serial": serial, "mode": mode}
        )

    async def set_options(self, serial: int, setpoint: float) -> dict[str, Any]:
        return await self._request(
            "PUT", "/SetOptions", json_body={"serial": serial, "setpoint": setpoint}
        )

    async def force_device(self, serial: int, state: str) -> dict[str, Any]:
        return await self._request(
            "PUT", "/ForceDevice", json_body={"serial": serial, "state": state}
        )

    async def set_max_energy_per_hour(self, serial: int, max_energy: int) -> dict[str, Any]:
        """/SetMaxEnergy requires the full 24-hour table in every call — any
        hour left out gets reset to 0 by the backend — so this applies the
        same cap uniformly across all 24 hours rather than a single hour."""
        return await self.set_max_energy_schedule(serial, [max_energy] * 24)

    async def set_max_energy_schedule(self, serial: int, max_energy: list[int]) -> dict[str, Any]:
        """Set a separate cap for each of the 24 hours (index 0 = 00:00-01:00)."""
        hours = [{"hour": hour, "maxEnergy": value} for hour, value in enumerate(max_energy)]
        return await self._request(
            "PUT", "/SetMaxEnergy", json_body={"serial": serial, "hours": hours}
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        authenticated: bool = True,
    ) -> Any:
        headers = {"Content-Type": "application/json"}
        if authenticated:
            if not self.token:
                raise SmartVVBAuthError("Not authenticated - call login() first")
            headers["Authorization"] = f"Bearer {self.token}"

        clean_params = None
        if params is not None:
            clean_params = {k: str(v) for k, v in params.items() if v is not None}

        try:
            async with self._session.request(
                method,
                f"{API_BASE_URL}{path}",
                params=clean_params,
                json=json_body,
                headers=headers,
            ) as response:
                text = await response.text()
        except aiohttp.ClientError as err:
            raise SmartVVBApiError(f"SmartVVB API request error: {err}") from err

        if not text:
            if response.status >= 400:
                raise SmartVVBApiError(f"SmartVVB API request failed: HTTP {response.status}")
            return {}

        try:
            data = json.loads(text)
        except ValueError as err:
            raise SmartVVBApiError(f"SmartVVB API returned invalid JSON: {err}") from err

        if response.status >= 400:
            message = data.get("error") or data.get("message") or f"HTTP {response.status}"
            if response.status in (401, 403):
                raise SmartVVBAuthError(message)
            raise SmartVVBApiError(f"SmartVVB API request failed: {message}")

        return data
