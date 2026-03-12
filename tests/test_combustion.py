"""Tests for combustion calculations."""

import pytest

from vedic_calc import calculate_chart
from vedic_calc.core.constants import Planet
from vedic_calc.chart.combustion import calculate_combustion


@pytest.fixture
def mumbai_chart():
    return calculate_chart(
        year=1990, month=3, day=15, hour=10, minute=30,
        latitude=19.0760, longitude=72.8777, timezone_offset=5.5,
    )


class TestCombustionStructure:
    def test_returns_list(self, mumbai_chart):
        results = calculate_combustion(mumbai_chart)
        assert isinstance(results, list)

    def test_excludes_sun_rahu_ketu(self, mumbai_chart):
        """Sun, Rahu, and Ketu should not be in combustion results."""
        results = calculate_combustion(mumbai_chart)
        planets_checked = {r.planet for r in results}
        assert Planet.SUN not in planets_checked
        assert Planet.RAHU not in planets_checked
        assert Planet.KETU not in planets_checked

    def test_includes_all_combustible_planets(self, mumbai_chart):
        """Moon, Mars, Mercury, Jupiter, Venus, Saturn should be checked."""
        results = calculate_combustion(mumbai_chart)
        planets_checked = {r.planet for r in results}
        for p in [Planet.MOON, Planet.MARS, Planet.MERCURY, Planet.JUPITER, Planet.VENUS, Planet.SATURN]:
            assert p in planets_checked


class TestCombustionValues:
    def test_distance_positive(self, mumbai_chart):
        """Distance from Sun should always be positive."""
        results = calculate_combustion(mumbai_chart)
        for r in results:
            assert r.distance_from_sun >= 0

    def test_distance_max_180(self, mumbai_chart):
        """Distance should never exceed 180° (shortest arc)."""
        results = calculate_combustion(mumbai_chart)
        for r in results:
            assert r.distance_from_sun <= 180

    def test_combust_when_close(self, mumbai_chart):
        """A planet closer than its threshold should be combust."""
        results = calculate_combustion(mumbai_chart)
        for r in results:
            if r.distance_from_sun < r.threshold:
                assert r.is_combust
            else:
                assert not r.is_combust

    def test_threshold_reasonable(self, mumbai_chart):
        """Thresholds should be in expected ranges (8° to 17°)."""
        results = calculate_combustion(mumbai_chart)
        for r in results:
            assert 8 <= r.threshold <= 17
