"""
Data models for Hue API v2 resources.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ConnectivityStatus(Enum):
    """Zigbee connectivity status for devices."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTIVITY_ISSUE = "connectivity_issue"
    UNIDIRECTIONAL_INCOMING = "unidirectional_incoming"
    PENDING_DISCOVERY = "pending_discovery"
    UNKNOWN = "unknown"


class GamutType(Enum):
    """Color gamut types supported by Hue lights."""
    A = "A"  # Early Philips color-only products
    B = "B"  # First Hue color products
    C = "C"  # Modern Hue white and color ambiance
    OTHER = "other"


@dataclass
class XYColor:
    """CIE 1931 xy color coordinates."""
    x: float
    y: float

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y}


@dataclass
class Gamut:
    """Color gamut defined by RGB triangle vertices in CIE xy space."""
    red: XYColor
    green: XYColor
    blue: XYColor


# Standard Hue gamuts
GAMUT_A = Gamut(
    red=XYColor(0.704, 0.296),
    green=XYColor(0.2151, 0.7106),
    blue=XYColor(0.138, 0.08)
)

GAMUT_B = Gamut(
    red=XYColor(0.675, 0.322),
    green=XYColor(0.4091, 0.518),
    blue=XYColor(0.167, 0.04)
)

GAMUT_C = Gamut(
    red=XYColor(0.6915, 0.3083),
    green=XYColor(0.17, 0.7),
    blue=XYColor(0.1532, 0.0475)
)

GAMUT_MAP = {
    GamutType.A: GAMUT_A,
    GamutType.B: GAMUT_B,
    GamutType.C: GAMUT_C,
}


@dataclass
class ResourceReference:
    """Reference to another Hue resource."""
    rid: str  # Resource UUID
    rtype: str  # Resource type (light, room, device, etc.)


@dataclass
class Light:
    """Represents a Hue light service."""
    id: str
    name: str
    id_v1: Optional[str] = None
    owner_id: Optional[str] = None  # Device that owns this light

    # State
    is_on: bool = False
    brightness: float = 100.0  # 0-100 percentage

    # Color capabilities
    supports_color: bool = False
    supports_color_temperature: bool = False
    color_xy: Optional[XYColor] = None
    color_temperature_mirek: Optional[int] = None
    mirek_min: Optional[int] = None
    mirek_max: Optional[int] = None
    gamut_type: GamutType = GamutType.C
    gamut: Optional[Gamut] = None

    # Connectivity (updated from zigbee_connectivity)
    connectivity_status: ConnectivityStatus = ConnectivityStatus.UNKNOWN

    @property
    def is_reachable(self) -> bool:
        return self.connectivity_status == ConnectivityStatus.CONNECTED

    def get_gamut(self) -> Gamut:
        """Return the appropriate gamut for color conversion."""
        if self.gamut:
            return self.gamut
        return GAMUT_MAP.get(self.gamut_type, GAMUT_C)


@dataclass
class Device:
    """Represents a physical Hue device."""
    id: str
    name: str
    id_v1: Optional[str] = None
    model_id: Optional[str] = None
    manufacturer: Optional[str] = None
    product_name: Optional[str] = None
    software_version: Optional[str] = None

    # Services this device provides
    service_ids: list[ResourceReference] = field(default_factory=list)

    # Connectivity
    zigbee_connectivity_id: Optional[str] = None
    connectivity_status: ConnectivityStatus = ConnectivityStatus.UNKNOWN


@dataclass
class Room:
    """Represents a Hue room (groups devices by physical location)."""
    id: str
    name: str
    id_v1: Optional[str] = None
    archetype: Optional[str] = None

    # Children are devices
    children: list[ResourceReference] = field(default_factory=list)

    # Services (including grouped_light)
    services: list[ResourceReference] = field(default_factory=list)

    # Cached grouped_light ID for quick access
    grouped_light_id: Optional[str] = None

    @property
    def device_ids(self) -> list[str]:
        """Get IDs of devices in this room."""
        return [ref.rid for ref in self.children if ref.rtype == "device"]


