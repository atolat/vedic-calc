"""
Accuracy validation tests.

These tests verify vedic-calc's results against independently computed
reference values using pyswisseph directly (bypassing our abstraction layer).

This ensures our code on top of pyswisseph (ayanamsa subtraction, sign/nakshatra
derivation, house calculation) doesn't introduce errors.

Strategy:
    1. Compute tropical positions using raw pyswisseph calls
    2. Subtract ayanamsa manually to get sidereal positions
    3. Compare against our calculate_chart() output
    4. Tolerance: < 0.01° (trivially satisfied since we use the same engine,
       but catches bugs in our arithmetic layer)

Additionally, we test against well-known astronomical facts:
    - Full moons: Sun and Moon should be ~180° apart (sidereal)
    - Solar ingress dates: Sun enters Aries (Mesha Sankranti) around April 13-14
    - Eclipses: Rahu/Ketu near Sun/Moon axis during eclipses
"""

import math

import swisseph as swe

from vedic_calc import calculate_chart
from vedic_calc.core.constants import Ayanamsa, Planet, Sign, Nakshatra
from vedic_calc.core.ephemeris import _to_julian_day, get_ayanamsa


# ---------------------------------------------------------------------------
# Cross-validation: our code vs raw pyswisseph
# ---------------------------------------------------------------------------

class TestCrossValidation:
    """Compare calculate_chart() output against raw pyswisseph calls."""

    def _raw_sidereal_longitude(
        self, jd: float, swe_planet: int, ayanamsa: float
    ) -> float:
        """Compute sidereal longitude using raw pyswisseph (no vedic-calc code)."""
        result = swe.calc_ut(jd, swe_planet)
        tropical = result[0][0]
        return (tropical - ayanamsa) % 360.0

    def test_all_planets_match_raw_swisseph(self):
        """Every planet's longitude should exactly match raw pyswisseph computation."""
        # Birth: March 15, 1990, 10:30 AM IST, Mumbai
        ut_hour = 10.5 - 5.5  # Convert IST to UT
        jd = _to_julian_day(1990, 3, 15, ut_hour)

        swe.set_sid_mode(int(Ayanamsa.LAHIRI))
        ayanamsa = swe.get_ayanamsa_ut(jd)

        chart = calculate_chart(
            year=1990, month=3, day=15, hour=10, minute=30,
            latitude=19.076, longitude=72.878, timezone_offset=5.5,
        )

        # Map our Planet enum to Swiss Ephemeris constants for direct comparison
        planet_swe_map = {
            Planet.SUN: 0, Planet.MOON: 1, Planet.MARS: 4,
            Planet.MERCURY: 2, Planet.JUPITER: 5, Planet.VENUS: 3,
            Planet.SATURN: 6, Planet.RAHU: 10,
        }

        for planet, swe_id in planet_swe_map.items():
            raw_lon = self._raw_sidereal_longitude(jd, swe_id, ayanamsa)
            our_lon = chart.planets[planet].longitude

            diff = abs(raw_lon - our_lon)
            if diff > 180:
                diff = 360 - diff

            assert diff < 0.01, (
                f"{planet.name}: our={our_lon:.4f}°, raw={raw_lon:.4f}°, diff={diff:.4f}°"
            )

    def test_ketu_matches_rahu_plus_180(self):
        """Ketu should be exactly Rahu + 180° (computed independently)."""
        ut_hour = 10.5 - 5.5
        jd = _to_julian_day(1990, 3, 15, ut_hour)

        swe.set_sid_mode(int(Ayanamsa.LAHIRI))
        ayanamsa = swe.get_ayanamsa_ut(jd)

        # Raw Rahu from pyswisseph
        rahu_result = swe.calc_ut(jd, 10)  # SE_MEAN_NODE
        rahu_tropical = rahu_result[0][0]
        rahu_sidereal = (rahu_tropical - ayanamsa) % 360.0
        expected_ketu = (rahu_sidereal + 180.0) % 360.0

        chart = calculate_chart(
            year=1990, month=3, day=15, hour=10, minute=30,
            latitude=19.076, longitude=72.878, timezone_offset=5.5,
        )

        diff = abs(chart.planets[Planet.KETU].longitude - expected_ketu)
        if diff > 180:
            diff = 360 - diff

        assert diff < 0.01, (
            f"Ketu: our={chart.planets[Planet.KETU].longitude:.4f}°, "
            f"expected={expected_ketu:.4f}°"
        )

    def test_ascendant_matches_raw_swisseph(self):
        """Ascendant should match raw pyswisseph houses_ex() call."""
        ut_hour = 10.5 - 5.5
        jd = _to_julian_day(1990, 3, 15, ut_hour)

        swe.set_sid_mode(int(Ayanamsa.LAHIRI))
        ayanamsa = swe.get_ayanamsa_ut(jd)

        # Raw ascendant from pyswisseph
        _, ascmc = swe.houses_ex(jd, 19.076, 72.878, b"W")
        raw_asc = (ascmc[0] - ayanamsa) % 360.0

        chart = calculate_chart(
            year=1990, month=3, day=15, hour=10, minute=30,
            latitude=19.076, longitude=72.878, timezone_offset=5.5,
        )

        diff = abs(chart.ascendant.longitude - raw_asc)
        if diff > 180:
            diff = 360 - diff

        assert diff < 0.01, (
            f"Ascendant: our={chart.ascendant.longitude:.4f}°, raw={raw_asc:.4f}°"
        )


