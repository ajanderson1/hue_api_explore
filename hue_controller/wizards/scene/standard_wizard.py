"""
Standard Scene Wizard

Light-by-light scene configuration with arrow key navigation.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Optional, Union
from rich.console import Console
from rich.table import Table
from rich import box

from ...bridge_connector import BridgeConnector
from ...device_manager import DeviceManager
from ...models import (
    Room, Zone, Light,
    CreateSceneRequest, SceneAction, SceneLightAction,
    XYColor,
)
from ...managers.scene_manager import SceneManager
from ..base_wizard import WizardResult
from ..ui import AsyncMenu, MenuChoice, WizardPanel, StatusMessage
from ..ui.components import LightConfig, LightConfigTable
from .preview import LivePreview


console = Console()


# Color temperature presets
COLOR_TEMP_PRESETS = [
    ("Candlelight", 2000),
    ("Warm", 2700),
    ("Soft", 3000),
    ("Neutral", 4000),
    ("Cool", 5000),
    ("Daylight", 5500),
    ("Bright", 6500),
]

# Common color presets (name, x, y)
COLOR_PRESETS = [
    ("Red", 0.675, 0.322),
    ("Orange", 0.588, 0.393),
    ("Yellow", 0.461, 0.469),
    ("Green", 0.214, 0.709),
    ("Cyan", 0.170, 0.340),
    ("Blue", 0.167, 0.040),
    ("Purple", 0.292, 0.132),
    ("Pink", 0.466, 0.227),
    ("White", 0.323, 0.329),
]


@dataclass
class LightSettings:
    """Settings for a single light in the scene."""
    light: Light
    enabled: bool = True
    on: bool = True
    brightness: float = 100.0
    color_mode: str = "temperature"  # "temperature" or "color"
    color_temp_kelvin: int = 4000
    color_xy: Optional[tuple[float, float]] = None


@dataclass
class StandardSceneWizard:
    """
    Standard scene wizard with per-light configuration.

    Provides arrow-key navigation for selecting and configuring
    each light individually.
    """
    connector: BridgeConnector
    device_manager: DeviceManager
    light_settings: dict[str, LightSettings] = field(default_factory=dict)

    def __post_init__(self):
        self.scene_manager = SceneManager(self.connector, self.device_manager)
        self.preview = LivePreview(self.connector, self.device_manager)

    async def run(self) -> WizardResult:
        """Run the standard scene wizard."""
        console.clear()
        WizardPanel.header(
            "Standard Scene Setup",
            "Configure each light individually"
        )

        # Step 1: Select room/zone
        target, target_type = await self._select_target()
        if target is None:
            return WizardResult(success=False, message="Cancelled")

        # Initialize light settings
        lights = self.device_manager.get_lights_for_target(target)
        if not lights:
            WizardPanel.error(f"No lights found in {target.name}")
            return WizardResult(success=False, message="No lights found")

        for light in lights:
            self.light_settings[light.id] = LightSettings(light=light)

        # Step 2: Name the scene
        name = await self._get_scene_name(target)
        if name is None:
            return WizardResult(success=False, message="Cancelled")

        # Step 3: Configure lights
        result = await self._configure_lights_menu()
        if result == "cancel":
            return WizardResult(success=False, message="Cancelled")

        # Step 4: Preview and create
        return await self._preview_and_create(name, target, target_type)

    async def _select_target(self) -> tuple[Optional[Union[Room, Zone]], Optional[str]]:
        """Select a room or zone."""
        console.print("\n[bold]Step 1:[/bold] Select room or zone\n")

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
            WizardPanel.error("No rooms or zones found.")
            return None, None

        selected = await AsyncMenu.select("Select location:", choices=choices)
        if selected is None:
            return None, None

        target_type, target_id = selected
        if target_type == "room":
            return self.device_manager.rooms.get(target_id), "room"
        else:
            return self.device_manager.zones.get(target_id), "zone"

    async def _get_scene_name(self, target: Union[Room, Zone]) -> Optional[str]:
        """Get the scene name."""
        console.print("\n[bold]Step 2:[/bold] Name your scene\n")

        name = await AsyncMenu.text(
            "Scene name:",
            default="",
            validate=lambda x: True if 1 <= len(x) <= 32 else "Name must be 1-32 characters",
        )

        return name

    async def _configure_lights_menu(self) -> str:
        """Main light configuration menu."""
        console.print("\n[bold]Step 3:[/bold] Configure lights\n")

        while True:
            # Show current configuration
            self._display_light_summary()

            # Menu options
            choices = [
                MenuChoice(label="Configure a light", value="configure"),
                MenuChoice(label="Apply template to all", value="template"),
                MenuChoice(label="Test current settings", value="test"),
                MenuChoice(label="Done configuring", value="done"),
                MenuChoice(label="Cancel", value="cancel"),
            ]

            action = await AsyncMenu.select("What would you like to do?", choices=choices)

            if action == "configure":
                await self._configure_single_light_menu()
            elif action == "template":
                await self._apply_template_to_all()
            elif action == "test":
                await self._test_all_lights()
            elif action == "done":
                return "done"
            elif action == "cancel" or action is None:
                return "cancel"

    def _display_light_summary(self) -> None:
        """Display a summary table of all light configurations."""
        table = Table(
            title="Light Configuration",
            box=box.ROUNDED,
            border_style="blue",
        )

        table.add_column("Light", style="white")
        table.add_column("Status", justify="center")
        table.add_column("Brightness", justify="right")
        table.add_column("Color/Temp")

        for settings in self.light_settings.values():
            if not settings.enabled:
                table.add_row(
                    f"[dim]{settings.light.name}[/dim]",
                    "[dim]EXCLUDED[/dim]",
                    "-", "-"
                )
                continue

            status = "[green]ON[/green]" if settings.on else "[red]OFF[/red]"
            brightness = f"{settings.brightness:.0f}%" if settings.on else "-"

            if settings.color_mode == "temperature":
                color = f"{settings.color_temp_kelvin}K"
            elif settings.color_xy:
                # Find matching preset name
                color_name = "Custom"
                for name, x, y in COLOR_PRESETS:
                    if abs(x - settings.color_xy[0]) < 0.05 and abs(y - settings.color_xy[1]) < 0.05:
                        color_name = name
                        break
                color = color_name
            else:
                color = "-"

            table.add_row(settings.light.name, status, brightness, color)

        console.print(table)
        console.print()

    async def _configure_single_light_menu(self) -> None:
        """Select and configure a single light."""
        # Build light choices
        choices = []
        for settings in self.light_settings.values():
            status = "ON" if settings.on else "OFF"
            if not settings.enabled:
                status = "EXCLUDED"
            choices.append(MenuChoice(
                label=f"{settings.light.name}",
                value=settings.light.id,
                description=f"{status}, {settings.brightness:.0f}%",
            ))

        selected = await AsyncMenu.select("Select light to configure:", choices=choices)
        if selected is None:
            return

        await self._configure_light(selected)

    async def _configure_light(self, light_id: str) -> None:
        """Configure a single light's settings."""
        settings = self.light_settings.get(light_id)
        if not settings:
            return

        console.print(f"\n[bold]Configuring: {settings.light.name}[/bold]\n")

        while True:
            # Current settings
            console.print(f"  Power: {'ON' if settings.on else 'OFF'}")
            console.print(f"  Brightness: {settings.brightness:.0f}%")
            if settings.color_mode == "temperature":
                console.print(f"  Color: {settings.color_temp_kelvin}K")
            else:
                console.print(f"  Color: Custom XY")
            console.print(f"  Included: {'Yes' if settings.enabled else 'No'}")
            console.print()

            choices = [
                MenuChoice(label="Toggle power (ON/OFF)", value="power"),
                MenuChoice(label="Set brightness", value="brightness"),
                MenuChoice(label="Set color temperature", value="temp"),
                MenuChoice(label="Set color", value="color"),
                MenuChoice(label="Toggle include/exclude", value="include"),
                MenuChoice(label="Test this light", value="test"),
                MenuChoice(label="Done with this light", value="done"),
            ]

            action = await AsyncMenu.select("Configure:", choices=choices)

            if action == "power":
                settings.on = not settings.on
                StatusMessage.info(f"Power: {'ON' if settings.on else 'OFF'}")

            elif action == "brightness":
                brightness = await AsyncMenu.number(
                    "Brightness (1-100%):",
                    min_value=1,
                    max_value=100,
                    default=settings.brightness,
                )
                if brightness is not None:
                    settings.brightness = brightness

            elif action == "temp":
                await self._set_color_temperature(settings)

            elif action == "color":
                await self._set_color(settings)

            elif action == "include":
                settings.enabled = not settings.enabled
                StatusMessage.info(f"Light {'included' if settings.enabled else 'excluded'}")

            elif action == "test":
                await self._test_single_light(settings)

            elif action == "done" or action is None:
                break

    async def _set_color_temperature(self, settings: LightSettings) -> None:
        """Set color temperature for a light."""
        choices = [
            MenuChoice(label=f"{name} ({temp}K)", value=temp)
            for name, temp in COLOR_TEMP_PRESETS
        ]
        choices.append(MenuChoice(label="Custom value...", value="custom"))

        selected = await AsyncMenu.select("Color temperature:", choices=choices)

        if selected == "custom":
            temp = await AsyncMenu.number(
                "Temperature (2000-6500K):",
                min_value=2000,
                max_value=6500,
                default=settings.color_temp_kelvin,
            )
            if temp is not None:
                settings.color_mode = "temperature"
                settings.color_temp_kelvin = int(temp)
        elif selected is not None:
            settings.color_mode = "temperature"
            settings.color_temp_kelvin = selected

    async def _set_color(self, settings: LightSettings) -> None:
        """Set color for a light."""
        choices = [
            MenuChoice(label=name, value=(x, y))
            for name, x, y in COLOR_PRESETS
        ]

        selected = await AsyncMenu.select("Select color:", choices=choices)

        if selected is not None:
            settings.color_mode = "color"
            settings.color_xy = selected

    async def _apply_template_to_all(self) -> None:
        """Apply a template to all lights."""
        choices = [
            MenuChoice(label="Bright (100%, 4000K)", value="bright"),
            MenuChoice(label="Warm Relaxed (50%, 2700K)", value="warm"),
            MenuChoice(label="Cozy Evening (30%, 2200K)", value="cozy"),
            MenuChoice(label="Energize (100%, 5500K)", value="energize"),
            MenuChoice(label="Nightlight (5%, 2200K)", value="night"),
            MenuChoice(label="All Off", value="off"),
        ]

        selected = await AsyncMenu.select("Select template:", choices=choices)
        if selected is None:
            return

        templates = {
            "bright": (True, 100, 4000),
            "warm": (True, 50, 2700),
            "cozy": (True, 30, 2200),
            "energize": (True, 100, 5500),
            "night": (True, 5, 2200),
            "off": (False, 0, 4000),
        }

        on, brightness, temp = templates[selected]

        for settings in self.light_settings.values():
            settings.on = on
            settings.brightness = brightness
            settings.color_temp_kelvin = temp
            settings.color_mode = "temperature"

        StatusMessage.success(f"Applied template to all lights")

    async def _test_single_light(self, settings: LightSettings) -> None:
        """Test a single light's settings."""
        action = self._settings_to_action(settings)
        await self.preview.preview_interactive([settings.light], action)

    async def _test_all_lights(self) -> None:
        """Test all light settings."""
        lights = []
        actions = []

        for settings in self.light_settings.values():
            if settings.enabled:
                lights.append(settings.light)
                actions.append(self._settings_to_action(settings))

        if not lights:
            WizardPanel.warning("No lights to test")
            return

        # Apply all settings
        await self.preview.capture_states(lights)
        console.print("\n[cyan]Applying all settings...[/cyan]")

        for light, action in zip(lights, actions):
            try:
                payload = action.to_dict()
                await self.connector.put(f"/resource/light/{light.id}", payload)
                console.print(f"  [green][/green] {light.name}")
            except Exception as e:
                console.print(f"  [red][/red] {light.name}: {e}")

        console.print("\n[bold]Look at your lights![/bold]")

        choice = await AsyncMenu.select(
            "What would you like to do?",
            choices=[
                "Keep these settings",
                "Restore previous settings",
            ],
        )

        if choice and "Restore" in choice:
            await self.preview.restore_states()
            StatusMessage.success("Settings restored")

    def _settings_to_action(self, settings: LightSettings) -> SceneLightAction:
        """Convert LightSettings to SceneLightAction."""
        action = SceneLightAction(
            on=settings.on if settings.enabled else False,
        )

        if settings.on and settings.enabled:
            action.brightness = settings.brightness

            if settings.color_mode == "temperature":
                action.color_temperature_mirek = int(1_000_000 / settings.color_temp_kelvin)
            elif settings.color_xy:
                action.color_xy = XYColor(x=settings.color_xy[0], y=settings.color_xy[1])

        return action

    async def _preview_and_create(
        self,
        name: str,
        target: Union[Room, Zone],
        target_type: str,
    ) -> WizardResult:
        """Preview settings and create the scene."""
        console.print("\n[bold]Step 4:[/bold] Create scene\n")

        # Build actions
        actions = []
        for settings in self.light_settings.values():
            if settings.enabled:
                actions.append(SceneAction(
                    target_rid=settings.light.id,
                    target_rtype="light",
                    action=self._settings_to_action(settings),
                ))

        if not actions:
            WizardPanel.error("No lights configured")
            return WizardResult(success=False, message="No lights configured")

        # Confirm creation
        confirm = await AsyncMenu.confirm(
            f"Create scene '{name}' with {len(actions)} lights?",
            default=True,
        )

        if not confirm:
            return WizardResult(success=False, message="Cancelled")

        try:
            request = CreateSceneRequest(
                name=name,
                group_id=target.id,
                group_type=target_type,
                actions=actions,
            )

            scene = await self.scene_manager.create_scene(request)
            WizardPanel.success(f"Created scene '{name}'!")

            # Offer to activate
            activate = await AsyncMenu.confirm("Activate this scene now?", default=True)
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
