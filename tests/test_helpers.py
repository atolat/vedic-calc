"""Tests for chart calculation helper functions."""

from vedic_calc.chart.calculator import (
    build_houses,
    longitude_to_degree_in_sign,
    longitude_to_nakshatra_info,
    longitude_to_sign,
)
from vedic_calc.core.constants import Nakshatra, Planet, Sign


# ---------------------------------------------------------------------------
# longitude_to_sign
# ---------------------------------------------------------------------------

class TestLongitudeToSign:
    def test_aries_start(self):
        assert longitude_to_sign(0.0) == Sign.ARIES

    def test_aries_end(self):
        assert longitude_to_sign(29.99) == Sign.ARIES

    def test_taurus_start(self):
        assert longitude_to_sign(30.0) == Sign.TAURUS

    def test_pisces(self):
        assert longitude_to_sign(350.0) == Sign.PISCES

    def test_mid_cancer(self):
        """105° = 3 full signs (90°) + 15° into Cancer."""
        assert longitude_to_sign(105.0) == Sign.CANCER


# ---------------------------------------------------------------------------
# longitude_to_degree_in_sign
# ---------------------------------------------------------------------------

class TestDegreeInSign:
    def test_start_of_sign(self):
        assert longitude_to_degree_in_sign(30.0) == 0.0

    def test_mid_sign(self):
        assert longitude_to_degree_in_sign(45.0) == 15.0

    def test_end_of_sign(self):
        assert abs(longitude_to_degree_in_sign(59.99) - 29.99) < 0.01


# ---------------------------------------------------------------------------
# longitude_to_nakshatra_info
# ---------------------------------------------------------------------------

class TestNakshatraInfo:
    def test_ashwini_start(self):
        """0° should be the start of Ashwini, pada 1."""
        info = longitude_to_nakshatra_info(0.0)
        assert info.nakshatra == Nakshatra.ASHWINI
        assert info.pada == 1
        assert info.lord == Planet.KETU

    def test_rohini(self):
        """Rohini starts at 40° (3 × 13.333°). 45° = Rohini, pada 2."""
        info = longitude_to_nakshatra_info(45.0)
        assert info.nakshatra == Nakshatra.ROHINI
        assert info.pada == 2
        assert info.lord == Planet.MOON

    def test_revati_end(self):
        """Just before 360° should be Revati, pada 4."""
        info = longitude_to_nakshatra_info(359.9)
        assert info.nakshatra == Nakshatra.REVATI
        assert info.pada == 4
        assert info.lord == Planet.MERCURY

    def test_pada_boundaries(self):
        """Each pada spans 3.333°. Verify pada transitions."""
        # Ashwini pada 1: 0° to 3.333°
        assert longitude_to_nakshatra_info(1.0).pada == 1
        # Ashwini pada 2: 3.333° to 6.667°
        assert longitude_to_nakshatra_info(4.0).pada == 2
        # Ashwini pada 3: 6.667° to 10.0°
        assert longitude_to_nakshatra_info(7.0).pada == 3
        # Ashwini pada 4: 10.0° to 13.333°
        assert longitude_to_nakshatra_info(11.0).pada == 4


# ---------------------------------------------------------------------------
# build_houses
# ---------------------------------------------------------------------------

class TestBuildHouses:
    def test_house_count(self):
        houses = build_houses(Sign.ARIES)
        assert len(houses) == 12

    def test_first_house_is_ascendant_sign(self):
        houses = build_houses(Sign.GEMINI)
        assert houses[0].sign == Sign.GEMINI
        assert houses[0].house_number == 1

    def test_seventh_house_is_opposite(self):
        """7th house should be the sign opposite the ascendant."""
        houses = build_houses(Sign.GEMINI)
        assert houses[6].sign == Sign.SAGITTARIUS

    def test_wraps_around_zodiac(self):
        """Starting from Scorpio (8), house 6 should be Aries (1)."""
        houses = build_houses(Sign.SCORPIO)
        assert houses[5].sign == Sign.ARIES

    def test_house_lords(self):
        """Each house lord should match the sign lord."""
        houses = build_houses(Sign.ARIES)
        assert houses[0].lord == Planet.MARS  # Aries lord
        assert houses[3].lord == Planet.MOON  # Cancer lord
