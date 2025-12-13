"""
Navigation State Management for Wizards

Provides:
- Section navigation tracking with breadcrumbs
- Back/forward history
- Session state persistence for interrupted wizards
- Auto-cleanup of old session files
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional

from rich.console import Console

from .visual_feedback import render_progress_breadcrumb


console = Console()


# Session files older than this will be cleaned up
SESSION_MAX_AGE_SECONDS = 24 * 60 * 60  # 24 hours

# Directory for session state files
SESSION_DIR = Path(tempfile.gettempdir()) / "hue_wizard_sessions"


@dataclass
class NavigationState:
    """
    Tracks navigation state through a wizard.

    Maintains section history for back navigation and provides
    breadcrumb rendering for visual progress indication.
    """
    section_history: list[str] = field(default_factory=list)
    current_section: Optional[str] = None
    sections: list[str] = field(default_factory=list)
    completed_sections: set[str] = field(default_factory=set)

    def push_section(self, section_id: str) -> None:
        """
        Push a section onto the history stack.

        Args:
            section_id: ID of the section being entered
        """
        if self.current_section is not None:
            self.section_history.append(self.current_section)
        self.current_section = section_id

    def pop_section(self) -> Optional[str]:
        """
        Pop a section from the history stack (go back).

        Returns:
            The section ID that was popped, or None if at start
        """
        if not self.section_history:
            return None

        popped = self.current_section
        self.current_section = self.section_history.pop()
        return popped

    def mark_completed(self, section_id: str) -> None:
        """
        Mark a section as completed.

        Args:
            section_id: ID of the completed section
        """
        self.completed_sections.add(section_id)

    def is_completed(self, section_id: str) -> bool:
        """Check if a section has been completed."""
        return section_id in self.completed_sections

    @property
    def can_go_back(self) -> bool:
        """Check if back navigation is possible."""
        return len(self.section_history) > 0

    @property
    def current_index(self) -> int:
        """Get the index of the current section."""
        if self.current_section and self.current_section in self.sections:
            return self.sections.index(self.current_section)
        return 0

    @property
    def breadcrumbs(self) -> str:
        """Get formatted breadcrumb string for current progress."""
        if not self.sections:
            return ""

        completed_indices = {
            self.sections.index(s) for s in self.completed_sections
            if s in self.sections
        }

        return render_progress_breadcrumb(
            self.sections,
            self.current_index,
            completed_indices,
        )

    def reset(self) -> None:
        """Reset navigation state to start."""
        self.section_history.clear()
        self.current_section = None
        self.completed_sections.clear()


@dataclass
class WizardSessionState:
    """
    Complete state of a wizard session for persistence.

    Enables resuming interrupted wizards by saving all relevant state.
    """
    wizard_type: str
    timestamp: float = field(default_factory=time.time)
    navigation: dict = field(default_factory=dict)
    data: dict = field(default_factory=dict)
    mode: Optional[str] = None

    @classmethod
    def from_navigation(
        cls,
        wizard_type: str,
        nav_state: NavigationState,
        data: Optional[dict] = None,
        mode: Optional[str] = None,
    ) -> "WizardSessionState":
        """
        Create session state from navigation state.

        Args:
            wizard_type: Type identifier for the wizard
            nav_state: Current navigation state
            data: Optional wizard-specific data
            mode: Optional interaction mode

        Returns:
            WizardSessionState instance
        """
        return cls(
            wizard_type=wizard_type,
            navigation={
                "section_history": nav_state.section_history,
                "current_section": nav_state.current_section,
                "sections": nav_state.sections,
                "completed_sections": list(nav_state.completed_sections),
            },
            data=data or {},
            mode=mode,
        )

    def to_navigation(self) -> NavigationState:
        """Convert back to NavigationState object."""
        nav = self.navigation
        return NavigationState(
            section_history=nav.get("section_history", []),
            current_section=nav.get("current_section"),
            sections=nav.get("sections", []),
            completed_sections=set(nav.get("completed_sections", [])),
        )


def _ensure_session_dir() -> Path:
    """Ensure session directory exists."""
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    return SESSION_DIR


def _session_filename(wizard_type: str) -> str:
    """Generate session filename for a wizard type."""
    # Sanitize wizard type for filename
    safe_type = "".join(c if c.isalnum() else "_" for c in wizard_type)
    return f"hue_wizard_{safe_type}.json"


def save_session_state(
    wizard_type: str,
    state: WizardSessionState,
) -> bool:
    """
    Save wizard session state to a temp file.

    Args:
        wizard_type: Type identifier for the wizard
        state: Session state to save

    Returns:
        True if saved successfully, False otherwise
    """
    try:
        session_dir = _ensure_session_dir()
        filepath = session_dir / _session_filename(wizard_type)

        state_dict = {
            "wizard_type": state.wizard_type,
            "timestamp": state.timestamp,
            "navigation": state.navigation,
            "data": state.data,
            "mode": state.mode,
        }

        with open(filepath, 'w') as f:
            json.dump(state_dict, f, indent=2)

        return True
    except Exception as e:
        console.print(f"[dim]Warning: Could not save session state: {e}[/dim]")
        return False


def load_session_state(wizard_type: str) -> Optional[WizardSessionState]:
    """
    Load wizard session state from a temp file.

    Args:
        wizard_type: Type identifier for the wizard

    Returns:
        WizardSessionState if found and valid, None otherwise
    """
    try:
        filepath = SESSION_DIR / _session_filename(wizard_type)

        if not filepath.exists():
            return None

        with open(filepath, 'r') as f:
            state_dict = json.load(f)

        # Check if session is too old
        timestamp = state_dict.get("timestamp", 0)
        if time.time() - timestamp > SESSION_MAX_AGE_SECONDS:
            filepath.unlink()  # Clean up old session
            return None

        return WizardSessionState(
            wizard_type=state_dict.get("wizard_type", wizard_type),
            timestamp=timestamp,
            navigation=state_dict.get("navigation", {}),
            data=state_dict.get("data", {}),
            mode=state_dict.get("mode"),
        )

    except Exception:
        return None


def clear_session_state(wizard_type: str) -> bool:
    """
    Clear saved session state for a wizard type.

    Args:
        wizard_type: Type identifier for the wizard

    Returns:
        True if cleared, False if no session existed
    """
    try:
        filepath = SESSION_DIR / _session_filename(wizard_type)

        if filepath.exists():
            filepath.unlink()
            return True
        return False
    except Exception:
        return False


def cleanup_old_sessions() -> int:
    """
    Clean up session files older than SESSION_MAX_AGE_SECONDS.

    Returns:
        Number of files cleaned up
    """
    if not SESSION_DIR.exists():
        return 0

    cleaned = 0
    now = time.time()

    try:
        for filepath in SESSION_DIR.glob("hue_wizard_*.json"):
            try:
                # Check file modification time
                mtime = filepath.stat().st_mtime
                if now - mtime > SESSION_MAX_AGE_SECONDS:
                    filepath.unlink()
                    cleaned += 1
            except Exception:
                continue
    except Exception:
        pass

    return cleaned


def has_saved_session(wizard_type: str) -> bool:
    """
    Check if there's a saved session for a wizard type.

    Args:
        wizard_type: Type identifier for the wizard

    Returns:
        True if a valid session exists
    """
    state = load_session_state(wizard_type)
    return state is not None


async def offer_session_resume(wizard_type: str) -> Optional[WizardSessionState]:
    """
    Check for saved session and offer to resume.

    Args:
        wizard_type: Type identifier for the wizard

    Returns:
        WizardSessionState if user chose to resume, None otherwise
    """
    import questionary

    state = load_session_state(wizard_type)
    if state is None:
        return None

    # Calculate how long ago the session was saved
    age_seconds = time.time() - state.timestamp
    if age_seconds < 60:
        age_str = "less than a minute ago"
    elif age_seconds < 3600:
        minutes = int(age_seconds / 60)
        age_str = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        hours = int(age_seconds / 3600)
        age_str = f"{hours} hour{'s' if hours != 1 else ''} ago"

    # Build resume message
    nav = state.navigation
    current = nav.get("current_section", "unknown")
    completed = nav.get("completed_sections", [])

    console.print()
    console.print(f"[bold cyan]Found an interrupted session[/bold cyan]")
    console.print(f"[dim]Started {age_str}[/dim]")
    console.print(f"[dim]Progress: {len(completed)} section(s) completed, last at '{current}'[/dim]")
    console.print()

    try:
        resume = await questionary.confirm(
            "Would you like to continue where you left off?",
            default=True,
        ).ask_async()

        if resume:
            return state
        else:
            # Clear the old session
            clear_session_state(wizard_type)
            return None

    except KeyboardInterrupt:
        return None


def get_session_info(wizard_type: str) -> Optional[dict]:
    """
    Get information about a saved session without loading full state.

    Args:
        wizard_type: Type identifier for the wizard

    Returns:
        Dict with session info, or None if no session exists
    """
    state = load_session_state(wizard_type)
    if state is None:
        return None

    nav = state.navigation
    return {
        "wizard_type": state.wizard_type,
        "timestamp": state.timestamp,
        "age_seconds": time.time() - state.timestamp,
        "current_section": nav.get("current_section"),
        "completed_count": len(nav.get("completed_sections", [])),
        "mode": state.mode,
    }
