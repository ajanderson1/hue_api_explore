"""
Natural language command interpreter for Hue control.

Parses plain English commands into Hue API payloads.
Supports extended commands for scene management, group management,
effects, and entertainment configurations.
"""

import re
from dataclasses import dataclass, field
from typing import Optional, Union

from .color_utils import parse_color, get_brightness_from_text, kelvin_to_mirek
from .device_manager import DeviceManager, Target
from .exceptions import InvalidCommandError, TargetNotFoundError, SceneNotFoundError
from .models import CommandResult, Light, Room, Zone, Scene
from .constants import EFFECT_TYPES, TIMED_EFFECT_TYPES


# Default transition time in milliseconds (400ms for smooth transitions)
DEFAULT_TRANSITION_MS = 400


@dataclass
class ParsedCommand:
    """Represents a parsed command ready for execution."""
    action_type: str  # "state", "scene", "identify", "effect", "timed_effect", "signal", "management"
    target: Optional[Target] = None
    target_name: Optional[str] = None
    scene: Optional[Scene] = None
    payload: dict = field(default_factory=dict)
    transition_ms: int = DEFAULT_TRANSITION_MS
    use_grouped_light: bool = True  # Use grouped_light for rooms/zones
    # Extended command data
    management_action: Optional[str] = None  # "create_scene", "delete_scene", "create_room", etc.
    effect_name: Optional[str] = None
    duration_minutes: Optional[int] = None


