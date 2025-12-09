"""
Color conversion utilities for Philips Hue.

Implements RGB/Hex to CIE 1931 xy color space conversion with gamut clamping.
Based on Philips Hue color conversion documentation.
"""

import math
import re
from typing import Optional

from .models import XYColor, Gamut, GAMUT_C


# Common color name mappings (RGB values)
COLOR_NAMES: dict[str, tuple[int, int, int]] = {
    # Primary colors
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),

    # Secondary colors
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),

    # Common variations
    "orange": (255, 165, 0),
    "pink": (255, 192, 203),
    "purple": (128, 0, 128),
    "violet": (238, 130, 238),
    "indigo": (75, 0, 130),
    "lime": (0, 255, 0),
    "teal": (0, 128, 128),
    "aqua": (0, 255, 255),
    "coral": (255, 127, 80),
    "salmon": (250, 128, 114),
    "gold": (255, 215, 0),
    "turquoise": (64, 224, 208),
    "lavender": (230, 230, 250),

    # Whites and neutrals
    "white": (255, 255, 255),
    "warm white": (255, 244, 229),
    "cool white": (255, 255, 255),
    "daylight": (255, 255, 251),
}

# Color temperature presets (in Kelvin)
TEMPERATURE_PRESETS: dict[str, int] = {
    "candle": 2000,
    "warm": 2700,
    "soft": 3000,
    "neutral": 4000,
    "cool": 5000,
    "daylight": 6500,
    "bright": 6500,
    "concentrate": 4200,
    "relax": 2700,
    "energize": 6500,
    "reading": 4000,
}


def _apply_gamma_correction(value: float) -> float:
    """Apply gamma correction to a linear RGB value (0-1)."""
    if value > 0.04045:
        return pow((value + 0.055) / 1.055, 2.4)
    return value / 12.92


def _reverse_gamma_correction(value: float) -> float:
    """Reverse gamma correction from linear to sRGB."""
    if value <= 0.0031308:
        return 12.92 * value
    return 1.055 * pow(value, 1 / 2.4) - 0.055


def _cross_product(p1: XYColor, p2: XYColor) -> float:
    """Calculate cross product of two points."""
    return p1.x * p2.y - p1.y * p2.x


def _get_closest_point_on_line(
    point: XYColor,
    line_start: XYColor,
    line_end: XYColor
) -> XYColor:
    """Find the closest point on a line segment to a given point."""
    # Vector from line_start to point
    ap_x = point.x - line_start.x
    ap_y = point.y - line_start.y

    # Vector from line_start to line_end
    ab_x = line_end.x - line_start.x
    ab_y = line_end.y - line_start.y

    # Calculate projection
    ab_squared = ab_x * ab_x + ab_y * ab_y
    if ab_squared == 0:
        return line_start

    t = (ap_x * ab_x + ap_y * ab_y) / ab_squared

    # Clamp t to [0, 1] to stay on segment
    t = max(0, min(1, t))

    return XYColor(
        x=line_start.x + t * ab_x,
        y=line_start.y + t * ab_y
    )


def _point_in_triangle(point: XYColor, gamut: Gamut) -> bool:
    """Check if a point is inside the gamut triangle."""
    # Using barycentric coordinates
    v0 = XYColor(gamut.blue.x - gamut.red.x, gamut.blue.y - gamut.red.y)
    v1 = XYColor(gamut.green.x - gamut.red.x, gamut.green.y - gamut.red.y)
    v2 = XYColor(point.x - gamut.red.x, point.y - gamut.red.y)

    dot00 = v0.x * v0.x + v0.y * v0.y
    dot01 = v0.x * v1.x + v0.y * v1.y
    dot02 = v0.x * v2.x + v0.y * v2.y
    dot11 = v1.x * v1.x + v1.y * v1.y
    dot12 = v1.x * v2.x + v1.y * v2.y

    inv_denom = 1 / (dot00 * dot11 - dot01 * dot01) if (dot00 * dot11 - dot01 * dot01) != 0 else 0
    u = (dot11 * dot02 - dot01 * dot12) * inv_denom
    v = (dot00 * dot12 - dot01 * dot02) * inv_denom

    return (u >= 0) and (v >= 0) and (u + v <= 1)


