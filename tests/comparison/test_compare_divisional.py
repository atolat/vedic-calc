"""Comparison tests: vedic-calc divisional charts vs PyJHora.

Compares sign placements for all nine planets (Sun-Ketu) across 15
divisional charts (D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27,
D30, D40, D45, D60) using three reference birth charts.

IMPORTANT METHOD DIFFERENCE:
    vedic-calc uses the Parashari method (formulas from BPHS Ch. 6) for
    divisional charts. PyJHora's `dasavarga_from_long()` and `dhasavarga()`
    both use the cyclic/Parivritti method: sign = (longitude * factor / 30) % 12.

    For some divisions (D9, D12, D60) both methods produce the same result.
    For others (D2, D3, D4, D7, D10, D30, etc.) the methods intentionally
    differ. Mismatches in those cases are NOT bugs — they reflect different
    but equally valid traditions.

    Divisions where Parashari == Cyclic: D1, D9, D12, D60
    Divisions where Parashari != Cyclic: D2, D3, D4, D7, D10, D16, D20,
        D24, D27, D30, D40, D45

PyJHora API:
    drik.dasavarga_from_long(longitude, division) returns (sign_0_11, degree)
    using the cyclic formula. We compare vedic-calc's Parashari output against
    this, and expect mismatches for divisions where the methods differ.

vedic-calc API:
    calculate_divisional_chart(chart, division) returns a DivisionalChart
    with .planets dict mapping Planet enum to Sign enum.
"""

import time

import pytest

from vedic_calc.chart.divisional import calculate_divisional_chart
from vedic_calc.core.constants import Planet, Sign

from .conftest import (
    REFERENCE_CHARTS,
    ComparisonRecord,
    pj_setup,
)

jhora = pytest.importorskip("jhora", reason="PyJHora not installed")

DIVISIONS = [2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]

# Divisions where Parashari and Cyclic methods give the same result.
# For these, mismatches indicate real bugs.
_SAME_METHOD_DIVISIONS = {1, 9}

# Planet names for readable output
_PLANET_NAMES = {
    Planet.SUN: "Sun",
    Planet.MOON: "Moon",
    Planet.MARS: "Mars",
    Planet.MERCURY: "Mercury",
    Planet.JUPITER: "Jupiter",
    Planet.VENUS: "Venus",
    Planet.SATURN: "Saturn",
    Planet.RAHU: "Rahu",
    Planet.KETU: "Ketu",
}


@pytest.mark.parametrize(
    "ref",
    REFERENCE_CHARTS,
    ids=[c.label for c in REFERENCE_CHARTS],
)
@pytest.mark.parametrize("division", DIVISIONS, ids=[f"D{d}" for d in DIVISIONS])
def test_divisional_chart_signs(ref, division, collector):
    """Compare divisional chart planet signs between vedic-calc and PyJHora.

    For divisions where Parashari != Cyclic, mismatches are recorded but
    the test does not fail (xfail-like behavior via soft assertion).
    """
    from jhora.panchanga import drik

    methods_match = division in _SAME_METHOD_DIVISIONS

    # -- vedic-calc ----------------------------------------------------------
    vc_chart = ref.calculate()

    vc_start = time.perf_counter()
    vc_div = calculate_divisional_chart(vc_chart, division)
    vc_time = (time.perf_counter() - vc_start) * 1000

    # -- PyJHora (cyclic method via dasavarga_from_long) ---------------------
    jd, place, _dob, _tob = pj_setup(ref)

    # IMPORTANT: PyJHora's julian_day_number uses LOCAL time, but
    # sidereal_longitude expects UTC JD. Convert by subtracting timezone.
    jd_utc = jd - ref.timezone_offset / 24.0

    pj_start = time.perf_counter()
    # Get each planet's sidereal longitude from PyJHora, then compute
    # divisional sign using the cyclic formula.
    pj_planets: dict[int, int] = {}
    from jhora import const
    # Map vedic-calc planet to PyJHora swe constant for sidereal_longitude
    _VC_TO_PJ_SWE = {
        0: 0,    # Sun
        1: 1,    # Moon
        2: 4,    # Mars → swe MARS=4
        3: 2,    # Mercury → swe MERCURY=2
        4: 5,    # Jupiter → swe JUPITER=5
        5: 3,    # Venus → swe VENUS=3
        6: 6,    # Saturn
        7: 10,   # Rahu — use Mean Node (SWE 10) to match vedic-calc
        # Ketu computed from Rahu below
    }
    # Get Rahu longitude first (needed for Ketu)
    # Use Mean Node (SWE 10) since vedic-calc uses Mean Node.
    # PyJHora's const._RAHU=11 is True Node, which differs by ~1-2°.
    rahu_lon = drik.sidereal_longitude(jd_utc, 10)

    for vc_planet_val in _PLANET_NAMES:
        if vc_planet_val.value == 8:  # Ketu = Rahu + 180°
            pj_lon = (rahu_lon + 180.0) % 360.0
        else:
            pj_swe_id = _VC_TO_PJ_SWE[vc_planet_val.value]
            pj_lon = drik.sidereal_longitude(jd_utc, pj_swe_id)
        pj_sign_0, _ = drik.dasavarga_from_long(pj_lon, division)
        pj_planets[vc_planet_val.value] = pj_sign_0 + 1  # Convert 0-11 → 1-12

    pj_time = (time.perf_counter() - pj_start) * 1000

    # -- Compare each planet --------------------------------------------------
    mismatches = []
    for planet in (
        Planet.SUN,
        Planet.MOON,
        Planet.MARS,
        Planet.MERCURY,
        Planet.JUPITER,
        Planet.VENUS,
        Planet.SATURN,
        Planet.RAHU,
        Planet.KETU,
    ):
        vc_sign = vc_div.planets[planet].value
        pj_sign = pj_planets.get(planet.value)

        match = vc_sign == pj_sign
        method_note = "" if methods_match else " [Parashari vs Cyclic]"
        notes = (
            ""
            if match
            else f"vc={Sign(vc_sign).name} pj={Sign(pj_sign).name}{method_note}"
        )
        collector.add(
            ComparisonRecord(
                feature=f"D{division} {_PLANET_NAMES[planet]} sign",
                chart_label=ref.label,
                vedic_calc_result=Sign(vc_sign).name,
                pyjhora_result=Sign(pj_sign).name,
                match=match,
                vc_time_ms=vc_time,
                pj_time_ms=pj_time,
                notes=notes,
            )
        )
        if not match:
            mismatches.append(
                f"{_PLANET_NAMES[planet]}: vc={Sign(vc_sign).name} pj={Sign(pj_sign).name}{method_note}"
            )

    # Only fail for divisions where both methods should agree
    if mismatches and methods_match:
        pytest.fail(
            f"D{division} sign mismatches for {ref.label}:\n"
            + "\n".join(f"  {m}" for m in mismatches)
        )
    elif mismatches and not methods_match:
        # Record but don't fail — different methods, not a bug
        pass
