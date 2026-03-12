"""Compare vedic-calc muhurta calculations against PyJHora.

Tests Rahu Kalam, Yamagandam, Gulika Kalam, and Abhijit Muhurta
windows with a 5-minute tolerance (the two libraries use slightly
different sunrise/sunset algorithms).
"""

from __future__ import annotations

import time

import pytest

pytest.importorskip("jhora")

from vedic_calc.muhurta.calculator import calculate_muhurta

from .conftest import REFERENCE_CHARTS, ComparisonRecord, pj_setup


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TOLERANCE_MINUTES = 5.0


def _time_str_to_minutes(t: str) -> float:
    """Convert a PyJHora time string like '14:16:53' to minutes from midnight."""
    parts = t.strip().split(":")
    h, m = int(parts[0]), int(parts[1])
    s = int(parts[2]) if len(parts) > 2 else 0
    return h * 60 + m + s / 60.0


def _datetime_to_minutes(dt) -> float:
    """Convert a datetime to minutes from midnight."""
    return dt.hour * 60 + dt.minute + dt.second / 60.0


def _compare_window(
    vc_start_min: float,
    vc_end_min: float,
    pj_start_min: float,
    pj_end_min: float,
    tolerance: float = TOLERANCE_MINUTES,
) -> bool:
    """Return True if both start and end times are within tolerance."""
    return (
        abs(vc_start_min - pj_start_min) <= tolerance
        and abs(vc_end_min - pj_end_min) <= tolerance
    )


