"""Bisection search utilities for finding astronomical transitions."""
from __future__ import annotations

from typing import Callable

from vedic_calc.core.constants import Ayanamsa, Planet
from vedic_calc.core.ephemeris import get_planet_longitude


def find_sign_entry(
    planet: Planet,
    target_sign_num: int,
    jd_start: float,
    jd_end: float,
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI,
    precision: float = 1e-6,
) -> float | None:
    """Find the Julian Day when a planet enters a target sign (1-12).

    Uses bisection search between jd_start and jd_end.
    Returns the JD of entry, or None if the planet doesn't enter that sign in the range.

    The target_sign_num is 1-12 (matching Sign enum values).
    """
    def _sign_at(jd: float) -> int:
        lon, _ = get_planet_longitude(jd, planet, ayanamsa)
        return int(lon / 30.0) + 1

    sign_start = _sign_at(jd_start)
    sign_end = _sign_at(jd_end)

    if sign_start == target_sign_num:
        # Already in target sign at start
        return jd_start

    if sign_end != target_sign_num and sign_start == sign_end:
        return None

    # For planets that may retrograde, we need to scan in steps first
    # then bisect between the step where the transition happens
    step = min((jd_end - jd_start) / 100.0, 1.0)  # Max 1 day steps

    jd = jd_start
    prev_jd = jd_start
    prev_sign = sign_start

    while jd <= jd_end:
        current_sign = _sign_at(jd)
        if current_sign == target_sign_num and prev_sign != target_sign_num:
            # Transition happened between prev_jd and jd — bisect
            lo, hi = prev_jd, jd
            while (hi - lo) > precision:
                mid = (lo + hi) / 2.0
                if _sign_at(mid) == target_sign_num:
                    hi = mid
                else:
                    lo = mid
            return hi
        prev_jd = jd
        prev_sign = current_sign
        jd += step

    return None


def find_element_transition(
    element_func: Callable[[float], int],
    jd_start: float,
    jd_end: float,
    precision: float = 1e-6,
) -> float | None:
    """Find the JD when an element (tithi, nakshatra, yoga, karana) changes value.

    element_func: a callable that takes a JD and returns an int index
    Returns the JD of the first transition, or None if no transition in range.
    """
    val_start = element_func(jd_start)
    val_end = element_func(jd_end)

    if val_start == val_end:
        return None

    # Bisect to find the exact transition point
    lo, hi = jd_start, jd_end
    while (hi - lo) > precision:
        mid = (lo + hi) / 2.0
        if element_func(mid) == val_start:
            lo = mid
        else:
            hi = mid
    return hi
