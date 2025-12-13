"""
Visual Feedback Components for Wizards

Provides ASCII-based visual representations for:
- Brightness bars
- Color swatches
- Temperature indicators
- Progress breadcrumbs
"""

from __future__ import annotations

from typing import Optional, Sequence

from rich.console import Console
from rich.text import Text
from rich.columns import Columns


console = Console()


# Color scheme matching wizard_ui.py
COLORS = {
    'primary': '#e94560',
    'info': '#00fff5',
    'success': '#00ff00',
    'warning': '#ffaa00',
    'muted': '#666666',
}


def render_brightness_bar(
    value: float,
    width: int = 30,
    show_percentage: bool = True,
) -> str:
    """
    Render an ASCII brightness bar.

    Args:
        value: Brightness value 0-100
        width: Width of the bar in characters
        show_percentage: Whether to show percentage label

    Returns:
        ASCII string representation of brightness

    Example:
        >>> render_brightness_bar(75)
        '█████████████████████░░░░░░░░░ 75%'
    """
    # Clamp value to valid range
    value = max(0, min(100, value))

    # Calculate filled portion
    filled = int(width * value / 100)
    empty = width - filled

    # Build bar
    bar = "█" * filled + "░" * empty

    if show_percentage:
        return f"{bar} {int(value)}%"
    return bar


def render_brightness_bar_colored(
    value: float,
    width: int = 30,
) -> Text:
    """
    Render a brightness bar with color gradient.

    Args:
        value: Brightness value 0-100
        width: Width of the bar in characters

    Returns:
        Rich Text object with colored bar
    """
    value = max(0, min(100, value))
    filled = int(width * value / 100)
    empty = width - filled

    text = Text()

    # Color the filled portion based on brightness level
    if value < 25:
        fill_color = "dim white"
    elif value < 50:
        fill_color = "white"
    elif value < 75:
        fill_color = "bright_white"
    else:
        fill_color = "bold bright_white"

    text.append("█" * filled, style=fill_color)
    text.append("░" * empty, style="dim")
    text.append(f" {int(value)}%", style="cyan")

    return text


def render_color_swatch(
    color_xy: tuple[float, float],
    size: int = 2,
) -> str:
    """
    Render a color swatch for XY color coordinates.

    Note: Terminal color approximation. Actual Hue colors depend on bulb gamut.

    Args:
        color_xy: Tuple of (x, y) CIE color coordinates
        size: Number of block characters to use

    Returns:
        Colored block characters as a string
    """
    x, y = color_xy

    # Convert XY to approximate RGB for terminal display
    # This is a simplified conversion - actual Hue colors are more complex
    r, g, b = xy_to_rgb(x, y)

    # Use rich markup for color
    hex_color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    block = "█" * size

    return f"[{hex_color}]{block}[/]"


def xy_to_rgb(x: float, y: float, brightness: float = 1.0) -> tuple[float, float, float]:
    """
    Convert CIE xy coordinates to approximate RGB values.

    This is a simplified conversion for display purposes.
    Actual bulb colors depend on gamut and hardware.

    Args:
        x: CIE x coordinate (0-1)
        y: CIE y coordinate (0-1)
        brightness: Brightness factor (0-1)

    Returns:
        Tuple of (r, g, b) values 0-1
    """
    # Handle edge cases
    if y == 0:
        y = 0.00001

    z = 1.0 - x - y

    # Convert to XYZ
    Y = brightness
    X = (Y / y) * x
    Z = (Y / y) * z

    # XYZ to sRGB matrix (D65 illuminant)
    r = X * 3.2406 - Y * 1.5372 - Z * 0.4986
    g = -X * 0.9689 + Y * 1.8758 + Z * 0.0415
    b = X * 0.0557 - Y * 0.2040 + Z * 1.0570

    # Apply gamma correction and clamp
    def gamma_correct(v: float) -> float:
        if v <= 0.0031308:
            return 12.92 * v
        return 1.055 * (v ** (1 / 2.4)) - 0.055

    r = max(0, min(1, gamma_correct(r)))
    g = max(0, min(1, gamma_correct(g)))
    b = max(0, min(1, gamma_correct(b)))

    return (r, g, b)


def render_temperature_swatch(
    mirek: int,
    size: int = 2,
) -> str:
    """
    Render a color swatch for color temperature (mirek).

    Args:
        mirek: Color temperature in mirek (153-500)
        size: Number of block characters to use

    Returns:
        Colored block characters approximating the temperature
    """
    # Convert mirek to approximate RGB
    # Lower mirek = cooler (bluer), higher mirek = warmer (yellower/redder)
    mirek = max(153, min(500, mirek))

    # Map mirek to color temperature feel
    # 153 (6500K) = cool daylight (slight blue)
    # 250 (4000K) = neutral white
    # 370 (2700K) = warm white (yellow/orange)
    # 500 (2000K) = very warm (orange/red)

    # Normalize mirek to 0-1 range (inverted so lower mirek = cooler)
    normalized = (mirek - 153) / (500 - 153)  # 0 = cool, 1 = warm

    # Generate color based on temperature
    if normalized < 0.3:
        # Cool daylight - slight blue tint
        r = 0.9 + normalized * 0.1
        g = 0.95 + normalized * 0.05
        b = 1.0
    elif normalized < 0.6:
        # Neutral to warm white
        r = 1.0
        g = 1.0 - (normalized - 0.3) * 0.3
        b = 1.0 - (normalized - 0.3) * 0.6
    else:
        # Warm to very warm
        r = 1.0
        g = 0.7 - (normalized - 0.6) * 0.5
        b = 0.4 - (normalized - 0.6) * 0.3

    # Clamp values
    r = max(0, min(1, r))
    g = max(0, min(1, g))
    b = max(0, min(1, b))

    hex_color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    block = "█" * size

    return f"[{hex_color}]{block}[/]"


