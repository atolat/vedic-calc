"""Comparison tests: vedic-calc planetary aspects vs PyJHora.

Compares Graha Drishti (planetary aspects) between vedic-calc and PyJHora
using three reference birth charts.

PyJHora API:
    house.graha_drishti_from_chart(chart_1d) returns a tuple of three elements:
    (aspected_rasis, aspected_houses, aspected_planets)
    - aspected_planets is a dict: {planet_id: [aspected_planet_ids]}
    - Planet IDs in chart_1d format: '0'=Sun, '1'=Moon, '2'=Mercury,
      '3'=Venus, '4'=Mars, '5'=Jupiter, '6'=Saturn, '7'=Rahu, '8'=Ketu
    - aspected_rasis is a dict: {planet_id: [rasi_indices]}

vedic-calc API:
    calculate_aspects(chart) returns a list of AspectInfo with:
    .aspecting_planet (Planet enum), .aspected_planet (Planet enum or None),
    .aspected_house (int 1-12), .aspect_type (str), .is_special (bool)

Note: PyJHora uses a different planet index order than vedic-calc for
chart_1d (Mercury=2, Venus=3, Mars=4, Jupiter=5) whereas vedic-calc uses
(Mars=2, Mercury=3, Jupiter=4, Venus=5). Mapping is handled carefully.
"""

import time

import pytest

from vedic_calc.chart.aspects import calculate_aspects
from vedic_calc.core.constants import Planet

from .conftest import (
    REFERENCE_CHARTS,
    ComparisonRecord,
    pj_build_chart_1d,
    pj_setup,
)

jhora = pytest.importorskip("jhora", reason="PyJHora not installed")

# ---------------------------------------------------------------------------
# Mapping between PyJHora chart_1d planet IDs and vedic-calc Planet enum
# ---------------------------------------------------------------------------
# graha_drishti_from_chart returns results keyed by planet_list index:
#   planet_list = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu']
# So: 0=Sun, 1=Moon, 2=Mars, 3=Mercury, 4=Jupiter, 5=Venus, 6=Saturn, 7=Rahu, 8=Ketu
# vedic-calc:  SUN=0, MOON=1, MARS=2, MERCURY=3, JUPITER=4, VENUS=5,
#              SATURN=6, RAHU=7, KETU=8
# The mapping is identity (same order).

_PJ_CHART1D_TO_VC_PLANET = {
    0: Planet.SUN,
    1: Planet.MOON,
    2: Planet.MARS,
    3: Planet.MERCURY,
    4: Planet.JUPITER,
    5: Planet.VENUS,
    6: Planet.SATURN,
    7: Planet.RAHU,
    8: Planet.KETU,
}

_VC_PLANET_TO_PJ_CHART1D = {v: k for k, v in _PJ_CHART1D_TO_VC_PLANET.items()}

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

# Planets that have aspects in Vedic astrology (all nine grahas)
_ALL_PLANETS = [
    Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
    Planet.JUPITER, Planet.VENUS, Planet.SATURN, Planet.RAHU, Planet.KETU,
]


def _normalize_pj_key(key):
    """Normalize a PyJHora dict key to an int, handling str or int."""
    if isinstance(key, str):
        # Handle 'L' (Lagna) or other non-numeric keys
        try:
            return int(key)
        except ValueError:
            return None
    return int(key)


def _extract_pj_aspected_rasis(pj_result):
    """Extract per-planet aspected rasi sets from PyJHora drishti output.

    Returns dict mapping vedic-calc Planet -> set of rasi indices (0-11).
    """
    aspected_rasis_dict = pj_result[0]  # first element is aspected_rasis
    result = {}
    for pj_key, rasi_list in aspected_rasis_dict.items():
        pj_id = _normalize_pj_key(pj_key)
        if pj_id is None or pj_id not in _PJ_CHART1D_TO_VC_PLANET:
            continue
        vc_planet = _PJ_CHART1D_TO_VC_PLANET[pj_id]
        # rasi_list items may be int or str
        rasis = set()
        for r in rasi_list:
            try:
                rasis.add(int(r))
            except (ValueError, TypeError):
                pass
        result[vc_planet] = rasis
    return result


