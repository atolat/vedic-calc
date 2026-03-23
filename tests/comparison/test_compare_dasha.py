"""Comparison tests: vedic-calc dashas vs PyJHora.

Compares the SEQUENCE of Mahadasha lords between vedic-calc and PyJHora
for Vimsottari, Yogini, and Ashtottari dasha systems.
"""

import time

import pytest

from vedic_calc.core.constants import Planet
from vedic_calc.dasha.calculator import calculate_dasha
from vedic_calc.dasha.yogini import calculate_yogini_dasha
from vedic_calc.dasha.ashtottari import calculate_ashtottari_dasha

from .conftest import (
    REFERENCE_CHARTS,
    ComparisonRecord,
    PJ_DASHA_LORD_TO_VC,
    pj_setup,
)

jhora = pytest.importorskip("jhora", reason="PyJHora not installed")


def _extract_maha_lord_sequence(pj_entries: list) -> list[int]:
    """Extract the unique mahadasha lord sequence from PyJHora output.

    PyJHora returns a flat list of [lord, sub_lord, date_str, ...] entries.
    The mahadasha lord is the first element of each sub-list.  We extract
    the unique lords in the order they first appear.
    """
    seen = set()
    sequence = []
    for entry in pj_entries:
        lord = entry[0]
        if lord not in seen:
            seen.add(lord)
            sequence.append(lord)
    return sequence


def _vc_maha_sequence(periods: list) -> list[int]:
    """Extract the mahadasha planet sequence from vedic-calc output.

    Returns list of Planet enum values for mahadasha-level periods.
    """
    return [
        p.lord.value
        for p in periods
        if p.level == "mahadasha"
    ]


# ─── Vimsottari ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_vimsottari_sequence_matches_pyjhora(ref, collector):
    """Compare Vimsottari mahadasha lord sequence with PyJHora."""
    from jhora.horoscope.dhasa.graha import vimsottari

    # vedic-calc
    vc_chart = ref.calculate()
    vc_start = time.perf_counter()
    vc_periods = calculate_dasha(vc_chart, levels=1)
    vc_time = (time.perf_counter() - vc_start) * 1000

    vc_sequence = _vc_maha_sequence(vc_periods)

    # PyJHora
    jd, place, dob, tob = pj_setup(ref)
    pj_start = time.perf_counter()
    pj_result = vimsottari.get_vimsottari_dhasa_bhukthi(jd, place)
    pj_time = (time.perf_counter() - pj_start) * 1000

    # pj_result is (balance_tuple, entries_list)
    _balance, pj_entries = pj_result
    pj_lord_ids = _extract_maha_lord_sequence(pj_entries)

    # Map PyJHora sequential planet IDs to vedic-calc Planet values
    pj_sequence = [PJ_DASHA_LORD_TO_VC[pid] for pid in pj_lord_ids]

    match = vc_sequence == pj_sequence

    collector.add(ComparisonRecord(
        feature="Vimsottari Dasha Sequence",
        chart_label=ref.label,
        vedic_calc_result=[Planet(v).name for v in vc_sequence],
        pyjhora_result=[Planet(v).name for v in pj_sequence],
        match=match,
        vc_time_ms=vc_time,
        pj_time_ms=pj_time,
        notes="" if match else (
            f"vc={[Planet(v).name for v in vc_sequence]} "
            f"pj={[Planet(v).name for v in pj_sequence]}"
        ),
    ))

    assert match, (
        f"Vimsottari sequence mismatch for {ref.label}:\n"
        f"  vedic-calc: {[Planet(v).name for v in vc_sequence]}\n"
        f"  PyJHora:    {[Planet(v).name for v in pj_sequence]}"
    )


@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_vimsottari_balance_matches_pyjhora(ref, collector):
    """Compare Vimsottari dasha balance at birth with PyJHora.

    The balance is the remaining duration (years) of the first mahadasha.
    We allow a tolerance of 0.05 years (~18 days) to account for minor
    algorithmic differences.
    """
    from jhora.horoscope.dhasa.graha import vimsottari

    TOLERANCE_YEARS = 0.05

    # vedic-calc: first mahadasha duration is the balance
    vc_chart = ref.calculate()
    vc_start = time.perf_counter()
    vc_periods = calculate_dasha(vc_chart, levels=1)
    vc_time = (time.perf_counter() - vc_start) * 1000

    vc_balance = vc_periods[0].duration_years

    # PyJHora
    jd, place, dob, tob = pj_setup(ref)
    pj_start = time.perf_counter()
    pj_result = vimsottari.get_vimsottari_dhasa_bhukthi(jd, place)
    pj_time = (time.perf_counter() - pj_start) * 1000

    balance_tuple, _entries = pj_result
    # balance_tuple is (years, months, days) of remaining dasha
    pj_balance = balance_tuple[0] + balance_tuple[1] / 12.0 + balance_tuple[2] / 365.25

    diff = abs(vc_balance - pj_balance)
    match = diff <= TOLERANCE_YEARS

    collector.add(ComparisonRecord(
        feature="Vimsottari Dasha Balance",
        chart_label=ref.label,
        vedic_calc_result=round(vc_balance, 4),
        pyjhora_result=round(pj_balance, 4),
        match=match,
        vc_time_ms=vc_time,
        pj_time_ms=pj_time,
        tolerance=TOLERANCE_YEARS,
        notes=f"diff={diff:.4f} years" if not match else "",
    ))

    assert match, (
        f"Vimsottari balance mismatch for {ref.label}: "
        f"vc={vc_balance:.4f}, pj={pj_balance:.4f}, diff={diff:.4f} years "
        f"(tolerance={TOLERANCE_YEARS})"
    )


