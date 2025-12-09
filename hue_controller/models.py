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
