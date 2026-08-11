"""Config flow for Presence Simulator."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlowWithReload
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    ACTIVITY_WINDOW_MODE_FIXED,
    ACTIVITY_WINDOW_MODE_SUN,
    CONF_ACTIVITY_WINDOW_MODE,
    CONF_FIXED_END_TIME,
    CONF_FIXED_START_TIME,
    CONF_FIXED_WEEKDAYS,
    CONF_LIGHTS,
    CONF_MAX_INITIAL_DELAY_MINUTES,
    CONF_MAX_OFF_MINUTES,
    CONF_MAX_ON_MINUTES,
    CONF_MAX_SIMULTANEOUS,
    CONF_MIN_INITIAL_DELAY_MINUTES,
    CONF_MIN_OFF_MINUTES,
    CONF_MIN_ON_MINUTES,
    CONF_SUN_END_EVENT,
    CONF_SUN_END_OFFSET_MINUTES,
    CONF_SUN_START_EVENT,
    CONF_SUN_START_OFFSET_MINUTES,
    DEFAULT_ACTIVITY_WINDOW_MODE,
    DEFAULT_FIXED_END_TIME,
    DEFAULT_FIXED_START_TIME,
    DEFAULT_FIXED_WEEKDAYS,
    DEFAULT_MAX_INITIAL_DELAY_MINUTES,
    DEFAULT_MAX_OFF_MINUTES,
    DEFAULT_MAX_ON_MINUTES,
    DEFAULT_MAX_SIMULTANEOUS,
    DEFAULT_MIN_INITIAL_DELAY_MINUTES,
    DEFAULT_MIN_OFF_MINUTES,
    DEFAULT_MIN_ON_MINUTES,
    DEFAULT_SUN_END_EVENT,
    DEFAULT_SUN_END_OFFSET_MINUTES,
    DEFAULT_SUN_START_EVENT,
    DEFAULT_SUN_START_OFFSET_MINUTES,
    DOMAIN,
    SUN_EVENT_SUNRISE,
    SUN_EVENT_SUNSET,
)


class PresenceSimulatorConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle a config flow for Presence Simulator."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle initial setup."""

        if user_input is not None:
            await self.async_set_unique_id("presence_simulator")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_NAME,
                    default="Presence Simulator",
                ): selector.TextSelector(),
                vol.Required(CONF_LIGHTS): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="light",
                        multiple=True,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> PresenceSimulatorOptionsFlow:
        """Create the options flow."""
        return PresenceSimulatorOptionsFlow()


