"""
Tests for the Varshaphal (Solar Return / Annual Horoscope) module.

Uses the Mumbai 1990 reference chart (March 15, 1990, 10:30 AM IST, Mumbai)
to verify solar return calculations, Muntha progression, year lord selection,
and Mudda Dasha period computation.
"""

import pytest

from vedic_calc import calculate_chart, calculate_varshaphal
from vedic_calc.core.constants import Ayanamsa, Planet, Sign


# ---------------------------------------------------------------------------
# Test fixture: natal chart for Mumbai 1990
# ---------------------------------------------------------------------------

@pytest.fixture
def mumbai_chart():
    """Birth chart: March 15, 1990, 10:30 AM IST, Mumbai."""
    return calculate_chart(
        year=1990, month=3, day=15,
        hour=10, minute=30, second=0,
        latitude=19.076, longitude=72.8777,
        timezone_offset=5.5,
        ayanamsa=Ayanamsa.LAHIRI,
    )


@pytest.fixture
def varshaphal_2025(mumbai_chart):
    """Varshaphal for year 2025 using the Mumbai 1990 chart."""
    return calculate_varshaphal(mumbai_chart, 2025)


# ---------------------------------------------------------------------------
# Solar return tests
# ---------------------------------------------------------------------------

class TestSolarReturn:
    def test_solar_return_near_birthday(self, varshaphal_2025):
        """Solar return date should be within ~2 days of calendar birthday (March 15)."""
        sr_dt = varshaphal_2025.solar_return_datetime
        assert sr_dt.year == 2025
        assert sr_dt.month == 3
        # Solar return should be within 2 days of March 15
        assert 13 <= sr_dt.day <= 17

    def test_solar_return_sun_longitude(self, mumbai_chart, varshaphal_2025):
        """Sun longitude in the annual chart should match natal Sun longitude.

        The solar return matches the tropical Sun position exactly. The sidereal
        longitude will differ slightly because the ayanamsa changes over the years
        (precession advances ~0.014 degrees/year). For a 35-year gap, the expected
        sidereal difference is ~0.49 degrees. We check within 1.0 degree to account
        for this precession drift.
        """
        natal_sun_lon = mumbai_chart.planets[Planet.SUN].longitude
        annual_sun_lon = varshaphal_2025.annual_chart.planets[Planet.SUN].longitude
        # Sidereal longitudes differ by the change in ayanamsa over the years.
        # The annual chart Sun should be close to the natal Sun but offset by
        # precession (~0.014 deg/year * 35 years ≈ 0.49 degrees).
        diff = abs(natal_sun_lon - annual_sun_lon)
        assert diff < 1.0, f"Sun longitude difference {diff}° exceeds 1.0°"
        # Also verify the ayanamsa difference explains the gap
        ayanamsa_diff = abs(
            varshaphal_2025.annual_chart.ayanamsa_degrees
            - mumbai_chart.ayanamsa_degrees
        )
        assert abs(diff - ayanamsa_diff) < 0.05

    def test_age_calculation(self, varshaphal_2025):
        """Age should be varshaphal_year - birth_year."""
        assert varshaphal_2025.age == 2025 - 1990
        assert varshaphal_2025.age == 35

    def test_birth_year_stored(self, varshaphal_2025):
        """Birth year should be stored correctly."""
        assert varshaphal_2025.birth_year == 1990
        assert varshaphal_2025.varshaphal_year == 2025


# ---------------------------------------------------------------------------
# Muntha tests
# ---------------------------------------------------------------------------

class TestMuntha:
    def test_muntha_progression(self, mumbai_chart):
        """Muntha should advance one sign per year from birth ascendant."""
        birth_asc_sign = mumbai_chart.ascendant.sign.value

        for year_offset in range(5):
            year = 1990 + year_offset
            result = calculate_varshaphal(mumbai_chart, year)
            expected_sign = ((birth_asc_sign - 1 + year_offset) % 12) + 1
            assert result.muntha.sign == expected_sign, (
                f"Year {year}: expected muntha sign {expected_sign}, "
                f"got {result.muntha.sign}"
            )

    def test_muntha_has_valid_sign(self, varshaphal_2025):
        """Muntha sign should be between 1 and 12."""
        assert 1 <= varshaphal_2025.muntha.sign <= 12

    def test_muntha_has_sign_name(self, varshaphal_2025):
        """Muntha should have a non-empty sign name."""
        assert len(varshaphal_2025.muntha.sign_name) > 0

    def test_muntha_lord_is_classical_planet(self, varshaphal_2025):
        """Muntha lord should be one of the 7 classical planets (not Rahu/Ketu)."""
        classical = {
            Planet.SUN.value, Planet.MOON.value, Planet.MARS.value,
            Planet.MERCURY.value, Planet.JUPITER.value, Planet.VENUS.value,
            Planet.SATURN.value,
        }
        assert varshaphal_2025.muntha.lord in classical


