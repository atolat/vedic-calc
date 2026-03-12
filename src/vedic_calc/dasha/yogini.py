"""
Yogini Dasha (planetary period) calculator.

THE YOGINI DASHA SYSTEM:
    "Yogini" refers to 8 celestial feminine energies. This system divides a
    36-year cycle into 8 major periods, each ruled by a yogini associated
    with a planet:

        Mangala (Moon)=1, Pingala (Sun)=2, Dhanya (Jupiter)=3,
        Bhramari (Mars)=4, Bhadrika (Mercury)=5, Ulka (Saturn)=6,
        Siddha (Venus)=7, Sankata (Rahu)=8  (total = 36 years)

    Because the total cycle is only 36 years, it repeats ~3.3 times in a
    120-year lifespan. This makes it useful as a quick-reference timing
    tool alongside Vimsottari.

HOW THE STARTING YOGINI IS DETERMINED:
    The count begins from Punarvasu (nakshatra 7) with Pingala (Sun, the
    2nd yogini).  Each subsequent nakshatra advances one position in the
    cyclic 8-yogini list.  Because 27 nakshatras are distributed among 8
    yoginis, some yoginis govern 4 nakshatras and others govern 3.

    Formula:
        yogini_index = (1 + (nakshatra_number - 7) % 27) % 8

    The elapsed fraction within the first mahadasha is computed from the
    Moon's position within its current nakshatra, the same way as Vimsottari.

SOURCE: BPHS and various Jyotish classics.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from vedic_calc.core.constants import (
    Planet,
    NAKSHATRA_SPAN,
    YOGINI_DASHA_ORDER,
    YOGINI_DASHA_TOTAL_YEARS,
    YOGINI_DASHA_YEARS,
)
from vedic_calc.core.types import BirthChart, DashaPeriod


# Number of days per year used for dasha date arithmetic.
# 365.25 accounts for leap years (standard astronomical convention).
_DAYS_PER_YEAR = 365.25


def _get_yogini_sequence(starting_index: int) -> list[str]:
    """Rotate the Yogini order to start from the given index.

    Args:
        starting_index: Index (0-7) into YOGINI_DASHA_ORDER.

    Returns:
        List of 8 yogini names, starting from the given index.
    """
    return (
        YOGINI_DASHA_ORDER[starting_index:]
        + YOGINI_DASHA_ORDER[:starting_index]
    )


def _sub_period_sequence(parent_yogini_index: int) -> list[str]:
    """Get the sub-period yogini sequence for a given parent period.

    Sub-periods (antardashas) within a mahadasha start from the mahadasha's
    yogini itself, then follow the Yogini order.

    Args:
        parent_yogini_index: Index (0-7) of the parent yogini.

    Returns:
        List of 8 yogini names starting from the parent yogini.
    """
    return _get_yogini_sequence(parent_yogini_index)


def calculate_yogini_dasha(
    chart: BirthChart,
    levels: int = 2,
) -> list[DashaPeriod]:
    """Calculate Yogini dasha periods from a birth chart.

    CALCULATION STEPS:
        1. Get Moon's nakshatra info from the birth chart
        2. Determine the starting yogini: (1 + (nakshatra - 7) % 27) % 8
        3. Calculate elapsed fraction of the first mahadasha
        4. Generate the 8 mahadasha periods (36 years total)
        5. Optionally subdivide each into antardashas

    Args:
        chart: A calculated BirthChart (from calculate_chart()).
        levels: How deep to calculate:
                1 = mahadashas only (8 periods)
                2 = + antardashas (8 x 8 = 64 sub-periods)

    Returns:
        Flat list of DashaPeriod objects, sorted chronologically.
        Each period has a `level` field ("mahadasha" or "antardasha").

    Example:
        >>> chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
        >>> periods = calculate_yogini_dasha(chart, levels=1)
        >>> len(periods)
        8
        >>> abs(sum(p.duration_years for p in periods) - 36.0) < 0.001
        True
    """
    # --- Step 1: Get Moon's nakshatra position ---
    moon = chart.planets[Planet.MOON]
    nak_info = moon.nakshatra_info

    # --- Step 2: Determine starting yogini ---
    # Count starts from Punarvasu (nakshatra 7) with Pingala (Sun, index 1).
    # Each successive nakshatra advances one position in the 8-yogini cycle.
    yogini_index = (1 + (int(nak_info.nakshatra) - 7) % 27) % 8

    # --- Step 3: Calculate elapsed fraction of the first dasha ---
    elapsed_fraction = nak_info.degree_in_nakshatra / NAKSHATRA_SPAN
    remaining_fraction = 1.0 - elapsed_fraction

    # --- Step 4: Generate yogini sequence ---
    sequence = _get_yogini_sequence(yogini_index)

    # --- Step 5: Generate mahadasha periods ---
    periods: list[DashaPeriod] = []
    current_start = chart.birth_datetime

    for i, yogini_name in enumerate(sequence):
        ruling_planet, full_years = YOGINI_DASHA_YEARS[yogini_name]

        if i == 0:
            # First mahadasha: only the remaining portion is left
            duration_years = full_years * remaining_fraction
        else:
            duration_years = float(full_years)

        duration_days = duration_years * _DAYS_PER_YEAR
        end = current_start + timedelta(days=duration_days)

        maha = DashaPeriod(
            lord=ruling_planet,
            level="mahadasha",
            start=current_start,
            end=end,
            duration_years=round(duration_years, 6),
        )
        periods.append(maha)

        # --- Step 6: Generate antardashas (if requested) ---
        if levels >= 2:
            antar_start = current_start
            # Antardasha sequence starts from the mahadasha yogini
            parent_idx = YOGINI_DASHA_ORDER.index(yogini_name)
            antar_sequence = _sub_period_sequence(parent_idx)

            for antar_yogini_name in antar_sequence:
                antar_planet, antar_full_years = YOGINI_DASHA_YEARS[
                    antar_yogini_name
                ]
                # Antardasha duration = mahadasha_duration *
                #                       (antar_lord_years / total_years)
                antar_years = duration_years * (
                    antar_full_years / YOGINI_DASHA_TOTAL_YEARS
                )
                antar_days = antar_years * _DAYS_PER_YEAR
                antar_end = antar_start + timedelta(days=antar_days)

                antar = DashaPeriod(
                    lord=antar_planet,
                    level="antardasha",
                    start=antar_start,
                    end=antar_end,
                    duration_years=round(antar_years, 6),
                )
                periods.append(antar)

                antar_start = antar_end

        current_start = end

    return periods