class CommandInterpreter:
    """
    Parses natural language commands into Hue API payloads.

    Supports commands like:
        - "turn on the living room"
        - "dim kitchen to 50%"
        - "set bedroom to blue"
        - "make office warm"
        - "relax mode in den"
        - "energize the study"
    """

    # Action keywords mapped to on/off state
    ON_KEYWORDS = {"on", "enable", "activate", "start"}
    OFF_KEYWORDS = {"off", "disable", "deactivate", "stop", "kill"}

    # Scene name patterns (commonly used Hue scenes)
    SCENE_KEYWORDS = {
        "relax", "concentrate", "energize", "read", "reading",
        "bright", "dimmed", "nightlight", "savanna sunset",
        "tropical twilight", "arctic aurora", "spring blossom"
    }

    # Preposition words to remove when finding targets
    PREPOSITIONS = {"the", "in", "on", "at", "to", "for", "a", "an", "my"}

    # Action verbs to strip from target names
    ACTION_VERBS = {
        "turn", "switch", "set", "make", "put", "change",
        "dim", "brighten", "light", "lights"
    }

    # Effect keywords
    EFFECT_KEYWORDS = {
        "candle", "fire", "prism", "sparkle", "opal",
        "glisten", "underwater", "cosmos", "sunbeam", "enchant"
    }

    # Timed effect keywords
    TIMED_EFFECT_KEYWORDS = {"sunrise", "sunset"}

    # Signal keywords
    SIGNAL_KEYWORDS = {"flash", "blink", "signal", "identify"}

    # Management keywords
    MANAGEMENT_KEYWORDS = {
        "create", "delete", "remove", "add", "rename",
        "duplicate", "copy", "edit", "wizard"
    }

    def __init__(self, device_manager: DeviceManager):
        """
        Initialize the interpreter.

        Args:
            device_manager: DeviceManager instance with synced state
        """
        self.dm = device_manager

    def parse(self, command: str) -> ParsedCommand:
        """
        Parse a natural language command.

        Args:
            command: User input string

        Returns:
            ParsedCommand ready for execution

        Raises:
            InvalidCommandError: If command cannot be parsed
            TargetNotFoundError: If specified target doesn't exist
        """
        original = command
        command = command.strip().lower()

        if not command:
            raise InvalidCommandError(original, "Empty command")

        # Check for management commands (create, delete, etc.)
        parsed = self._try_parse_management(command)
        if parsed:
            return parsed

        # Check for effect commands
        parsed = self._try_parse_effect(command)
        if parsed:
            return parsed

        # Check for timed effect commands (sunrise/sunset)
        parsed = self._try_parse_timed_effect(command)
        if parsed:
            return parsed

        # Check for signal commands (flash, identify)
        parsed = self._try_parse_signal(command)
        if parsed:
            return parsed

        # Check for scene activation
        parsed = self._try_parse_scene(command)
        if parsed:
            return parsed

        # Try to parse as state change
        parsed = self._parse_state_command(command)
        if parsed:
            return parsed

        raise InvalidCommandError(original, "Could not understand command")

    def _try_parse_scene(self, command: str) -> Optional[ParsedCommand]:
        """
        Try to parse as a scene activation command.

        Patterns:
            - "relax mode in kitchen"
            - "set living room to energize"
            - "activate concentrate in office"
        """
        # Check for "X mode" pattern
        mode_match = re.search(r'(\w+)\s+mode', command)
        if mode_match:
            scene_name = mode_match.group(1)
            # Extract target from rest of command
            remaining = command.replace(mode_match.group(0), "").strip()
            target_name = self._extract_target_name(remaining)

            if target_name:
                target = self.dm.find_target(target_name)
                if target:
                    scene = self.dm.find_scene(scene_name, target_name)
                    if scene:
                        return ParsedCommand(
                            action_type="scene",
                            target=target,
                            target_name=target_name,
                            scene=scene,
                        )

        # Check for scene keywords in command
        for scene_kw in self.SCENE_KEYWORDS:
            if scene_kw in command:
                # Extract target
                remaining = command.replace(scene_kw, "").strip()
                target_name = self._extract_target_name(remaining)

                if target_name:
                    target = self.dm.find_target(target_name)
                    if target and isinstance(target, (Room, Zone)):
                        scene = self.dm.find_scene(scene_kw, target_name)
                        if scene:
                            return ParsedCommand(
                                action_type="scene",
                                target=target,
                                target_name=target_name,
                                scene=scene,
                            )

        return None

    def _parse_state_command(self, command: str) -> Optional[ParsedCommand]:
        """
        Parse a state change command (on/off, brightness, color).

        Returns:
            ParsedCommand with payload, or None if can't parse
        """
        payload: dict = {}
        transition_ms = DEFAULT_TRANSITION_MS

        # Check for on/off
        is_on = self._check_on_off(command)
        if is_on is not None:
            payload["on"] = {"on": is_on}

        # Check for brightness
        brightness = get_brightness_from_text(command)
        if brightness is not None:
            payload["dimming"] = {"brightness": brightness}
            # If dimming, also turn on
            if "on" not in payload:
                payload["on"] = {"on": True}

        # Check for color
        color_payload = self._extract_color(command)
        if color_payload:
            payload.update(color_payload)
            # If setting color, also turn on
            if "on" not in payload:
                payload["on"] = {"on": True}

        # Check for transition time
        transition = self._extract_transition(command)
        if transition is not None:
            transition_ms = transition

        # If we have a payload, find the target
        if payload:
            # Add dynamics for smooth transition
            payload["dynamics"] = {"duration": transition_ms}

            target_name = self._extract_target_name(command)
            if not target_name:
                # Check for "all lights" or similar
                if "all" in command and "light" in command:
                    target_name = "all"

            if target_name:
                # Handle "all lights"
                if target_name == "all":
                    # Use bridge_home or return all lights
                    # For now, we'll need the caller to handle this
                    return ParsedCommand(
                        action_type="state",
                        target=None,  # Signal to apply to all
                        target_name="all lights",
                        payload=payload,
                        transition_ms=transition_ms,
                        use_grouped_light=False,
                    )

                target = self.dm.find_target(target_name)
                if target:
                    return ParsedCommand(
                        action_type="state",
                        target=target,
                        target_name=self._get_display_name(target),
                        payload=payload,
                        transition_ms=transition_ms,
                        use_grouped_light=isinstance(target, (Room, Zone)),
                    )
                else:
                    raise TargetNotFoundError(target_name)

        return None

    def _check_on_off(self, command: str) -> Optional[bool]:
        """Check if command contains on/off keywords."""
        words = set(command.split())

        for kw in self.ON_KEYWORDS:
            if kw in words:
                return True

        for kw in self.OFF_KEYWORDS:
            if kw in words:
                return False

        return None

    def _extract_color(self, command: str) -> Optional[dict]:
        """Extract color specification from command."""
        # Try common patterns

        # "set X to COLOR"
        to_match = re.search(r'\bto\s+(.+?)(?:\s+at|\s+in|\s*$)', command)
        if to_match:
            color_str = to_match.group(1).strip()
            # Remove brightness specs
            color_str = re.sub(r'\d+\s*%', '', color_str).strip()
            if color_str:
                result = parse_color(color_str)
                if result:
                    return result

        # "make X COLOR"
        make_match = re.search(r'\b(?:make|set)\s+\w+\s+(\w+)', command)
        if make_match:
            color_str = make_match.group(1)
            result = parse_color(color_str)
            if result:
                return result

        # Check for color words anywhere
        for word in command.split():
            result = parse_color(word)
            if result:
                return result

        # Check for hex colors
        hex_match = re.search(r'#[0-9a-f]{3,6}\b', command, re.I)
        if hex_match:
            return parse_color(hex_match.group(0))

        return None

    def _extract_transition(self, command: str) -> Optional[int]:
        """Extract transition time from command."""
        # "in X seconds"
        sec_match = re.search(r'(?:in|over)\s+(\d+(?:\.\d+)?)\s*(?:s|sec|second)', command)
        if sec_match:
            return int(float(sec_match.group(1)) * 1000)

        # "slowly"
        if "slow" in command:
            return 2000

        # "instantly" or "immediately"
        if "instant" in command or "immediate" in command:
            return 0

        # "quickly" or "fast"
        if "quick" in command or "fast" in command:
            return 100

        return None

    def _extract_target_name(self, command: str) -> Optional[str]:
        """
        Extract the target (room/light/zone) name from command.

        Strips action verbs and prepositions to find the target.
        """
        # Remove common action words and prepositions
        words = command.split()
        filtered = []

        skip_next = False
        for i, word in enumerate(words):
            if skip_next:
                skip_next = False
                continue

            # Skip action verbs at start
            if not filtered and word in self.ACTION_VERBS:
                continue

            # Skip prepositions
            if word in self.PREPOSITIONS:
                continue

            # Skip brightness specs
            if re.match(r'^\d+%?$', word):
                continue

            # Skip color words (they're not targets)
            if parse_color(word):
                continue

            # Skip "mode"
            if word == "mode":
                continue

            filtered.append(word)

        if not filtered:
            return None

        # Join remaining words and try to match
        candidate = " ".join(filtered)

        # Try progressively shorter substrings
        words = candidate.split()
        for length in range(len(words), 0, -1):
            for start in range(len(words) - length + 1):
                substring = " ".join(words[start:start + length])
                if self.dm.find_target(substring):
                    return substring

        return candidate if candidate else None

    def _try_parse_management(self, command: str) -> Optional[ParsedCommand]:
        """
        Parse management commands (create, delete, etc.).

        Patterns:
            - "create scene X in room Y"
            - "delete scene X"
            - "create room X"
            - "rename room X to Y"
            - "wizard scene"
        """
        words = command.split()

        # Check for wizard commands
        if "wizard" in words:
            if "scene" in command:
                return ParsedCommand(
                    action_type="management",
                    management_action="wizard_scene"
                )
            elif "room" in command:
                return ParsedCommand(
                    action_type="management",
                    management_action="wizard_room"
                )
            elif "zone" in command:
                return ParsedCommand(
                    action_type="management",
                    management_action="wizard_zone"
                )
            elif "entertainment" in command:
                return ParsedCommand(
                    action_type="management",
                    management_action="wizard_entertainment"
                )

        # Check for create commands
        if "create" in words or "new" in words:
            if "scene" in command:
                # Extract scene name and group
                match = re.search(r'(?:create|new)\s+scene\s+"?([^"]+)"?\s+in\s+(.+)', command)
                if match:
                    return ParsedCommand(
                        action_type="management",
                        management_action="create_scene",
                        payload={
                            "scene_name": match.group(1).strip(),
                            "group_name": match.group(2).strip()
                        }
                    )
                # "create scene from current state in X"
                if "current" in command or "capture" in command:
                    match = re.search(r'in\s+(.+?)(?:\s*$)', command)
                    if match:
                        return ParsedCommand(
                            action_type="management",
                            management_action="capture_scene",
                            payload={"group_name": match.group(1).strip()}
                        )

            elif "room" in command:
                match = re.search(r'(?:create|new)\s+room\s+"?([^"]+)"?', command)
                if match:
                    return ParsedCommand(
                        action_type="management",
                        management_action="create_room",
                        payload={"room_name": match.group(1).strip()}
                    )

            elif "zone" in command:
                match = re.search(r'(?:create|new)\s+zone\s+"?([^"]+)"?', command)
                if match:
                    return ParsedCommand(
                        action_type="management",
                        management_action="create_zone",
                        payload={"zone_name": match.group(1).strip()}
                    )

        # Check for delete commands
        if "delete" in words or "remove" in words:
            if "scene" in command:
                match = re.search(r'(?:delete|remove)\s+scene\s+"?([^"]+)"?', command)
                if match:
                    return ParsedCommand(
                        action_type="management",
                        management_action="delete_scene",
                        payload={"scene_name": match.group(1).strip()}
                    )

            elif "room" in command:
                match = re.search(r'(?:delete|remove)\s+room\s+"?([^"]+)"?', command)
                if match:
                    return ParsedCommand(
                        action_type="management",
                        management_action="delete_room",
                        payload={"room_name": match.group(1).strip()}
                    )

            elif "zone" in command:
                match = re.search(r'(?:delete|remove)\s+zone\s+"?([^"]+)"?', command)
                if match:
                    return ParsedCommand(
                        action_type="management",
                        management_action="delete_zone",
                        payload={"zone_name": match.group(1).strip()}
                    )

        # Check for duplicate commands
        if "duplicate" in words or "copy" in words:
            if "scene" in command:
                match = re.search(
                    r'(?:duplicate|copy)\s+scene\s+"?([^"]+)"?\s+(?:as|to)\s+"?([^"]+)"?',
                    command
                )
                if match:
                    return ParsedCommand(
                        action_type="management",
                        management_action="duplicate_scene",
                        payload={
                            "scene_name": match.group(1).strip(),
                            "new_name": match.group(2).strip()
                        }
                    )

        # Check for rename commands
        if "rename" in words:
            if "scene" in command:
                match = re.search(
                    r'rename\s+scene\s+"?([^"]+)"?\s+to\s+"?([^"]+)"?',
                    command
                )
                if match:
                    return ParsedCommand(
                        action_type="management",
                        management_action="rename_scene",
                        payload={
                            "scene_name": match.group(1).strip(),
                            "new_name": match.group(2).strip()
                        }
                    )

            elif "room" in command:
                match = re.search(
                    r'rename\s+room\s+"?([^"]+)"?\s+to\s+"?([^"]+)"?',
                    command
                )
                if match:
                    return ParsedCommand(
                        action_type="management",
                        management_action="rename_room",
                        payload={
                            "room_name": match.group(1).strip(),
                            "new_name": match.group(2).strip()
                        }
                    )

            elif "zone" in command:
                match = re.search(
                    r'rename\s+zone\s+"?([^"]+)"?\s+to\s+"?([^"]+)"?',
                    command
                )
                if match:
                    return ParsedCommand(
                        action_type="management",
                        management_action="rename_zone",
                        payload={
                            "zone_name": match.group(1).strip(),
                            "new_name": match.group(2).strip()
                        }
                    )

        # Check for add/remove light commands
        if "add" in words:
            # "add X to room Y" or "add X to zone Y"
            match = re.search(
                r'add\s+"?([^"]+)"?\s+to\s+(room|zone)\s+"?([^"]+)"?',
                command
            )
            if match:
                return ParsedCommand(
                    action_type="management",
                    management_action=f"add_to_{match.group(2)}",
                    payload={
                        "item_name": match.group(1).strip(),
                        "group_name": match.group(3).strip()
                    }
                )

        return None

    def _try_parse_effect(self, command: str) -> Optional[ParsedCommand]:
        """
        Parse effect commands.

        Patterns:
            - "candle effect on living room"
            - "set bedroom to fire"
            - "sparkle in kitchen"
            - "clear effect on X"
            - "stop effect"
        """
        # Check for "clear effect" or "stop effect"
        if "clear effect" in command or "stop effect" in command or "no effect" in command:
            target_name = self._extract_target_name(command)
            if target_name:
                target = self.dm.find_target(target_name)
                if target:
                    return ParsedCommand(
                        action_type="effect",
                        target=target,
                        target_name=self._get_display_name(target),
                        effect_name="no_effect"
                    )

        # Check for effect keywords
        for effect in self.EFFECT_KEYWORDS:
            if effect in command:
                # Extract target
                remaining = command.replace(effect, "").replace("effect", "")
                target_name = self._extract_target_name(remaining)

                if target_name:
                    target = self.dm.find_target(target_name)
                    if target:
                        return ParsedCommand(
                            action_type="effect",
                            target=target,
                            target_name=self._get_display_name(target),
                            effect_name=effect
                        )

        return None

    def _try_parse_timed_effect(self, command: str) -> Optional[ParsedCommand]:
        """
        Parse timed effect commands (sunrise/sunset).

        Patterns:
            - "sunrise in bedroom"
            - "sunset in living room over 30 minutes"
            - "start sunrise in kitchen"
            - "stop sunrise"
        """
        # Check for stop commands
        if "stop" in command:
            for effect in self.TIMED_EFFECT_KEYWORDS:
                if effect in command:
                    target_name = self._extract_target_name(
                        command.replace("stop", "").replace(effect, "")
                    )
                    if target_name:
                        target = self.dm.find_target(target_name)
                        if target:
                            return ParsedCommand(
                                action_type="timed_effect",
                                target=target,
                                target_name=self._get_display_name(target),
                                effect_name="no_effect"
                            )

        # Check for sunrise/sunset
        for effect in self.TIMED_EFFECT_KEYWORDS:
            if effect in command:
                # Extract duration
                duration = 30  # Default 30 minutes
                duration_match = re.search(r'(\d+)\s*(?:min|minute)', command)
                if duration_match:
                    duration = int(duration_match.group(1))

                # Extract target
                remaining = re.sub(r'(?:start\s+)?(?:in\s+)?(\d+\s*(?:min|minute)s?\s*)?', '', command)
                remaining = remaining.replace(effect, "").replace("over", "")
                target_name = self._extract_target_name(remaining)

                if target_name:
                    target = self.dm.find_target(target_name)
                    if target:
                        return ParsedCommand(
                            action_type="timed_effect",
                            target=target,
                            target_name=self._get_display_name(target),
                            effect_name=effect,
                            duration_minutes=duration
                        )

        return None

    def _try_parse_signal(self, command: str) -> Optional[ParsedCommand]:
        """
        Parse signal/identify commands.

        Patterns:
            - "flash living room"
            - "identify kitchen light"
            - "blink bedroom"
        """
        for signal in self.SIGNAL_KEYWORDS:
            if signal in command:
                remaining = command.replace(signal, "")
                target_name = self._extract_target_name(remaining)

                if target_name:
                    target = self.dm.find_target(target_name)
                    if target:
                        return ParsedCommand(
                            action_type="signal",
                            target=target,
                            target_name=self._get_display_name(target),
                            effect_name=signal  # Use effect_name for signal type
                        )

        return None

    def _get_display_name(self, target: Target) -> str:
        """Get the display name for a target."""
        if isinstance(target, Light):
            return target.name
        elif isinstance(target, Room):
            return target.name
        elif isinstance(target, Zone):
            return target.name
        return "Unknown"

    def get_help_text(self) -> str:
        """Return help text showing example commands."""
        return """
Available commands:
  Power:
    turn on [target]           - Turn on a light/room/zone
    turn off [target]          - Turn off a light/room/zone

  Brightness:
    dim [target] to 50%        - Set brightness to 50%
    brighten [target]          - Set brightness to 100%
    set [target] to low        - Set brightness to 25%

  Color:
    set [target] to red        - Set color by name
    set [target] to #FF5500    - Set color by hex code
    make [target] warm         - Set to warm white (2700K)
    set [target] to 4000K      - Set color temperature

  Scenes:
    relax mode in [room]       - Activate Relax scene
    energize [room]            - Activate Energize scene
    create scene "X" in [room] - Create a new scene
    delete scene "X"           - Delete a scene
    duplicate scene "X" as "Y" - Copy a scene

  Effects:
    candle effect on [target]  - Set candle effect
    fire effect on [target]    - Set fire effect
    sparkle in [target]        - Set sparkle effect
    clear effect on [target]   - Remove effect

  Timed Effects:
    sunrise in [room]          - Start sunrise simulation
    sunset in [room] over 45m  - Start sunset simulation
    stop sunrise               - Stop timed effect

  Signaling:
    flash [target]             - Flash lights
    identify [light]           - Identify a light

  Management:
    create room "X"            - Create a room
    create zone "X"            - Create a zone
    rename room "X" to "Y"     - Rename a room
    delete room "X"            - Delete a room
    add "light" to room "X"    - Add device to room

  Wizards:
    wizard scene               - Scene creation wizard
    wizard room                - Room management wizard
    wizard zone                - Zone management wizard
    wizard entertainment       - Entertainment setup wizard

  Transition Options:
    ... slowly                 - Use 2 second transition
    ... instantly              - No transition
    ... in 5 seconds           - Custom transition time

Examples:
    turn on living room
    dim kitchen to 50%
    set bedroom to blue
    candle effect on den
    sunrise in bedroom over 30 minutes
    create scene "Movie Night" in living room
    wizard scene
"""


