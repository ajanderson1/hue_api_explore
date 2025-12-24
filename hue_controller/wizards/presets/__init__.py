"""
Wizard Presets

Pre-configured lighting configurations for Simple and Standard modes.
"""

from .simple_mode import (
    SimpleScenePreset,
    SIMPLE_SCENE_PRESETS,
    get_preset_by_name,
    get_preset_by_id,
    get_presets_by_category,
)

from .standard_mode import (
    StandardPreset,
    STANDARD_PRESETS,
)

__all__ = [
    "SimpleScenePreset",
    "SIMPLE_SCENE_PRESETS",
    "get_preset_by_name",
    "get_preset_by_id",
    "get_presets_by_category",
    "StandardPreset",
    "STANDARD_PRESETS",
]
