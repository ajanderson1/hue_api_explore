"""
Rich-based Visual Components for Wizards

Provides styled panels, tables, progress indicators, and status messages
using the Rich library for consistent visual output.
"""

from dataclasses import dataclass
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.text import Text
from rich.style import Style
from rich import box


console = Console()


@dataclass
class LightConfig:
    """Configuration state for a single light."""
    name: str
    enabled: bool = True
    on: bool = True
    brightness: float = 100.0
    color_mode: str = "temperature"  # "temperature", "color", "gradient", "effect"
    color_temp_kelvin: Optional[int] = 4000
    color_hex: Optional[str] = None
    color_xy: Optional[tuple[float, float]] = None
    effect: Optional[str] = None
    transition_ms: int = 400


class WizardPanel:
    """
    Styled panel for wizard sections and messages.
    """

    @staticmethod
    def header(title: str, subtitle: Optional[str] = None) -> None:
        """Display a wizard header panel."""
        content = Text()
        content.append(title, style="bold white")
        if subtitle:
            content.append(f"\n{subtitle}", style="dim")

        panel = Panel(
            content,
            box=box.ROUNDED,
            border_style="bright_blue",
            padding=(1, 2),
        )
        console.print(panel)

    @staticmethod
    def section(title: str, content: str) -> None:
        """Display a section panel with title."""
        panel = Panel(
            content,
            title=f"[bold]{title}[/bold]",
            box=box.ROUNDED,
            border_style="blue",
            padding=(0, 1),
        )
        console.print(panel)

    @staticmethod
    def info(message: str) -> None:
        """Display an info message panel."""
        panel = Panel(
            message,
            box=box.ROUNDED,
            border_style="cyan",
            padding=(0, 1),
        )
        console.print(panel)

    @staticmethod
    def success(message: str) -> None:
        """Display a success message panel."""
        panel = Panel(
            f"[green]{message}[/green]",
            box=box.ROUNDED,
            border_style="green",
            padding=(0, 1),
        )
        console.print(panel)

    @staticmethod
    def error(message: str) -> None:
        """Display an error message panel."""
        panel = Panel(
            f"[red]{message}[/red]",
            box=box.ROUNDED,
            border_style="red",
            padding=(0, 1),
        )
        console.print(panel)

    @staticmethod
    def warning(message: str) -> None:
        """Display a warning message panel."""
        panel = Panel(
            f"[yellow]{message}[/yellow]",
            box=box.ROUNDED,
            border_style="yellow",
            padding=(0, 1),
        )
        console.print(panel)


class ProgressIndicator:
    """
    Progress and loading indicators.
    """

    @staticmethod
    def spinner(message: str):
        """
        Create a spinner progress context.

        Usage:
            with ProgressIndicator.spinner("Loading..."):
                await do_something()
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        )

    @staticmethod
    def bar(message: str, total: int):
        """
        Create a progress bar context.

        Usage:
            with ProgressIndicator.bar("Processing lights...", len(lights)) as progress:
                task = progress.add_task("Processing", total=len(lights))
                for light in lights:
                    process(light)
                    progress.advance(task)
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            transient=True,
        )


class LightConfigTable:
    """
    Display table of light configurations.
    """

    @staticmethod
    def display(lights: list[LightConfig], title: str = "Light Configuration") -> None:
        """Display a table showing all light configurations."""
        table = Table(
            title=title,
            box=box.ROUNDED,
            border_style="blue",
            header_style="bold cyan",
        )

        table.add_column("Light", style="white")
        table.add_column("Status", justify="center")
        table.add_column("Brightness", justify="right")
        table.add_column("Color/Temp", style="dim")
        table.add_column("Effect", style="magenta")

        for light in lights:
            if not light.enabled:
                table.add_row(
                    f"[dim]{light.name}[/dim]",
                    "[dim]EXCLUDED[/dim]",
                    "-",
                    "-",
                    "-",
                )
                continue

            # Status
            status = "[green]ON[/green]" if light.on else "[red]OFF[/red]"

            # Brightness
            brightness = f"{light.brightness:.0f}%" if light.on else "-"

            # Color/Temperature
            if light.color_mode == "temperature" and light.color_temp_kelvin:
                color = f"{light.color_temp_kelvin}K"
            elif light.color_mode == "color" and light.color_hex:
                color = light.color_hex
            elif light.color_mode == "gradient":
                color = "Gradient"
            elif light.color_mode == "effect":
                color = "-"
            else:
                color = "-"

            # Effect
            effect = light.effect if light.effect and light.effect != "no_effect" else "-"

            table.add_row(light.name, status, brightness, color, effect)

        console.print(table)

    @staticmethod
    def display_single(light: LightConfig) -> None:
        """Display detailed view of a single light configuration."""
        table = Table(
            title=f"[bold]{light.name}[/bold]",
            box=box.ROUNDED,
            border_style="cyan",
            show_header=False,
        )

        table.add_column("Setting", style="dim")
        table.add_column("Value")

        table.add_row("Power", "[green]ON[/green]" if light.on else "[red]OFF[/red]")
        table.add_row("Brightness", f"{light.brightness:.0f}%")
        table.add_row("Color Mode", light.color_mode.title())

        if light.color_mode == "temperature":
            table.add_row("Temperature", f"{light.color_temp_kelvin}K")
        elif light.color_mode == "color":
            if light.color_hex:
                table.add_row("Color", light.color_hex)
            elif light.color_xy:
                table.add_row("Color XY", f"({light.color_xy[0]:.3f}, {light.color_xy[1]:.3f})")
        elif light.color_mode == "gradient":
            table.add_row("Gradient", "Configured")

        if light.effect and light.effect != "no_effect":
            table.add_row("Effect", light.effect)

        table.add_row("Transition", f"{light.transition_ms}ms")
        table.add_row("Included", "[green]Yes[/green]" if light.enabled else "[red]No[/red]")

        console.print(table)


class StatusMessage:
    """
    Inline status messages (not panels).
    """

    @staticmethod
    def info(message: str) -> None:
        """Print an info message."""
        console.print(f"[cyan]i[/cyan] {message}")

    @staticmethod
    def success(message: str) -> None:
        """Print a success message."""
        console.print(f"[green][/green] {message}")

    @staticmethod
    def error(message: str) -> None:
        """Print an error message."""
        console.print(f"[red][/red] {message}")

    @staticmethod
    def warning(message: str) -> None:
        """Print a warning message."""
        console.print(f"[yellow]![/yellow] {message}")

    @staticmethod
    def step(number: int, message: str, total: Optional[int] = None) -> None:
        """Print a step indicator."""
        if total:
            console.print(f"[dim]({number}/{total})[/dim] {message}")
        else:
            console.print(f"[dim]({number})[/dim] {message}")


class TemplatePicker:
    """
    Visual template selection display.
    """

    @staticmethod
    def display_templates(templates: list[dict], selected_idx: int = 0) -> None:
        """
        Display templates in a visual grid.

        Args:
            templates: List of template dicts with 'name', 'icon', 'description'
            selected_idx: Currently selected template index
        """
        for idx, template in enumerate(templates):
            icon = template.get("icon", "")
            name = template.get("name", "Unknown")
            desc = template.get("description", "")

            if idx == selected_idx:
                console.print(f"  [bold cyan]> {icon} {name}[/bold cyan]")
                console.print(f"    [dim]{desc}[/dim]")
            else:
                console.print(f"    {icon} {name}")


def clear_screen() -> None:
    """Clear the terminal screen."""
    console.clear()


def print_blank_lines(count: int = 1) -> None:
    """Print blank lines for spacing."""
    for _ in range(count):
        console.print()
