"""
Hue Controller Constants

Contains enumerations and constant values for Hue API v2.
"""

from typing import Final

# Room archetypes supported by Hue API v2
ROOM_ARCHETYPES: Final[list[str]] = [
    "living_room",
    "kitchen",
    "dining",
    "bedroom",
    "kids_bedroom",
    "bathroom",
    "nursery",
    "recreation",
    "office",
    "gym",
    "hallway",
    "toilet",
    "front_door",
    "garage",
    "terrace",
    "garden",
    "driveway",
    "carport",
    "home",
    "downstairs",
    "upstairs",
    "top_floor",
    "attic",
    "guest_room",
    "staircase",
    "lounge",
    "man_cave",
    "computer",
    "studio",
    "music",
    "tv",
    "reading",
    "closet",
    "storage",
    "laundry_room",
    "balcony",
    "porch",
    "barbecue",
    "pool",
    "other",
]

# Human-readable descriptions for room archetypes
ROOM_ARCHETYPE_DESCRIPTIONS: Final[dict[str, str]] = {
    "living_room": "Living Room",
    "kitchen": "Kitchen",
    "dining": "Dining Room",
    "bedroom": "Bedroom",
    "kids_bedroom": "Kids Bedroom",
    "bathroom": "Bathroom",
    "nursery": "Nursery",
    "recreation": "Recreation Room",
    "office": "Office",
    "gym": "Gym",
    "hallway": "Hallway",
    "toilet": "Toilet",
    "front_door": "Front Door",
    "garage": "Garage",
    "terrace": "Terrace",
    "garden": "Garden",
    "driveway": "Driveway",
    "carport": "Carport",
    "home": "Home",
    "downstairs": "Downstairs",
    "upstairs": "Upstairs",
    "top_floor": "Top Floor",
    "attic": "Attic",
    "guest_room": "Guest Room",
    "staircase": "Staircase",
    "lounge": "Lounge",
    "man_cave": "Man Cave",
    "computer": "Computer Room",
    "studio": "Studio",
    "music": "Music Room",
    "tv": "TV Room",
    "reading": "Reading Room",
    "closet": "Closet",
    "storage": "Storage",
    "laundry_room": "Laundry Room",
    "balcony": "Balcony",
    "porch": "Porch",
    "barbecue": "Barbecue Area",
    "pool": "Pool Area",
    "other": "Other",
}

# Light effects supported by Hue API v2
EFFECT_TYPES: Final[list[str]] = [
    "no_effect",
    "candle",
    "fire",
    "prism",
    "sparkle",
    "opal",
    "glisten",
    "underwater",
    "cosmos",
    "sunbeam",
    "enchant",
]

# Human-readable effect descriptions
EFFECT_DESCRIPTIONS: Final[dict[str, str]] = {
    "no_effect": "No effect (static light)",
    "candle": "Flickering candle effect",
    "fire": "Warm fire glow effect",
    "prism": "Shifting rainbow colors",
    "sparkle": "Twinkling sparkle effect",
    "opal": "Soft shifting opal colors",
    "glisten": "Gentle glistening effect",
    "underwater": "Blue underwater shimmer",
    "cosmos": "Deep space colors",
    "sunbeam": "Warm sunbeam glow",
    "enchant": "Magical enchanting colors",
}

# Timed effects for sunrise/sunset simulation
TIMED_EFFECT_TYPES: Final[list[str]] = [
    "no_effect",
    "sunrise",
    "sunset",
]

# Gradient modes for gradient-capable lights
GRADIENT_MODES: Final[list[str]] = [
    "interpolated_palette",
    "interpolated_palette_mirrored",
    "random_pixelated",
    "segmented",
]

# Gradient mode descriptions
GRADIENT_MODE_DESCRIPTIONS: Final[dict[str, str]] = {
    "interpolated_palette": "Smooth gradient between colors",
    "interpolated_palette_mirrored": "Mirrored gradient (symmetric)",
    "random_pixelated": "Random color pixels",
    "segmented": "Distinct color segments",
}

# Signal types for light signaling/identification
SIGNAL_TYPES: Final[list[str]] = [
    "no_signal",
    "on_off",
    "on_off_color",
    "alternating",
]

