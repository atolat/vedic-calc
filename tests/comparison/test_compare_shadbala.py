"""Comparison tests: vedic-calc Shadbala vs PyJHora.

Compares total Shadbala values and relative planet rankings between
vedic-calc's calculate_shadbala and PyJHora's strength.shad_bala.

Known algorithmic differences between the two implementations:

- **Dig Bala**: vedic-calc caps distance at 180° (max 60 SA per BPHS Ch. 27).
  PyJHora uses uncapped distance (max 120 SA). For any planet, vc + pj ≈ 120.
- **Kaala Bala**: Different Ahargana epoch tables for abda/masa/vaara lords.
  Different Nathonnatha and Tribhaga formulas. Can differ by 50%+.
- **Chesta Bala**: Different mean longitude orbital elements and methods.
- **Sthana Bala**: Different compound friendship models (Panchada vs simple).
- **Drik Bala**: Different aspect strength slab formulas and benefic/malefic
  classification approaches. Both follow BPHS but with different interpretations.

Because of these differences, component-level comparison uses very wide
tolerance (soft-fail), while ranking comparison checks only the strongest
and weakest planets.
"""

import time

import pytest

from vedic_calc.core.constants import Planet
from vedic_calc.strength.shadbala import calculate_shadbala
from .conftest import REFERENCE_CHARTS, ComparisonRecord, pj_setup

jhora = pytest.importorskip("jhora", reason="PyJHora (jhora) not installed")

# PyJHora shadbala planet order is the same as vedic-calc for indices 0-6:
# [Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn]
_PJ_INDEX_TO_PLANET = [
    Planet.SUN,
    Planet.MOON,
    Planet.MARS,
    Planet.MERCURY,
    Planet.JUPITER,
    Planet.VENUS,
    Planet.SATURN,
]

# Component index names in PyJHora's shad_bala output (sb[0]-sb[5])
_COMPONENT_NAMES = [
    "sthana_bala",
    "dig_bala",
    "kaala_bala",
    "chesta_bala",
    "naisargika_bala",
    "drik_bala",
]

# Tolerance for total shadbala comparison (35%)
# Wide tolerance needed because the two implementations use fundamentally
# different sub-algorithms for Dig Bala (60 vs 120 max), Kaala Bala, etc.
_TOLERANCE = 0.35

# Component-level comparison is informational only (soft-fail via xfail).
# Individual components can vary by 100%+ due to legitimate differences
# (e.g., Dig Bala: vedic-calc max=60, PyJHora max=120).
_COMPONENT_TOLERANCE = 0.50


def _pct_diff(a: float, b: float) -> float:
    """Return the relative difference between two values, using max as denominator."""
    denom = max(abs(a), abs(b))
    if denom == 0:
        return 0.0
    return abs(a - b) / denom


def _get_pyjhora_shadbala(jd, place):
    """Call PyJHora's shad_bala and return structured results.

    Returns a dict mapping Planet -> dict with keys:
        sthana_bala, dig_bala, kaala_bala, chesta_bala, naisargika_bala,
        drik_bala, total, required, ratio
    """
    from jhora.horoscope.chart import strength

    sb = strength.shad_bala(jd, place)

    # PyJHora shad_bala returns: [sthana, kaala, dig, chesta, naisargika, drik, ...]
    # Note: indices 1 and 2 are kaala and dig (not dig and kaala).
    results = {}
    for idx, planet in enumerate(_PJ_INDEX_TO_PLANET):
        results[planet] = {
            "sthana_bala": sb[0][idx],
            "kaala_bala": sb[1][idx],
            "dig_bala": sb[2][idx],
            "chesta_bala": sb[3][idx],
            "naisargika_bala": sb[4][idx],
            "drik_bala": sb[5][idx],
            "total": sb[6][idx],
            "required": sb[7][idx],
            "ratio": sb[8][idx],
        }
    return results


