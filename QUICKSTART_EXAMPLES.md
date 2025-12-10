# Quickstart Examples

Practical examples for controlling your Philips Hue lights with Hue Controller.

## Table of Contents

- [CLI Examples](#cli-examples)
  - [Basic Control](#basic-control)
  - [Brightness](#brightness)
  - [Colors](#colors)
  - [Scenes](#scenes)
  - [Effects](#effects)
  - [Transitions](#transitions)
  - [Status & Information](#status--information)
- [Programmatic Examples](#programmatic-examples)
  - [Basic Setup](#basic-setup)
  - [Controlling Lights](#controlling-lights)
  - [Working with Rooms](#working-with-rooms)
  - [Scene Management](#scene-management)
  - [Color Utilities](#color-utilities)
  - [Effects & Animations](#effects--animations)
  - [Event Listening](#event-listening)
  - [Error Handling](#error-handling)

---

## CLI Examples

Launch the CLI with:
```bash
python cli_interface.py
```

### Basic Control

```bash
# Turn lights on/off
hue> turn on living room
hue> turn off kitchen
hue> turn on bedroom lamp
hue> turn off all lights

# Target types: light names, room names, zone names
hue> turn on Office                  # Room
hue> turn on Reading Nook            # Zone
hue> turn on Desk Lamp               # Individual light
```

### Brightness

```bash
# Set specific brightness
hue> dim living room to 50%
hue> set kitchen to 75%
hue> dim bedroom to 10%

# Use presets
hue> set office to low               # 25%
hue> set office to half              # 50%
hue> brighten office                 # 100%

# Relative adjustments
hue> dim kitchen                     # Reduce brightness
hue> brighten bedroom                # Increase brightness
```

### Colors

```bash
# Named colors
hue> set bedroom to red
hue> set living room to blue
hue> make kitchen orange
hue> set office to purple

# Hex codes
hue> set bedroom to #FF5500
hue> set living room to #00FF88
hue> set kitchen to #FFE4B5

# RGB values
hue> set bedroom to rgb(255, 100, 0)
hue> set living room to rgb(0, 255, 136)

# Color temperature (Kelvin)
hue> set office to 2700K             # Warm/candlelight
hue> set kitchen to 4000K            # Neutral white
hue> set bathroom to 6500K           # Daylight/cool

# Temperature presets
hue> make bedroom warm               # 2700K
hue> make office cool                # 6500K
hue> set kitchen to daylight         # 6500K
hue> set living room to candlelight  # 2200K
```

### Scenes

```bash
# Activate built-in scenes
hue> relax mode in living room
hue> energize kitchen
hue> concentrate in office
hue> nightlight in bedroom

# Activate custom scenes
hue> movie night in living room
hue> dinner party in kitchen
hue> reading mode in office

# Scene shortcuts
hue> relax in bedroom                # Same as "relax mode in bedroom"
```

### Effects

```bash
# Light effects
hue> candle effect on bedroom
hue> fire effect on living room
hue> sparkle kitchen

# Stop effects
hue> stop effect on bedroom
hue> clear effect on living room

# Timed effects (sunrise/sunset simulation)
hue> sunrise in bedroom
hue> sunset in living room

# Custom duration
hue> sunrise in bedroom over 60 minutes
hue> sunset in living room over 45 minutes

# Identify a light (makes it blink)
hue> identify desk lamp
hue> find kitchen light
```

### Transitions

```bash
# Append transition modifiers to any command
hue> turn on living room slowly           # 2 second fade
hue> turn off bedroom instantly           # No transition
hue> dim kitchen to 50% in 5 seconds      # Custom duration
hue> set office to warm in 10 seconds

# Combine with other commands
hue> set bedroom to red slowly
hue> relax mode in living room in 3 seconds
```

### Status & Information

```bash
# System overview
hue> status
# Output:
# Bridge: 192.168.1.100
# Lights: 5/12 on (1 unreachable)
# Rooms: 4
# Scenes: 8

# Detailed target status
hue> status living room
hue> status desk lamp

# List resources
hue> lights                          # All lights with status
hue> rooms                           # All rooms
hue> zones                           # All zones
hue> scenes                          # All scenes by room
hue> effects                         # Available effects
hue> temps                           # Color temperature presets

# Refresh state from bridge
hue> refresh

# Interactive wizards
hue> wizard scene                    # Scene creation wizard
hue> wizard room                     # Room setup wizard
hue> wizard zone                     # Zone configuration wizard
```

---

## Programmatic Examples

### Basic Setup

```python
import asyncio
from hue_controller import BridgeConnector, DeviceManager

async def main():
    # Initialize connector with config file
    connector = BridgeConnector("config.json")

    # Check if configured
    if not connector.is_configured:
        print("Please run setup_bridge.py first")
        return

    # Initialize device manager and sync state
    dm = DeviceManager(connector)
    await dm.sync_state()

    print(f"Connected! Found {len(dm.lights)} lights")

    # ... your code here ...

    # Always clean up
    await connector.close()

asyncio.run(main())
```

### Controlling Lights

```python
import asyncio
from hue_controller import BridgeConnector, DeviceManager

async def main():
    connector = BridgeConnector("config.json")
    dm = DeviceManager(connector)
    await dm.sync_state()

    # Find a light by name (fuzzy matching)
    light = dm.find_target("desk lamp")

    # Turn on
    await connector.put(
        f"/resource/light/{light.id}",
        {"on": {"on": True}}
    )

    # Set brightness (0-100)
    await connector.put(
        f"/resource/light/{light.id}",
        {"dimming": {"brightness": 75}}
    )

    # Set color (CIE xy color space)
    await connector.put(
        f"/resource/light/{light.id}",
        {"color": {"xy": {"x": 0.6, "y": 0.35}}}
    )

    # Set color temperature (mirek = 1,000,000 / Kelvin)
    # 153 mirek = 6535K (cool), 500 mirek = 2000K (warm)
    await connector.put(
        f"/resource/light/{light.id}",
        {"color_temperature": {"mirek": 250}}  # ~4000K
    )

    # Combined: on + brightness + transition
    await connector.put(
        f"/resource/light/{light.id}",
        {
            "on": {"on": True},
            "dimming": {"brightness": 50},
            "dynamics": {"duration": 1000}  # 1 second transition
        }
    )

    # Turn off with slow fade
    await connector.put(
        f"/resource/light/{light.id}",
        {
            "on": {"on": False},
            "dynamics": {"duration": 5000}  # 5 second fade out
        }
    )

    await connector.close()

asyncio.run(main())
```

### Working with Rooms

```python
import asyncio
from hue_controller import BridgeConnector, DeviceManager

async def main():
    connector = BridgeConnector("config.json")
    dm = DeviceManager(connector)
    await dm.sync_state()

    # Find a room
    room = dm.find_target("living room")

    # Get the grouped_light service for the room
    grouped_light = dm.grouped_lights.get(room.grouped_light_id)

    # Control all lights in room at once (more efficient)
    await connector.put(
        f"/resource/grouped_light/{grouped_light.id}",
        {
            "on": {"on": True},
            "dimming": {"brightness": 60}
        }
    )

    # Get individual lights in a room
    lights = dm.get_lights_for_target(room)
    for light in lights:
        print(f"  {light.name}: {'on' if light.on else 'off'}")

    # Check for unreachable lights
    unreachable = dm.get_unreachable_lights(room)
    if unreachable:
        print(f"Warning: {len(unreachable)} lights unreachable")

    # List all rooms
    for room in dm.rooms.values():
        print(f"Room: {room.name}")

    # List all zones
    for zone in dm.zones.values():
        print(f"Zone: {zone.name}")

    await connector.close()

asyncio.run(main())
```

### Scene Management

```python
import asyncio
from hue_controller import BridgeConnector, DeviceManager
from hue_controller.managers import SceneManager

async def main():
    connector = BridgeConnector("config.json")
    dm = DeviceManager(connector)
    await dm.sync_state()

    scene_manager = SceneManager(connector, dm)

    # List all scenes
    scenes = await scene_manager.list_scenes()
    for scene in scenes:
        print(f"{scene.name} (Room: {scene.group_name})")

    # Find a scene by name
    scene = dm.find_scene("relax", room_hint="living room")

    # Recall/activate a scene
    await scene_manager.recall_scene(scene.id)

    # Recall with custom transition
    await scene_manager.recall_scene(
        scene.id,
        transition_ms=3000  # 3 second transition
    )

    # Create a scene from current light states
    room = dm.find_target("bedroom")
    new_scene = await scene_manager.create_scene_from_current_state(
        room=room,
        name="Cozy Evening"
    )
    print(f"Created scene: {new_scene.name}")

    # Duplicate an existing scene
    duplicated = await scene_manager.duplicate_scene(
        scene_id=scene.id,
        new_name="Relax Copy"
    )

    # Rename a scene
    await scene_manager.rename_scene(
        scene_id=duplicated.id,
        new_name="Super Relax"
    )

    # Delete a scene
    await scene_manager.delete_scene(duplicated.id)

    # Get detailed scene info
    details = await scene_manager.get_scene_details(scene.id)
    print(f"Scene has {len(details.actions)} light actions")

    await connector.close()

asyncio.run(main())
```

### Color Utilities

```python
from hue_controller.color_utils import (
    rgb_to_xy,
    hex_to_xy,
    parse_color,
    kelvin_to_mirek,
    XYColor
)

# Convert RGB to CIE xy (for Hue API)
xy = rgb_to_xy(255, 0, 0)  # Red
print(f"Red: x={xy.x:.4f}, y={xy.y:.4f}")

xy = rgb_to_xy(0, 255, 0)  # Green
xy = rgb_to_xy(0, 0, 255)  # Blue
xy = rgb_to_xy(255, 165, 0)  # Orange

# Convert hex to xy
xy = hex_to_xy("#FF5500")
xy = hex_to_xy("FF5500")  # # is optional
xy = hex_to_xy("#00FF88")

# Parse any color format (returns API-ready payload)
payload = parse_color("red")
# Returns: {"color": {"xy": {"x": 0.6784, "y": 0.3174}}}

payload = parse_color("#FF5500")
# Returns: {"color": {"xy": {"x": ..., "y": ...}}}

payload = parse_color("warm")
# Returns: {"color_temperature": {"mirek": 370}}

payload = parse_color("4000K")
# Returns: {"color_temperature": {"mirek": 250}}

payload = parse_color("rgb(255, 100, 50)")
# Returns: {"color": {"xy": {"x": ..., "y": ...}}}

# Color temperature conversion
mirek = kelvin_to_mirek(2700)  # 370 mirek (warm)
mirek = kelvin_to_mirek(4000)  # 250 mirek (neutral)
mirek = kelvin_to_mirek(6500)  # 153 mirek (cool)

# Use in API calls
import asyncio
from hue_controller import BridgeConnector, DeviceManager

async def set_light_color(light_id: str, color_spec: str):
    connector = BridgeConnector("config.json")

    payload = parse_color(color_spec)
    await connector.put(f"/resource/light/{light_id}", payload)

    await connector.close()

# asyncio.run(set_light_color("abc123", "warm"))
# asyncio.run(set_light_color("abc123", "#FF5500"))
# asyncio.run(set_light_color("abc123", "blue"))
```

### Effects & Animations

```python
import asyncio
from hue_controller import BridgeConnector, DeviceManager
from hue_controller.managers import EffectsManager

async def main():
    connector = BridgeConnector("config.json")
    dm = DeviceManager(connector)
    await dm.sync_state()

    effects = EffectsManager(connector, dm)

    # Get available effects for a light
    light = dm.find_target("desk lamp")
    supported = await effects.get_supported_effects(light)
    print(f"Supported effects: {supported}")
    # e.g., ['candle', 'fire', 'prism', 'sparkle']

    # Apply an effect
    await effects.set_effect(light, "candle")

    # Clear effect
    await effects.clear_effect(light)

    # Timed effects (sunrise/sunset)
    room = dm.find_target("bedroom")

    # Start sunrise (default 30 minutes)
    await effects.start_sunrise(room)

    # Custom duration sunrise
    await effects.start_sunrise(room, duration_minutes=60)

    # Sunset effect
    await effects.start_sunset(room, duration_minutes=45)

    # Stop timed effect
    await effects.stop_timed_effect(room)

    # Flash/signal a light
    await effects.flash(light)
    await effects.flash_color(light, color_xy=(0.6, 0.35))  # Flash red

    # Identify (blink) a light
    await effects.identify_light(light)

    await connector.close()

asyncio.run(main())
```

### Event Listening

```python
import asyncio
from hue_controller import BridgeConnector, DeviceManager

async def main():
    connector = BridgeConnector("config.json")
    dm = DeviceManager(connector)
    await dm.sync_state()

    # Start listening for real-time events from bridge
    await dm.start_event_listener()

    print("Listening for changes... (Ctrl+C to stop)")
    print("Try changing lights with the Hue app!")

    # Monitor for changes
    previous_states = {
        light.id: light.on
        for light in dm.lights.values()
    }

    try:
        while True:
            await asyncio.sleep(1)

            # Check for state changes
            for light in dm.lights.values():
                prev = previous_states.get(light.id)
                if prev != light.on:
                    status = "on" if light.on else "off"
                    print(f"{light.name} turned {status}")
                    previous_states[light.id] = light.on

    except KeyboardInterrupt:
        print("\nStopping...")

    await dm.stop_event_listener()
    await connector.close()

asyncio.run(main())
```

### Error Handling

```python
import asyncio
from hue_controller import BridgeConnector, DeviceManager
from hue_controller.exceptions import (
    HueError,
    ConnectionError,
    AuthenticationError,
    ResourceNotFoundError,
    RateLimitError
)

async def main():
    try:
        connector = BridgeConnector("config.json")

        if not connector.is_configured:
            print("Not configured. Run setup_bridge.py first.")
            return

        dm = DeviceManager(connector)
        await dm.sync_state()

        # Find target with error handling
        try:
            light = dm.find_target("nonexistent light")
        except ResourceNotFoundError:
            print("Light not found!")
            # List available targets
            targets = dm.list_all_targets()
            print(f"Available: {[t.name for t in targets[:5]]}...")

        # Handle rate limiting
        try:
            # Rapid commands might hit rate limit
            for i in range(20):
                await connector.put(
                    f"/resource/light/{light.id}",
                    {"dimming": {"brightness": i * 5}}
                )
        except RateLimitError:
            print("Rate limited! Waiting...")
            await asyncio.sleep(1)

        # General API errors
        try:
            await connector.put("/resource/light/invalid-id", {"on": {"on": True}})
        except HueError as e:
            print(f"API error: {e}")

    except ConnectionError:
        print("Could not connect to bridge. Check network.")
    except AuthenticationError:
        print("Authentication failed. Re-run setup_bridge.py")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if 'connector' in locals():
            await connector.close()

asyncio.run(main())
```

---

## Complete Example: Smart Morning Routine

```python
"""
Complete example: Automated morning wake-up routine
Gradually brightens lights and adjusts color temperature
"""

import asyncio
from hue_controller import BridgeConnector, DeviceManager
from hue_controller.managers import EffectsManager, SceneManager
from hue_controller.color_utils import kelvin_to_mirek

async def morning_routine():
    # Setup
    connector = BridgeConnector("config.json")
    dm = DeviceManager(connector)
    await dm.sync_state()

    effects = EffectsManager(connector, dm)
    scenes = SceneManager(connector, dm)

    bedroom = dm.find_target("bedroom")
    kitchen = dm.find_target("kitchen")

    print("Starting morning routine...")

    # Phase 1: Gentle sunrise in bedroom (15 minutes)
    print("  Starting bedroom sunrise...")
    await effects.start_sunrise(bedroom, duration_minutes=15)

    # Wait for sunrise to complete
    await asyncio.sleep(15 * 60)

    # Phase 2: Bright, cool light for alertness
    print("  Setting energize mode...")
    grouped_light = dm.grouped_lights.get(bedroom.grouped_light_id)
    await connector.put(
        f"/resource/grouped_light/{grouped_light.id}",
        {
            "on": {"on": True},
            "dimming": {"brightness": 100},
            "color_temperature": {"mirek": kelvin_to_mirek(5000)},
            "dynamics": {"duration": 2000}
        }
    )

    # Phase 3: Turn on kitchen
    print("  Turning on kitchen...")
    kitchen_grouped = dm.grouped_lights.get(kitchen.grouped_light_id)
    await connector.put(
        f"/resource/grouped_light/{kitchen_grouped.id}",
        {
            "on": {"on": True},
            "dimming": {"brightness": 80},
            "color_temperature": {"mirek": kelvin_to_mirek(4000)}
        }
    )

    print("Morning routine complete!")
    await connector.close()

if __name__ == "__main__":
    asyncio.run(morning_routine())
```

---

## Complete Example: Party Mode

```python
"""
Complete example: Party lighting with color cycling
"""

import asyncio
import random
from hue_controller import BridgeConnector, DeviceManager
from hue_controller.color_utils import rgb_to_xy

# Party colors
PARTY_COLORS = [
    (255, 0, 0),    # Red
    (0, 255, 0),    # Green
    (0, 0, 255),    # Blue
    (255, 0, 255),  # Magenta
    (255, 255, 0),  # Yellow
    (0, 255, 255),  # Cyan
    (255, 128, 0),  # Orange
]

async def party_mode(room_name: str, duration_seconds: int = 60):
    connector = BridgeConnector("config.json")
    dm = DeviceManager(connector)
    await dm.sync_state()

    room = dm.find_target(room_name)
    lights = dm.get_lights_for_target(room)

    # Filter to only color-capable lights
    color_lights = [l for l in lights if l.color_capable]

    if not color_lights:
        print("No color-capable lights in this room!")
        await connector.close()
        return

    print(f"Party mode: {len(color_lights)} lights for {duration_seconds}s")

    # Turn all lights on at full brightness
    for light in color_lights:
        await connector.put(
            f"/resource/light/{light.id}",
            {"on": {"on": True}, "dimming": {"brightness": 100}}
        )

    # Color cycle
    end_time = asyncio.get_event_loop().time() + duration_seconds

    try:
        while asyncio.get_event_loop().time() < end_time:
            for light in color_lights:
                # Random color
                r, g, b = random.choice(PARTY_COLORS)
                xy = rgb_to_xy(r, g, b)

                await connector.put(
                    f"/resource/light/{light.id}",
                    {
                        "color": {"xy": {"x": xy.x, "y": xy.y}},
                        "dynamics": {"duration": 500}
                    }
                )

            await asyncio.sleep(1)  # Change every second

    except KeyboardInterrupt:
        print("\nStopping party mode...")

    # Reset to warm white
    print("Resetting lights...")
    for light in color_lights:
        await connector.put(
            f"/resource/light/{light.id}",
            {
                "color_temperature": {"mirek": 370},
                "dimming": {"brightness": 50},
                "dynamics": {"duration": 1000}
            }
        )

    await connector.close()
    print("Party mode ended!")

if __name__ == "__main__":
    asyncio.run(party_mode("living room", duration_seconds=120))
```

---

<p align="center">
  <sub>Built with Claude Code by Anthropic</sub>
</p>
