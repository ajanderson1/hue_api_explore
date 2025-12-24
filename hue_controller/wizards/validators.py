"""
User-Friendly Validators for Wizard Inputs

Provides validation functions that return helpful, human-readable error messages
instead of technical jargon. Designed for use with questionary's validate parameter.
"""

from __future__ import annotations

from typing import Callable, Optional, Union


# Type alias for validator return type
ValidatorResult = Union[bool, str]


def validate_mirek(value: str) -> ValidatorResult:
    """
    Validate a mirek (color temperature) value.

    Args:
        value: String input to validate

    Returns:
        True if valid, or error message string if invalid
    """
    if not value.strip():
        return "Please enter a color temperature value."

    try:
        mirek = int(value)
    except ValueError:
        return "Please enter a number (e.g., 370 for warm white)."

    if mirek < 153:
        return (
            f"Value {mirek} is too low. Minimum is 153 (6500K, cool daylight). "
            "Try 153-200 for energizing light."
        )
    if mirek > 500:
        return (
            f"Value {mirek} is too high. Maximum is 500 (2000K, candlelight). "
            "Try 370-500 for cozy, warm light."
        )

    return True


def validate_kelvin(value: str) -> ValidatorResult:
    """
    Validate a Kelvin color temperature value.

    Args:
        value: String input to validate (with or without 'K' suffix)

    Returns:
        True if valid, or error message string if invalid
    """
    if not value.strip():
        return "Please enter a color temperature in Kelvin (e.g., 2700K)."

    # Remove 'K' suffix if present
    clean_value = value.strip().upper().rstrip('K')

    try:
        kelvin = int(clean_value)
    except ValueError:
        return "Please enter a number like 2700 or 2700K."

    if kelvin < 2000:
        return (
            f"{kelvin}K is too low. Minimum is 2000K (very warm, like candlelight). "
            "Most people prefer 2700K-3000K for cozy lighting."
        )
    if kelvin > 6500:
        return (
            f"{kelvin}K is too high. Maximum is 6500K (cool daylight). "
            "Try 5000K-6500K for energizing, task lighting."
        )

    return True


def validate_brightness(value: str) -> ValidatorResult:
    """
    Validate a brightness percentage value.

    Args:
        value: String input to validate

    Returns:
        True if valid, or error message string if invalid
    """
    if not value.strip():
        return "Please enter a brightness percentage (0-100)."

    # Handle percentage sign
    clean_value = value.strip().rstrip('%')

    try:
        brightness = float(clean_value)
    except ValueError:
        return "Please enter a number from 0 to 100 (e.g., 75 or 75%)."

    if brightness < 0:
        return "Brightness cannot be negative. Use 0 for minimum (light stays on but dim)."
    if brightness > 100:
        return f"{brightness}% is over 100%. Maximum brightness is 100%."

    return True


def validate_scene_name(value: str) -> ValidatorResult:
    """
    Validate a scene name.

    Args:
        value: String input to validate

    Returns:
        True if valid, or error message string if invalid
    """
    if not value or not value.strip():
        return "Please enter a name for your scene."

    name = value.strip()

    if len(name) < 1:
        return "Scene name must be at least 1 character."

    if len(name) > 32:
        return (
            f"Scene name is too long ({len(name)} characters). "
            f"Maximum is 32 characters. Try shortening to: '{name[:29]}...'"
        )

    # Check for problematic characters
    if name.startswith(' ') or name.endswith(' '):
        return "Scene name should not start or end with spaces."

    return True


def validate_xy_color(x_str: str, y_str: str) -> ValidatorResult:
    """
    Validate CIE xy color coordinates.

    Args:
        x_str: X coordinate as string
        y_str: Y coordinate as string

    Returns:
        True if valid, or error message string if invalid
    """
    try:
        x = float(x_str)
        y = float(y_str)
    except ValueError:
        return "Please enter decimal values for x and y (e.g., 0.675 and 0.322 for red)."

    if x < 0 or x > 1:
        return f"X coordinate ({x}) must be between 0 and 1. Try '?xy color' for example values."

    if y < 0 or y > 1:
        return f"Y coordinate ({y}) must be between 0 and 1. Try '?xy color' for example values."

    # Check if in visible gamut (rough approximation)
    if y < 0.01:
        return "Y coordinate is too low. This would result in an invisible/non-displayable color."

    return True


def validate_xy_string(value: str) -> ValidatorResult:
    """
    Validate CIE xy color as a comma-separated string.

    Args:
        value: String like "0.675, 0.322" or "0.675,0.322"

    Returns:
        True if valid, or error message string if invalid
    """
    if not value.strip():
        return "Please enter x,y coordinates (e.g., 0.675, 0.322)."

    parts = value.replace(' ', '').split(',')

    if len(parts) != 2:
        return "Please enter two values separated by comma (e.g., 0.5, 0.4)."

    return validate_xy_color(parts[0], parts[1])


