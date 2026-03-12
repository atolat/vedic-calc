"""Tests for Porutham (South Indian compatibility) calculations."""

import pytest

from vedic_calc import calculate_chart
from vedic_calc.core.constants import Planet
from vedic_calc.compatibility.porutham import calculate_porutham


@pytest.fixture
def chart_a():
    return calculate_chart(
        year=1990, month=3, day=15, hour=10, minute=30,
        latitude=19.0760, longitude=72.8777, timezone_offset=5.5,
    )


@pytest.fixture
def chart_b():
    return calculate_chart(
        year=1985, month=7, day=22, hour=5, minute=15,
        latitude=28.6139, longitude=77.2090, timezone_offset=5.5,
    )


class TestPoruthamStructure:
    def test_returns_10_factors(self, chart_a, chart_b):
        result = calculate_porutham(chart_a, chart_b)
        assert len(result.factors) == 10
        assert result.total_factors == 10

    def test_factor_names(self, chart_a, chart_b):
        result = calculate_porutham(chart_a, chart_b)
        names = {f.name for f in result.factors}
        expected = {"Dina", "Gana", "Mahendra", "Stree Dirgha", "Yoni",
                    "Rasi", "Rasiyathipathi", "Vasya", "Rajju", "Vedha"}
        assert names == expected

    def test_matched_count_valid(self, chart_a, chart_b):
        result = calculate_porutham(chart_a, chart_b)
        assert 0 <= result.matched_count <= 10
        actual_matched = sum(1 for f in result.factors if f.matched)
        assert result.matched_count == actual_matched
