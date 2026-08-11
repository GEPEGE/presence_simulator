# Presence Simulator

Presence Simulator is a custom integration for Home Assistant that simulates realistic occupancy by randomly controlling selected lights during configurable activity windows.

Unlike history-based presence simulation, Presence Simulator generates activity dynamically and independently for each configured light.

## Features

- Independent random activity for each light
- Configurable minimum and maximum ON durations
- Configurable minimum and maximum OFF durations
- Random initial delay when an activity window opens
- Configurable maximum number of simultaneous lights
- Fixed-time activity windows
- Sun-based activity windows using sunrise or sunset with offsets
- Overnight fixed-time windows
- Configurable active weekdays
- Automatic cleanup when simulation stops or the activity window closes
- Does not turn off lights that were already ON before the simulator attempted to use them
- Restores the master simulation switch after a Home Assistant restart
- Status sensor showing whether the simulator is disabled, waiting, or active

## Example

A typical holiday configuration could use:

- Activity window: Sunset -15 minutes to Sunrise +60 minutes
- Initial delay: 1-30 minutes
- ON duration: 5-25 minutes
- OFF duration: 20-90 minutes
- Maximum simultaneous lights: 2

Each selected light operates independently, producing natural overlapping activity rather than switching all lights together.

## Installation

### HACS

HACS installation will be supported once the integration is published.

For development and testing, add this repository as a custom HACS integration repository.

### Manual installation

Copy:

custom_components/presence_simulator

into your Home Assistant:

/config/custom_components/

Restart Home Assistant, then go to:

Settings > Devices & services > Add integration > Presence Simulator

## Configuration

After adding the integration, use Configure to select:

1. Activity window mode
2. Fixed-time or sun-based window settings
3. Lights
4. Random timing ranges
5. Maximum simultaneous lights

The integration creates:

- A master simulation switch
- A status sensor

## Status

This project is currently under active development.

## Disclaimer

This project is a vibe-coded initiative. I am not a professional developer, and this integration was built primarily through experimentation, testing, and AI-assisted development.
I created Presence Simulator because I missed the simple and effective presence simulation functionality I previously had with eedomus and could not find exactly the same experience in Home Assistant.
It started as a solution for my own home, but since it may be useful to others looking for the same functionality, I decided to share it with the Home Assistant community.
Please keep in mind that this is an independent community project. Use it at your own risk, and feel free to report issues, suggest improvements, or contribute fixes.

## License

License information will be added before the first public release.
