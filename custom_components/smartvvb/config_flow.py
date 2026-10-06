"""Config flow for SmartVVB."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import aiohttp_client

from .api import SmartVVBApi, SmartVVBApiError, SmartVVBAuthError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class SmartVVBConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SmartVVB.

    Only the resulting bearer token is stored (the backend's own token is
    non-expiring — see GetToken.php), never the password itself.
    """

    VERSION = 1

    def __init__(self) -> None:
        self._reauth_entry: config_entries.ConfigEntry | None = None

    async def _async_validate_and_get_token(
        self, username: str, password: str
    ) -> tuple[str | None, dict[str, str]]:
        session = aiohttp_client.async_get_clientsession(self.hass)
        api = SmartVVBApi(session)
        errors: dict[str, str] = {}

        try:
            await api.login(username, password)
        except SmartVVBAuthError:
            errors["base"] = "invalid_auth"
        except SmartVVBApiError:
            _LOGGER.exception("Unexpected error validating SmartVVB credentials")
            errors["base"] = "cannot_connect"
        else:
            return api.token, errors

        return None, errors

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            token, errors = await self._async_validate_and_get_token(
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            if token:
                await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data={CONF_USERNAME: user_input[CONF_USERNAME], "token": token},
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Triggered by ConfigEntryAuthFailed if the stored token ever stops working."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        assert self._reauth_entry is not None

        if user_input is not None:
            token, errors = await self._async_validate_and_get_token(
                self._reauth_entry.data[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            if token:
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry,
                    data={**self._reauth_entry.data, "token": token},
                )
                await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
            description_placeholders={CONF_USERNAME: self._reauth_entry.data[CONF_USERNAME]},
        )