def validate_transition_ms(value: str) -> ValidatorResult:
    """
    Validate a transition duration in milliseconds.

    Args:
        value: String input to validate

    Returns:
        True if valid, or error message string if invalid
    """
    if not value.strip():
        return "Please enter a transition time in milliseconds."

    # Handle common suffixes
    clean_value = value.strip().lower()
    multiplier = 1

    if clean_value.endswith('ms'):
        clean_value = clean_value[:-2]
    elif clean_value.endswith('s') and not clean_value.endswith('ms'):
        clean_value = clean_value[:-1]
        multiplier = 1000
    elif clean_value.endswith('m'):
        clean_value = clean_value[:-1]
        multiplier = 60000

    try:
        ms = int(float(clean_value) * multiplier)
    except ValueError:
        return "Please enter a number (e.g., 400 for 400ms, or 2s for 2 seconds)."

    if ms < 0:
        return "Transition time cannot be negative. Use 0 for instant changes."

    # Max is about 109 minutes
    max_ms = 6_553_500
    if ms > max_ms:
        return (
            f"{ms}ms is too long. Maximum transition is about 109 minutes ({max_ms}ms). "
            "For longer effects, consider using timed effects like sunrise/sunset."
        )

    return True


def validate_speed(value: str) -> ValidatorResult:
    """
    Validate a dynamic scene speed value.

    Args:
        value: String input to validate (0.0 to 1.0)

    Returns:
        True if valid, or error message string if invalid
    """
    if not value.strip():
        return "Please enter a speed value from 0 to 1."

    try:
        speed = float(value)
    except ValueError:
        return "Please enter a decimal number from 0 to 1 (e.g., 0.5 for medium speed)."

    if speed < 0:
        return "Speed cannot be negative. Use 0 for slowest color cycling."
    if speed > 1:
        return f"Speed {speed} is too high. Maximum is 1.0 (fastest color cycling)."

    return True


def validate_gradient_points(value: str) -> ValidatorResult:
    """
    Validate number of gradient color points.

    Args:
        value: String input to validate

    Returns:
        True if valid, or error message string if invalid
    """
    if not value.strip():
        return "Please enter the number of color points (2-5)."

    try:
        points = int(value)
    except ValueError:
        return "Please enter a whole number from 2 to 5."

    if points < 2:
        return "Gradients need at least 2 color points to blend between."
    if points > 5:
        return "Maximum 5 color points per gradient. Try reducing for simpler effects."

    return True


def validate_positive_int(value: str, field_name: str = "value") -> ValidatorResult:
    """
    Validate a positive integer.

    Args:
        value: String input to validate
        field_name: Name of field for error messages

    Returns:
        True if valid, or error message string if invalid
    """
    if not value.strip():
        return f"Please enter a {field_name}."

    try:
        num = int(value)
    except ValueError:
        return f"Please enter a whole number for {field_name}."

    if num <= 0:
        return f"{field_name.capitalize()} must be greater than 0."

    return True


def validate_non_empty(value: str, field_name: str = "value") -> ValidatorResult:
    """
    Validate that a string is not empty.

    Args:
        value: String input to validate
        field_name: Name of field for error messages

    Returns:
        True if valid, or error message string if invalid
    """
    if not value or not value.strip():
        return f"Please enter a {field_name}."
    return True


# Factory functions for creating validators with parameters


def create_range_validator(
    min_val: float,
    max_val: float,
    field_name: str = "value",
    allow_float: bool = True,
) -> Callable[[str], ValidatorResult]:
    """
    Create a validator for a numeric range.

    Args:
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        field_name: Name of field for error messages
        allow_float: Whether to allow decimal values

    Returns:
        Validator function
    """
    def validator(value: str) -> ValidatorResult:
        if not value.strip():
            return f"Please enter a {field_name} ({min_val}-{max_val})."

        try:
            num = float(value) if allow_float else int(value)
        except ValueError:
            type_hint = "number" if allow_float else "whole number"
            return f"Please enter a {type_hint} for {field_name}."

        if num < min_val:
            return f"{field_name.capitalize()} must be at least {min_val}."
        if num > max_val:
            return f"{field_name.capitalize()} cannot exceed {max_val}."

        return True

    return validator


def create_length_validator(
    min_length: int = 1,
    max_length: int = 100,
    field_name: str = "value",
) -> Callable[[str], ValidatorResult]:
    """
    Create a validator for string length.

    Args:
        min_length: Minimum string length
        max_length: Maximum string length
        field_name: Name of field for error messages

    Returns:
        Validator function
    """
    def validator(value: str) -> ValidatorResult:
        if not value:
            if min_length > 0:
                return f"Please enter a {field_name}."
            return True

        length = len(value.strip())

        if length < min_length:
            return f"{field_name.capitalize()} must be at least {min_length} character(s)."
        if length > max_length:
            return (
                f"{field_name.capitalize()} is too long ({length} characters). "
                f"Maximum is {max_length}."
            )

        return True

    return validator


# Questionary-compatible validator wrappers


def questionary_validator(
    validator_func: Callable[[str], ValidatorResult],
) -> Callable[[str], Union[bool, str]]:
    """
    Wrap a validator function for use with questionary.

    Questionary expects validators to return True for valid input,
    or a string error message for invalid input.

    Args:
        validator_func: Validator function to wrap

    Returns:
        Questionary-compatible validator
    """
    def wrapper(value: str) -> Union[bool, str]:
        result = validator_func(value)
        if result is True:
            return True
        return str(result)

    return wrapper
