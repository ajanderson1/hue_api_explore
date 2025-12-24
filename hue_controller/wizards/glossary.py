"""
Hue Terminology Glossary

Centralized definitions for all Hue API terminology with:
- Clear, user-friendly definitions
- Practical examples
- Related terms for cross-reference
- Rich formatting for terminal display
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text


console = Console()


@dataclass
class GlossaryEntry:
    """A glossary entry for a Hue term."""
    term: str
    definition: str
    example: Optional[str] = None
    related_terms: list[str] = field(default_factory=list)
    technical_note: Optional[str] = None
    simple_label: Optional[str] = None  # Friendly label for Simple Mode


# Comprehensive glossary of Hue terminology
GLOSSARY: dict[str, GlossaryEntry] = {
    # Color and Light Terms
    "mirek": GlossaryEntry(
        term="Mirek",
        definition=(
            "A unit for measuring color temperature (micro reciprocal degrees). "
            "Lower mirek = cooler/bluer light (like daylight). "
            "Higher mirek = warmer/yellower light (like candlelight)."
        ),
        example="153 mirek = 6500K (cool daylight), 370 mirek = 2700K (warm white), 500 mirek = 2000K (candlelight)",
        related_terms=["color temperature", "kelvin", "warm", "cool"],
        technical_note="Mirek = 1,000,000 / Kelvin. Valid range: 153-500 (6500K-2000K).",
        simple_label="warmth",
    ),
    "color temperature": GlossaryEntry(
        term="Color Temperature",
        definition=(
            "How 'warm' or 'cool' white light appears. Measured in Kelvin (K) or Mirek. "
            "Warm light (2700K) feels cozy like incandescent bulbs. "
            "Cool light (6500K) feels bright like daylight."
        ),
        example="2700K = warm living room, 4000K = neutral office, 6500K = energizing workspace",
        related_terms=["mirek", "kelvin", "white light"],
        simple_label="warmth",
    ),
    "kelvin": GlossaryEntry(
        term="Kelvin (K)",
        definition=(
            "The standard unit for color temperature. Named after physicist Lord Kelvin. "
            "Common values: 2700K (warm), 4000K (neutral), 6500K (daylight)."
        ),
        example="Candlelight ~2000K, Sunset ~3000K, Noon daylight ~5500K",
        related_terms=["mirek", "color temperature"],
        technical_note="Hue uses mirek internally. Kelvin = 1,000,000 / mirek.",
    ),
    "gamut": GlossaryEntry(
        term="Gamut",
        definition=(
            "The range of colors a light can produce. Different Hue bulbs have different gamuts "
            "(A, B, or C) based on their LED capabilities."
        ),
        example="Gamut C bulbs can produce more vivid greens and cyans than older Gamut A bulbs.",
        related_terms=["xy color", "cie", "color space"],
        technical_note="Gamut A: older bulbs, Gamut B: strips, Gamut C: newer bulbs with wider color range.",
    ),
    "xy color": GlossaryEntry(
        term="XY Color (CIE xy)",
        definition=(
            "A way to specify any color using two coordinates (x, y) on a color diagram. "
            "The Hue API uses this system for precise color control."
        ),
        example="Red: x=0.675, y=0.322. Blue: x=0.167, y=0.040. Pure white: x=0.313, y=0.329.",
        related_terms=["gamut", "cie", "color"],
        technical_note="Values range 0-1. The actual visible color depends on the bulb's gamut.",
        simple_label="color",
    ),
    "cie": GlossaryEntry(
        term="CIE",
        definition=(
            "The International Commission on Illumination (Commission Internationale de l'Eclairage). "
            "They created the xy color space used by Hue for color specification."
        ),
        example="CIE 1931 xy chromaticity diagram maps all visible colors to x,y coordinates.",
        related_terms=["xy color", "gamut"],
    ),
    # Hue Concepts
    "grouped light": GlossaryEntry(
        term="Grouped Light",
        definition=(
            "A virtual light that represents all lights in a room or zone. "
            "When you control a grouped light, all lights in that group respond together."
        ),
        example="Setting 'Living Room' grouped light to 50% dims all living room lights at once.",
        related_terms=["room", "zone", "light"],
        technical_note="More efficient than controlling individual lights - uses one API call instead of many.",
        simple_label="room/zone control",
    ),
    "dynamics": GlossaryEntry(
        term="Dynamics",
        definition=(
            "How lights animate when changing. Controls transition speed and whether colors "
            "gradually shift over time (like in dynamic scenes)."
        ),
        example="A 'Sunset' dynamic scene slowly shifts from orange to deep red over 30 minutes.",
        related_terms=["transition", "speed", "auto dynamic"],
        simple_label="animation",
    ),
    "transition": GlossaryEntry(
        term="Transition Duration",
        definition=(
            "How long it takes for a light to change from one state to another. "
            "Longer transitions create smooth, gradual changes."
        ),
        example="Instant (0ms) for quick changes, 400ms for normal, 2000ms+ for smooth fades.",
        related_terms=["dynamics", "fade"],
        technical_note="Measured in milliseconds. Max ~109 minutes (6,553,500ms).",
        simple_label="fade time",
    ),
    "signaling": GlossaryEntry(
        term="Signaling",
        definition=(
            "A way to make lights flash or blink to get attention, like for notifications "
            "or to identify which light you're configuring."
        ),
        example="'Identify' makes a light blink so you know which physical bulb it is.",
        related_terms=["alert", "identify"],
        simple_label="flashing",
    ),
    "gradient": GlossaryEntry(
        term="Gradient",
        definition=(
            "Multi-color display on gradient-capable lights (like Gradient Lightstrip). "
            "Shows multiple colors smoothly blending along the light's length."
        ),
        example="A sunset gradient might show orange at one end fading to purple at the other.",
        related_terms=["gradient mode", "palette"],
        technical_note="Requires gradient-capable hardware. Supports 2-5 color points.",
    ),
    "gradient mode": GlossaryEntry(
        term="Gradient Mode",
        definition=(
            "How colors are distributed along a gradient light. Options include smooth "
            "interpolation, mirrored patterns, random pixels, or distinct segments."
        ),
        example="'Interpolated' blends colors smoothly; 'Segmented' shows distinct color blocks.",
        related_terms=["gradient", "palette"],
        technical_note="Modes: interpolated_palette, interpolated_palette_mirrored, random_pixelated, segmented.",
    ),
    "archetype": GlossaryEntry(
        term="Archetype",
        definition=(
            "A category describing what type of light or room something is. "
            "Helps Hue provide appropriate default behaviors and icons."
        ),
        example="Light archetypes: sultan_bulb, spot_bulb, pendant. Room archetypes: living_room, bedroom.",
        related_terms=["room", "device"],
        simple_label="type",
    ),
    # Scene Terms
    "scene": GlossaryEntry(
        term="Scene",
        definition=(
            "A saved lighting configuration that can be activated with one command. "
            "Stores brightness, color, and effects for multiple lights."
        ),
        example="A 'Movie Night' scene might dim all lights to 20% with warm amber color.",
        related_terms=["recall", "palette", "actions"],
    ),
    "recall": GlossaryEntry(
        term="Recall / Active",
        definition=(
            "Activating a scene. 'Recall' is the API term for turning on a scene. "
            "The 'active' action triggers the scene normally."
        ),
        example="Recall 'Relax' scene to apply its settings to all configured lights.",
        related_terms=["scene", "dynamic palette"],
        technical_note="Recall actions: active (normal), dynamic_palette (cycling colors), static (no transition).",
        simple_label="activate",
    ),
    "palette": GlossaryEntry(
        term="Palette",
        definition=(
            "A collection of colors used in a scene. For dynamic scenes, lights cycle "
            "through palette colors over time creating animated effects."
        ),
        example="A 'Forest' palette might include multiple shades of green and brown.",
        related_terms=["scene", "dynamic", "auto dynamic"],
    ),
    "auto dynamic": GlossaryEntry(
        term="Auto Dynamic",
        definition=(
            "When enabled, a scene automatically cycles through its palette colors "
            "creating a living, animated lighting effect."
        ),
        example="Enable auto_dynamic on a 'Party' scene to make colors continuously shift.",
        related_terms=["palette", "dynamics", "speed"],
        simple_label="color cycling",
    ),
    "scene action": GlossaryEntry(
        term="Scene Action",
        definition=(
            "The specific settings applied to one light when a scene is activated. "
            "Each light in a scene can have different actions."
        ),
        example="In a 'Focus' scene: desk lamp = bright white, ceiling = off.",
        related_terms=["scene", "light"],
    ),
    "public image": GlossaryEntry(
        term="Public Image",
        definition=(
            "A thumbnail image associated with a scene, shown in the official Hue app. "
            "Helps identify scenes visually."
        ),
        example="A sunset scene might have an orange/pink gradient thumbnail.",
        related_terms=["scene"],
    ),
    # Entertainment
    "entertainment area": GlossaryEntry(
        term="Entertainment Area",
        definition=(
            "A group of lights configured for high-speed sync with media like games, "
            "movies, or music. Uses a special low-latency streaming mode."
        ),
        example="TV entertainment area syncs lights behind your TV with on-screen colors.",
        related_terms=["entertainment", "sync"],
        technical_note="Requires Entertainment API. Lights must be positioned in 3D space.",
    ),
    # Effects
    "effect": GlossaryEntry(
        term="Effect",
        definition=(
            "A dynamic lighting animation built into Hue bulbs. Effects like 'candle' "
            "or 'fire' simulate natural light flickering."
        ),
        example="The 'candle' effect makes a light gently flicker like a real candle flame.",
        related_terms=["timed effect"],
        technical_note="Available effects: candle, fire, prism, sparkle, opal, glisten, underwater, cosmos, sunbeam, enchant.",
    ),
    "timed effect": GlossaryEntry(
        term="Timed Effect",
        definition=(
            "A special effect that runs for a set duration, like sunrise simulation. "
            "Gradually changes light over minutes to hours."
        ),
        example="'Sunrise' timed effect slowly brightens and warms over 30 minutes.",
        related_terms=["effect", "sunrise", "sunset"],
        technical_note="Available: sunrise, sunset. Duration up to 6 hours.",
        simple_label="wake-up light",
    ),
    # Common Aliases
    "brightness": GlossaryEntry(
        term="Brightness",
        definition=(
            "How bright the light is, from 0% (off but still in 'on' state) to 100% (full power). "
            "Also called 'dimming' in the API."
        ),
        example="Dimmed reading light: 30%, Task lighting: 70%, Full brightness: 100%.",
        related_terms=["dimming"],
        technical_note="API uses 'dimming' with 'brightness' as percentage 0-100.",
        simple_label="intensity",
    ),
    "room": GlossaryEntry(
        term="Room",
        definition=(
            "A group of devices (lights, sensors, switches) that belong to a physical space. "
            "Each device can only belong to one room."
        ),
        example="'Living Room' contains ceiling light, floor lamp, and light strip.",
        related_terms=["zone", "grouped light"],
    ),
    "zone": GlossaryEntry(
        term="Zone",
        definition=(
            "A flexible grouping of lights that can overlap with rooms. A light can belong "
            "to multiple zones, allowing creative groupings."
        ),
        example="'Reading Nook' zone contains desk lamp from Office + floor lamp from Living Room.",
        related_terms=["room", "grouped light"],
    ),
    "speed": GlossaryEntry(
        term="Speed",
        definition=(
            "How fast dynamic scenes cycle through their palette colors. "
            "Higher speed = faster color changes."
        ),
        example="Slow speed (0.2) for relaxing ambiance, high speed (0.8) for party mode.",
        related_terms=["dynamics", "auto dynamic", "palette"],
        technical_note="Value 0.0-1.0. Lower = slower color cycling.",
    ),
}


def get_glossary_entry(term: str) -> Optional[GlossaryEntry]:
    """
    Look up a term in the glossary with fuzzy matching.

    Handles:
    - Case-insensitive lookup
    - Plural forms (e.g., 'mireks' -> 'mirek')
    - Common variations (e.g., 'colour' -> 'color')

    Args:
        term: The term to look up

    Returns:
        GlossaryEntry if found, None otherwise
    """
    if not term:
        return None

    # Normalize the search term
    normalized = term.lower().strip()

    # Direct lookup
    if normalized in GLOSSARY:
        return GLOSSARY[normalized]

    # Try removing trailing 's' for plurals
    if normalized.endswith('s') and len(normalized) > 2:
        singular = normalized[:-1]
        if singular in GLOSSARY:
            return GLOSSARY[singular]

    # Try removing 'es' suffix
    if normalized.endswith('es') and len(normalized) > 3:
        singular = normalized[:-2]
        if singular in GLOSSARY:
            return GLOSSARY[singular]

    # Common variations
    variations = {
        "colour": "color",
        "colour temperature": "color temperature",
        "xy": "xy color",
        "cie xy": "xy color",
        "color temp": "color temperature",
        "ct": "color temperature",
        "bri": "brightness",
        "dim": "brightness",
        "dimming": "brightness",
        "temp": "color temperature",
        "k": "kelvin",
        "activate": "recall",
        "trigger": "recall",
        "animation": "dynamics",
        "fade": "transition",
        "flash": "signaling",
        "blink": "signaling",
        "group": "grouped light",
        "groups": "grouped light",
    }

    if normalized in variations:
        return GLOSSARY.get(variations[normalized])

    # Partial match - check if term is contained in any glossary key
    for key, entry in GLOSSARY.items():
        if normalized in key or key in normalized:
            return entry

    return None


def format_glossary_entry(entry: GlossaryEntry, detailed: bool = True) -> str:
    """
    Format a glossary entry for rich terminal display.

    Args:
        entry: The glossary entry to format
        detailed: Whether to include all details or just definition

    Returns:
        Rich-formatted string for console display
    """
    if not detailed:
        return f"[bold]{entry.term}[/bold]: {entry.definition}"

    # Build content
    lines = [f"[bold cyan]{entry.term}[/bold cyan]", ""]
    lines.append(entry.definition)

    if entry.example:
        lines.append("")
        lines.append(f"[dim]Example:[/dim] {entry.example}")

    if entry.technical_note:
        lines.append("")
        lines.append(f"[dim italic]Technical: {entry.technical_note}[/dim italic]")

    if entry.related_terms:
        lines.append("")
        related = ", ".join(entry.related_terms)
        lines.append(f"[dim]See also:[/dim] {related}")

    return "\n".join(lines)


def display_glossary_entry(entry: GlossaryEntry) -> None:
    """Display a glossary entry in a rich panel."""
    content = format_glossary_entry(entry)
    console.print(Panel(
        content,
        title=f"[bold] {entry.term} [/bold]",
        border_style="cyan",
        padding=(1, 2),
    ))


def list_all_terms() -> list[str]:
    """Get a sorted list of all glossary terms."""
    return sorted(GLOSSARY.keys())


def search_glossary(query: str) -> list[GlossaryEntry]:
    """
    Search the glossary for terms matching a query.

    Searches term names, definitions, and related terms.

    Args:
        query: Search query string

    Returns:
        List of matching GlossaryEntry objects
    """
    if not query:
        return []

    query_lower = query.lower()
    results = []

    for entry in GLOSSARY.values():
        # Check term name
        if query_lower in entry.term.lower():
            results.append(entry)
            continue

        # Check definition
        if query_lower in entry.definition.lower():
            results.append(entry)
            continue

        # Check related terms
        for related in entry.related_terms:
            if query_lower in related.lower():
                results.append(entry)
                break

    return results


def get_simple_label(term: str) -> Optional[str]:
    """
    Get the Simple Mode friendly label for a term.

    Args:
        term: The technical term

    Returns:
        Friendly label if defined, None otherwise
    """
    entry = get_glossary_entry(term)
    if entry and entry.simple_label:
        return entry.simple_label
    return None