def _fmt_minutes(m: float) -> str:
    """Format minutes-from-midnight as HH:MM for readable output."""
    h = int(m // 60)
    mins = int(m % 60)
    return f"{h:02d}:{mins:02d}"


# ---------------------------------------------------------------------------
# Parametrized tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_rahu_kalam(ref, collector):
    """Compare Rahu Kalam window between vedic-calc and PyJHora."""
    from jhora.panchanga import drik

    jd, place, dob, tob = pj_setup(ref)

    # vedic-calc
    t0 = time.perf_counter()
    vc = calculate_muhurta(
        ref.year, ref.month, ref.day,
        ref.latitude, ref.longitude, ref.timezone_offset,
    )
    vc_ms = (time.perf_counter() - t0) * 1000
    vc_start = _datetime_to_minutes(vc.rahu_kalam[0])
    vc_end = _datetime_to_minutes(vc.rahu_kalam[1])

    # PyJHora
    t0 = time.perf_counter()
    pj_result = drik.raahu_kaalam(jd, place)
    pj_ms = (time.perf_counter() - t0) * 1000
    pj_start = _time_str_to_minutes(pj_result[0])
    pj_end = _time_str_to_minutes(pj_result[1])

    match = _compare_window(vc_start, vc_end, pj_start, pj_end)

    collector.add(ComparisonRecord(
        feature="Muhurta: Rahu Kalam",
        chart_label=ref.label,
        vedic_calc_result=f"{_fmt_minutes(vc_start)}-{_fmt_minutes(vc_end)}",
        pyjhora_result=f"{_fmt_minutes(pj_start)}-{_fmt_minutes(pj_end)}",
        match=match,
        vc_time_ms=vc_ms,
        pj_time_ms=pj_ms,
        tolerance=TOLERANCE_MINUTES,
        notes=f"start delta={abs(vc_start - pj_start):.1f}min, "
              f"end delta={abs(vc_end - pj_end):.1f}min",
    ))

    assert match, (
        f"Rahu Kalam mismatch for {ref.label}: "
        f"vc={_fmt_minutes(vc_start)}-{_fmt_minutes(vc_end)} vs "
        f"pj={_fmt_minutes(pj_start)}-{_fmt_minutes(pj_end)} "
        f"(tolerance={TOLERANCE_MINUTES}min)"
    )


@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_yamagandam(ref, collector):
    """Compare Yamagandam window between vedic-calc and PyJHora."""
    from jhora.panchanga import drik

    jd, place, dob, tob = pj_setup(ref)

    # vedic-calc
    t0 = time.perf_counter()
    vc = calculate_muhurta(
        ref.year, ref.month, ref.day,
        ref.latitude, ref.longitude, ref.timezone_offset,
    )
    vc_ms = (time.perf_counter() - t0) * 1000
    vc_start = _datetime_to_minutes(vc.yamagandam[0])
    vc_end = _datetime_to_minutes(vc.yamagandam[1])

    # PyJHora
    t0 = time.perf_counter()
    pj_result = drik.yamaganda_kaalam(jd, place)
    pj_ms = (time.perf_counter() - t0) * 1000
    pj_start = _time_str_to_minutes(pj_result[0])
    pj_end = _time_str_to_minutes(pj_result[1])

    match = _compare_window(vc_start, vc_end, pj_start, pj_end)

    collector.add(ComparisonRecord(
        feature="Muhurta: Yamagandam",
        chart_label=ref.label,
        vedic_calc_result=f"{_fmt_minutes(vc_start)}-{_fmt_minutes(vc_end)}",
        pyjhora_result=f"{_fmt_minutes(pj_start)}-{_fmt_minutes(pj_end)}",
        match=match,
        vc_time_ms=vc_ms,
        pj_time_ms=pj_ms,
        tolerance=TOLERANCE_MINUTES,
        notes=f"start delta={abs(vc_start - pj_start):.1f}min, "
              f"end delta={abs(vc_end - pj_end):.1f}min",
    ))

    assert match, (
        f"Yamagandam mismatch for {ref.label}: "
        f"vc={_fmt_minutes(vc_start)}-{_fmt_minutes(vc_end)} vs "
        f"pj={_fmt_minutes(pj_start)}-{_fmt_minutes(pj_end)} "
        f"(tolerance={TOLERANCE_MINUTES}min)"
    )


@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_gulika_kalam(ref, collector):
    """Compare Gulika Kalam window between vedic-calc and PyJHora."""
    from jhora.panchanga import drik

    jd, place, dob, tob = pj_setup(ref)

    # vedic-calc
    t0 = time.perf_counter()
    vc = calculate_muhurta(
        ref.year, ref.month, ref.day,
        ref.latitude, ref.longitude, ref.timezone_offset,
    )
    vc_ms = (time.perf_counter() - t0) * 1000
    vc_start = _datetime_to_minutes(vc.gulika_kalam[0])
    vc_end = _datetime_to_minutes(vc.gulika_kalam[1])

    # PyJHora
    t0 = time.perf_counter()
    pj_result = drik.gulikai_kaalam(jd, place)
    pj_ms = (time.perf_counter() - t0) * 1000
    pj_start = _time_str_to_minutes(pj_result[0])
    pj_end = _time_str_to_minutes(pj_result[1])

    match = _compare_window(vc_start, vc_end, pj_start, pj_end)

    collector.add(ComparisonRecord(
        feature="Muhurta: Gulika Kalam",
        chart_label=ref.label,
        vedic_calc_result=f"{_fmt_minutes(vc_start)}-{_fmt_minutes(vc_end)}",
        pyjhora_result=f"{_fmt_minutes(pj_start)}-{_fmt_minutes(pj_end)}",
        match=match,
        vc_time_ms=vc_ms,
        pj_time_ms=pj_ms,
        tolerance=TOLERANCE_MINUTES,
        notes=f"start delta={abs(vc_start - pj_start):.1f}min, "
              f"end delta={abs(vc_end - pj_end):.1f}min",
    ))

    assert match, (
        f"Gulika Kalam mismatch for {ref.label}: "
        f"vc={_fmt_minutes(vc_start)}-{_fmt_minutes(vc_end)} vs "
        f"pj={_fmt_minutes(pj_start)}-{_fmt_minutes(pj_end)} "
        f"(tolerance={TOLERANCE_MINUTES}min)"
    )


@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_abhijit_muhurta(ref, collector):
    """Compare Abhijit Muhurta window between vedic-calc and PyJHora."""
    from jhora.panchanga import drik

    jd, place, dob, tob = pj_setup(ref)

    # vedic-calc
    t0 = time.perf_counter()
    vc = calculate_muhurta(
        ref.year, ref.month, ref.day,
        ref.latitude, ref.longitude, ref.timezone_offset,
    )
    vc_ms = (time.perf_counter() - t0) * 1000
    vc_start = _datetime_to_minutes(vc.abhijit_muhurta[0])
    vc_end = _datetime_to_minutes(vc.abhijit_muhurta[1])

    # PyJHora
    t0 = time.perf_counter()
    pj_result = drik.abhijit_muhurta(jd, place)
    pj_ms = (time.perf_counter() - t0) * 1000
    pj_start = _time_str_to_minutes(pj_result[0])
    pj_end = _time_str_to_minutes(pj_result[1])

    match = _compare_window(vc_start, vc_end, pj_start, pj_end)

    collector.add(ComparisonRecord(
        feature="Muhurta: Abhijit Muhurta",
        chart_label=ref.label,
        vedic_calc_result=f"{_fmt_minutes(vc_start)}-{_fmt_minutes(vc_end)}",
        pyjhora_result=f"{_fmt_minutes(pj_start)}-{_fmt_minutes(pj_end)}",
        match=match,
        vc_time_ms=vc_ms,
        pj_time_ms=pj_ms,
        tolerance=TOLERANCE_MINUTES,
        notes=f"start delta={abs(vc_start - pj_start):.1f}min, "
              f"end delta={abs(vc_end - pj_end):.1f}min",
    ))

    assert match, (
        f"Abhijit Muhurta mismatch for {ref.label}: "
        f"vc={_fmt_minutes(vc_start)}-{_fmt_minutes(vc_end)} vs "
        f"pj={_fmt_minutes(pj_start)}-{_fmt_minutes(pj_end)} "
        f"(tolerance={TOLERANCE_MINUTES}min)"
    )
