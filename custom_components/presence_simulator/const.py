"""Constants for Presence Simulator."""

DOMAIN = "presence_simulator"

CONF_ACTIVITY_WINDOW_MODE = "activity_window_mode"

ACTIVITY_WINDOW_MODE_FIXED = "fixed"
ACTIVITY_WINDOW_MODE_SUN = "sun"

CONF_LIGHTS = "lights"

CONF_FIXED_START_TIME = "fixed_start_time"
CONF_FIXED_END_TIME = "fixed_end_time"
CONF_FIXED_WEEKDAYS = "fixed_weekdays"

CONF_SUN_START_EVENT = "sun_start_event"
CONF_SUN_START_OFFSET_MINUTES = "sun_start_offset_minutes"

CONF_SUN_END_EVENT = "sun_end_event"
CONF_SUN_END_OFFSET_MINUTES = "sun_end_offset_minutes"

SUN_EVENT_SUNRISE = "sunrise"
SUN_EVENT_SUNSET = "sunset"

CONF_MIN_ON_MINUTES = "min_on_minutes"
CONF_MAX_ON_MINUTES = "max_on_minutes"

CONF_MIN_OFF_MINUTES = "min_off_minutes"
CONF_MAX_OFF_MINUTES = "max_off_minutes"

CONF_MIN_INITIAL_DELAY_MINUTES = "min_initial_delay_minutes"
CONF_MAX_INITIAL_DELAY_MINUTES = "max_initial_delay_minutes"

CONF_MAX_SIMULTANEOUS = "max_simultaneous"


DEFAULT_ACTIVITY_WINDOW_MODE = ACTIVITY_WINDOW_MODE_FIXED

DEFAULT_FIXED_START_TIME = "19:00:00"
DEFAULT_FIXED_END_TIME = "08:00:00"

DEFAULT_FIXED_WEEKDAYS = [
    "mon",
    "tue",
    "wed",
    "thu",
    "fri",
    "sat",
    "sun",
]

DEFAULT_SUN_START_EVENT = SUN_EVENT_SUNSET
DEFAULT_SUN_START_OFFSET_MINUTES = -15

DEFAULT_SUN_END_EVENT = SUN_EVENT_SUNRISE
DEFAULT_SUN_END_OFFSET_MINUTES = 60

DEFAULT_MIN_ON_MINUTES = 5
DEFAULT_MAX_ON_MINUTES = 25

DEFAULT_MIN_OFF_MINUTES = 20
DEFAULT_MAX_OFF_MINUTES = 90

DEFAULT_MIN_INITIAL_DELAY_MINUTES = 1
DEFAULT_MAX_INITIAL_DELAY_MINUTES = 30

DEFAULT_MAX_SIMULTANEOUS = 2