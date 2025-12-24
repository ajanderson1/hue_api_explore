"""
Quick Scene Wizard

Mood-first scene creation in ~30 seconds.
Flow: Pick mood -> Select room -> Name scene -> Preview -> Create
"""

import asyncio
from dataclasses import dataclass
from typing import Optional, Union
from rich.console import Console
from rich.panel import Panel

from ...bridge_connector import BridgeConnector
from ...device_manager import DeviceManager
from ...models import (
    Room, Zone, Light,
    CreateSceneRequest, SceneAction, SceneLightAction, ScenePalette,
    XYColor, ScenePaletteColor,
)
from ...managers.scene_manager import SceneManager
from ..base_wizard import WizardResult
from ..ui import AsyncMenu, MenuChoice, WizardPanel, StatusMessage
from ..templates import MoodTemplate, MOOD_TEMPLATES, get_icon_for_template, get_template_choices
from .preview import LivePreview


console = Console()


@dataclass
class QuickSceneWizard:
    """
    Quick scene creation wizard with mood-first flow.

    This wizard is designed for speed - most users can create
    a scene in under 30 seconds by picking a mood and room.
    """
    connector: BridgeConnector
    device_manager: DeviceManager

    def __post_init__(self):
        self.scene_manager = SceneManager(self.connector, self.device_manager)
        self.preview = LivePreview(self.connector, self.device_manager)

    async def run(self) -> WizardResult:
        """Run the quick scene wizard."""
        console.clear()
        WizardPanel.header(
            "Quick Scene Setup",
            "Create a scene in seconds by picking a mood"
        )

        # Step 1: Pick a mood
        template = await self._select_mood()
        if template is None:
            return WizardResult(success=False, message="Cancelled")

        # Step 2: Select room/zone
        target, target_type = await self._select_target()
        if target is None:
            return WizardResult(success=False, message="Cancelled")

        # Step 3: Name the scene
        name = await self._get_scene_name(template, target)
        if name is None:
            return WizardResult(success=False, message="Cancelled")

        # Step 4: Preview
        lights = self.device_manager.get_lights_for_target(target)
        if not lights:
            WizardPanel.error(f"No lights found in {target.name}")
            return WizardResult(success=False, message="No lights found")

        action = self._template_to_action(template)
        preview_result = await self._preview_scene(lights, action, template)

        if preview_result == "cancel":
            return WizardResult(success=False, message="Cancelled")

        # Step 5: Create the scene
        return await self._create_scene(
            name=name,
            target=target,
            target_type=target_type,
            template=template,
            lights=lights,
        )

    async def _select_mood(self) -> Optional[MoodTemplate]:
        """Select a mood template."""
        console.print("\n[bold]Step 1:[/bold] What mood are you going for?\n")

        # Build categorized choices
        categories = get_template_choices()
        choices = []

        for category_name, templates in categories.items():
            # Add category separator
            from questionary import Separator
            choices.append(Separator(f"  {category_name}"))

            for template in templates:
                icon = get_icon_for_template(template)
                choices.append(MenuChoice(
                    label=f"{icon}  {template.name}",
                    value=template.id,
                    description=template.description,
                ))

        # Add custom option
        from questionary import Separator
        choices.append(Separator(""))
        choices.append(MenuChoice(
            label="   Custom...",
            value="custom",
            description="Build from scratch (opens Standard wizard)",
        ))

        selected = await AsyncMenu.select(
            "Select a mood:",
            choices=choices,
        )

        if selected is None:
            return None

        if selected == "custom":
            # Signal to router to switch to standard wizard
            return None

        # Find the template
        for template in MOOD_TEMPLATES:
            if template.id == selected:
                return template

        return None

    async def _select_target(self) -> tuple[Optional[Union[Room, Zone]], Optional[str]]:
        """Select a room or zone."""
        console.print("\n[bold]Step 2:[/bold] Where should this scene apply?\n")

        choices = []

        # Add rooms
        rooms = list(self.device_manager.rooms.values())
        if rooms:
            from questionary import Separator
            choices.append(Separator("  Rooms"))

            for room in sorted(rooms, key=lambda r: r.name):
                light_count = len(self.device_manager.get_lights_for_target(room))
                choices.append(MenuChoice(
                    label=f"   {room.name}",
                    value=("room", room.id),
                    description=f"{light_count} lights",
                ))

        # Add zones
        zones = list(self.device_manager.zones.values())
        if zones:
            from questionary import Separator
            choices.append(Separator("  Zones"))

            for zone in sorted(zones, key=lambda z: z.name):
                light_count = len(self.device_manager.get_lights_for_target(zone))
                choices.append(MenuChoice(
                    label=f"   {zone.name}",
                    value=("zone", zone.id),
                    description=f"{light_count} lights",
                ))

        if not choices:
            WizardPanel.error("No rooms or zones found. Create a room first.")
            return None, None

        selected = await AsyncMenu.select(
            "Select location:",
            choices=choices,
        )

        if selected is None:
            return None, None

        target_type, target_id = selected

        if target_type == "room":
            return self.device_manager.rooms.get(target_id), "room"
        else:
            return self.device_manager.zones.get(target_id), "zone"

    async def _get_scene_name(
        self,
        template: MoodTemplate,
        target: Union[Room, Zone],
    ) -> Optional[str]:
        """Get scene name with smart default."""
        console.print("\n[bold]Step 3:[/bold] Name your scene\n")

        # Generate smart default
        default_name = f"{template.name}"

        name = await AsyncMenu.text(
            "Scene name:",
            default=default_name,
            validate=lambda x: True if 1 <= len(x) <= 32 else "Name must be 1-32 characters",
        )

        return name

    def _template_to_action(self, template: MoodTemplate) -> SceneLightAction:
        """Convert a mood template to a SceneLightAction."""
        action = SceneLightAction(
            on=template.on,
            brightness=template.brightness if template.on else None,
        )

        if template.color_mode == "temperature":
            action.color_temperature_mirek = template.get_mirek()
        elif template.color_mode == "color" and template.color_xy:
            action.color_xy = XYColor(x=template.color_xy[0], y=template.color_xy[1])
        elif template.color_mode == "effect" and template.effect:
            action.effect = template.effect
            # Effects usually work better with color temp set
            action.color_temperature_mirek = template.get_mirek()

        if template.transition_ms:
            action.dynamics_duration_ms = template.transition_ms

        return action

    async def _preview_scene(
        self,
        lights: list[Light],
        action: SceneLightAction,
        template: MoodTemplate,
    ) -> str:
        """Preview the scene on actual lights."""
        console.print("\n[bold]Step 4:[/bold] Preview\n")

        icon = get_icon_for_template(template)
        console.print(f"Previewing [bold]{icon} {template.name}[/bold] on {len(lights)} lights...\n")

        result = await self.preview.preview_interactive(lights, action)
        return result

    async def _create_scene(
        self,
        name: str,
        target: Union[Room, Zone],
        target_type: str,
        template: MoodTemplate,
        lights: list[Light],
    ) -> WizardResult:
        """Create the scene."""
        console.print("\n[bold]Step 5:[/bold] Creating scene...\n")

        try:
            # Build actions for each light
            actions = []
            base_action = self._template_to_action(template)

            for light in lights:
                actions.append(SceneAction(
                    target_rid=light.id,
                    target_rtype="light",
                    action=base_action,
                ))

            # Build palette if template has dynamic colors
            palette = None
            if template.palette_colors and template.auto_dynamic:
                palette_colors = [
                    ScenePaletteColor(
                        color=XYColor(x=xy[0], y=xy[1]),
                        dimming=template.brightness,
                    )
                    for xy in template.palette_colors
                ]
                palette = ScenePalette(colors=palette_colors)

            # Create the request
            request = CreateSceneRequest(
                name=name,
                group_id=target.id,
                group_type=target_type,
                actions=actions,
                palette=palette,
                speed=template.speed,
                auto_dynamic=template.auto_dynamic,
            )

            # Create the scene
            scene = await self.scene_manager.create_scene(request)

            WizardPanel.success(f"Created scene '{name}'!")

            # Ask if user wants to activate
            activate = await AsyncMenu.confirm(
                "Activate this scene now?",
                default=True,
            )

            if activate:
                await self.scene_manager.recall_scene(scene.id)
                StatusMessage.success("Scene activated!")

            return WizardResult(
                success=True,
                message=f"Created scene '{name}'",
                data=scene,
            )

        except Exception as e:
            WizardPanel.error(f"Failed to create scene: {e}")
            return WizardResult(success=False, message=str(e))
