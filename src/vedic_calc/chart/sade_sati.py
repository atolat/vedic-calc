"""Sade Sati and related Saturn transit afflictions calculator.

Covers three types of Saturn-over-Moon transits:
  1. **Sade Sati** (7.5-year cycle): Saturn in 12th, 1st (same), or 2nd sign from Moon.
     - Rising phase: Saturn in the sign before Moon's sign (12th from Moon)
     - Peak phase: Saturn in the same sign as Moon
     - Setting phase: Saturn in the sign after Moon's sign (2nd from Moon)
  2. **Small Panoti** (Kantaka Shani): Saturn in the 4th sign from Moon.
  3. **Ashtama Shani**: Saturn in the 8th sign from Moon.

All three are sign-based (whole-sign transits), not degree-based.
Prokerala (and many traditional sources) group all three under the
"Sade Sati" umbrella, so `is_active` is True when ANY of these apply.
"""

from __future__ import annotations

from datetime import datetime

from vedic_calc.core.constants import Ayanamsa, Planet, Sign
from vedic_calc.core.ephemeris import _to_julian_day, get_planet_longitude, jd_to_datetime
from vedic_calc.core.types import BirthChart, SadeSatiPhase, SadeSatiResult


def _saturn_sign_at(jd: float, ayanamsa: Ayanamsa) -> int:
    """Get Saturn's sign number (1-12) at a given JD."""
    lon, _ = get_planet_longitude(jd, Planet.SATURN, ayanamsa)
    return int(lon / 30.0) + 1


def _get_saturn_transit_signs(moon_num: int) -> set[int]:
    """Return the set of signs where Saturn causes affliction relative to the Moon.

    This includes:
      - 12th from Moon (Sade Sati rising)
      - 1st / same as Moon (Sade Sati peak)
      - 2nd from Moon (Sade Sati setting)
      - 4th from Moon (Small Panoti / Kantaka Shani)
      - 8th from Moon (Ashtama Shani)
    """
    sign_12th = ((moon_num - 2) % 12) + 1   # one sign before Moon
    sign_1st = moon_num                      # same sign as Moon
    sign_2nd = (moon_num % 12) + 1           # one sign after Moon
    sign_4th = ((moon_num + 2) % 12) + 1     # 4th from Moon
    sign_8th = ((moon_num + 6) % 12) + 1     # 8th from Moon
    return {sign_12th, sign_1st, sign_2nd, sign_4th, sign_8th}


def _scan_saturn_sign_periods(
    target_signs: set[int],
    jd_start: float,
    jd_end: float,
    ayanamsa: Ayanamsa,
    step_days: float = 5.0,
    precision: float = 0.001,  # ~86 seconds
) -> list[tuple[int, float, float]]:
    """Scan for all periods when Saturn is in any of the target signs.

    Returns list of (sign_num, entry_jd, exit_jd).
    Saturn moves ~0.034 deg/day, so 5-day steps are fine for catching transitions.
    """
    periods: list[tuple[int, float, float]] = []

    jd = jd_start
    prev_sign = _saturn_sign_at(jd, ayanamsa)
    in_target = prev_sign in target_signs
    period_start = jd if in_target else None
    current_sign = prev_sign

    while True:
        prev_jd = jd
        jd += step_days
        at_end = False
        if jd >= jd_end:
            jd = jd_end
            at_end = True

        sign = _saturn_sign_at(jd, ayanamsa)

        if sign != prev_sign:
            # Transition happened -- bisect for exact time
            lo, hi = prev_jd, jd
            while (hi - lo) > precision:
                mid = (lo + hi) / 2.0
                mid_sign = _saturn_sign_at(mid, ayanamsa)
                if mid_sign == prev_sign:
                    lo = mid
                else:
                    hi = mid

            transition_jd = hi

            if in_target:
                # Exiting target sign
                periods.append((current_sign, period_start, transition_jd))
                in_target = False

            if sign in target_signs:
                # Entering target sign
                period_start = transition_jd
                current_sign = sign
                in_target = True

        prev_sign = sign

        if at_end:
            break

    # Close any open period at the end of the range
    if in_target and period_start is not None:
        periods.append((current_sign, period_start, jd_end))

    return periods


