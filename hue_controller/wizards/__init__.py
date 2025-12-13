"""
Hue Controller Wizards

Interactive wizards for complex configuration tasks.
"""

from .base_wizard import BaseWizard, WizardResult
from .scene_wizard import SceneWizard
from .group_wizard import GroupWizard
from .entertainment_wizard import EntertainmentWizard
from .admin_scene_wizard import AdminSceneWizard
from .wizard_ui import WizardUI, NavAction, SelectOption, WizardSection

# New unified scene wizard system
from .scene import QuickSceneWizard, SceneWizardRouter, run_scene_wizard

__all__ = [
    "BaseWizard",
    "WizardResult",
    "SceneWizard",
    "GroupWizard",
    "EntertainmentWizard",
    "AdminSceneWizard",
    "WizardUI",
    "NavAction",
    "SelectOption",
    "WizardSection",
    # New scene wizards
    "QuickSceneWizard",
    "SceneWizardRouter",
    "run_scene_wizard",
]