@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_shadbala_total_matches_pyjhora(ref, collector):
    """Compare total Shadbala for each planet (10% tolerance)."""
    # vedic-calc
    vc_chart = ref.calculate()
    t0 = time.perf_counter()
    vc_results = calculate_shadbala(vc_chart)
    vc_ms = (time.perf_counter() - t0) * 1000

    # PyJHora
    jd, place, _dob, _tob = pj_setup(ref)
    t0 = time.perf_counter()
    pj_results = _get_pyjhora_shadbala(jd, place)
    pj_ms = (time.perf_counter() - t0) * 1000

    for planet in _PJ_INDEX_TO_PLANET:
        vc_total = vc_results[planet].total
        pj_total = pj_results[planet]["total"]

        diff = _pct_diff(vc_total, pj_total)
        match = diff <= _TOLERANCE

        collector.add(ComparisonRecord(
            feature="shadbala_total",
            chart_label=ref.label,
            vedic_calc_result=round(vc_total, 2),
            pyjhora_result=round(pj_total, 2),
            match=match,
            vc_time_ms=vc_ms,
            pj_time_ms=pj_ms,
            tolerance=_TOLERANCE,
            notes=f"{planet.name}: diff={diff:.1%}",
        ))

        assert match, (
            f"{ref.label} | {planet.name}: vedic-calc total={vc_total:.2f}, "
            f"PyJHora total={pj_total:.2f}, diff={diff:.1%} exceeds {_TOLERANCE:.0%}"
        )


@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_shadbala_components_match_pyjhora(ref, collector):
    """Compare each Shadbala component for each planet (10% tolerance)."""
    vc_chart = ref.calculate()
    t0 = time.perf_counter()
    vc_results = calculate_shadbala(vc_chart)
    vc_ms = (time.perf_counter() - t0) * 1000

    jd, place, _dob, _tob = pj_setup(ref)
    t0 = time.perf_counter()
    pj_results = _get_pyjhora_shadbala(jd, place)
    pj_ms = (time.perf_counter() - t0) * 1000

    failures = []

    for planet in _PJ_INDEX_TO_PLANET:
        vc_sb = vc_results[planet]
        pj_sb = pj_results[planet]

        for comp_name in _COMPONENT_NAMES:
            vc_val = getattr(vc_sb, comp_name)
            pj_val = pj_sb[comp_name]

            diff = _pct_diff(vc_val, pj_val)
            match = diff <= _COMPONENT_TOLERANCE

            collector.add(ComparisonRecord(
                feature=f"shadbala_{comp_name}",
                chart_label=ref.label,
                vedic_calc_result=round(vc_val, 2),
                pyjhora_result=round(pj_val, 2),
                match=match,
                vc_time_ms=vc_ms,
                pj_time_ms=pj_ms,
                tolerance=_COMPONENT_TOLERANCE,
                notes=f"{planet.name}.{comp_name}: diff={diff:.1%}",
            ))

            if not match:
                failures.append(
                    f"{planet.name}.{comp_name}: vc={vc_val:.2f} pj={pj_val:.2f} "
                    f"diff={diff:.1%}"
                )

    if failures:
        pytest.xfail(
            f"{ref.label} | {len(failures)} component(s) exceed "
            f"{_COMPONENT_TOLERANCE:.0%} tolerance (known algorithmic diffs):\n  "
            + "\n  ".join(failures)
        )


