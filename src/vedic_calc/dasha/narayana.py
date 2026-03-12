"""
Narayana Dasha (Jaimini sign-based dasha) calculator.

THE NARAYANA DASHA SYSTEM:
    Unlike Vimsottari and other nakshatra-based dashas, Narayana Dasha is a
    SIGN-BASED system from the Jaimini school of Vedic astrology. Each period
    is ruled by a zodiac sign rather than a planet.

    Key differences from Vimsottari:
    - 12 periods (one per sign) instead of 9
    - Duration varies based on the sign lord's position in the chart
    - Direction of sign progression depends on whether the lagna is odd/even
    - Much shorter total cycle (variable, typically 60-144 years)

HOW IT WORKS:
    1. Start from the lagna (ascendant) sign
    2. If lagna is an odd sign (Aries, Gemini, Leo, Libra, Sagittarius,
       Aquarius), signs progress forward. If even, signs progress backward.
    3. Duration of each sign's dasha = count from the sign to its lord's
       position (in the chart). If the lord is in its own sign, duration = 12.

    This is a simplified implementation. The full Narayana Dasha has many
    conditional rules (e.g., exalted/debilitated lord adjustments, Rahu/Ketu
    exceptions, dual lordship rules for Scorpio/Aquarius).

SOURCE: Jaimini Sutras, Brihat Parashara Hora Shastra (Jaimini section).
"""

from __future__ import annotations

from datetime import timedelta

from vedic_calc.core.constants import (
    Planet,
    Sign,
    SIGN_LORDS,
)
from vedic_calc.core.types import BirthChart, DashaPeriod


# Number of days per year used for dasha date arithmetic.
_DAYS_PER_YEAR = 365.25

# Odd signs progress forward; even signs progress backward.
_ODD_SIGNS = {
    Sign.ARIES, Sign.GEMINI, Sign.LEO,
    Sign.LIBRA, Sign.SAGITTARIUS, Sign.AQUARIUS,
}


def _is_odd_sign(sign: Sign) -> bool:
    """Check whether a sign is odd (progresses forward in Narayana)."""
    return sign in _ODD_SIGNS


def _count_signs(from_sign: Sign, to_sign: Sign, forward: bool) -> int:
    """Count the number of signs from one sign to another (inclusive).

    Args:
        from_sign: The starting sign.
        to_sign: The target sign.
        forward: If True, count forward (1→2→3...); if False, backward.

    Returns:
        Count from 1 to 12. If lord is in its own sign, returns 12.
    """
    from_val = int(from_sign)
    to_val = int(to_sign)

    if from_val == to_val:
        return 12

    if forward:
        count = ((to_val - from_val) % 12)
    else:
        count = ((from_val - to_val) % 12)

    # count of 0 means same sign, which we already handled above
    return count if count != 0 else 12


def calculate_narayana_dasha(
    chart: BirthChart,
) -> list[DashaPeriod]:
    """Calculate Narayana Dasha periods from a birth chart.

    CALCULATION STEPS:
        1. Get the lagna (ascendant) sign
        2. Determine direction: odd sign = forward, even = backward
        3. For each of the 12 signs in sequence:
           a. Find the sign's lord and where it is placed in the chart
           b. Count from the sign to its lord's sign (inclusive, in direction)
           c. Duration in years = that count (12 if lord is in own sign)
        4. Create DashaPeriod with the sign lord as the `lord` field

    Args:
        chart: A calculated BirthChart (from calculate_chart()).

    Returns:
        List of 12 DashaPeriod objects (mahadasha level only), sorted
        chronologically. The `lord` field contains the sign lord for that
        period.

    Example:
        >>> chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
        >>> periods = calculate_narayana_dasha(chart)
        >>> len(periods)
        12
    """
    # --- Step 1: Get the lagna sign ---
    lagna_sign = chart.ascendant.sign
    lagna_val = int(lagna_sign)

    # --- Step 2: Determine direction ---
    forward = _is_odd_sign(lagna_sign)

    # --- Step 3: Generate 12 sign-based dasha periods ---
    periods: list[DashaPeriod] = []
    current_start = chart.birth_datetime

    for i in range(12):
        # Determine the sign for this period
        if forward:
            sign_val = ((lagna_val - 1 + i) % 12) + 1
        else:
            sign_val = ((lagna_val - 1 - i) % 12) + 1

        sign = Sign(sign_val)
        lord = SIGN_LORDS[sign]

        # Find where the lord is placed in the chart
        lord_sign = chart.planets[lord].sign

        # Count from this sign to the lord's sign
        count = _count_signs(sign, lord_sign, forward)
        duration_years = float(count)

        # Create the period
        duration_days = duration_years * _DAYS_PER_YEAR
        end = current_start + timedelta(days=duration_days)

        period = DashaPeriod(
            lord=lord,
            level="mahadasha",
            start=current_start,
            end=end,
            duration_years=round(duration_years, 6),
        )
        periods.append(period)

        current_start = end

    return periods
