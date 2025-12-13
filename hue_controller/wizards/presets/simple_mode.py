"""
Simple Mode Presets

Pre-configured scene presets using plain English names and descriptions.
No technical values are exposed to users in Simple Mode.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LightingConfig:
    """Configuration for a lighting preset."""
    on: bool = True
    brightness: Optional[float] = None  # 0-100 percentage
    color_mode: str = "temperature"  # temperature, color, effect

    # Color temperature (mirek)
    color_temperature_mirek: Optional[int] = None

    # XY color coordinates
    color_xy: Optional[tuple[float, float]] = None

    # Effect name
    effect: Optional[str] = None

    # Transition time in milliseconds
    transition_ms: Optional[int] = None

    # For dynamic scenes
    auto_dynamic: bool = False
    speed: float = 0.5
    palette_colors: list[tuple[float, float]] = field(default_factory=list)


@dataclass
class SimpleScenePreset:
    """
    A Simple Mode preset for quick scene creation.

    Uses friendly names and descriptions with no technical jargon.
    """
    id: str
    name: str
    description: str
    icon: str
    category: str
    lighting: LightingConfig

    def __post_init__(self):
        """Ensure category is valid."""
        valid_categories = ["everyday", "relax", "focus", "entertainment", "special"]
        if self.category not in valid_categories:
            self.category = "everyday"


# Pre-defined presets for Simple Mode
SIMPLE_SCENE_PRESETS: list[SimpleScenePreset] = [
    # === Everyday ===
    SimpleScenePreset(
        id="bright_energizing",
        name="Bright & Energizing",
        description="Full brightness, cool daylight - perfect for mornings or active tasks",
        icon="☀️",
        category="everyday",
        lighting=LightingConfig(
            on=True,
            brightness=100.0,
            color_mode="temperature",
            color_temperature_mirek=153,  # 6500K cool daylight
            transition_ms=400,
        ),
    ),
    SimpleScenePreset(
        id="natural_daylight",
        name="Natural Daylight",
        description="Bright and balanced - good for daytime activities",
        icon="🌤️",
        category="everyday",
        lighting=LightingConfig(
            on=True,
            brightness=85.0,
            color_mode="temperature",
            color_temperature_mirek=200,  # 5000K
            transition_ms=400,
        ),
    ),
    SimpleScenePreset(
        id="soft_white",
        name="Soft White",
        description="Comfortable everyday lighting - not too bright, not too dim",
        icon="💡",
        category="everyday",
        lighting=LightingConfig(
            on=True,
            brightness=70.0,
            color_mode="temperature",
            color_temperature_mirek=333,  # 3000K
            transition_ms=400,
        ),
    ),

    # === Relax ===
    SimpleScenePreset(
        id="warm_cozy",
        name="Warm & Cozy",
        description="Relaxing warm glow - like incandescent bulbs",
        icon="🔥",
        category="relax",
        lighting=LightingConfig(
            on=True,
            brightness=50.0,
            color_mode="temperature",
            color_temperature_mirek=370,  # 2700K warm white
            transition_ms=1000,
        ),
    ),
    SimpleScenePreset(
        id="dim_relaxing",
        name="Dim & Relaxing",
        description="Low, warm light for winding down",
        icon="🌙",
        category="relax",
        lighting=LightingConfig(
            on=True,
            brightness=30.0,
            color_mode="temperature",
            color_temperature_mirek=400,  # ~2500K
            transition_ms=1500,
        ),
    ),
    SimpleScenePreset(
        id="candlelight",
        name="Candlelight",
        description="Very warm, flickering ambiance - romantic or intimate",
        icon="🕯️",
        category="relax",
        lighting=LightingConfig(
            on=True,
            brightness=40.0,
            color_mode="effect",
            effect="candle",
            color_temperature_mirek=500,  # 2000K very warm
            transition_ms=2000,
        ),
    ),
    SimpleScenePreset(
        id="nightlight",
        name="Nightlight",
        description="Very dim for navigation without disturbing sleep",
        icon="🌜",
        category="relax",
        lighting=LightingConfig(
            on=True,
            brightness=5.0,
            color_mode="temperature",
            color_temperature_mirek=500,  # Very warm
            transition_ms=2000,
        ),
    ),

    # === Focus ===
    SimpleScenePreset(
        id="focus_mode",
        name="Focus Mode",
        description="Bright, cool light for concentration and productivity",
        icon="🎯",
        category="focus",
        lighting=LightingConfig(
            on=True,
            brightness=80.0,
            color_mode="temperature",
            color_temperature_mirek=182,  # 5500K daylight
            transition_ms=400,
        ),
    ),
    SimpleScenePreset(
        id="reading_light",
        name="Reading Light",
        description="Good visibility without eye strain",
        icon="📖",
        category="focus",
        lighting=LightingConfig(
            on=True,
            brightness=65.0,
            color_mode="temperature",
            color_temperature_mirek=250,  # 4000K neutral
            transition_ms=400,
        ),
    ),

    # === Entertainment ===
    SimpleScenePreset(
        id="movie_time",
        name="Movie Time",
        description="Dim, warm bias lighting for watching movies",
        icon="🎬",
        category="entertainment",
        lighting=LightingConfig(
            on=True,
            brightness=15.0,
            color_mode="temperature",
            color_temperature_mirek=370,  # Warm
            transition_ms=1500,
        ),
    ),
    SimpleScenePreset(
        id="gaming",
        name="Gaming",
        description="Dynamic colors that shift over time",
        icon="🎮",
        category="entertainment",
        lighting=LightingConfig(
            on=True,
            brightness=60.0,
            color_mode="color",
            color_xy=(0.15, 0.10),  # Purple-ish start
            auto_dynamic=True,
            speed=0.5,
            palette_colors=[
                (0.15, 0.10),  # Purple
                (0.20, 0.06),  # Blue
                (0.65, 0.32),  # Red
                (0.35, 0.55),  # Green
            ],
            transition_ms=400,
        ),
    ),
    SimpleScenePreset(
        id="party",
        name="Party Colors",
        description="Vibrant, shifting colors for celebrations",
        icon="🎉",
        category="entertainment",
        lighting=LightingConfig(
            on=True,
            brightness=75.0,
            color_mode="color",
            color_xy=(0.65, 0.32),  # Red start
            auto_dynamic=True,
            speed=0.7,
            palette_colors=[
                (0.65, 0.32),  # Red
                (0.52, 0.43),  # Orange
                (0.42, 0.52),  # Yellow
                (0.35, 0.55),  # Green
                (0.15, 0.10),  # Purple
            ],
            transition_ms=300,
        ),
    ),

    # === Special ===
    SimpleScenePreset(
        id="romantic",
        name="Romantic",
        description="Soft, warm ambiance with gentle pink tones",
        icon="💕",
        category="special",
        lighting=LightingConfig(
            on=True,
            brightness=35.0,
            color_mode="color",
            color_xy=(0.45, 0.28),  # Warm pink
            transition_ms=2000,
        ),
    ),
    SimpleScenePreset(
        id="sunset",
        name="Sunset Glow",
        description="Warm orange and pink tones like a sunset",
        icon="🌅",
        category="special",
        lighting=LightingConfig(
            on=True,
            brightness=55.0,
            color_mode="color",
            color_xy=(0.55, 0.38),  # Orange
            auto_dynamic=True,
            speed=0.2,
            palette_colors=[
                (0.55, 0.38),  # Orange
                (0.58, 0.35),  # Deep orange
                (0.50, 0.30),  # Pinkish
            ],
            transition_ms=2000,
        ),
    ),
    SimpleScenePreset(
        id="ocean",
        name="Ocean Waves",
        description="Calm, flowing blue tones",
        icon="🌊",
        category="special",
        lighting=LightingConfig(
            on=True,
            brightness=45.0,
            color_mode="color",
            color_xy=(0.15, 0.12),  # Blue
            auto_dynamic=True,
            speed=0.3,
            palette_colors=[
                (0.15, 0.12),  # Blue
                (0.17, 0.20),  # Teal
                (0.20, 0.25),  # Cyan
            ],
            transition_ms=2000,
        ),
    ),
    SimpleScenePreset(
        id="forest",
        name="Forest",
        description="Natural greens and earthy tones",
        icon="🌲",
        category="special",
        lighting=LightingConfig(
            on=True,
            brightness=50.0,
            color_mode="color",
            color_xy=(0.35, 0.55),  # Green
            auto_dynamic=True,
            speed=0.25,
            palette_colors=[
                (0.35, 0.55),  # Green
                (0.40, 0.50),  # Yellow-green
                (0.42, 0.42),  # Earthy
            ],
            transition_ms=2000,
        ),
    ),

    # === Off state ===
    SimpleScenePreset(
        id="lights_off",
        name="Lights Off",
        description="Turn all lights off",
        icon="⬛",
        category="everyday",
        lighting=LightingConfig(
            on=False,
            transition_ms=1000,
        ),
    ),
]


def get_preset_by_name(name: str) -> Optional[SimpleScenePreset]:
    """
    Find a preset by name (case-insensitive).

    Args:
        name: Preset name to search for

    Returns:
        SimpleScenePreset if found, None otherwise
    """
    name_lower = name.lower()
    for preset in SIMPLE_SCENE_PRESETS:
        if preset.name.lower() == name_lower:
            return preset
    return None


def get_preset_by_id(preset_id: str) -> Optional[SimpleScenePreset]:
    """
    Find a preset by ID.

    Args:
        preset_id: Preset ID to search for

    Returns:
        SimpleScenePreset if found, None otherwise
    """
    for preset in SIMPLE_SCENE_PRESETS:
        if preset.id == preset_id:
            return preset
    return None


def get_presets_by_category(category: str) -> list[SimpleScenePreset]:
    """
    Get all presets in a category.

    Args:
        category: Category name (everyday, relax, focus, entertainment, special)

    Returns:
        List of presets in that category
    """
    return [p for p in SIMPLE_SCENE_PRESETS if p.category == category]


def get_all_categories() -> list[str]:
    """Get list of all preset categories."""
    return ["everyday", "relax", "focus", "entertainment", "special"]


def get_category_label(category: str) -> str:
    """Get human-readable label for a category."""
    labels = {
        "everyday": "Everyday",
        "relax": "Relax & Unwind",
        "focus": "Focus & Work",
        "entertainment": "Entertainment",
        "special": "Special Moods",
    }
    return labels.get(category, category.title())
