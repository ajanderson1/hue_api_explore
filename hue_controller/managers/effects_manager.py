"""
Effects Manager

Handles effects, gradients, timed effects, and signaling for Hue API v2.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Union

from ..models import (
    Light,
    Room,
    Zone,
    GradientConfig,
    TimedEffectConfig,
    SignalingConfig,
    EffectConfig,
    XYColor,
    CommandResult,
)
from ..constants import (
    EFFECT_TYPES,
    TIMED_EFFECT_TYPES,
    GRADIENT_MODES,
    SIGNAL_TYPES,
    GRADIENT_MIN_POINTS,
    GRADIENT_MAX_POINTS,
)
from ..exceptions import (
    EffectNotSupportedError,
    GradientNotSupportedError,
    InvalidGradientError,
    APIError,
)

if TYPE_CHECKING:
    from ..bridge_connector import BridgeConnector
    from ..device_manager import DeviceManager

logger = logging.getLogger(__name__)

Target = Union[Light, Room, Zone]


class EffectsManager:
    """Manages effects, gradients, and signaling."""

    def __init__(self, connector: BridgeConnector, device_manager: DeviceManager):
        """
        Initialize the effects manager.

        Args:
            connector: Bridge connector for API calls
            device_manager: Device manager for state access
        """
        self.connector = connector
        self.dm = device_manager

    # =========================================================================
    # Basic Effects
    # =========================================================================

    async def set_effect(
        self,
        target: Target,
        effect: str
    ) -> CommandResult:
        """
        Set an effect on a light or group.

        Args:
            target: Light, Room, or Zone to set effect on
            effect: Effect name (from EFFECT_TYPES)

        Returns:
            CommandResult indicating success/failure
        """
        if effect not in EFFECT_TYPES:
            return CommandResult(
                success=False,
                message=f"Unknown effect: {effect}",
                errors=[f"Valid effects: {', '.join(EFFECT_TYPES)}"]
            )

        config = EffectConfig(effect=effect)
        return await self._apply_to_target(target, config.to_dict(), f"Set {effect} effect")

    async def clear_effect(self, target: Target) -> CommandResult:
        """
        Clear any active effect.

        Args:
            target: Light, Room, or Zone

        Returns:
            CommandResult indicating success/failure
        """
        return await self.set_effect(target, "no_effect")

    async def get_supported_effects(self, light: Light) -> list[str]:
        """
        Get effects supported by a specific light.

        Args:
            light: Light to check

        Returns:
            List of supported effect names
        """
        try:
            response = await self.connector.get(f"/resource/light/{light.id}")
            data = response.get("data", [])
            if not data:
                return []

            light_data = data[0]
            effects = light_data.get("effects", {})
            return effects.get("effect_values", [])

        except APIError:
            return []

    # =========================================================================
    # Timed Effects (Sunrise/Sunset)
    # =========================================================================

    async def start_sunrise(
        self,
        target: Target,
        duration_minutes: int = 30
    ) -> CommandResult:
        """
        Start a sunrise simulation.

        Args:
            target: Light, Room, or Zone
            duration_minutes: Duration of sunrise in minutes

        Returns:
            CommandResult indicating success/failure
        """
        config = TimedEffectConfig(
            effect="sunrise",
            duration_ms=duration_minutes * 60 * 1000
        )
        return await self._apply_to_target(
            target,
            config.to_dict(),
            f"Started sunrise ({duration_minutes} min)"
        )

    async def start_sunset(
        self,
        target: Target,
        duration_minutes: int = 30
    ) -> CommandResult:
        """
        Start a sunset simulation.

        Args:
            target: Light, Room, or Zone
            duration_minutes: Duration of sunset in minutes

        Returns:
            CommandResult indicating success/failure
        """
        config = TimedEffectConfig(
            effect="sunset",
            duration_ms=duration_minutes * 60 * 1000
        )
        return await self._apply_to_target(
            target,
            config.to_dict(),
            f"Started sunset ({duration_minutes} min)"
        )

    async def stop_timed_effect(self, target: Target) -> CommandResult:
        """
        Stop any running timed effect.

        Args:
            target: Light, Room, or Zone

        Returns:
            CommandResult indicating success/failure
        """
        config = TimedEffectConfig(effect="no_effect", duration_ms=0)
        return await self._apply_to_target(
            target,
            config.to_dict(),
            "Stopped timed effect"
        )

    # =========================================================================
    # Gradients
    # =========================================================================

    async def set_gradient(
        self,
        light: Light,
        config: GradientConfig
    ) -> CommandResult:
        """
        Set a gradient on a gradient-capable light.

        Args:
            light: Light to set gradient on
            config: Gradient configuration

        Returns:
            CommandResult indicating success/failure
        """
        # Validate gradient
        if len(config.points) < GRADIENT_MIN_POINTS:
            raise InvalidGradientError(
                f"Gradient requires at least {GRADIENT_MIN_POINTS} colors"
            )
        if len(config.points) > GRADIENT_MAX_POINTS:
            raise InvalidGradientError(
                f"Gradient supports at most {GRADIENT_MAX_POINTS} colors"
            )
        if config.mode not in GRADIENT_MODES:
            raise InvalidGradientError(
                f"Invalid gradient mode. Valid modes: {', '.join(GRADIENT_MODES)}"
            )

        # Check if light supports gradients
        gradient_info = await self.get_gradient_support(light)
        if not gradient_info:
            raise GradientNotSupportedError(light.name)

        payload = {"gradient": config.to_dict()}

        try:
            await self.connector.put(f"/resource/light/{light.id}", payload)
            return CommandResult(
                success=True,
                message=f"Set gradient on {light.name}",
                target_name=light.name,
                affected_lights=1
            )
        except APIError as e:
            return CommandResult(
                success=False,
                message=f"Failed to set gradient: {e}",
                errors=[str(e)]
            )

    async def get_gradient_support(self, light: Light) -> Optional[dict]:
        """
        Check if light supports gradients and get capabilities.

        Args:
            light: Light to check

        Returns:
            Dict with gradient capabilities or None if not supported
        """
        try:
            response = await self.connector.get(f"/resource/light/{light.id}")
            data = response.get("data", [])
            if not data:
                return None

            light_data = data[0]
            gradient = light_data.get("gradient")

            if gradient:
                return {
                    "points_capable": gradient.get("points_capable", 0),
                    "mode_values": gradient.get("mode_values", []),
                    "pixel_count": gradient.get("pixel_count", 0),
                }
            return None

        except APIError:
            return None

    async def create_gradient(
        self,
        light: Light,
        colors: list[XYColor],
        mode: str = "interpolated_palette"
    ) -> CommandResult:
        """
        Convenience method to create and set a gradient.

        Args:
            light: Light to set gradient on
            colors: List of XYColor objects (2-5 colors)
            mode: Gradient mode

        Returns:
            CommandResult indicating success/failure
        """
        config = GradientConfig(points=colors, mode=mode)
        return await self.set_gradient(light, config)

    # =========================================================================
    # Signaling
    # =========================================================================

    async def signal_light(
        self,
        target: Target,
        config: SignalingConfig
    ) -> CommandResult:
        """
        Make lights signal (flash/pulse).

        Args:
            target: Light, Room, or Zone
            config: Signaling configuration

        Returns:
            CommandResult indicating success/failure
        """
        if config.signal not in SIGNAL_TYPES:
            return CommandResult(
                success=False,
                message=f"Unknown signal type: {config.signal}",
                errors=[f"Valid types: {', '.join(SIGNAL_TYPES)}"]
            )

        return await self._apply_to_target(
            target,
            config.to_dict(),
            f"Signaling {target.name}" if hasattr(target, 'name') else "Signaling"
        )

    async def flash(
        self,
        target: Target,
        duration_ms: int = 2000
    ) -> CommandResult:
        """
        Flash a light or group on/off.

        Args:
            target: Light, Room, or Zone
            duration_ms: Flash duration in milliseconds

        Returns:
            CommandResult indicating success/failure
        """
        config = SignalingConfig(signal="on_off", duration_ms=duration_ms)
        return await self.signal_light(target, config)

    async def flash_color(
        self,
        target: Target,
        color: XYColor,
        duration_ms: int = 2000
    ) -> CommandResult:
        """
        Flash a light or group with a specific color.

        Args:
            target: Light, Room, or Zone
            color: Color to flash
            duration_ms: Flash duration in milliseconds

        Returns:
            CommandResult indicating success/failure
        """
        config = SignalingConfig(
            signal="on_off_color",
            duration_ms=duration_ms,
            colors=[color]
        )
        return await self.signal_light(target, config)

    async def identify_light(
        self,
        light: Light,
        duration_ms: int = 5000
    ) -> CommandResult:
        """
        Identify a light by signaling.

        Args:
            light: Light to identify
            duration_ms: Identification duration

        Returns:
            CommandResult indicating success/failure
        """
        # Use the identify endpoint if available, otherwise fall back to signaling
        try:
            await self.connector.put(
                f"/resource/light/{light.id}",
                {"identify": {"action": "identify"}}
            )
            return CommandResult(
                success=True,
                message=f"Identifying {light.name}",
                target_name=light.name,
                affected_lights=1
            )
        except APIError:
            # Fall back to flashing
            return await self.flash(light, duration_ms)

    async def stop_signaling(self, target: Target) -> CommandResult:
        """
        Stop any active signaling.

        Args:
            target: Light, Room, or Zone

        Returns:
            CommandResult indicating success/failure
        """
        config = SignalingConfig(signal="no_signal", duration_ms=0)
        return await self._apply_to_target(target, config.to_dict(), "Stopped signaling")

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _apply_to_target(
        self,
        target: Target,
        payload: dict,
        success_message: str
    ) -> CommandResult:
        """
        Apply a payload to a target (light, room, or zone).

        Args:
            target: Light, Room, or Zone
            payload: API payload to send
            success_message: Message on success

        Returns:
            CommandResult indicating success/failure
        """
        errors: list[str] = []
        affected = 0
        unreachable: list[str] = []

        if isinstance(target, Light):
            # Apply directly to light
            try:
                await self.connector.put(f"/resource/light/{target.id}", payload)
                affected = 1
                if not target.is_reachable:
                    unreachable.append(target.name)
            except APIError as e:
                errors.append(f"{target.name}: {e}")

        elif isinstance(target, (Room, Zone)):
            # Apply to grouped_light for efficiency
            if target.grouped_light_id:
                try:
                    await self.connector.put(
                        f"/resource/grouped_light/{target.grouped_light_id}",
                        payload
                    )
                    lights = self.dm.get_lights_for_target(target)
                    affected = len(lights)
                    unreachable = [l.name for l in lights if not l.is_reachable]
                except APIError as e:
                    errors.append(str(e))
            else:
                # Fall back to applying to each light
                lights = self.dm.get_lights_for_target(target)
                for light in lights:
                    try:
                        await self.connector.put(f"/resource/light/{light.id}", payload)
                        affected += 1
                        if not light.is_reachable:
                            unreachable.append(light.name)
                    except APIError as e:
                        errors.append(f"{light.name}: {e}")

        if errors:
            return CommandResult(
                success=False,
                message=f"Failed: {', '.join(errors)}",
                target_name=target.name if hasattr(target, 'name') else None,
                affected_lights=affected,
                unreachable_lights=unreachable,
                errors=errors
            )

        return CommandResult(
            success=True,
            message=f"{success_message} on {target.name}" if hasattr(target, 'name') else success_message,
            target_name=target.name if hasattr(target, 'name') else None,
            affected_lights=affected,
            unreachable_lights=unreachable
        )

    def get_available_effects(self) -> list[str]:
        """Get list of all available effect names."""
        return [e for e in EFFECT_TYPES if e != "no_effect"]

    def get_available_timed_effects(self) -> list[str]:
        """Get list of all available timed effect names."""
        return [e for e in TIMED_EFFECT_TYPES if e != "no_effect"]

    def get_available_gradient_modes(self) -> list[str]:
        """Get list of all available gradient modes."""
        return GRADIENT_MODES.copy()

    def get_available_signal_types(self) -> list[str]:
        """Get list of all available signal types."""
        return [s for s in SIGNAL_TYPES if s != "no_signal"]
