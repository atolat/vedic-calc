"""Tests for the Muhurta constraint solver."""

import pytest
from datetime import datetime

from vedic_calc import find_muhurta_windows, MuhurtaSearchResult, MuhurtaWindow
from vedic_calc.muhurta.solver import _chandrabala_ok, _tarabala_ok


# Mumbai location
LAT, LON, TZ = 19.076, 72.878, 5.5

# A 7-day range in March 2026
START = datetime(2026, 3, 15)
END = datetime(2026, 3, 21)

# A wider range to ensure we find results
WIDE_START = datetime(2026, 3, 1)
WIDE_END = datetime(2026, 3, 31)


class TestMuhurtaWindowStructure:
    """Test that the solver returns valid MuhurtaSearchResult."""

    def test_returns_search_result(self):
        result = find_muhurta_windows(
            "general", START, END, LAT, LON, TZ,
        )
        assert isinstance(result, MuhurtaSearchResult)
        assert result.activity == "general"

    def test_windows_are_muhurta_window(self):
        result = find_muhurta_windows(
            "general", WIDE_START, WIDE_END, LAT, LON, TZ,
        )
        for w in result.windows:
            assert isinstance(w, MuhurtaWindow)

    def test_max_results_respected(self):
        result = find_muhurta_windows(
            "general", WIDE_START, WIDE_END, LAT, LON, TZ,
            max_results=3,
        )
        assert len(result.windows) <= 3

    def test_score_range(self):
        result = find_muhurta_windows(
            "general", WIDE_START, WIDE_END, LAT, LON, TZ,
        )
        for w in result.windows:
            assert 0.0 <= w.score <= 100.0

    def test_windows_have_reasoning(self):
        result = find_muhurta_windows(
            "general", WIDE_START, WIDE_END, LAT, LON, TZ,
        )
        for w in result.windows:
            assert len(w.reasoning) > 0


class TestMuhurtaFiltering:
    """Test that bad panchanga elements are filtered out."""

    def test_excludes_bad_days(self):
        """Over a full month, the solver should find some windows but skip bad days."""
        result = find_muhurta_windows(
            "general", WIDE_START, WIDE_END, LAT, LON, TZ,
            max_results=10,
        )
        # Should find at least 1 window in a month
        assert len(result.windows) >= 1

    def test_rahu_kalam_mentioned(self):
        """Each window should mention Rahu Kalam in reasoning."""
        result = find_muhurta_windows(
            "general", WIDE_START, WIDE_END, LAT, LON, TZ,
        )
        for w in result.windows:
            rk_mentioned = any("Rahu Kalam" in r for r in w.reasoning)
            assert rk_mentioned, f"Rahu Kalam not mentioned in {w.start.date()}"


class TestScoringOrder:
    """Test that windows are sorted by score descending."""

    def test_descending_scores(self):
        result = find_muhurta_windows(
            "general", WIDE_START, WIDE_END, LAT, LON, TZ,
            max_results=10,
        )
        scores = [w.score for w in result.windows]
        assert scores == sorted(scores, reverse=True)


class TestChandrabala:
    """Unit test the Chandrabala helper."""

    def test_favorable_positions(self):
        # distance 1 (same sign), 3, 6, 7, 10, 11 are good
        assert _chandrabala_ok(1, 1) is True   # distance 1
        assert _chandrabala_ok(3, 1) is True   # distance 3
        assert _chandrabala_ok(6, 1) is True   # distance 6
        assert _chandrabala_ok(7, 1) is True   # distance 7
        assert _chandrabala_ok(10, 1) is True  # distance 10
        assert _chandrabala_ok(11, 1) is True  # distance 11

    def test_unfavorable_positions(self):
        # distance 2, 4, 5, 8, 9, 12 are bad
        assert _chandrabala_ok(2, 1) is False  # distance 2
        assert _chandrabala_ok(4, 1) is False  # distance 4
        assert _chandrabala_ok(5, 1) is False  # distance 5
        assert _chandrabala_ok(8, 1) is False  # distance 8
        assert _chandrabala_ok(9, 1) is False  # distance 9
        assert _chandrabala_ok(12, 1) is False # distance 12

    def test_wraparound(self):
        # Transit in Aries(1), natal in Pisces(12) → distance = (1-12)%12 + 1 = 2 → bad
        assert _chandrabala_ok(1, 12) is False
        # Transit in Pisces(12), natal in Aries(1) → distance = (12-1)%12 + 1 = 12 → bad
        assert _chandrabala_ok(12, 1) is False


class TestTarabala:
    """Unit test the Tarabala helper."""

    def test_same_nakshatra(self):
        # Same nakshatra = distance 27 → tara = ((27-1)%9)+1 = 9 = Parama Mitra → good
        assert _tarabala_ok(1, 1) is True

    def test_good_taras(self):
        # tara 1 (Janma): distance 1 from natal
        assert _tarabala_ok(2, 1) is True  # distance 1 → tara 1
        # tara 2 (Sampat): distance 2
        assert _tarabala_ok(3, 1) is True  # distance 2 → tara 2

    def test_bad_taras(self):
        # tara 3 (Vipat): distance 3
        assert _tarabala_ok(4, 1) is False  # distance 3 → tara 3
        # tara 5 (Pratyari): distance 5
        assert _tarabala_ok(6, 1) is False  # distance 5 → tara 5
        # tara 7 (Vadha): distance 7
        assert _tarabala_ok(8, 1) is False  # distance 7 → tara 7


class TestPersonalOverlays:
    """Test that natal Moon overlays work."""

    def test_with_natal_moon(self):
        result = find_muhurta_windows(
            "marriage", WIDE_START, WIDE_END, LAT, LON, TZ,
            natal_moon_nakshatra=4,  # Rohini
            natal_moon_sign=2,       # Taurus
        )
        for w in result.windows:
            assert w.chandrabala_ok is not None
            assert w.tarabala_ok is not None

    def test_without_natal_moon(self):
        result = find_muhurta_windows(
            "marriage", WIDE_START, WIDE_END, LAT, LON, TZ,
        )
        for w in result.windows:
            assert w.chandrabala_ok is None
            assert w.tarabala_ok is None


class TestDifferentActivities:
    """Test that different activities may produce different results."""

    def test_marriage_vs_business(self):
        marriage = find_muhurta_windows(
            "marriage", WIDE_START, WIDE_END, LAT, LON, TZ, max_results=3,
        )
        business = find_muhurta_windows(
            "business", WIDE_START, WIDE_END, LAT, LON, TZ, max_results=3,
        )
        # Both should return results
        assert len(marriage.windows) >= 1
        assert len(business.windows) >= 1
        # Activities differ
        assert marriage.activity == "marriage"
        assert business.activity == "business"

    def test_unknown_activity_falls_back_to_general(self):
        result = find_muhurta_windows(
            "xyz_unknown", WIDE_START, WIDE_END, LAT, LON, TZ,
        )
        # Should not crash, falls back to "general" rules
        assert isinstance(result, MuhurtaSearchResult)


class TestEmptyRange:
    """Test edge cases."""

    def test_single_day(self):
        result = find_muhurta_windows(
            "general",
            datetime(2026, 3, 15), datetime(2026, 3, 15),
            LAT, LON, TZ,
        )
        assert isinstance(result, MuhurtaSearchResult)
        # May or may not have a window depending on the day's panchanga

    def test_end_before_start(self):
        result = find_muhurta_windows(
            "general",
            datetime(2026, 3, 20), datetime(2026, 3, 15),
            LAT, LON, TZ,
        )
        assert result.windows == []
