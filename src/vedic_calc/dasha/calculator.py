"""
Vimsottari Dasha (planetary period) calculator.

THE VIMSOTTARI DASHA SYSTEM:
    "Vimsottari" literally means "120" — the system divides a 120-year cycle
    into 9 major periods (mahadashas), each ruled by a planet:

        Ketu=7, Venus=20, Sun=6, Moon=10, Mars=7,
        Rahu=18, Jupiter=16, Saturn=19, Mercury=17

    These major periods are subdivided into sub-periods (antardashas) and
    sub-sub-periods (pratyantardashas), using the same proportional ratios.

    This is the most widely used timing system in Vedic astrology. When an
    astrologer says "you're running Jupiter dasha", they mean the current
    major period is ruled by Jupiter, which influences the types of events
    and themes you experience.

HOW THE STARTING DASHA IS DETERMINED:
    1. Look at the Moon's position at birth
    2. Determine which nakshatra the Moon is in
    3. The nakshatra's ruling planet = the starting mahadasha lord
    4. How far the Moon has traversed through the nakshatra determines
       how much of that first dasha has already elapsed at birth

    Example:
        Moon at 45° → Rohini nakshatra → lord is Moon → starts in Moon dasha
        Rohini spans 40.0°–53.333°, so Moon is 5° into its 13.333° span
        Elapsed fraction = 5.0 / 13.333 = 0.375 (37.5% done)
        Moon dasha = 10 years, so 10 × (1 - 0.375) = 6.25 years remain

SUB-PERIOD CALCULATION:
    Each mahadasha of planet M is divided into 9 antardashas. The antardasha
    sequence starts from M itself, then follows the Vimsottari order.

    Duration formula:
        antardasha_duration = mahadasha_duration × (antardasha_lord_years / 120)

    Example: Within Moon mahadasha (10 years):
        Moon-Moon = 10 × (10/120) = 0.833 years
        Moon-Mars = 10 × (7/120) = 0.583 years
        Moon-Rahu = 10 × (18/120) = 1.500 years
        ... (total of all antardashas = 10 years exactly)

    Pratyantardashas work the same way, one more level deep:
        pratyantar_duration = antar_duration × (pratyantar_lord_years / 120)

SOURCE: BPHS Chapter 46 (Vimsottari Dasha Adhyaya).
"""

from __future__ import annotations

from datetime import datetime, timedelta

from vedic_calc.core.constants import (
    Planet,
    NAKSHATRA_SPAN,
    VIMSOTTARI_ORDER,
    VIMSOTTARI_TOTAL_YEARS,
    VIMSOTTARI_YEARS,
)
from vedic_calc.core.types import BirthChart, DashaPeriod


# Number of days per year used for dasha date arithmetic.
# 365.25 accounts for leap years (standard astronomical convention).
_DAYS_PER_YEAR = 365.25


def _get_dasha_sequence(starting_lord: Planet) -> list[Planet]:
    """Rotate the Vimsottari planet order to start from the given planet.

    The Vimsottari sequence is always:
        Ketu → Venus → Sun → Moon → Mars → Rahu → Jupiter → Saturn → Mercury

    If the starting lord is Moon, the rotated sequence becomes:
        Moon → Mars → Rahu → Jupiter → Saturn → Mercury → Ketu → Venus → Sun

    Args:
        starting_lord: The planet to start the sequence from.

    Returns:
        List of 9 planets in Vimsottari order, starting from starting_lord.
    """
    idx = VIMSOTTARI_ORDER.index(starting_lord)
    return VIMSOTTARI_ORDER[idx:] + VIMSOTTARI_ORDER[:idx]


def _sub_period_sequence(parent_lord: Planet) -> list[Planet]:
    """Get the sub-period planet sequence for a given parent period lord.

    Sub-periods (antardashas) within a mahadasha start from the mahadasha
    lord itself, then follow the Vimsottari order. Same rule applies for
    pratyantardashas within antardashas.

    Example: Jupiter mahadasha → antardashas start from Jupiter:
        Jupiter → Saturn → Mercury → Ketu → Venus → Sun → Moon → Mars → Rahu

    Args:
        parent_lord: The ruling planet of the parent period.

    Returns:
        List of 9 planets starting from parent_lord.
    """
    return _get_dasha_sequence(parent_lord)


