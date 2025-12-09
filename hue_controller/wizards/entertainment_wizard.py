"""
Entertainment Wizard

Interactive wizard for creating and managing entertainment configurations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base_wizard import BaseWizard, WizardResult, WizardAction
from ..models import (
    EntertainmentConfiguration,
    EntertainmentLocation,
)
from ..constants import ENTERTAINMENT_TYPES, ENTERTAINMENT_TYPE_DESCRIPTIONS
from ..managers.entertainment_manager import EntertainmentManager

if TYPE_CHECKING:
    from ..device_manager import DeviceManager
    from ..bridge_connector import BridgeConnector


class EntertainmentWizard(BaseWizard):
    """Interactive wizard for entertainment configuration management."""

    def __init__(
        self,
        connector: BridgeConnector,
        device_manager: DeviceManager
    ):
        """
        Initialize the entertainment wizard.

        Args:
            connector: Bridge connector for API calls
            device_manager: Device manager for state access
        """
        super().__init__(device_manager)
        self.connector = connector
        self.entertainment_manager = EntertainmentManager(connector, device_manager)

    async def run(self) -> WizardResult:
        """
        Run the entertainment wizard main menu.

        Returns:
            WizardResult indicating success/failure
        """
        self.print_header("Entertainment Wizard")

        print("Entertainment configurations enable synchronized lighting")
        print("for games, movies, and music visualization.\n")

        options = [
            ("Create new configuration", "create"),
            ("Edit configuration", "edit"),
            ("Delete configuration", "delete"),
            ("View configurations", "view"),
            ("Set light positions", "positions"),
        ]

        choice, action = self.select_one("What would you like to do?", options)

        if action == WizardAction.CANCEL:
            return self.handle_cancel("Entertainment")

        if choice == "create":
            return await self._create_wizard()
        elif choice == "edit":
            return await self._edit_wizard()
        elif choice == "delete":
            return await self._delete_wizard()
        elif choice == "view":
            return await self._view_configurations()
        elif choice == "positions":
            return await self._set_positions_wizard()

        return WizardResult(success=False, message="Invalid choice")

    async def run_create(self) -> WizardResult:
        """Run the creation wizard directly."""
        return await self._create_wizard()

    # =========================================================================
    # Create Configuration Wizard
    # =========================================================================

    async def _create_wizard(self) -> WizardResult:
        """Create a new entertainment configuration."""
        self.print_header("Create Entertainment Configuration")

        # Step 1: Name
        self.print_step(1, 4, "Name your configuration")
        name, action = self.get_input(
            "Configuration name",
            validator=lambda x: len(x) >= 1 and len(x) <= 32,
            error_message="Name must be 1-32 characters"
        )
        if action != WizardAction.CONTINUE:
            return self.handle_cancel("Entertainment")

        # Step 2: Type
        self.print_step(2, 4, "Select configuration type")
        config_type, action = await self._select_type()
        if action != WizardAction.CONTINUE:
            return self.handle_cancel("Entertainment")

        # Step 3: Select lights
        self.print_step(3, 4, "Select lights")
        print("\nSelect the lights to include in this entertainment area.")
        print("For best results, choose lights that are visible from your viewing position.\n")

        light_ids, action = await self._select_lights()
        if action != WizardAction.CONTINUE or not light_ids:
            return self.handle_cancel("Entertainment")

        # Step 4: Confirm
        self.print_step(4, 4, "Confirm and create")
        print(f"\nConfiguration: {name}")
        print(f"Type: {ENTERTAINMENT_TYPE_DESCRIPTIONS.get(config_type, config_type)}")
        print(f"Lights: {len(light_ids)}")

        confirmed, action = self.get_confirmation("Create this configuration?", default=True)
        if not confirmed or action != WizardAction.CONTINUE:
            return self.handle_cancel("Entertainment")

        # Create the configuration
        try:
            config = await self.entertainment_manager.create_configuration(
                name=name,
                config_type=config_type,
                light_ids=light_ids
            )

            self.print_success(f"Created entertainment configuration '{name}'")

            # Offer to set positions
            set_pos, _ = self.get_confirmation(
                "Would you like to set light positions now?",
                default=True
            )
            if set_pos:
                await self._set_positions_for_config(config.id, config_type)

            return WizardResult(
                success=True,
                message=f"Created configuration '{name}'",
                data=config
            )

        except Exception as e:
            self.print_error(str(e))
            return WizardResult(success=False, message=str(e))

    # =========================================================================
    # Edit Configuration Wizard
    # =========================================================================

    async def _edit_wizard(self) -> WizardResult:
        """Edit an existing entertainment configuration."""
        self.print_header("Edit Entertainment Configuration")

        # Select configuration
        config, action = await self._select_configuration()
        if action != WizardAction.CONTINUE or config is None:
            return self.handle_cancel("Entertainment")

        # Edit menu
        while True:
            print(f"\nEditing: {config.name}")
            print(f"Type: {ENTERTAINMENT_TYPE_DESCRIPTIONS.get(config.configuration_type, config.configuration_type)}")
            print(f"Status: {config.status}")
            print(f"Lights: {len(config.light_services)}")

            options = [
                ("Rename configuration", "rename"),
                ("Update lights", "lights"),
                ("Set light positions", "positions"),
                ("Done", "done"),
            ]

            choice, action = self.select_one("What would you like to do?", options)

            if action == WizardAction.CANCEL:
                return self.handle_cancel("Entertainment")

            if choice == "rename":
                new_name, action = self.get_input("New name")
                if action == WizardAction.CONTINUE:
                    try:
                        config = await self.entertainment_manager.rename_configuration(
                            config.id, new_name
                        )
                        self.print_success(f"Renamed to '{new_name}'")
                    except Exception as e:
                        self.print_error(str(e))

            elif choice == "lights":
                light_ids, action = await self._select_lights()
                if action == WizardAction.CONTINUE and light_ids:
                    try:
                        config = await self.entertainment_manager.update_configuration(
                            config.id, light_ids=light_ids
                        )
                        self.print_success(f"Updated lights ({len(light_ids)} selected)")
                    except Exception as e:
                        self.print_error(str(e))

            elif choice == "positions":
                await self._set_positions_for_config(config.id, config.configuration_type)

            elif choice == "done":
                break

        return WizardResult(
            success=True,
            message=f"Finished editing '{config.name}'",
            data=config
        )

    # =========================================================================
    # Delete Configuration Wizard
    # =========================================================================

    async def _delete_wizard(self) -> WizardResult:
        """Delete an entertainment configuration."""
        self.print_header("Delete Entertainment Configuration")

        config, action = await self._select_configuration()
        if action != WizardAction.CONTINUE or config is None:
            return self.handle_cancel("Entertainment")

        confirmed, action = self.get_confirmation(
            f"Delete configuration '{config.name}'?",
            default=False
        )
        if not confirmed or action != WizardAction.CONTINUE:
            return self.handle_cancel("Entertainment")

        try:
            await self.entertainment_manager.delete_configuration(config.id)
            self.print_success(f"Deleted configuration '{config.name}'")
            return WizardResult(
                success=True,
                message=f"Deleted configuration '{config.name}'"
            )

        except Exception as e:
            self.print_error(str(e))
            return WizardResult(success=False, message=str(e))

    # =========================================================================
    # View Configurations
    # =========================================================================

    async def _view_configurations(self) -> WizardResult:
        """View all entertainment configurations."""
        self.print_header("Entertainment Configurations")

        try:
            configs = await self.entertainment_manager.list_configurations()
        except Exception as e:
            self.print_error(str(e))
            return WizardResult(success=False, message=str(e))

        if not configs:
            print("No entertainment configurations found.")
            print("\nUse 'Create new configuration' to set one up.")
            return WizardResult(
                success=True,
                message="No configurations found"
            )

        for config in configs:
            print(f"\n{config.name}")
            print(f"  Type: {ENTERTAINMENT_TYPE_DESCRIPTIONS.get(config.configuration_type, config.configuration_type)}")
            print(f"  Status: {config.status}")
            print(f"  Lights: {len(config.light_services)}")

            if config.channels:
                print(f"  Channels: {len(config.channels)}")

        return WizardResult(
            success=True,
            message=f"Found {len(configs)} configuration(s)",
            data=configs
        )

    # =========================================================================
    # Set Light Positions Wizard
    # =========================================================================

    async def _set_positions_wizard(self) -> WizardResult:
        """Set light positions for a configuration."""
        self.print_header("Set Light Positions")

        config, action = await self._select_configuration()
        if action != WizardAction.CONTINUE or config is None:
            return self.handle_cancel("Entertainment")

        await self._set_positions_for_config(config.id, config.configuration_type)

        return WizardResult(
            success=True,
            message="Updated light positions"
        )

    async def _set_positions_for_config(
        self,
        config_id: str,
        config_type: str
    ) -> None:
        """Set light positions for a specific configuration."""
        try:
            config = await self.entertainment_manager.get_configuration(config_id)
        except Exception as e:
            self.print_error(str(e))
            return

        if not config.light_services:
            print("No lights in this configuration.")
            return

        print("\nPosition lights in your entertainment space.")
        print("Coordinates are relative to your viewing position:")
        print("  X: -1.0 (left) to 1.0 (right)")
        print("  Y: -1.0 (back) to 1.0 (front)")
        print("  Z: 0.0 (floor) to 1.0 (ceiling)")

        # Offer presets for screen type
        if config_type in ("screen", "monitor"):
            await self._set_screen_positions(config_id, config.light_services)
        else:
            await self._set_custom_positions(config_id, config.light_services)

    async def _set_screen_positions(
        self,
        config_id: str,
        light_ids: list[str]
    ) -> None:
        """Set positions using screen presets."""
        print("\nScreen Position Presets:")
        print("  1. Left side of screen")
        print("  2. Right side of screen")
        print("  3. Behind screen (center)")
        print("  4. Ambient/background")
        print("  5. Custom position")

        positions: dict[str, tuple[float, float, float]] = {}

        for light_id in light_ids:
            # Get light name
            light = self.dm.lights.get(light_id)
            light_name = light.name if light else light_id

            print(f"\n{light_name}:")
            preset, action = self.get_input(
                "Position (1-5)",
                validator=lambda x: x in ("1", "2", "3", "4", "5"),
                error_message="Enter 1-5"
            )

            if action != WizardAction.CONTINUE:
                break

            if preset == "1":  # Left
                positions[light_id] = (-1.0, 1.0, 0.5)
            elif preset == "2":  # Right
                positions[light_id] = (1.0, 1.0, 0.5)
            elif preset == "3":  # Behind center
                positions[light_id] = (0.0, 1.0, 0.5)
            elif preset == "4":  # Ambient
                positions[light_id] = (0.0, -0.5, 0.5)
            elif preset == "5":  # Custom
                pos = await self._get_custom_position()
                if pos:
                    positions[light_id] = pos

        if positions:
            try:
                await self.entertainment_manager.set_light_positions(
                    config_id, positions
                )
                self.print_success("Updated light positions")
            except Exception as e:
                self.print_error(str(e))

    async def _set_custom_positions(
        self,
        config_id: str,
        light_ids: list[str]
    ) -> None:
        """Set custom positions for each light."""
        positions: dict[str, tuple[float, float, float]] = {}

        for light_id in light_ids:
            light = self.dm.lights.get(light_id)
            light_name = light.name if light else light_id

            print(f"\n{light_name}:")
            pos = await self._get_custom_position()
            if pos:
                positions[light_id] = pos

        if positions:
            try:
                await self.entertainment_manager.set_light_positions(
                    config_id, positions
                )
                self.print_success("Updated light positions")
            except Exception as e:
                self.print_error(str(e))

    async def _get_custom_position(self) -> Optional[tuple[float, float, float]]:
        """Get a custom position from the user."""
        x, action = self.get_number("X (-1.0 to 1.0)", min_value=-1.0, max_value=1.0)
        if action != WizardAction.CONTINUE:
            return None

        y, action = self.get_number("Y (-1.0 to 1.0)", min_value=-1.0, max_value=1.0)
        if action != WizardAction.CONTINUE:
            return None

        z, action = self.get_number("Z (0.0 to 1.0)", min_value=0.0, max_value=1.0)
        if action != WizardAction.CONTINUE:
            return None

        return (x, y, z)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _select_type(self) -> tuple[Optional[str], WizardAction]:
        """Let user select an entertainment type."""
        options = [
            (ENTERTAINMENT_TYPE_DESCRIPTIONS.get(t, t), t)
            for t in ENTERTAINMENT_TYPES
        ]
        return self.select_one("Select configuration type", options)

    async def _select_configuration(
        self
    ) -> tuple[Optional[EntertainmentConfiguration], WizardAction]:
        """Let user select an entertainment configuration."""
        try:
            configs = await self.entertainment_manager.list_configurations()
        except Exception as e:
            self.print_error(str(e))
            return None, WizardAction.CANCEL

        if not configs:
            print("No entertainment configurations found.")
            return None, WizardAction.CANCEL

        options = [
            (f"{c.name} ({c.configuration_type})", c)
            for c in configs
        ]
        return self.select_one("Select configuration", options)

    async def _select_lights(self) -> tuple[list[str], WizardAction]:
        """Let user select lights for entertainment."""
        # Get entertainment-capable lights
        lights = list(self.dm.lights.values())

        if not lights:
            self.print_error("No lights found")
            return [], WizardAction.CANCEL

        options = [(l.name, l.id) for l in sorted(lights, key=lambda l: l.name)]

        selected, action = self.select_multiple(
            "Select lights (comma-separated numbers)",
            options,
            min_selections=1
        )

        return selected, action