def _extract_pj_aspected_planets(pj_result):
    """Extract per-planet aspected planet sets from PyJHora drishti output.

    Returns dict mapping vedic-calc Planet -> set of vedic-calc Planets.
    """
    aspected_planets_dict = pj_result[2]  # third element is aspected_planets
    result = {}
    for pj_key, target_list in aspected_planets_dict.items():
        pj_id = _normalize_pj_key(pj_key)
        if pj_id is None or pj_id not in _PJ_CHART1D_TO_VC_PLANET:
            continue
        vc_planet = _PJ_CHART1D_TO_VC_PLANET[pj_id]
        targets = set()
        for t in target_list:
            t_id = _normalize_pj_key(t)
            if t_id is not None and t_id in _PJ_CHART1D_TO_VC_PLANET:
                targets.add(_PJ_CHART1D_TO_VC_PLANET[t_id])
        result[vc_planet] = targets
    return result


def _vc_aspected_houses_by_planet(aspects):
    """Build dict: Planet -> set of aspected house numbers from vedic-calc."""
    result = {}
    for a in aspects:
        result.setdefault(a.aspecting_planet, set()).add(a.aspected_house)
    return result


def _vc_aspected_planets_by_planet(aspects):
    """Build dict: Planet -> set of aspected Planets from vedic-calc."""
    result = {}
    for a in aspects:
        if a.aspected_planet is not None:
            result.setdefault(a.aspecting_planet, set()).add(a.aspected_planet)
    return result


# ---------------------------------------------------------------------------
# Test: compare aspected rasis/houses per planet
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "ref",
    REFERENCE_CHARTS,
    ids=[c.label for c in REFERENCE_CHARTS],
)
def test_aspected_houses_match_pyjhora(ref, collector):
    """Compare which houses/rasis each planet aspects in vedic-calc vs PyJHora."""
    from jhora.horoscope.chart import house

    # -- vedic-calc -----------------------------------------------------------
    vc_chart = ref.calculate()

    vc_start = time.perf_counter()
    vc_aspects = calculate_aspects(vc_chart)
    vc_time = (time.perf_counter() - vc_start) * 1000

    vc_houses = _vc_aspected_houses_by_planet(vc_aspects)

    # Convert vedic-calc house numbers (1-12) to rasi indices (0-11) for
    # comparison. In whole-sign houses, house N corresponds to a sign;
    # we use the chart's house list to get the sign index.
    vc_rasis_by_planet = {}
    for planet, houses_set in vc_houses.items():
        rasis = set()
        for h in houses_set:
            # house_number is 1-based; chart.houses is 0-indexed
            sign_val = vc_chart.houses[h - 1].sign.value  # Sign enum value 1-12
            rasis.add(sign_val - 1)  # Convert to 0-11
        vc_rasis_by_planet[planet] = rasis

    # -- PyJHora --------------------------------------------------------------
    jd, place, _dob, _tob = pj_setup(ref)

    pj_start = time.perf_counter()
    try:
        chart_1d = pj_build_chart_1d(jd, place)
        pj_result = house.graha_drishti_from_chart(chart_1d)
        pj_time = (time.perf_counter() - pj_start) * 1000
    except Exception as exc:
        pj_time = (time.perf_counter() - pj_start) * 1000
        collector.add(
            ComparisonRecord(
                feature="Aspects (houses)",
                chart_label=ref.label,
                vedic_calc_result=f"{len(vc_aspects)} aspects",
                pyjhora_result=f"ERROR: {exc}",
                match=False,
                vc_time_ms=vc_time,
                pj_time_ms=pj_time,
                notes=f"PyJHora graha_drishti_from_chart raised: {type(exc).__name__}",
            )
        )
        pytest.skip(f"PyJHora graha_drishti_from_chart failed: {exc}")
        return

    pj_rasis_by_planet = _extract_pj_aspected_rasis(pj_result)

    # -- Compare each planet --------------------------------------------------
    mismatches = []
    for planet in _ALL_PLANETS:
        vc_rasis = vc_rasis_by_planet.get(planet, set())
        pj_rasis = pj_rasis_by_planet.get(planet, set())

        match = vc_rasis == pj_rasis
        vc_sorted = sorted(vc_rasis)
        pj_sorted = sorted(pj_rasis)

        collector.add(
            ComparisonRecord(
                feature=f"Aspects {_PLANET_NAMES[planet]} aspected rasis",
                chart_label=ref.label,
                vedic_calc_result=str(vc_sorted),
                pyjhora_result=str(pj_sorted),
                match=match,
                vc_time_ms=vc_time,
                pj_time_ms=pj_time,
                notes="" if match else (
                    f"vc_only={sorted(vc_rasis - pj_rasis)} "
                    f"pj_only={sorted(pj_rasis - vc_rasis)}"
                ),
            )
        )
        if not match:
            mismatches.append(
                f"{_PLANET_NAMES[planet]}: "
                f"vc={vc_sorted} pj={pj_sorted} "
                f"(vc_only={sorted(vc_rasis - pj_rasis)}, "
                f"pj_only={sorted(pj_rasis - vc_rasis)})"
            )

    if mismatches:
        pytest.fail(
            f"Aspected rasi mismatches for {ref.label}:\n"
            + "\n".join(f"  {m}" for m in mismatches)
        )


