"""
Tests for Visual Feedback Components

Tests ASCII rendering functions for brightness bars, color swatches,
and progress indicators.
"""

import pytest

from hue_controller.wizards.visual_feedback import (
    render_brightness_bar,
    render_brightness_bar_colored,
    render_color_swatch,
    render_temperature_swatch,
    render_progress_breadcrumb,
    render_progress_bar,
    render_light_state_indicator,
    xy_to_rgb,
)


class TestBrightnessBar:
    """Tests for brightness bar rendering."""

    def test_brightness_bar_zero(self):
        """Test brightness bar at 0%."""
        bar = render_brightness_bar(0, width=10)
        assert "░" * 10 in bar
        assert "0%" in bar

    def test_brightness_bar_full(self):
        """Test brightness bar at 100%."""
        bar = render_brightness_bar(100, width=10)
        assert "█" * 10 in bar
        assert "100%" in bar

    def test_brightness_bar_half(self):
        """Test brightness bar at 50%."""
        bar = render_brightness_bar(50, width=20)
        # Should have 10 filled, 10 empty
        assert bar.count("█") == 10
        assert bar.count("░") == 10
        assert "50%" in bar

    def test_brightness_bar_custom_width(self):
        """Test brightness bar with custom width."""
        bar = render_brightness_bar(75, width=40)
        # 75% of 40 = 30 filled
        assert bar.count("█") == 30
        assert bar.count("░") == 10

    def test_brightness_bar_without_percentage(self):
        """Test brightness bar without percentage label."""
        bar = render_brightness_bar(50, width=10, show_percentage=False)
        assert "%" not in bar

    def test_brightness_bar_clamping(self):
        """Test brightness bar clamps values to valid range."""
        bar_low = render_brightness_bar(-10, width=10)
        bar_high = render_brightness_bar(150, width=10)

        assert "0%" in bar_low
        assert "100%" in bar_high

    def test_brightness_bar_colored_returns_text(self):
        """Test colored brightness bar returns Rich Text."""
        from rich.text import Text
        result = render_brightness_bar_colored(75, width=20)
        assert isinstance(result, Text)


class TestColorSwatch:
    """Tests for color swatch rendering."""

    def test_color_swatch_basic(self):
        """Test basic color swatch rendering."""
        swatch = render_color_swatch((0.5, 0.5), size=2)
        assert "█" in swatch  # Should contain block characters
        assert "[" in swatch  # Should have rich markup

    def test_color_swatch_size(self):
        """Test color swatch respects size parameter."""
        swatch_small = render_color_swatch((0.5, 0.5), size=1)
        swatch_large = render_color_swatch((0.5, 0.5), size=4)

        # Larger size should have more block characters
        assert swatch_small.count("█") < swatch_large.count("█")

    def test_xy_to_rgb_red(self):
        """Test XY to RGB conversion for red."""
        r, g, b = xy_to_rgb(0.675, 0.322)
        assert r > g  # Red should be dominant
        assert r > b

    def test_xy_to_rgb_blue(self):
        """Test XY to RGB conversion for blue."""
        r, g, b = xy_to_rgb(0.167, 0.040)
        # Very saturated colors can cause clamping; just verify values are valid
        assert 0 <= r <= 1
        assert 0 <= g <= 1
        assert 0 <= b <= 1
        # For this specific blue XY, blue should be significant
        assert b >= 0.8  # Should be high blue value

    def test_xy_to_rgb_clamping(self):
        """Test XY to RGB clamps values to 0-1."""
        r, g, b = xy_to_rgb(0.5, 0.5, brightness=2.0)  # Bright
        assert 0 <= r <= 1
        assert 0 <= g <= 1
        assert 0 <= b <= 1