def _clamp_to_gamut(point: XYColor, gamut: Gamut) -> XYColor:
    """Clamp a point to the nearest edge of the gamut triangle if outside."""
    if _point_in_triangle(point, gamut):
        return point

    # Find closest point on each edge
    closest_red_green = _get_closest_point_on_line(point, gamut.red, gamut.green)
    closest_green_blue = _get_closest_point_on_line(point, gamut.green, gamut.blue)
    closest_blue_red = _get_closest_point_on_line(point, gamut.blue, gamut.red)

    # Calculate distances
    def distance(p1: XYColor, p2: XYColor) -> float:
        return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

    d_rg = distance(point, closest_red_green)
    d_gb = distance(point, closest_green_blue)
    d_br = distance(point, closest_blue_red)

    # Return the closest point
    min_dist = min(d_rg, d_gb, d_br)
    if min_dist == d_rg:
        return closest_red_green
    elif min_dist == d_gb:
        return closest_green_blue
    return closest_blue_red


def rgb_to_xy(
    r: int,
    g: int,
    b: int,
    gamut: Gamut = GAMUT_C
) -> XYColor:
    """
    Convert RGB values to CIE 1931 xy coordinates.

    Args:
        r: Red component (0-255)
        g: Green component (0-255)
        b: Blue component (0-255)
        gamut: Color gamut for clamping (default: Gamut C)

    Returns:
        XYColor with x, y coordinates clamped to the gamut
    """
    # Normalize to 0-1 range
    red = r / 255.0
    green = g / 255.0
    blue = b / 255.0

    # Apply gamma correction
    red = _apply_gamma_correction(red)
    green = _apply_gamma_correction(green)
    blue = _apply_gamma_correction(blue)

    # Convert to XYZ using Wide RGB D65 conversion matrix
    X = red * 0.664511 + green * 0.154324 + blue * 0.162028
    Y = red * 0.283881 + green * 0.668433 + blue * 0.047685
    Z = red * 0.000088 + green * 0.072310 + blue * 0.986039

    # Convert to xy
    total = X + Y + Z
    if total == 0:
        # Return white point for black
        return XYColor(x=0.3127, y=0.3290)

    x = X / total
    y = Y / total

    # Clamp to gamut
    return _clamp_to_gamut(XYColor(x=x, y=y), gamut)


def xy_to_rgb(xy: XYColor, brightness: float = 1.0, gamut: Gamut = GAMUT_C) -> tuple[int, int, int]:
    """
    Convert CIE xy coordinates back to RGB.

    Args:
        xy: XYColor coordinates
        brightness: Brightness level (0-1)
        gamut: Color gamut (default: Gamut C)

    Returns:
        Tuple of (r, g, b) values (0-255)
    """
    # Clamp to gamut first
    xy = _clamp_to_gamut(xy, gamut)

    # Calculate XYZ from xy and brightness
    x, y = xy.x, xy.y
    if y == 0:
        y = 0.00001

    Y = brightness
    X = (Y / y) * x
    Z = (Y / y) * (1 - x - y)

    # Convert XYZ to RGB using inverse matrix
    r = X * 1.656492 - Y * 0.354851 - Z * 0.255038
    g = -X * 0.707196 + Y * 1.655397 + Z * 0.036152
    b = X * 0.051713 - Y * 0.121364 + Z * 1.011530

    # Apply reverse gamma correction
    r = _reverse_gamma_correction(r)
    g = _reverse_gamma_correction(g)
    b = _reverse_gamma_correction(b)

    # Clamp to 0-1 and scale to 0-255
    def clamp_and_scale(v: float) -> int:
        return int(max(0, min(255, round(v * 255))))

    return (clamp_and_scale(r), clamp_and_scale(g), clamp_and_scale(b))


def hex_to_xy(hex_color: str, gamut: Gamut = GAMUT_C) -> XYColor:
    """
    Convert a hex color code to CIE xy coordinates.

    Args:
        hex_color: Hex color string (with or without #, 3 or 6 digits)
        gamut: Color gamut for clamping

    Returns:
        XYColor coordinates

    Raises:
        ValueError: If hex color format is invalid
    """
    # Remove # prefix if present
    hex_color = hex_color.lstrip('#')

    # Expand 3-digit hex to 6-digit
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)

    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")

    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
    except ValueError as e:
        raise ValueError(f"Invalid hex color: {hex_color}") from e

    return rgb_to_xy(r, g, b, gamut)


