"""
Scene Templates

Pre-configured mood-based templates for quick scene creation.
"""

from .scene_templates import (
    MoodTemplate,
    MOOD_TEMPLATES,
    get_template_by_id,
    get_all_templates,
    get_template_choices,
    get_icon_for_template,
)

__all__ = [
    "MoodTemplate",
    "MOOD_TEMPLATES",
    "get_template_by_id",
    "get_all_templates",
    "get_template_choices",
    "get_icon_for_template",
]