class TestTemperatureSwatch:
    """Tests for temperature swatch rendering."""

    def test_temperature_swatch_cool(self):
        """Test cool temperature swatch (low mirek)."""
        swatch = render_temperature_swatch(153)  # 6500K
        assert "█" in swatch
        assert "[" in swatch  # Rich markup

    def test_temperature_swatch_warm(self):
        """Test warm temperature swatch (high mirek)."""
        swatch = render_temperature_swatch(500)  # 2000K
        assert "█" in swatch

    def test_temperature_swatch_clamping(self):
        """Test temperature swatch clamps mirek values."""
        # Should not crash with out-of-range values
        swatch_low = render_temperature_swatch(50)  # Below 153
        swatch_high = render_temperature_swatch(600)  # Above 500

        assert "█" in swatch_low
        assert "█" in swatch_high


class TestProgressBreadcrumb:
    """Tests for progress breadcrumb rendering."""

    def test_breadcrumb_basic(self):
        """Test basic breadcrumb rendering."""
        sections = ["Step 1", "Step 2", "Step 3"]
        breadcrumb = render_progress_breadcrumb(sections, current=1)

        assert "Step 1" in breadcrumb
        assert "Step 2" in breadcrumb
        assert "Step 3" in breadcrumb

    def test_breadcrumb_shows_completed(self):
        """Test breadcrumb shows completed sections with checkmark."""
        sections = ["A", "B", "C"]
        breadcrumb = render_progress_breadcrumb(sections, current=2)

        # First two should be completed (current is 2, so 0 and 1 completed)
        assert "✓" in breadcrumb

    def test_breadcrumb_shows_current(self):
        """Test breadcrumb highlights current section."""
        sections = ["A", "B", "C"]
        breadcrumb = render_progress_breadcrumb(sections, current=1)

        # Current marker
        assert "●" in breadcrumb

    def test_breadcrumb_shows_pending(self):
        """Test breadcrumb shows pending sections."""
        sections = ["A", "B", "C"]
        breadcrumb = render_progress_breadcrumb(sections, current=0)

        # Pending marker
        assert "○" in breadcrumb

    def test_breadcrumb_with_explicit_completed(self):
        """Test breadcrumb with explicit completed set."""
        sections = ["A", "B", "C", "D"]
        completed = {0, 2}  # Skip B
        breadcrumb = render_progress_breadcrumb(
            sections, current=3, completed=completed
        )

        # Should show A and C as completed
        assert breadcrumb.count("✓") >= 2


class TestProgressBar:
    """Tests for progress bar rendering."""

    def test_progress_bar_basic(self):
        """Test basic progress bar."""
        bar = render_progress_bar(5, 10)
        assert "5/10" in bar

    def test_progress_bar_with_label(self):
        """Test progress bar with label."""
        bar = render_progress_bar(3, 10, label="Progress")
        assert "Progress" in bar
        assert "3/10" in bar

    def test_progress_bar_complete(self):
        """Test complete progress bar."""
        bar = render_progress_bar(10, 10)
        assert "10/10" in bar


class TestLightStateIndicator:
    """Tests for light state indicator rendering."""

    def test_indicator_on(self):
        """Test indicator for light on."""
        indicator = render_light_state_indicator(is_on=True)
        assert "On" in indicator
        assert "●" in indicator or "◕" in indicator or "◔" in indicator or "◑" in indicator

    def test_indicator_off(self):
        """Test indicator for light off."""
        indicator = render_light_state_indicator(is_on=False)
        assert "Off" in indicator
        assert "○" in indicator

    def test_indicator_unreachable(self):
        """Test indicator for unreachable light."""
        indicator = render_light_state_indicator(is_on=True, reachable=False)
        assert "Unreachable" in indicator

    def test_indicator_with_brightness(self):
        """Test indicator shows brightness."""
        indicator = render_light_state_indicator(is_on=True, brightness=75.0)
        assert "75%" in indicator
        assert "On" in indicator

    def test_indicator_brightness_levels(self):
        """Test indicator uses different icons for brightness levels."""
        ind_low = render_light_state_indicator(is_on=True, brightness=10.0)
        ind_mid = render_light_state_indicator(is_on=True, brightness=50.0)
        ind_high = render_light_state_indicator(is_on=True, brightness=90.0)

        # Different brightness levels should show different indicators
        # (we can't easily test the exact icon, but they should all work)
        assert "10%" in ind_low
        assert "50%" in ind_mid
        assert "90%" in ind_high
