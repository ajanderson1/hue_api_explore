"""
Live Preview Functionality

Allows previewing scene settings on actual lights with auto-restore.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Optional
from rich.console import Console

from ...bridge_connector import BridgeConnector
from ...device_manager import DeviceManager
from ...models import Light, SceneLightAction


console = Console()


@dataclass
class LightState:
    """Captured state of a single light for restoration."""
    light_id: str
    on: bool
    brightness: Optional[float]
    color_xy: Optional[tuple[float, float]]
    color_temp_mirek: Optional[int]

    def to_restore_payload(self) -> dict:
        """Convert to API payload for restoration."""
        payload = {"on": {"on": self.on}}

        if self.on:
            if self.brightness is not None:
                payload["dimming"] = {"brightness": self.brightness}

            # Restore color mode - use color_temp if available, else xy color
            if self.color_temp_mirek is not None:
                payload["color_temperature"] = {"mirek": self.color_temp_mirek}
            elif self.color_xy is not None:
                payload["color"] = {"xy": {"x": self.color_xy[0], "y": self.color_xy[1]}}

        return payload


@dataclass
class LivePreview:
    """
    Live preview system with auto-restore functionality.

    Captures current light states, applies preview settings,
    and automatically restores after a timeout.
    """
    connector: BridgeConnector
    device_manager: DeviceManager
    restore_delay: float = 5.0  # seconds before auto-restore
    captured_states: dict[str, LightState] = field(default_factory=dict)

    async def capture_states(self, lights: list[Light]) -> None:
        """
        Capture current states of lights for later restoration.

        Args:
            lights: List of lights to capture state from
        """
        self.captured_states.clear()

        for light in lights:
            # Get fresh state from device manager
            current = self.device_manager.lights.get(light.id)
            if not current:
                continue

            # Capture current state
            color_xy = None
            if current.color_xy:
                color_xy = (current.color_xy.x, current.color_xy.y)

            self.captured_states[light.id] = LightState(
                light_id=light.id,
                on=current.is_on,
                brightness=current.brightness,
                color_xy=color_xy,
                color_temp_mirek=current.color_temperature_mirek,
            )

    async def apply_settings(
        self,
        lights: list[Light],
        action: SceneLightAction,
    ) -> list[str]:
        """
        Apply preview settings to lights.

        Args:
            lights: List of lights to apply settings to
            action: The scene action settings to apply

        Returns:
            List of light names that were successfully updated
        """
        payload = action.to_dict()
        applied = []

        for light in lights:
            try:
                await self.connector.put(f"/resource/light/{light.id}", payload)
                applied.append(light.name)
            except Exception as e:
                console.print(f"[yellow]![/yellow] Skipped {light.name}: {e}")

        return applied

    async def restore_states(self) -> list[str]:
        """
        Restore lights to their captured states.

        Returns:
            List of light names that were successfully restored
        """
        restored = []

        for light_id, state in self.captured_states.items():
            try:
                payload = state.to_restore_payload()
                await self.connector.put(f"/resource/light/{light_id}", payload)

                light = self.device_manager.lights.get(light_id)
                if light:
                    restored.append(light.name)
            except Exception as e:
                light = self.device_manager.lights.get(light_id)
                name = light.name if light else light_id
                console.print(f"[yellow]![/yellow] Failed to restore {name}: {e}")

        return restored

    async def preview_with_restore(
        self,
        lights: list[Light],
        action: SceneLightAction,
        on_applied: Optional[callable] = None,
    ) -> bool:
        """
        Preview settings and automatically restore after delay.

        Args:
            lights: Lights to preview on
            action: Settings to apply
            on_applied: Optional callback when settings are applied

        Returns:
            True if preview completed successfully
        """
        # Capture current states
        await self.capture_states(lights)

        # Apply preview settings
        console.print("\n[cyan]Applying preview...[/cyan]")
        applied = await self.apply_settings(lights, action)

        if not applied:
            console.print("[red]No lights were updated[/red]")
            return False

        # Show what was applied
        for name in applied:
            console.print(f"  [green][/green] {name}")

        if on_applied:
            on_applied()

        # Wait for user or timeout
        console.print(f"\n[dim]Look at your lights! Auto-restoring in {self.restore_delay:.0f}s...[/dim]")
        console.print("[dim]Press Ctrl+C to keep these settings[/dim]\n")

        try:
            await asyncio.sleep(self.restore_delay)
        except asyncio.CancelledError:
            console.print("[yellow]Preview cancelled - keeping current settings[/yellow]")
            return True

        # Restore original states
        console.print("[cyan]Restoring original settings...[/cyan]")
        restored = await self.restore_states()

        for name in restored:
            console.print(f"  [green][/green] {name}")

        return True

    async def preview_interactive(
        self,
        lights: list[Light],
        action: SceneLightAction,
    ) -> str:
        """
        Preview with interactive choice to keep or restore.

        Args:
            lights: Lights to preview on
            action: Settings to apply

        Returns:
            "keep" if user wants to keep settings, "restore" if restored
        """
        from ..ui import AsyncMenu

        # Capture and apply
        await self.capture_states(lights)
        console.print("\n[cyan]Applying preview...[/cyan]")
        applied = await self.apply_settings(lights, action)

        if not applied:
            console.print("[red]No lights were updated[/red]")
            return "failed"

        for name in applied:
            console.print(f"  [green][/green] {name}")

        console.print("\n[bold]Look at your lights![/bold]\n")

        # Ask what to do
        choice = await AsyncMenu.select(
            "What would you like to do?",
            choices=[
                "Looks great! Keep these settings",
                "Restore previous settings",
            ],
        )

        if choice and "Keep" in choice:
            console.print("[green]Settings kept[/green]")
            return "keep"
        else:
            console.print("[cyan]Restoring...[/cyan]")
            await self.restore_states()
            console.print("[green]Original settings restored[/green]")
            return "restore"