# ---------------------------------------------------------------------------
# Test: compare aspected planets per planet
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "ref",
    REFERENCE_CHARTS,
    ids=[c.label for c in REFERENCE_CHARTS],
)
def test_aspected_planets_match_pyjhora(ref, collector):
    """Compare which planets each planet aspects in vedic-calc vs PyJHora."""
    from jhora.horoscope.chart import house

    # -- vedic-calc -----------------------------------------------------------
    vc_chart = ref.calculate()

    vc_start = time.perf_counter()
    vc_aspects = calculate_aspects(vc_chart)
    vc_time = (time.perf_counter() - vc_start) * 1000

    vc_aspected = _vc_aspected_planets_by_planet(vc_aspects)

    # -- PyJHora --------------------------------------------------------------
    jd, place, _dob, _tob = pj_setup(ref)

    pj_start = time.perf_counter()
    try:
        chart_1d = pj_build_chart_1d(jd, place)
        pj_result = house.graha_drishti_from_chart(chart_1d)
        pj_time = (time.perf_counter() - pj_start) * 1000
    except Exception as exc:
        pj_time = (time.perf_counter() - pj_start) * 1000
        collector.add(
            ComparisonRecord(
                feature="Aspects (planets)",
                chart_label=ref.label,
                vedic_calc_result=f"{len(vc_aspects)} aspects",
                pyjhora_result=f"ERROR: {exc}",
                match=False,
                vc_time_ms=vc_time,
                pj_time_ms=pj_time,
                notes=f"PyJHora graha_drishti_from_chart raised: {type(exc).__name__}",
            )
        )
        pytest.skip(f"PyJHora graha_drishti_from_chart failed: {exc}")
        return

    pj_aspected = _extract_pj_aspected_planets(pj_result)

    # -- Compare each planet --------------------------------------------------
    mismatches = []
    for planet in _ALL_PLANETS:
        vc_targets = vc_aspected.get(planet, set())
        pj_targets = pj_aspected.get(planet, set())

        match = vc_targets == pj_targets

        vc_names = sorted(p.name for p in vc_targets)
        pj_names = sorted(p.name for p in pj_targets)

        collector.add(
            ComparisonRecord(
                feature=f"Aspects {_PLANET_NAMES[planet]} aspected planets",
                chart_label=ref.label,
                vedic_calc_result=str(vc_names),
                pyjhora_result=str(pj_names),
                match=match,
                vc_time_ms=vc_time,
                pj_time_ms=pj_time,
                notes="" if match else (
                    f"vc_only={sorted(p.name for p in vc_targets - pj_targets)} "
                    f"pj_only={sorted(p.name for p in pj_targets - vc_targets)}"
                ),
            )
        )
        if not match:
            mismatches.append(
                f"{_PLANET_NAMES[planet]}: "
                f"vc={vc_names} pj={pj_names}"
            )

    if mismatches:
        pytest.fail(
            f"Aspected planet mismatches for {ref.label}:\n"
            + "\n".join(f"  {m}" for m in mismatches)
        )


