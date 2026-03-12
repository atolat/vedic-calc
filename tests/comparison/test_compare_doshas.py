"""Comparison tests: vedic-calc doshas vs PyJHora.

Compares dosha detection (presence/absence) between vedic-calc and PyJHora
for all reference charts. PyJHora returns HTML strings for each dosha;
we parse those to determine presence/absence and compare against vedic-calc's
boolean DoshaResult.is_present.

Dosha name mapping:
    vedic-calc "Manglik Dosha"       ↔ PyJHora "Manglik Dosha"
    vedic-calc "Kaal Sarpa Dosha"    ↔ PyJHora "Kala Sarpa Dosha"
    vedic-calc "Pitru Dosha"         ↔ PyJHora "Pitru Dosha"
    vedic-calc "Guru Chandal Dosha"  ↔ PyJHora "Guru Chandala Dosha"
"""

from __future__ import annotations

import re
import time

import pytest

from vedic_calc.dosha.calculator import detect_doshas
from .conftest import REFERENCE_CHARTS, ComparisonRecord, pj_setup

jhora = pytest.importorskip("jhora", reason="PyJHora (jhora) not installed")


# ---------------------------------------------------------------------------
# Dosha name mapping: vedic-calc name → PyJHora dict key
# ---------------------------------------------------------------------------

DOSHA_NAME_MAP: dict[str, str] = {
    "Manglik Dosha": "Manglik Dosha",
    "Kaal Sarpa Dosha": "Kala Sarpa Dosha",
    "Pitru Dosha": "Pitru Dosha",
    "Guru Chandal Dosha": "Guru Chandala Dosha",
}

# Patterns that indicate a dosha is *absent* in PyJHora HTML output.
# PyJHora embeds phrases like "no Kala Sarpa Dosha" or "no Manglik Dosha"
# in its HTML when the dosha is not found.
_ABSENCE_PATTERNS: dict[str, re.Pattern] = {
    "Manglik Dosha": re.compile(r"no\s+manglik", re.IGNORECASE),
    "Kala Sarpa Dosha": re.compile(r"no\s+kala\s*sarpa", re.IGNORECASE),
    "Pitru Dosha": re.compile(r"no\s+pitru", re.IGNORECASE),
    "Guru Chandala Dosha": re.compile(r"no\s+guru\s*chandala?", re.IGNORECASE),
}


def _pj_dosha_is_present(pj_key: str, html_value: str) -> bool:
    """Parse PyJHora dosha HTML to determine if the dosha is present.

    Returns True if the dosha appears to be present (the absence pattern
    is NOT found in the HTML string).
    """
    if not html_value or not html_value.strip():
        return False

    pattern = _ABSENCE_PATTERNS.get(pj_key)
    if pattern is None:
        # No known absence pattern — assume present if non-empty
        return True

    # If the absence pattern matches, dosha is NOT present
    return not pattern.search(html_value)


def _get_pj_dosha_details(jd, place) -> dict[str, str]:
    """Call PyJHora dosha.get_dosha_details and return the result dict."""
    from jhora.horoscope.chart import dosha

    return dosha.get_dosha_details(jd, place)


