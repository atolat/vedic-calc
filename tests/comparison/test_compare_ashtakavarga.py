"""Comparison tests: vedic-calc Ashtakavarga vs PyJHora.

Compares Bhinnashtakavarga (BAV) and Sarvashtakavarga (SAV) calculations
between vedic-calc and PyJHora using three reference birth charts.

PyJHora API:
    ashtakavarga.get_ashtaka_varga(chart_1d) returns (bav, sav, pav)
    - bav: list of 8 lists (indices 0-7: Sun, Moon, Mars, Mercury, Jupiter,
      Venus, Saturn, Lagna), each a list of 12 ints (points per sign 0-11).
    - sav: list of 12 ints (Sarvashtakavarga total per sign 0-11).

vedic-calc API:
    calculate_ashtakavarga(chart) returns AshtakavargaResult
    - .bhinna: dict mapping Planet enum (Sun=0 .. Saturn=6) to list of 12 ints.
    - .sarva: list of 12 ints.

Both BAV arrays are 12-element lists indexed 0-11 (Aries through Pisces).
"""

import time

import pytest

from vedic_calc.core.constants import Planet
from vedic_calc.strength.ashtakavarga import calculate_ashtakavarga

from .conftest import (
    REFERENCE_CHARTS,
    ComparisonRecord,
    pj_build_chart_1d,
    pj_setup,
)

jhora = pytest.importorskip("jhora", reason="PyJHora not installed")

# Planet names for readable output
_PLANET_NAMES = {
    Planet.SUN: "Sun",
    Planet.MOON: "Moon",
    Planet.MARS: "Mars",
    Planet.MERCURY: "Mercury",
    Planet.JUPITER: "Jupiter",
    Planet.VENUS: "Venus",
    Planet.SATURN: "Saturn",
}

# Map vedic-calc Planet enum value to PyJHora BAV index.
# PyJHora BAV indices: 0=Sun, 1=Moon, 2=Mars, 3=Mercury, 4=Jupiter, 5=Venus, 6=Saturn
# vedic-calc Planet:   Sun=0, Moon=1, Mars=2, Mercury=3, Jupiter=4, Venus=5, Saturn=6
# They happen to match exactly.
_VC_PLANET_TO_PJ_BAV_INDEX = {
    Planet.SUN: 0,
    Planet.MOON: 1,
    Planet.MARS: 2,
    Planet.MERCURY: 3,
    Planet.JUPITER: 4,
    Planet.VENUS: 5,
    Planet.SATURN: 6,
}

# Sign names for readable output
_SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


@pytest.mark.parametrize(
    "ref",
    REFERENCE_CHARTS,
    ids=[c.label for c in REFERENCE_CHARTS],
)
def test_bhinnashtakavarga(ref, collector):
    """Compare Bhinnashtakavarga for each of the 7 planets."""
    from jhora.horoscope.chart import ashtakavarga

    # -- vedic-calc ----------------------------------------------------------
    vc_chart = ref.calculate()

    vc_start = time.perf_counter()
    vc_result = calculate_ashtakavarga(vc_chart)
    vc_time = (time.perf_counter() - vc_start) * 1000

    # -- PyJHora --------------------------------------------------------------
    jd, place, _dob, _tob = pj_setup(ref)
    chart_1d = pj_build_chart_1d(jd, place)

    pj_start = time.perf_counter()
    pj_bav, pj_sav, _pj_pav = ashtakavarga.get_ashtaka_varga(chart_1d)
    pj_time = (time.perf_counter() - pj_start) * 1000

    # -- Compare BAV for each planet -----------------------------------------
    mismatches = []
    for planet in (
        Planet.SUN,
        Planet.MOON,
        Planet.MARS,
        Planet.MERCURY,
        Planet.JUPITER,
        Planet.VENUS,
        Planet.SATURN,
    ):
        pj_idx = _VC_PLANET_TO_PJ_BAV_INDEX[planet]
        vc_bav = vc_result.bhinna[planet]  # list of 12 ints
        pj_bav_planet = pj_bav[pj_idx]  # list of 12 ints

        match = vc_bav == pj_bav_planet

        collector.add(
            ComparisonRecord(
                feature=f"BAV {_PLANET_NAMES[planet]}",
                chart_label=ref.label,
                vedic_calc_result=vc_bav,
                pyjhora_result=pj_bav_planet,
                match=match,
                vc_time_ms=vc_time,
                pj_time_ms=pj_time,
                notes="" if match else _format_bav_diff(vc_bav, pj_bav_planet),
            )
        )
        if not match:
            mismatches.append(
                f"{_PLANET_NAMES[planet]}:\n"
                f"    vc = {vc_bav}\n"
                f"    pj = {pj_bav_planet}\n"
                f"    diff at: {_format_bav_diff(vc_bav, pj_bav_planet)}"
            )

    if mismatches:
        pytest.fail(
            f"BAV mismatches for {ref.label}:\n"
            + "\n".join(f"  {m}" for m in mismatches)
        )


