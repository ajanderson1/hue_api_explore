"""
Custom exceptions for Hue Controller.
"""


class HueError(Exception):
    """Base exception for all Hue-related errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class BridgeNotFoundError(HueError):
    """Raised when no Hue Bridge can be discovered on the network."""

    def __init__(self, message: str = "No Hue Bridge found on the network"):
        super().__init__(message)


class AuthenticationError(HueError):
    """Raised when authentication with the bridge fails."""

    def __init__(self, message: str = "Authentication failed", details: dict | None = None):
        super().__init__(message, details)


class LinkButtonNotPressedError(AuthenticationError):
    """Raised when the link button was not pressed during authentication."""

    def __init__(self):
        super().__init__(
            "Link button not pressed. Press the button on your Hue Bridge and try again."
        )


class DeviceUnreachableError(HueError):
    """Raised when a device is not reachable (powered off at wall switch, etc.)."""

    def __init__(
        self,
        device_name: str,
        device_id: str,
        status: str = "disconnected"
    ):
        message = f"Device '{device_name}' is {status}"
        super().__init__(message, {"device_id": device_id, "status": status})
        self.device_name = device_name
        self.device_id = device_id
        self.status = status


class RateLimitError(HueError):
    """Raised when the bridge rate limit is exceeded."""

    def __init__(self, retry_after: int | None = None):
        message = "Rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message, {"retry_after": retry_after})
        self.retry_after = retry_after


class TargetNotFoundError(HueError):
    """Raised when a light, room, zone, or scene cannot be found."""

    def __init__(self, target_name: str, target_type: str = "target"):
        message = f"{target_type.capitalize()} '{target_name}' not found"
        super().__init__(message, {"target_name": target_name, "target_type": target_type})
        self.target_name = target_name
        self.target_type = target_type


class SceneNotFoundError(TargetNotFoundError):
    """Raised when a scene cannot be found."""

    def __init__(self, scene_name: str, room_name: str | None = None):
        if room_name:
            message = f"Scene '{scene_name}' not found in '{room_name}'"
        else:
            message = f"Scene '{scene_name}' not found"
        super(TargetNotFoundError, self).__init__(
            message,
            {"scene_name": scene_name, "room_name": room_name}
        )
        self.scene_name = scene_name
        self.room_name = room_name


class InvalidCommandError(HueError):
    """Raised when a command cannot be parsed."""

    def __init__(self, command: str, reason: str = "Could not understand command"):
        message = f"{reason}: '{command}'"
        super().__init__(message, {"command": command, "reason": reason})
        self.command = command
        self.reason = reason


class ConnectionError(HueError):
    """Raised when connection to the bridge fails."""

    def __init__(self, message: str, host: str | None = None):
        super().__init__(message, {"host": host})
        self.host = host


class APIError(HueError):
    """Raised when the Hue API returns an error response."""

    def __init__(
        self,
        message: str,
        status_code: int,
        endpoint: str,
        errors: list[dict] | None = None
    ):
        super().__init__(
            message,
            {
                "status_code": status_code,
                "endpoint": endpoint,
                "errors": errors or []
            }
        )
        self.status_code = status_code
        self.endpoint = endpoint
        self.errors = errors or []


# =============================================================================
# Scene-related Exceptions
# =============================================================================

class SceneCreationError(HueError):
    """Raised when scene creation fails."""

    def __init__(
        self,
        scene_name: str,
        reason: str,
        group_id: str | None = None
    ):
        message = f"Failed to create scene '{scene_name}': {reason}"
        super().__init__(message, {
            "scene_name": scene_name,
            "reason": reason,
            "group_id": group_id
        })
        self.scene_name = scene_name
        self.reason = reason
        self.group_id = group_id


class SceneUpdateError(HueError):
    """Raised when scene update fails."""

    def __init__(self, scene_id: str, reason: str):
        message = f"Failed to update scene '{scene_id}': {reason}"
        super().__init__(message, {"scene_id": scene_id, "reason": reason})
        self.scene_id = scene_id
        self.reason = reason


# =============================================================================
# Group-related Exceptions
# =============================================================================

class GroupCreationError(HueError):
    """Raised when room or zone creation fails."""

    def __init__(
        self,
        group_name: str,
        group_type: str,
        reason: str
    ):
        message = f"Failed to create {group_type} '{group_name}': {reason}"
        super().__init__(message, {
            "group_name": group_name,
            "group_type": group_type,
            "reason": reason
        })
        self.group_name = group_name
        self.group_type = group_type
        self.reason = reason


class GroupUpdateError(HueError):
    """Raised when room or zone update fails."""

    def __init__(
        self,
        group_id: str,
        group_type: str,
        reason: str
    ):
        message = f"Failed to update {group_type} '{group_id}': {reason}"
        super().__init__(message, {
            "group_id": group_id,
            "group_type": group_type,
            "reason": reason
        })
        self.group_id = group_id
        self.group_type = group_type
        self.reason = reason


class InvalidArchetypeError(HueError):
    """Raised when an invalid room archetype is specified."""

    def __init__(self, archetype: str, valid_archetypes: list[str] | None = None):
        message = f"Invalid archetype: '{archetype}'"
        super().__init__(message, {
            "archetype": archetype,
            "valid_archetypes": valid_archetypes
        })
        self.archetype = archetype
        self.valid_archetypes = valid_archetypes


# =============================================================================
# Effects-related Exceptions
# =============================================================================

class EffectNotSupportedError(HueError):
    """Raised when a light does not support the requested effect."""

    def __init__(
        self,
        effect: str,
        light_name: str,
        supported_effects: list[str] | None = None
    ):
        message = f"Effect '{effect}' not supported by '{light_name}'"
        super().__init__(message, {
            "effect": effect,
            "light_name": light_name,
            "supported_effects": supported_effects
        })
        self.effect = effect
        self.light_name = light_name
        self.supported_effects = supported_effects


class GradientNotSupportedError(HueError):
    """Raised when a light does not support gradients."""

    def __init__(self, light_name: str):
        message = f"Light '{light_name}' does not support gradients"
        super().__init__(message, {"light_name": light_name})
        self.light_name = light_name


class InvalidGradientError(HueError):
    """Raised when gradient configuration is invalid."""

    def __init__(self, reason: str):
        message = f"Invalid gradient configuration: {reason}"
        super().__init__(message, {"reason": reason})
        self.reason = reason


# =============================================================================
# Entertainment-related Exceptions
# =============================================================================

class EntertainmentError(HueError):
    """Base exception for entertainment configuration errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, details)


