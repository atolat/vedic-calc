"""
Ashtottari Dasha (planetary period) calculator.

THE ASHTOTTARI DASHA SYSTEM:
    "Ashtottari" literally means "108" — the system divides a 108-year cycle
    into 8 major periods. Unlike Vimsottari (which uses all 9 planets),
    Ashtottari excludes Ketu:

        Sun=6, Moon=15, Mars=8, Mercury=17, Saturn=10,
        Jupiter=19, Rahu=12, Venus=21  (total = 108 years)

    Ashtottari is considered applicable when Rahu is in a kendra or trikona
    from the lagna lord, or when the birth occurs during daytime in Krishna
    Paksha (waning Moon) or nighttime in Shukla Paksha (waxing Moon).

HOW THE STARTING PLANET IS DETERMINED:
    The 27 nakshatras are divided into 8 uneven groups (some lords rule 4
    nakshatras, others rule 3), starting from Ardra (nakshatra 6):

        Sun:     Ardra(6)  – Ashlesha(9)        [4 nakshatras]
        Moon:    Magha(10) – UttaraPhalguni(12)  [3 nakshatras]
        Mars:    Hasta(13) – Vishakha(16)        [4 nakshatras]
        Mercury: Anuradha(17) – Moola(19)        [3 nakshatras]
        Saturn:  PurvaAshadha(20) – Shravana(22) [3 nakshatras]
        Jupiter: Dhanishta(23) – PurvaBhadra(25) [3 nakshatras]
        Rahu:    UttaraBhadra(26) – Bharani(2)   [4 nakshatras, wraps]
        Venus:   Krittika(3) – Mrigashira(5)     [3 nakshatras]

    The Moon's birth nakshatra determines the starting lord.  The elapsed
    fraction is computed over the lord's entire nakshatra range (not just
    the single nakshatra the Moon occupies).

SOURCE: BPHS Chapter 46, various Jyotish texts on conditional dasha systems.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from vedic_calc.core.constants import (
    Nakshatra,
    Planet,
    NAKSHATRA_SPAN,
)
from vedic_calc.core.types import BirthChart, DashaPeriod


# ---------------------------------------------------------------------------
# Ashtottari dasha constants
# ---------------------------------------------------------------------------

# Years assigned to each planet in the Ashtottari system.
ASHTOTTARI_YEARS: dict[Planet, int] = {
    Planet.SUN: 6,
    Planet.MOON: 15,
    Planet.MARS: 8,
    Planet.MERCURY: 17,
    Planet.SATURN: 10,
    Planet.JUPITER: 19,
    Planet.RAHU: 12,
    Planet.VENUS: 21,
}

# The fixed sequence of planets in Ashtottari dasha.
ASHTOTTARI_ORDER: list[Planet] = [
    Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
    Planet.SATURN, Planet.JUPITER, Planet.RAHU, Planet.VENUS,
]

# Total cycle length.
ASHTOTTARI_TOTAL_YEARS: int = 108

# Nakshatra ranges for each Ashtottari lord.
# Each entry is (start_nakshatra, end_nakshatra) — inclusive, 1-based.
# When end < start, the range wraps around past nakshatra 27 to 1.
_ASHTOTTARI_RANGES: list[tuple[Planet, int, int]] = [
    (Planet.SUN, 6, 9),
    (Planet.MOON, 10, 12),
    (Planet.MARS, 13, 16),
    (Planet.MERCURY, 17, 19),
    (Planet.SATURN, 20, 22),
    (Planet.JUPITER, 23, 25),
    (Planet.RAHU, 26, 2),       # wraps: 26, 27, 1, 2
    (Planet.VENUS, 3, 5),
]


# Number of days per year used for dasha date arithmetic.
_DAYS_PER_YEAR = 365.25


def _find_lord_and_elapsed(
    nakshatra_num: int,
    degree_in_nakshatra: float,
) -> tuple[Planet, float]:
    """Find the Ashtottari lord and elapsed fraction for a given nakshatra.

    The elapsed fraction is computed over the lord's entire multi-nakshatra
    range — not just the single nakshatra.

    Args:
        nakshatra_num: Nakshatra number (1-27).
        degree_in_nakshatra: Moon's degree within the nakshatra (0 to ~13.333).

    Returns:
        (lord, elapsed_fraction) where elapsed_fraction is in [0, 1).
    """
    for lord, start, end in _ASHTOTTARI_RANGES:
        # How many nakshatras in this range (handles wrapping)
        if end >= start:
            count = end - start + 1
            in_range = start <= nakshatra_num <= end
        else:
            # Wraps around: e.g. 26..2 means 26,27,1,2
            count = (27 - start + 1) + end
            in_range = nakshatra_num >= start or nakshatra_num <= end

        if in_range:
            # How many whole nakshatras before the current one in this range
            if end >= start:
                offset_naks = nakshatra_num - start
            else:
                if nakshatra_num >= start:
                    offset_naks = nakshatra_num - start
                else:
                    offset_naks = (27 - start) + nakshatra_num

            # Total span in degrees for this lord's range
            total_span = count * NAKSHATRA_SPAN
            # Degrees elapsed = whole nakshatras before + partial current
            degrees_elapsed = offset_naks * NAKSHATRA_SPAN + degree_in_nakshatra
            elapsed_fraction = degrees_elapsed / total_span

            return lord, elapsed_fraction

    # Should never reach here for valid nakshatras 1-27
    raise ValueError(f"Nakshatra {nakshatra_num} not found in Ashtottari ranges")


def _get_dasha_sequence(starting_lord: Planet) -> list[Planet]:
    """Rotate the Ashtottari planet order to start from the given planet.

    Args:
        starting_lord: The planet to start the sequence from.

    Returns:
        List of 8 planets in Ashtottari order, starting from starting_lord.
    """
    idx = ASHTOTTARI_ORDER.index(starting_lord)
    return ASHTOTTARI_ORDER[idx:] + ASHTOTTARI_ORDER[:idx]


def _sub_period_sequence(parent_lord: Planet) -> list[Planet]:
    """Get the sub-period planet sequence for a given parent period lord.

    Sub-periods (antardashas) within a mahadasha start from the mahadasha
    lord itself, then follow the Ashtottari order.

    Args:
        parent_lord: The ruling planet of the parent period.

    Returns:
        List of 8 planets starting from parent_lord.
    """
    return _get_dasha_sequence(parent_lord)


def calculate_ashtottari_dasha(
    chart: BirthChart,
    levels: int = 2,
) -> list[DashaPeriod]:
    """Calculate Ashtottari dasha periods from a birth chart.

    CALCULATION STEPS:
        1. Get Moon's nakshatra info from the birth chart
        2. Look up the starting lord from Ashtottari nakshatra ranges
        3. Calculate elapsed fraction over the lord's full nakshatra span
        4. Generate the 8 mahadasha periods (108 years total)
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
        >>> periods = calculate_ashtottari_dasha(chart, levels=1)
        >>> len(periods)
        8
        >>> abs(sum(p.duration_years for p in periods) - 108.0) < 0.001
        True
    """
    # --- Step 1: Get Moon's nakshatra position ---
    moon = chart.planets[Planet.MOON]
    nak_info = moon.nakshatra_info

    # --- Step 2 & 3: Determine starting lord and elapsed fraction ---
    starting_lord, elapsed_fraction = _find_lord_and_elapsed(
        int(nak_info.nakshatra),
        nak_info.degree_in_nakshatra,
    )
    remaining_fraction = 1.0 - elapsed_fraction

    # --- Step 4: Generate planet sequence ---
    sequence = _get_dasha_sequence(starting_lord)

    # --- Step 5: Generate mahadasha periods ---
    periods: list[DashaPeriod] = []
    current_start = chart.birth_datetime

    for i, lord in enumerate(sequence):
        full_years = ASHTOTTARI_YEARS[lord]

        if i == 0:
            # First mahadasha: only the remaining portion is left
            duration_years = full_years * remaining_fraction
        else:
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

        # --- Step 6: Generate antardashas (if requested) ---
        if levels >= 2:
            antar_start = current_start
            antar_sequence = _sub_period_sequence(lord)

            for antar_lord in antar_sequence:
                # Antardasha duration = mahadasha_duration *
                #                       (antar_lord_years / 108)
                antar_years = duration_years * (
                    ASHTOTTARI_YEARS[antar_lord] / ASHTOTTARI_TOTAL_YEARS
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

                antar_start = antar_end

        current_start = end

    return periods
