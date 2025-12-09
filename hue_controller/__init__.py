"""
Philips Hue Controller - A natural language interface for Hue Bridge API v2.

This package provides:
- Bridge discovery and authentication
- Device state management with caching
- Natural language command parsing
- Scene, group, and effect management
- Interactive wizards for configuration

Basic usage:
    from hue_controller import BridgeConnector, DeviceManager

    connector = BridgeConnector("config.json")
    dm = DeviceManager(connector)
    await dm.sync_state()

For advanced features:
    from hue_controller.managers import SceneManager, GroupManager, EffectsManager
    from hue_controller.wizards import SceneWizard, GroupWizard
"""

__version__ = "2.0.0"

# Core components
from .bridge_connector import BridgeConnector
from .device_manager import DeviceManager
from .command_interpreter import CommandInterpreter, CommandExecutor

# Managers
from .managers import (
    SceneManager,
    GroupManager,
    EffectsManager,
    EntertainmentManager,
)

# Wizards
from .wizards import (
    SceneWizard,
    GroupWizard,
    EntertainmentWizard,
)

# Models
from .models import (
    Light,
    Room,
    Zone,
    Scene,
    Device,
    GroupedLight,
    CommandResult,
    XYColor,
    # Scene models
    SceneAction,
    SceneLightAction,
    ScenePalette,
    CreateSceneRequest,
    UpdateSceneRequest,
    # Group models
    CreateRoomRequest,
    CreateZoneRequest,
    UpdateGroupRequest,
    # Effect models
    GradientConfig,
    TimedEffectConfig,
    SignalingConfig,
    # Entertainment models
    EntertainmentConfiguration,
    EntertainmentChannel,
    EntertainmentLocation,
)

# Exceptions
from .exceptions import (
    HueError,
    BridgeNotFoundError,
    AuthenticationError,
    LinkButtonNotPressedError,
    DeviceUnreachableError,
    RateLimitError,
    TargetNotFoundError,
    SceneNotFoundError,
    InvalidCommandError,
    APIError,
    # New exceptions
    SceneCreationError,
    SceneUpdateError,
    GroupCreationError,
    GroupUpdateError,
    InvalidArchetypeError,
    EffectNotSupportedError,
    GradientNotSupportedError,
    InvalidGradientError,
    EntertainmentError,
    EntertainmentCreationError,
    EntertainmentActivationError,
    WizardCancelledError,
    WizardValidationError,
)

# Constants
from .constants import (
    ROOM_ARCHETYPES,
    EFFECT_TYPES,
    TIMED_EFFECT_TYPES,
    GRADIENT_MODES,
    SIGNAL_TYPES,
    ENTERTAINMENT_TYPES,
)

__all__ = [
    # Core
    "BridgeConnector",
    "DeviceManager",
    "CommandInterpreter",
    "CommandExecutor",
    # Managers
    "SceneManager",
    "GroupManager",
    "EffectsManager",
    "EntertainmentManager",
    # Wizards
    "SceneWizard",
    "GroupWizard",
    "EntertainmentWizard",
    # Models
    "Light",
    "Room",
    "Zone",
    "Scene",
    "Device",
    "GroupedLight",
    "CommandResult",
    "XYColor",
    "SceneAction",
    "SceneLightAction",
    "ScenePalette",
    "CreateSceneRequest",
    "UpdateSceneRequest",
    "CreateRoomRequest",
    "CreateZoneRequest",
    "UpdateGroupRequest",
    "GradientConfig",
    "TimedEffectConfig",
    "SignalingConfig",
    "EntertainmentConfiguration",
    "EntertainmentChannel",
    "EntertainmentLocation",
    # Exceptions
    "HueError",
    "BridgeNotFoundError",
    "AuthenticationError",
    "LinkButtonNotPressedError",
    "DeviceUnreachableError",
    "RateLimitError",
    "TargetNotFoundError",
    "SceneNotFoundError",
    "InvalidCommandError",
    "APIError",
    "SceneCreationError",
    "SceneUpdateError",
    "GroupCreationError",
    "GroupUpdateError",
    "InvalidArchetypeError",
    "EffectNotSupportedError",
    "GradientNotSupportedError",
    "InvalidGradientError",
    "EntertainmentError",
    "EntertainmentCreationError",
    "EntertainmentActivationError",
    "WizardCancelledError",
    "WizardValidationError",
    # Constants
    "ROOM_ARCHETYPES",
    "EFFECT_TYPES",
    "TIMED_EFFECT_TYPES",
    "GRADIENT_MODES",
    "SIGNAL_TYPES",
    "ENTERTAINMENT_TYPES",
]
