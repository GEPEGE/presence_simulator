"""Presence Simulator integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .manager import PresenceSimulatorManager


PLATFORMS: list[Platform] = [
    Platform.SWITCH,
    Platform.SENSOR,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up Presence Simulator from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    manager = PresenceSimulatorManager(hass, entry)

    hass.data[DOMAIN][entry.entry_id] = {
        "manager": manager,
    }

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload Presence Simulator config entry."""

    manager: PresenceSimulatorManager = hass.data[DOMAIN][entry.entry_id]["manager"]

    await manager.async_stop()

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN, None)

    return unload_ok