# ─── Yogini ───────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_yogini_sequence_matches_pyjhora(ref, collector):
    """Compare Yogini mahadasha lord sequence with PyJHora."""
    from jhora.horoscope.dhasa.graha import yogini

    # vedic-calc
    vc_chart = ref.calculate()
    vc_start = time.perf_counter()
    vc_periods = calculate_yogini_dasha(vc_chart, levels=1)
    vc_time = (time.perf_counter() - vc_start) * 1000

    # Yogini dasha repeats in 36-year cycles; only compare the first cycle (8 periods)
    vc_sequence = _vc_maha_sequence(vc_periods)[:8]

    # PyJHora
    jd, place, dob, tob = pj_setup(ref)
    pj_start = time.perf_counter()
    pj_result = yogini.get_dhasa_bhukthi(dob, tob, place)
    pj_time = (time.perf_counter() - pj_start) * 1000

    # Yogini returns a flat list (no balance), unlike Vimsottari
    pj_entries = pj_result
    pj_lord_ids = _extract_maha_lord_sequence(pj_entries)

    # Map PyJHora sequential planet IDs to vedic-calc Planet values
    pj_sequence = [PJ_DASHA_LORD_TO_VC[pid] for pid in pj_lord_ids]

    match = vc_sequence == pj_sequence

    collector.add(ComparisonRecord(
        feature="Yogini Dasha Sequence",
        chart_label=ref.label,
        vedic_calc_result=[Planet(v).name for v in vc_sequence],
        pyjhora_result=[Planet(v).name for v in pj_sequence],
        match=match,
        vc_time_ms=vc_time,
        pj_time_ms=pj_time,
        notes="" if match else (
            f"vc={[Planet(v).name for v in vc_sequence]} "
            f"pj={[Planet(v).name for v in pj_sequence]}"
        ),
    ))

    assert match, (
        f"Yogini sequence mismatch for {ref.label}:\n"
        f"  vedic-calc: {[Planet(v).name for v in vc_sequence]}\n"
        f"  PyJHora:    {[Planet(v).name for v in pj_sequence]}"
    )


# ─── Ashtottari ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "ref", REFERENCE_CHARTS, ids=[c.label for c in REFERENCE_CHARTS]
)
def test_ashtottari_sequence_matches_pyjhora(ref, collector):
    """Compare Ashtottari mahadasha lord sequence with PyJHora."""
    from jhora.horoscope.dhasa.graha import ashtottari

    # vedic-calc
    vc_chart = ref.calculate()
    vc_start = time.perf_counter()
    vc_periods = calculate_ashtottari_dasha(vc_chart, levels=1)
    vc_time = (time.perf_counter() - vc_start) * 1000

    vc_sequence = _vc_maha_sequence(vc_periods)

    # PyJHora
    jd, place, dob, tob = pj_setup(ref)
    pj_start = time.perf_counter()
    pj_result = ashtottari.get_ashtottari_dhasa_bhukthi(jd, place)
    pj_time = (time.perf_counter() - pj_start) * 1000

    # Ashtottari returns a flat list (no balance), unlike Vimsottari
    pj_entries = pj_result
    pj_lord_ids = _extract_maha_lord_sequence(pj_entries)

    # Map PyJHora sequential planet IDs to vedic-calc Planet values
    pj_sequence = [PJ_DASHA_LORD_TO_VC[pid] for pid in pj_lord_ids]

    match = vc_sequence == pj_sequence

    collector.add(ComparisonRecord(
        feature="Ashtottari Dasha Sequence",
        chart_label=ref.label,
        vedic_calc_result=[Planet(v).name for v in vc_sequence],
        pyjhora_result=[Planet(v).name for v in pj_sequence],
        match=match,
        vc_time_ms=vc_time,
        pj_time_ms=pj_time,
        notes="" if match else (
            f"vc={[Planet(v).name for v in vc_sequence]} "
            f"pj={[Planet(v).name for v in pj_sequence]}"
        ),
    ))

    assert match, (
        f"Ashtottari sequence mismatch for {ref.label}:\n"
        f"  vedic-calc: {[Planet(v).name for v in vc_sequence]}\n"
        f"  PyJHora:    {[Planet(v).name for v in pj_sequence]}"
    )
