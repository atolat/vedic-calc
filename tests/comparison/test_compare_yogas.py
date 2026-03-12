"""Comparison tests: vedic-calc yogas vs PyJHora.

Compares yoga detection between vedic-calc and PyJHora across reference charts.
Since the two systems may define and name yogas differently, we:

1. Compare total yoga counts as a rough metric.
2. Normalize yoga names (lowercase, strip whitespace/hyphens) to find common yogas.
3. For well-known yogas found in both systems, compare presence/absence.
4. Record all comparisons via the ComparisonCollector for the summary report.
"""

from __future__ import annotations

import time

import pytest

from vedic_calc.yoga.calculator import detect_yogas
from .conftest import (
    REFERENCE_CHARTS,
    ComparisonRecord,
    pj_setup,
)

jhora = pytest.importorskip("jhora", reason="PyJHora (jhora) not installed")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_yoga_name(name: str) -> str:
    """Normalize a yoga name for fuzzy matching across systems.

    Lowercases, strips whitespace, removes hyphens and common suffixes
    like 'yoga' so that e.g. 'Gaja Kesari Yoga' matches 'Gajakesari'.
    """
    n = name.lower().strip()
    # Remove common suffixes
    for suffix in (" yoga", "_yoga"):
        if n.endswith(suffix):
            n = n[: -len(suffix)]
    # Remove separators
    for ch in ("-", "_", " "):
        n = n.replace(ch, "")
    return n


def _get_pyjhora_yogas(jd, place):
    """Call PyJHora yoga detection and return parsed results.

    Returns:
        tuple: (yoga_names_set, count_found, total_possible, raw_dict)
            - yoga_names_set: set of normalized yoga name strings
            - count_found: int, number of yogas PyJHora found
            - total_possible: int, total yogas PyJHora checked
            - raw_dict: the original yoga_dict for debugging
    """
    from jhora.horoscope.chart import yoga

    yoga_dict, count_found, total_possible = yoga.get_yoga_details(
        jd, place, divisional_chart_factor=1, language="en"
    )

    # yoga_dict values are lists like ['D1', 'Yoga Name', 'condition', 'result']
    # Extract the yoga name (index 1) from each entry
    pj_yoga_names: set[str] = set()
    for key, info in yoga_dict.items():
        if isinstance(info, (list, tuple)) and len(info) >= 2:
            raw_name = str(info[1])
            pj_yoga_names.add(_normalize_yoga_name(raw_name))

    return pj_yoga_names, count_found, total_possible, yoga_dict


def _get_vc_yogas(chart):
    """Run vedic-calc yoga detection and return parsed results.

    Returns:
        tuple: (present_names_set, all_results)
            - present_names_set: set of normalized yoga names that are present
            - all_results: full list of YogaResult objects
    """
    all_yogas = detect_yogas(chart)
    present = [y for y in all_yogas if y.is_present]
    vc_names = {_normalize_yoga_name(y.name) for y in present}
    return vc_names, all_yogas


# Well-known yogas we specifically look for in both systems.
# Keys are normalized names; values are human-readable labels.
WELL_KNOWN_YOGAS = {
    "gajakesari": "Gajakesari Yoga",
    "budhaditya": "Budhaditya Yoga",
    "ruchaka": "Ruchaka Yoga",
    "bhadra": "Bhadra Yoga",
    "hamsa": "Hamsa Yoga",
    "malavya": "Malavya Yoga",
    "shasha": "Shasha Yoga",
    "sunapha": "Sunapha Yoga",
    "anapha": "Anapha Yoga",
    "durudhara": "Durudhara Yoga",
    "kemadruma": "Kemadruma Yoga",
    "veshi": "Veshi Yoga",
    "voshi": "Voshi Yoga",
    "ubhayachari": "Ubhayachari Yoga",
    "chandramangal": "Chandra-Mangal Yoga",
    "amala": "Amala Yoga",
    "shakata": "Shakata Yoga",
    "saraswati": "Saraswati Yoga",
    "lakshmi": "Lakshmi Yoga",
}

# Alternative normalized names PyJHora might use for the same yoga.
# Maps alternative → canonical normalized name.
PJ_NAME_ALIASES = {
    "gajakeshari": "gajakesari",
    "budhadithya": "budhaditya",
    "budhaaditya": "budhaditya",
    "chandramangala": "chandramangal",
    "sasa": "shasha",
    "sasaka": "shasha",
    "vosi": "voshi",
    "vasi": "veshi",
    "obhayachari": "ubhayachari",
    "obhayachary": "ubhayachari",
    "ubhayachary": "ubhayachari",
    "laxmi": "lakshmi",
    "sarasvati": "saraswati",
    "kemdrum": "kemadruma",
    "kemadrum": "kemadruma",
    "rajayoga": "raja",
    "raja": "raja",
}