def render_temperature_scale() -> str:
    """
    Render a color temperature scale from cool to warm.

    Returns:
        Rich-formatted string showing temperature gradient
    """
    parts = []
    temps = [153, 200, 250, 333, 370, 500]
    labels = ["6500K", "5000K", "4000K", "3000K", "2700K", "2000K"]

    for mirek, label in zip(temps, labels):
        swatch = render_temperature_swatch(mirek, size=3)
        parts.append(f"{swatch}")

    return " ".join(parts) + "\n" + "  ".join(labels)


def render_progress_breadcrumb(
    sections: Sequence[str],
    current: int,
    completed: Optional[set[int]] = None,
) -> str:
    """
    Render a breadcrumb-style progress indicator.

    Args:
        sections: List of section names
        current: Index of current section (0-based)
        completed: Set of indices for completed sections

    Returns:
        Rich-formatted string showing progress through sections

    Example:
        >>> render_progress_breadcrumb(["Basics", "Colors", "Review"], current=1)
        '✓ Basics → ● Colors → ○ Review'
    """
    if completed is None:
        completed = set(range(current))

    parts = []
    for i, section in enumerate(sections):
        if i < current or i in completed:
            # Completed
            parts.append(f"[{COLORS['success']}]✓ {section}[/]")
        elif i == current:
            # Current
            parts.append(f"[{COLORS['primary']}]● {section}[/]")
        else:
            # Pending
            parts.append(f"[{COLORS['muted']}]○ {section}[/]")

    return " → ".join(parts)


def render_progress_bar(
    current: int,
    total: int,
    width: int = 20,
    label: Optional[str] = None,
) -> str:
    """
    Render a simple progress bar.

    Args:
        current: Current step (1-based)
        total: Total number of steps
        width: Width of the bar
        label: Optional label to show

    Returns:
        Rich-formatted progress bar string
    """
    if total <= 0:
        return ""

    progress = min(current, total) / total
    filled = int(width * progress)
    empty = width - filled

    bar = f"[{COLORS['primary']}]{'━' * filled}[/]"
    bar += f"[{COLORS['muted']}]{'─' * empty}[/]"

    result = f"{bar} {current}/{total}"
    if label:
        result = f"{label}: {result}"

    return result


def render_light_state_indicator(
    is_on: bool,
    brightness: Optional[float] = None,
    reachable: bool = True,
) -> str:
    """
    Render an indicator showing light state.

    Args:
        is_on: Whether the light is on
        brightness: Brightness percentage (0-100)
        reachable: Whether the light is reachable/connected

    Returns:
        Rich-formatted status indicator
    """
    if not reachable:
        return f"[{COLORS['muted']}]◌ Unreachable[/]"

    if not is_on:
        return f"[{COLORS['muted']}]○ Off[/]"

    if brightness is not None:
        # Show brightness level with icon
        if brightness < 25:
            icon = "◔"
        elif brightness < 50:
            icon = "◑"
        elif brightness < 75:
            icon = "◕"
        else:
            icon = "●"
        return f"[{COLORS['success']}]{icon}[/] On ({int(brightness)}%)"

    return f"[{COLORS['success']}]● On[/]"


def display_color_palette(
    colors: list[tuple[float, float]],
    labels: Optional[list[str]] = None,
) -> None:
    """
    Display a palette of XY colors.

    Args:
        colors: List of (x, y) color coordinates
        labels: Optional labels for each color
    """
    swatches = []
    for i, (x, y) in enumerate(colors):
        swatch = render_color_swatch((x, y), size=3)
        if labels and i < len(labels):
            swatches.append(f"{swatch} {labels[i]}")
        else:
            swatches.append(swatch)

    console.print(Columns(swatches, equal=True))


def display_temperature_presets() -> None:
    """Display a visual guide to color temperature presets."""
    console.print("\n[bold]Color Temperature Guide[/bold]\n")

    presets = [
        (153, "Daylight", "Energizing, like midday sun"),
        (182, "Cool White", "Crisp and clean"),
        (250, "Neutral", "Balanced, for general use"),
        (333, "Soft White", "Relaxed, cozy feel"),
        (370, "Warm White", "Like incandescent bulbs"),
        (500, "Candlelight", "Very warm, intimate"),
    ]

    for mirek, name, description in presets:
        swatch = render_temperature_swatch(mirek, size=2)
        kelvin = int(1_000_000 / mirek)
        console.print(f"  {swatch} [bold]{name}[/bold] ({kelvin}K / {mirek} mirek)")
        console.print(f"      [{COLORS['muted']}]{description}[/]")

    console.print()
