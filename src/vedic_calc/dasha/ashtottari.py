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
    Each of the 27 nakshatras is assigned to one of the 8 Ashtottari planets.
    Starting from Ardra (nakshatra 6), the nakshatras cycle through the 8
    planets in groups, repeating every 8 nakshatras:
        Ardra(6)→Sun, Punarvasu(7)→Moon, Pushya(8)→Mars, ...

    The Moon's birth nakshatra determines the starting lord.

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

# Nakshatra-to-lord mapping for Ashtottari.
# Starting from Ardra (6), nakshatras cycle through the 8 planets.
# The pattern repeats every 8 nakshatras from Ardra onward, wrapping
# around through all 27 nakshatras.
_ASHTOTTARI_NAK_LORD: dict[Nakshatra, Planet] = {
    Nakshatra.ARDRA: Planet.SUN,
    Nakshatra.PUNARVASU: Planet.MOON,
    Nakshatra.PUSHYA: Planet.MARS,
    Nakshatra.ASHLESHA: Planet.MERCURY,
    Nakshatra.MAGHA: Planet.SATURN,
    Nakshatra.PURVA_PHALGUNI: Planet.JUPITER,
    Nakshatra.UTTARA_PHALGUNI: Planet.RAHU,
    Nakshatra.HASTA: Planet.VENUS,
    Nakshatra.CHITRA: Planet.SUN,
    Nakshatra.SWATI: Planet.MOON,
    Nakshatra.VISHAKHA: Planet.MARS,
    Nakshatra.ANURADHA: Planet.MERCURY,
    Nakshatra.JYESHTHA: Planet.SATURN,
    Nakshatra.MOOLA: Planet.JUPITER,
    Nakshatra.PURVA_ASHADHA: Planet.RAHU,
    Nakshatra.UTTARA_ASHADHA: Planet.VENUS,
    Nakshatra.SHRAVANA: Planet.SUN,
    Nakshatra.DHANISHTA: Planet.MOON,
    Nakshatra.SHATABHISHA: Planet.MARS,
    Nakshatra.PURVA_BHADRAPADA: Planet.MERCURY,
    Nakshatra.UTTARA_BHADRAPADA: Planet.SATURN,
    Nakshatra.REVATI: Planet.JUPITER,
    Nakshatra.ASHWINI: Planet.RAHU,
    Nakshatra.BHARANI: Planet.VENUS,
    Nakshatra.KRITTIKA: Planet.SUN,
    Nakshatra.ROHINI: Planet.MOON,
    Nakshatra.MRIGASHIRA: Planet.MARS,
}


# Number of days per year used for dasha date arithmetic.
_DAYS_PER_YEAR = 365.25


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
        2. Look up the starting lord from the Ashtottari nakshatra mapping
        3. Calculate elapsed fraction of the first mahadasha
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

    # --- Step 2: Determine starting lord from Ashtottari mapping ---
    starting_lord = _ASHTOTTARI_NAK_LORD[nak_info.nakshatra]

    # --- Step 3: Calculate elapsed fraction of the first dasha ---
    elapsed_fraction = nak_info.degree_in_nakshatra / NAKSHATRA_SPAN
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
