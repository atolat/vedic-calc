"""Comparison tests: vedic-calc divisional charts vs PyJHora.

Compares sign placements for all nine planets (Sun-Ketu) across 15
divisional charts (D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27,
D30, D40, D45, D60) using three reference birth charts.

PyJHora API:
    drik.dhasavarga(jd, place, division) returns a list of
    [planet_idx, (sign, deg)] entries where planet indices 0-8 follow
    the order Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Rahu, Ketu
    and signs are 0-11.

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
    PJ_DHASA_TO_VC_PLANET,
    map_pj_sign_to_vc,
    pj_setup,
)

jhora = pytest.importorskip("jhora", reason="PyJHora not installed")

DIVISIONS = [2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]

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
    """Compare divisional chart planet signs between vedic-calc and PyJHora."""
    from jhora.panchanga import drik

    # -- vedic-calc ----------------------------------------------------------
    vc_chart = ref.calculate()

    vc_start = time.perf_counter()
    vc_div = calculate_divisional_chart(vc_chart, division)
    vc_time = (time.perf_counter() - vc_start) * 1000

    # -- PyJHora --------------------------------------------------------------
    jd, place, _dob, _tob = pj_setup(ref)

    pj_start = time.perf_counter()
    pj_result = drik.dhasavarga(jd, place, division)
    pj_time = (time.perf_counter() - pj_start) * 1000

    # Build PyJHora lookup: vc_planet_value -> vc_sign_value
    pj_planets: dict[int, int] = {}
    for entry in pj_result:
        pj_idx = entry[0]
        pj_sign = entry[1][0]
        # Only map planet indices 0-8 (skip Lagna=9 and outer planets)
        if pj_idx in PJ_DHASA_TO_VC_PLANET:
            vc_planet_val = PJ_DHASA_TO_VC_PLANET[pj_idx]
            pj_planets[vc_planet_val] = map_pj_sign_to_vc(pj_sign)

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

        if pj_sign is None:
            # Planet not in PyJHora output — record and skip
            collector.add(
                ComparisonRecord(
                    feature=f"D{division} {_PLANET_NAMES[planet]} sign",
                    chart_label=ref.label,
                    vedic_calc_result=Sign(vc_sign).name,
                    pyjhora_result="MISSING",
                    match=False,
                    vc_time_ms=vc_time,
                    pj_time_ms=pj_time,
                    notes="Planet not found in PyJHora dhasavarga output",
                )
            )
            mismatches.append(f"{_PLANET_NAMES[planet]}: vc={Sign(vc_sign).name} pj=MISSING")
            continue

        match = vc_sign == pj_sign
        collector.add(
            ComparisonRecord(
                feature=f"D{division} {_PLANET_NAMES[planet]} sign",
                chart_label=ref.label,
                vedic_calc_result=Sign(vc_sign).name,
                pyjhora_result=Sign(pj_sign).name,
                match=match,
                vc_time_ms=vc_time,
                pj_time_ms=pj_time,
                notes="" if match else f"vc={Sign(vc_sign).name} pj={Sign(pj_sign).name}",
            )
        )
        if not match:
            mismatches.append(
                f"{_PLANET_NAMES[planet]}: vc={Sign(vc_sign).name} pj={Sign(pj_sign).name}"
            )

    if mismatches:
        pytest.fail(
            f"D{division} sign mismatches for {ref.label}:\n"
            + "\n".join(f"  {m}" for m in mismatches)
        )
