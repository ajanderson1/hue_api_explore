"""
Standard Mode Presets

Extends Simple Mode presets with technical details and explanations.
Shows values like color temperature in Kelvin and mirek, brightness percentages,
and other parameters with helpful context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .simple_mode import SimpleScenePreset, LightingConfig, SIMPLE_SCENE_PRESETS


@dataclass
class TechnicalDetails:
    """Technical parameter details for Standard Mode display."""
    color_temperature_kelvin: Optional[int] = None
    color_temperature_mirek: Optional[int] = None
    brightness_percent: Optional[float] = None
    transition_seconds: Optional[float] = None
    effect_name: Optional[str] = None
    color_description: Optional[str] = None
    dynamic_info: Optional[str] = None


@dataclass
class StandardPreset:
    """
    Standard Mode preset with technical annotations.

    Extends SimpleScenePreset with technical details visible to user.
    """
    base: SimpleScenePreset
    technical: TechnicalDetails
    technical_description: str  # Brief technical summary

    @property
    def id(self) -> str:
        return self.base.id

    @property
    def name(self) -> str:
        return self.base.name

    @property
    def icon(self) -> str:
        return self.base.icon

    @property
    def category(self) -> str:
        return self.base.category

    @property
    def lighting(self) -> LightingConfig:
        return self.base.lighting

    @property
    def description(self) -> str:
        """Combined description with technical details."""
        return f"{self.base.description}\n[dim]{self.technical_description}[/dim]"

    @property
    def short_technical(self) -> str:
        """Short technical summary for menu display."""
        parts = []
        if self.technical.brightness_percent is not None:
            parts.append(f"{int(self.technical.brightness_percent)}%")
        if self.technical.color_temperature_kelvin is not None:
            parts.append(f"{self.technical.color_temperature_kelvin}K")
        if self.technical.effect_name:
            parts.append(self.technical.effect_name)
        if self.technical.color_description:
            parts.append(self.technical.color_description)
        return " · ".join(parts) if parts else ""


def _mirek_to_kelvin(mirek: int) -> int:
    """Convert mirek to approximate Kelvin."""
    return round(1_000_000 / mirek)


def _create_technical_details(lighting: LightingConfig) -> TechnicalDetails:
    """Create technical details from a lighting config."""
    details = TechnicalDetails()

    if lighting.brightness is not None:
        details.brightness_percent = lighting.brightness

    if lighting.color_temperature_mirek is not None:
        details.color_temperature_mirek = lighting.color_temperature_mirek
        details.color_temperature_kelvin = _mirek_to_kelvin(lighting.color_temperature_mirek)

    if lighting.transition_ms is not None:
        details.transition_seconds = lighting.transition_ms / 1000

    if lighting.effect:
        details.effect_name = lighting.effect

    if lighting.color_xy:
        x, y = lighting.color_xy
        # Simple color description based on xy
        if x > 0.5 and y > 0.3:
            details.color_description = "warm colors"
        elif x < 0.25 and y < 0.2:
            details.color_description = "cool blues/purples"
        elif y > 0.4:
            details.color_description = "greens/yellows"
        else:
            details.color_description = f"xy({x:.2f}, {y:.2f})"

    if lighting.auto_dynamic:
        details.dynamic_info = f"Dynamic, speed {lighting.speed:.1f}"

    return details


def _create_technical_description(lighting: LightingConfig) -> str:
    """Create a technical description string."""
    parts = []

    if not lighting.on:
        return "Turns lights off with fade"

    if lighting.brightness is not None:
        parts.append(f"{int(lighting.brightness)}% brightness")

    if lighting.color_temperature_mirek is not None:
        kelvin = _mirek_to_kelvin(lighting.color_temperature_mirek)
        parts.append(f"{kelvin}K ({lighting.color_temperature_mirek} mirek)")

    if lighting.effect:
        parts.append(f"'{lighting.effect}' effect")

    if lighting.color_xy and not lighting.effect:
        x, y = lighting.color_xy
        parts.append(f"color xy({x:.2f}, {y:.2f})")

    if lighting.auto_dynamic:
        parts.append(f"dynamic cycling at {lighting.speed:.1f} speed")

    if lighting.transition_ms:
        secs = lighting.transition_ms / 1000
        if secs >= 1:
            parts.append(f"{secs:.1f}s transition")
        else:
            parts.append(f"{lighting.transition_ms}ms transition")

    return "Technical: " + ", ".join(parts) if parts else ""


def _create_standard_preset(base: SimpleScenePreset) -> StandardPreset:
    """Create a StandardPreset from a SimpleScenePreset."""
    return StandardPreset(
        base=base,
        technical=_create_technical_details(base.lighting),
        technical_description=_create_technical_description(base.lighting),
    )


# Build Standard Mode presets from Simple Mode presets
STANDARD_PRESETS: list[StandardPreset] = [
    _create_standard_preset(preset) for preset in SIMPLE_SCENE_PRESETS
]


def get_standard_preset_by_id(preset_id: str) -> Optional[StandardPreset]:
    """
    Find a standard preset by ID.

    Args:
        preset_id: Preset ID to search for

    Returns:
        StandardPreset if found, None otherwise
    """
    for preset in STANDARD_PRESETS:
        if preset.id == preset_id:
            return preset
    return None


def get_standard_presets_by_category(category: str) -> list[StandardPreset]:
    """
    Get all standard presets in a category.

    Args:
        category: Category name

    Returns:
        List of StandardPresets in that category
    """
    return [p for p in STANDARD_PRESETS if p.category == category]


def format_preset_for_menu(preset: StandardPreset) -> str:
    """
    Format a preset for display in a selection menu.

    Args:
        preset: The preset to format

    Returns:
        Formatted string with name and technical summary
    """
    tech = preset.short_technical
    if tech:
        return f"{preset.icon} {preset.name} ({tech})"
    return f"{preset.icon} {preset.name}"