@pytest.mark.parametrize(
    "ref",
    REFERENCE_CHARTS,
    ids=[c.label for c in REFERENCE_CHARTS],
)
def test_sarvashtakavarga(ref, collector):
    """Compare Sarvashtakavarga totals per sign."""
    from jhora.horoscope.chart import ashtakavarga

    # -- vedic-calc ----------------------------------------------------------
    vc_chart = ref.calculate()

    vc_start = time.perf_counter()
    vc_result = calculate_ashtakavarga(vc_chart)
    vc_time = (time.perf_counter() - vc_start) * 1000

    # -- PyJHora --------------------------------------------------------------
    jd, place, _dob, _tob = pj_setup(ref)
    chart_1d = pj_build_chart_1d(jd, place)

    pj_start = time.perf_counter()
    _pj_bav, pj_sav, _pj_pav = ashtakavarga.get_ashtaka_varga(chart_1d)
    pj_time = (time.perf_counter() - pj_start) * 1000

    # -- Compare SAV ---------------------------------------------------------
    vc_sav = vc_result.sarva  # list of 12 ints
    match = vc_sav == pj_sav

    collector.add(
        ComparisonRecord(
            feature="SAV",
            chart_label=ref.label,
            vedic_calc_result=vc_sav,
            pyjhora_result=pj_sav,
            match=match,
            vc_time_ms=vc_time,
            pj_time_ms=pj_time,
            notes="" if match else _format_bav_diff(vc_sav, pj_sav),
        )
    )

    if not match:
        pytest.fail(
            f"SAV mismatch for {ref.label}:\n"
            f"  vc  = {vc_sav}\n"
            f"  pj  = {pj_sav}\n"
            f"  diff: {_format_bav_diff(vc_sav, pj_sav)}"
        )


@pytest.mark.parametrize(
    "ref",
    REFERENCE_CHARTS,
    ids=[c.label for c in REFERENCE_CHARTS],
)
def test_bav_row_totals(ref, collector):
    """Verify BAV row totals are consistent between vedic-calc and PyJHora.

    Each planet's BAV row should sum to the same total in both libraries.
    This is a weaker check than exact sign-level match but useful for
    diagnosing whether differences are due to sign assignment vs point count.
    """
    from jhora.horoscope.chart import ashtakavarga

    # -- vedic-calc ----------------------------------------------------------
    vc_chart = ref.calculate()
    vc_result = calculate_ashtakavarga(vc_chart)

    # -- PyJHora --------------------------------------------------------------
    jd, place, _dob, _tob = pj_setup(ref)
    chart_1d = pj_build_chart_1d(jd, place)
    pj_bav, _pj_sav, _pj_pav = ashtakavarga.get_ashtaka_varga(chart_1d)

    # -- Compare row totals ---------------------------------------------------
    mismatches = []
    for planet in (
        Planet.SUN,
        Planet.MOON,
        Planet.MARS,
        Planet.MERCURY,
        Planet.JUPITER,
        Planet.VENUS,
        Planet.SATURN,
    ):
        pj_idx = _VC_PLANET_TO_PJ_BAV_INDEX[planet]
        vc_total = sum(vc_result.bhinna[planet])
        pj_total = sum(pj_bav[pj_idx])

        match = vc_total == pj_total
        collector.add(
            ComparisonRecord(
                feature=f"BAV total {_PLANET_NAMES[planet]}",
                chart_label=ref.label,
                vedic_calc_result=vc_total,
                pyjhora_result=pj_total,
                match=match,
                notes="" if match else f"diff={vc_total - pj_total}",
            )
        )
        if not match:
            mismatches.append(
                f"{_PLANET_NAMES[planet]}: vc_total={vc_total} pj_total={pj_total}"
            )

    if mismatches:
        pytest.fail(
            f"BAV row total mismatches for {ref.label}:\n"
            + "\n".join(f"  {m}" for m in mismatches)
        )


@pytest.mark.parametrize(
    "ref",
    REFERENCE_CHARTS,
    ids=[c.label for c in REFERENCE_CHARTS],
)
def test_sav_grand_total(ref, collector):
    """Verify SAV grand total (sum of all 12 signs) matches between libraries.

    The classical SAV grand total should always equal the sum of all BAV entries
    (7 planets x 12 signs). Both libraries should agree on this value.
    """
    from jhora.horoscope.chart import ashtakavarga

    # -- vedic-calc ----------------------------------------------------------
    vc_chart = ref.calculate()
    vc_result = calculate_ashtakavarga(vc_chart)

    # -- PyJHora --------------------------------------------------------------
    jd, place, _dob, _tob = pj_setup(ref)
    chart_1d = pj_build_chart_1d(jd, place)
    _pj_bav, pj_sav, _pj_pav = ashtakavarga.get_ashtaka_varga(chart_1d)

    # -- Compare grand totals -------------------------------------------------
    vc_grand = sum(vc_result.sarva)
    pj_grand = sum(pj_sav)

    match = vc_grand == pj_grand
    collector.add(
        ComparisonRecord(
            feature="SAV grand total",
            chart_label=ref.label,
            vedic_calc_result=vc_grand,
            pyjhora_result=pj_grand,
            match=match,
            notes="" if match else f"diff={vc_grand - pj_grand}",
        )
    )

    if not match:
        pytest.fail(
            f"SAV grand total mismatch for {ref.label}: "
            f"vc={vc_grand} pj={pj_grand} diff={vc_grand - pj_grand}"
        )


def _format_bav_diff(vc_list: list[int], pj_list: list[int]) -> str:
    """Format sign-level differences between two 12-element BAV/SAV lists."""
    diffs = []
    for i in range(12):
        if vc_list[i] != pj_list[i]:
            diffs.append(
                f"{_SIGN_NAMES[i]}: vc={vc_list[i]} pj={pj_list[i]}"
            )
    return "; ".join(diffs) if diffs else "identical"
