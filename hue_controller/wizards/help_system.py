"""
Help System for Wizards

Provides contextual help, inline tooltips, and glossary lookup throughout
the wizard interface. Supports both inline help display and command-based
help queries.
"""

from __future__ import annotations

import re
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .glossary import (
    get_glossary_entry,
    format_glossary_entry,
    display_glossary_entry,
    list_all_terms,
    search_glossary,
    GLOSSARY,
)


console = Console()


class HelpSystem:
    """
    Centralized help system for wizard interfaces.

    Provides:
    - Inline contextual help below prompts
    - Glossary term lookup via /help or ?term
    - Quick tips and hints
    - Full glossary listing
    """

    # Help command patterns
    HELP_PATTERNS = [
        r'^/help\s+(.+)$',        # /help <term>
        r'^help\s+(.+)$',         # help <term>
        r'^\?(.+)$',              # ?term (quick lookup)
        r'^/\?\s*(.+)$',          # /? term
    ]

    # Color scheme matching wizard_ui.py
    COLORS = {
        'help': '#00fff5',        # Cyan for help text
        'muted': '#666666',       # Gray for secondary text
        'term': '#e94560',        # Pink for term names
        'example': '#00ff00',     # Green for examples
    }

    def __init__(self, console_instance: Optional[Console] = None):
        """
        Initialize the help system.

        Args:
            console_instance: Optional Rich console to use for output
        """
        self.console = console_instance or console

    def show_inline_help(
        self,
        help_text: str,
        compact: bool = False,
    ) -> None:
        """
        Display inline help text below a prompt.

        Args:
            help_text: The help text to display
            compact: If True, use minimal formatting
        """
        if not help_text:
            return

        if compact:
            self.console.print(f"[{self.COLORS['muted']}]  {help_text}[/]")
        else:
            self.console.print(f"[{self.COLORS['help']}]  {help_text}[/]")

    def show_term_help(self, term: str) -> bool:
        """
        Look up and display help for a glossary term.

        Args:
            term: The term to look up

        Returns:
            True if term was found and displayed, False otherwise
        """
        entry = get_glossary_entry(term)

        if entry is None:
            self.console.print(f"\n[{self.COLORS['muted']}]No help found for '{term}'.[/]")
            self.console.print(f"[{self.COLORS['muted']}]Try 'glossary' to see all available terms.[/]\n")
            return False

        display_glossary_entry(entry)
        return True

    def show_quick_tip(self, tip: str) -> None:
        """
        Display a quick tip or hint.

        Args:
            tip: The tip text to display
        """
        self.console.print(f"[{self.COLORS['muted']}]  Tip: {tip}[/]")

    def show_glossary_list(self, category: Optional[str] = None) -> None:
        """
        Display a list of all glossary terms.

        Args:
            category: Optional category to filter by (not implemented yet)
        """
        self.console.print()

        # Group terms by category for better organization
        categories = {
            "Color & Light": ["mirek", "color temperature", "kelvin", "gamut", "xy color", "cie", "brightness"],
            "Groups & Rooms": ["room", "zone", "grouped light", "archetype"],
            "Scenes": ["scene", "recall", "palette", "auto dynamic", "scene action", "public image"],
            "Effects & Dynamics": ["effect", "timed effect", "dynamics", "transition", "signaling", "gradient", "gradient mode", "speed"],
            "Entertainment": ["entertainment area"],
        }

        table = Table(
            title="[bold]Hue Terminology Glossary[/bold]",
            show_header=True,
            header_style="bold cyan",
            border_style=self.COLORS['muted'],
        )
        table.add_column("Category", style="bold")
        table.add_column("Terms")

        for category_name, terms in categories.items():
            # Filter to only terms that exist in glossary
            existing_terms = [t for t in terms if t in GLOSSARY]
            if existing_terms:
                terms_str = ", ".join(existing_terms)
                table.add_row(category_name, terms_str)

        self.console.print(table)
        self.console.print()
        self.console.print(f"[{self.COLORS['muted']}]Type '/help <term>' or '?<term>' for detailed information.[/]")
        self.console.print()

    def parse_help_command(self, user_input: str) -> Optional[str]:
        """
        Parse user input to detect help commands.

        Recognizes patterns like:
        - /help mirek
        - help mirek
        - ?mirek
        - /? mirek

        Args:
            user_input: The raw user input string

        Returns:
            The term to look up, or None if not a help command
        """
        if not user_input:
            return None

        user_input = user_input.strip()

        # Check for glossary list command
        if user_input.lower() in ('glossary', '/glossary', 'terms', '/terms'):
            return '__list__'

        # Check each pattern
        for pattern in self.HELP_PATTERNS:
            match = re.match(pattern, user_input, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def handle_help_command(self, user_input: str) -> bool:
        """
        Check if input is a help command and handle it.

        Args:
            user_input: The raw user input string

        Returns:
            True if a help command was handled, False otherwise
        """
        term = self.parse_help_command(user_input)

        if term is None:
            return False

        if term == '__list__':
            self.show_glossary_list()
            return True

        self.show_term_help(term)
        return True

    def get_contextual_help(self, context: str) -> Optional[str]:
        """
        Get contextual help text based on the current wizard context.

        Args:
            context: A key describing the current context (e.g., 'brightness', 'color_temp')

        Returns:
            Help text appropriate for the context, or None
        """
        # Context-specific help messages
        help_texts = {
            # Input contexts
            'brightness': "Enter 0-100%. Tip: 30% is good for ambient, 70% for tasks.",
            'brightness_slider': "Adjust brightness from 0% (minimum, still on) to 100% (maximum).",
            'color_temperature': "Choose warmth: 2700K (cozy) to 6500K (energizing). Type '?mirek' for details.",
            'mirek': "Enter mirek value 153-500. Lower = cooler/bluer, higher = warmer/yellower. Type '?mirek' for details.",
            'scene_name': "Enter a name for your scene (1-32 characters). Tip: Use descriptive names like 'Movie Night' or 'Morning Focus'.",
            'xy_color': "Enter x,y coordinates (0-1). Tip: Use presets or type '?xy color' for common values.",

            # Selection contexts
            'room_select': "Select the room where this scene will apply.",
            'zone_select': "Select the zone for this scene. Zones can include lights from multiple rooms.",
            'light_select': "Select which lights to include. You can choose multiple.",
            'effect_select': "Choose a dynamic effect. Type '?effect' for descriptions of each.",
            'template_select': "Choose a preset to start from. You can customize it afterwards.",
            'mode_select': "Choose your experience level. You can always change this later.",

            # Section contexts
            'palette_section': "Configure the color palette for dynamic scenes. Type '?palette' for details.",
            'dynamics_section': "Control how lights animate and transition. Type '?dynamics' for details.",
            'gradient_section': "Configure multi-color gradients (requires gradient-capable lights). Type '?gradient' for details.",
            'recall_section': "Set how the scene activates. Type '?recall' for details.",
        }

        return help_texts.get(context)

    def show_help_hint(self) -> None:
        """Display a hint about how to access help."""
        self.console.print(
            f"[{self.COLORS['muted']}]"
            "Tip: Type '?term' for help on any term, or 'glossary' to see all terms."
            "[/]"
        )


# Global help system instance for convenience
_help_system: Optional[HelpSystem] = None


def get_help_system() -> HelpSystem:
    """Get the global help system instance."""
    global _help_system
    if _help_system is None:
        _help_system = HelpSystem()
    return _help_system


def show_help(term: str) -> bool:
    """
    Convenience function to show help for a term.

    Args:
        term: The term to look up

    Returns:
        True if term was found
    """
    return get_help_system().show_term_help(term)


def show_inline_help(help_text: str, compact: bool = False) -> None:
    """
    Convenience function to show inline help.

    Args:
        help_text: The help text to display
        compact: If True, use minimal formatting
    """
    get_help_system().show_inline_help(help_text, compact)
