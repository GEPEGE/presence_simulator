"""Sensor platform for Presence Simulator."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_MAX_SIMULTANEOUS,
    DEFAULT_MAX_SIMULTANEOUS,
    DOMAIN,
)
from .manager import PresenceSimulatorManager


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Presence Simulator sensors."""

    manager: PresenceSimulatorManager = hass.data[DOMAIN][entry.entry_id]["manager"]

    async_add_entities(
        [
            PresenceSimulatorStatusSensor(
                entry,
                manager,
            )
        ]
    )


class PresenceSimulatorStatusSensor(SensorEntity):
    """Status sensor for Presence Simulator."""

    _attr_has_entity_name = True
    _attr_name = "Status"
    _attr_should_poll = False

    def __init__(
        self,
        entry: ConfigEntry,
        manager: PresenceSimulatorManager,
    ) -> None:
        """Initialize the status sensor."""

        self._entry = entry
        self._manager = manager
        self._attr_unique_id = f"{entry.entry_id}_status"

        self._remove_listener: Callable[[], None] | None = None

        self._attr_device_info = {
            "identifiers": {
                (DOMAIN, entry.entry_id),
            },
            "name": entry.title,
            "manufacturer": "Presence Simulator",
            "model": "Presence Simulator",
        }

    async def async_added_to_hass(self) -> None:
        """Subscribe to manager state changes."""

        await super().async_added_to_hass()

        self._remove_listener = self._manager.async_add_state_listener(
            self._handle_manager_update
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from manager state changes."""

        if self._remove_listener is not None:
            self._remove_listener()
            self._remove_listener = None

        await super().async_will_remove_from_hass()

    @callback
    def _handle_manager_update(self) -> None:
        """Handle manager state changes."""

        self.async_write_ha_state()

    @property
    def native_value(self) -> str:
        """Return the current simulator status."""

        if not self._manager.is_running:
            return "disabled"

        if self._manager.is_activity_window_active():
            return "active"

        return "waiting"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return diagnostic state attributes."""

        configured_max = int(
            self._entry.options.get(
                CONF_MAX_SIMULTANEOUS,
                DEFAULT_MAX_SIMULTANEOUS,
            )
        )

        return {
            "window_mode": self._manager._get_window_mode(),
            "managed_lights": len(self._manager.light_entity_ids),
            "active_simulated_lights": len(
                self._manager._simulated_lights_on
            ),
            "max_simultaneous": configured_max,
        }