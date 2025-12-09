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

# Rate limiting defaults
LIGHT_RATE_LIMIT: Final[float] = 10.0  # requests per second for individual lights
GROUP_RATE_LIMIT: Final[float] = 1.0   # requests per second for groups

# Color temperature ranges (in mirek)
MIREK_MIN: Final[int] = 153   # ~6500K (cool daylight)
MIREK_MAX: Final[int] = 500   # ~2000K (very warm)
MIREK_WARM: Final[int] = 370  # ~2700K (warm white)
MIREK_NEUTRAL: Final[int] = 250  # ~4000K (neutral)
MIREK_COOL: Final[int] = 182  # ~5500K (cool white)

# Brightness range
BRIGHTNESS_MIN: Final[float] = 0.0
BRIGHTNESS_MAX: Final[float] = 100.0

# Gradient constraints
GRADIENT_MIN_POINTS: Final[int] = 2
GRADIENT_MAX_POINTS: Final[int] = 5
