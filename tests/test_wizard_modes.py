"""
Tests for Wizard Interaction Modes

Tests the three-tier interaction model (Simple/Standard/Advanced)
and mode configuration.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from hue_controller.wizards.modes import (
    InteractionMode,
    ModeConfig,
    detect_user_mode,
    get_mode_label,
    get_mode_description,
    MODE_DESCRIPTIONS,
    MODE_ICONS,
)


class TestInteractionMode:
    """Tests for InteractionMode enum."""

    def test_mode_enum_values(self):
        """Verify SIMPLE, STANDARD, ADVANCED exist."""
        assert InteractionMode.SIMPLE.value == "simple"
        assert InteractionMode.STANDARD.value == "standard"
        assert InteractionMode.ADVANCED.value == "advanced"

    def test_mode_enum_members(self):
        """Verify all expected modes exist."""
        modes = list(InteractionMode)
        assert len(modes) == 3
        assert InteractionMode.SIMPLE in modes
        assert InteractionMode.STANDARD in modes
        assert InteractionMode.ADVANCED in modes

    def test_mode_from_string(self):
        """Test creating mode from string value."""
        assert InteractionMode("simple") == InteractionMode.SIMPLE
        assert InteractionMode("standard") == InteractionMode.STANDARD
        assert InteractionMode("advanced") == InteractionMode.ADVANCED


class TestModeConfig:
    """Tests for ModeConfig dataclass."""

    def test_mode_config_creation(self):
        """Verify ModeConfig dataclass instantiation."""
        config = ModeConfig(mode=InteractionMode.SIMPLE)
        assert config.mode == InteractionMode.SIMPLE

    def test_simple_mode_config(self):
        """Test Simple Mode configuration defaults."""
        config = ModeConfig.for_mode(InteractionMode.SIMPLE)

        assert config.mode == InteractionMode.SIMPLE
        assert config.show_technical_values is False
        assert config.show_presets is True
        assert config.show_all_options is False
        assert config.show_help_text is True
        assert config.show_advanced_sections is False
        assert config.show_palette_section is False
        assert config.show_dynamics_section is False
        assert config.show_gradient_section is False
        assert config.show_recall_section is False
        assert config.allow_raw_values is False
        assert config.use_friendly_labels is True

    def test_standard_mode_config(self):
        """Test Standard Mode configuration defaults."""
        config = ModeConfig.for_mode(InteractionMode.STANDARD)

        assert config.mode == InteractionMode.STANDARD
        assert config.show_technical_values is True
        assert config.show_presets is True
        assert config.show_all_options is False
        assert config.show_help_text is True
        assert config.show_advanced_sections is False
        assert config.show_palette_section is False
        assert config.show_dynamics_section is True
        assert config.allow_raw_values is True
        assert config.use_friendly_labels is True
        assert config.show_current_values is True

    def test_advanced_mode_config(self):
        """Test Advanced Mode configuration defaults."""
        config = ModeConfig.for_mode(InteractionMode.ADVANCED)

        assert config.mode == InteractionMode.ADVANCED
        assert config.show_technical_values is True
        assert config.show_presets is True
        assert config.show_all_options is True
        assert config.show_help_text is True
        assert config.show_advanced_sections is True
        assert config.show_palette_section is True
        assert config.show_dynamics_section is True
        assert config.show_gradient_section is True
        assert config.show_recall_section is True
        assert config.allow_raw_values is True
        assert config.use_friendly_labels is False


class TestModeDescriptions:
    """Tests for mode descriptions and icons."""

    def test_all_modes_have_descriptions(self):
        """Verify every mode has a description."""
        for mode in InteractionMode:
            assert mode in MODE_DESCRIPTIONS
            assert len(MODE_DESCRIPTIONS[mode]) > 0

    def test_all_modes_have_icons(self):
        """Verify every mode has an icon."""
        for mode in InteractionMode:
            assert mode in MODE_ICONS
            assert len(MODE_ICONS[mode]) > 0

    def test_get_mode_label(self):
        """Test get_mode_label function."""
        label = get_mode_label(InteractionMode.SIMPLE)
        assert "Simple" in label
        assert MODE_ICONS[InteractionMode.SIMPLE] in label

    def test_get_mode_description(self):
        """Test get_mode_description function."""
        desc = get_mode_description(InteractionMode.ADVANCED)
        assert len(desc) > 0
        assert desc == MODE_DESCRIPTIONS[InteractionMode.ADVANCED]


class TestDetectUserMode:
    """Tests for detect_user_mode function."""

    @pytest.mark.asyncio
    async def test_detect_user_mode_returns_default_on_cancel(self):
        """Test that cancellation returns default mode."""
        with patch('questionary.select') as mock_select:
            mock_select.return_value.ask_async = AsyncMock(return_value=None)

            result = await detect_user_mode(default=InteractionMode.ADVANCED)

            assert result == InteractionMode.ADVANCED

    @pytest.mark.asyncio
    async def test_detect_user_mode_returns_selected_mode(self):
        """Test that selection returns chosen mode."""
        with patch('questionary.select') as mock_select:
            mock_select.return_value.ask_async = AsyncMock(
                return_value=InteractionMode.SIMPLE
            )

            result = await detect_user_mode(default=InteractionMode.ADVANCED)

            assert result == InteractionMode.SIMPLE

    @pytest.mark.asyncio
    async def test_detect_user_mode_handles_keyboard_interrupt(self):
        """Test that KeyboardInterrupt returns default mode."""
        with patch('questionary.select') as mock_select:
            mock_select.return_value.ask_async = AsyncMock(
                side_effect=KeyboardInterrupt
            )

            result = await detect_user_mode(default=InteractionMode.STANDARD)

            assert result == InteractionMode.STANDARD


class TestModeConfigIntegration:
    """Integration tests for mode configuration."""

    def test_simple_mode_hides_advanced_features(self):
        """Verify Simple Mode hides advanced sections."""
        config = ModeConfig.for_mode(InteractionMode.SIMPLE)

        # Should hide all advanced sections
        assert not config.show_palette_section
        assert not config.show_dynamics_section
        assert not config.show_gradient_section
        assert not config.show_recall_section
        assert not config.show_advanced_sections

    def test_standard_mode_shows_some_technical(self):
        """Verify Standard Mode shows technical values with help."""
        config = ModeConfig.for_mode(InteractionMode.STANDARD)

        assert config.show_technical_values
        assert config.show_help_text
        assert config.show_dynamics_section
        assert not config.show_palette_section  # Still hidden

    def test_advanced_mode_shows_everything(self):
        """Verify Advanced Mode shows all features."""
        config = ModeConfig.for_mode(InteractionMode.ADVANCED)

        assert config.show_technical_values
        assert config.show_all_options
        assert config.show_palette_section
        assert config.show_dynamics_section
        assert config.show_gradient_section
        assert config.show_recall_section
        assert config.show_advanced_sections