def _resolve_alias(normalized_name: str) -> str:
    """Resolve a normalized yoga name through the alias table."""
    return PJ_NAME_ALIASES.get(normalized_name, normalized_name)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_yoga_count_comparison(ref, collector):
    """Compare total yoga counts between vedic-calc and PyJHora.

    This is a soft comparison — the two systems check different sets of yogas,
    so we only record the counts without asserting equality.
    """
    chart = ref.calculate()

    t0 = time.perf_counter()
    vc_names, vc_all = _get_vc_yogas(chart)
    vc_ms = (time.perf_counter() - t0) * 1000

    jd, place, _, _ = pj_setup(ref)
    t0 = time.perf_counter()
    pj_names, pj_count, pj_total, _ = _get_pyjhora_yogas(jd, place)
    pj_ms = (time.perf_counter() - t0) * 1000

    vc_present_count = len(vc_names)

    collector.add(ComparisonRecord(
        feature="yoga_count",
        chart_label=ref.label,
        vedic_calc_result=vc_present_count,
        pyjhora_result=pj_count,
        match=True,  # informational — no strict assertion on counts
        vc_time_ms=vc_ms,
        pj_time_ms=pj_ms,
        notes=(
            f"vc checked {len(vc_all)} yogas, {vc_present_count} present; "
            f"pj found {pj_count}/{pj_total}"
        ),
    ))


@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_common_yoga_overlap(ref, collector):
    """Find yogas detected by both systems and measure overlap.

    Normalizes names and resolves aliases to find the intersection.
    Records the overlap ratio as a comparison metric.
    """
    chart = ref.calculate()

    t0 = time.perf_counter()
    vc_names, _ = _get_vc_yogas(chart)
    vc_ms = (time.perf_counter() - t0) * 1000

    jd, place, _, _ = pj_setup(ref)
    t0 = time.perf_counter()
    pj_names_raw, _, _, _ = _get_pyjhora_yogas(jd, place)
    pj_ms = (time.perf_counter() - t0) * 1000

    # Resolve aliases in PyJHora names
    pj_names = {_resolve_alias(n) for n in pj_names_raw}

    # Also resolve aliases in vc names (should be identity, but for safety)
    vc_resolved = {_resolve_alias(n) for n in vc_names}

    common = vc_resolved & pj_names
    vc_only = vc_resolved - pj_names
    pj_only = pj_names - vc_resolved

    union = vc_resolved | pj_names
    overlap_pct = (len(common) / len(union) * 100) if union else 0.0

    collector.add(ComparisonRecord(
        feature="yoga_overlap",
        chart_label=ref.label,
        vedic_calc_result=sorted(vc_resolved),
        pyjhora_result=sorted(pj_names),
        match=len(common) > 0,
        vc_time_ms=vc_ms,
        pj_time_ms=pj_ms,
        notes=(
            f"common={sorted(common)}; "
            f"vc_only={sorted(vc_only)}; "
            f"pj_only={sorted(pj_only)}; "
            f"overlap={overlap_pct:.0f}%"
        ),
    ))


@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_well_known_yogas(ref, collector):
    """Compare presence/absence of well-known yogas between both systems.

    For each yoga in WELL_KNOWN_YOGAS, check if both systems agree on
    whether it is present. Records each yoga as a separate comparison point.
    """
    chart = ref.calculate()

    t0 = time.perf_counter()
    vc_names, _ = _get_vc_yogas(chart)
    vc_ms = (time.perf_counter() - t0) * 1000

    jd, place, _, _ = pj_setup(ref)
    t0 = time.perf_counter()
    pj_names_raw, _, _, _ = _get_pyjhora_yogas(jd, place)
    pj_ms = (time.perf_counter() - t0) * 1000

    # Resolve aliases
    pj_names = {_resolve_alias(n) for n in pj_names_raw}
    vc_resolved = {_resolve_alias(n) for n in vc_names}

    matches = 0
    mismatches = 0

    for norm_name, display_name in WELL_KNOWN_YOGAS.items():
        vc_present = norm_name in vc_resolved
        pj_present = norm_name in pj_names

        agreed = vc_present == pj_present

        if agreed:
            matches += 1
        else:
            mismatches += 1

        collector.add(ComparisonRecord(
            feature=f"yoga_wellknown_{norm_name}",
            chart_label=ref.label,
            vedic_calc_result=f"{display_name}: {'present' if vc_present else 'absent'}",
            pyjhora_result=f"{display_name}: {'present' if pj_present else 'absent'}",
            match=agreed,
            vc_time_ms=vc_ms,
            pj_time_ms=pj_ms,
            notes="" if agreed else f"DISAGREE on {display_name}",
        ))