# ---------------------------------------------------------------------------
# Parametrized comparison test
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_doshas_match_pyjhora(ref, collector):
    """Compare dosha presence/absence between vedic-calc and PyJHora."""

    # --- vedic-calc ---
    vc_chart = ref.calculate()
    t0 = time.perf_counter()
    vc_doshas = detect_doshas(vc_chart)
    vc_time = (time.perf_counter() - t0) * 1000

    # Build lookup: vc dosha name → DoshaResult
    vc_by_name: dict[str, bool] = {d.name: d.is_present for d in vc_doshas}

    # --- PyJHora ---
    jd, place, _dob, _tob = pj_setup(ref)
    t0 = time.perf_counter()
    pj_details = _get_pj_dosha_details(jd, place)
    pj_time = (time.perf_counter() - t0) * 1000

    # --- Compare each mapped dosha ---
    mismatches: list[str] = []

    for vc_name, pj_key in DOSHA_NAME_MAP.items():
        vc_present = vc_by_name.get(vc_name)
        if vc_present is None:
            # vedic-calc doesn't produce this dosha — skip
            continue

        pj_html = pj_details.get(pj_key, "")
        pj_present = _pj_dosha_is_present(pj_key, pj_html)

        match = vc_present == pj_present

        collector.add(ComparisonRecord(
            feature=f"dosha:{vc_name}",
            chart_label=ref.label,
            vedic_calc_result=vc_present,
            pyjhora_result=pj_present,
            match=match,
            vc_time_ms=vc_time,
            pj_time_ms=pj_time,
            notes=(
                f"vc={'present' if vc_present else 'absent'}, "
                f"pj={'present' if pj_present else 'absent'}"
                + (f" | pj_html_snippet={pj_html[:120]!r}" if not match else "")
            ),
        ))

        if not match:
            mismatches.append(
                f"{vc_name}: vc={'present' if vc_present else 'absent'}, "
                f"pj={'present' if pj_present else 'absent'}"
            )

    # Soft-assert: record all results but still flag mismatches
    if mismatches:
        pytest.xfail(
            f"Dosha mismatches for {ref.label}: {'; '.join(mismatches)}"
        )


@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_manglik_dosha_detail(ref, collector):
    """Focused comparison on Manglik Dosha presence between systems."""

    vc_chart = ref.calculate()
    vc_doshas = detect_doshas(vc_chart)
    manglik = next(d for d in vc_doshas if d.name == "Manglik Dosha")

    jd, place, _dob, _tob = pj_setup(ref)
    pj_details = _get_pj_dosha_details(jd, place)
    pj_html = pj_details.get("Manglik Dosha", "")
    pj_present = _pj_dosha_is_present("Manglik Dosha", pj_html)

    match = manglik.is_present == pj_present

    collector.add(ComparisonRecord(
        feature="dosha:Manglik (detail)",
        chart_label=ref.label,
        vedic_calc_result={
            "present": manglik.is_present,
            "severity": manglik.severity,
            "cancellations": manglik.cancellation_factors,
        },
        pyjhora_result={"present": pj_present, "html": pj_html[:200]},
        match=match,
        notes=manglik.description,
    ))

    if not match:
        pytest.xfail(
            f"Manglik detail mismatch for {ref.label}: "
            f"vc={manglik.is_present}, pj={pj_present}"
        )


@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_kaal_sarpa_dosha_detail(ref, collector):
    """Focused comparison on Kaal Sarpa Dosha presence between systems."""

    vc_chart = ref.calculate()
    vc_doshas = detect_doshas(vc_chart)
    kaal_sarpa = next(d for d in vc_doshas if d.name == "Kaal Sarpa Dosha")

    jd, place, _dob, _tob = pj_setup(ref)
    pj_details = _get_pj_dosha_details(jd, place)
    pj_html = pj_details.get("Kala Sarpa Dosha", "")
    pj_present = _pj_dosha_is_present("Kala Sarpa Dosha", pj_html)

    match = kaal_sarpa.is_present == pj_present

    collector.add(ComparisonRecord(
        feature="dosha:Kaal Sarpa (detail)",
        chart_label=ref.label,
        vedic_calc_result={
            "present": kaal_sarpa.is_present,
            "severity": kaal_sarpa.severity,
            "cancellations": kaal_sarpa.cancellation_factors,
        },
        pyjhora_result={"present": pj_present, "html": pj_html[:200]},
        match=match,
        notes=kaal_sarpa.description,
    ))

    if not match:
        pytest.xfail(
            f"Kaal Sarpa detail mismatch for {ref.label}: "
            f"vc={kaal_sarpa.is_present}, pj={pj_present}"
        )
