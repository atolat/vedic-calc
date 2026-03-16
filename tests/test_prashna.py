"""Tests for Prashna (horary) chart casting, Tajika yoga detection, and verdict evaluation."""

import pytest

from vedic_calc import (
    cast_prashna_chart,
    detect_tajika_yogas,
    evaluate_prashna,
    BirthChart,
    TajikaYoga,
    PrashnaVerdict,
)
from vedic_calc.core.constants import Planet
from vedic_calc.prashna.tajika import _angular_distance, _has_tajika_aspect


# Mumbai, 2026-03-15 10:30 AM IST
PRASHNA_ARGS = dict(
    year=2026, month=3, day=15,
    hour=10, minute=30,
    latitude=19.076, longitude=72.878,
    timezone_offset=5.5,
)


class TestCastPrashnaChart:
    """Test that cast_prashna_chart produces a valid BirthChart."""

    def test_returns_birth_chart(self):
        chart = cast_prashna_chart(**PRASHNA_ARGS)
        assert isinstance(chart, BirthChart)

    def test_has_nine_planets(self):
        chart = cast_prashna_chart(**PRASHNA_ARGS)
        assert len(chart.planets) == 9

    def test_has_twelve_houses(self):
        chart = cast_prashna_chart(**PRASHNA_ARGS)
        assert len(chart.houses) == 12

    def test_ascendant_sign_valid(self):
        chart = cast_prashna_chart(**PRASHNA_ARGS)
        assert 1 <= chart.ascendant.sign.value <= 12

    def test_birth_datetime_matches(self):
        chart = cast_prashna_chart(**PRASHNA_ARGS)
        assert chart.birth_datetime.year == 2026
        assert chart.birth_datetime.month == 3
        assert chart.birth_datetime.day == 15


class TestAngularDistance:
    """Test the _angular_distance helper."""

    def test_zero(self):
        assert _angular_distance(0.0, 0.0) == 0.0

    def test_same_point(self):
        assert _angular_distance(100.0, 100.0) == 0.0

    def test_opposite(self):
        assert _angular_distance(0.0, 180.0) == 180.0

    def test_wraparound(self):
        assert abs(_angular_distance(350.0, 10.0) - 20.0) < 0.001

    def test_symmetric(self):
        assert _angular_distance(30.0, 90.0) == _angular_distance(90.0, 30.0)

    def test_ninety_degrees(self):
        assert abs(_angular_distance(0.0, 90.0) - 90.0) < 0.001

    def test_one_twenty(self):
        assert abs(_angular_distance(0.0, 120.0) - 120.0) < 0.001


class TestHasTajikaAspect:
    """Test Tajika aspect detection with orbs."""

    def test_conjunction_exact(self):
        assert _has_tajika_aspect(100.0, 100.0) == "conjunction"

    def test_conjunction_within_orb(self):
        assert _has_tajika_aspect(100.0, 107.0) == "conjunction"

    def test_conjunction_outside_orb(self):
        assert _has_tajika_aspect(100.0, 109.0) != "conjunction"

    def test_opposition_exact(self):
        assert _has_tajika_aspect(0.0, 180.0) == "opposition"

    def test_trine_within_orb(self):
        assert _has_tajika_aspect(0.0, 123.0) == "trine"

    def test_square_within_orb(self):
        assert _has_tajika_aspect(0.0, 93.0) == "square"

    def test_sextile_within_orb(self):
        assert _has_tajika_aspect(0.0, 62.0) == "sextile"

    def test_no_aspect(self):
        # 45° is not a Tajika aspect
        assert _has_tajika_aspect(0.0, 45.0) is None


class TestDetectTajikaYogas:
    """Test Tajika yoga detection on a real chart."""

    def test_returns_five_yogas(self):
        chart = cast_prashna_chart(**PRASHNA_ARGS)
        yogas = detect_tajika_yogas(chart, query_house=10)
        assert len(yogas) == 5

    def test_yoga_names(self):
        chart = cast_prashna_chart(**PRASHNA_ARGS)
        yogas = detect_tajika_yogas(chart, query_house=7)
        names = {y.name for y in yogas}
        assert names == {"Ithasala", "Easarapha", "Induvara", "Kamboola", "Nakta"}

    def test_all_yogas_are_tajika_type(self):
        chart = cast_prashna_chart(**PRASHNA_ARGS)
        yogas = detect_tajika_yogas(chart, query_house=10)
        for y in yogas:
            assert isinstance(y, TajikaYoga)
            assert y.significance in {"favorable", "unfavorable", "mixed", "neutral"}

    def test_ithasala_or_induvara_mutually_exclusive(self):
        """Ithasala (applying aspect) and Induvara (no aspect) cannot both be present."""
        chart = cast_prashna_chart(**PRASHNA_ARGS)
        yogas = detect_tajika_yogas(chart, query_house=10)
        yoga_map = {y.name: y for y in yogas}
        # If there's an aspect (Ithasala or Easarapha), Induvara must be absent
        if yoga_map["Ithasala"].is_present or yoga_map["Easarapha"].is_present:
            assert not yoga_map["Induvara"].is_present
        # If Induvara is present, neither Ithasala nor Easarapha should be
        if yoga_map["Induvara"].is_present:
            assert not yoga_map["Ithasala"].is_present
            assert not yoga_map["Easarapha"].is_present

    def test_different_houses_may_differ(self):
        """Different query houses should potentially produce different results."""
        chart = cast_prashna_chart(**PRASHNA_ARGS)
        yogas_7 = detect_tajika_yogas(chart, query_house=7)
        yogas_10 = detect_tajika_yogas(chart, query_house=10)
        # They use different query lords, so descriptions should differ
        # (unless by coincidence the same planet rules both houses)
        # Just verify both run without error
        assert len(yogas_7) == 5
        assert len(yogas_10) == 5


class TestEvaluatePrashna:
    """Test the full Prashna evaluation."""

    def test_returns_verdict(self):
        chart = cast_prashna_chart(**PRASHNA_ARGS)
        verdict = evaluate_prashna(chart, query_house=10)
        assert isinstance(verdict, PrashnaVerdict)

    def test_verdict_values(self):
        chart = cast_prashna_chart(**PRASHNA_ARGS)
        verdict = evaluate_prashna(chart, query_house=10)
        assert verdict.verdict in {"favorable", "unfavorable", "mixed"}

    def test_has_reasoning(self):
        chart = cast_prashna_chart(**PRASHNA_ARGS)
        verdict = evaluate_prashna(chart, query_house=10)
        assert len(verdict.reasoning) > 0

    def test_has_tajika_yogas(self):
        chart = cast_prashna_chart(**PRASHNA_ARGS)
        verdict = evaluate_prashna(chart, query_house=10)
        assert len(verdict.tajika_yogas) == 5

    def test_query_house_lord_set(self):
        chart = cast_prashna_chart(**PRASHNA_ARGS)
        verdict = evaluate_prashna(chart, query_house=7)
        assert isinstance(verdict.query_house_lord, Planet)
        assert verdict.query_house == 7

    def test_chart_time_preserved(self):
        chart = cast_prashna_chart(**PRASHNA_ARGS)
        verdict = evaluate_prashna(chart, query_house=1)
        assert verdict.chart_time == chart.birth_datetime

    def test_all_houses_work(self):
        """Evaluation should work for any house 1-12."""
        chart = cast_prashna_chart(**PRASHNA_ARGS)
        for house in range(1, 13):
            verdict = evaluate_prashna(chart, query_house=house)
            assert verdict.verdict in {"favorable", "unfavorable", "mixed"}
