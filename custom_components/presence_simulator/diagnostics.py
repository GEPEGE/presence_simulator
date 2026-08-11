"""Diagnostics support for Presence Simulator."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .manager import PresenceSimulatorManager


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""

    manager: PresenceSimulatorManager = hass.data[DOMAIN][entry.entry_id]["manager"]

    return {
        "config_entry": {
            "title": entry.title,
            "version": entry.version,
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "runtime": {
            "is_running": manager.is_running,
            "activity_window_active": manager.is_activity_window_active(),
            "window_mode": manager._get_window_mode(),
            "managed_lights": list(manager.light_entity_ids),
            "active_simulated_lights": list(manager._simulated_lights_on),
        },
    }