@dataclass
class Zone:
    """Represents a Hue zone (groups services by any criteria)."""
    id: str
    name: str
    id_v1: Optional[str] = None
    archetype: Optional[str] = None

    # Children can be lights directly
    children: list[ResourceReference] = field(default_factory=list)

    # Services (including grouped_light)
    services: list[ResourceReference] = field(default_factory=list)

    # Cached grouped_light ID for quick access
    grouped_light_id: Optional[str] = None

    @property
    def light_ids(self) -> list[str]:
        """Get IDs of lights in this zone."""
        return [ref.rid for ref in self.children if ref.rtype == "light"]


@dataclass
class GroupedLight:
    """Represents a grouped_light service for controlling rooms/zones."""
    id: str
    id_v1: Optional[str] = None
    owner_id: Optional[str] = None  # Room or zone that owns this

    # Aggregate state
    is_on: bool = False
    brightness: float = 100.0


@dataclass
class Scene:
    """Represents a Hue scene."""
    id: str
    name: str
    id_v1: Optional[str] = None

    # Group this scene belongs to
    group_id: Optional[str] = None
    group_type: Optional[str] = None  # "room" or "zone"

    # Scene metadata
    image_id: Optional[str] = None
    speed: float = 0.5  # Dynamic palette speed
    auto_dynamic: bool = False


@dataclass
class CommandResult:
    """Result of executing a command."""
    success: bool
    message: str
    target_name: Optional[str] = None
    affected_lights: int = 0
    unreachable_lights: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


# =============================================================================
# Scene Action Models (for scene creation/editing)
# =============================================================================

@dataclass
class GradientPoint:
    """A single point in a gradient configuration."""
    color: XYColor

    def to_dict(self) -> dict:
        return {"color": {"xy": self.color.to_dict()}}


@dataclass
class GradientConfig:
    """Gradient configuration for gradient-capable lights."""
    points: list[XYColor]  # 2-5 color points
    mode: str = "interpolated_palette"

    def to_dict(self) -> dict:
        return {
            "points": [{"color": {"xy": p.to_dict()}} for p in self.points],
            "mode": self.mode,
        }


