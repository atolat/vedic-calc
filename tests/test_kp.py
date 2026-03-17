"""
Tests for KP (Krishnamurti Paddhati) astrology module.

Uses a Mumbai 1990 chart as the test fixture:
    Date: March 15, 1990, 10:30:00
    Location: Mumbai (19.076°N, 72.8777°E)
    Timezone: IST (+5.5)
"""

import pytest

from vedic_calc.core.constants import Planet, Sign, VIMSOTTARI_ORDER, VIMSOTTARI_YEARS, NAKSHATRA_LORDS, Nakshatra
from vedic_calc.kp.sublords import get_kp_sublord, _get_vimsottari_sequence_from
from vedic_calc.kp.houses import calculate_kp_houses
from vedic_calc.kp.calculator import calculate_kp_chart


# ---------------------------------------------------------------------------
# Test fixture parameters (Mumbai 1990 chart)
# ---------------------------------------------------------------------------
YEAR, MONTH, DAY = 1990, 3, 15
HOUR, MINUTE, SECOND = 10, 30, 0
LAT, LON = 19.076, 72.8777
TZ = 5.5


# ---------------------------------------------------------------------------
# Sub-lord tests
# ---------------------------------------------------------------------------

class TestSublord:
    """Tests for KP sub-lord calculation."""

    def test_sublord_at_zero_degrees(self):
        """0 degrees Aries: Ashwini nakshatra, lord = Ketu.
        Sub-lord should also be Ketu (first sub starts with the star lord).
        Sub-sub-lord should also be Ketu (first sub-sub starts with the sub-lord).
        """
        info = get_kp_sublord(0.0)
        assert info.sign == Sign.ARIES.value
        assert info.sign_lord == Planet.MARS.value  # Mars rules Aries
        assert info.star_lord == Planet.KETU.value   # Ashwini lord = Ketu
        assert info.sub_lord == Planet.KETU.value    # First sub = star lord = Ketu
        assert info.sub_sub_lord == Planet.KETU.value  # First sub-sub = sub lord = Ketu

    def test_sublord_coverage(self):
        """Every degree in 0-360 should resolve to valid lords."""
        step = 0.5  # half-degree steps
        deg = 0.0
        planet_values = {p.value for p in Planet}
        sign_values = {s.value for s in Sign}

        while deg < 360.0:
            info = get_kp_sublord(deg)
            assert info.sign in sign_values, f"Invalid sign at {deg}°"
            assert info.sign_lord in planet_values, f"Invalid sign lord at {deg}°"
            assert info.star_lord in planet_values, f"Invalid star lord at {deg}°"
            assert info.sub_lord in planet_values, f"Invalid sub lord at {deg}°"
            assert info.sub_sub_lord in planet_values, f"Invalid sub-sub lord at {deg}°"
            deg += step

    def test_sublord_sequence_follows_vimsottari(self):
        """Sub-lords within a nakshatra follow Vimsottari order from the star lord.

        Test with Ashwini (0° - 13.333°, lord = Ketu).
        The sub sequence should be: Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury.
        """
        star_lord = Planet.KETU
        expected_sequence = _get_vimsottari_sequence_from(star_lord)

        # Walk through Ashwini in small steps and collect the sub-lord transitions
        observed_subs: list[int] = []
        prev_sub = None
        deg = 0.0
        nakshatra_end = 360.0 / 27.0  # ~13.3333

        while deg < nakshatra_end:
            info = get_kp_sublord(deg)
            if info.sub_lord != prev_sub:
                observed_subs.append(info.sub_lord)
                prev_sub = info.sub_lord
            deg += 0.01

        # Should have exactly 9 sub-lords in Vimsottari order from Ketu
        assert len(observed_subs) == 9, f"Expected 9 subs, got {len(observed_subs)}: {observed_subs}"
        for i, planet in enumerate(expected_sequence):
            assert observed_subs[i] == planet.value, (
                f"Sub {i}: expected {planet.name} ({planet.value}), "
                f"got {observed_subs[i]}"
            )

    def test_sublord_at_nakshatra_boundary(self):
        """At the start of Bharani (13.333°), star lord should be Venus."""
        # Bharani starts at 13.333... degrees
        info = get_kp_sublord(360.0 / 27.0)
        assert info.star_lord == Planet.VENUS.value  # Bharani lord = Venus
        # Sub lord should also be Venus (first sub = star lord)
        assert info.sub_lord == Planet.VENUS.value

    def test_sublord_last_degree(self):
        """At 359.99 degrees (end of Revati), star lord should be Mercury."""
        info = get_kp_sublord(359.99)
        assert info.star_lord == Planet.MERCURY.value  # Revati lord = Mercury
        assert info.sign == Sign.PISCES.value


# ---------------------------------------------------------------------------
# Placidus house cusp tests
# ---------------------------------------------------------------------------