@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_pancha_mahapurusha_yogas(ref, collector):
    """Compare Pancha Mahapurusha Yoga detection specifically.

    These five yogas (Ruchaka, Bhadra, Hamsa, Malavya, Shasha) are
    well-defined and should have high agreement between systems.
    """
    chart = ref.calculate()
    pmp_names = ["ruchaka", "bhadra", "hamsa", "malavya", "shasha"]

    t0 = time.perf_counter()
    vc_names, _ = _get_vc_yogas(chart)
    vc_ms = (time.perf_counter() - t0) * 1000

    jd, place, _, _ = pj_setup(ref)
    t0 = time.perf_counter()
    pj_names_raw, _, _, _ = _get_pyjhora_yogas(jd, place)
    pj_ms = (time.perf_counter() - t0) * 1000

    pj_names = {_resolve_alias(n) for n in pj_names_raw}
    vc_resolved = {_resolve_alias(n) for n in vc_names}

    for yoga_name in pmp_names:
        vc_present = yoga_name in vc_resolved
        pj_present = yoga_name in pj_names
        agreed = vc_present == pj_present

        collector.add(ComparisonRecord(
            feature="yoga_pancha_mahapurusha",
            chart_label=ref.label,
            vedic_calc_result=f"{yoga_name}: {'present' if vc_present else 'absent'}",
            pyjhora_result=f"{yoga_name}: {'present' if pj_present else 'absent'}",
            match=agreed,
            vc_time_ms=vc_ms,
            pj_time_ms=pj_ms,
            notes=f"{yoga_name.title()} Yoga" + ("" if agreed else " — DISAGREE"),
        ))


@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_lunar_yogas(ref, collector):
    """Compare lunar yoga detection (Sunapha, Anapha, Durudhara, Kemadruma).

    These yogas depend on planets adjacent to Moon and should align
    if both systems use the same adjacency definition (sign-based).
    """
    chart = ref.calculate()
    lunar_yogas = ["sunapha", "anapha", "durudhara", "kemadruma"]

    t0 = time.perf_counter()
    vc_names, _ = _get_vc_yogas(chart)
    vc_ms = (time.perf_counter() - t0) * 1000

    jd, place, _, _ = pj_setup(ref)
    t0 = time.perf_counter()
    pj_names_raw, _, _, _ = _get_pyjhora_yogas(jd, place)
    pj_ms = (time.perf_counter() - t0) * 1000

    pj_names = {_resolve_alias(n) for n in pj_names_raw}
    vc_resolved = {_resolve_alias(n) for n in vc_names}

    for yoga_name in lunar_yogas:
        vc_present = yoga_name in vc_resolved
        pj_present = yoga_name in pj_names
        agreed = vc_present == pj_present

        collector.add(ComparisonRecord(
            feature="yoga_lunar",
            chart_label=ref.label,
            vedic_calc_result=f"{yoga_name}: {'present' if vc_present else 'absent'}",
            pyjhora_result=f"{yoga_name}: {'present' if pj_present else 'absent'}",
            match=agreed,
            vc_time_ms=vc_ms,
            pj_time_ms=pj_ms,
            notes=f"{yoga_name.title()} Yoga" + ("" if agreed else " — DISAGREE"),
        ))


