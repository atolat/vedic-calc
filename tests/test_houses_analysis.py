"""Tests for house analysis."""

import pytest

from vedic_calc import calculate_chart
from vedic_calc.core.constants import Planet, Sign
from vedic_calc.chart.houses import analyze_houses


@pytest.fixture
def mumbai_chart():
    return calculate_chart(
        year=1990, month=3, day=15, hour=10, minute=30,
        latitude=19.0760, longitude=72.8777, timezone_offset=5.5,
    )


class TestHouseAnalysisStructure:
    def test_returns_12_houses(self, mumbai_chart):
        analysis = analyze_houses(mumbai_chart)
        assert len(analysis) == 12

    def test_house_numbers_sequential(self, mumbai_chart):
        analysis = analyze_houses(mumbai_chart)
        for i, house in enumerate(analysis):
            assert house.house_number == i + 1

    def test_signs_match_chart(self, mumbai_chart):
        analysis = analyze_houses(mumbai_chart)
        for i, house in enumerate(analysis):
            assert house.sign == mumbai_chart.houses[i].sign


class TestHouseCategories:
    def test_valid_categories(self, mumbai_chart):
        analysis = analyze_houses(mumbai_chart)
        valid = {"kendra", "trikona", "dusthana", "upachaya", "maraka", "neutral"}
        for house in analysis:
            assert house.category in valid, f"House {house.house_number}: '{house.category}'"

    def test_kendras_marked(self, mumbai_chart):
        analysis = analyze_houses(mumbai_chart)
        for house in analysis:
            if house.house_number in [1, 4, 7, 10]:
                assert house.category in {"kendra", "trikona"}  # 1 is both kendra and trikona


class TestOccupantsAndAspects:
    def test_all_planets_in_some_house(self, mumbai_chart):
        """Every planet should appear as an occupant in exactly one house."""
        analysis = analyze_houses(mumbai_chart)
        all_occupants = []
        for house in analysis:
            all_occupants.extend(house.occupants)
        assert len(all_occupants) == 9  # 9 planets
        assert set(all_occupants) == set(Planet)

    def test_aspected_by_non_empty(self, mumbai_chart):
        """At least some houses should be aspected by planets."""
        analysis = analyze_houses(mumbai_chart)
        total_aspects = sum(len(h.aspected_by) for h in analysis)
        assert total_aspects > 0
