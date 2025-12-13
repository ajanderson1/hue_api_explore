"""
Tests for Glossary System

Tests glossary lookup, formatting, and term definitions.
"""

import pytest

from hue_controller.wizards.glossary import (
    GlossaryEntry,
    GLOSSARY,
    get_glossary_entry,
    format_glossary_entry,
    list_all_terms,
    search_glossary,
    get_simple_label,
)


class TestGlossaryEntry:
    """Tests for GlossaryEntry dataclass."""

    def test_glossary_entry_creation(self):
        """Test basic entry creation."""
        entry = GlossaryEntry(
            term="Test Term",
            definition="A test definition.",
        )
        assert entry.term == "Test Term"
        assert entry.definition == "A test definition."
        assert entry.example is None
        assert entry.related_terms == []

    def test_glossary_entry_with_all_fields(self):
        """Test entry with all fields populated."""
        entry = GlossaryEntry(
            term="Mirek",
            definition="Color temperature unit.",
            example="370 = warm white",
            related_terms=["kelvin", "color temperature"],
            technical_note="Mirek = 1M / Kelvin",
            simple_label="warmth",
        )
        assert entry.term == "Mirek"
        assert entry.example == "370 = warm white"
        assert "kelvin" in entry.related_terms
        assert entry.simple_label == "warmth"


class TestGlossaryLookup:
    """Tests for glossary lookup functions."""

    def test_exact_lookup(self):
        """Test exact term match."""
        entry = get_glossary_entry("mirek")
        assert entry is not None
        assert entry.term.lower() == "mirek"

    def test_case_insensitive_lookup(self):
        """Test case-insensitive lookup."""
        entry1 = get_glossary_entry("MIREK")
        entry2 = get_glossary_entry("Mirek")
        entry3 = get_glossary_entry("mirek")

        assert entry1 is not None
        assert entry2 is not None
        assert entry3 is not None
        assert entry1.term == entry2.term == entry3.term

    def test_plural_handling(self):
        """Test plural form lookup."""
        # 'mireks' should find 'mirek'
        entry = get_glossary_entry("mireks")
        assert entry is not None
        assert "mirek" in entry.term.lower()

    def test_variation_handling(self):
        """Test common variation lookup."""
        # 'xy' should find 'xy color'
        entry = get_glossary_entry("xy")
        assert entry is not None

        # 'bri' should find 'brightness'
        entry = get_glossary_entry("bri")
        assert entry is not None
        assert "brightness" in entry.term.lower()

    def test_not_found(self):
        """Test lookup for non-existent term."""
        entry = get_glossary_entry("nonexistent_term_xyz")
        assert entry is None

    def test_empty_lookup(self):
        """Test lookup with empty string."""
        entry = get_glossary_entry("")
        assert entry is None

        entry = get_glossary_entry(None)
        assert entry is None


class TestGlossaryFormatting:
    """Tests for glossary entry formatting."""

    def test_format_simple(self):
        """Test simple (non-detailed) formatting."""
        entry = get_glossary_entry("mirek")
        formatted = format_glossary_entry(entry, detailed=False)

        assert "Mirek" in formatted
        assert entry.definition in formatted

    def test_format_detailed(self):
        """Test detailed formatting includes all parts."""
        entry = get_glossary_entry("mirek")
        formatted = format_glossary_entry(entry, detailed=True)

        assert entry.term in formatted
        assert entry.definition in formatted
        if entry.example:
            assert "Example" in formatted
        if entry.technical_note:
            assert "Technical" in formatted

    def test_format_with_related_terms(self):
        """Test formatting includes related terms."""
        entry = get_glossary_entry("mirek")
        formatted = format_glossary_entry(entry, detailed=True)

        if entry.related_terms:
            assert "See also" in formatted


class TestGlossaryContent:
    """Tests for glossary content completeness."""

    def test_glossary_not_empty(self):
        """Test that glossary has entries."""
        assert len(GLOSSARY) > 0

    def test_key_terms_exist(self):
        """Test that key Hue terms are defined."""
        key_terms = [
            "mirek",
            "color temperature",
            "kelvin",
            "gamut",
            "xy color",
            "grouped light",
            "dynamics",
            "signaling",
            "gradient",
            "scene",
            "palette",
            "effect",
            "entertainment area",
            "brightness",
            "room",
            "zone",
        ]

        for term in key_terms:
            entry = get_glossary_entry(term)
            assert entry is not None, f"Missing glossary entry for '{term}'"

    def test_all_entries_have_definitions(self):
        """Test all glossary entries have definitions."""
        for term, entry in GLOSSARY.items():
            assert entry.definition, f"Entry '{term}' has no definition"
            assert len(entry.definition) > 10, f"Entry '{term}' has too short definition"


class TestGlossarySearch:
    """Tests for glossary search functionality."""

    def test_search_by_term_name(self):
        """Test searching by term name."""
        results = search_glossary("color")
        assert len(results) > 0

        # Should find 'color temperature', 'xy color', etc.
        found_terms = [r.term.lower() for r in results]
        assert any("color" in term for term in found_terms)

    def test_search_in_definition(self):
        """Test searching within definitions."""
        results = search_glossary("temperature")
        assert len(results) > 0

    def test_search_empty_query(self):
        """Test searching with empty query."""
        results = search_glossary("")
        assert results == []

    def test_list_all_terms(self):
        """Test listing all terms."""
        terms = list_all_terms()
        assert len(terms) > 0
        assert terms == sorted(terms)  # Should be sorted


class TestSimpleLabels:
    """Tests for Simple Mode labels."""

    def test_get_simple_label_exists(self):
        """Test getting simple labels for known terms."""
        label = get_simple_label("mirek")
        assert label is not None
        assert label == "warmth"

    def test_get_simple_label_missing(self):
        """Test getting simple label for term without one."""
        # Entertainment area doesn't have a simple label
        label = get_simple_label("entertainment area")
        assert label is None

    def test_simple_labels_are_friendly(self):
        """Test that simple labels are user-friendly."""
        # Get all entries with simple labels
        entries_with_labels = [
            e for e in GLOSSARY.values()
            if e.simple_label
        ]

        assert len(entries_with_labels) > 0

        # Labels should not contain technical jargon
        technical_terms = ["mirek", "xy", "cie", "api", "http"]
        for entry in entries_with_labels:
            label_lower = entry.simple_label.lower()
            for tech in technical_terms:
                assert tech not in label_lower, (
                    f"Simple label '{entry.simple_label}' contains technical term '{tech}'"
                )