class EntertainmentCreationError(EntertainmentError):
    """Raised when entertainment configuration creation fails."""

    def __init__(self, name: str, reason: str):
        message = f"Failed to create entertainment configuration '{name}': {reason}"
        super().__init__(message, {"name": name, "reason": reason})
        self.name = name
        self.reason = reason


class EntertainmentActivationError(EntertainmentError):
    """Raised when entertainment configuration cannot be activated."""

    def __init__(self, config_id: str, reason: str):
        message = f"Failed to activate entertainment '{config_id}': {reason}"
        super().__init__(message, {"config_id": config_id, "reason": reason})
        self.config_id = config_id
        self.reason = reason


# =============================================================================
# Wizard-related Exceptions
# =============================================================================

class WizardCancelledError(HueError):
    """Raised when user cancels a wizard."""

    def __init__(self, wizard_name: str):
        message = f"{wizard_name} wizard cancelled"
        super().__init__(message, {"wizard_name": wizard_name})
        self.wizard_name = wizard_name


class WizardValidationError(HueError):
    """Raised when wizard input validation fails."""

    def __init__(self, field: str, reason: str):
        message = f"Invalid input for '{field}': {reason}"
        super().__init__(message, {"field": field, "reason": reason})
        self.field = field
        self.reason = reason
