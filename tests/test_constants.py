"""Tests for constants and lookup tables."""

from vedic_calc.core.constants import (
    NAKSHATRA_LORDS,
    SIGN_LORDS,
    VIMSOTTARI_ORDER,
    VIMSOTTARI_YEARS,
    VIMSOTTARI_TOTAL_YEARS,
    Nakshatra,
    Planet,
    Sign,
)


def test_all_27_nakshatras_have_lords():
    """Every nakshatra should have an assigned ruling planet."""
    assert len(NAKSHATRA_LORDS) == 27
    for nak in Nakshatra:
        assert nak in NAKSHATRA_LORDS


def test_all_12_signs_have_lords():
    """Every sign should have a ruling planet."""
    assert len(SIGN_LORDS) == 12
    for sign in Sign:
        assert sign in SIGN_LORDS


def test_vimsottari_total_is_120():
    """The Vimsottari dasha cycle totals exactly 120 years."""
    assert sum(VIMSOTTARI_YEARS.values()) == VIMSOTTARI_TOTAL_YEARS == 120


def test_vimsottari_order_has_9_planets():
    """The dasha order should contain all 9 planets exactly once."""
    assert len(VIMSOTTARI_ORDER) == 9
    assert set(VIMSOTTARI_ORDER) == set(VIMSOTTARI_YEARS.keys())


def test_nakshatra_lord_cycle_repeats():
    """Nakshatra lords repeat every 9 nakshatras in the Vimsottari sequence."""
    for i in range(9):
        # Nakshatras 1, 10, 19 should all have the same lord (Ketu)
        # Nakshatras 2, 11, 20 should all have the same lord (Venus) etc.
        lord_1 = NAKSHATRA_LORDS[Nakshatra(i + 1)]
        lord_2 = NAKSHATRA_LORDS[Nakshatra(i + 10)]
        lord_3 = NAKSHATRA_LORDS[Nakshatra(i + 19)]
        assert lord_1 == lord_2 == lord_3
