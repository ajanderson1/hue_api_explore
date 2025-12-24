"""
Admin Scene Wizard

Advanced interactive wizard for comprehensive scene configuration.
Provides access to ALL scene options with templates, live preview, and
an intuitive sectioned interface.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Any

from .wizard_ui import WizardUI, NavAction, SelectOption, WizardSection
from .base_wizard import WizardResult
from ..models import (
    Scene,
    Light,
    Room,
    Zone,
    XYColor,
    GradientConfig,
    SceneAction,
    SceneLightAction,
    ScenePalette,
    ScenePaletteColor,
    ScenePaletteColorTemp,
    CreateSceneRequest,
    UpdateSceneRequest,
    RecallSceneRequest,
)
from ..color_utils import parse_color
from ..constants import (
    EFFECT_TYPES,
    EFFECT_DESCRIPTIONS,
    GRADIENT_MODES,
    GRADIENT_MODE_DESCRIPTIONS,
    TEMPERATURE_BY_NAME,
    TEMPERATURE_DESCRIPTIONS,
    MIREK_MIN,
    MIREK_MAX,
    MAX_TRANSITION_MS,
    SCENE_RECALL_ACTIONS,
    SCENE_RECALL_DESCRIPTIONS,
)

if TYPE_CHECKING:
    from ..device_manager import DeviceManager
    from ..bridge_connector import BridgeConnector
    from ..managers.scene_manager import SceneManager


# =============================================================================
# Scene Configuration Data Classes
# =============================================================================

@dataclass
class LightActionConfig:
    """Configuration for a single light's action in the scene."""
    light_id: str
    light_name: str
    enabled: bool = True
    on: bool = True
    brightness: float = 100.0
    color_mode: str = "temperature"  # "temperature", "color", "gradient"
    color_xy: Optional[XYColor] = None
    color_temperature_mirek: int = 370  # Warm white
    gradient: Optional[GradientConfig] = None
    effect: Optional[str] = None
    dynamics_duration_ms: Optional[int] = None

    def to_scene_action(self) -> SceneAction:
        """Convert to SceneAction model."""
        action = SceneLightAction(
            on=self.on if self.enabled else False,
            brightness=self.brightness if self.on and self.enabled else None,
            dynamics_duration_ms=self.dynamics_duration_ms,
        )

        if self.on and self.enabled:
            if self.color_mode == "color" and self.color_xy:
                action.color_xy = self.color_xy
            elif self.color_mode == "gradient" and self.gradient:
                action.gradient = self.gradient
            elif self.color_mode == "temperature":
                action.color_temperature_mirek = self.color_temperature_mirek

            if self.effect and self.effect != "no_effect":
                action.effect = self.effect

        return SceneAction(
            target_rid=self.light_id,
            target_rtype="light",
            action=action
        )


@dataclass
class PaletteConfig:
    """Configuration for the scene's dynamic palette."""
    enabled: bool = False
    colors: list[tuple[XYColor, Optional[float]]] = field(default_factory=list)  # (color, brightness)
    color_temperatures: list[tuple[int, Optional[float]]] = field(default_factory=list)  # (mirek, brightness)
    dimming_levels: list[float] = field(default_factory=list)
    effects: list[str] = field(default_factory=list)

    def to_scene_palette(self) -> Optional[ScenePalette]:
        """Convert to ScenePalette model."""
        if not self.enabled:
            return None

        palette = ScenePalette()

        for color, brightness in self.colors:
            palette.colors.append(ScenePaletteColor(color=color, dimming=brightness))

        for mirek, brightness in self.color_temperatures:
            palette.color_temperatures.append(
                ScenePaletteColorTemp(color_temperature_mirek=mirek, dimming=brightness)
            )

        palette.dimming = self.dimming_levels
        palette.effects = self.effects

        return palette if (palette.colors or palette.color_temperatures or
                         palette.dimming or palette.effects) else None


@dataclass
class DynamicsConfig:
    """Configuration for scene dynamics (speed, auto_dynamic)."""
    speed: float = 0.5  # 0.0-1.0
    auto_dynamic: bool = False
    global_duration_ms: Optional[int] = None  # Applied to all lights if set


@dataclass
class RecallConfig:
    """Configuration for how the scene is recalled/activated."""
    action: str = "active"  # "active", "dynamic_palette", "static"
    duration_ms: Optional[int] = None
    brightness_override: Optional[float] = None


@dataclass
class SceneConfig:
    """Complete scene configuration."""
    # Metadata
    name: str = ""
    image_rid: Optional[str] = None

    # Group target
    group_id: str = ""
    group_type: str = "room"  # "room", "zone", "bridge_home"
    group_name: str = ""

    # Actions per light
    light_actions: list[LightActionConfig] = field(default_factory=list)

    # Palette
    palette: PaletteConfig = field(default_factory=PaletteConfig)

    # Dynamics
    dynamics: DynamicsConfig = field(default_factory=DynamicsConfig)

    # Recall settings
    recall: RecallConfig = field(default_factory=RecallConfig)

    def to_create_request(self) -> CreateSceneRequest:
        """Convert to API create request."""
        return CreateSceneRequest(
            name=self.name,
            group_id=self.group_id,
            group_type=self.group_type,
            actions=[la.to_scene_action() for la in self.light_actions if la.enabled],
            palette=self.palette.to_scene_palette(),
            speed=self.dynamics.speed,
            auto_dynamic=self.dynamics.auto_dynamic,
            image_rid=self.image_rid,
        )


# =============================================================================
# Light Templates
# =============================================================================

@dataclass
class LightTemplate:
    """Pre-configured light settings template."""
    name: str
    description: str
    icon: str
    on: bool = True
    brightness: float = 100.0
    color_mode: str = "temperature"
    color_xy: Optional[XYColor] = None
    color_temp_mirek: int = 370
    effect: Optional[str] = None


