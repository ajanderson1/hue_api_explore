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
