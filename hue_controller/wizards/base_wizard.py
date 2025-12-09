"""
Base Wizard

Base class for interactive wizards with common navigation and input helpers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Optional, TypeVar

from ..exceptions import WizardCancelledError, WizardValidationError

if TYPE_CHECKING:
    from ..device_manager import DeviceManager

T = TypeVar('T')


class WizardAction(Enum):
    """Actions a user can take during wizard navigation."""
    CONTINUE = "continue"
    BACK = "back"
    CANCEL = "cancel"
    SKIP = "skip"


@dataclass
class WizardResult:
    """Result from a wizard execution."""
    success: bool
    message: str
    data: Any = None
    cancelled: bool = False


class BaseWizard(ABC):
    """
    Base class for interactive wizards.

    Provides common functionality for:
    - User input with validation
    - Navigation (back, cancel, skip)
    - Selection menus
    - Confirmation prompts
    """

    BACK_COMMAND = "back"
    CANCEL_COMMAND = "cancel"
    SKIP_COMMAND = "skip"

    def __init__(self, device_manager: DeviceManager):
        """
        Initialize the wizard.

        Args:
            device_manager: Device manager for accessing bridge state
        """
        self.dm = device_manager
        self._step_history: list[str] = []

    @abstractmethod
    async def run(self) -> WizardResult:
        """
        Run the wizard.

        Returns:
            WizardResult indicating success/failure
        """
        pass

    # =========================================================================
    # Input Methods
    # =========================================================================

    def get_input(
        self,
        prompt: str,
        validator: Optional[Callable[[str], bool]] = None,
        error_message: str = "Invalid input",
        allow_empty: bool = False,
        allow_back: bool = True,
        allow_cancel: bool = True
    ) -> tuple[str, WizardAction]:
        """
        Get user input with optional validation.

        Args:
            prompt: Prompt to display
            validator: Optional validation function
            error_message: Message to show on invalid input
            allow_empty: Whether to allow empty input
            allow_back: Whether to allow 'back' command
            allow_cancel: Whether to allow 'cancel' command

        Returns:
            Tuple of (input_value, action)
        """
        hints = []
        if allow_back:
            hints.append("'back'")
        if allow_cancel:
            hints.append("'cancel'")

        full_prompt = prompt
        if hints:
            full_prompt += f" (type {' or '.join(hints)} to navigate)"
        full_prompt += ": "

        while True:
            try:
                value = input(full_prompt).strip()
            except EOFError:
                return "", WizardAction.CANCEL

            # Check for navigation commands
            lower_value = value.lower()
            if allow_back and lower_value == self.BACK_COMMAND:
                return "", WizardAction.BACK
            if allow_cancel and lower_value == self.CANCEL_COMMAND:
                return "", WizardAction.CANCEL
            if lower_value == self.SKIP_COMMAND:
                return "", WizardAction.SKIP

            # Check empty
            if not value and not allow_empty:
                print("  Input cannot be empty.")
                continue

            # Validate
            if validator and not validator(value):
                print(f"  {error_message}")
                continue

            return value, WizardAction.CONTINUE

    def get_number(
        self,
        prompt: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        allow_float: bool = True,
        default: Optional[float] = None
    ) -> tuple[Optional[float], WizardAction]:
        """
        Get a numeric input from the user.

        Args:
            prompt: Prompt to display
            min_value: Optional minimum value
            max_value: Optional maximum value
            allow_float: Whether to allow floating point
            default: Default value if empty

        Returns:
            Tuple of (number, action)
        """
        range_hint = ""
        if min_value is not None and max_value is not None:
            range_hint = f" ({min_value}-{max_value})"
        elif min_value is not None:
            range_hint = f" (min: {min_value})"
        elif max_value is not None:
            range_hint = f" (max: {max_value})"

        default_hint = ""
        if default is not None:
            default_hint = f" [default: {default}]"

        full_prompt = f"{prompt}{range_hint}{default_hint}"

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

        value, action = self.get_input(
            full_prompt,
            validator=validate,
            error_message=f"Please enter a valid number{range_hint}",
            allow_empty=default is not None
        )

        if action != WizardAction.CONTINUE:
            return None, action

        if not value and default is not None:
            return default, WizardAction.CONTINUE

        num = float(value) if allow_float else int(value)
        return num, WizardAction.CONTINUE

    def get_confirmation(
        self,
        prompt: str,
        default: bool = False
    ) -> tuple[bool, WizardAction]:
        """
        Get a yes/no confirmation from the user.

        Args:
            prompt: Prompt to display
            default: Default value if empty

        Returns:
            Tuple of (confirmed, action)
        """
        default_hint = "[Y/n]" if default else "[y/N]"
        full_prompt = f"{prompt} {default_hint}"

        value, action = self.get_input(
            full_prompt,
            allow_empty=True
        )

        if action != WizardAction.CONTINUE:
            return False, action

        if not value:
            return default, WizardAction.CONTINUE

        return value.lower() in ("y", "yes", "true", "1"), WizardAction.CONTINUE

    # =========================================================================
    # Selection Methods
    # =========================================================================

    def select_one(
        self,
        prompt: str,
        options: list[tuple[str, T]],
        allow_back: bool = True,
        allow_cancel: bool = True
    ) -> tuple[Optional[T], WizardAction]:
        """
        Present a numbered menu for single selection.

        Args:
            prompt: Prompt to display
            options: List of (display_name, value) tuples
            allow_back: Whether to allow back navigation
            allow_cancel: Whether to allow cancellation

        Returns:
            Tuple of (selected_value, action)
        """
        print(f"\n{prompt}")
        print("-" * 40)

        for i, (display, _) in enumerate(options, 1):
            print(f"  {i}. {display}")

        print()

        def validate(value: str) -> bool:
            try:
                num = int(value)
                return 1 <= num <= len(options)
            except ValueError:
                return False

        value, action = self.get_input(
            "Enter number",
            validator=validate,
            error_message=f"Please enter a number between 1 and {len(options)}",
            allow_back=allow_back,
            allow_cancel=allow_cancel
        )

        if action != WizardAction.CONTINUE:
            return None, action

        index = int(value) - 1
        return options[index][1], WizardAction.CONTINUE

    def select_multiple(
        self,
        prompt: str,
        options: list[tuple[str, T]],
        min_selections: int = 0,
        max_selections: Optional[int] = None,
        allow_back: bool = True,
        allow_cancel: bool = True
    ) -> tuple[list[T], WizardAction]:
        """
        Present a numbered menu for multiple selection.

        Args:
            prompt: Prompt to display
            options: List of (display_name, value) tuples
            min_selections: Minimum number of selections required
            max_selections: Maximum number of selections allowed
            allow_back: Whether to allow back navigation
            allow_cancel: Whether to allow cancellation

        Returns:
            Tuple of (selected_values, action)
        """
        print(f"\n{prompt}")
        print("-" * 40)

        for i, (display, _) in enumerate(options, 1):
            print(f"  {i}. {display}")

        print()
        print("  Enter numbers separated by commas (e.g., 1,3,5)")
        if min_selections > 0:
            print(f"  (minimum {min_selections} selection(s))")
        print()

        def validate(value: str) -> bool:
            try:
                nums = [int(n.strip()) for n in value.split(",") if n.strip()]
                if len(nums) < min_selections:
                    return False
                if max_selections and len(nums) > max_selections:
                    return False
                return all(1 <= n <= len(options) for n in nums)
            except ValueError:
                return False

        value, action = self.get_input(
            "Enter numbers",
            validator=validate,
            error_message="Please enter valid numbers separated by commas",
            allow_empty=min_selections == 0,
            allow_back=allow_back,
            allow_cancel=allow_cancel
        )

        if action != WizardAction.CONTINUE:
            return [], action

        if not value:
            return [], WizardAction.CONTINUE

        indices = [int(n.strip()) - 1 for n in value.split(",") if n.strip()]
        return [options[i][1] for i in indices], WizardAction.CONTINUE

    def select_from_dict(
        self,
        prompt: str,
        options: dict[str, str],
        allow_back: bool = True,
        allow_cancel: bool = True
    ) -> tuple[Optional[str], WizardAction]:
        """
        Present a numbered menu from a dictionary.

        Args:
            prompt: Prompt to display
            options: Dict of value -> display_name
            allow_back: Whether to allow back navigation
            allow_cancel: Whether to allow cancellation

        Returns:
            Tuple of (selected_key, action)
        """
        option_list = [(display, key) for key, display in options.items()]
        return self.select_one(prompt, option_list, allow_back, allow_cancel)

    # =========================================================================
    # Display Methods
    # =========================================================================

    def print_header(self, title: str) -> None:
        """Print a section header."""
        print()
        print("=" * 50)
        print(f"  {title}")
        print("=" * 50)
        print()

    def print_step(self, step: int, total: int, description: str) -> None:
        """Print a step indicator."""
        print()
        print(f"Step {step}/{total}: {description}")
        print("-" * 40)

    def print_success(self, message: str) -> None:
        """Print a success message."""
        print(f"\n  SUCCESS: {message}\n")

    def print_error(self, message: str) -> None:
        """Print an error message."""
        print(f"\n  ERROR: {message}\n")

    def print_warning(self, message: str) -> None:
        """Print a warning message."""
        print(f"\n  WARNING: {message}\n")

    def print_info(self, message: str) -> None:
        """Print an info message."""
        print(f"  {message}")

    def print_list(self, items: list[str], title: Optional[str] = None) -> None:
        """Print a list of items."""
        if title:
            print(f"\n{title}:")
        for item in items:
            print(f"    - {item}")

    # =========================================================================
    # Navigation Helpers
    # =========================================================================

    def handle_cancel(self, wizard_name: str) -> WizardResult:
        """Handle wizard cancellation."""
        print(f"\n{wizard_name} wizard cancelled.")
        return WizardResult(
            success=False,
            message=f"{wizard_name} wizard cancelled",
            cancelled=True
        )

    def push_step(self, step_name: str) -> None:
        """Push a step onto the history stack."""
        self._step_history.append(step_name)

    def pop_step(self) -> Optional[str]:
        """Pop a step from the history stack."""
        if self._step_history:
            return self._step_history.pop()
        return None

    def can_go_back(self) -> bool:
        """Check if back navigation is possible."""
        return len(self._step_history) > 0