def kelvin_to_mirek(kelvin: int) -> int:
    """
    Convert color temperature from Kelvin to mirek (mired).

    Args:
        kelvin: Color temperature in Kelvin (1000-10000)

    Returns:
        Color temperature in mirek (100-1000)
    """
    if kelvin <= 0:
        raise ValueError("Kelvin must be positive")
    mirek = int(1_000_000 / kelvin)
    # Clamp to Hue's valid range
    return max(153, min(500, mirek))


def mirek_to_kelvin(mirek: int) -> int:
    """
    Convert color temperature from mirek to Kelvin.

    Args:
        mirek: Color temperature in mirek

    Returns:
        Color temperature in Kelvin
    """
    if mirek <= 0:
        raise ValueError("Mirek must be positive")
    return int(1_000_000 / mirek)


def parse_color(color_spec: str, gamut: Gamut = GAMUT_C) -> Optional[dict]:
    """
    Parse a color specification into a Hue API payload.

    Supports:
        - Named colors: "red", "blue", "warm white"
        - Hex codes: "#FF0000", "FF0000", "#F00"
        - RGB: "rgb(255, 0, 0)"
        - Temperature names: "warm", "cool", "daylight"
        - Kelvin values: "2700K", "6500k"

    Args:
        color_spec: Color specification string
        gamut: Color gamut for xy conversion

    Returns:
        Dict with either {"color": {"xy": {...}}} or {"color_temperature": {"mirek": ...}}
        Returns None if color cannot be parsed
    """
    color_spec = color_spec.strip().lower()

    # Check temperature presets first
    if color_spec in TEMPERATURE_PRESETS:
        kelvin = TEMPERATURE_PRESETS[color_spec]
        return {"color_temperature": {"mirek": kelvin_to_mirek(kelvin)}}

    # Check for Kelvin notation (e.g., "2700K")
    kelvin_match = re.match(r'^(\d{3,5})\s*k$', color_spec)
    if kelvin_match:
        kelvin = int(kelvin_match.group(1))
        if 1000 <= kelvin <= 10000:
            return {"color_temperature": {"mirek": kelvin_to_mirek(kelvin)}}

    # Check named colors
    if color_spec in COLOR_NAMES:
        r, g, b = COLOR_NAMES[color_spec]
        xy = rgb_to_xy(r, g, b, gamut)
        return {"color": {"xy": xy.to_dict()}}

    # Check hex format
    hex_match = re.match(r'^#?([0-9a-f]{3}|[0-9a-f]{6})$', color_spec)
    if hex_match:
        try:
            xy = hex_to_xy(hex_match.group(1), gamut)
            return {"color": {"xy": xy.to_dict()}}
        except ValueError:
            pass

    # Check RGB format: rgb(255, 0, 0) or 255,0,0
    rgb_match = re.match(r'^(?:rgb\s*\(\s*)?(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)?$', color_spec)
    if rgb_match:
        r, g, b = int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3))
        if all(0 <= v <= 255 for v in (r, g, b)):
            xy = rgb_to_xy(r, g, b, gamut)
            return {"color": {"xy": xy.to_dict()}}

    return None


def get_brightness_from_text(text: str) -> Optional[float]:
    """
    Extract brightness value from text.

    Args:
        text: Text that may contain brightness specification

    Returns:
        Brightness as percentage (0-100) or None if not found
    """
    text = text.lower()

    # Check for percentage
    pct_match = re.search(r'(\d{1,3})\s*%', text)
    if pct_match:
        value = int(pct_match.group(1))
        return max(1, min(100, value))

    # Check for word-based brightness
    brightness_words = {
        "full": 100, "max": 100, "maximum": 100, "bright": 100, "brightest": 100,
        "high": 80,
        "medium": 50, "half": 50, "mid": 50,
        "low": 25, "dim": 25,
        "minimum": 1, "min": 1, "lowest": 1, "dimmest": 1,
    }

    for word, value in brightness_words.items():
        if word in text.split():
            return value

    return None