LIGHT_TEMPLATES: list[LightTemplate] = [
    LightTemplate(
        name="Bright White",
        description="Full brightness, neutral white",
        icon="☀",
        brightness=100.0,
        color_mode="temperature",
        color_temp_mirek=250,  # 4000K
    ),
    LightTemplate(
        name="Warm Relaxed",
        description="Dimmed warm light for relaxation",
        icon="🕯",
        brightness=50.0,
        color_mode="temperature",
        color_temp_mirek=370,  # 2700K
    ),
    LightTemplate(
        name="Cozy Evening",
        description="Very warm, low brightness",
        icon="🌙",
        brightness=30.0,
        color_mode="temperature",
        color_temp_mirek=454,  # 2200K
    ),
    LightTemplate(
        name="Energize",
        description="Cool bright light for focus",
        icon="⚡",
        brightness=100.0,
        color_mode="temperature",
        color_temp_mirek=182,  # 5500K
    ),
    LightTemplate(
        name="Nightlight",
        description="Very dim warm light",
        icon="🌜",
        brightness=5.0,
        color_mode="temperature",
        color_temp_mirek=454,
    ),
    LightTemplate(
        name="Off",
        description="Light turned off",
        icon="⭘",
        on=False,
        brightness=0.0,
    ),
    LightTemplate(
        name="Sunset Red",
        description="Warm red-orange color",
        icon="🔴",
        brightness=80.0,
        color_mode="color",
        color_xy=XYColor(x=0.6, y=0.38),
    ),
    LightTemplate(
        name="Ocean Blue",
        description="Calm blue color",
        icon="🔵",
        brightness=70.0,
        color_mode="color",
        color_xy=XYColor(x=0.17, y=0.15),
    ),
    LightTemplate(
        name="Forest Green",
        description="Natural green color",
        icon="🟢",
        brightness=60.0,
        color_mode="color",
        color_xy=XYColor(x=0.2, y=0.7),
    ),
    LightTemplate(
        name="Purple Mood",
        description="Deep purple ambiance",
        icon="🟣",
        brightness=50.0,
        color_mode="color",
        color_xy=XYColor(x=0.3, y=0.15),
    ),
    LightTemplate(
        name="Candle Effect",
        description="Flickering candle simulation",
        icon="🕯",
        brightness=60.0,
        color_mode="temperature",
        color_temp_mirek=454,
        effect="candle",
    ),
    LightTemplate(
        name="Fire Effect",
        description="Warm fire glow",
        icon="🔥",
        brightness=80.0,
        color_mode="temperature",
        color_temp_mirek=454,
        effect="fire",
    ),
]


# =============================================================================
# Scene Image Presets (curated from Hue public images)
# =============================================================================

SCENE_IMAGE_PRESETS: list[tuple[str, str, str]] = [
    # (rid, name, description)
    ("732ff1d9-76a7-4630-aad0-c8acc499bb0b", "Bright", "Bright daylight scene"),
    ("a1f7da49-d181-4328-abea-68c9dc4b5416", "Dimmed", "Dimmed ambient scene"),
    ("c1e74278-758b-4d9c-9e3d-c60aba1e526d", "Nightlight", "Soft nightlight"),
    ("ab71ef7c-b1b2-421f-8ae8-f6d5caa73e96", "Relax", "Relaxing warm scene"),
    ("2869afc0-a84c-43ab-a672-c32dad9c06ce", "Read", "Reading light"),
    ("a1b0a844-d7d4-4cf3-9d7b-d5c53df2f02a", "Concentrate", "Focus light"),
    ("0c38e0bf-0d62-4e86-b6fd-3ead4b45c5ed", "Energize", "Energizing cool light"),
    ("8e740d69-b35a-4f78-b2ed-a0d8fd19ce99", "Movie", "Movie watching scene"),
    ("15dfa43f-8eb4-49d0-85a0-4ba16545c1f4", "Romance", "Romantic ambiance"),
    ("4d5c69e6-0d92-434c-8f72-0e8a6eb8e1a9", "Party", "Party colors"),
]


# =============================================================================
# Admin Scene Wizard
# =============================================================================