# Signal type descriptions
SIGNAL_DESCRIPTIONS: Final[dict[str, str]] = {
    "no_signal": "No signaling",
    "on_off": "Flash on/off",
    "on_off_color": "Flash with color",
    "alternating": "Alternate between colors",
}

# Entertainment configuration types
ENTERTAINMENT_TYPES: Final[list[str]] = [
    "screen",
    "monitor",
    "music",
    "3dspace",
    "other",
]

# Entertainment type descriptions
ENTERTAINMENT_TYPE_DESCRIPTIONS: Final[dict[str, str]] = {
    "screen": "TV or projection screen sync",
    "monitor": "Computer monitor sync",
    "music": "Music visualization",
    "3dspace": "3D spatial arrangement",
    "other": "Other configuration",
}

# Scene recall actions
SCENE_RECALL_ACTIONS: Final[list[str]] = [
    "active",
    "dynamic_palette",
    "static",
]

# Scene recall action descriptions
SCENE_RECALL_DESCRIPTIONS: Final[dict[str, str]] = {
    "active": "Activate scene normally",
    "dynamic_palette": "Activate with dynamic color cycling",
    "static": "Activate without transitions",
}

# Default transition times (in milliseconds)
DEFAULT_TRANSITION_MS: Final[int] = 400
SLOW_TRANSITION_MS: Final[int] = 2000
INSTANT_TRANSITION_MS: Final[int] = 0
# API maximum: 65535 deciseconds (100ms units) = 6,553,500ms (~109 minutes)
MAX_TRANSITION_MS: Final[int] = 6_553_500

# =============================================================================
# Timed Effect Duration Presets
# =============================================================================

# API maximum for timed effects (sunrise/sunset): 6 hours
TIMED_EFFECT_MAX_MS: Final[int] = 21_600_000  # 6 hours in milliseconds

# Named duration presets for timed effects
TIMED_EFFECT_DURATION_PRESETS: Final[dict[str, int]] = {
    "max": 21_600_000,      # 6 hours (API maximum)
    "long": 7_200_000,      # 2 hours
    "medium": 1_800_000,    # 30 minutes (default)
    "short": 600_000,       # 10 minutes
    "quick": 300_000,       # 5 minutes
}

# Human-readable descriptions for duration presets
DURATION_PRESET_DESCRIPTIONS: Final[dict[str, str]] = {
    "max": "6 hours (maximum)",
    "long": "2 hours",
    "medium": "30 minutes",
    "short": "10 minutes",
    "quick": "5 minutes",
}

# Rate limiting defaults
LIGHT_RATE_LIMIT: Final[float] = 10.0  # requests per second for individual lights
GROUP_RATE_LIMIT: Final[float] = 1.0   # requests per second for groups

# Color temperature ranges (in mirek)
MIREK_MIN: Final[int] = 153   # ~6500K (cool daylight)
MIREK_MAX: Final[int] = 500   # ~2000K (very warm)
MIREK_WARM: Final[int] = 370  # ~2700K (warm white)
MIREK_NEUTRAL: Final[int] = 250  # ~4000K (neutral)
MIREK_COOL: Final[int] = 182  # ~5500K (cool white)

# =============================================================================
# White Color Temperature Presets
# =============================================================================

# Kelvin-based naming convention (e.g., "2700k" -> mirek value)
TEMPERATURE_BY_KELVIN: Final[dict[str, int]] = {
    "2000k": 500,   # Very warm (candlelight)
    "2700k": 370,   # Warm white (incandescent)
    "3000k": 333,   # Soft white
    "4000k": 250,   # Neutral white
    "5000k": 200,   # Cool white
    "5500k": 182,   # Daylight
    "6500k": 153,   # Bright daylight (coolest)
}

# Descriptive naming convention (maps to same mirek values)
TEMPERATURE_BY_NAME: Final[dict[str, int]] = {
    "candlelight": 500,    # 2000K - Very warm, flickering candle
    "warm": 370,           # 2700K - Traditional incandescent
    "soft": 333,           # 3000K - Soft white
    "neutral": 250,        # 4000K - Neutral white
    "cool": 200,           # 5000K - Cool white
    "daylight": 182,       # 5500K - Daylight
    "bright": 153,         # 6500K - Bright daylight (coolest)
}

