"""Tests for planetary state/dignity calculations."""

import pytest

from vedic_calc import calculate_chart
from vedic_calc.core.constants import Planet, Sign
from vedic_calc.chart.states import calculate_planet_states


@pytest.fixture
def mumbai_chart():
    return calculate_chart(
        year=1990, month=3, day=15, hour=10, minute=30,
        latitude=19.0760, longitude=72.8777, timezone_offset=5.5,
    )


class TestPlanetStateStructure:
    def test_returns_all_planets(self, mumbai_chart):
        states = calculate_planet_states(mumbai_chart)
        assert len(states) == 9
        for planet in Planet:
            assert planet in states

    def test_state_has_required_fields(self, mumbai_chart):
        states = calculate_planet_states(mumbai_chart)
        for planet, state in states.items():
            assert hasattr(state, "dignity")
            assert hasattr(state, "is_combust")
            assert hasattr(state, "is_retrograde")
            assert hasattr(state, "is_vargottama")
            assert hasattr(state, "sign")
            assert hasattr(state, "sign_lord")


class TestDignityValues:
    def test_valid_dignity_values(self, mumbai_chart):
        states = calculate_planet_states(mumbai_chart)
        valid = {"exalted", "moolatrikona", "own_sign", "friend", "neutral", "enemy", "debilitated"}
        for planet, state in states.items():
            assert state.dignity in valid, f"{planet.name}: invalid dignity '{state.dignity}'"

    def test_retrograde_matches_chart(self, mumbai_chart):
        states = calculate_planet_states(mumbai_chart)
        for planet, state in states.items():
            assert state.is_retrograde == mumbai_chart.planets[planet].is_retrograde

    def test_sign_matches_chart(self, mumbai_chart):
        states = calculate_planet_states(mumbai_chart)
        for planet, state in states.items():
            assert state.sign == mumbai_chart.planets[planet].sign