class AdminSceneWizard:
    """
    Advanced scene configuration wizard.

    Provides comprehensive access to all scene properties with:
    - Sectioned navigation (Metadata, Actions, Palette, Dynamics, Recall)
    - Light templates for quick configuration
    - Live preview/test functionality
    - Intuitive UI with rich formatting
    """

    SECTIONS = [
        WizardSection("metadata", "Metadata", "📝", "Scene name and icon", required=True),
        WizardSection("actions", "Light Actions", "💡", "Configure each light"),
        WizardSection("palette", "Palette", "🎨", "Dynamic color cycling"),
        WizardSection("dynamics", "Dynamics", "⚡", "Speed and transitions"),
        WizardSection("recall", "Recall", "▶", "Activation settings"),
        WizardSection("review", "Review", "✓", "Review and create"),
    ]

    def __init__(
        self,
        connector: BridgeConnector,
        device_manager: DeviceManager,
        scene_manager: SceneManager,
    ):
        """Initialize the admin scene wizard."""
        self.connector = connector
        self.dm = device_manager
        self.scene_manager = scene_manager
        self.ui = WizardUI()
        self.config = SceneConfig()
        self._current_section = 0

    async def run(self) -> WizardResult:
        """Run the admin scene wizard."""
        self.ui.print_wizard_header(
            "Admin Scene Wizard",
            "Complete control over every scene parameter"
        )

        # Step 1: Select target group first (required for everything else)
        result = await self._select_target_group()
        if result:
            return result

        # Main wizard loop with section navigation
        while True:
            # Show section navigation
            self.ui.print_section_nav(self.SECTIONS, self.SECTIONS[self._current_section].id)

            # Handle current section
            section = self.SECTIONS[self._current_section]
            action = await self._handle_section(section.id)

            if action == NavAction.CANCEL:
                return WizardResult(
                    success=False,
                    message="Admin scene wizard cancelled",
                    cancelled=True
                )
            elif action == NavAction.BACK:
                if self._current_section > 0:
                    self._current_section -= 1
            elif action == NavAction.CONTINUE:
                if self._current_section < len(self.SECTIONS) - 1:
                    self.SECTIONS[self._current_section].completed = True
                    self._current_section += 1
                else:
                    # Final section - create the scene
                    return await self._create_scene()
            elif action == NavAction.SAVE:
                # Jump to review
                self._current_section = len(self.SECTIONS) - 1

    async def _select_target_group(self) -> Optional[WizardResult]:
        """Select the target room, zone, or bridge_home."""
        self.ui.print_section_header(
            "Select Target",
            description="Choose where this scene will apply"
        )

        options: list[SelectOption] = []

        # Add bridge_home option for all lights
        options.append(SelectOption(
            label="All Lights (Bridge Home)",
            value=("bridge_home", "bridge_home", "All Lights"),
            description="Apply scene to all lights on the bridge",
            icon="🏠"
        ))

        # Add rooms
        for room in sorted(self.dm.rooms.values(), key=lambda r: r.name):
            light_count = len(self.dm.get_lights_for_target(room))
            options.append(SelectOption(
                label=f"{room.name}",
                value=(room.id, "room", room.name),
                description=f"Room with {light_count} light(s)",
                icon="🚪"
            ))

        # Add zones
        for zone in sorted(self.dm.zones.values(), key=lambda z: z.name):
            light_count = len(self.dm.get_lights_for_target(zone))
            options.append(SelectOption(
                label=f"{zone.name}",
                value=(zone.id, "zone", zone.name),
                description=f"Zone with {light_count} light(s)",
                icon="📍"
            ))

        result, action = await self.ui.select_one(
            "Select target for the scene",
            options,
            allow_back=False
        )

        if action == NavAction.CANCEL or result is None:
            return WizardResult(success=False, message="Cancelled", cancelled=True)

        self.config.group_id, self.config.group_type, self.config.group_name = result

        # Initialize light actions based on target
        await self._initialize_light_actions()
        return None

    async def _initialize_light_actions(self) -> None:
        """Initialize light action configs for all lights in the target."""
        if self.config.group_type == "bridge_home":
            lights = list(self.dm.lights.values())
        else:
            group = (self.dm.rooms.get(self.config.group_id) or
                    self.dm.zones.get(self.config.group_id))
            lights = self.dm.get_lights_for_target(group) if group else []

        self.config.light_actions = []
        for light in sorted(lights, key=lambda l: l.name):
            # Use current state as default
            action_config = LightActionConfig(
                light_id=light.id,
                light_name=light.name,
                on=light.is_on,
                brightness=light.brightness if light.is_on else 100.0,
            )

            # Detect current color mode
            if light.color_xy:
                action_config.color_mode = "color"
                action_config.color_xy = light.color_xy
            elif light.color_temperature_mirek:
                action_config.color_mode = "temperature"
                action_config.color_temperature_mirek = light.color_temperature_mirek

            self.config.light_actions.append(action_config)

    async def _handle_section(self, section_id: str) -> NavAction:
        """Handle a wizard section."""
        if section_id == "metadata":
            return await self._section_metadata()
        elif section_id == "actions":
            return await self._section_actions()
        elif section_id == "palette":
            return await self._section_palette()
        elif section_id == "dynamics":
            return await self._section_dynamics()
        elif section_id == "recall":
            return await self._section_recall()
        elif section_id == "review":
            return await self._section_review()
        return NavAction.CONTINUE

    # =========================================================================
    # Section: Metadata
    # =========================================================================

    async def _section_metadata(self) -> NavAction:
        """Configure scene metadata (name, image)."""
        self.ui.print_section_header(
            "Scene Metadata",
            step=1, total=6,
            description="Set the scene name and icon"
        )

        # Scene name
        name, action = await self.ui.get_input(
            "Scene name (1-32 characters)",
            default=self.config.name or None,
            validator=lambda x: 1 <= len(x) <= 32,
            error_message="Name must be 1-32 characters"
        )

        if action == NavAction.CANCEL:
            return NavAction.CANCEL
        if action == NavAction.BACK:
            return NavAction.BACK

        self.config.name = name

        # Scene image (optional)
        self.ui.print_info("\nScene Icon (optional)")

        image_options: list[SelectOption] = [
            SelectOption(
                label="Skip (use default)",
                value=None,
                description="Use the default scene icon",
                icon="⏭"
            )
        ]

        for rid, img_name, img_desc in SCENE_IMAGE_PRESETS:
            image_options.append(SelectOption(
                label=img_name,
                value=rid,
                description=img_desc,
            ))

        image_result, action = await self.ui.select_one(
            "Select scene icon",
            image_options,
            default=self.config.image_rid,
            allow_skip=True
        )

        if action == NavAction.CANCEL:
            return NavAction.CANCEL
        if action == NavAction.BACK:
            return NavAction.BACK

        self.config.image_rid = image_result
        return NavAction.CONTINUE

    # =========================================================================
    # Section: Light Actions
    # =========================================================================

    async def _section_actions(self) -> NavAction:
        """Configure light actions with templates."""
        self.ui.print_section_header(
            "Light Actions",
            step=2, total=6,
            description=f"Configure lights in {self.config.group_name}"
        )

        # Main menu for actions section
        while True:
            options = [
                SelectOption("Apply template to ALL lights", "template_all",
                           description="Quick setup with a preset", icon="📋"),
                SelectOption("Configure lights individually", "individual",
                           description="Fine-tune each light", icon="🔧"),
                SelectOption("View current configuration", "view",
                           description="See what's configured", icon="👁"),
                SelectOption("Continue to next section", "continue",
                           description="Accept current settings", icon="▶"),
            ]

            if any(la.enabled for la in self.config.light_actions):
                options.insert(3, SelectOption(
                    "Test current settings", "test",
                    description="Preview on actual lights", icon="⚡"
                ))

            choice, action = await self.ui.select_one(
                "Light Actions Menu",
                options,
                allow_back=True
            )

            if action == NavAction.CANCEL:
                return NavAction.CANCEL
            if action == NavAction.BACK:
                return NavAction.BACK

            if choice == "template_all":
                await self._apply_template_to_all()
            elif choice == "individual":
                await self._configure_lights_individually()
            elif choice == "view":
                self._view_light_configuration()
            elif choice == "test":
                await self._test_light_actions()
            elif choice == "continue":
                return NavAction.CONTINUE

    async def _apply_template_to_all(self) -> None:
        """Apply a template to all lights."""
        template_options = [
            SelectOption(
                label=t.name,
                value=t,
                description=t.description,
                icon=t.icon
            )
            for t in LIGHT_TEMPLATES
        ]

        template, action = await self.ui.select_one(
            "Select template for ALL lights",
            template_options
        )

        if action != NavAction.CONTINUE or template is None:
            return

        # Apply template to all lights
        for la in self.config.light_actions:
            la.on = template.on
            la.brightness = template.brightness
            la.color_mode = template.color_mode
            if template.color_xy:
                la.color_xy = template.color_xy
            la.color_temperature_mirek = template.color_temp_mirek
            la.effect = template.effect

        self.ui.print_success(f"Applied '{template.name}' to all {len(self.config.light_actions)} lights")

    async def _configure_lights_individually(self) -> None:
        """Configure each light individually."""
        while True:
            # Build options for each light
            light_options = []
            for la in self.config.light_actions:
                status = "ON" if la.on and la.enabled else "OFF"
                if la.enabled and la.on:
                    status += f" {la.brightness:.0f}%"
                    if la.effect:
                        status += f" [{la.effect}]"

                light_options.append(SelectOption(
                    label=la.light_name,
                    value=la,
                    description=status,
                    icon="💡" if la.on and la.enabled else "⭘"
                ))

            light_options.append(SelectOption(
                label="Done configuring lights",
                value=None,
                description="Return to actions menu",
                icon="✓"
            ))

            selected, action = await self.ui.select_one(
                "Select light to configure",
                light_options
            )

            if action != NavAction.CONTINUE or selected is None:
                break

            await self._configure_single_light(selected)

    async def _configure_single_light(self, light_action: LightActionConfig) -> None:
        """Configure a single light with all options."""
        self.ui.print_section_header(f"Configure: {light_action.light_name}")

        # Menu for this light
        while True:
            options = [
                SelectOption("Apply template", "template",
                           description="Use a preset configuration", icon="📋"),
                SelectOption(f"Power: {'ON' if light_action.on else 'OFF'}",
                           "power", description="Toggle on/off", icon="⚡"),
            ]

            if light_action.on:
                options.extend([
                    SelectOption(f"Brightness: {light_action.brightness:.0f}%",
                               "brightness", description="0-100%", icon="☀"),
                    SelectOption(f"Color Mode: {light_action.color_mode}",
                               "color_mode", description="Temperature, Color, or Gradient", icon="🎨"),
                    SelectOption(f"Effect: {light_action.effect or 'None'}",
                               "effect", description="Special light effects", icon="✨"),
                    SelectOption(f"Transition: {self._format_duration(light_action.dynamics_duration_ms)}",
                               "transition", description="Animation duration", icon="⏱"),
                ])

            options.extend([
                SelectOption(f"Enabled: {'Yes' if light_action.enabled else 'No (excluded)'}",
                           "enabled", description="Include in scene", icon="✓" if light_action.enabled else "✗"),
                SelectOption("Test this light", "test",
                           description="Preview current settings", icon="▶"),
                SelectOption("Done with this light", "done",
                           description="Return to light list", icon="←"),
            ])

            choice, action = await self.ui.select_one(
                f"Options for {light_action.light_name}",
                options
            )

            if action != NavAction.CONTINUE or choice == "done":
                break

            if choice == "template":
                await self._apply_template_to_light(light_action)
            elif choice == "power":
                light_action.on = not light_action.on
            elif choice == "brightness":
                await self._configure_brightness(light_action)
            elif choice == "color_mode":
                await self._configure_color_mode(light_action)
            elif choice == "effect":
                await self._configure_effect(light_action)
            elif choice == "transition":
                await self._configure_transition(light_action)
            elif choice == "enabled":
                light_action.enabled = not light_action.enabled
            elif choice == "test":
                await self._test_single_light(light_action)

    async def _apply_template_to_light(self, light_action: LightActionConfig) -> None:
        """Apply a template to a single light."""
        template_options = [
            SelectOption(t.name, t, description=t.description, icon=t.icon)
            for t in LIGHT_TEMPLATES
        ]

        template, action = await self.ui.select_one("Select template", template_options)

        if action == NavAction.CONTINUE and template:
            light_action.on = template.on
            light_action.brightness = template.brightness
            light_action.color_mode = template.color_mode
            if template.color_xy:
                light_action.color_xy = template.color_xy
            light_action.color_temperature_mirek = template.color_temp_mirek
            light_action.effect = template.effect
            self.ui.print_success(f"Applied '{template.name}'")

    async def _configure_brightness(self, light_action: LightActionConfig) -> None:
        """Configure brightness for a light."""
        brightness, action = await self.ui.get_slider_value(
            "Brightness",
            min_value=1,
            max_value=100,
            default=light_action.brightness,
            unit="%"
        )
        if action == NavAction.CONTINUE and brightness is not None:
            light_action.brightness = brightness

    async def _configure_color_mode(self, light_action: LightActionConfig) -> None:
        """Configure color mode and value."""
        mode_options = [
            SelectOption("Color Temperature", "temperature",
                       description="Warm to cool white", icon="🌡"),
            SelectOption("Color (XY)", "color",
                       description="Full color spectrum", icon="🌈"),
            SelectOption("Gradient", "gradient",
                       description="Multi-color gradient (if supported)", icon="🎨"),
        ]

        mode, action = await self.ui.select_one(
            "Select color mode",
            mode_options,
            default=light_action.color_mode
        )

        if action != NavAction.CONTINUE or mode is None:
            return

        light_action.color_mode = mode

        if mode == "temperature":
            await self._configure_color_temperature(light_action)
        elif mode == "color":
            await self._configure_color_xy(light_action)
        elif mode == "gradient":
            await self._configure_gradient(light_action)

    async def _configure_color_temperature(self, light_action: LightActionConfig) -> None:
        """Configure color temperature."""
        temp_options = []
        for name, mirek in TEMPERATURE_BY_NAME.items():
            kelvin = int(1_000_000 / mirek)
            temp_options.append(SelectOption(
                label=f"{name.title()} ({kelvin}K)",
                value=mirek,
                description=TEMPERATURE_DESCRIPTIONS.get(name, "")
            ))

        temp_options.append(SelectOption(
            label="Custom mirek value",
            value="custom",
            description=f"Enter value between {MIREK_MIN}-{MIREK_MAX}"
        ))

        choice, action = await self.ui.select_one(
            "Select color temperature",
            temp_options,
            default=light_action.color_temperature_mirek
        )

        if action != NavAction.CONTINUE:
            return

        if choice == "custom":
            mirek, _ = await self.ui.get_number(
                "Enter mirek value",
                min_value=MIREK_MIN,
                max_value=MIREK_MAX,
                default=light_action.color_temperature_mirek,
                allow_float=False
            )
            if mirek:
                light_action.color_temperature_mirek = int(mirek)
        elif choice:
            light_action.color_temperature_mirek = choice

    async def _configure_color_xy(self, light_action: LightActionConfig) -> None:
        """Configure XY color."""
        color_str, action = await self.ui.get_color(
            "Enter color (name, hex #RRGGBB, or 'custom' for XY values)"
        )

        if action != NavAction.CONTINUE or not color_str:
            return

        if color_str.lower() == "custom":
            # Manual XY input
            x, action = await self.ui.get_number("X value", min_value=0, max_value=1, default=0.5)
            if action != NavAction.CONTINUE or x is None:
                return
            y, action = await self.ui.get_number("Y value", min_value=0, max_value=1, default=0.5)
            if action == NavAction.CONTINUE and y is not None:
                light_action.color_xy = XYColor(x=x, y=y)
        else:
            # Parse color name/hex
            color_payload = parse_color(color_str)
            if color_payload and "color" in color_payload:
                xy = color_payload["color"]["xy"]
                light_action.color_xy = XYColor(x=xy["x"], y=xy["y"])
                self.ui.print_success(f"Set color to XY({xy['x']:.3f}, {xy['y']:.3f})")
            else:
                self.ui.print_error("Could not parse color")

    async def _configure_gradient(self, light_action: LightActionConfig) -> None:
        """Configure gradient colors (2-5 points)."""
        self.ui.print_info("Configure gradient (2-5 color points)")

        points: list[XYColor] = []

        while len(points) < 5:
            prompt = f"Color point {len(points) + 1}/5"
            if len(points) >= 2:
                prompt += " (or 'done' to finish)"

            color_str, action = await self.ui.get_color(prompt, allow_skip=len(points) >= 2)

            if action == NavAction.SKIP or not color_str:
                break

            color_payload = parse_color(color_str)
            if color_payload and "color" in color_payload:
                xy = color_payload["color"]["xy"]
                points.append(XYColor(x=xy["x"], y=xy["y"]))
                self.ui.print_success(f"Added point {len(points)}")
            else:
                self.ui.print_error("Could not parse color, try again")

        if len(points) >= 2:
            # Select gradient mode
            mode_options = [
                SelectOption(mode, mode, description=GRADIENT_MODE_DESCRIPTIONS.get(mode, ""))
                for mode in GRADIENT_MODES
            ]

            mode, _ = await self.ui.select_one("Select gradient mode", mode_options)
            light_action.gradient = GradientConfig(
                points=points,
                mode=mode or "interpolated_palette"
            )
            self.ui.print_success(f"Created gradient with {len(points)} points")
        else:
            self.ui.print_warning("Need at least 2 colors for gradient")

    async def _configure_effect(self, light_action: LightActionConfig) -> None:
        """Configure light effect."""
        effect_options = [
            SelectOption(
                label=effect.replace("_", " ").title(),
                value=effect if effect != "no_effect" else None,
                description=EFFECT_DESCRIPTIONS.get(effect, "")
            )
            for effect in EFFECT_TYPES
        ]

        effect, action = await self.ui.select_one(
            "Select effect",
            effect_options,
            default=light_action.effect
        )

        if action == NavAction.CONTINUE:
            light_action.effect = effect

    async def _configure_transition(self, light_action: LightActionConfig) -> None:
        """Configure transition duration."""
        preset_options = [
            SelectOption("Instant", 0, description="No transition"),
            SelectOption("Fast (400ms)", 400, description="Default"),
            SelectOption("Medium (1s)", 1000, description="Smooth transition"),
            SelectOption("Slow (2s)", 2000, description="Gradual change"),
            SelectOption("Very Slow (5s)", 5000, description="Slow fade"),
            SelectOption("Custom", "custom", description="Enter custom duration"),
        ]

        choice, action = await self.ui.select_one(
            "Select transition duration",
            preset_options
        )

        if action != NavAction.CONTINUE:
            return

        if choice == "custom":
            ms, _ = await self.ui.get_number(
                "Duration in milliseconds",
                min_value=0,
                max_value=MAX_TRANSITION_MS,
                default=400,
                allow_float=False,
                unit="ms"
            )
            light_action.dynamics_duration_ms = int(ms) if ms else None
        else:
            light_action.dynamics_duration_ms = choice if choice else None

    def _view_light_configuration(self) -> None:
        """Display current light configuration."""
        columns = ["Light", "On", "Brightness", "Mode", "Effect", "Transition"]
        rows = []

        for la in self.config.light_actions:
            if not la.enabled:
                rows.append([la.light_name, "EXCLUDED", "-", "-", "-", "-"])
            else:
                mode_val = la.color_mode
                if la.color_mode == "temperature":
                    kelvin = int(1_000_000 / la.color_temperature_mirek)
                    mode_val = f"{kelvin}K"
                elif la.color_mode == "color" and la.color_xy:
                    mode_val = f"XY({la.color_xy.x:.2f},{la.color_xy.y:.2f})"
                elif la.color_mode == "gradient":
                    mode_val = f"Gradient ({len(la.gradient.points) if la.gradient else 0}pts)"

                rows.append([
                    la.light_name,
                    "ON" if la.on else "OFF",
                    f"{la.brightness:.0f}%" if la.on else "-",
                    mode_val if la.on else "-",
                    la.effect or "-",
                    self._format_duration(la.dynamics_duration_ms)
                ])

        self.ui.print_table(
            f"Light Configuration ({self.config.group_name})",
            columns,
            rows
        )

    async def _test_light_actions(self) -> None:
        """Test all configured light actions on actual lights."""
        self.ui.print_test_indicator(True)

        try:
            # Apply each light action
            for la in self.config.light_actions:
                if not la.enabled:
                    continue

                action = la.to_scene_action()
                payload = action.action.to_dict()

                await self.connector.put(f"/resource/light/{la.light_id}", payload)
                await asyncio.sleep(0.1)  # Rate limiting

            self.ui.print_info("Settings applied. Press Enter when done viewing.")
            input()
            self.ui.print_test_indicator(False)

        except Exception as e:
            self.ui.print_error(f"Test failed: {e}")

    async def _test_single_light(self, light_action: LightActionConfig) -> None:
        """Test a single light's settings."""
        self.ui.print_test_indicator(True)

        try:
            action = light_action.to_scene_action()
            payload = action.action.to_dict()
            await self.connector.put(f"/resource/light/{light_action.light_id}", payload)

            self.ui.print_info("Setting applied. Press Enter when done viewing.")
            input()
            self.ui.print_test_indicator(False)

        except Exception as e:
            self.ui.print_error(f"Test failed: {e}")

    # =========================================================================
    # Section: Palette
    # =========================================================================

    async def _section_palette(self) -> NavAction:
        """Configure dynamic color palette."""
        self.ui.print_section_header(
            "Dynamic Palette",
            step=3, total=6,
            description="Configure colors that cycle dynamically"
        )

        # Enable/disable palette
        enabled, action = await self.ui.get_confirmation(
            "Enable dynamic palette?",
            default=self.config.palette.enabled
        )

        if action == NavAction.CANCEL:
            return NavAction.CANCEL
        if action == NavAction.BACK:
            return NavAction.BACK

        self.config.palette.enabled = enabled

        if not enabled:
            return NavAction.CONTINUE

        # Palette configuration menu
        while True:
            options = [
                SelectOption(
                    f"Colors ({len(self.config.palette.colors)})",
                    "colors",
                    description="Add/edit palette colors",
                    icon="🎨"
                ),
                SelectOption(
                    f"Color Temperatures ({len(self.config.palette.color_temperatures)})",
                    "temps",
                    description="Add/edit temperature values",
                    icon="🌡"
                ),
                SelectOption(
                    f"Brightness Levels ({len(self.config.palette.dimming_levels)})",
                    "dimming",
                    description="Add brightness variation",
                    icon="☀"
                ),
                SelectOption(
                    f"Effects ({len(self.config.palette.effects)})",
                    "effects",
                    description="Add effect cycling",
                    icon="✨"
                ),
                SelectOption("Continue", "continue", icon="▶"),
            ]

            choice, action = await self.ui.select_one("Palette Configuration", options)

            if action == NavAction.CANCEL:
                return NavAction.CANCEL
            if action == NavAction.BACK:
                return NavAction.BACK

            if choice == "colors":
                await self._configure_palette_colors()
            elif choice == "temps":
                await self._configure_palette_temperatures()
            elif choice == "dimming":
                await self._configure_palette_dimming()
            elif choice == "effects":
                await self._configure_palette_effects()
            elif choice == "continue":
                return NavAction.CONTINUE

    async def _configure_palette_colors(self) -> None:
        """Configure palette colors."""
        self.ui.print_info("Add up to 9 colors for dynamic cycling")

        colors: list[tuple[XYColor, Optional[float]]] = list(self.config.palette.colors)

        while len(colors) < 9:
            color_str, action = await self.ui.get_color(
                f"Color {len(colors) + 1}/9 (or 'done')",
                allow_skip=True
            )

            if action == NavAction.SKIP or not color_str:
                break

            color_payload = parse_color(color_str)
            if not color_payload or "color" not in color_payload:
                self.ui.print_error("Invalid color")
                continue

            xy = color_payload["color"]["xy"]
            color = XYColor(x=xy["x"], y=xy["y"])

            # Ask for brightness for this color
            brightness, _ = await self.ui.get_number(
                "Brightness for this color (skip for default)",
                min_value=1,
                max_value=100,
                default=None,
                unit="%",
                allow_skip=True
            )

            colors.append((color, brightness))
            self.ui.print_success(f"Added color {len(colors)}")

        self.config.palette.colors = colors

    async def _configure_palette_temperatures(self) -> None:
        """Configure palette color temperatures."""
        self.ui.print_info("Add color temperatures for cycling")

        temps: list[tuple[int, Optional[float]]] = []

        temp_options = [
            SelectOption(f"{name.title()}", mirek, description=f"{int(1_000_000/mirek)}K")
            for name, mirek in TEMPERATURE_BY_NAME.items()
        ]
        temp_options.append(SelectOption("Done adding", None, icon="✓"))

        while len(temps) < 9:
            choice, action = await self.ui.select_one(
                f"Add temperature {len(temps) + 1}/9",
                temp_options
            )

            if action != NavAction.CONTINUE or choice is None:
                break

            brightness, _ = await self.ui.get_number(
                "Brightness (skip for default)",
                min_value=1,
                max_value=100,
                default=None,
                allow_skip=True
            )

            temps.append((choice, brightness))

        self.config.palette.color_temperatures = temps

    async def _configure_palette_dimming(self) -> None:
        """Configure palette brightness levels."""
        self.ui.print_info("Add brightness levels for cycling")

        levels: list[float] = []

        while len(levels) < 9:
            level, action = await self.ui.get_number(
                f"Brightness level {len(levels) + 1}/9 (or skip to finish)",
                min_value=1,
                max_value=100,
                default=None,
                unit="%",
                allow_skip=True
            )

            if action == NavAction.SKIP or level is None:
                break

            levels.append(level)

        self.config.palette.dimming_levels = levels

    async def _configure_palette_effects(self) -> None:
        """Configure palette effects."""
        effect_options = [
            SelectOption(e.replace("_", " ").title(), e, description=EFFECT_DESCRIPTIONS.get(e, ""))
            for e in EFFECT_TYPES if e != "no_effect"
        ]

        effects, action = await self.ui.select_multiple(
            "Select effects to cycle through",
            effect_options,
            defaults=self.config.palette.effects
        )

        if action == NavAction.CONTINUE:
            self.config.palette.effects = effects

    # =========================================================================
    # Section: Dynamics
    # =========================================================================

    async def _section_dynamics(self) -> NavAction:
        """Configure dynamics (speed, auto_dynamic)."""
        self.ui.print_section_header(
            "Scene Dynamics",
            step=4, total=6,
            description="Configure transition speed and auto-dynamic mode"
        )

        # Speed
        self.ui.print_info("Palette cycling speed (0.0 = slowest, 1.0 = fastest)")
        self.ui._print_slider_bar(self.config.dynamics.speed, 0, 1)

        speed, action = await self.ui.get_number(
            "Speed",
            min_value=0.0,
            max_value=1.0,
            default=self.config.dynamics.speed
        )

        if action == NavAction.CANCEL:
            return NavAction.CANCEL
        if action == NavAction.BACK:
            return NavAction.BACK

        self.config.dynamics.speed = speed if speed is not None else 0.5

        # Auto dynamic
        auto_dynamic, action = await self.ui.get_confirmation(
            "Enable auto-dynamic mode? (automatically enable palette cycling)",
            default=self.config.dynamics.auto_dynamic
        )

        if action == NavAction.CANCEL:
            return NavAction.CANCEL
        if action == NavAction.BACK:
            return NavAction.BACK

        self.config.dynamics.auto_dynamic = auto_dynamic

        # Global transition duration
        self.ui.print_info("\nGlobal transition duration (applies to all lights without individual settings)")

        duration_options = [
            SelectOption("None (use defaults)", None),
            SelectOption("Instant", 0),
            SelectOption("Fast (400ms)", 400),
            SelectOption("Medium (1s)", 1000),
            SelectOption("Slow (2s)", 2000),
            SelectOption("Very Slow (5s)", 5000),
            SelectOption("Gradual (30s)", 30000),
            SelectOption("Custom", "custom"),
        ]

        choice, action = await self.ui.select_one(
            "Global transition duration",
            duration_options,
            allow_skip=True
        )

        if action == NavAction.CONTINUE:
            if choice == "custom":
                ms, _ = await self.ui.get_number(
                    "Duration in milliseconds",
                    min_value=0,
                    max_value=3600000,  # 1 hour max
                    default=1000,
                    allow_float=False
                )
                self.config.dynamics.global_duration_ms = int(ms) if ms else None
            else:
                self.config.dynamics.global_duration_ms = choice

            # Apply global duration to lights without individual settings
            if self.config.dynamics.global_duration_ms is not None:
                for la in self.config.light_actions:
                    if la.dynamics_duration_ms is None:
                        la.dynamics_duration_ms = self.config.dynamics.global_duration_ms

        return NavAction.CONTINUE

    # =========================================================================
    # Section: Recall
    # =========================================================================

    async def _section_recall(self) -> NavAction:
        """Configure recall settings."""
        self.ui.print_section_header(
            "Recall Settings",
            step=5, total=6,
            description="Configure how the scene is activated"
        )

        # Recall action
        recall_options = [
            SelectOption(
                action.replace("_", " ").title(),
                action,
                description=SCENE_RECALL_DESCRIPTIONS.get(action, "")
            )
            for action in SCENE_RECALL_ACTIONS
        ]

        recall_action, action = await self.ui.select_one(
            "Default recall action",
            recall_options,
            default=self.config.recall.action
        )

        if action == NavAction.CANCEL:
            return NavAction.CANCEL
        if action == NavAction.BACK:
            return NavAction.BACK

        self.config.recall.action = recall_action or "active"

        # Recall duration
        duration_options = [
            SelectOption("Use scene defaults", None),
            SelectOption("Instant", 0),
            SelectOption("Fast (400ms)", 400),
            SelectOption("Medium (1s)", 1000),
            SelectOption("Slow (2s)", 2000),
            SelectOption("Custom", "custom"),
        ]

        choice, action = await self.ui.select_one(
            "Recall transition duration",
            duration_options
        )

        if action != NavAction.CONTINUE:
            return action

        if choice == "custom":
            ms, _ = await self.ui.get_number(
                "Duration in milliseconds",
                min_value=0,
                max_value=MAX_TRANSITION_MS,
                default=400,
                allow_float=False
            )
            self.config.recall.duration_ms = int(ms) if ms else None
        else:
            self.config.recall.duration_ms = choice

        # Brightness override
        override, action = await self.ui.get_confirmation(
            "Set brightness override when recalling?",
            default=False
        )

        if action == NavAction.CONTINUE and override:
            brightness, _ = await self.ui.get_number(
                "Override brightness",
                min_value=1,
                max_value=100,
                default=100,
                unit="%"
            )
            self.config.recall.brightness_override = brightness

        return NavAction.CONTINUE

    # =========================================================================
    # Section: Review
    # =========================================================================

    async def _section_review(self) -> NavAction:
        """Review and confirm scene creation."""
        self.ui.print_section_header(
            "Review & Create",
            step=6, total=6,
            description="Review your configuration"
        )

        # Summary
        enabled_lights = sum(1 for la in self.config.light_actions if la.enabled)

        self.ui.print_summary_panel(
            "Scene Summary",
            {
                "Name": self.config.name,
                "Target": f"{self.config.group_name} ({self.config.group_type})",
                "Lights": f"{enabled_lights} configured",
                "Palette": "Enabled" if self.config.palette.enabled else "Disabled",
                "Speed": f"{self.config.dynamics.speed:.1f}",
                "Auto Dynamic": "Yes" if self.config.dynamics.auto_dynamic else "No",
                "Recall Action": self.config.recall.action,
            }
        )

        # Options
        options = [
            SelectOption("Create Scene", "create", description="Save the scene", icon="✓"),
            SelectOption("Test All Settings", "test", description="Preview before saving", icon="▶"),
            SelectOption("Edit Metadata", "metadata", icon="📝"),
            SelectOption("Edit Light Actions", "actions", icon="💡"),
            SelectOption("Edit Palette", "palette", icon="🎨"),
            SelectOption("Edit Dynamics", "dynamics", icon="⚡"),
            SelectOption("Edit Recall", "recall", icon="▶"),
            SelectOption("Cancel", "cancel", icon="✗"),
        ]

        choice, action = await self.ui.select_one(
            "What would you like to do?",
            options,
            allow_back=True
        )

        if action == NavAction.CANCEL or choice == "cancel":
            return NavAction.CANCEL
        if action == NavAction.BACK:
            return NavAction.BACK

        if choice == "create":
            return NavAction.CONTINUE
        elif choice == "test":
            await self._test_light_actions()
            return await self._section_review()  # Stay in review
        else:
            # Jump to specific section
            section_map = {
                "metadata": 0,
                "actions": 1,
                "palette": 2,
                "dynamics": 3,
                "recall": 4,
            }
            if choice in section_map:
                self._current_section = section_map[choice]
                return NavAction.BACK  # Will be handled by main loop

        return NavAction.CONTINUE

    async def _create_scene(self) -> WizardResult:
        """Create the scene via API."""
        self.ui.print_info("Creating scene...")

        try:
            request = self.config.to_create_request()
            scene = await self.scene_manager.create_scene(request)

            self.ui.print_success(f"Created scene '{self.config.name}'")

            # Offer to activate immediately
            activate, _ = await self.ui.get_confirmation(
                "Activate the scene now?",
                default=True
            )

            if activate:
                recall_request = RecallSceneRequest(
                    scene_id=scene.id,
                    action=self.config.recall.action,
                    duration_ms=self.config.recall.duration_ms,
                    brightness=self.config.recall.brightness_override,
                )
                await self.scene_manager.recall_scene(
                    scene.id,
                    action=recall_request.action,
                    duration_ms=recall_request.duration_ms
                )
                self.ui.print_success("Scene activated!")

            return WizardResult(
                success=True,
                message=f"Created scene '{self.config.name}'",
                data=scene
            )

        except Exception as e:
            self.ui.print_error(f"Failed to create scene: {e}")
            return WizardResult(success=False, message=str(e))

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _format_duration(self, ms: Optional[int]) -> str:
        """Format duration in human-readable form."""
        if ms is None:
            return "Default"
        if ms == 0:
            return "Instant"
        if ms < 1000:
            return f"{ms}ms"
        if ms < 60000:
            return f"{ms/1000:.1f}s"
        if ms < 3600000:
            return f"{ms/60000:.1f}m"
        # Handle hour+ durations (max ~109 minutes)
        hours = ms / 3600000
        return f"{hours:.1f}h"
