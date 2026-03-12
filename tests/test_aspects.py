"""Tests for planetary aspect calculations."""

import pytest

from vedic_calc import calculate_chart
from vedic_calc.core.constants import Planet, Sign
from vedic_calc.chart.aspects import calculate_aspects


@pytest.fixture
def mumbai_chart():
    return calculate_chart(
        year=1990, month=3, day=15, hour=10, minute=30,
        latitude=19.0760, longitude=72.8777, timezone_offset=5.5,
    )


class TestAspectStructure:
    def test_returns_list(self, mumbai_chart):
        aspects = calculate_aspects(mumbai_chart)
        assert isinstance(aspects, list)
        assert len(aspects) > 0

    def test_all_aspects_have_required_fields(self, mumbai_chart):
        aspects = calculate_aspects(mumbai_chart)
        for a in aspects:
            assert hasattr(a, "aspecting_planet")
            assert hasattr(a, "aspected_house")
            assert 1 <= a.aspected_house <= 12

    def test_all_planets_aspect_7th(self, mumbai_chart):
        """Every planet should have at least a 7th house aspect."""
        aspects = calculate_aspects(mumbai_chart)
        aspecting_planets = {a.aspecting_planet for a in aspects}
        for planet in Planet:
            assert planet in aspecting_planets, f"{planet.name} has no aspects"


class TestSpecialAspects:
    def test_mars_has_special_aspects(self, mumbai_chart):
        """Mars should have aspects on 4th, 7th, and 8th houses."""
        aspects = calculate_aspects(mumbai_chart)
        mars_aspects = [a for a in aspects if a.aspecting_planet == Planet.MARS]
        # Mars should have at least 3 aspects (4th, 7th, 8th)
        assert len(mars_aspects) >= 3

    def test_jupiter_has_special_aspects(self, mumbai_chart):
        """Jupiter should have aspects on 5th, 7th, and 9th houses."""
        aspects = calculate_aspects(mumbai_chart)
        jupiter_aspects = [a for a in aspects if a.aspecting_planet == Planet.JUPITER]
        assert len(jupiter_aspects) >= 3

    def test_saturn_has_special_aspects(self, mumbai_chart):
        """Saturn should have aspects on 3rd, 7th, and 10th houses."""
        aspects = calculate_aspects(mumbai_chart)
        saturn_aspects = [a for a in aspects if a.aspecting_planet == Planet.SATURN]
        assert len(saturn_aspects) >= 3

    def test_special_aspects_marked(self, mumbai_chart):
        """Special aspects should be marked with is_special=True."""
        aspects = calculate_aspects(mumbai_chart)
        mars_special = [a for a in aspects if a.aspecting_planet == Planet.MARS and a.is_special]
        assert len(mars_special) >= 2  # 4th and 8th are special