class TestPlacidusHouses:
    """Tests for KP Placidus house cusp calculation."""

    def _get_cusps(self):
        """Helper to compute cusps for the Mumbai 1990 chart."""
        from vedic_calc.core.ephemeris import _to_julian_day, get_ayanamsa
        from vedic_calc.core.constants import Ayanamsa

        hour_decimal = HOUR + MINUTE / 60.0 + SECOND / 3600.0
        ut_hour = hour_decimal - TZ
        jd = _to_julian_day(YEAR, MONTH, DAY, ut_hour)
        ayanamsa_value = get_ayanamsa(jd, Ayanamsa.LAHIRI)
        return calculate_kp_houses(jd, LAT, LON, ayanamsa_value)

    def test_placidus_cusps_12_houses(self):
        """Exactly 12 cusps should be returned."""
        cusps = self._get_cusps()
        assert len(cusps) == 12

    def test_cusps_have_valid_sublords(self):
        """Every cusp should have valid sign/star/sub lord values."""
        cusps = self._get_cusps()
        planet_values = {p.value for p in Planet}
        sign_values = {s.value for s in Sign}

        for cusp in cusps:
            assert 1 <= cusp.house_number <= 12
            assert 0.0 <= cusp.cusp_longitude < 360.0
            assert cusp.sign in sign_values, f"Invalid sign for house {cusp.house_number}"
            assert cusp.sign_lord in planet_values, f"Invalid sign lord for house {cusp.house_number}"
            assert cusp.star_lord in planet_values, f"Invalid star lord for house {cusp.house_number}"
            assert cusp.sub_lord in planet_values, f"Invalid sub lord for house {cusp.house_number}"

    def test_cusps_house_numbers_sequential(self):
        """House numbers should be 1 through 12 in order."""
        cusps = self._get_cusps()
        for i, cusp in enumerate(cusps):
            assert cusp.house_number == i + 1


# ---------------------------------------------------------------------------
# Full KP chart tests
# ---------------------------------------------------------------------------

class TestKPChart:
    """Tests for the full KP chart calculation."""

    @pytest.fixture
    def kp_chart(self):
        """Compute the KP chart once for all tests in this class."""
        return calculate_kp_chart(
            YEAR, MONTH, DAY, HOUR, MINUTE, SECOND, LAT, LON, TZ
        )

    def test_kp_chart_planets_have_sublords(self, kp_chart):
        """All 9 planets should have sub-lord info."""
        assert len(kp_chart.planets) == 9

        planet_values = {p.value for p in Planet}
        sign_values = {s.value for s in Sign}

        for pi in kp_chart.planets:
            assert pi.planet in planet_values
            assert pi.sign in sign_values
            assert pi.sign_lord in planet_values
            assert pi.star_lord in planet_values
            assert pi.sub_lord in planet_values
            assert pi.sub_sub_lord in planet_values
            assert 0.0 <= pi.longitude < 360.0

    def test_kp_chart_has_12_cusps(self, kp_chart):
        """The chart should have exactly 12 Placidus cusps."""
        assert len(kp_chart.cusps) == 12

    def test_kp_significators_cover_all_houses(self, kp_chart):
        """Every house (1-12) should appear in the significator table."""
        for h in range(1, 13):
            assert str(h) in kp_chart.significators, f"House {h} missing from significators"
            # Each house should have at least one significator planet
            # (in practice, most houses have multiple signifying planets)
            assert isinstance(kp_chart.significators[str(h)], list)

    def test_kp_significators_planets_valid(self, kp_chart):
        """All planet values in the significator table should be valid."""
        planet_values = {p.value for p in Planet}
        for house_str, planets in kp_chart.significators.items():
            for p in planets:
                assert p in planet_values, f"Invalid planet {p} for house {house_str}"

    def test_ruling_planets_valid(self, kp_chart):
        """Ruling planets should be valid Planet enum values."""
        planet_values = {p.value for p in Planet}
        assert len(kp_chart.ruling_planets) > 0, "Should have at least one ruling planet"
        for p in kp_chart.ruling_planets:
            assert p in planet_values, f"Invalid ruling planet: {p}"

    def test_ruling_planets_unique(self, kp_chart):
        """Ruling planets should not have duplicates."""
        assert len(kp_chart.ruling_planets) == len(set(kp_chart.ruling_planets))

    def test_planet_significator_houses_nonempty(self, kp_chart):
        """Each planet should signify at least one house."""
        for pi in kp_chart.planets:
            assert len(pi.significator_houses) > 0, (
                f"Planet {pi.planet} has no significator houses"
            )

    def test_planet_significator_houses_valid_range(self, kp_chart):
        """All significator house numbers should be 1-12."""
        for pi in kp_chart.planets:
            for h in pi.significator_houses:
                assert 1 <= h <= 12, (
                    f"Planet {pi.planet} has invalid significator house {h}"
                )
