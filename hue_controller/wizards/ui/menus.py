"""
Async Questionary Menu Wrappers

Provides async-compatible menu selection using questionary's ask_async() method.
These wrappers work within existing asyncio event loops (unlike prompt_toolkit dialogs).
"""

from dataclasses import dataclass
from typing import Any, Optional, TypeVar, Callable
import questionary
from questionary import Choice, Separator


T = TypeVar("T")


@dataclass
class MenuChoice:
    """A choice in a menu with optional description and icon."""
    label: str
    value: Any
    description: Optional[str] = None
    icon: Optional[str] = None
    disabled: Optional[str] = None  # If set, shows why it's disabled

    def to_questionary_choice(self) -> Choice:
        """Convert to questionary Choice object."""
        # Build display text with icon if present
        display = f"{self.icon} {self.label}" if self.icon else self.label

        return Choice(
            title=display,
            value=self.value,
            disabled=self.disabled,
        )


class AsyncMenu:
    """
    Async-compatible menu system using questionary.

    All methods use questionary's ask_async() which properly integrates
    with existing asyncio event loops.
    """

    @staticmethod
    async def select(
        message: str,
        choices: list[MenuChoice | str],
        default: Optional[Any] = None,
        show_descriptions: bool = True,
    ) -> Optional[Any]:
        """
        Single selection menu with arrow key navigation.

        Args:
            message: The question/prompt to display
            choices: List of MenuChoice objects or simple strings
            default: Default selected value
            show_descriptions: Whether to show choice descriptions

        Returns:
            The selected value, or None if cancelled (Ctrl+C)
        """
        q_choices = []

        for choice in choices:
            if isinstance(choice, str):
                q_choices.append(Choice(title=choice, value=choice))
            elif isinstance(choice, MenuChoice):
                q_choices.append(choice.to_questionary_choice())
            else:
                # It's a Separator or raw Choice
                q_choices.append(choice)

        try:
            result = await questionary.select(
                message,
                choices=q_choices,
                default=default,
                use_shortcuts=False,
                use_arrow_keys=True,
                use_jk_keys=True,  # vim-style navigation
            ).ask_async()
            return result
        except KeyboardInterrupt:
            return None

    @staticmethod
    async def select_with_categories(
        message: str,
        categories: dict[str, list[MenuChoice]],
        default: Optional[Any] = None,
    ) -> Optional[Any]:
        """
        Selection menu with categorized choices separated by headers.

        Args:
            message: The question/prompt to display
            categories: Dict mapping category name to list of choices
            default: Default selected value

        Returns:
            The selected value, or None if cancelled
        """
        q_choices = []

        for category_name, category_choices in categories.items():
            # Add separator with category name
            q_choices.append(Separator(f"  {category_name}"))

            for choice in category_choices:
                q_choices.append(choice.to_questionary_choice())

        try:
            result = await questionary.select(
                message,
                choices=q_choices,
                default=default,
                use_shortcuts=False,
                use_arrow_keys=True,
            ).ask_async()
            return result
        except KeyboardInterrupt:
            return None

    @staticmethod
    async def checkbox(
        message: str,
        choices: list[MenuChoice | str],
        default: Optional[list[Any]] = None,
    ) -> Optional[list[Any]]:
        """
        Multi-selection menu with checkboxes.

        Args:
            message: The question/prompt to display
            choices: List of MenuChoice objects or simple strings
            default: List of pre-selected values

        Returns:
            List of selected values, or None if cancelled
        """
        q_choices = []

        for choice in choices:
            if isinstance(choice, str):
                checked = default and choice in default
                q_choices.append(Choice(title=choice, value=choice, checked=checked))
            elif isinstance(choice, MenuChoice):
                checked = default and choice.value in default
                qc = choice.to_questionary_choice()
                qc.checked = checked
                q_choices.append(qc)

        try:
            result = await questionary.checkbox(
                message,
                choices=q_choices,
            ).ask_async()
            return result
        except KeyboardInterrupt:
            return None

    @staticmethod
    async def text(
        message: str,
        default: str = "",
        validate: Optional[Callable[[str], bool | str]] = None,
        placeholder: Optional[str] = None,
    ) -> Optional[str]:
        """
        Text input with optional validation.

        Args:
            message: The question/prompt to display
            default: Default text value
            validate: Validation function returning True or error message
            placeholder: Placeholder text (shown when empty)

        Returns:
            The entered text, or None if cancelled
        """
        try:
            result = await questionary.text(
                message,
                default=default,
                validate=validate,
            ).ask_async()
            return result
        except KeyboardInterrupt:
            return None

    @staticmethod
    async def confirm(
        message: str,
        default: bool = True,
    ) -> Optional[bool]:
        """
        Yes/No confirmation prompt.

        Args:
            message: The question to confirm
            default: Default answer (True=Yes, False=No)

        Returns:
            True/False, or None if cancelled
        """
        try:
            result = await questionary.confirm(
                message,
                default=default,
            ).ask_async()
            return result
        except KeyboardInterrupt:
            return None

    @staticmethod
    async def number(
        message: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        default: Optional[float] = None,
        float_allowed: bool = True,
    ) -> Optional[float]:
        """
        Numeric input with range validation.

        Args:
            message: The question/prompt to display
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            default: Default value
            float_allowed: Whether decimals are allowed

        Returns:
            The entered number, or None if cancelled
        """
        def validate(val: str) -> bool | str:
            if not val:
                return "Please enter a number"
            try:
                num = float(val) if float_allowed else int(val)
                if min_value is not None and num < min_value:
                    return f"Must be at least {min_value}"
                if max_value is not None and num > max_value:
                    return f"Must be at most {max_value}"
                return True
            except ValueError:
                return "Please enter a valid number"

        default_str = str(default) if default is not None else ""

        try:
            result = await questionary.text(
                message,
                default=default_str,
                validate=validate,
            ).ask_async()

            if result is None:
                return None

            return float(result) if float_allowed else int(result)
        except KeyboardInterrupt:
            return None

    @staticmethod
    async def path(
        message: str,
        default: str = "",
        only_directories: bool = False,
    ) -> Optional[str]:
        """
        Path input with autocomplete.

        Args:
            message: The question/prompt to display
            default: Default path
            only_directories: Whether to only accept directories

        Returns:
            The entered path, or None if cancelled
        """
        try:
            result = await questionary.path(
                message,
                default=default,
                only_directories=only_directories,
            ).ask_async()
            return result
        except KeyboardInterrupt:
            return None

    @staticmethod
    async def autocomplete(
        message: str,
        choices: list[str],
        default: str = "",
        validate: Optional[Callable[[str], bool | str]] = None,
    ) -> Optional[str]:
        """
        Text input with autocomplete suggestions.

        Args:
            message: The question/prompt to display
            choices: List of autocomplete suggestions
            default: Default text value
            validate: Validation function

        Returns:
            The entered/selected text, or None if cancelled
        """
        try:
            result = await questionary.autocomplete(
                message,
                choices=choices,
                default=default,
                validate=validate,
            ).ask_async()
            return result
        except KeyboardInterrupt:
            return None


# Convenience separator for grouping menu items
def menu_separator(text: str = "") -> Separator:
    """Create a visual separator in menus."""
    return Separator(f"  {text}" if text else "")