# ---------------------------------------------------------------------------
# Test: compare total aspect counts as a high-level sanity check
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "ref",
    REFERENCE_CHARTS,
    ids=[c.label for c in REFERENCE_CHARTS],
)
def test_aspect_count_comparison(ref, collector):
    """Compare total number of planet-to-planet aspects as a sanity check.

    Even if individual aspect mappings differ slightly, the total count of
    planet-to-planet aspects should be in the same ballpark. This test uses
    a tolerance of +/- 5 to account for Rahu/Ketu aspect differences.
    """
    from jhora.horoscope.chart import house

    # -- vedic-calc -----------------------------------------------------------
    vc_chart = ref.calculate()

    vc_start = time.perf_counter()
    vc_aspects = calculate_aspects(vc_chart)
    vc_time = (time.perf_counter() - vc_start) * 1000

    # Count only planet-to-planet aspects (not house-only)
    vc_p2p_count = sum(1 for a in vc_aspects if a.aspected_planet is not None)

    # -- PyJHora --------------------------------------------------------------
    jd, place, _dob, _tob = pj_setup(ref)

    pj_start = time.perf_counter()
    try:
        chart_1d = pj_build_chart_1d(jd, place)
        pj_result = house.graha_drishti_from_chart(chart_1d)
        pj_time = (time.perf_counter() - pj_start) * 1000
    except Exception as exc:
        pj_time = (time.perf_counter() - pj_start) * 1000
        collector.add(
            ComparisonRecord(
                feature="Aspects (count)",
                chart_label=ref.label,
                vedic_calc_result=str(vc_p2p_count),
                pyjhora_result=f"ERROR: {exc}",
                match=False,
                vc_time_ms=vc_time,
                pj_time_ms=pj_time,
                notes=f"PyJHora raised: {type(exc).__name__}",
            )
        )
        pytest.skip(f"PyJHora graha_drishti_from_chart failed: {exc}")
        return

    pj_aspected = _extract_pj_aspected_planets(pj_result)
    pj_p2p_count = sum(len(targets) for targets in pj_aspected.values())

    # Allow tolerance since Rahu/Ketu aspect rules may differ
    tolerance = 5
    match = abs(vc_p2p_count - pj_p2p_count) <= tolerance

    collector.add(
        ComparisonRecord(
            feature="Aspects total planet-to-planet count",
            chart_label=ref.label,
            vedic_calc_result=str(vc_p2p_count),
            pyjhora_result=str(pj_p2p_count),
            match=match,
            vc_time_ms=vc_time,
            pj_time_ms=pj_time,
            tolerance=tolerance,
            notes="" if match else f"diff={abs(vc_p2p_count - pj_p2p_count)}",
        )
    )
    if not match:
        pytest.fail(
            f"Aspect count mismatch for {ref.label}: "
            f"vc={vc_p2p_count} pj={pj_p2p_count} "
            f"(diff={abs(vc_p2p_count - pj_p2p_count)}, tolerance={tolerance})"
        )
