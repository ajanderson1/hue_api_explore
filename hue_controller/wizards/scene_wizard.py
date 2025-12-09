"""
Scene Wizard

Interactive wizard for creating and editing scenes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base_wizard import BaseWizard, WizardResult, WizardAction
from ..models import (
    Scene,
    SceneDetails,
    SceneAction,
    SceneLightAction,
    ScenePalette,
    ScenePaletteColor,
    CreateSceneRequest,
    UpdateSceneRequest,
    Room,
    Zone,
    Light,
    XYColor,
)
from ..color_utils import parse_color, hex_to_xy
from ..managers.scene_manager import SceneManager

if TYPE_CHECKING:
    from ..device_manager import DeviceManager
    from ..bridge_connector import BridgeConnector


class SceneWizard(BaseWizard):
    """Interactive wizard for scene creation and editing."""

    def __init__(
        self,
        connector: BridgeConnector,
        device_manager: DeviceManager
    ):
        """
        Initialize the scene wizard.

        Args:
            connector: Bridge connector for API calls
            device_manager: Device manager for state access
        """
        super().__init__(device_manager)
        self.connector = connector
        self.scene_manager = SceneManager(connector, device_manager)

    async def run(self) -> WizardResult:
        """
        Run the scene wizard main menu.

        Returns:
            WizardResult indicating success/failure
        """
        self.print_header("Scene Wizard")

        options = [
            ("Create new scene", "create"),
            ("Create from current state", "capture"),
            ("Edit existing scene", "edit"),
            ("Duplicate scene", "duplicate"),
            ("Delete scene", "delete"),
        ]

        choice, action = self.select_one("What would you like to do?", options)

        if action == WizardAction.CANCEL:
            return self.handle_cancel("Scene")

        if choice == "create":
            return await self._create_scene_wizard()
        elif choice == "capture":
            return await self._capture_scene_wizard()
        elif choice == "edit":
            return await self._edit_scene_wizard()
        elif choice == "duplicate":
            return await self._duplicate_scene_wizard()
        elif choice == "delete":
            return await self._delete_scene_wizard()

        return WizardResult(success=False, message="Invalid choice")

    async def run_create(self) -> WizardResult:
        """Run the scene creation wizard directly."""
        return await self._create_scene_wizard()

    async def run_edit(self, scene_id: Optional[str] = None) -> WizardResult:
        """Run the scene edit wizard directly."""
        return await self._edit_scene_wizard(scene_id)

    # =========================================================================
    # Create Scene Wizard
    # =========================================================================

    async def _create_scene_wizard(self) -> WizardResult:
        """Create a new scene with custom light settings."""
        self.print_header("Create New Scene")

        # Step 1: Select group
        self.print_step(1, 4, "Select room or zone")
        group, group_type, action = await self._select_group()
        if action != WizardAction.CONTINUE:
            return self.handle_cancel("Scene")

        # Step 2: Enter name
        self.print_step(2, 4, "Name your scene")
        name, action = self.get_input(
            "Scene name",
            validator=lambda x: len(x) >= 1 and len(x) <= 32,
            error_message="Name must be 1-32 characters"
        )
        if action != WizardAction.CONTINUE:
            return self.handle_cancel("Scene")

        # Step 3: Configure lights
        self.print_step(3, 4, "Configure lights")
        lights = self.dm.get_lights_for_target(group)
        actions = await self._configure_lights(lights)

        if actions is None:
            return self.handle_cancel("Scene")

        # Step 4: Confirm and create
        self.print_step(4, 4, "Confirm and create")
        print(f"\nScene: {name}")
        print(f"Group: {group.name}")
        print(f"Lights configured: {len(actions)}")

        confirmed, action = self.get_confirmation("Create this scene?", default=True)
        if not confirmed or action != WizardAction.CONTINUE:
            return self.handle_cancel("Scene")

        # Create the scene
        try:
            request = CreateSceneRequest(
                name=name,
                group_id=group.id,
                group_type=group_type,
                actions=actions
            )
            scene = await self.scene_manager.create_scene(request)

            self.print_success(f"Created scene '{name}'")
            return WizardResult(
                success=True,
                message=f"Created scene '{name}'",
                data=scene
            )

        except Exception as e:
            self.print_error(str(e))
            return WizardResult(success=False, message=str(e))

    # =========================================================================
    # Capture Scene Wizard
    # =========================================================================

    async def _capture_scene_wizard(self) -> WizardResult:
        """Create a scene from current light states."""
        self.print_header("Capture Current State")

        # Step 1: Select group
        self.print_step(1, 3, "Select room or zone")
        group, group_type, action = await self._select_group()
        if action != WizardAction.CONTINUE:
            return self.handle_cancel("Scene")

        # Step 2: Show current state
        self.print_step(2, 3, "Current light states")
        lights = self.dm.get_lights_for_target(group)

        print(f"\nLights in {group.name}:")
        for light in lights:
            state = "on" if light.is_on else "off"
            brightness = f", {light.brightness:.0f}%" if light.is_on else ""
            print(f"  - {light.name}: {state}{brightness}")

        # Step 3: Name and create
        self.print_step(3, 3, "Name your scene")
        name, action = self.get_input(
            "Scene name",
            validator=lambda x: len(x) >= 1 and len(x) <= 32,
            error_message="Name must be 1-32 characters"
        )
        if action != WizardAction.CONTINUE:
            return self.handle_cancel("Scene")

        try:
            scene = await self.scene_manager.create_scene_from_current_state(
                name=name,
                group_id=group.id,
                group_type=group_type
            )

            self.print_success(f"Created scene '{name}' from current state")
            return WizardResult(
                success=True,
                message=f"Created scene '{name}'",
                data=scene
            )

        except Exception as e:
            self.print_error(str(e))
            return WizardResult(success=False, message=str(e))

    # =========================================================================
    # Edit Scene Wizard
    # =========================================================================

    async def _edit_scene_wizard(
        self,
        scene_id: Optional[str] = None
    ) -> WizardResult:
        """Edit an existing scene."""
        self.print_header("Edit Scene")

        # Select scene if not provided
        if scene_id is None:
            scene, action = await self._select_scene()
            if action != WizardAction.CONTINUE or scene is None:
                return self.handle_cancel("Scene")
            scene_id = scene.id

        # Get scene details
        try:
            details = await self.scene_manager.get_scene_details(scene_id)
        except Exception as e:
            self.print_error(str(e))
            return WizardResult(success=False, message=str(e))

        # Show edit menu
        while True:
            print(f"\nEditing: {details.name}")
            print(f"Actions: {len(details.actions)} light(s) configured")

            options = [
                ("Edit light settings", "lights"),
                ("Add/edit palette", "palette"),
                ("Rename scene", "rename"),
                ("Preview scene", "preview"),
                ("Save and exit", "save"),
            ]

            choice, action = self.select_one("What would you like to do?", options)

            if action == WizardAction.CANCEL:
                return self.handle_cancel("Scene")

            if choice == "lights":
                await self._edit_scene_lights(details)
            elif choice == "palette":
                await self._edit_scene_palette(details)
            elif choice == "rename":
                new_name, action = self.get_input("New name")
                if action == WizardAction.CONTINUE:
                    details.name = new_name
            elif choice == "preview":
                await self._preview_scene(scene_id)
            elif choice == "save":
                break

        # Save changes
        try:
            await self.scene_manager.update_scene(UpdateSceneRequest(
                scene_id=scene_id,
                name=details.name,
                actions=details.actions,
                palette=details.palette
            ))

            self.print_success(f"Updated scene '{details.name}'")
            return WizardResult(
                success=True,
                message=f"Updated scene '{details.name}'",
                data=details
            )

        except Exception as e:
            self.print_error(str(e))
            return WizardResult(success=False, message=str(e))

    # =========================================================================
    # Duplicate Scene Wizard
    # =========================================================================

    async def _duplicate_scene_wizard(self) -> WizardResult:
        """Duplicate an existing scene."""
        self.print_header("Duplicate Scene")

        # Select scene
        scene, action = await self._select_scene()
        if action != WizardAction.CONTINUE or scene is None:
            return self.handle_cancel("Scene")

        # Get new name
        default_name = f"{scene.name} (copy)"
        name, action = self.get_input(
            f"New name [{default_name}]",
            allow_empty=True
        )
        if action != WizardAction.CONTINUE:
            return self.handle_cancel("Scene")

        if not name:
            name = default_name

        try:
            new_scene = await self.scene_manager.duplicate_scene(scene.id, name)

            self.print_success(f"Created '{name}' as copy of '{scene.name}'")
            return WizardResult(
                success=True,
                message=f"Duplicated scene to '{name}'",
                data=new_scene
            )

        except Exception as e:
            self.print_error(str(e))
            return WizardResult(success=False, message=str(e))

    # =========================================================================
    # Delete Scene Wizard
    # =========================================================================

    async def _delete_scene_wizard(self) -> WizardResult:
        """Delete a scene."""
        self.print_header("Delete Scene")

        # Select scene
        scene, action = await self._select_scene()
        if action != WizardAction.CONTINUE or scene is None:
            return self.handle_cancel("Scene")

        # Confirm deletion
        confirmed, action = self.get_confirmation(
            f"Delete scene '{scene.name}'? This cannot be undone.",
            default=False
        )
        if not confirmed or action != WizardAction.CONTINUE:
            return self.handle_cancel("Scene")

        try:
            await self.scene_manager.delete_scene(scene.id)

            self.print_success(f"Deleted scene '{scene.name}'")
            return WizardResult(
                success=True,
                message=f"Deleted scene '{scene.name}'"
            )

        except Exception as e:
            self.print_error(str(e))
            return WizardResult(success=False, message=str(e))

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _select_group(self) -> tuple[Room | Zone, str, WizardAction]:
        """Let user select a room or zone."""
        options = []

        # Add rooms
        for room in sorted(self.dm.rooms.values(), key=lambda r: r.name):
            light_count = len(self.dm.get_lights_for_target(room))
            options.append((f"{room.name} (Room, {light_count} lights)", (room, "room")))

        # Add zones
        for zone in sorted(self.dm.zones.values(), key=lambda z: z.name):
            light_count = len(self.dm.get_lights_for_target(zone))
            options.append((f"{zone.name} (Zone, {light_count} lights)", (zone, "zone")))

        if not options:
            self.print_error("No rooms or zones found")
            return None, "", WizardAction.CANCEL

        result, action = self.select_one("Select a room or zone", options)

        if action != WizardAction.CONTINUE or result is None:
            return None, "", action

        return result[0], result[1], WizardAction.CONTINUE

    async def _select_scene(self) -> tuple[Optional[Scene], WizardAction]:
        """Let user select a scene."""
        scenes = list(self.dm.scenes.values())

        if not scenes:
            self.print_error("No scenes found")
            return None, WizardAction.CANCEL

        # Group by room
        scenes_by_group: dict[str, list[Scene]] = {}
        for scene in scenes:
            group_name = "Unknown"
            if scene.group_id:
                if scene.group_id in self.dm.rooms:
                    group_name = self.dm.rooms[scene.group_id].name
                elif scene.group_id in self.dm.zones:
                    group_name = self.dm.zones[scene.group_id].name
            if group_name not in scenes_by_group:
                scenes_by_group[group_name] = []
            scenes_by_group[group_name].append(scene)

        options = []
        for group_name in sorted(scenes_by_group.keys()):
            for scene in sorted(scenes_by_group[group_name], key=lambda s: s.name):
                options.append((f"{scene.name} ({group_name})", scene))

        return self.select_one("Select a scene", options)

    async def _configure_lights(
        self,
        lights: list[Light]
    ) -> Optional[list[SceneAction]]:
        """Configure light settings for a scene."""
        actions = []

        for i, light in enumerate(lights, 1):
            print(f"\n[{i}/{len(lights)}] {light.name}")
            print(f"  Current: {'on' if light.is_on else 'off'}", end="")
            if light.is_on:
                print(f", {light.brightness:.0f}%")
            else:
                print()

            # Ask what to do
            options = [
                ("Configure this light", "configure"),
                ("Use current state", "current"),
                ("Skip (exclude from scene)", "skip"),
            ]

            choice, action = self.select_one(
                "Action for this light",
                options,
                allow_back=i > 1
            )

            if action == WizardAction.CANCEL:
                return None
            if action == WizardAction.BACK:
                # Remove last action and redo
                if actions:
                    actions.pop()
                continue

            if choice == "skip":
                continue
            elif choice == "current":
                # Use current state
                scene_action = SceneLightAction(
                    on=light.is_on,
                    brightness=light.brightness if light.is_on else None,
                    color_xy=light.color_xy if light.supports_color else None,
                    color_temperature_mirek=(
                        light.color_temperature_mirek
                        if light.supports_color_temperature else None
                    )
                )
            else:
                # Configure manually
                scene_action = await self._configure_single_light(light)
                if scene_action is None:
                    continue

            actions.append(SceneAction(
                target_rid=light.id,
                target_rtype="light",
                action=scene_action
            ))

        return actions

    async def _configure_single_light(
        self,
        light: Light
    ) -> Optional[SceneLightAction]:
        """Configure settings for a single light."""
        # On/Off
        on_state, action = self.get_confirmation("Light on?", default=True)
        if action != WizardAction.CONTINUE:
            return None

        if not on_state:
            return SceneLightAction(on=False)

        # Brightness
        brightness, action = self.get_number(
            "Brightness",
            min_value=0,
            max_value=100,
            default=100
        )
        if action != WizardAction.CONTINUE:
            return None

        result = SceneLightAction(on=True, brightness=brightness)

        # Color (if supported)
        if light.supports_color:
            color_str, action = self.get_input(
                "Color (name, hex #FF0000, or 'skip')",
                allow_empty=True
            )
            if action == WizardAction.CONTINUE and color_str and color_str.lower() != "skip":
                color_payload = parse_color(color_str)
                if color_payload and "color" in color_payload:
                    xy = color_payload["color"]["xy"]
                    result.color_xy = XYColor(x=xy["x"], y=xy["y"])

        # Color temperature (if supported and no color set)
        if light.supports_color_temperature and not result.color_xy:
            temp, action = self.get_number(
                "Color temperature (2000-6500K, or skip)",
                min_value=2000,
                max_value=6500,
                default=None,
                allow_float=False
            )
            if action == WizardAction.CONTINUE and temp:
                result.color_temperature_mirek = int(1_000_000 / temp)

        return result

    async def _edit_scene_lights(self, details: SceneDetails) -> None:
        """Edit light settings within a scene."""
        # Get lights in the scene's group
        group = None
        if details.group_id:
            group = self.dm.rooms.get(details.group_id) or self.dm.zones.get(details.group_id)

        if not group:
            self.print_error("Cannot find scene's group")
            return

        lights = self.dm.get_lights_for_target(group)

        # Build options
        options = []
        for light in lights:
            # Find existing action for this light
            existing = None
            for action in details.actions:
                if action.target_rid == light.id:
                    existing = action.action
                    break

            status = "configured" if existing else "not configured"
            options.append((f"{light.name} ({status})", light))

        selected, action = self.select_one("Select light to edit", options)
        if action != WizardAction.CONTINUE or selected is None:
            return

        light = selected
        new_action = await self._configure_single_light(light)

        if new_action:
            # Update or add action
            found = False
            for i, action in enumerate(details.actions):
                if action.target_rid == light.id:
                    details.actions[i] = SceneAction(
                        target_rid=light.id,
                        target_rtype="light",
                        action=new_action
                    )
                    found = True
                    break

            if not found:
                details.actions.append(SceneAction(
                    target_rid=light.id,
                    target_rtype="light",
                    action=new_action
                ))

    async def _edit_scene_palette(self, details: SceneDetails) -> None:
        """Edit dynamic palette for a scene."""
        print("\nDynamic Palette Configuration")
        print("A palette allows colors to cycle dynamically when the scene is active.")

        colors: list[ScenePaletteColor] = []

        while len(colors) < 5:
            color_str, action = self.get_input(
                f"Color {len(colors) + 1} (name, hex, or 'done')",
                allow_empty=True
            )

            if action != WizardAction.CONTINUE:
                break
            if not color_str or color_str.lower() == "done":
                break

            color_payload = parse_color(color_str)
            if color_payload and "color" in color_payload:
                xy = color_payload["color"]["xy"]
                colors.append(ScenePaletteColor(
                    color=XYColor(x=xy["x"], y=xy["y"])
                ))
                print(f"  Added color {len(colors)}")
            else:
                print("  Invalid color, try again")

        if colors:
            details.palette = ScenePalette(colors=colors)
            print(f"\nPalette set with {len(colors)} colors")
        else:
            details.palette = None
            print("\nPalette cleared")

    async def _preview_scene(self, scene_id: str) -> None:
        """Preview a scene by temporarily activating it."""
        print("\nPreviewing scene (activating for 5 seconds)...")

        try:
            await self.scene_manager.recall_scene(scene_id)
            import asyncio
            await asyncio.sleep(5)
            print("Preview complete. Scene remains active.")
        except Exception as e:
            self.print_error(f"Preview failed: {e}")
