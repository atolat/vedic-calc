"""Tests for additional dasha systems (Yogini, Ashtottari, Narayana)."""

import pytest

from vedic_calc import calculate_chart
from vedic_calc.core.constants import Planet
from vedic_calc.dasha.yogini import calculate_yogini_dasha
from vedic_calc.dasha.ashtottari import calculate_ashtottari_dasha
from vedic_calc.dasha.narayana import calculate_narayana_dasha


@pytest.fixture
def mumbai_chart():
    return calculate_chart(
        year=1990, month=3, day=15, hour=10, minute=30,
        latitude=19.0760, longitude=72.8777, timezone_offset=5.5,
    )


class TestYoginiDasha:
    def test_returns_periods(self, mumbai_chart):
        """Yogini cycle repeats 4 times -> 32 mahadasha periods."""
        periods = calculate_yogini_dasha(mumbai_chart, levels=1)
        assert len(periods) == 32  # 8 yoginis × 4 cycles

    def test_total_duration_covers_lifetime(self, mumbai_chart):
        """Total should be ~140 years (4 cycles of ~36y, first period partial)."""
        periods = calculate_yogini_dasha(mumbai_chart, levels=1)
        total = sum(p.duration_years for p in periods)
        # 4 full cycles = 144y, minus partial first period
        assert total > 130
        assert total <= 144.01

    def test_level2_has_sub_periods(self, mumbai_chart):
        periods = calculate_yogini_dasha(mumbai_chart, levels=2)
        mahas = [p for p in periods if p.level == "mahadasha"]
        antars = [p for p in periods if p.level == "antardasha"]
        assert len(mahas) == 32  # 8 × 4 cycles
        assert len(antars) == 256  # 8 × 8 × 4 cycles


class TestAshtottariDasha:
    def test_returns_periods(self, mumbai_chart):
        periods = calculate_ashtottari_dasha(mumbai_chart, levels=1)
        assert len(periods) == 8  # 8 planets

    def test_total_duration_at_most_108_years(self, mumbai_chart):
        """Total should be <= 108 years (first period is partial)."""
        periods = calculate_ashtottari_dasha(mumbai_chart, levels=1)
        total = sum(p.duration_years for p in periods)
        assert total <= 108.01
        assert total > 90  # Should be close to 108

    def test_no_ketu(self, mumbai_chart):
        """Ashtottari uses 8 planets — no Ketu."""
        periods = calculate_ashtottari_dasha(mumbai_chart, levels=1)
        lords = {p.lord for p in periods}
        assert Planet.KETU not in lords


class TestNarayanaDasha:
    def test_returns_12_periods(self, mumbai_chart):
        periods = calculate_narayana_dasha(mumbai_chart)
        mahas = [p for p in periods if p.level == "mahadasha"]
        assert len(mahas) == 12

    def test_durations_valid(self, mumbai_chart):
        periods = calculate_narayana_dasha(mumbai_chart)
        for p in periods:
            if p.level == "mahadasha":
                assert 1 <= p.duration_years <= 12
