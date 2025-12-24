"""
Enhanced Wizard UI Components

Provides rich terminal UI components for interactive wizards using
rich for display and prompt_toolkit for input handling.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Generic,
    Optional,
    TypeVar,
    Union,
)

# Rich imports for beautiful output
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.box import ROUNDED, HEAVY, DOUBLE
from rich.style import Style
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

# Prompt toolkit for interactive input
from prompt_toolkit import prompt as pt_prompt
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter


T = TypeVar('T')

# Global console instance
console = Console()

# Check if we have full terminal capabilities
HAS_INTERACTIVE_TERMINAL = sys.stdin.isatty() and sys.stdout.isatty()


class NavAction(Enum):
    """Navigation actions in the wizard."""
    CONTINUE = "continue"
    BACK = "back"
    CANCEL = "cancel"
    SKIP = "skip"
    SAVE = "save"
    TEST = "test"


@dataclass
class SelectOption(Generic[T]):
    """An option in a selection menu."""
    label: str
    value: T
    description: Optional[str] = None
    disabled: bool = False
    icon: str = ""
    help_text: Optional[str] = None  # Contextual help for this option


@dataclass
class WizardSection:
    """A section in the wizard navigation."""
    id: str
    name: str
    icon: str
    description: str
    completed: bool = False
    required: bool = True


class WizardUI:
    """
    Enhanced UI components for wizards.

    Provides beautiful terminal interfaces with:
    - Scrollable selection menus
    - Progress indicators
    - Sectioned navigation
    - Live previews
    - Color pickers
    """

    # Color scheme
    COLORS = {
        'primary': '#e94560',      # Accent color (pink/red)
        'secondary': '#0f3460',    # Dark blue
        'background': '#1a1a2e',   # Dark background
        'success': '#00ff00',      # Green
        'warning': '#ffaa00',      # Orange
        'error': '#ff0000',        # Red
        'info': '#00fff5',         # Cyan
        'muted': '#666666',        # Gray
    }

    def __init__(self):
        """Initialize the wizard UI."""
        self.console = console
        self.interactive = HAS_INTERACTIVE_TERMINAL
        self._section_history: list[str] = []

    # =========================================================================
    # Headers and Sections
    # =========================================================================

    def print_wizard_header(self, title: str, subtitle: Optional[str] = None) -> None:
        """Print a prominent wizard header."""
        header_text = Text()
        header_text.append(f"\n{title}\n", style=f"bold {self.COLORS['primary']}")
        if subtitle:
            header_text.append(subtitle, style=self.COLORS['muted'])

        self.console.print(Panel(
            header_text,
            box=DOUBLE,
            border_style=self.COLORS['primary'],
            padding=(1, 2),
        ))

    def print_section_header(
        self,
        title: str,
        step: Optional[int] = None,
        total: Optional[int] = None,
        description: Optional[str] = None
    ) -> None:
        """Print a section header with optional step indicator."""
        step_text = ""
        if step is not None and total is not None:
            step_text = f"[{self.COLORS['info']}]Step {step}/{total}[/] "

        self.console.print()
        self.console.print(f"{step_text}[bold]{title}[/bold]")
        if description:
            self.console.print(f"[{self.COLORS['muted']}]{description}[/]")
        self.console.print(f"[{self.COLORS['muted']}]{'─' * 50}[/]")

    def print_section_nav(self, sections: list[WizardSection], current: str) -> None:
        """Print a navigation bar showing all sections."""
        nav_items = []
        for section in sections:
            if section.id == current:
                style = f"bold {self.COLORS['primary']}"
                marker = "●"
            elif section.completed:
                style = self.COLORS['success']
                marker = "✓"
            else:
                style = self.COLORS['muted']
                marker = "○"

            nav_items.append(Text(f" {marker} {section.name} ", style=style))

        self.console.print()
        self.console.print(Columns(nav_items, equal=True, expand=True))
        self.console.print()

    # =========================================================================
    # Selection Menus
    # =========================================================================

    async def select_one(
        self,
        title: str,
        options: list[SelectOption[T]],
        description: Optional[str] = None,
        default: Optional[T] = None,
        allow_back: bool = True,
        allow_skip: bool = False,
        show_descriptions: bool = True
    ) -> tuple[Optional[T], NavAction]:
        """
        Present a styled single-selection menu.

        Uses rich formatting for a beautiful numbered selection interface.
        """
        if not options:
            self.print_error("No options available")
            return None, NavAction.CANCEL

        # Find default index
        default_idx = -1
        for i, opt in enumerate(options):
            if opt.value == default:
                default_idx = i
                break

        return await self._select_one_styled(
            title, options, description, default_idx,
            allow_back, allow_skip, show_descriptions
        )

    async def _select_one_styled(
        self,
        title: str,
        options: list[SelectOption[T]],
        description: Optional[str],
        default_idx: int,
        allow_back: bool,
        allow_skip: bool,
        show_descriptions: bool
    ) -> tuple[Optional[T], NavAction]:
        """Arrow-key selection menu using questionary."""
        import questionary
        from questionary import Choice, Separator

        self.console.print()

        # Build choices for questionary
        q_choices = []
        for opt in options:
            icon_prefix = f"{opt.icon} " if opt.icon else ""
            label = f"{icon_prefix}{opt.label}"
            if show_descriptions and opt.description:
                label = f"{label} - {opt.description}"

            q_choices.append(Choice(
                title=label,
                value=("option", opt.value),
                disabled=opt.disabled if opt.disabled else None,
            ))

        # Add navigation options
        q_choices.append(Separator())
        if allow_back:
            q_choices.append(Choice(title="← Back", value=("nav", "back")))
        if allow_skip:
            q_choices.append(Choice(title="→ Skip", value=("nav", "skip")))
        q_choices.append(Choice(title="✕ Cancel", value=("nav", "cancel")))

        # Determine default
        default_choice = None
        if default_idx >= 0 and default_idx < len(options):
            # Find the matching choice
            for qc in q_choices:
                if hasattr(qc, 'value') and qc.value == ("option", options[default_idx].value):
                    default_choice = qc.value
                    break

        # Show title with description
        prompt = title
        if description:
            self.console.print(f"[{self.COLORS['muted']}]{description}[/]")

        try:
            result = await questionary.select(
                prompt,
                choices=q_choices,
                default=default_choice,
                use_arrow_keys=True,
                use_jk_keys=True,
            ).ask_async()

            if result is None:
                return None, NavAction.CANCEL

            result_type, result_value = result

            if result_type == "nav":
                if result_value == "back":
                    return None, NavAction.BACK
                elif result_value == "skip":
                    return None, NavAction.SKIP
                else:
                    return None, NavAction.CANCEL
            else:
                return result_value, NavAction.CONTINUE

        except KeyboardInterrupt:
            return None, NavAction.CANCEL

    async def select_multiple(
        self,
        title: str,
        options: list[SelectOption[T]],
        description: Optional[str] = None,
        defaults: Optional[list[T]] = None,
        min_selections: int = 0,
        max_selections: Optional[int] = None,
        allow_back: bool = True
    ) -> tuple[list[T], NavAction]:
        """
        Present a styled multi-selection menu.

        Uses comma-separated input with rich formatting.
        """
        defaults = defaults or []

        return await self._select_multiple_styled(
            title, options, description, defaults,
            min_selections, max_selections, allow_back
        )

    async def _select_multiple_styled(
        self,
        title: str,
        options: list[SelectOption[T]],
        description: Optional[str],
        defaults: list[T],
        min_selections: int,
        max_selections: Optional[int],
        allow_back: bool
    ) -> tuple[list[T], NavAction]:
        """Arrow-key multi-selection menu using questionary checkboxes."""
        import questionary
        from questionary import Choice, Separator

        self.console.print()

        # Build choices for questionary
        q_choices = []
        for opt in options:
            icon_prefix = f"{opt.icon} " if opt.icon else ""
            label = f"{icon_prefix}{opt.label}"
            if opt.description:
                label = f"{label} - {opt.description}"

            q_choices.append(Choice(
                title=label,
                value=opt.value,
                checked=opt.value in defaults,
                disabled=opt.disabled if opt.disabled else None,
            ))

        # Show description and constraints
        if description:
            self.console.print(f"[{self.COLORS['muted']}]{description}[/]")
        if min_selections > 0 or max_selections:
            constraints = []
            if min_selections > 0:
                constraints.append(f"min: {min_selections}")
            if max_selections:
                constraints.append(f"max: {max_selections}")
            self.console.print(f"[{self.COLORS['muted']}]({', '.join(constraints)})[/]")

        try:
            result = await questionary.checkbox(
                title,
                choices=q_choices,
            ).ask_async()

            if result is None:
                return [], NavAction.CANCEL

            # Validate min/max selections
            if min_selections and len(result) < min_selections:
                self.print_error(f"Please select at least {min_selections} option(s)")
                # Recursively call to let user try again
                return await self._select_multiple_styled(
                    title, options, description, result,
                    min_selections, max_selections, allow_back
                )

            if max_selections and len(result) > max_selections:
                self.print_error(f"Please select at most {max_selections} option(s)")
                return await self._select_multiple_styled(
                    title, options, description, result,
                    min_selections, max_selections, allow_back
                )

            return result, NavAction.CONTINUE

        except KeyboardInterrupt:
            return [], NavAction.CANCEL

    # =========================================================================
    # Input Methods
    # =========================================================================

    async def get_input(
        self,
        prompt_text: str,
        default: Optional[str] = None,
        validator: Optional[Callable[[str], bool]] = None,
        error_message: str = "Invalid input",
        completions: Optional[list[str]] = None,
        allow_empty: bool = False,
        allow_back: bool = True,
        allow_skip: bool = False
    ) -> tuple[str, NavAction]:
        """Get text input with optional validation using questionary."""
        import questionary

        self.console.print()

        # Build validator function for questionary
        def q_validate(text: str) -> bool | str:
            # Navigation commands
            lower_text = text.lower()
            if lower_text in ("back", "b") and allow_back:
                return True  # Allow navigation commands through
            if lower_text in ("skip", "s") and allow_skip:
                return True
            if lower_text in ("cancel", "c", "q"):
                return True

            if not text:
                if default is not None or allow_empty:
                    return True
                return "Input cannot be empty"

            if validator and not validator(text):
                return error_message

            return True

        try:
            if completions:
                result = await questionary.autocomplete(
                    prompt_text,
                    choices=completions,
                    default=default or "",
                    validate=q_validate,
                ).ask_async()
            else:
                result = await questionary.text(
                    prompt_text,
                    default=default or "",
                    validate=q_validate,
                ).ask_async()

            if result is None:
                return "", NavAction.CANCEL

            # Handle navigation commands
            lower_result = result.lower()
            if lower_result in ("back", "b") and allow_back:
                return "", NavAction.BACK
            if lower_result in ("skip", "s") and allow_skip:
                return "", NavAction.SKIP
            if lower_result in ("cancel", "c", "q"):
                return "", NavAction.CANCEL

            # Handle default for empty input
            if not result and default is not None:
                return default, NavAction.CONTINUE

            return result, NavAction.CONTINUE

        except KeyboardInterrupt:
            return "", NavAction.CANCEL

    async def get_number(
        self,
        prompt_text: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        default: Optional[float] = None,
        allow_float: bool = True,
        unit: Optional[str] = None,
        allow_back: bool = True,
        allow_skip: bool = False
    ) -> tuple[Optional[float], NavAction]:
        """Get numeric input with range validation."""
        range_parts = []
        if min_value is not None:
            range_parts.append(f"min: {min_value}")
        if max_value is not None:
            range_parts.append(f"max: {max_value}")

        range_hint = f" ({', '.join(range_parts)})" if range_parts else ""
        unit_hint = f" {unit}" if unit else ""
        default_hint = f" [default: {default}{unit_hint}]" if default is not None else ""

        full_prompt = f"{prompt_text}{range_hint}{default_hint}"

        def validate(value: str) -> bool:
            if not value and default is not None:
                return True
            try:
                num = float(value) if allow_float else int(value)
                if min_value is not None and num < min_value:
                    return False
                if max_value is not None and num > max_value:
                    return False
                return True
            except ValueError:
                return False

        value, action = await self.get_input(
            full_prompt,
            validator=validate,
            error_message=f"Please enter a valid number{range_hint}",
            allow_empty=default is not None,
            allow_back=allow_back,
            allow_skip=allow_skip
        )

        if action != NavAction.CONTINUE:
            return None, action

        if not value and default is not None:
            return default, NavAction.CONTINUE

        num = float(value) if allow_float else int(value)
        return num, NavAction.CONTINUE

    async def get_confirmation(
        self,
        prompt_text: str,
        default: bool = False,
        allow_back: bool = True
    ) -> tuple[bool, NavAction]:
        """Get yes/no confirmation using questionary."""
        import questionary

        self.console.print()

        try:
            result = await questionary.confirm(
                prompt_text,
                default=default,
            ).ask_async()

            if result is None:
                return False, NavAction.CANCEL

            return result, NavAction.CONTINUE

        except KeyboardInterrupt:
            return False, NavAction.CANCEL

    # =========================================================================
    # Special Input Methods
    # =========================================================================

    async def get_color(
        self,
        prompt_text: str = "Enter color",
        default: Optional[str] = None,
        allow_skip: bool = True
    ) -> tuple[Optional[str], NavAction]:
        """Get color input with preview."""
        color_presets = [
            "red", "orange", "yellow", "green", "cyan", "blue",
            "purple", "pink", "white", "warm", "cool"
        ]

        self.console.print(f"\n[bold]{prompt_text}[/bold]")
        self.console.print(f"[{self.COLORS['muted']}]Enter a color name, hex code (#FF0000), or preset:[/]")

        # Show color swatches
        swatches = []
        for color in color_presets[:6]:
            swatches.append(f"[{color}]■[/] {color}")
        self.console.print("  " + "  ".join(swatches))
        swatches = []
        for color in color_presets[6:]:
            swatches.append(f"[{color if color not in ('warm', 'cool', 'white') else 'white'}]■[/] {color}")
        self.console.print("  " + "  ".join(swatches))

        return await self.get_input(
            "",
            default=default,
            completions=color_presets,
            allow_skip=allow_skip,
            allow_empty=allow_skip
        )

    async def get_slider_value(
        self,
        prompt_text: str,
        min_value: float,
        max_value: float,
        default: float,
        step: float = 1.0,
        unit: str = "",
        show_bar: bool = True
    ) -> tuple[Optional[float], NavAction]:
        """Get a value with visual slider feedback."""
        if show_bar:
            self._print_slider_bar(default, min_value, max_value, unit)

        return await self.get_number(
            prompt_text,
            min_value=min_value,
            max_value=max_value,
            default=default,
            unit=unit
        )

    def _print_slider_bar(
        self,
        value: float,
        min_value: float,
        max_value: float,
        unit: str = ""
    ) -> None:
        """Print a visual slider bar."""
        bar_width = 30
        ratio = (value - min_value) / (max_value - min_value) if max_value > min_value else 0
        filled = int(bar_width * ratio)

        bar = "█" * filled + "░" * (bar_width - filled)
        self.console.print(f"  [{self.COLORS['info']}]{bar}[/] {value}{unit}")

    # =========================================================================
    # Display Methods
    # =========================================================================

    def print_success(self, message: str) -> None:
        """Print a success message."""
        self.console.print(f"\n[{self.COLORS['success']}]✓ {message}[/]\n")

    def print_error(self, message: str) -> None:
        """Print an error message."""
        self.console.print(f"[{self.COLORS['error']}]✗ {message}[/]")

    def print_warning(self, message: str) -> None:
        """Print a warning message."""
        self.console.print(f"[{self.COLORS['warning']}]⚠ {message}[/]")

    def print_info(self, message: str) -> None:
        """Print an info message."""
        self.console.print(f"[{self.COLORS['info']}]ℹ {message}[/]")

    def print_muted(self, message: str) -> None:
        """Print muted/secondary text."""
        self.console.print(f"[{self.COLORS['muted']}]{message}[/]")

    def print_key_value(self, key: str, value: Any, indent: int = 0) -> None:
        """Print a key-value pair."""
        spaces = "  " * indent
        self.console.print(f"{spaces}[bold]{key}:[/] {value}")

    def print_table(
        self,
        title: str,
        columns: list[str],
        rows: list[list[Any]],
        show_header: bool = True
    ) -> None:
        """Print a formatted table."""
        table = Table(title=title, box=ROUNDED, border_style=self.COLORS['muted'])

        for col in columns:
            table.add_column(col, style=self.COLORS['info'])

        for row in rows:
            table.add_row(*[str(cell) for cell in row])

        self.console.print(table)

    def print_summary_panel(
        self,
        title: str,
        items: dict[str, Any],
        style: str = "info"
    ) -> None:
        """Print a summary panel with key-value pairs."""
        content = "\n".join(f"[bold]{k}:[/] {v}" for k, v in items.items())

        border_color = self.COLORS.get(style, self.COLORS['info'])
        self.console.print(Panel(
            content,
            title=title,
            border_style=border_color,
            box=ROUNDED,
            padding=(1, 2)
        ))

    # =========================================================================
    # Progress and Loading
    # =========================================================================

    def show_spinner(self, message: str) -> Progress:
        """Show a spinner for async operations."""
        return Progress(
            SpinnerColumn(),
            TextColumn(f"[{self.COLORS['info']}]{message}[/]"),
            console=self.console
        )

    def print_test_indicator(self, testing: bool = True) -> None:
        """Print a test mode indicator."""
        if testing:
            self.console.print(
                f"\n[{self.COLORS['warning']}]▶ Testing setting... "
                f"(press Enter when done viewing)[/]"
            )
        else:
            self.console.print(f"[{self.COLORS['success']}]✓ Test complete[/]")

    # =========================================================================
    # Contextual Help Methods
    # =========================================================================

    def show_contextual_help(
        self,
        help_text: str,
        compact: bool = False,
    ) -> None:
        """
        Display contextual help text below a prompt.

        Args:
            help_text: The help text to display
            compact: If True, use minimal formatting (muted gray)
        """
        if not help_text:
            return

        if compact:
            self.console.print(f"[{self.COLORS['muted']}]  {help_text}[/]")
        else:
            self.console.print(f"[{self.COLORS['info']}]  {help_text}[/]")

    def show_help_hint(self) -> None:
        """Display a hint about how to access help."""
        self.console.print(
            f"[{self.COLORS['muted']}]"
            "Tip: Type '?term' for help on any term"
            "[/]"
        )

    # =========================================================================
    # Visual Feedback Methods
    # =========================================================================

    def render_brightness_preview(
        self,
        value: float,
        width: int = 30,
    ) -> None:
        """
        Render a visual brightness bar preview.

        Args:
            value: Brightness value 0-100
            width: Width of the bar in characters
        """
        from .visual_feedback import render_brightness_bar
        bar = render_brightness_bar(value, width)
        self.console.print(f"  [{self.COLORS['info']}]{bar}[/]")

    def render_temperature_preview(
        self,
        mirek: int,
    ) -> None:
        """
        Render a color temperature swatch preview.

        Args:
            mirek: Color temperature in mirek (153-500)
        """
        from .visual_feedback import render_temperature_swatch
        swatch = render_temperature_swatch(mirek, size=4)
        kelvin = int(1_000_000 / mirek) if mirek > 0 else 0
        self.console.print(f"  {swatch} {kelvin}K ({mirek} mirek)")

    def render_color_preview(
        self,
        x: float,
        y: float,
    ) -> None:
        """
        Render a color swatch preview for XY coordinates.

        Args:
            x: CIE x coordinate
            y: CIE y coordinate
        """
        from .visual_feedback import render_color_swatch
        swatch = render_color_swatch((x, y), size=4)
        self.console.print(f"  {swatch} xy({x:.3f}, {y:.3f})")

    # =========================================================================
    # Mode-Aware Input Methods
    # =========================================================================

    async def get_input_with_help(
        self,
        prompt_text: str,
        help_text: Optional[str] = None,
        default: Optional[str] = None,
        validator: Optional[Callable[[str], bool]] = None,
        error_message: str = "Invalid input",
        completions: Optional[list[str]] = None,
        allow_empty: bool = False,
        allow_back: bool = True,
        allow_skip: bool = False,
        show_help: bool = True,
    ) -> tuple[str, NavAction]:
        """
        Get text input with optional contextual help displayed.

        This is an enhanced version of get_input that shows help text
        before the prompt when show_help is True.

        Args:
            prompt_text: The prompt to display
            help_text: Optional contextual help to show
            default: Default value
            validator: Validation function
            error_message: Error message for invalid input
            completions: Tab completion options
            allow_empty: Allow empty input
            allow_back: Allow back navigation
            allow_skip: Allow skip navigation
            show_help: Whether to display help text

        Returns:
            Tuple of (input_value, NavAction)
        """
        if show_help and help_text:
            self.show_contextual_help(help_text, compact=True)

        return await self.get_input(
            prompt_text=prompt_text,
            default=default,
            validator=validator,
            error_message=error_message,
            completions=completions,
            allow_empty=allow_empty,
            allow_back=allow_back,
            allow_skip=allow_skip,
        )

    async def get_number_with_preview(
        self,
        prompt_text: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        default: Optional[float] = None,
        allow_float: bool = True,
        unit: Optional[str] = None,
        allow_back: bool = True,
        allow_skip: bool = False,
        help_text: Optional[str] = None,
        preview_type: Optional[str] = None,  # 'brightness', 'temperature', etc.
    ) -> tuple[Optional[float], NavAction]:
        """
        Get numeric input with visual preview and help text.

        Args:
            prompt_text: The prompt to display
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            default: Default value
            allow_float: Allow decimal values
            unit: Unit label to show
            allow_back: Allow back navigation
            allow_skip: Allow skip navigation
            help_text: Contextual help text
            preview_type: Type of visual preview to show

        Returns:
            Tuple of (number, NavAction)
        """
        if help_text:
            self.show_contextual_help(help_text, compact=True)

        if preview_type == 'brightness' and default is not None:
            self.render_brightness_preview(default)
        elif preview_type == 'temperature' and default is not None:
            self.render_temperature_preview(int(default))

        return await self.get_number(
            prompt_text=prompt_text,
            min_value=min_value,
            max_value=max_value,
            default=default,
            allow_float=allow_float,
            unit=unit,
            allow_back=allow_back,
            allow_skip=allow_skip,
        )
