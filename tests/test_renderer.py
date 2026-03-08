"""Tests for the Kundali (chart) renderer."""

import pytest

from vedic_calc import calculate_chart, render_north_indian, render_south_indian, render_svg
from vedic_calc.core.constants import PLANET_ABBREVIATIONS


@pytest.fixture
def mumbai_chart():
    """Birth chart: March 15, 1990, 10:30 AM IST, Mumbai."""
    return calculate_chart(
        year=1990, month=3, day=15,
        hour=10, minute=30,
        latitude=19.0760, longitude=72.8777,
        timezone_offset=5.5,
    )


# ---------------------------------------------------------------------------
# South Indian chart
# ---------------------------------------------------------------------------

class TestSouthIndian:
    """Test South Indian style chart rendering."""

    def test_returns_string(self, mumbai_chart):
        result = render_south_indian(mumbai_chart)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_sign_abbreviations(self, mumbai_chart):
        result = render_south_indian(mumbai_chart)
        # South Indian chart should contain fixed sign abbreviations
        assert "Ar" in result  # Aries
        assert "Ta" in result  # Taurus
        assert "Pi" in result  # Pisces

    def test_contains_planet_abbreviations(self, mumbai_chart):
        result = render_south_indian(mumbai_chart)
        # All 9 planets should appear somewhere in the chart
        for abbr in PLANET_ABBREVIATIONS.values():
            assert abbr in result, f"Missing planet {abbr} in South Indian chart"

    def test_contains_ascendant_marker(self, mumbai_chart):
        result = render_south_indian(mumbai_chart)
        assert "Asc" in result

    def test_multiline_output(self, mumbai_chart):
        result = render_south_indian(mumbai_chart)
        lines = result.strip().split("\n")
        assert len(lines) > 5  # Should be a multi-line chart


# ---------------------------------------------------------------------------
# North Indian chart
# ---------------------------------------------------------------------------

class TestNorthIndian:
    """Test North Indian style chart rendering."""

    def test_returns_string(self, mumbai_chart):
        result = render_north_indian(mumbai_chart)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_house_labels(self, mumbai_chart):
        result = render_north_indian(mumbai_chart)
        # Should contain house labels like H1, H7, H12
        assert "H1:" in result
        assert "H7:" in result

    def test_contains_planet_abbreviations(self, mumbai_chart):
        result = render_north_indian(mumbai_chart)
        for abbr in PLANET_ABBREVIATIONS.values():
            assert abbr in result, f"Missing planet {abbr} in North Indian chart"

    def test_ascendant_marked(self, mumbai_chart):
        """H1 should have an asterisk marking the ascendant."""
        result = render_north_indian(mumbai_chart)
        assert "H1:" in result
        # The ascendant house should be marked with *
        assert "*" in result


# ---------------------------------------------------------------------------
# SVG output
# ---------------------------------------------------------------------------

class TestSVG:
    """Test SVG chart rendering."""

    def test_svg_south_starts_correctly(self, mumbai_chart):
        svg = render_svg(mumbai_chart, style="south")
        assert svg.strip().startswith("<svg")
        assert svg.strip().endswith("</svg>")

    def test_svg_north_starts_correctly(self, mumbai_chart):
        svg = render_svg(mumbai_chart, style="north")
        assert svg.strip().startswith("<svg")
        assert svg.strip().endswith("</svg>")

    def test_svg_contains_planets(self, mumbai_chart):
        svg = render_svg(mumbai_chart, style="south")
        for abbr in PLANET_ABBREVIATIONS.values():
            assert abbr in svg, f"Missing planet {abbr} in SVG"

    def test_svg_contains_birth_date(self, mumbai_chart):
        svg = render_svg(mumbai_chart)
        assert "1990-03-15" in svg
