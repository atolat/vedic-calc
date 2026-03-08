"""Tests for the Vimsottari Dasha calculator."""

from datetime import datetime

import pytest

from vedic_calc import calculate_chart, calculate_dasha, get_current_dasha
from vedic_calc.core.constants import Planet, VIMSOTTARI_YEARS, NAKSHATRA_LORDS
from vedic_calc.core.types import DashaPeriod


# Reuse the same Mumbai 1990 fixture from test_chart.py
@pytest.fixture
def mumbai_chart():
    """Birth chart: March 15, 1990, 10:30 AM IST, Mumbai."""
    return calculate_chart(
        year=1990, month=3, day=15,
        hour=10, minute=30,
        latitude=19.0760, longitude=72.8777,
        timezone_offset=5.5,
    )


# ---------------------------------------------------------------------------
# Structure tests
# ---------------------------------------------------------------------------

class TestDashaStructure:
    """Verify the basic structure of dasha output."""

    def test_returns_list_of_dasha_periods(self, mumbai_chart):
        periods = calculate_dasha(mumbai_chart, levels=1)
        assert isinstance(periods, list)
        assert all(isinstance(p, DashaPeriod) for p in periods)

    def test_mahadasha_count(self, mumbai_chart):
        """There should be exactly 9 mahadashas (one per planet)."""
        periods = calculate_dasha(mumbai_chart, levels=1)
        mahas = [p for p in periods if p.level == "mahadasha"]
        assert len(mahas) == 9

    def test_antardasha_count(self, mumbai_chart):
        """Each mahadasha has 9 antardashas = 81 total."""
        periods = calculate_dasha(mumbai_chart, levels=2)
        antars = [p for p in periods if p.level == "antardasha"]
        assert len(antars) == 81

    def test_all_levels_present(self, mumbai_chart):
        """With levels=3, all three levels should be present."""
        periods = calculate_dasha(mumbai_chart, levels=3)
        levels = {p.level for p in periods}
        assert levels == {"mahadasha", "antardasha", "pratyantardasha"}

    def test_pratyantardasha_count(self, mumbai_chart):
        """Each antardasha has 9 pratyantardashas = 729 total."""
        periods = calculate_dasha(mumbai_chart, levels=3)
        prats = [p for p in periods if p.level == "pratyantardasha"]
        assert len(prats) == 729


# ---------------------------------------------------------------------------
# Duration tests
# ---------------------------------------------------------------------------

class TestDashaDurations:
    """Verify duration arithmetic."""

    def test_total_duration_up_to_120_years(self, mumbai_chart):
        """Sum of all mahadasha durations should be ≤ 120 years.

        The first mahadasha is partial (only the remaining portion from birth),
        so the total from birth is: 120 - elapsed_portion_of_first_dasha.
        Adding the first dasha's full duration should give exactly 120.
        """
        periods = calculate_dasha(mumbai_chart, levels=1)
        mahas = [p for p in periods if p.level == "mahadasha"]
        total = sum(p.duration_years for p in mahas)

        # Total should be < 120 (because first dasha is partial)
        assert total < 120.0

        # But adding back the elapsed portion should give 120
        first = mahas[0]
        full_first = VIMSOTTARI_YEARS[first.lord]
        elapsed = full_first - first.duration_years
        assert abs((total + elapsed) - 120.0) < 0.01

    def test_first_mahadasha_is_partial(self, mumbai_chart):
        """The first mahadasha should be shorter than its full duration
        (because part of it has elapsed at birth)."""
        periods = calculate_dasha(mumbai_chart, levels=1)
        first = periods[0]
        full_years = VIMSOTTARI_YEARS[first.lord]
        assert first.duration_years <= full_years

    def test_subsequent_mahadashas_are_full(self, mumbai_chart):
        """Mahadashas 2-9 should have full durations."""
        periods = calculate_dasha(mumbai_chart, levels=1)
        mahas = [p for p in periods if p.level == "mahadasha"]
        for maha in mahas[1:]:
            assert abs(maha.duration_years - VIMSOTTARI_YEARS[maha.lord]) < 0.001

    def test_antardasha_sum_equals_mahadasha(self, mumbai_chart):
        """The sum of antardasha durations within a mahadasha should
        equal the mahadasha's duration."""
        periods = calculate_dasha(mumbai_chart, levels=2)
        mahas = [p for p in periods if p.level == "mahadasha"]
        antars = [p for p in periods if p.level == "antardasha"]

        for maha in mahas:
            # Find antardashas within this mahadasha's time range
            maha_antars = [
                a for a in antars
                if a.start >= maha.start and a.end <= maha.end + __import__('datetime').timedelta(seconds=1)
            ]
            antar_total = sum(a.duration_years for a in maha_antars)
            assert abs(antar_total - maha.duration_years) < 0.01


# ---------------------------------------------------------------------------
# Sequence tests
# ---------------------------------------------------------------------------

class TestDashaSequence:
    """Verify the correct planet sequence."""

    def test_first_lord_matches_moon_nakshatra(self, mumbai_chart):
        """The first mahadasha lord should be the Moon's nakshatra lord."""
        moon_nak = mumbai_chart.planets[Planet.MOON].nakshatra_info
        expected_lord = moon_nak.lord

        periods = calculate_dasha(mumbai_chart, levels=1)
        assert periods[0].lord == expected_lord

    def test_chronological_order(self, mumbai_chart):
        """Mahadasha periods should be in chronological order with no gaps."""
        periods = calculate_dasha(mumbai_chart, levels=1)
        mahas = [p for p in periods if p.level == "mahadasha"]
        for i in range(len(mahas) - 1):
            # End of one period should be very close to start of next
            gap = abs((mahas[i].end - mahas[i + 1].start).total_seconds())
            assert gap < 1.0, f"Gap between mahadashas {i} and {i+1}: {gap}s"

    def test_starts_at_birth(self, mumbai_chart):
        """First dasha should start at birth time."""
        periods = calculate_dasha(mumbai_chart, levels=1)
        assert periods[0].start == mumbai_chart.birth_datetime


# ---------------------------------------------------------------------------
# Current dasha lookup
# ---------------------------------------------------------------------------

class TestGetCurrentDasha:
    """Test the get_current_dasha convenience function."""

    def test_returns_3_levels(self, mumbai_chart):
        """Should return active mahadasha + antardasha + pratyantardasha."""
        current = get_current_dasha(mumbai_chart, datetime(2000, 6, 15))
        assert len(current) == 3
        assert current[0].level == "mahadasha"
        assert current[1].level == "antardasha"
        assert current[2].level == "pratyantardasha"

    def test_date_within_range(self, mumbai_chart):
        """The queried date should fall within each returned period."""
        query_date = datetime(2000, 6, 15)
        current = get_current_dasha(mumbai_chart, query_date)
        for period in current:
            assert period.start <= query_date < period.end

    def test_birth_date_works(self, mumbai_chart):
        """Should work for the birth date itself."""
        current = get_current_dasha(mumbai_chart, mumbai_chart.birth_datetime)
        assert len(current) >= 1
        assert current[0].level == "mahadasha"
