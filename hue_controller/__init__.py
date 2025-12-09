"""
Philips Hue Controller - A natural language interface for Hue Bridge API v2.
"""

__version__ = "1.0.0"

from .bridge_connector import BridgeConnector
from .device_manager import DeviceManager
from .command_interpreter import CommandInterpreter
from .exceptions import (
    HueError,
    BridgeNotFoundError,
    AuthenticationError,
    DeviceUnreachableError,
    RateLimitError,
    TargetNotFoundError,
)

__all__ = [
    "BridgeConnector",
    "DeviceManager",
    "CommandInterpreter",
    "HueError",
    "BridgeNotFoundError",
    "AuthenticationError",
    "DeviceUnreachableError",
    "RateLimitError",
    "TargetNotFoundError",
]
