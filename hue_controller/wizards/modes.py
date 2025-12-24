"""
Interaction Modes for Wizards

Defines the three-tier interaction model:
- SIMPLE: Preset-based selections with plain English, no technical values
- STANDARD: Technical values with explanations, skip-able steps
- ADVANCED: Full API parameter access with validation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import questionary
from rich.console import Console
from rich.panel import Panel


console = Console()


class InteractionMode(Enum):
    """
    User interaction mode for wizards.

    Controls the level of detail and technical exposure in wizard flows.
    """
    SIMPLE = "simple"
    STANDARD = "standard"
    ADVANCED = "advanced"


@dataclass
class ModeConfig:
    """
    Configuration settings for each interaction mode.

    Determines what UI elements and options are shown based on mode.
    """
    mode: InteractionMode

    # Display settings
    show_technical_values: bool = False
    show_presets: bool = True
    show_all_options: bool = False
    show_help_text: bool = True
    show_advanced_sections: bool = False

    # Section visibility
    show_palette_section: bool = False
    show_dynamics_section: bool = False
    show_gradient_section: bool = False
    show_recall_section: bool = False

    # Input settings
    allow_raw_values: bool = False
    use_friendly_labels: bool = True
    show_current_values: bool = True

    @classmethod
    def for_mode(cls, mode: InteractionMode) -> "ModeConfig":
        """Create a ModeConfig for the specified mode."""
        if mode == InteractionMode.SIMPLE:
            return cls(
                mode=mode,
                show_technical_values=False,
                show_presets=True,
                show_all_options=False,
                show_help_text=True,
                show_advanced_sections=False,
                show_palette_section=False,
                show_dynamics_section=False,
                show_gradient_section=False,
                show_recall_section=False,
                allow_raw_values=False,
                use_friendly_labels=True,
                show_current_values=False,
            )
        elif mode == InteractionMode.STANDARD:
            return cls(
                mode=mode,
                show_technical_values=True,
                show_presets=True,
                show_all_options=False,
                show_help_text=True,
                show_advanced_sections=False,
                show_palette_section=False,
                show_dynamics_section=True,
                show_gradient_section=False,
                show_recall_section=False,
                allow_raw_values=True,
                use_friendly_labels=True,
                show_current_values=True,
            )
        else:  # ADVANCED
            return cls(
                mode=mode,
                show_technical_values=True,
                show_presets=True,
                show_all_options=True,
                show_help_text=True,
                show_advanced_sections=True,
                show_palette_section=True,
                show_dynamics_section=True,
                show_gradient_section=True,
                show_recall_section=True,
                allow_raw_values=True,
                use_friendly_labels=False,
                show_current_values=True,
            )


# Mode descriptions for selection menu
MODE_DESCRIPTIONS: dict[InteractionMode, str] = {
    InteractionMode.SIMPLE: (
        "Quick and easy - choose from presets like 'Cozy', 'Bright', or 'Relaxing'. "
        "Perfect for getting started without technical details."
    ),
    InteractionMode.STANDARD: (
        "See technical values (like 2700K) with helpful explanations. "
        "Good balance of control and guidance."
    ),
    InteractionMode.ADVANCED: (
        "Full access to every API parameter - mirek values, XY colors, gradients, "
        "dynamics, and palette configuration. For power users."
    ),
}

# Mode icons for display
MODE_ICONS: dict[InteractionMode, str] = {
    InteractionMode.SIMPLE: "🟢",
    InteractionMode.STANDARD: "🟡",
    InteractionMode.ADVANCED: "🔴",
}


async def detect_user_mode(
    default: InteractionMode = InteractionMode.ADVANCED,
    show_descriptions: bool = True,
) -> InteractionMode:
    """
    Prompt user to select their preferred interaction mode.

    Args:
        default: Default mode if user just presses Enter
        show_descriptions: Whether to show detailed mode descriptions

    Returns:
        The selected InteractionMode
    """
    console.print()
    console.print(Panel(
        "[bold]Choose Your Experience Level[/bold]\n\n"
        "Select how much detail you want to see in this wizard.",
        border_style="cyan",
    ))

    choices = []
    for mode in InteractionMode:
        icon = MODE_ICONS[mode]
        label = f"{icon} {mode.value.title()} Mode"
        if show_descriptions:
            desc = MODE_DESCRIPTIONS[mode]
            # Truncate long descriptions for display
            if len(desc) > 80:
                desc = desc[:77] + "..."
            label = f"{label}"
            choices.append(questionary.Choice(
                title=label,
                value=mode,
            ))
        else:
            choices.append(questionary.Choice(title=label, value=mode))

    # Find default choice
    default_choice = None
    for choice in choices:
        if choice.value == default:
            default_choice = choice.value
            break

    try:
        result = await questionary.select(
            "Select mode:",
            choices=choices,
            default=default_choice,
            instruction="(Use arrow keys to navigate, Enter to select)",
        ).ask_async()

        if result is None:
            return default

        # Show confirmation of selected mode
        selected_icon = MODE_ICONS[result]
        console.print(f"\n{selected_icon} Using [bold]{result.value.title()}[/bold] mode\n")

        return result

    except KeyboardInterrupt:
        return default


def get_mode_label(mode: InteractionMode) -> str:
    """Get a display label for a mode."""
    icon = MODE_ICONS[mode]
    return f"{icon} {mode.value.title()}"


def get_mode_description(mode: InteractionMode) -> str:
    """Get the description for a mode."""
    return MODE_DESCRIPTIONS.get(mode, "")