class CommandExecutor:
    """
    Executes parsed commands against the Hue API.
    """

    def __init__(self, device_manager: DeviceManager):
        """
        Initialize the executor.

        Args:
            device_manager: DeviceManager instance
        """
        self.dm = device_manager

    async def execute(self, parsed: ParsedCommand) -> CommandResult:
        """
        Execute a parsed command.

        Args:
            parsed: ParsedCommand from interpreter

        Returns:
            CommandResult with success/failure info
        """
        if parsed.action_type == "scene":
            return await self._execute_scene(parsed)
        elif parsed.action_type == "state":
            return await self._execute_state(parsed)
        elif parsed.action_type == "identify":
            return await self._execute_identify(parsed)
        else:
            return CommandResult(
                success=False,
                message=f"Unknown action type: {parsed.action_type}"
            )

    async def _execute_scene(self, parsed: ParsedCommand) -> CommandResult:
        """Execute a scene activation."""
        if not parsed.scene:
            return CommandResult(
                success=False,
                message="No scene specified"
            )

        try:
            # Recall scene via PUT to scene resource
            await self.dm.connector.put(
                f"/resource/scene/{parsed.scene.id}",
                {"recall": {"action": "active"}}
            )

            return CommandResult(
                success=True,
                message=f"Activated scene '{parsed.scene.name}'",
                target_name=parsed.target_name,
            )

        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to activate scene: {e}",
                errors=[str(e)]
            )

    async def _execute_state(self, parsed: ParsedCommand) -> CommandResult:
        """Execute a state change command."""
        if parsed.target is None:
            # Handle "all lights" case
            return await self._execute_all_lights(parsed)

        target = parsed.target
        unreachable = self.dm.get_unreachable_lights(target)
        unreachable_names = [l.name for l in unreachable]

        # Determine endpoint
        if parsed.use_grouped_light and isinstance(target, (Room, Zone)):
            # Use grouped_light for room/zone
            grouped_id = target.grouped_light_id
            if grouped_id:
                endpoint = f"/resource/grouped_light/{grouped_id}"
                is_group = True
            else:
                # Fall back to individual lights
                return await self._execute_individual_lights(parsed, target)
        else:
            # Individual light
            endpoint = f"/resource/light/{target.id}"
            is_group = False

        try:
            await self.dm.connector.put(
                endpoint,
                parsed.payload,
                is_group_command=is_group
            )

            # Build result message
            lights = self.dm.get_lights_for_target(target)
            reachable_count = len(lights) - len(unreachable)

            message = self._build_success_message(parsed, reachable_count)

            return CommandResult(
                success=True,
                message=message,
                target_name=parsed.target_name,
                affected_lights=reachable_count,
                unreachable_lights=unreachable_names,
            )

        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed: {e}",
                target_name=parsed.target_name,
                errors=[str(e)]
            )

    async def _execute_individual_lights(
        self,
        parsed: ParsedCommand,
        target: Target
    ) -> CommandResult:
        """Execute state change on individual lights."""
        lights = self.dm.get_reachable_lights(target)
        unreachable = self.dm.get_unreachable_lights(target)

        errors = []
        success_count = 0

        for light in lights:
            try:
                await self.dm.connector.put(
                    f"/resource/light/{light.id}",
                    parsed.payload
                )
                success_count += 1
            except Exception as e:
                errors.append(f"{light.name}: {e}")

        message = self._build_success_message(parsed, success_count)

        return CommandResult(
            success=success_count > 0,
            message=message,
            target_name=parsed.target_name,
            affected_lights=success_count,
            unreachable_lights=[l.name for l in unreachable],
            errors=errors,
        )

    async def _execute_all_lights(self, parsed: ParsedCommand) -> CommandResult:
        """Execute state change on all lights."""
        lights = list(self.dm.lights.values())
        reachable = [l for l in lights if l.is_reachable]
        unreachable = [l for l in lights if not l.is_reachable]

        errors = []
        success_count = 0

        for light in reachable:
            try:
                await self.dm.connector.put(
                    f"/resource/light/{light.id}",
                    parsed.payload
                )
                success_count += 1
            except Exception as e:
                errors.append(f"{light.name}: {e}")

        message = self._build_success_message(parsed, success_count)

        return CommandResult(
            success=success_count > 0,
            message=message,
            target_name="all lights",
            affected_lights=success_count,
            unreachable_lights=[l.name for l in unreachable],
            errors=errors,
        )

    async def _execute_identify(self, parsed: ParsedCommand) -> CommandResult:
        """Execute identify/alert on a light."""
        if not parsed.target or not isinstance(parsed.target, Light):
            return CommandResult(
                success=False,
                message="Identify requires a specific light"
            )

        try:
            await self.dm.connector.put(
                f"/resource/light/{parsed.target.id}",
                {"identify": {"action": "identify"}}
            )

            return CommandResult(
                success=True,
                message=f"Identifying {parsed.target.name}",
                target_name=parsed.target_name,
                affected_lights=1,
            )

        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to identify: {e}",
                errors=[str(e)]
            )

    def _build_success_message(self, parsed: ParsedCommand, light_count: int) -> str:
        """Build a human-readable success message."""
        parts = []

        # Describe the action
        payload = parsed.payload

        if "on" in payload:
            if payload["on"]["on"]:
                parts.append("Turned on")
            else:
                parts.append("Turned off")
        elif "dimming" in payload:
            bri = payload["dimming"]["brightness"]
            parts.append(f"Set to {bri:.0f}%")
        elif "color" in payload:
            parts.append("Set color")
        elif "color_temperature" in payload:
            mirek = payload["color_temperature"]["mirek"]
            kelvin = int(1_000_000 / mirek)
            parts.append(f"Set to {kelvin}K")

        # Add target
        if parsed.target_name:
            parts.append(parsed.target_name)

        # Add light count
        if light_count > 1:
            parts.append(f"({light_count} lights)")
        elif light_count == 1:
            parts.append("(1 light)")

        return " ".join(parts)
