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
    Per BPHS: "Add 3 to the birth star (nakshatra) number, divide by 8.
    The remainder gives the ruling yogini."  Using 0-indexed yogini list,
    the formula simplifies to:

        yogini_index = (nakshatra_number + 2) % 8

    This gives the standard mapping:
        Ardra(6)→Mangala, Punarvasu(7)→Pingala, Pushya(8)→Dhanya, etc.

    The elapsed fraction within the first mahadasha is computed from the
    Moon's position within its current nakshatra, the same way as Vimsottari.

    Because the full cycle is only 36 years, it repeats multiple times
    within a lifetime.  We generate enough cycles to cover ~120 years.

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
                1 = mahadashas only (32 periods = 4 cycles of 8)
                2 = + antardashas (32 x 8 = 256 sub-periods)

    Returns:
        Flat list of DashaPeriod objects, sorted chronologically.
        Each period has a `level` field ("mahadasha" or "antardasha").
        Covers ~140 years (4 repeating 36-year cycles).

    Example:
        >>> chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
        >>> periods = calculate_yogini_dasha(chart, levels=1)
        >>> len(periods)
        32
        >>> mahas = [p for p in periods if p.level == "mahadasha"][:8]
        >>> abs(sum(p.duration_years for p in mahas) - 36.0) < 1.0
        True
    """
    # --- Step 1: Get Moon's nakshatra position ---
    moon = chart.planets[Planet.MOON]
    nak_info = moon.nakshatra_info

    # --- Step 2: Determine starting yogini ---
    # BPHS rule: add 3 to nakshatra number, divide by 8, remainder = yogini.
    # With 0-indexed yogini list this simplifies to (nak + 2) % 8.
    yogini_index = (int(nak_info.nakshatra) + 2) % 8

    # --- Step 3: Calculate elapsed fraction of the first dasha ---
    elapsed_fraction = nak_info.degree_in_nakshatra / NAKSHATRA_SPAN
    remaining_fraction = 1.0 - elapsed_fraction

    # --- Step 4: Generate yogini sequence ---
    sequence = _get_yogini_sequence(yogini_index)

    # --- Step 5: Generate mahadasha periods ---
    # The 36-year Yogini cycle repeats multiple times in a lifetime.
    # We generate enough cycles to cover ~120 years (ceil(120/36) = 4 cycles).
    _NUM_CYCLES = 4
    periods: list[DashaPeriod] = []
    current_start = chart.birth_datetime
    is_first_period = True  # Only the very first period is partial

    for _cycle in range(_NUM_CYCLES):
        for yogini_name in sequence:
            ruling_planet, full_years = YOGINI_DASHA_YEARS[yogini_name]

            if is_first_period:
                # First mahadasha: only the remaining portion is left
                duration_years = full_years * remaining_fraction
                is_first_period = False
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
