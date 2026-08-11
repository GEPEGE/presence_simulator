"""Switch platform for Presence Simulator."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .manager import PresenceSimulatorManager


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Presence Simulator switch."""

    manager: PresenceSimulatorManager = hass.data[DOMAIN][entry.entry_id]["manager"]

    async_add_entities([PresenceSimulatorSwitch(entry, manager)])


class PresenceSimulatorSwitch(SwitchEntity, RestoreEntity):
    """Master switch for Presence Simulator."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        entry: ConfigEntry,
        manager: PresenceSimulatorManager,
    ) -> None:
        """Initialize the switch."""

        self._entry = entry
        self._manager = manager
        self._attr_unique_id = f"{entry.entry_id}_simulation"

        self._attr_device_info = {
            "identifiers": {
                (DOMAIN, entry.entry_id),
            },
            "name": entry.title,
            "manufacturer": "Presence Simulator",
            "model": "Presence Simulator",
        }

    @property
    def is_on(self) -> bool:
        """Return true if the simulator is running."""

        return self._manager.is_running

    async def async_added_to_hass(self) -> None:
        """Restore previous switch state."""

        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()

        if last_state is not None and last_state.state == "on":
            await self._manager.async_start()

        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the simulation on."""

        await self._manager.async_start()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the simulation off."""

        await self._manager.async_stop()
        self.async_write_ha_state()