# Human-readable descriptions for each temperature preset
TEMPERATURE_DESCRIPTIONS: Final[dict[str, str]] = {
    "candlelight": "2000K - Very warm, like candlelight",
    "warm": "2700K - Warm white, like incandescent bulbs",
    "soft": "3000K - Soft white, slightly warmer than neutral",
    "neutral": "4000K - Neutral white, balanced",
    "cool": "5000K - Cool white, slightly blue tint",
    "daylight": "5500K - Daylight, natural outdoor light",
    "bright": "6500K - Bright daylight, cool and energizing",
}

# Brightness range
BRIGHTNESS_MIN: Final[float] = 0.0
BRIGHTNESS_MAX: Final[float] = 100.0

# Gradient constraints
GRADIENT_MIN_POINTS: Final[int] = 2
GRADIENT_MAX_POINTS: Final[int] = 5

# =============================================================================
# Simple Mode Labels
# =============================================================================
#
# Friendly labels for technical terms used in Simple Mode.
# These map API/technical terminology to user-friendly alternatives.

SIMPLE_MODE_LABELS: Final[dict[str, str]] = {
    # Technical term -> Simple mode label
    "mirek": "warmth",
    "color_temperature": "warmth",
    "brightness": "intensity",
    "dimming": "intensity",
    "xy": "color",
    "xy_color": "color",
    "color_xy": "color",
    "gamut": "color range",
    "transition": "fade time",
    "transition_ms": "fade time",
    "dynamics": "animation",
    "dynamics_duration": "animation speed",
    "signaling": "flashing",
    "gradient": "color blend",
    "gradient_mode": "blend style",
    "palette": "color set",
    "auto_dynamic": "color cycling",
    "speed": "animation speed",
    "recall": "activate",
    "grouped_light": "room control",
    "archetype": "type",
    "effect": "effect",
    "timed_effect": "wake-up light",
}

# Extended descriptions with practical examples for all constant dictionaries
EFFECT_DESCRIPTIONS_EXTENDED: Final[dict[str, str]] = {
    "no_effect": "No effect (static light). Example: Regular lighting for everyday use.",
    "candle": "Flickering candle effect. Example: Romantic dinners, meditation, cozy evenings.",
    "fire": "Warm fire glow effect. Example: Fireplace ambiance, autumn vibes.",
    "prism": "Shifting rainbow colors. Example: Party mode, kids' rooms.",
    "sparkle": "Twinkling sparkle effect. Example: Holiday decorations, festive occasions.",
    "opal": "Soft shifting opal colors. Example: Relaxation, gentle ambient lighting.",
    "glisten": "Gentle glistening effect. Example: Spa-like atmosphere, calming spaces.",
    "underwater": "Blue underwater shimmer. Example: Bathrooms, pool areas, aquarium feel.",
    "cosmos": "Deep space colors. Example: Home theaters, stargazing ambiance.",
    "sunbeam": "Warm sunbeam glow. Example: Morning wake-up, energizing spaces.",
    "enchant": "Magical enchanting colors. Example: Fairy tale themes, children's rooms.",
}

TEMPERATURE_DESCRIPTIONS_EXTENDED: Final[dict[str, str]] = {
    "candlelight": "2000K (500 mirek) - Very warm, like candlelight. Example: Intimate dinners, evening relaxation.",
    "warm": "2700K (370 mirek) - Warm white, like incandescent bulbs. Example: Living rooms, bedrooms.",
    "soft": "3000K (333 mirek) - Soft white, slightly warmer than neutral. Example: Hallways, general use.",
    "neutral": "4000K (250 mirek) - Neutral white, balanced. Example: Kitchens, offices, task lighting.",
    "cool": "5000K (200 mirek) - Cool white, slightly blue tint. Example: Garages, workspaces.",
    "daylight": "5500K (182 mirek) - Daylight, natural outdoor light. Example: Art studios, makeup areas.",
    "bright": "6500K (153 mirek) - Bright daylight, cool and energizing. Example: Morning routines, focus work.",
}
