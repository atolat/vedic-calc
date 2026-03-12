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

Known divergence — Moon BAV:
    PyJHora uses slightly different benefic-house tables for Moon's BAV
    compared to BPHS (vedic-calc follows BPHS). Specifically:
      - Moon from Moon:    vedic-calc [1,3,6,7,10,11]     vs PyJHora [1,3,6,7,9,10,11]
      - Mars from Moon:    vedic-calc [2,3,5,6,9,10,11]   vs PyJHora [2,3,5,6,10,11]
      - Jupiter from Moon: vedic-calc [1,4,7,8,10,11,12]  vs PyJHora [1,2,4,7,8,10,11]
    Row totals match (same number of total bindus), but sign-level distribution
    differs.  SAV is also affected since it sums all 7 BAV tables.
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
    # Moon BAV has a known table divergence (see module docstring) — different
    # benefic-house lists between BPHS (vedic-calc) and PyJHora.  We still
    # record the comparison but only fail on unexpected mismatches.
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
        is_known_divergence = planet == Planet.MOON

        notes = ""
        if not match:
            notes = _format_bav_diff(vc_bav, pj_bav_planet)
            if is_known_divergence:
                notes = "KNOWN TABLE DIVERGENCE (BPHS vs PyJHora); " + notes

        collector.add(
            ComparisonRecord(
                feature=f"BAV {_PLANET_NAMES[planet]}",
                chart_label=ref.label,
                vedic_calc_result=vc_bav,
                pyjhora_result=pj_bav_planet,
                match=match,
                vc_time_ms=vc_time,
                pj_time_ms=pj_time,
                notes=notes,
            )
        )
        if not match and not is_known_divergence:
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
    # SAV includes Moon BAV, which has a known table divergence (see module
    # docstring).  Compute SAV-without-Moon to verify the non-Moon planets
    # contribute identically, and attribute any remaining diff to Moon.
    vc_sav = vc_result.sarva  # list of 12 ints
    match = vc_sav == pj_sav

    # SAV excluding Moon — should match exactly
    pj_bav, _, _ = ashtakavarga.get_ashtaka_varga(chart_1d)
    vc_sav_no_moon = [
        vc_sav[i] - vc_result.bhinna[Planet.MOON][i] for i in range(12)
    ]
    pj_sav_no_moon = [pj_sav[i] - pj_bav[1][i] for i in range(12)]
    sav_no_moon_match = vc_sav_no_moon == pj_sav_no_moon

    notes = ""
    if not match:
        notes = _format_bav_diff(vc_sav, pj_sav)
        if sav_no_moon_match:
            notes = "KNOWN: diff entirely from Moon BAV table divergence; " + notes

    collector.add(
        ComparisonRecord(
            feature="SAV",
            chart_label=ref.label,
            vedic_calc_result=vc_sav,
            pyjhora_result=pj_sav,
            match=match,
            vc_time_ms=vc_time,
            pj_time_ms=pj_time,
            notes=notes,
        )
    )

    # Fail only if SAV-without-Moon diverges (unexpected mismatch)
    if not sav_no_moon_match:
        pytest.fail(
            f"SAV mismatch for {ref.label} (beyond known Moon divergence):\n"
            f"  vc  = {vc_sav}\n"
            f"  pj  = {pj_sav}\n"
            f"  diff: {_format_bav_diff(vc_sav, pj_sav)}\n"
            f"  SAV-no-Moon vc = {vc_sav_no_moon}\n"
            f"  SAV-no-Moon pj = {pj_sav_no_moon}"
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