def calculate_dasha(
    chart: BirthChart,
    levels: int = 2,
) -> list[DashaPeriod]:
    """Calculate Vimsottari dasha periods from a birth chart.

    CALCULATION STEPS:
        1. Get Moon's nakshatra info from the birth chart
        2. Determine how much of the first mahadasha remains at birth
        3. Generate the 9 mahadasha periods (120 years total)
        4. Optionally subdivide each into antardashas and pratyantardashas

    Args:
        chart: A calculated BirthChart (from calculate_chart()).
        levels: How deep to calculate:
                1 = mahadashas only (9 periods)
                2 = + antardashas (9 × 9 = 81 sub-periods)
                3 = + pratyantardashas (9 × 9 × 9 = 729 sub-sub-periods)

    Returns:
        Flat list of DashaPeriod objects, sorted chronologically.
        Each period has a `level` field ("mahadasha", "antardasha",
        or "pratyantardasha") to distinguish the levels.

    Example:
        >>> chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
        >>> periods = calculate_dasha(chart, levels=1)
        >>> len(periods)
        9
        >>> sum(p.duration_years for p in periods)  # ≈ 120.0
        120.0...
    """
    # ─── Step 1: Get Moon's nakshatra position ───
    moon = chart.planets[Planet.MOON]
    nak_info = moon.nakshatra_info

    # ─── Step 2: Calculate elapsed fraction of the first dasha ───
    # How far the Moon has traveled through its birth nakshatra.
    # If the Moon is 5° into a 13.333° nakshatra, 37.5% has elapsed.
    elapsed_fraction = nak_info.degree_in_nakshatra / NAKSHATRA_SPAN
    remaining_fraction = 1.0 - elapsed_fraction

    # ─── Step 3: Determine the mahadasha sequence ───
    # Start from the Moon's nakshatra lord
    starting_lord = nak_info.lord
    sequence = _get_dasha_sequence(starting_lord)

    # ─── Step 4: Generate mahadasha periods ───
    periods: list[DashaPeriod] = []

    # The first mahadasha started BEFORE birth — go back by the elapsed portion.
    # Example: Moon in Swati (Rahu = 18 yrs), 37.5% elapsed → dasha started
    # 18 × 0.375 = 6.75 years before birth.
    first_full_years = VIMSOTTARI_YEARS[starting_lord]
    elapsed_days = first_full_years * elapsed_fraction * _DAYS_PER_YEAR
    current_start = chart.birth_datetime - timedelta(days=elapsed_days)

    for i, lord in enumerate(sequence):
        full_years = VIMSOTTARI_YEARS[lord]
        duration_years = float(full_years)

        duration_days = duration_years * _DAYS_PER_YEAR
        end = current_start + timedelta(days=duration_days)

        maha = DashaPeriod(
            lord=lord,
            level="mahadasha",
            start=current_start,
            end=end,
            duration_years=round(duration_years, 6),
        )
        periods.append(maha)

        # ─── Step 5: Generate antardashas (if requested) ───
        if levels >= 2:
            antar_start = current_start
            antar_sequence = _sub_period_sequence(lord)

            for antar_lord in antar_sequence:
                # Antardasha duration = mahadasha_duration × (lord_years / 120)
                antar_years = duration_years * (
                    VIMSOTTARI_YEARS[antar_lord] / VIMSOTTARI_TOTAL_YEARS
                )
                antar_days = antar_years * _DAYS_PER_YEAR
                antar_end = antar_start + timedelta(days=antar_days)

                antar = DashaPeriod(
                    lord=antar_lord,
                    level="antardasha",
                    start=antar_start,
                    end=antar_end,
                    duration_years=round(antar_years, 6),
                )
                periods.append(antar)

                # ─── Step 6: Generate pratyantardashas (if requested) ───
                if levels >= 3:
                    prat_start = antar_start
                    prat_sequence = _sub_period_sequence(antar_lord)

                    for prat_lord in prat_sequence:
                        prat_years = antar_years * (
                            VIMSOTTARI_YEARS[prat_lord] / VIMSOTTARI_TOTAL_YEARS
                        )
                        prat_days = prat_years * _DAYS_PER_YEAR
                        prat_end = prat_start + timedelta(days=prat_days)

                        periods.append(DashaPeriod(
                            lord=prat_lord,
                            level="pratyantardasha",
                            start=prat_start,
                            end=prat_end,
                            duration_years=round(prat_years, 6),
                        ))
                        prat_start = prat_end

                antar_start = antar_end

        current_start = end

    return periods


def get_current_dasha(
    chart: BirthChart,
    date: datetime | None = None,
    levels: int = 3,
) -> list[DashaPeriod]:
    """Get the active dasha periods for a specific date.

    Returns the mahadasha, antardasha, and pratyantardasha that are active
    on the given date. This is what astrologers mean when they say "you're
    currently running Jupiter-Saturn-Mercury dasha".

    Args:
        chart: A calculated BirthChart.
        date: The date to check (defaults to now).
        levels: How many levels to return (1-3).

    Returns:
        List of active DashaPeriod objects, one per level.
        [0] = active mahadasha, [1] = active antardasha, etc.
        Returns empty list if date is outside the 120-year dasha range.

    Example:
        >>> chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
        >>> current = get_current_dasha(chart, datetime(2026, 3, 8))
        >>> current[0].lord  # Active mahadasha
        <Planet.JUPITER: 4>
    """
    if date is None:
        date = datetime.now()

    all_periods = calculate_dasha(chart, levels=levels)

    active: list[DashaPeriod] = []
    level_names = ["mahadasha", "antardasha", "pratyantardasha"]

    for level_name in level_names[:levels]:
        for period in all_periods:
            if period.level == level_name and period.start <= date < period.end:
                active.append(period)
                break

    return active