# ---------------------------------------------------------------------------
# Mudda Dasha tests
# ---------------------------------------------------------------------------

class TestMuddaDasha:
    def test_mudda_dasha_total_one_year(self, varshaphal_2025):
        """All Mudda Dasha periods should sum to approximately 365.25 days."""
        total_days = sum(p.duration_years * 365.25 for p in varshaphal_2025.mudda_dasha)
        assert abs(total_days - 365.25) < 0.1, (
            f"Mudda Dasha total is {total_days} days, expected ~365.25"
        )

    def test_mudda_dasha_has_9_periods(self, varshaphal_2025):
        """Mudda Dasha should have exactly 9 periods (one per planet)."""
        assert len(varshaphal_2025.mudda_dasha) == 9

    def test_mudda_dasha_covers_all_planets(self, varshaphal_2025):
        """Mudda Dasha should include all 9 Vimsottari planets."""
        lords = {p.lord for p in varshaphal_2025.mudda_dasha}
        expected = set(Planet)
        assert lords == expected

    def test_mudda_dasha_periods_are_consecutive(self, varshaphal_2025):
        """Mudda Dasha periods should be consecutive (no gaps)."""
        periods = varshaphal_2025.mudda_dasha
        for i in range(len(periods) - 1):
            # End of one period should equal start of next (within 1 second)
            gap = abs((periods[i].end - periods[i + 1].start).total_seconds())
            assert gap < 1.0, f"Gap of {gap}s between period {i} and {i+1}"

    def test_mudda_dasha_level_is_mudda(self, varshaphal_2025):
        """All Mudda Dasha periods should have level='mudda_dasha'."""
        for period in varshaphal_2025.mudda_dasha:
            assert period.level == "mudda_dasha"


# ---------------------------------------------------------------------------
# Year Lord tests
# ---------------------------------------------------------------------------

class TestYearLord:
    def test_year_lord_is_valid_planet(self, varshaphal_2025):
        """Year lord should be one of the 7 classical planets."""
        classical = {
            Planet.SUN.value, Planet.MOON.value, Planet.MARS.value,
            Planet.MERCURY.value, Planet.JUPITER.value, Planet.VENUS.value,
            Planet.SATURN.value,
        }
        assert varshaphal_2025.year_lord in classical

    def test_year_lord_has_name(self, varshaphal_2025):
        """Year lord should have a non-empty name."""
        assert len(varshaphal_2025.year_lord_name) > 0


# ---------------------------------------------------------------------------
# Annual chart validation tests
# ---------------------------------------------------------------------------

class TestAnnualChart:
    def test_annual_chart_is_valid(self, varshaphal_2025):
        """Annual chart should have all 9 planets with valid longitudes."""
        ac = varshaphal_2025.annual_chart
        assert len(ac.planets) == 9

        for planet, pos in ac.planets.items():
            assert 0.0 <= pos.longitude < 360.0, (
                f"{planet.name} has invalid longitude {pos.longitude}"
            )

    def test_annual_chart_has_12_houses(self, varshaphal_2025):
        """Annual chart should have 12 houses."""
        assert len(varshaphal_2025.annual_chart.houses) == 12

    def test_annual_chart_uses_birth_location(self, mumbai_chart, varshaphal_2025):
        """Annual chart should use the birth location (traditional Varshaphal)."""
        assert varshaphal_2025.annual_chart.latitude == mumbai_chart.latitude
        assert varshaphal_2025.annual_chart.longitude == mumbai_chart.longitude

    def test_annual_chart_uses_same_ayanamsa(self, mumbai_chart, varshaphal_2025):
        """Annual chart should use the same ayanamsa as the natal chart."""
        assert varshaphal_2025.annual_chart.ayanamsa == mumbai_chart.ayanamsa


# ---------------------------------------------------------------------------
# Multiple years test
# ---------------------------------------------------------------------------

class TestMultipleYears:
    def test_different_years_give_different_charts(self, mumbai_chart):
        """Varshaphal for different years should produce different annual charts."""
        r2024 = calculate_varshaphal(mumbai_chart, 2024)
        r2025 = calculate_varshaphal(mumbai_chart, 2025)

        # Solar return times should be different
        assert r2024.solar_return_datetime != r2025.solar_return_datetime
        # Ages should differ by 1
        assert r2025.age - r2024.age == 1

    def test_birth_year_varshaphal(self, mumbai_chart):
        """Varshaphal for the birth year should have age=0."""
        result = calculate_varshaphal(mumbai_chart, 1990)
        assert result.age == 0
