"""
Mood-based Scene Templates

Pre-configured templates covering the most common lighting scenarios.
Each template defines settings that can be applied to all lights in a room/zone.
"""

from dataclasses import dataclass, field
from typing import Optional, Literal


@dataclass
class MoodTemplate:
    """A mood-based scene template."""

    id: str
    name: str
    icon: str
    description: str
    category: str  # "daily", "relax", "entertainment", "utility"

    # Light settings
    on: bool = True
    brightness: float = 100.0
    color_mode: Literal["temperature", "color", "effect"] = "temperature"
    color_temp_kelvin: int = 4000
    color_xy: Optional[tuple[float, float]] = None
    effect: Optional[str] = None

    # Transition
    transition_ms: int = 400

    # Dynamic features (optional)
    palette_colors: Optional[list[tuple[float, float]]] = None
    speed: float = 0.5
    auto_dynamic: bool = False

    def get_mirek(self) -> Optional[int]:
        """Convert Kelvin to mirek (Hue API uses mirek)."""
        if self.color_temp_kelvin:
            return int(1_000_000 / self.color_temp_kelvin)
        return None


# The 8 essential mood templates covering 90% of use cases
MOOD_TEMPLATES: list[MoodTemplate] = [
    # Daily / Utility
    MoodTemplate(
        id="bright",
        name="Bright",
        icon="sun",
        description="Full brightness, neutral white - for general use",
        category="daily",
        brightness=100.0,
        color_temp_kelvin=4000,
        color_mode="temperature",
    ),

    MoodTemplate(
        id="energize",
        name="Energize",
        icon="zap",
        description="Cool bright light for focus and alertness",
        category="daily",
        brightness=100.0,
        color_temp_kelvin=5500,
        color_mode="temperature",
    ),

    # Relaxation
    MoodTemplate(
        id="cozy",
        name="Cozy Evening",
        icon="sunset",
        description="Warm dim light for relaxation",
        category="relax",
        brightness=50.0,
        color_temp_kelvin=2700,
        color_mode="temperature",
        transition_ms=1000,
    ),

    MoodTemplate(
        id="candle",
        name="Candlelight",
        icon="flame",
        description="Very warm with flickering candle effect",
        category="relax",
        brightness=40.0,
        color_temp_kelvin=2200,
        color_mode="effect",
        effect="candle",
        transition_ms=1000,
    ),

    MoodTemplate(
        id="nightlight",
        name="Nightlight",
        icon="moon",
        description="Minimal soft glow for nighttime",
        category="relax",
        brightness=5.0,
        color_temp_kelvin=2200,
        color_mode="temperature",
        transition_ms=2000,
    ),

    # Entertainment
    MoodTemplate(
        id="movie",
        name="Movie Time",
        icon="film",
        description="Dark ambient lighting for viewing",
        category="entertainment",
        brightness=20.0,
        color_temp_kelvin=2700,
        color_mode="temperature",
        transition_ms=2000,
    ),

    MoodTemplate(
        id="party",
        name="Party",
        icon="sparkles",
        description="Dynamic color cycling for parties",
        category="entertainment",
        brightness=80.0,
        color_mode="color",
        # Rainbow palette: red, orange, yellow, green, blue, purple
        palette_colors=[
            (0.675, 0.322),  # Red
            (0.588, 0.393),  # Orange
            (0.461, 0.469),  # Yellow
            (0.214, 0.709),  # Green
            (0.167, 0.040),  # Blue
            (0.292, 0.132),  # Purple
        ],
        speed=0.5,
        auto_dynamic=True,
        transition_ms=500,
    ),

    # Utility
    MoodTemplate(
        id="off",
        name="All Off",
        icon="circle-off",
        description="Turn all lights off",
        category="utility",
        on=False,
        brightness=0.0,
    ),
]


def get_template_by_id(template_id: str) -> Optional[MoodTemplate]:
    """Get a template by its ID."""
    for template in MOOD_TEMPLATES:
        if template.id == template_id:
            return template
    return None


def get_all_templates() -> list[MoodTemplate]:
    """Get all available templates."""
    return MOOD_TEMPLATES.copy()


def get_templates_by_category(category: str) -> list[MoodTemplate]:
    """Get templates filtered by category."""
    return [t for t in MOOD_TEMPLATES if t.category == category]


def get_template_choices() -> dict[str, list[MoodTemplate]]:
    """
    Get templates organized by category for menu display.

    Returns:
        Dict mapping category display names to template lists
    """
    categories = {
        "Daily": get_templates_by_category("daily"),
        "Relaxation": get_templates_by_category("relax"),
        "Entertainment": get_templates_by_category("entertainment"),
        "Utility": get_templates_by_category("utility"),
    }
    return {k: v for k, v in categories.items() if v}


# Icon mapping for display (using common unicode/emoji alternatives)
ICON_MAP = {
    "sun": "\u2600",           # sun
    "zap": "\u26a1",           # lightning bolt
    "sunset": "\U0001F305",    # sunrise over mountains (close to sunset)
    "flame": "\U0001F525",     # fire
    "moon": "\U0001F319",      # crescent moon
    "film": "\U0001F3AC",      # clapper board
    "sparkles": "\U00002728",  # sparkles
    "circle-off": "\u25CB",    # white circle (representing off)
}


def get_icon_for_template(template: MoodTemplate) -> str:
    """Get the display icon for a template."""
    return ICON_MAP.get(template.icon, "\u2022")  # Default to bullet


# Extended templates for power users (can be added to MOOD_TEMPLATES if needed)
EXTENDED_TEMPLATES: list[MoodTemplate] = [
    MoodTemplate(
        id="sunrise",
        name="Gentle Sunrise",
        icon="sun",
        description="Simulated sunrise, gradual warm light",
        category="daily",
        brightness=80.0,
        color_temp_kelvin=2700,
        color_mode="temperature",
        transition_ms=60000,  # 1 minute transition
    ),

    MoodTemplate(
        id="reading",
        name="Reading Light",
        icon="book",
        description="Warm neutral light, easy on the eyes",
        category="daily",
        brightness=70.0,
        color_temp_kelvin=3000,
        color_mode="temperature",
    ),

    MoodTemplate(
        id="concentrate",
        name="Concentrate",
        icon="target",
        description="Cool white for deep focus work",
        category="daily",
        brightness=90.0,
        color_temp_kelvin=5000,
        color_mode="temperature",
    ),

    MoodTemplate(
        id="romance",
        name="Romance",
        icon="heart",
        description="Deep warm red-orange ambiance",
        category="relax",
        brightness=30.0,
        color_mode="color",
        color_xy=(0.6, 0.35),  # Warm red-orange
        transition_ms=2000,
    ),

    MoodTemplate(
        id="ocean",
        name="Ocean",
        icon="waves",
        description="Calm blue tones like the sea",
        category="relax",
        brightness=50.0,
        color_mode="color",
        color_xy=(0.17, 0.15),  # Deep blue
        transition_ms=1500,
    ),

    MoodTemplate(
        id="forest",
        name="Forest",
        icon="tree",
        description="Natural green tones",
        category="relax",
        brightness=45.0,
        color_mode="color",
        color_xy=(0.25, 0.55),  # Forest green
        transition_ms=1500,
    ),

    MoodTemplate(
        id="fire",
        name="Fireplace",
        icon="flame",
        description="Warm fire glow effect",
        category="relax",
        brightness=60.0,
        color_temp_kelvin=2200,
        color_mode="effect",
        effect="fire",
        transition_ms=1000,
    ),
]
