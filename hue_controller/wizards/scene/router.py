"""
Scene Wizard Router

Entry point for the unified scene wizard system.
Presents mode selection (Quick/Standard/Advanced) and routes to the appropriate wizard.
"""

from dataclasses import dataclass
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich import box

from ...bridge_connector import BridgeConnector
from ...device_manager import DeviceManager
from ..base_wizard import WizardResult
from ..ui import AsyncMenu, MenuChoice, WizardPanel
from .quick_wizard import QuickSceneWizard


console = Console()


@dataclass
class SceneWizardRouter:
    """
    Entry point for the unified scene wizard.

    Presents three modes:
    - Quick: Mood-first, ~30 second scene creation
    - Standard: Light-by-light configuration
    - Advanced: Full API access with all options
    """
    connector: BridgeConnector
    device_manager: DeviceManager

    async def run(self, mode: Optional[str] = None) -> WizardResult:
        """
        Run the scene wizard.

        Args:
            mode: Optional pre-selected mode ("quick", "standard", "advanced")
                  If None, shows mode selection.

        Returns:
            WizardResult from the chosen wizard
        """
        # If mode is pre-selected, skip to that wizard
        if mode:
            return await self._run_mode(mode)

        # Show mode selection
        console.clear()
        self._show_header()

        selected_mode = await self._select_mode()
        if selected_mode is None:
            return WizardResult(success=False, message="Cancelled")

        return await self._run_mode(selected_mode)

    def _show_header(self) -> None:
        """Display the wizard header."""
        header_content = """[bold white]SCENE WIZARD[/bold white]

Create scenes for your Philips Hue lights.
Choose a mode based on how much control you need."""

        panel = Panel(
            header_content,
            box=box.ROUNDED,
            border_style="bright_blue",
            padding=(1, 2),
        )
        console.print(panel)

    async def _select_mode(self) -> Optional[str]:
        """Present mode selection menu."""
        choices = [
            MenuChoice(
                label="Quick Setup",
                value="quick",
                description="Pick a mood, we'll handle the rest (~30 seconds)",
                icon="",
            ),
            MenuChoice(
                label="Standard",
                value="standard",
                description="Configure each light individually",
                icon="",
            ),
            MenuChoice(
                label="Advanced",
                value="advanced",
                description="Full control: palettes, effects, dynamics",
                icon="",
            ),
        ]

        console.print()
        selected = await AsyncMenu.select(
            "How would you like to create your scene?",
            choices=choices,
        )

        return selected

    async def _run_mode(self, mode: str) -> WizardResult:
        """Run the selected wizard mode."""
        if mode == "quick":
            wizard = QuickSceneWizard(
                connector=self.connector,
                device_manager=self.device_manager,
            )
            return await wizard.run()

        elif mode == "standard":
            # Use the new StandardSceneWizard with questionary
            from .standard_wizard import StandardSceneWizard
            wizard = StandardSceneWizard(
                connector=self.connector,
                device_manager=self.device_manager,
            )
            return await wizard.run()

        elif mode == "advanced":
            # Use the existing AdminSceneWizard for now (will be refactored)
            from ..admin_scene_wizard import AdminSceneWizard
            from ...managers.scene_manager import SceneManager
            scene_manager = SceneManager(self.connector, self.device_manager)
            wizard = AdminSceneWizard(
                connector=self.connector,
                device_manager=self.device_manager,
                scene_manager=scene_manager,
            )
            return await wizard.run()

        else:
            return WizardResult(success=False, message=f"Unknown mode: {mode}")


async def run_scene_wizard(
    connector: BridgeConnector,
    device_manager: DeviceManager,
    mode: Optional[str] = None,
) -> WizardResult:
    """
    Convenience function to run the scene wizard.

    Args:
        connector: Bridge connector
        device_manager: Device manager
        mode: Optional pre-selected mode

    Returns:
        WizardResult from the wizard
    """
    router = SceneWizardRouter(connector, device_manager)
    return await router.run(mode)