def _sign_to_phase(sign_num: int, moon_sign: Sign) -> str:
    """Determine which Saturn transit phase a sign corresponds to.

    Phases:
      - "rising": Saturn in 12th from Moon (entering Sade Sati)
      - "peak": Saturn conjunct Moon's sign
      - "setting": Saturn in 2nd from Moon (exiting Sade Sati)
      - "small_panoti": Saturn in 4th from Moon (Kantaka Shani)
      - "ashtama_shani": Saturn in 8th from Moon
    """
    moon_num = int(moon_sign)
    # dist = how many signs ahead of Moon (1-based, so same sign = 1)
    dist = ((sign_num - moon_num) % 12) + 1
    if dist == 12:
        return "rising"
    elif dist == 1:
        return "peak"
    elif dist == 2:
        return "setting"
    elif dist == 4:
        return "small_panoti"
    elif dist == 8:
        return "ashtama_shani"
    return "unknown"


def calculate_sade_sati(
    chart: BirthChart,
    target_date: datetime | None = None,
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI,
) -> SadeSatiResult:
    """Check if Sade Sati (or related Saturn transit affliction) is active.

    Detects Sade Sati proper (12th/1st/2nd from Moon), Small Panoti (4th),
    and Ashtama Shani (8th). All are sign-based (whole-sign transits).

    Args:
        chart: Birth chart (used for Moon sign).
        target_date: Date to check (defaults to chart's birth datetime).
        ayanamsa: Ayanamsa for calculations.

    Returns:
        SadeSatiResult with active status and phase info.
    """
    if target_date is None:
        target_date = chart.birth_datetime

    moon_sign = chart.planets[Planet.MOON].sign
    moon_num = int(moon_sign)

    # All Saturn transit affliction signs (Sade Sati + Small Panoti + Ashtama Shani)
    target_signs = _get_saturn_transit_signs(moon_num)

    # Check Saturn's current sign
    tz = chart.timezone_offset
    jd = _to_julian_day(target_date.year, target_date.month, target_date.day,
                        target_date.hour + target_date.minute / 60.0 - tz)

    saturn_sign = _saturn_sign_at(jd, ayanamsa)
    is_active = saturn_sign in target_signs
    current_phase = _sign_to_phase(saturn_sign, moon_sign) if is_active else None

    return SadeSatiResult(
        is_active=is_active,
        current_phase=current_phase,
        moon_sign=moon_sign,
        phases=[],  # Phases populated by calculate_sade_sati_periods
    )


def calculate_sade_sati_periods(
    chart: BirthChart,
    start_date: datetime,
    end_date: datetime,
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI,
) -> SadeSatiResult:
    """Calculate all Saturn transit affliction periods in a date range.

    Includes Sade Sati (12th/1st/2nd from Moon), Small Panoti (4th),
    and Ashtama Shani (8th).

    Args:
        chart: Birth chart (used for Moon sign).
        start_date: Start of range.
        end_date: End of range.
        ayanamsa: Ayanamsa for calculations.

    Returns:
        SadeSatiResult with all phases in the range.
    """
    moon_sign = chart.planets[Planet.MOON].sign
    moon_num = int(moon_sign)

    target_signs = _get_saturn_transit_signs(moon_num)

    tz = chart.timezone_offset
    jd_start = _to_julian_day(start_date.year, start_date.month, start_date.day,
                              start_date.hour - tz)
    jd_end = _to_julian_day(end_date.year, end_date.month, end_date.day,
                            end_date.hour - tz)

    raw_periods = _scan_saturn_sign_periods(target_signs, jd_start, jd_end, ayanamsa)

    phases: list[SadeSatiPhase] = []
    for sign_num, entry_jd, exit_jd in raw_periods:
        phase_name = _sign_to_phase(sign_num, moon_sign)
        phases.append(SadeSatiPhase(
            phase=phase_name,
            sign=Sign(sign_num),
            start=jd_to_datetime(entry_jd, tz),
            end=jd_to_datetime(exit_jd, tz),
        ))

    # Check if currently active
    now_jd = _to_julian_day(start_date.year, start_date.month, start_date.day,
                            start_date.hour - tz)
    saturn_sign = _saturn_sign_at(now_jd, ayanamsa)
    is_active = saturn_sign in target_signs
    current_phase = _sign_to_phase(saturn_sign, moon_sign) if is_active else None

    return SadeSatiResult(
        is_active=is_active,
        current_phase=current_phase,
        moon_sign=moon_sign,
        phases=phases,
    )
