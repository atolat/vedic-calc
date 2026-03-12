"""Tests for Saham (Arabic Parts) calculations."""

import pytest

from vedic_calc import calculate_chart
from vedic_calc.core.constants import Planet, Sign
from vedic_calc.chart.sahams import calculate_sahams


@pytest.fixture
def mumbai_chart():
    return calculate_chart(
        year=1990, month=3, day=15, hour=10, minute=30,
        latitude=19.0760, longitude=72.8777, timezone_offset=5.5,
    )


class TestSahamStructure:
    def test_returns_list(self, mumbai_chart):
        sahams = calculate_sahams(mumbai_chart)
        assert isinstance(sahams, list)
        assert len(sahams) > 0

    def test_valid_longitudes(self, mumbai_chart):
        sahams = calculate_sahams(mumbai_chart)
        for s in sahams:
            assert 0 <= s.longitude < 360

    def test_sign_matches_longitude(self, mumbai_chart):
        sahams = calculate_sahams(mumbai_chart)
        for s in sahams:
            expected_sign = int(s.longitude / 30.0) + 1
            assert s.sign.value == expected_sign

    def test_has_punya_saham(self, mumbai_chart):
        sahams = calculate_sahams(mumbai_chart)
        names = {s.name for s in sahams}
        assert "Punya" in names