@dataclass
class SceneLightAction:
    """Per-light settings within a scene."""
    on: Optional[bool] = None
    brightness: Optional[float] = None  # 0-100
    color_xy: Optional[XYColor] = None
    color_temperature_mirek: Optional[int] = None
    gradient: Optional[GradientConfig] = None
    effect: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to API payload format."""
        result = {}
        if self.on is not None:
            result["on"] = {"on": self.on}
        if self.brightness is not None:
            result["dimming"] = {"brightness": self.brightness}
        if self.color_xy is not None:
            result["color"] = {"xy": self.color_xy.to_dict()}
        if self.color_temperature_mirek is not None:
            result["color_temperature"] = {"mirek": self.color_temperature_mirek}
        if self.gradient is not None:
            result["gradient"] = self.gradient.to_dict()
        if self.effect is not None:
            result["effects"] = {"effect": self.effect}
        return result


@dataclass
class SceneAction:
    """Action within a scene targeting a light or grouped_light."""
    target_rid: str
    target_rtype: str  # "light" or "grouped_light"
    action: SceneLightAction

    def to_dict(self) -> dict:
        return {
            "target": {
                "rid": self.target_rid,
                "rtype": self.target_rtype,
            },
            "action": self.action.to_dict(),
        }


@dataclass
class ScenePaletteColor:
    """Color entry in a scene palette."""
    color: XYColor
    dimming: Optional[float] = None  # 0-100

    def to_dict(self) -> dict:
        result = {"color": {"xy": self.color.to_dict()}}
        if self.dimming is not None:
            result["dimming"] = {"brightness": self.dimming}
        return result


@dataclass
class ScenePaletteColorTemp:
    """Color temperature entry in a scene palette."""
    color_temperature_mirek: int
    dimming: Optional[float] = None  # 0-100

    def to_dict(self) -> dict:
        result = {"color_temperature": {"mirek": self.color_temperature_mirek}}
        if self.dimming is not None:
            result["dimming"] = {"brightness": self.dimming}
        return result


@dataclass
class ScenePalette:
    """Color palette for dynamic scenes."""
    colors: list[ScenePaletteColor] = field(default_factory=list)
    color_temperatures: list[ScenePaletteColorTemp] = field(default_factory=list)
    dimming: list[float] = field(default_factory=list)  # Brightness levels

    def to_dict(self) -> dict:
        result = {}
        if self.colors:
            result["color"] = [c.to_dict() for c in self.colors]
        if self.color_temperatures:
            result["color_temperature"] = [ct.to_dict() for ct in self.color_temperatures]
        if self.dimming:
            result["dimming"] = [{"brightness": d} for d in self.dimming]
        return result


# =============================================================================
# Scene Request Models
# =============================================================================

@dataclass
class CreateSceneRequest:
    """Request to create a new scene."""
    name: str
    group_id: str
    group_type: str = "room"  # "room" or "zone"
    actions: list[SceneAction] = field(default_factory=list)
    palette: Optional[ScenePalette] = None
    speed: float = 0.5  # 0.0-1.0, dynamic palette speed
    auto_dynamic: bool = False

    def to_dict(self) -> dict:
        result = {
            "metadata": {"name": self.name},
            "group": {"rid": self.group_id, "rtype": self.group_type},
            "speed": self.speed,
            "auto_dynamic": self.auto_dynamic,
        }
        if self.actions:
            result["actions"] = [a.to_dict() for a in self.actions]
        if self.palette:
            result["palette"] = self.palette.to_dict()
        return result


@dataclass
class UpdateSceneRequest:
    """Request to update an existing scene."""
    scene_id: str
    name: Optional[str] = None
    actions: Optional[list[SceneAction]] = None
    palette: Optional[ScenePalette] = None
    speed: Optional[float] = None
    auto_dynamic: Optional[bool] = None

    def to_dict(self) -> dict:
        result = {}
        if self.name is not None:
            result["metadata"] = {"name": self.name}
        if self.actions is not None:
            result["actions"] = [a.to_dict() for a in self.actions]
        if self.palette is not None:
            result["palette"] = self.palette.to_dict()
        if self.speed is not None:
            result["speed"] = self.speed
        if self.auto_dynamic is not None:
            result["auto_dynamic"] = self.auto_dynamic
        return result


@dataclass
class RecallSceneRequest:
    """Request to recall (activate) a scene."""
    scene_id: str
    action: str = "active"  # "active", "dynamic_palette", "static"
    duration_ms: Optional[int] = None  # Transition duration
    brightness: Optional[float] = None  # Override brightness

    def to_dict(self) -> dict:
        result = {"recall": {"action": self.action}}
        if self.duration_ms is not None:
            result["recall"]["duration"] = self.duration_ms
        if self.brightness is not None:
            result["recall"]["dimming"] = {"brightness": self.brightness}
        return result


# =============================================================================
# Group Request Models
# =============================================================================

@dataclass
class CreateRoomRequest:
    """Request to create a new room."""
    name: str
    archetype: str  # From ROOM_ARCHETYPES
    children: list[str] = field(default_factory=list)  # Device IDs to add

    def to_dict(self) -> dict:
        result = {
            "metadata": {"name": self.name, "archetype": self.archetype},
            "children": [{"rid": rid, "rtype": "device"} for rid in self.children],
        }
        return result


@dataclass
class CreateZoneRequest:
    """Request to create a new zone."""
    name: str
    archetype: str  # From ROOM_ARCHETYPES
    children: list[str] = field(default_factory=list)  # Light service IDs

    def to_dict(self) -> dict:
        result = {
            "metadata": {"name": self.name, "archetype": self.archetype},
            "children": [{"rid": rid, "rtype": "light"} for rid in self.children],
        }
        return result


@dataclass
class UpdateGroupRequest:
    """Request to update a room or zone."""
    group_id: str
    name: Optional[str] = None
    archetype: Optional[str] = None
    children_to_add: list[str] = field(default_factory=list)
    children_to_remove: list[str] = field(default_factory=list)

    def to_dict(self, is_room: bool = True) -> dict:
        result = {}
        if self.name is not None or self.archetype is not None:
            result["metadata"] = {}
            if self.name is not None:
                result["metadata"]["name"] = self.name
            if self.archetype is not None:
                result["metadata"]["archetype"] = self.archetype
        # Note: Children updates require separate API calls
        return result


# =============================================================================
# Effects Models
# =============================================================================

@dataclass
class TimedEffectConfig:
    """Configuration for timed effects (sunrise/sunset)."""
    effect: str  # "sunrise", "sunset", or "no_effect"
    duration_ms: int = 1800000  # Default 30 minutes

    def to_dict(self) -> dict:
        return {
            "timed_effects": {
                "effect": self.effect,
                "duration": self.duration_ms,
            }
        }


@dataclass
class SignalingConfig:
    """Configuration for light signaling."""
    signal: str  # "no_signal", "on_off", "on_off_color", "alternating"
    duration_ms: int = 2000
    colors: list[XYColor] = field(default_factory=list)

    def to_dict(self) -> dict:
        result = {
            "signaling": {
                "signal_values": [{
                    "signal": self.signal,
                    "duration": self.duration_ms,
                }]
            }
        }
        if self.colors and self.signal in ("on_off_color", "alternating"):
            result["signaling"]["signal_values"][0]["color"] = {
                "xy": self.colors[0].to_dict()
            }
        return result


@dataclass
class EffectConfig:
    """Configuration for basic light effects."""
    effect: str  # From EFFECT_TYPES

    def to_dict(self) -> dict:
        return {"effects": {"effect": self.effect}}


# =============================================================================
# Entertainment Models
# =============================================================================

@dataclass
class EntertainmentLocation:
    """Position of a light in entertainment configuration space."""
    service_id: str
    position: tuple[float, float, float]  # x, y, z coordinates

    def to_dict(self) -> dict:
        return {
            "service": {"rid": self.service_id, "rtype": "entertainment"},
            "position": {"x": self.position[0], "y": self.position[1], "z": self.position[2]},
        }


@dataclass
class EntertainmentChannel:
    """Channel assignment in entertainment configuration."""
    channel_id: int
    position: tuple[float, float, float]  # x, y, z in CIE space
    members: list[str] = field(default_factory=list)  # Light service IDs

    def to_dict(self) -> dict:
        return {
            "channel_id": self.channel_id,
            "position": {"x": self.position[0], "y": self.position[1], "z": self.position[2]},
            "members": [{"service": {"rid": rid, "rtype": "entertainment"}} for rid in self.members],
        }


@dataclass
class EntertainmentConfiguration:
    """Entertainment area configuration."""
    id: str
    name: str
    configuration_type: str  # "screen", "monitor", "music", "3dspace", "other"
    status: str = "inactive"  # "inactive" or "active"
    stream_proxy_mode: str = "auto"  # "auto" or "manual"
    channels: list[EntertainmentChannel] = field(default_factory=list)
    locations: list[EntertainmentLocation] = field(default_factory=list)
    light_services: list[str] = field(default_factory=list)  # Light service IDs


@dataclass
class CreateEntertainmentRequest:
    """Request to create an entertainment configuration."""
    name: str
    configuration_type: str
    light_services: list[str] = field(default_factory=list)
    locations: list[EntertainmentLocation] = field(default_factory=list)

    def to_dict(self) -> dict:
        result = {
            "metadata": {"name": self.name},
            "configuration_type": self.configuration_type,
            "light_services": [{"rid": rid, "rtype": "light"} for rid in self.light_services],
        }
        if self.locations:
            result["locations"] = {"service_locations": [loc.to_dict() for loc in self.locations]}
        return result


# =============================================================================
# Extended Scene Model (with full action details)
# =============================================================================

@dataclass
class SceneDetails(Scene):
    """Extended scene model with full action details."""
    actions: list[SceneAction] = field(default_factory=list)
    palette: Optional[ScenePalette] = None


# Type alias for targets that can receive commands
Target = Light | Room | Zone
