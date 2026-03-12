"""Tests for transit chart calculations."""

import pytest

from vedic_calc.core.constants import Planet, Sign
from vedic_calc.chart.transits import calculate_transit_chart


class TestTransitChart:
    def test_returns_transit_chart(self):
        tc = calculate_transit_chart(2026, 3, 12, 12, 0, 0, 19.076, 72.878, 5.5)
        assert tc is not None
        assert len(tc.planets) == 9

    def test_all_planets_present(self):
        tc = calculate_transit_chart(2026, 3, 12, 12, 0, 0, 19.076, 72.878, 5.5)
        for planet in Planet:
            assert planet in tc.planets

    def test_valid_longitudes(self):
        tc = calculate_transit_chart(2026, 3, 12, 12, 0, 0, 19.076, 72.878, 5.5)
        for planet, pos in tc.planets.items():
            assert 0 <= pos.longitude < 360

    def test_different_dates_different_positions(self):
        tc1 = calculate_transit_chart(2026, 3, 12, 12, 0, 0, 19.076, 72.878, 5.5)
        tc2 = calculate_transit_chart(2026, 6, 12, 12, 0, 0, 19.076, 72.878, 5.5)
        # Moon should definitely move between March and June
        assert tc1.planets[Planet.MOON].longitude != tc2.planets[Planet.MOON].longitude