@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_solar_yogas(ref, collector):
    """Compare solar yoga detection (Veshi, Voshi, Ubhayachari).

    These yogas depend on planets adjacent to Sun and should have
    high agreement if both systems use sign-based adjacency.
    """
    chart = ref.calculate()
    solar_yogas = ["veshi", "voshi", "ubhayachari"]

    t0 = time.perf_counter()
    vc_names, _ = _get_vc_yogas(chart)
    vc_ms = (time.perf_counter() - t0) * 1000

    jd, place, _, _ = pj_setup(ref)
    t0 = time.perf_counter()
    pj_names_raw, _, _, _ = _get_pyjhora_yogas(jd, place)
    pj_ms = (time.perf_counter() - t0) * 1000

    pj_names = {_resolve_alias(n) for n in pj_names_raw}
    vc_resolved = {_resolve_alias(n) for n in vc_names}

    for yoga_name in solar_yogas:
        vc_present = yoga_name in vc_resolved
        pj_present = yoga_name in pj_names
        agreed = vc_present == pj_present

        collector.add(ComparisonRecord(
            feature="yoga_solar",
            chart_label=ref.label,
            vedic_calc_result=f"{yoga_name}: {'present' if vc_present else 'absent'}",
            pyjhora_result=f"{yoga_name}: {'present' if pj_present else 'absent'}",
            match=agreed,
            vc_time_ms=vc_ms,
            pj_time_ms=pj_ms,
            notes=f"{yoga_name.title()} Yoga" + ("" if agreed else " — DISAGREE"),
        ))


@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_gajakesari_detail(ref, collector):
    """Detailed Gajakesari Yoga comparison with diagnostic info.

    Gajakesari (Jupiter in kendra from Moon) is one of the most common
    and well-defined yogas. This test provides extra diagnostic info
    about Moon and Jupiter positions for debugging disagreements.
    """
    chart = ref.calculate()

    t0 = time.perf_counter()
    vc_all = detect_yogas(chart)
    vc_ms = (time.perf_counter() - t0) * 1000

    vc_gk = next((y for y in vc_all if _normalize_yoga_name(y.name) == "gajakesari"), None)

    jd, place, _, _ = pj_setup(ref)
    t0 = time.perf_counter()
    pj_names_raw, _, _, pj_dict = _get_pyjhora_yogas(jd, place)
    pj_ms = (time.perf_counter() - t0) * 1000

    pj_names = {_resolve_alias(n) for n in pj_names_raw}

    vc_present = vc_gk.is_present if vc_gk else False
    pj_present = "gajakesari" in pj_names

    # Get diagnostic positions
    from vedic_calc.core.constants import Planet
    moon_sign = chart.planets[Planet.MOON].sign
    jup_sign = chart.planets[Planet.JUPITER].sign
    distance = ((int(jup_sign) - int(moon_sign)) % 12) + 1

    agreed = vc_present == pj_present
    collector.add(ComparisonRecord(
        feature="yoga_gajakesari_detail",
        chart_label=ref.label,
        vedic_calc_result=f"present={vc_present}",
        pyjhora_result=f"present={pj_present}",
        match=agreed,
        vc_time_ms=vc_ms,
        pj_time_ms=pj_ms,
        notes=(
            f"Moon={moon_sign.name}, Jupiter={jup_sign.name}, "
            f"sign_distance={distance}"
            + ("" if agreed else " — DISAGREE")
        ),
    ))


@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_budhaditya_detail(ref, collector):
    """Detailed Budhaditya Yoga comparison with diagnostic info.

    Budhaditya (Sun-Mercury conjunction) is very common since Mercury
    never strays far from Sun. Provides position diagnostics.
    """
    chart = ref.calculate()

    t0 = time.perf_counter()
    vc_all = detect_yogas(chart)
    vc_ms = (time.perf_counter() - t0) * 1000

    vc_bd = next((y for y in vc_all if _normalize_yoga_name(y.name) == "budhaditya"), None)

    jd, place, _, _ = pj_setup(ref)
    t0 = time.perf_counter()
    pj_names_raw, _, _, _ = _get_pyjhora_yogas(jd, place)
    pj_ms = (time.perf_counter() - t0) * 1000

    pj_names = {_resolve_alias(n) for n in pj_names_raw}

    vc_present = vc_bd.is_present if vc_bd else False
    pj_present = "budhaditya" in pj_names

    from vedic_calc.core.constants import Planet
    sun_sign = chart.planets[Planet.SUN].sign
    mer_sign = chart.planets[Planet.MERCURY].sign

    agreed = vc_present == pj_present
    collector.add(ComparisonRecord(
        feature="yoga_budhaditya_detail",
        chart_label=ref.label,
        vedic_calc_result=f"present={vc_present}",
        pyjhora_result=f"present={pj_present}",
        match=agreed,
        vc_time_ms=vc_ms,
        pj_time_ms=pj_ms,
        notes=(
            f"Sun={sun_sign.name}, Mercury={mer_sign.name}, "
            f"same_sign={sun_sign == mer_sign}"
            + ("" if agreed else " — DISAGREE")
        ),
    ))