class PresenceSimulatorOptionsFlow(OptionsFlowWithReload):
    """Handle Presence Simulator options."""

    def __init__(self) -> None:
        """Initialize the options flow."""

        self._pending_options: dict[str, Any] = {}

    def _current_value(self, key: str, default: Any) -> Any:
        """Return pending, saved, or default value."""

        if key in self._pending_options:
            return self._pending_options[key]

        return self.config_entry.options.get(key, default)

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Choose activity window mode."""

        if user_input is not None:
            self._pending_options.update(user_input)

            if (
                user_input[CONF_ACTIVITY_WINDOW_MODE]
                == ACTIVITY_WINDOW_MODE_SUN
            ):
                return await self.async_step_sun()

            return await self.async_step_fixed()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_ACTIVITY_WINDOW_MODE,
                    default=self._current_value(
                        CONF_ACTIVITY_WINDOW_MODE,
                        DEFAULT_ACTIVITY_WINDOW_MODE,
                    ),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            ACTIVITY_WINDOW_MODE_FIXED,
                            ACTIVITY_WINDOW_MODE_SUN,
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )

    async def async_step_fixed(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Configure fixed-time activity window."""

        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input[CONF_FIXED_WEEKDAYS]:
                errors["base"] = "no_weekdays_selected"

            if not errors:
                self._pending_options.update(user_input)
                return await self.async_step_activity()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_FIXED_START_TIME,
                    default=self._current_value(
                        CONF_FIXED_START_TIME,
                        DEFAULT_FIXED_START_TIME,
                    ),
                ): selector.TimeSelector(),

                vol.Required(
                    CONF_FIXED_END_TIME,
                    default=self._current_value(
                        CONF_FIXED_END_TIME,
                        DEFAULT_FIXED_END_TIME,
                    ),
                ): selector.TimeSelector(),

                vol.Required(
                    CONF_FIXED_WEEKDAYS,
                    default=self._current_value(
                        CONF_FIXED_WEEKDAYS,
                        DEFAULT_FIXED_WEEKDAYS,
                    ),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            "mon",
                            "tue",
                            "wed",
                            "thu",
                            "fri",
                            "sat",
                            "sun",
                        ],
                        multiple=True,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="fixed",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_sun(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Configure sun-based activity window."""

        if user_input is not None:
            self._pending_options.update(user_input)
            return await self.async_step_activity()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SUN_START_EVENT,
                    default=self._current_value(
                        CONF_SUN_START_EVENT,
                        DEFAULT_SUN_START_EVENT,
                    ),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            SUN_EVENT_SUNRISE,
                            SUN_EVENT_SUNSET,
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),

                vol.Required(
                    CONF_SUN_START_OFFSET_MINUTES,
                    default=self._current_value(
                        CONF_SUN_START_OFFSET_MINUTES,
                        DEFAULT_SUN_START_OFFSET_MINUTES,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=-360,
                        max=360,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="min",
                    )
                ),

                vol.Required(
                    CONF_SUN_END_EVENT,
                    default=self._current_value(
                        CONF_SUN_END_EVENT,
                        DEFAULT_SUN_END_EVENT,
                    ),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            SUN_EVENT_SUNRISE,
                            SUN_EVENT_SUNSET,
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),

                vol.Required(
                    CONF_SUN_END_OFFSET_MINUTES,
                    default=self._current_value(
                        CONF_SUN_END_OFFSET_MINUTES,
                        DEFAULT_SUN_END_OFFSET_MINUTES,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=-360,
                        max=360,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="min",
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="sun",
            data_schema=schema,
        )

    async def async_step_activity(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Configure lights and activity timings."""

        errors: dict[str, str] = {}

        if user_input is not None:
            if (
                user_input[CONF_MIN_INITIAL_DELAY_MINUTES]
                > user_input[CONF_MAX_INITIAL_DELAY_MINUTES]
            ):
                errors["base"] = "min_initial_delay_greater_than_max"

            if (
                user_input[CONF_MIN_ON_MINUTES]
                > user_input[CONF_MAX_ON_MINUTES]
            ):
                errors["base"] = "min_on_greater_than_max"

            if (
                user_input[CONF_MIN_OFF_MINUTES]
                > user_input[CONF_MAX_OFF_MINUTES]
            ):
                errors["base"] = "min_off_greater_than_max"

            if not errors:
                self._pending_options.update(user_input)

                return self.async_create_entry(
                    title="",
                    data=self._pending_options,
                )

        original_lights = self.config_entry.data.get(CONF_LIGHTS, [])

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_LIGHTS,
                    default=self._current_value(
                        CONF_LIGHTS,
                        original_lights,
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="light",
                        multiple=True,
                    )
                ),

                vol.Required(
                    CONF_MIN_INITIAL_DELAY_MINUTES,
                    default=self._current_value(
                        CONF_MIN_INITIAL_DELAY_MINUTES,
                        DEFAULT_MIN_INITIAL_DELAY_MINUTES,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=180,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="min",
                    )
                ),

                vol.Required(
                    CONF_MAX_INITIAL_DELAY_MINUTES,
                    default=self._current_value(
                        CONF_MAX_INITIAL_DELAY_MINUTES,
                        DEFAULT_MAX_INITIAL_DELAY_MINUTES,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=180,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="min",
                    )
                ),

                vol.Required(
                    CONF_MIN_ON_MINUTES,
                    default=self._current_value(
                        CONF_MIN_ON_MINUTES,
                        DEFAULT_MIN_ON_MINUTES,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=180,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="min",
                    )
                ),

                vol.Required(
                    CONF_MAX_ON_MINUTES,
                    default=self._current_value(
                        CONF_MAX_ON_MINUTES,
                        DEFAULT_MAX_ON_MINUTES,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=180,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="min",
                    )
                ),

                vol.Required(
                    CONF_MIN_OFF_MINUTES,
                    default=self._current_value(
                        CONF_MIN_OFF_MINUTES,
                        DEFAULT_MIN_OFF_MINUTES,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=360,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="min",
                    )
                ),

                vol.Required(
                    CONF_MAX_OFF_MINUTES,
                    default=self._current_value(
                        CONF_MAX_OFF_MINUTES,
                        DEFAULT_MAX_OFF_MINUTES,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=360,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="min",
                    )
                ),

                vol.Required(
                    CONF_MAX_SIMULTANEOUS,
                    default=self._current_value(
                        CONF_MAX_SIMULTANEOUS,
                        DEFAULT_MAX_SIMULTANEOUS,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=10,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="activity",
            data_schema=schema,
            errors=errors,
        )