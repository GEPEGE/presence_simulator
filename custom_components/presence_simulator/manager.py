"""Runtime manager for Presence Simulator."""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Callable
from datetime import datetime, time, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import (
    async_track_sunrise,
    async_track_sunset,
    async_track_time_change,
)
from homeassistant.util import dt as dt_util

from .const import (
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
    SUN_EVENT_SUNRISE,
)

_LOGGER = logging.getLogger(__name__)

WEEKDAY_MAP = {
    0: "mon",
    1: "tue",
    2: "wed",
    3: "thu",
    4: "fri",
    5: "sat",
    6: "sun",
}


class PresenceSimulatorManager:
    """Manage runtime state for one Presence Simulator config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the manager."""

        self.hass = hass
        self.entry = entry
        self.is_running = False

        self.light_entity_ids: list[str] = self.entry.options.get(
            CONF_LIGHTS,
            self.entry.data[CONF_LIGHTS],
        )

        self._window_listeners: list[Callable[[], None]] = []
        self._state_listeners: list[Callable[[], None]] = []

        self._light_tasks: dict[str, asyncio.Task] = {}
        self._simulated_lights_on: set[str] = set()
        self._simultaneous_limit: asyncio.Semaphore | None = None

    @callback
    def async_add_state_listener(
        self,
        listener: Callable[[], None],
    ) -> Callable[[], None]:
        """Subscribe to simulator state changes."""

        self._state_listeners.append(listener)

        @callback
        def remove_listener() -> None:
            if listener in self._state_listeners:
                self._state_listeners.remove(listener)

        return remove_listener

    @callback
    def _notify_state_listeners(self) -> None:
        """Notify entities that manager state changed."""

        for listener in list(self._state_listeners):
            listener()

    def _get_window_mode(self) -> str:
        """Return the configured activity window mode."""

        return self.entry.options.get(
            CONF_ACTIVITY_WINDOW_MODE,
            DEFAULT_ACTIVITY_WINDOW_MODE,
        )

    def _parse_time(self, value: str) -> time:
        """Convert HH:MM[:SS] into a time object."""

        return time.fromisoformat(value)

    def _is_fixed_window_active(self) -> bool:
        """Return true if current time is inside the fixed activity window."""

        options = self.entry.options

        start = self._parse_time(
            options.get(
                CONF_FIXED_START_TIME,
                DEFAULT_FIXED_START_TIME,
            )
        )
        end = self._parse_time(
            options.get(
                CONF_FIXED_END_TIME,
                DEFAULT_FIXED_END_TIME,
            )
        )
        weekdays = options.get(
            CONF_FIXED_WEEKDAYS,
            DEFAULT_FIXED_WEEKDAYS,
        )

        now = dt_util.now()
        current_time = now.time().replace(tzinfo=None)

        if start == end:
            return WEEKDAY_MAP[now.weekday()] in weekdays

        if start < end:
            return (
                WEEKDAY_MAP[now.weekday()] in weekdays
                and start <= current_time < end
            )

        if current_time >= start:
            return WEEKDAY_MAP[now.weekday()] in weekdays

        if current_time < end:
            previous_day = (now.weekday() - 1) % 7
            return WEEKDAY_MAP[previous_day] in weekdays

        return False

    def _get_next_sun_event(
        self,
        event_name: str,
        offset_minutes: int,
    ) -> datetime | None:
        """Return next configured sunrise/sunset including offset."""

        sun_state = self.hass.states.get("sun.sun")

        if sun_state is None:
            return None

        attribute = (
            "next_rising"
            if event_name == SUN_EVENT_SUNRISE
            else "next_setting"
        )

        value = sun_state.attributes.get(attribute)

        if value is None:
            return None

        event_time = dt_util.parse_datetime(value)

        if event_time is None:
            return None

        return event_time + timedelta(minutes=offset_minutes)

    def _is_sun_window_active(self) -> bool:
        """Return true if current time is inside the sun-based window."""

        options = self.entry.options
        now = dt_util.utcnow()

        start_event = options.get(
            CONF_SUN_START_EVENT,
            DEFAULT_SUN_START_EVENT,
        )
        start_offset = int(
            options.get(
                CONF_SUN_START_OFFSET_MINUTES,
                DEFAULT_SUN_START_OFFSET_MINUTES,
            )
        )

        end_event = options.get(
            CONF_SUN_END_EVENT,
            DEFAULT_SUN_END_EVENT,
        )
        end_offset = int(
            options.get(
                CONF_SUN_END_OFFSET_MINUTES,
                DEFAULT_SUN_END_OFFSET_MINUTES,
            )
        )

        next_start = self._get_next_sun_event(
            start_event,
            start_offset,
        )
        next_end = self._get_next_sun_event(
            end_event,
            end_offset,
        )

        if next_start is None or next_end is None:
            return False

        while next_start <= now:
            next_start += timedelta(days=1)

        while next_end <= now:
            next_end += timedelta(days=1)

        return next_end < next_start

    def is_activity_window_active(self) -> bool:
        """Return true if the configured activity window is active."""

        if self._get_window_mode() == ACTIVITY_WINDOW_MODE_SUN:
            return self._is_sun_window_active()

        return self._is_fixed_window_active()

    def _get_initial_delay_options(self) -> tuple[int, int]:
        """Return initial delay range in seconds."""

        options = self.entry.options

        return (
            int(
                options.get(
                    CONF_MIN_INITIAL_DELAY_MINUTES,
                    DEFAULT_MIN_INITIAL_DELAY_MINUTES,
                )
            )
            * 60,
            int(
                options.get(
                    CONF_MAX_INITIAL_DELAY_MINUTES,
                    DEFAULT_MAX_INITIAL_DELAY_MINUTES,
                )
            )
            * 60,
        )

    def _get_timing_options(self) -> tuple[int, int, int, int]:
        """Return ON and OFF timing ranges in seconds."""

        options = self.entry.options

        return (
            int(options.get(CONF_MIN_ON_MINUTES, DEFAULT_MIN_ON_MINUTES)) * 60,
            int(options.get(CONF_MAX_ON_MINUTES, DEFAULT_MAX_ON_MINUTES)) * 60,
            int(options.get(CONF_MIN_OFF_MINUTES, DEFAULT_MIN_OFF_MINUTES)) * 60,
            int(options.get(CONF_MAX_OFF_MINUTES, DEFAULT_MAX_OFF_MINUTES)) * 60,
        )

    def _get_max_simultaneous(self) -> int:
        """Return maximum number of lights allowed ON simultaneously."""

        configured = int(
            self.entry.options.get(
                CONF_MAX_SIMULTANEOUS,
                DEFAULT_MAX_SIMULTANEOUS,
            )
        )

        return max(1, min(configured, len(self.light_entity_ids)))

    async def _async_turn_light_on(self, light_entity_id: str) -> None:
        """Turn on one simulated light."""

        await self.hass.services.async_call(
            "light",
            "turn_on",
            {"entity_id": light_entity_id},
            blocking=True,
        )

        self._simulated_lights_on.add(light_entity_id)

    async def _async_turn_light_off(self, light_entity_id: str) -> None:
        """Turn off one light if the simulator owns it."""

        if light_entity_id not in self._simulated_lights_on:
            return

        await self.hass.services.async_call(
            "light",
            "turn_off",
            {"entity_id": light_entity_id},
            blocking=True,
        )

        self._simulated_lights_on.discard(light_entity_id)

    async def _async_light_worker(self, light_entity_id: str) -> None:
        """Run an independent activity loop for one light."""

        try:
            min_initial, max_initial = self._get_initial_delay_options()

            initial_delay = random.randint(
                min_initial,
                max_initial,
            )

            if initial_delay > 0:
                await asyncio.sleep(initial_delay)

            while self.is_running and self.is_activity_window_active():
                min_on, max_on, min_off, max_off = self._get_timing_options()

                if self._simultaneous_limit is None:
                    break

                async with self._simultaneous_limit:
                    if (
                        not self.is_running
                        or not self.is_activity_window_active()
                    ):
                        break

                    state = self.hass.states.get(light_entity_id)

                    if state is None or state.state != "on":
                        await self._async_turn_light_on(light_entity_id)

                        try:
                            await asyncio.sleep(
                                random.randint(min_on, max_on)
                            )
                        finally:
                            await self._async_turn_light_off(light_entity_id)

                if (
                    not self.is_running
                    or not self.is_activity_window_active()
                ):
                    break

                await asyncio.sleep(
                    random.randint(min_off, max_off)
                )

        except asyncio.CancelledError:
            await self._async_turn_light_off(light_entity_id)
            raise

    def _start_light_tasks(self) -> None:
        """Start one independent worker per configured light."""

        if self._light_tasks:
            return

        self._simultaneous_limit = asyncio.Semaphore(
            self._get_max_simultaneous()
        )

        for light_entity_id in self.light_entity_ids:
            self._light_tasks[light_entity_id] = self.hass.async_create_task(
                self._async_light_worker(light_entity_id)
            )

    async def _async_cancel_light_tasks(self) -> None:
        """Cancel all active light tasks."""

        tasks = list(self._light_tasks.values())

        for task in tasks:
            if not task.done():
                task.cancel()

        if tasks:
            await asyncio.gather(
                *tasks,
                return_exceptions=True,
            )

        self._light_tasks.clear()
        self._simultaneous_limit = None

        for light_entity_id in list(self._simulated_lights_on):
            await self._async_turn_light_off(light_entity_id)

    async def _async_reevaluate_window(self) -> None:
        """Start or stop simulated activity when the window changes."""

        if not self.is_running:
            self._notify_state_listeners()
            return

        if self.is_activity_window_active():
            self._start_light_tasks()
        else:
            await self._async_cancel_light_tasks()

        self._notify_state_listeners()

    @callback
    def _window_event_callback(self, *_) -> None:
        """Handle a fixed-time or sun boundary event."""

        self.hass.async_create_task(
            self._async_reevaluate_window()
        )

    def _remove_window_listeners(self) -> None:
        """Remove all activity-window listeners."""

        for remove_listener in self._window_listeners:
            remove_listener()

        self._window_listeners.clear()

    def _setup_window_listeners(self) -> None:
        """Register listeners for the configured window mode."""

        self._remove_window_listeners()

        options = self.entry.options

        if self._get_window_mode() == ACTIVITY_WINDOW_MODE_SUN:
            start_event = options.get(
                CONF_SUN_START_EVENT,
                DEFAULT_SUN_START_EVENT,
            )
            start_offset = timedelta(
                minutes=int(
                    options.get(
                        CONF_SUN_START_OFFSET_MINUTES,
                        DEFAULT_SUN_START_OFFSET_MINUTES,
                    )
                )
            )

            end_event = options.get(
                CONF_SUN_END_EVENT,
                DEFAULT_SUN_END_EVENT,
            )
            end_offset = timedelta(
                minutes=int(
                    options.get(
                        CONF_SUN_END_OFFSET_MINUTES,
                        DEFAULT_SUN_END_OFFSET_MINUTES,
                    )
                )
            )

            start_tracker = (
                async_track_sunrise
                if start_event == SUN_EVENT_SUNRISE
                else async_track_sunset
            )

            end_tracker = (
                async_track_sunrise
                if end_event == SUN_EVENT_SUNRISE
                else async_track_sunset
            )

            self._window_listeners.append(
                start_tracker(
                    self.hass,
                    self._window_event_callback,
                    offset=start_offset,
                )
            )

            self._window_listeners.append(
                end_tracker(
                    self.hass,
                    self._window_event_callback,
                    offset=end_offset,
                )
            )

        else:
            start = self._parse_time(
                options.get(
                    CONF_FIXED_START_TIME,
                    DEFAULT_FIXED_START_TIME,
                )
            )
            end = self._parse_time(
                options.get(
                    CONF_FIXED_END_TIME,
                    DEFAULT_FIXED_END_TIME,
                )
            )

            self._window_listeners.append(
                async_track_time_change(
                    self.hass,
                    self._window_event_callback,
                    hour=start.hour,
                    minute=start.minute,
                    second=start.second,
                )
            )

            self._window_listeners.append(
                async_track_time_change(
                    self.hass,
                    self._window_event_callback,
                    hour=end.hour,
                    minute=end.minute,
                    second=end.second,
                )
            )

    async def async_start(self) -> None:
        """Start the simulator."""

        if self.is_running:
            return

        self.is_running = True
        self._setup_window_listeners()

        await self._async_reevaluate_window()
        self._notify_state_listeners()

    async def async_stop(self) -> None:
        """Stop the simulator."""

        if not self.is_running:
            return

        self.is_running = False

        self._remove_window_listeners()
        await self._async_cancel_light_tasks()

        self._notify_state_listeners()