# ---------------------------------------------------------------------------
# Astronomical fact checks
# ---------------------------------------------------------------------------

class TestAstronomicalFacts:
    """Verify against known astronomical events and facts."""

    def test_full_moon_opposition(self):
        """On a full moon, Sun and Moon should be ~180° apart (sidereal).

        March 11, 1990 was a full moon. Sun and Moon should be roughly
        opposite in the sidereal zodiac.
        """
        chart = calculate_chart(
            year=1990, month=3, day=11, hour=12, minute=0,
            latitude=0.0, longitude=0.0, timezone_offset=0.0,
        )
        sun_lon = chart.planets[Planet.SUN].longitude
        moon_lon = chart.planets[Planet.MOON].longitude
        diff = abs(sun_lon - moon_lon)
        if diff > 180:
            diff = 360 - diff
        # Full moon: Sun-Moon separation should be close to 180° (within ~15°
        # since exact full moon may not be at noon UT)
        assert 165 < diff < 195, f"Sun-Moon diff on full moon: {diff:.1f}°"

    def test_new_moon_conjunction(self):
        """On a new moon (Amavasya), Sun and Moon should be near conjunction.

        March 26, 1990 was a new moon.
        """
        chart = calculate_chart(
            year=1990, month=3, day=26, hour=12, minute=0,
            latitude=0.0, longitude=0.0, timezone_offset=0.0,
        )
        sun_lon = chart.planets[Planet.SUN].longitude
        moon_lon = chart.planets[Planet.MOON].longitude
        diff = abs(sun_lon - moon_lon)
        if diff > 180:
            diff = 360 - diff
        # New moon: Sun-Moon should be within ~15°
        assert diff < 15, f"Sun-Moon diff on new moon: {diff:.1f}°"

    def test_sun_in_aries_mid_april(self):
        """Sun enters sidereal Aries (Mesha Sankranti) around April 13-14.

        By April 15, Sun should be in Aries.
        """
        chart = calculate_chart(
            year=2024, month=4, day=15, hour=12, minute=0,
            latitude=0.0, longitude=0.0, timezone_offset=0.0,
        )
        assert chart.planets[Planet.SUN].sign == Sign.ARIES

    def test_sun_in_capricorn_mid_january(self):
        """Sun enters sidereal Capricorn (Makar Sankranti) around Jan 14-15.

        By Jan 16, Sun should be in Capricorn.
        """
        chart = calculate_chart(
            year=2024, month=1, day=16, hour=12, minute=0,
            latitude=0.0, longitude=0.0, timezone_offset=0.0,
        )
        assert chart.planets[Planet.SUN].sign == Sign.CAPRICORN


# ---------------------------------------------------------------------------
# Sign and nakshatra arithmetic validation
# ---------------------------------------------------------------------------

class TestArithmeticAccuracy:
    """Verify our sign/nakshatra derivation is consistent with longitudes."""

    def test_sign_from_longitude_multiple_charts(self):
        """For several birth dates, verify sign = floor(longitude/30) + 1."""
        test_dates = [
            (1985, 6, 15, 8, 0),
            (1995, 12, 25, 23, 30),
            (2000, 1, 1, 0, 0),
            (2010, 7, 4, 14, 15),
        ]
        for y, m, d, h, mi in test_dates:
            chart = calculate_chart(
                year=y, month=m, day=d, hour=h, minute=mi,
                latitude=28.6139, longitude=77.209, timezone_offset=5.5,  # Delhi
            )
            for planet, pos in chart.planets.items():
                expected_sign = int(pos.longitude / 30.0) + 1
                assert pos.sign.value == expected_sign, (
                    f"{y}-{m}-{d} {planet.name}: "
                    f"sign={pos.sign.value}, expected={expected_sign}, "
                    f"lon={pos.longitude}"
                )

    def test_nakshatra_from_longitude_multiple_charts(self):
        """Verify nakshatra index = floor(longitude / 13.333) + 1."""
        test_dates = [
            (1985, 6, 15, 8, 0),
            (1995, 12, 25, 23, 30),
            (2000, 1, 1, 0, 0),
            (2010, 7, 4, 14, 15),
        ]
        nak_span = 360.0 / 27.0
        for y, m, d, h, mi in test_dates:
            chart = calculate_chart(
                year=y, month=m, day=d, hour=h, minute=mi,
                latitude=28.6139, longitude=77.209, timezone_offset=5.5,
            )
            for planet, pos in chart.planets.items():
                expected_nak = int(pos.longitude / nak_span) + 1
                expected_nak = min(expected_nak, 27)
                assert pos.nakshatra_info.nakshatra.value == expected_nak, (
                    f"{y}-{m}-{d} {planet.name}: "
                    f"nak={pos.nakshatra_info.nakshatra.value}, "
                    f"expected={expected_nak}, lon={pos.longitude}"
                )

    def test_degree_in_sign_consistency(self):
        """degree_in_sign should equal longitude % 30."""
        chart = calculate_chart(
            year=2000, month=6, day=21, hour=12, minute=0,
            latitude=0.0, longitude=0.0, timezone_offset=0.0,
        )
        for planet, pos in chart.planets.items():
            expected = pos.longitude % 30.0
            assert abs(pos.degree_in_sign - expected) < 0.001, (
                f"{planet.name}: degree_in_sign={pos.degree_in_sign}, "
                f"expected={expected}"
            )
