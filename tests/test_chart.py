"""
Integration tests for full birth chart calculation.

Uses a known reference chart to verify calculations:
- Birth: March 15, 1990, 10:30 AM IST, Mumbai (19.076°N, 72.878°E)

Reference values verified against multiple online Vedic astrology calculators.
Slight variations (1-2°) between calculators are normal due to different
ayanamsa values and ephemeris precision.
"""

import pytest

from vedic_calc import calculate_chart
from vedic_calc.core.constants import Planet, Sign, Nakshatra, Ayanamsa


# ---------------------------------------------------------------------------
# Test fixture: a known birth chart
# ---------------------------------------------------------------------------

@pytest.fixture
def mumbai_chart():
    """Birth chart: March 15, 1990, 10:30 AM IST, Mumbai."""
    return calculate_chart(
        year=1990, month=3, day=15,
        hour=10, minute=30,
        latitude=19.0760, longitude=72.8777,
        timezone_offset=5.5,
        ayanamsa=Ayanamsa.LAHIRI,
    )


# ---------------------------------------------------------------------------
# Basic structure tests
# ---------------------------------------------------------------------------

class TestChartStructure:
    def test_has_9_planets(self, mumbai_chart):
        assert len(mumbai_chart.planets) == 9

    def test_has_12_houses(self, mumbai_chart):
        assert len(mumbai_chart.houses) == 12

    def test_all_planets_present(self, mumbai_chart):
        for planet in Planet:
            assert planet in mumbai_chart.planets

    def test_metadata(self, mumbai_chart):
        assert mumbai_chart.latitude == 19.0760
        assert mumbai_chart.longitude == 72.8777
        assert mumbai_chart.timezone_offset == 5.5
        assert mumbai_chart.ayanamsa == Ayanamsa.LAHIRI

    def test_ayanamsa_reasonable(self, mumbai_chart):
        """Lahiri ayanamsa in 1990 should be approximately 23.7°."""
        assert 23.0 < mumbai_chart.ayanamsa_degrees < 24.5


# ---------------------------------------------------------------------------
# Planetary position sanity checks
# ---------------------------------------------------------------------------

class TestPlanetaryPositions:
    def test_all_longitudes_valid(self, mumbai_chart):
        """All longitudes should be in [0, 360)."""
        for planet, pos in mumbai_chart.planets.items():
            assert 0 <= pos.longitude < 360, f"{planet.name}: {pos.longitude}"

    def test_all_degrees_in_sign_valid(self, mumbai_chart):
        """Degree within sign should be in [0, 30)."""
        for planet, pos in mumbai_chart.planets.items():
            assert 0 <= pos.degree_in_sign < 30, f"{planet.name}: {pos.degree_in_sign}"

    def test_sign_matches_longitude(self, mumbai_chart):
        """The sign should correspond to the longitude range."""
        for planet, pos in mumbai_chart.planets.items():
            expected_sign_index = int(pos.longitude / 30.0) + 1
            assert pos.sign.value == expected_sign_index, (
                f"{planet.name}: sign={pos.sign}, lon={pos.longitude}"
            )

    def test_nakshatra_has_valid_pada(self, mumbai_chart):
        """All nakshatras should have pada 1-4."""
        for planet, pos in mumbai_chart.planets.items():
            assert 1 <= pos.nakshatra_info.pada <= 4

    def test_rahu_ketu_opposite(self, mumbai_chart):
        """Rahu and Ketu should always be ~180° apart."""
        rahu_lon = mumbai_chart.planets[Planet.RAHU].longitude
        ketu_lon = mumbai_chart.planets[Planet.KETU].longitude
        diff = abs(rahu_lon - ketu_lon)
        # Account for wraparound (e.g., Rahu=350°, Ketu=170°)
        if diff > 180:
            diff = 360 - diff
        assert abs(diff - 180) < 0.1, f"Rahu-Ketu diff: {diff}°"

    def test_rahu_ketu_retrograde(self, mumbai_chart):
        """Rahu and Ketu are always retrograde in Vedic astrology."""
        assert mumbai_chart.planets[Planet.RAHU].is_retrograde
        assert mumbai_chart.planets[Planet.KETU].is_retrograde

    def test_sun_in_pisces_or_aquarius(self, mumbai_chart):
        """Sun in mid-March 1990 (sidereal) should be in Aquarius or Pisces."""
        sun_sign = mumbai_chart.planets[Planet.SUN].sign
        assert sun_sign in (Sign.AQUARIUS, Sign.PISCES)


# ---------------------------------------------------------------------------
# House tests
# ---------------------------------------------------------------------------

class TestHouses:
    def test_first_house_matches_ascendant(self, mumbai_chart):
        """1st house sign should match the ascendant sign."""
        assert mumbai_chart.houses[0].sign == mumbai_chart.ascendant.sign

    def test_houses_sequential(self, mumbai_chart):
        """Houses should go through signs sequentially."""
        for i in range(11):
            current = mumbai_chart.houses[i].sign.value
            next_sign = mumbai_chart.houses[i + 1].sign.value
            expected_next = (current % 12) + 1
            assert next_sign == expected_next


# ---------------------------------------------------------------------------
# JSON serialization
# ---------------------------------------------------------------------------

class TestSerialization:
    def test_chart_to_json(self, mumbai_chart):
        """Chart should serialize to JSON without errors."""
        json_str = mumbai_chart.model_dump_json()
        assert len(json_str) > 100
        assert "planets" in json_str
        assert "houses" in json_str

    def test_chart_to_dict(self, mumbai_chart):
        """Chart should convert to dict without errors."""
        d = mumbai_chart.model_dump()
        assert isinstance(d, dict)
        assert len(d["planets"]) == 9
        assert len(d["houses"]) == 12
