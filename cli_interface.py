#!/usr/bin/env python3
"""
Hue Controller CLI Interface

A natural language REPL for controlling your Philips Hue lights.

Usage:
    python cli_interface.py [--config CONFIG_PATH]

Commands:
    help        - Show available commands
    status      - Show system status
    lights      - List all lights
    rooms       - List all rooms
    scenes      - List all scenes
    refresh     - Re-sync device state
    quit/exit   - Exit the CLI
"""

import argparse
import asyncio
import logging
import sys
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


class HueCLI:
    """Interactive CLI for Hue control."""

    VERSION = "1.0.0"
    PROMPT = "hue> "

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.connector: Optional["BridgeConnector"] = None
        self.device_manager: Optional["DeviceManager"] = None
        self.interpreter: Optional["CommandInterpreter"] = None
        self.executor: Optional["CommandExecutor"] = None
        self._running = False

    async def initialize(self) -> bool:
        """Initialize the CLI and connect to bridge."""
        try:
            from hue_controller.bridge_connector import BridgeConnector
            from hue_controller.device_manager import DeviceManager
            from hue_controller.command_interpreter import CommandInterpreter, CommandExecutor
            from hue_controller.exceptions import ConnectionError
        except ImportError as e:
            print(f"Error: Could not import hue_controller. {e}")
            print("Make sure you've installed the dependencies:")
            print("  pip install httpx zeroconf")
            return False

        # Initialize connector
        self.connector = BridgeConnector(self.config_path)

        if not self.connector.is_configured:
            print("Error: No bridge configuration found.")
            print("Please run setup first:")
            print("  python setup_bridge.py")
            return False

        print(f"Hue Controller v{self.VERSION}")
        print(f"Connecting to bridge at {self.connector.bridge_ip}...")

        # Initialize device manager
        self.device_manager = DeviceManager(self.connector)

        try:
            await self.device_manager.sync_state()
        except Exception as e:
            print(f"Error: Could not sync device state: {e}")
            return False

        # Initialize interpreter and executor
        self.interpreter = CommandInterpreter(self.device_manager)
        self.executor = CommandExecutor(self.device_manager)

        # Print summary
        lights = len(self.device_manager.lights)
        rooms = len(self.device_manager.rooms)
        zones = len(self.device_manager.zones)
        scenes = len(self.device_manager.scenes)

        print(f"Connected! Found {lights} lights, {rooms} rooms, {zones} zones, {scenes} scenes")
        print()
        print('Type "help" for commands or enter a command like "turn on living room"')
        print()

        return True

    async def run(self) -> None:
        """Run the interactive REPL."""
        self._running = True

        while self._running:
            try:
                # Read input
                try:
                    line = input(self.PROMPT).strip()
                except EOFError:
                    break

                if not line:
                    continue

                # Process command
                await self.process_input(line)

            except KeyboardInterrupt:
                print()  # New line after ^C
                continue

        print("Goodbye!")

    async def process_input(self, line: str) -> None:
        """Process a line of input."""
        lower = line.lower().strip()

        # Built-in commands
        if lower in ("quit", "exit", "q"):
            self._running = False
            return

        if lower in ("help", "?"):
            self.show_help()
            return

        if lower == "status":
            await self.show_status()
            return

        if lower in ("lights", "list lights"):
            self.list_lights()
            return

        if lower in ("rooms", "list rooms"):
            self.list_rooms()
            return

        if lower in ("zones", "list zones"):
            self.list_zones()
            return

        if lower in ("scenes", "list scenes"):
            self.list_scenes()
            return

        if lower in ("refresh", "sync"):
            await self.refresh()
            return

        if lower.startswith("status "):
            target_name = line[7:].strip()
            self.show_target_status(target_name)
            return

        # Try to parse as Hue command
        await self.execute_command(line)

    def show_help(self) -> None:
        """Display help information."""
        print(self.interpreter.get_help_text())
        print()
        print("Built-in commands:")
        print("  help              - Show this help")
        print("  status            - Show overall system status")
        print("  status [target]   - Show status of a specific light/room")
        print("  lights            - List all lights")
        print("  rooms             - List all rooms")
        print("  zones             - List all zones")
        print("  scenes            - List all scenes")
        print("  refresh           - Re-sync device state from bridge")
        print("  quit              - Exit the CLI")
        print()

    async def show_status(self) -> None:
        """Show overall system status."""
        dm = self.device_manager

        on_count = sum(1 for l in dm.lights.values() if l.is_on)
        total_lights = len(dm.lights)
        unreachable = sum(1 for l in dm.lights.values() if not l.is_reachable)

        print(f"Bridge: {self.connector.bridge_ip}")
        print(f"Lights: {on_count}/{total_lights} on", end="")
        if unreachable > 0:
            print(f" ({unreachable} unreachable)", end="")
        print()
        print(f"Rooms: {len(dm.rooms)}")
        print(f"Zones: {len(dm.zones)}")
        print(f"Scenes: {len(dm.scenes)}")
        print()

    def list_lights(self) -> None:
        """List all lights with their status."""
        lights = sorted(self.device_manager.lights.values(), key=lambda l: l.name)

        if not lights:
            print("No lights found.")
            return

        print("Lights:")
        for light in lights:
            status = "on" if light.is_on else "off"
            brightness = f"{light.brightness:.0f}%" if light.is_on else ""
            reachable = "" if light.is_reachable else " [unreachable]"

            print(f"  {light.name}: {status} {brightness}{reachable}")
        print()

    def list_rooms(self) -> None:
        """List all rooms."""
        rooms = sorted(self.device_manager.rooms.values(), key=lambda r: r.name)

        if not rooms:
            print("No rooms found.")
            return

        print("Rooms:")
        for room in rooms:
            light_count = len(self.device_manager.get_lights_for_target(room))
            print(f"  {room.name} ({light_count} lights)")
        print()

    def list_zones(self) -> None:
        """List all zones."""
        zones = sorted(self.device_manager.zones.values(), key=lambda z: z.name)

        if not zones:
            print("No zones found.")
            return

        print("Zones:")
        for zone in zones:
            light_count = len(self.device_manager.get_lights_for_target(zone))
            print(f"  {zone.name} ({light_count} lights)")
        print()

    def list_scenes(self) -> None:
        """List all scenes grouped by room."""
        dm = self.device_manager

        if not dm.scenes:
            print("No scenes found.")
            return

        # Group scenes by room
        scenes_by_group: dict[str, list] = {}
        for scene in dm.scenes.values():
            group_name = "Unknown"
            if scene.group_id:
                if scene.group_id in dm.rooms:
                    group_name = dm.rooms[scene.group_id].name
                elif scene.group_id in dm.zones:
                    group_name = dm.zones[scene.group_id].name

            if group_name not in scenes_by_group:
                scenes_by_group[group_name] = []
            scenes_by_group[group_name].append(scene.name)

        print("Scenes:")
        for group_name in sorted(scenes_by_group.keys()):
            print(f"  {group_name}:")
            for scene_name in sorted(scenes_by_group[group_name]):
                print(f"    - {scene_name}")
        print()

    def show_target_status(self, target_name: str) -> None:
        """Show detailed status for a specific target."""
        target = self.device_manager.find_target(target_name)

        if not target:
            print(f"Target '{target_name}' not found.")
            return

        from hue_controller.models import Light, Room, Zone

        if isinstance(target, Light):
            print(f"Light: {target.name}")
            print(f"  State: {'on' if target.is_on else 'off'}")
            print(f"  Brightness: {target.brightness:.0f}%")
            print(f"  Reachable: {'yes' if target.is_reachable else 'no'}")
            if target.supports_color and target.color_xy:
                print(f"  Color XY: ({target.color_xy.x:.4f}, {target.color_xy.y:.4f})")
            if target.supports_color_temperature and target.color_temperature_mirek:
                kelvin = int(1_000_000 / target.color_temperature_mirek)
                print(f"  Color Temp: {kelvin}K")

        elif isinstance(target, (Room, Zone)):
            type_name = "Room" if isinstance(target, Room) else "Zone"
            print(f"{type_name}: {target.name}")

            lights = self.device_manager.get_lights_for_target(target)
            on_count = sum(1 for l in lights if l.is_on)
            unreachable = sum(1 for l in lights if not l.is_reachable)

            print(f"  Lights: {on_count}/{len(lights)} on", end="")
            if unreachable > 0:
                print(f" ({unreachable} unreachable)", end="")
            print()

            # List lights in this room/zone
            for light in lights:
                status = "on" if light.is_on else "off"
                reach = "" if light.is_reachable else " [unreachable]"
                print(f"    - {light.name}: {status}{reach}")

            # List scenes
            if isinstance(target, (Room, Zone)):
                scenes = self.device_manager.get_scenes_for_group(target)
                if scenes:
                    print(f"  Scenes: {', '.join(s.name for s in scenes)}")

        print()

    async def refresh(self) -> None:
        """Re-sync device state from bridge."""
        print("Syncing...")
        try:
            await self.device_manager.sync_state()
            print("Done!")
        except Exception as e:
            print(f"Error: {e}")
        print()

    async def execute_command(self, command: str) -> None:
        """Parse and execute a Hue command."""
        from hue_controller.exceptions import (
            InvalidCommandError,
            TargetNotFoundError,
            SceneNotFoundError,
        )

        try:
            parsed = self.interpreter.parse(command)
            result = await self.executor.execute(parsed)

            if result.success:
                print(f"  {result.message}")
                if result.unreachable_lights:
                    print(f"  Note: {len(result.unreachable_lights)} light(s) unreachable: "
                          f"{', '.join(result.unreachable_lights)}")
            else:
                print(f"  Failed: {result.message}")
                for error in result.errors:
                    print(f"    - {error}")

        except InvalidCommandError as e:
            print(f"  Could not understand: {e.command}")
            print('  Type "help" for available commands')

        except TargetNotFoundError as e:
            print(f"  Target not found: {e.target_name}")
            print('  Type "lights" or "rooms" to see available targets')

        except SceneNotFoundError as e:
            print(f"  Scene not found: {e.scene_name}")
            if e.room_name:
                print(f"  in room: {e.room_name}")
            print('  Type "scenes" to see available scenes')

        except Exception as e:
            print(f"  Error: {e}")

        print()

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.device_manager:
            await self.device_manager.stop_event_listener()
        if self.connector:
            await self.connector.close()


async def main_async(config_path: str) -> int:
    """Async main entry point."""
    cli = HueCLI(config_path)

    try:
        if not await cli.initialize():
            return 1

        await cli.run()
        return 0

    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 1

    finally:
        await cli.cleanup()


def main():
    parser = argparse.ArgumentParser(
        description="Natural language CLI for Philips Hue"
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to configuration file (default: config.json)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        return_code = asyncio.run(main_async(args.config))
        sys.exit(return_code)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)


if __name__ == "__main__":
    main()
