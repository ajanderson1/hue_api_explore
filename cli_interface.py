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
    zones       - List all zones
    scenes      - List all scenes
    effects     - List available effects
    refresh     - Re-sync device state
    wizard X    - Run interactive wizard (scene/room/zone/entertainment)
    quit/exit   - Exit the CLI
"""

import argparse
import asyncio
import logging
import os
import readline
import sys
import time
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


class HueCLI:
    """Interactive CLI for Hue control."""

    VERSION = "2.0.0"
    PROMPT = "hue> "
    HISTORY_FILE = os.path.expanduser("~/.hue_history")
    HISTORY_LENGTH = 500
    DOUBLE_CTRL_C_THRESHOLD = 1.0  # seconds

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.connector: Optional["BridgeConnector"] = None
        self.device_manager: Optional["DeviceManager"] = None
        self.interpreter: Optional["CommandInterpreter"] = None
        self.executor: Optional["CommandExecutor"] = None
        # Managers for extended functionality
        self.scene_manager = None
        self.group_manager = None
        self.effects_manager = None
        self.entertainment_manager = None
        self._running = False
        self._last_interrupt_time: float = 0.0

    def _setup_readline(self) -> None:
        """Configure readline for command history and line editing."""
        readline.set_history_length(self.HISTORY_LENGTH)
        try:
            readline.read_history_file(self.HISTORY_FILE)
        except FileNotFoundError:
            pass  # No history file yet
        except (PermissionError, OSError):
            pass  # Can't read history file (e.g., macOS extended attributes)  # No history file yet

    def _save_history(self) -> None:
        """Save command history to file."""
        try:
            readline.write_history_file(self.HISTORY_FILE)
        except OSError:
            pass  # Silently fail if can't write

    async def initialize(self) -> bool:
        """Initialize the CLI and connect to bridge."""
        self._setup_readline()
        try:
            from hue_controller.bridge_connector import BridgeConnector
            from hue_controller.device_manager import DeviceManager
            from hue_controller.command_interpreter import CommandInterpreter, CommandExecutor
            from hue_controller.exceptions import ConnectionError
            from hue_controller.managers import (
                SceneManager, GroupManager, EffectsManager, EntertainmentManager
            )
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

        # Initialize managers
        self.scene_manager = SceneManager(self.connector, self.device_manager)
        self.group_manager = GroupManager(self.connector, self.device_manager)
        self.effects_manager = EffectsManager(self.connector, self.device_manager)
        self.entertainment_manager = EntertainmentManager(self.connector, self.device_manager)

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
                now = time.time()
                if now - self._last_interrupt_time < self.DOUBLE_CTRL_C_THRESHOLD:
                    print("\nForce exit.")
                    break
                self._last_interrupt_time = now
                print("  (Press Ctrl+C again to exit)")
                continue

        print("Goodbye!")

    async def process_input(self, line: str) -> None:
        """Process a line of input."""
        lower = line.lower().strip()

        # Check for glossary/help term commands first
        # These patterns: /help <term>, ?<term>, glossary
        if self._handle_help_command(line):
            return

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

        if lower in ("effects", "list effects"):
            self.list_effects()
            return

        if lower in ("entertainment", "list entertainment"):
            await self.list_entertainment()
            return

        if lower in ("temps", "temperatures", "list temps"):
            self.list_temperatures()
            return

        # Check for wizard commands
        if lower.startswith("wizard"):
            await self.run_wizard(lower)
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
        print("  effects           - List available effects")
        print("  temps             - List white temperature and duration presets")
        print("  entertainment     - List entertainment configurations")
        print("  refresh           - Re-sync device state from bridge")
        print()
        print("Wizards (interactive):")
        print("  wizard scene         - Scene creation/editing wizard (basic)")
        print("  wizard admin         - Advanced scene wizard (all options)")
        print("  wizard room          - Room management wizard")
        print("  wizard zone          - Zone management wizard")
        print("  wizard entertainment - Entertainment setup wizard")
        print()
        print("  quit              - Exit the CLI")
        print()
        print("Glossary:")
        print("  /help <term>      - Look up Hue terminology (e.g., /help mirek)")
        print("  ?<term>           - Quick term lookup (e.g., ?gamut)")
        print("  glossary          - List all available terms")
        print()

    def _handle_help_command(self, line: str) -> bool:
        """
        Handle glossary/help term lookup commands.

        Recognizes patterns like:
        - /help mirek
        - ?gamut
        - glossary

        Returns:
            True if this was a help command that was handled, False otherwise
        """
        from hue_controller.wizards.help_system import HelpSystem

        help_system = HelpSystem()
        return help_system.handle_help_command(line)

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

    def list_effects(self) -> None:
        """List available effects."""
        from hue_controller.constants import EFFECT_TYPES, EFFECT_DESCRIPTIONS

        print("Available Effects:")
        for effect in EFFECT_TYPES:
            if effect == "no_effect":
                continue
            desc = EFFECT_DESCRIPTIONS.get(effect, "")
            print(f"  {effect}: {desc}")

        print()
        print("Timed Effects:")
        print("  sunrise: Gradual wake-up light simulation")
        print("  sunset: Gradual wind-down light simulation")
        print()

    def list_temperatures(self) -> None:
        """List available white temperature presets."""
        from hue_controller.constants import (
            TEMPERATURE_BY_NAME,
            TEMPERATURE_DESCRIPTIONS,
            TIMED_EFFECT_DURATION_PRESETS,
            DURATION_PRESET_DESCRIPTIONS,
        )

        print("White Temperature Presets:")
        print()
        for name, mirek in TEMPERATURE_BY_NAME.items():
            kelvin = int(1_000_000 / mirek)
            desc = TEMPERATURE_DESCRIPTIONS.get(name, "")
            print(f"  {name:12} {kelvin:>5}K  {desc}")
        print()
        print("  You can also use Kelvin directly: 2700K, 4000K, etc.")
        print()
        print("Duration Presets (for sunrise/sunset):")
        print()
        for name, ms in TIMED_EFFECT_DURATION_PRESETS.items():
            desc = DURATION_PRESET_DESCRIPTIONS.get(name, "")
            print(f"  {name:8} {desc}")
        print()

    async def list_entertainment(self) -> None:
        """List entertainment configurations."""
        try:
            configs = await self.entertainment_manager.list_configurations()
        except Exception as e:
            print(f"Error: {e}")
            return

        if not configs:
            print("No entertainment configurations found.")
            print('Use "wizard entertainment" to create one.')
            print()
            return

        print("Entertainment Configurations:")
        for config in configs:
            print(f"  {config.name}")
            print(f"    Type: {config.configuration_type}")
            print(f"    Status: {config.status}")
            print(f"    Lights: {len(config.light_services)}")
        print()

    async def run_wizard(self, command: str) -> None:
        """Run an interactive wizard."""
        from hue_controller.wizards import (
            SceneWizard,
            GroupWizard,
            EntertainmentWizard,
        )
        from hue_controller.wizards.scene import run_scene_wizard

        wizard_type = command.replace("wizard", "").strip()

        try:
            if wizard_type in ("scene", "scenes"):
                # Unified scene wizard with mode selection
                result = await run_scene_wizard(self.connector, self.device_manager)

            elif wizard_type == "quick":
                # Quick scene wizard directly
                result = await run_scene_wizard(
                    self.connector, self.device_manager, mode="quick"
                )

            elif wizard_type in ("admin", "admin scene", "admin-scene", "advanced"):
                # Advanced mode of unified wizard
                result = await run_scene_wizard(
                    self.connector, self.device_manager, mode="advanced"
                )

            elif wizard_type in ("room", "rooms"):
                wizard = GroupWizard(self.connector, self.device_manager)
                result = await wizard.run_create_room()

            elif wizard_type in ("zone", "zones"):
                wizard = GroupWizard(self.connector, self.device_manager)
                result = await wizard.run_create_zone()

            elif wizard_type in ("group", "groups"):
                wizard = GroupWizard(self.connector, self.device_manager)
                result = await wizard.run()

            elif wizard_type in ("entertainment", "ent"):
                wizard = EntertainmentWizard(self.connector, self.device_manager)
                result = await wizard.run()

            elif not wizard_type:
                # Show wizard options
                print("Available wizards:")
                print("  wizard scene         - Create scenes (Quick/Standard/Advanced)")
                print("  wizard quick         - Quick scene setup (mood-first)")
                print("  wizard advanced      - Advanced scene wizard (all options)")
                print("  wizard room          - Create/manage rooms")
                print("  wizard zone          - Create/manage zones")
                print("  wizard entertainment - Setup entertainment areas")
                print()
                return

            else:
                print(f"Unknown wizard: {wizard_type}")
                print('Available: scene, quick, advanced, room, zone, entertainment')
                print()
                return

            # Refresh state after wizard completes
            if result.success:
                await self.device_manager.sync_state()

        except Exception as e:
            print(f"Wizard error: {e}")
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

            # Handle management commands
            if parsed.action_type == "management":
                await self._execute_management(parsed)
                return

            # Handle effect commands
            if parsed.action_type == "effect":
                await self._execute_effect(parsed)
                return

            # Handle timed effect commands
            if parsed.action_type == "timed_effect":
                await self._execute_timed_effect(parsed)
                return

            # Handle signal commands
            if parsed.action_type == "signal":
                await self._execute_signal(parsed)
                return

            # Standard commands go through executor
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

    async def _execute_management(self, parsed) -> None:
        """Execute a management command."""
        from hue_controller.wizards import SceneWizard, GroupWizard, EntertainmentWizard

        action = parsed.management_action

        # Wizard commands
        if action == "wizard_scene":
            wizard = SceneWizard(self.connector, self.device_manager)
            await wizard.run()
            await self.device_manager.sync_state()
            return
        elif action == "wizard_room":
            wizard = GroupWizard(self.connector, self.device_manager)
            await wizard.run_create_room()
            await self.device_manager.sync_state()
            return
        elif action == "wizard_zone":
            wizard = GroupWizard(self.connector, self.device_manager)
            await wizard.run_create_zone()
            await self.device_manager.sync_state()
            return
        elif action == "wizard_entertainment":
            wizard = EntertainmentWizard(self.connector, self.device_manager)
            await wizard.run()
            await self.device_manager.sync_state()
            return

        # Scene management
        if action == "delete_all_scenes_in_room":
            room_name = parsed.payload.get("room_name")
            force = parsed.payload.get("force", False)

            # Find the room
            room = self.device_manager.find_target(room_name)
            if not room or not hasattr(room, 'grouped_light_id'):
                print(f"  Room '{room_name}' not found")
                return

            # Get scenes for this room
            scenes = self.scene_manager.get_scenes_for_room(room.id)
            if not scenes:
                print(f"  No scenes found in '{room.name}'")
                return

            # Confirm unless force flag is set
            if not force:
                print(f"\n  This will delete {len(scenes)} scene(s) from '{room.name}':")
                for scene in scenes:
                    print(f"    - {scene.name}")
                print()
                confirm = input("  Are you sure? Type 'yes' to confirm: ").strip().lower()
                if confirm != "yes":
                    print("  Cancelled.")
                    return

            # Delete with progress
            def show_progress(name: str, current: int, total: int):
                print(f"  Deleting '{name}' ({current}/{total})...")

            deleted, errors = await self.scene_manager.delete_scenes_for_room(
                room.id,
                force=True,  # Already confirmed above
                on_progress=show_progress
            )

            await self.device_manager.sync_state()

            print(f"\n  Deleted {deleted} scene(s) from '{room.name}'")
            if errors:
                print(f"  Errors: {len(errors)}")
                for err in errors:
                    print(f"    - {err}")
            return

        if action == "delete_scene":
            scene_name = parsed.payload.get("scene_name")
            scene = self.device_manager.find_scene(scene_name)
            if scene:
                await self.scene_manager.delete_scene(scene.id)
                print(f"  Deleted scene '{scene_name}'")
            else:
                print(f"  Scene '{scene_name}' not found")
            return

        if action == "rename_scene":
            scene_name = parsed.payload.get("scene_name")
            new_name = parsed.payload.get("new_name")
            scene = self.device_manager.find_scene(scene_name)
            if scene:
                await self.scene_manager.rename_scene(scene.id, new_name)
                await self.device_manager.sync_state()
                print(f"  Renamed scene to '{new_name}'")
            else:
                print(f"  Scene '{scene_name}' not found")
            return

        if action == "duplicate_scene":
            scene_name = parsed.payload.get("scene_name")
            new_name = parsed.payload.get("new_name")
            scene = self.device_manager.find_scene(scene_name)
            if scene:
                await self.scene_manager.duplicate_scene(scene.id, new_name)
                await self.device_manager.sync_state()
                print(f"  Created '{new_name}' as copy of '{scene_name}'")
            else:
                print(f"  Scene '{scene_name}' not found")
            return

        # Room management
        if action == "delete_room":
            room_name = parsed.payload.get("room_name")
            room = self.device_manager.find_target(room_name)
            if room and hasattr(room, 'grouped_light_id'):
                await self.group_manager.delete_room(room.id)
                await self.device_manager.sync_state()
                print(f"  Deleted room '{room_name}'")
            else:
                print(f"  Room '{room_name}' not found")
            return

        if action == "rename_room":
            room_name = parsed.payload.get("room_name")
            new_name = parsed.payload.get("new_name")
            room = self.device_manager.find_target(room_name)
            if room and hasattr(room, 'grouped_light_id'):
                await self.group_manager.rename_room(room.id, new_name)
                await self.device_manager.sync_state()
                print(f"  Renamed room to '{new_name}'")
            else:
                print(f"  Room '{room_name}' not found")
            return

        # Zone management
        if action == "delete_zone":
            zone_name = parsed.payload.get("zone_name")
            zone = self.device_manager.find_target(zone_name)
            if zone:
                await self.group_manager.delete_zone(zone.id)
                await self.device_manager.sync_state()
                print(f"  Deleted zone '{zone_name}'")
            else:
                print(f"  Zone '{zone_name}' not found")
            return

        if action == "rename_zone":
            zone_name = parsed.payload.get("zone_name")
            new_name = parsed.payload.get("new_name")
            zone = self.device_manager.find_target(zone_name)
            if zone:
                await self.group_manager.rename_zone(zone.id, new_name)
                await self.device_manager.sync_state()
                print(f"  Renamed zone to '{new_name}'")
            else:
                print(f"  Zone '{zone_name}' not found")
            return

        print(f"  Management action '{action}' not yet implemented")
        print('  Try using a wizard: wizard scene, wizard room, wizard zone')

    async def _execute_effect(self, parsed) -> None:
        """Execute an effect command."""
        if not parsed.target:
            print("  No target specified for effect")
            return

        result = await self.effects_manager.set_effect(
            parsed.target,
            parsed.effect_name
        )

        if result.success:
            print(f"  {result.message}")
        else:
            print(f"  Failed: {result.message}")

    async def _execute_timed_effect(self, parsed) -> None:
        """Execute a timed effect command (sunrise/sunset)."""
        if not parsed.target:
            print("  No target specified for timed effect")
            return

        duration = parsed.duration_minutes or 30

        if parsed.effect_name == "sunrise":
            result = await self.effects_manager.start_sunrise(
                parsed.target, duration
            )
        elif parsed.effect_name == "sunset":
            result = await self.effects_manager.start_sunset(
                parsed.target, duration
            )
        elif parsed.effect_name == "no_effect":
            result = await self.effects_manager.stop_timed_effect(parsed.target)
        else:
            print(f"  Unknown timed effect: {parsed.effect_name}")
            return

        if result.success:
            print(f"  {result.message}")
        else:
            print(f"  Failed: {result.message}")

    async def _execute_signal(self, parsed) -> None:
        """Execute a signal/identify command."""
        if not parsed.target:
            print("  No target specified for signal")
            return

        from hue_controller.models import Light

        if parsed.effect_name == "identify" and isinstance(parsed.target, Light):
            result = await self.effects_manager.identify_light(parsed.target)
        else:
            result = await self.effects_manager.flash(parsed.target)

        if result.success:
            print(f"  {result.message}")
        else:
            print(f"  Failed: {result.message}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._save_history()
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
