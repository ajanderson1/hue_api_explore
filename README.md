<p align="center">
  <h1 align="center">Hue Controller</h1>
  <p align="center">
    <strong>A natural language CLI for Philips Hue smart lights</strong>
  </p>
  <p align="center">
    Control your lights with plain English commands using the Hue API v2
  </p>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#commands">Commands</a> •
  <a href="#api-usage">API Usage</a> •
  <a href="#troubleshooting">Troubleshooting</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Hue%20API-v2-orange.svg" alt="Hue API v2">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/built%20with-Claude%20Code-blueviolet.svg" alt="Built with Claude Code">
</p>

---

## About

Hue Controller is a powerful command-line interface that lets you control your Philips Hue smart lights using natural language. Instead of navigating apps or memorizing API calls, simply type what you want:

```
hue> turn on living room
hue> dim kitchen to 50%
hue> set bedroom to warm
hue> relax mode in office
```

> **Note:** This entire application was written by [Claude Code](https://claude.ai/code), Anthropic's AI coding assistant. From architecture design to implementation, testing patterns to documentation—Claude Code authored every line of code in this repository.

## Features

### Core Functionality
- **Natural Language Commands** — Control lights with plain English
- **Automatic Bridge Discovery** — Finds your Hue Bridge via mDNS or cloud lookup
- **Fuzzy Name Matching** — "livingroom" matches "Living Room"
- **Command History** — Arrow keys navigate history (persisted across sessions)
- **Real-time State Sync** — SSE events keep state current without polling

### Light Control
- **Power** — Turn lights on/off individually or by room/zone
- **Brightness** — Set exact percentages or use presets (low, half, full)
- **Colors** — Named colors, hex codes (#FF5500), RGB values, color temperature (Kelvin)
- **Transitions** — Smooth fades with customizable duration

### Advanced Features
- **Scene Management** — Create, duplicate, modify, and recall scenes
- **Room & Zone Management** — Organize lights into logical groups
- **Light Effects** — Candle, fireplace, and other dynamic effects
- **Timed Effects** — Sunrise/sunset simulations with configurable duration
- **Entertainment Zones** — Configure areas for Hue Sync and gaming
- **Interactive Wizards** — Guided setup for complex operations

### Technical
- **Async Architecture** — Non-blocking I/O with `httpx` and HTTP/2
- **Rate Limiting** — Automatic throttling to respect bridge limits
- **Graceful Degradation** — Handles unreachable lights elegantly
- **Secure Credentials** — Config stored with restricted permissions (0600)

## Requirements

- **Python 3.10+**
- **Philips Hue Bridge** with API v2 support (firmware 1948086000+)
- **Network access** to the bridge (same LAN)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/hue-controller.git
cd hue-controller

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `httpx[http2]` | Async HTTP client with HTTP/2 support |
| `zeroconf` | mDNS bridge discovery |

## Quick Start

### 1. Connect to Your Bridge

Run the setup script to discover your bridge and authenticate:

```bash
python setup_bridge.py
```

You'll be prompted to:
1. Select your bridge (auto-discovered or manual IP entry)
2. Press the **link button** on top of your bridge
3. Credentials are saved to `config.json`

### 2. Launch the CLI

```bash
python cli_interface.py
```

### 3. Start Controlling

```
hue> turn on living room
  Turned on Living Room (3 lights)

hue> dim kitchen to 50%
  Set Kitchen to 50%

hue> set bedroom to blue
  Set color Bedroom

hue> relax mode in office
  Activated scene 'Relax'

hue> status
Bridge: 192.168.1.100
Lights: 5/12 on (1 unreachable)
Rooms: 4
Scenes: 8
```

## Commands

### Power Control

| Command | Description |
|---------|-------------|
| `turn on [target]` | Turn on a light, room, or zone |
| `turn off [target]` | Turn off a light, room, or zone |
| `turn on all lights` | Turn on every light |
| `turn off all lights` | Turn off every light |

### Brightness

| Command | Description |
|---------|-------------|
| `dim [target] to 50%` | Set specific brightness |
| `set [target] to low` | Set to 25% |
| `set [target] to half` | Set to 50% |
| `brighten [target]` | Set to 100% |

### Colors

| Command | Description |
|---------|-------------|
| `set [target] to red` | Set by color name |
| `set [target] to #FF5500` | Set by hex code |
| `set [target] to rgb(255,100,0)` | Set by RGB values |
| `make [target] warm` | Warm white (2700K) |
| `make [target] cool` | Cool white (6500K) |
| `set [target] to 4000K` | Specific color temperature |

### Scenes

| Command | Description |
|---------|-------------|
| `relax mode in [room]` | Activate Relax scene |
| `energize [room]` | Activate Energize scene |
| `concentrate in [room]` | Activate Concentrate scene |
| `[scene name] in [room]` | Activate any scene by name |

### Effects

| Command | Description |
|---------|-------------|
| `candle effect on [target]` | Flickering candle effect |
| `fire effect on [target]` | Fireplace effect |
| `sparkle [target]` | Sparkle effect |
| `stop effect on [target]` | Clear active effect |

### Timed Effects

| Command | Description |
|---------|-------------|
| `sunrise in [target]` | 30-minute sunrise simulation |
| `sunset in [target]` | 30-minute sunset simulation |
| `sunrise in [target] over 60 minutes` | Custom duration |

### Transitions

Append to any command:

| Modifier | Description |
|----------|-------------|
| `... slowly` | 2-second transition |
| `... instantly` | No transition |
| `... in 5 seconds` | Custom transition time |

### Built-in Commands

| Command | Description |
|---------|-------------|
| `help` | Show command help |
| `status` | System overview |
| `status [target]` | Detailed target info |
| `lights` | List all lights |
| `rooms` | List all rooms |
| `zones` | List all zones |
| `scenes` | List all scenes |
| `effects` | List available effects |
| `temps` | List color temperature presets |
| `entertainment` | List entertainment configurations |
| `refresh` | Re-sync state from bridge |
| `wizard [type]` | Run interactive wizard |
| `quit` / `exit` | Exit the CLI |

### Interactive Wizards

Launch guided wizards for complex operations:

```
hue> wizard scene      # Create or modify scenes
hue> wizard room       # Set up rooms
hue> wizard zone       # Configure zones
hue> wizard entertainment  # Set up entertainment areas
```

## Project Structure

```
hue-controller/
├── cli_interface.py           # Interactive REPL entry point
├── setup_bridge.py            # One-time bridge setup
├── config.json                # Credentials (gitignored)
├── requirements.txt           # Python dependencies
│
└── hue_controller/            # Core library
    ├── __init__.py
    ├── models.py              # Data models (Light, Room, Scene, etc.)
    ├── exceptions.py          # Custom exceptions
    ├── constants.py           # Configuration constants
    ├── color_utils.py         # Color space conversions
    ├── bridge_connector.py    # HTTP client, discovery, auth
    ├── device_manager.py      # State cache, fuzzy matching
    ├── command_interpreter.py # NLP parsing, command execution
    │
    ├── managers/              # Feature managers
    │   ├── scene_manager.py       # Scene CRUD operations
    │   ├── group_manager.py       # Room/zone management
    │   ├── effects_manager.py     # Light effects & gradients
    │   └── entertainment_manager.py
    │
    └── wizards/               # Interactive wizards
        ├── base_wizard.py
        ├── scene_wizard.py
        ├── group_wizard.py
        └── entertainment_wizard.py
```

## API Usage

### As a Library

```python
import asyncio
from hue_controller import BridgeConnector, DeviceManager

async def main():
    # Connect to bridge
    connector = BridgeConnector("config.json")

    # Initialize device manager
    dm = DeviceManager(connector)
    await dm.sync_state()

    # Find and control a target
    light = dm.find_target("living room")
    await connector.put(
        f"/resource/light/{light.id}",
        {"on": {"on": True}, "dimming": {"brightness": 75}}
    )

    # Use the command interpreter for natural language
    from hue_controller import CommandInterpreter, CommandExecutor

    interpreter = CommandInterpreter(dm)
    executor = CommandExecutor(dm)

    parsed = interpreter.parse("dim kitchen to 50%")
    result = await executor.execute(parsed)
    print(result.message)

    await connector.close()

asyncio.run(main())
```

### Scene Management

```python
from hue_controller.managers import SceneManager

scene_manager = SceneManager(connector, device_manager)

# Create a scene from current light states
await scene_manager.create_scene_from_current_state(
    room=room,
    name="Movie Night"
)

# Recall a scene with transition
await scene_manager.recall_scene(
    scene_id="abc123",
    transition_ms=2000
)
```

### Color Utilities

```python
from hue_controller.color_utils import rgb_to_xy, hex_to_xy, parse_color

# Convert RGB to CIE xy color space
xy = rgb_to_xy(255, 0, 0)  # XYColor(x=0.6484, y=0.3309)

# Parse various color formats
payload = parse_color("warm")      # {"color_temperature": {"mirek": 370}}
payload = parse_color("#FF5500")   # {"color": {"xy": {...}}}
payload = parse_color("4000K")     # {"color_temperature": {"mirek": 250}}
```

### Effects

```python
from hue_controller.managers import EffectsManager

effects = EffectsManager(connector, device_manager)

# Apply a light effect
await effects.set_effect(light, "candle")

# Start a timed sunrise effect
await effects.start_sunrise(
    target=room,
    duration_minutes=30
)
```

## Configuration

Credentials are stored in `config.json`:

```json
{
  "bridge_ip": "192.168.1.100",
  "application_key": "your-40-character-key",
  "bridge_id": "001788FFFE123456"
}
```

This file is:
- Created automatically by `setup_bridge.py`
- Stored with restricted permissions (0600)
- Should be added to `.gitignore`

### CLI Options

```bash
python cli_interface.py --help

Options:
  --config PATH   Path to config file (default: config.json)
  -v, --verbose   Enable verbose logging
```

## Troubleshooting

### Bridge Not Found

- Ensure your bridge is powered on and connected to the network
- Verify you're on the same network/VLAN as the bridge
- Try entering the bridge IP manually during setup
- Check if mDNS is blocked by your router/firewall

### Authentication Failed

- Press the link button **before** the 30-second timeout
- The link button is the large round button on top of the bridge
- Delete `config.json` and run setup again

### Lights Not Responding

- Check `status` — lights may show as "unreachable"
- Unreachable usually means the physical switch is off
- Run `refresh` to re-sync state from the bridge
- Verify the light is still paired in the official Hue app

### Rate Limit Errors

- The bridge limits requests: ~10/sec for lights, ~1/sec for groups
- Wait a few seconds and retry
- Use room/zone commands instead of individual lights
- The built-in rate limiter should prevent most issues

### Arrow Keys Show Escape Codes

- This was fixed in v2.0 with readline support
- Ensure you're running the latest version
- History is stored in `~/.hue_history`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **[Claude Code](https://claude.ai/code)** — This entire application was designed and written by Claude Code, Anthropic's AI coding assistant
- **[Philips Hue Developer Program](https://developers.meethue.com/)** — API documentation and developer resources
- **Color Science** — CIE xy color space conversion based on Philips technical guidance

---

<p align="center">
  <sub>Built with Claude Code by Anthropic</sub>
</p>