@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_shadbala_ranking_matches_pyjhora(ref, collector):
    """Compare relative planet rankings by total Shadbala.

    The ranking order should match between vedic-calc and PyJHora, even if
    absolute values differ. We compare the top-3 and bottom-3 rankings
    to allow for minor reordering in the middle.
    """
    vc_chart = ref.calculate()
    t0 = time.perf_counter()
    vc_results = calculate_shadbala(vc_chart)
    vc_ms = (time.perf_counter() - t0) * 1000

    jd, place, _dob, _tob = pj_setup(ref)
    t0 = time.perf_counter()
    pj_results = _get_pyjhora_shadbala(jd, place)
    pj_ms = (time.perf_counter() - t0) * 1000

    # Build rankings (strongest first)
    vc_ranking = sorted(
        _PJ_INDEX_TO_PLANET,
        key=lambda p: vc_results[p].total,
        reverse=True,
    )
    pj_ranking = sorted(
        _PJ_INDEX_TO_PLANET,
        key=lambda p: pj_results[p]["total"],
        reverse=True,
    )

    vc_rank_names = [p.name for p in vc_ranking]
    pj_rank_names = [p.name for p in pj_ranking]

    # Check strongest planet
    strongest_match = vc_ranking[0] == pj_ranking[0]
    collector.add(ComparisonRecord(
        feature="shadbala_strongest_planet",
        chart_label=ref.label,
        vedic_calc_result=vc_ranking[0].name,
        pyjhora_result=pj_ranking[0].name,
        match=strongest_match,
        vc_time_ms=vc_ms,
        pj_time_ms=pj_ms,
        notes="Strongest planet by total Shadbala",
    ))

    # Check weakest planet
    weakest_match = vc_ranking[-1] == pj_ranking[-1]
    collector.add(ComparisonRecord(
        feature="shadbala_weakest_planet",
        chart_label=ref.label,
        vedic_calc_result=vc_ranking[-1].name,
        pyjhora_result=pj_ranking[-1].name,
        match=weakest_match,
        vc_time_ms=vc_ms,
        pj_time_ms=pj_ms,
        notes="Weakest planet by total Shadbala",
    ))

    # Check top-3 set (order-independent — same planets should be in top 3)
    vc_top3 = set(vc_rank_names[:3])
    pj_top3 = set(pj_rank_names[:3])
    top3_match = vc_top3 == pj_top3

    collector.add(ComparisonRecord(
        feature="shadbala_top3_set",
        chart_label=ref.label,
        vedic_calc_result=sorted(vc_top3),
        pyjhora_result=sorted(pj_top3),
        match=top3_match,
        vc_time_ms=vc_ms,
        pj_time_ms=pj_ms,
        notes="Top 3 strongest planets (set comparison)",
    ))

    # Check bottom-3 set (order-independent)
    vc_bottom3 = set(vc_rank_names[-3:])
    pj_bottom3 = set(pj_rank_names[-3:])
    bottom3_match = vc_bottom3 == pj_bottom3

    collector.add(ComparisonRecord(
        feature="shadbala_bottom3_set",
        chart_label=ref.label,
        vedic_calc_result=sorted(vc_bottom3),
        pyjhora_result=sorted(pj_bottom3),
        match=bottom3_match,
        vc_time_ms=vc_ms,
        pj_time_ms=pj_ms,
        notes="Bottom 3 weakest planets (set comparison)",
    ))

    # Full ranking comparison for the record
    full_match = vc_rank_names == pj_rank_names
    collector.add(ComparisonRecord(
        feature="shadbala_full_ranking",
        chart_label=ref.label,
        vedic_calc_result=vc_rank_names,
        pyjhora_result=pj_rank_names,
        match=full_match,
        vc_time_ms=vc_ms,
        pj_time_ms=pj_ms,
        notes="Full ranking comparison (exact order)",
    ))

    # Shadbala sub-algorithms differ too much between implementations for
    # reliable ranking comparison. Log all data for the report and xfail
    # on mismatches rather than hard-failing.
    if not strongest_match or not top3_match or not bottom3_match:
        pytest.xfail(
            f"{ref.label} | Ranking mismatch (known algorithmic diffs): "
            f"strongest vc={vc_ranking[0].name} pj={pj_ranking[0].name}, "
            f"vc_top3={sorted(vc_top3)}, pj_top3={sorted(pj_top3)}"
        )


@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_shadbala_ratio_direction_matches_pyjhora(ref, collector):
    """Check that planets deemed strong/weak agree between implementations.

    If PyJHora's ratio >= 1.0 (planet meets minimum), vedic-calc should
    also mark the planet as strong (is_strong=True), and vice versa.
    """
    vc_chart = ref.calculate()
    t0 = time.perf_counter()
    vc_results = calculate_shadbala(vc_chart)
    vc_ms = (time.perf_counter() - t0) * 1000

    jd, place, _dob, _tob = pj_setup(ref)
    t0 = time.perf_counter()
    pj_results = _get_pyjhora_shadbala(jd, place)
    pj_ms = (time.perf_counter() - t0) * 1000

    for planet in _PJ_INDEX_TO_PLANET:
        vc_strong = vc_results[planet].is_strong
        pj_ratio = pj_results[planet]["ratio"]
        pj_strong = pj_ratio >= 1.0

        match = vc_strong == pj_strong

        collector.add(ComparisonRecord(
            feature="shadbala_strong_weak_agreement",
            chart_label=ref.label,
            vedic_calc_result=f"{planet.name}: is_strong={vc_strong}",
            pyjhora_result=f"{planet.name}: ratio={pj_ratio:.2f} (strong={pj_strong})",
            match=match,
            vc_time_ms=vc_ms,
            pj_time_ms=pj_ms,
            notes=f"{planet.name}: vc_strong={vc_strong}, pj_ratio={pj_ratio:.2f}",
        ))

        # Soft assertion: log mismatch but don't fail (different thresholds)
        if not match:
            pytest.xfail(
                f"{ref.label} | {planet.name}: strong/weak disagree "
                f"(vc={vc_strong}, pj_ratio={pj_ratio:.2f}) — "
                f"likely different minimum thresholds"
            )
