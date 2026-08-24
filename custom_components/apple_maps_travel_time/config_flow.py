"""Config flow for Apple Maps Travel Time integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_DESTINATION,
    CONF_KEY_ID,
    CONF_ORIGIN,
    CONF_PRIVATE_KEY,
    CONF_SCAN_INTERVAL,
    CONF_TEAM_ID,
    CONF_TRAVEL_MODE,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TRAVEL_MODE,
    DOMAIN,
    TRAVEL_MODES,
)
from .coordinator import format_private_key

_LOGGER = logging.getLogger(__name__)


class AppleMapsTravelTimeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Apple Maps Travel Time."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate Private Key format
            try:
                import jwt

                pem = format_private_key(user_input[CONF_PRIVATE_KEY])
                headers = {"alg": "ES256", "typ": "JWT", "kid": user_input[CONF_KEY_ID]}
                payload = {"iss": user_input[CONF_TEAM_ID], "iat": 0, "exp": 3600}
                jwt.encode(payload, pem, algorithm="ES256", headers=headers)
            except Exception as err:
                _LOGGER.warning("Apple Maps key validation error: %s", err)
                errors["base"] = "invalid_auth"

            if not errors:
                name = user_input.get(CONF_NAME) or DEFAULT_NAME
                return self.async_create_entry(
                    title=name,
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_TEAM_ID): str,
                vol.Required(CONF_KEY_ID): str,
                vol.Required(CONF_PRIVATE_KEY): str,
                vol.Required(
                    CONF_ORIGIN,
                    default="zone.home",
                ): str,
                vol.Required(
                    CONF_DESTINATION,
                    default="zone.work",
                ): str,
                vol.Optional(
                    CONF_TRAVEL_MODE,
                    default=DEFAULT_TRAVEL_MODE,
                ): vol.In(TRAVEL_MODES),
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=DEFAULT_SCAN_INTERVAL,
                ): cv.positive_int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return AppleMapsOptionsFlowHandler(config_entry)


class AppleMapsOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Apple Maps Travel Time."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        data = self.config_entry.data

        current_origin = options.get(CONF_ORIGIN, data.get(CONF_ORIGIN, "zone.home"))
        current_destination = options.get(
            CONF_DESTINATION, data.get(CONF_DESTINATION, "zone.work")
        )
        current_mode = options.get(
            CONF_TRAVEL_MODE, data.get(CONF_TRAVEL_MODE, DEFAULT_TRAVEL_MODE)
        )
        current_interval = options.get(
            CONF_SCAN_INTERVAL, data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_ORIGIN, default=current_origin): str,
                vol.Required(CONF_DESTINATION, default=current_destination): str,
                vol.Optional(CONF_TRAVEL_MODE, default=current_mode): vol.In(TRAVEL_MODES),
                vol.Optional(CONF_SCAN_INTERVAL, default=current_interval): cv.positive_int,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
