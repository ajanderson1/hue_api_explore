# Hue Controller

A natural language control interface for Philips Hue lights using API v2.

## Features

- **Natural Language Commands**: Control lights with plain English ("turn on living room", "dim kitchen to 50%")
- **Automatic Bridge Discovery**: Finds your Hue Bridge via mDNS
- **Color Support**: Set colors by name, hex code, RGB, or color temperature
- **Scene Activation**: Recall Hue scenes by name ("relax mode in bedroom")
- **Fuzzy Matching**: Flexible target matching ("livingroom" matches "Living Room")
- **Unreachable Light Handling**: Gracefully reports lights that are physically switched off
- **Smooth Transitions**: Default 400ms transitions for pleasant visual effects
- **Rate Limiting**: Built-in rate limiting to prevent overloading the bridge

## Requirements

- Python 3.10+
- Philips Hue Bridge with firmware supporting API v2 (version 1948086000+)
- Network access to the bridge

## Installation

```bash
# Clone or download this repository
cd hue_api_explore

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Set Up Bridge Connection

Run the setup script to discover your bridge and create authentication credentials:

```bash
python setup_bridge.py
```

Follow the prompts to:
1. Discover your bridge on the network
2. Press the link button on your bridge
3. Save credentials to `config.json`

### 2. Start the CLI

```bash
python cli_interface.py
```

### 3. Control Your Lights

```
hue> turn on living room
  Turned on Living Room (3 lights)

hue> dim kitchen to 50%
  Set to 50% Kitchen (2 lights)

hue> set bedroom to blue
  Set color Bedroom (1 light)

hue> relax mode in office
  Activated scene 'Relax'

hue> status
Bridge: 192.168.1.100
Lights: 5/12 on (1 unreachable)
Rooms: 4
Scenes: 8
```

## Command Reference

### Power Control
```
turn on [target]          - Turn on a light, room, or zone
turn off [target]         - Turn off a light, room, or zone
```

### Brightness
```
dim [target] to 50%       - Set brightness to specific percentage
set [target] to low       - Set brightness to 25%
set [target] to half      - Set brightness to 50%
brighten [target]         - Set brightness to 100%
```

### Colors
```
set [target] to red       - Set color by name
set [target] to #FF5500   - Set color by hex code
set [target] to rgb(255,100,0)  - Set color by RGB values
make [target] warm        - Set to warm white (2700K)
set [target] to 4000K     - Set color temperature in Kelvin
```

### Scenes
```
relax mode in [room]      - Activate the Relax scene
energize [room]           - Activate the Energize scene
concentrate in [room]     - Activate the Concentrate scene
```

### Transition Speed
```
... slowly                - Use 2 second transition
... instantly             - No transition
... in 5 seconds          - Custom transition time
```

### Built-in Commands
```
help                      - Show command help
status                    - Show system overview
status [target]           - Show detailed target status
lights                    - List all lights
rooms                     - List all rooms
zones                     - List all zones
scenes                    - List all scenes
refresh                   - Re-sync state from bridge
quit                      - Exit the CLI
```

## Project Structure

```
hue_api_explore/
├── hue_controller/
│   ├── __init__.py           # Package exports
│   ├── models.py             # Data models (Light, Room, Scene, etc.)
│   ├── exceptions.py         # Custom exception types
│   ├── color_utils.py        # RGB/Hex to CIE xy conversion
│   ├── bridge_connector.py   # Discovery, auth, HTTP client
│   ├── device_manager.py     # State caching, fuzzy matching
│   └── command_interpreter.py # NLP parsing, command execution
├── setup_bridge.py           # One-time setup script
├── cli_interface.py          # Interactive REPL
├── config.json               # Saved credentials (gitignored)
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Configuration

Credentials are stored in `config.json`:

```json
{
  "bridge_ip": "192.168.1.100",
  "application_key": "your-application-key",
  "bridge_id": "optional-bridge-id"
}
```

This file is created automatically by `setup_bridge.py` with restricted permissions (0600).

## API Reference

### Using as a Library

```python
import asyncio
from hue_controller import BridgeConnector, DeviceManager, CommandInterpreter

async def main():
    # Connect to bridge
    connector = BridgeConnector("config.json")

    # Sync device state
    dm = DeviceManager(connector)
    await dm.sync_state()

    # Find and control a light
    light = dm.find_target("living room")
    await connector.put(
        f"/resource/light/{light.id}",
        {"on": {"on": True}, "dimming": {"brightness": 75}}
    )

    # Or use the command interpreter
    interpreter = CommandInterpreter(dm)
    parsed = interpreter.parse("turn on kitchen")
    # ... execute parsed command

    await connector.close()

asyncio.run(main())
```

### Color Conversion

```python
from hue_controller.color_utils import rgb_to_xy, hex_to_xy, parse_color

# RGB to xy
xy = rgb_to_xy(255, 0, 0)  # Returns XYColor(x=0.6484, y=0.3309)

# Hex to xy
xy = hex_to_xy("#FF5500")

# Parse color specification
payload = parse_color("warm")  # Returns {"color_temperature": {"mirek": 370}}
payload = parse_color("blue")  # Returns {"color": {"xy": {"x": ..., "y": ...}}}
```

## Troubleshooting

### Bridge Not Found

- Ensure your bridge is powered on and connected to the network
- Check that you're on the same network as the bridge
- Try entering the bridge IP manually during setup

### Authentication Failed

- Make sure to press the link button within 30 seconds
- The link button is the large button on top of the bridge
- Try running setup again

### Lights Not Responding

- Check if lights show as "unreachable" in status
- Unreachable lights are typically switched off at the wall
- Try `refresh` to re-sync state from the bridge

### Rate Limit Errors

- The bridge limits requests to ~10/second for lights, ~1/second for groups
- Wait a few seconds and try again
- Use room/zone commands instead of controlling lights individually

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Philips Hue Developer Program for API documentation
- Color conversion algorithms based on Philips guidance
