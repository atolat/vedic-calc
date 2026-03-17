"""
Panchanga Transition Engine — finds exact times when panchanga elements change.

In Vedic astrology, a "day" runs from sunrise to the next sunrise. During that
window, the five panchanga elements (tithi, nakshatra, yoga, karana, vara) can
each change value one or more times. For example, a tithi lasts roughly 23–26
hours, so there is usually one tithi transition per day, but sometimes zero or
two.

This module scans the sunrise-to-sunrise window for ALL transitions across
tithi, nakshatra, yoga, and karana, then returns them sorted chronologically.
(Vara is omitted since it always changes exactly at sunrise.)

APPROACH:
    1. Sample each element every ~30 minutes (0.02083 JD)
    2. When the value changes between consecutive samples, use bisection
       to pinpoint the exact transition JD to ~0.08-second precision (1e-6 JD)
    3. Convert each transition JD to a local datetime

WHY 30-MINUTE SAMPLING?
    The fastest-changing element is karana (6° of Moon-Sun separation). The Moon
    moves ~0.55°/hr relative to the Sun, so a karana lasts ~10.9 hours minimum.
    A 30-minute step guarantees we never skip a transition.
"""

from __future__ import annotations

from datetime import datetime

from vedic_calc.core.constants import (
    Ayanamsa,
    KARANA_NAMES,
    NAKSHATRA_NAMES,
    NAKSHATRA_SPAN,
    Planet,
    TITHI_NAMES,
    YOGA_NAMES,
)
from vedic_calc.core.ephemeris import (
    _to_julian_day,
    get_planet_longitude,
    get_sunrise_sunset,
    jd_to_datetime,
)
from vedic_calc.core.types import PanchangaTransitions, TransitionMoment


# ---------------------------------------------------------------------------
# Element value functions — return the element index at a given JD
# ---------------------------------------------------------------------------

def _tithi_at(jd: float, ayanamsa: Ayanamsa) -> int:
    moon, _ = get_planet_longitude(jd, Planet.MOON, ayanamsa)
    sun, _ = get_planet_longitude(jd, Planet.SUN, ayanamsa)
    return int(((moon - sun) % 360) / 12) + 1


def _nakshatra_at(jd: float, ayanamsa: Ayanamsa) -> int:
    moon, _ = get_planet_longitude(jd, Planet.MOON, ayanamsa)
    return min(int(moon / NAKSHATRA_SPAN) + 1, 27)


def _yoga_at(jd: float, ayanamsa: Ayanamsa) -> int:
    moon, _ = get_planet_longitude(jd, Planet.MOON, ayanamsa)
    sun, _ = get_planet_longitude(jd, Planet.SUN, ayanamsa)
    return min(int(((moon + sun) % 360) / NAKSHATRA_SPAN) + 1, 27)


def _karana_at(jd: float, ayanamsa: Ayanamsa) -> int:
    moon, _ = get_planet_longitude(jd, Planet.MOON, ayanamsa)
    sun, _ = get_planet_longitude(jd, Planet.SUN, ayanamsa)
    return min(int(((moon - sun) % 360) / 6) + 1, 60)


# ---------------------------------------------------------------------------
# Name lookup tables (element name → names dict)
# ---------------------------------------------------------------------------

_ELEMENT_CONFIG: dict[str, tuple] = {
    # element_name: (value_func, names_dict)
    "tithi":     (_tithi_at,     TITHI_NAMES),
    "nakshatra": (_nakshatra_at, NAKSHATRA_NAMES),
    "yoga":      (_yoga_at,      YOGA_NAMES),
    "karana":    (_karana_at,     KARANA_NAMES),
}


# ---------------------------------------------------------------------------
# Bisection helper
# ---------------------------------------------------------------------------

def _bisect_transition(
    value_func,
    jd_lo: float,
    jd_hi: float,
    val_lo: int,
    ayanamsa: Ayanamsa,
    precision: float = 1e-6,
) -> float:
    """Bisect to find the exact JD where value_func changes from val_lo.

    Precondition: value_func(jd_lo) == val_lo and value_func(jd_hi) != val_lo.
    Returns the JD of the first moment with the new value (within *precision*).
    """
    while (jd_hi - jd_lo) > precision:
        mid = (jd_lo + jd_hi) / 2.0
        if value_func(mid, ayanamsa) == val_lo:
            jd_lo = mid
        else:
            jd_hi = mid
    return jd_hi


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_panchanga_transitions(
    year: int,
    month: int,
    day: int,
    latitude: float,
    longitude: float,
    timezone_offset: float = 0.0,
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI,
) -> PanchangaTransitions:
    """Find all panchanga element transitions during a Vedic day.

    A Vedic day runs from sunrise on the given date to sunrise the next day.
    This function scans that window and returns every moment when a tithi,
    nakshatra, yoga, or karana changes value, sorted chronologically.

    Args:
        year: Calendar year.
        month: Month (1-12).
        day: Day (1-31).
        latitude: Geographic latitude (north positive).
        longitude: Geographic longitude (east positive).
        timezone_offset: UTC offset in hours (e.g., 5.5 for IST).
        ayanamsa: Ayanamsa system. Defaults to Lahiri.

    Returns:
        PanchangaTransitions with sorted list of TransitionMoment objects.

    Example:
        >>> t = calculate_panchanga_transitions(2026, 3, 8, 19.076, 72.878, 5.5)
        >>> isinstance(t.transitions, list)
        True
    """
    # ── Step 1: Compute sunrise today and next sunrise ──────────────────
    ut_hour = 0.0 - timezone_offset
    jd_midnight_today = _to_julian_day(year, month, day, ut_hour)
    jd_midnight_tomorrow = jd_midnight_today + 1.0

    sunrise_jd, _ = get_sunrise_sunset(jd_midnight_today, latitude, longitude)
    next_sunrise_jd, _ = get_sunrise_sunset(jd_midnight_tomorrow, latitude, longitude)

    sunrise_dt = jd_to_datetime(sunrise_jd, timezone_offset)
    next_sunrise_dt = jd_to_datetime(next_sunrise_jd, timezone_offset)

    # ── Step 2: Scan each element for transitions ───────────────────────
    step = 0.02083  # ~30 minutes in JD
    transitions: list[TransitionMoment] = []

    for element_name, (value_func, names_dict) in _ELEMENT_CONFIG.items():
        jd = sunrise_jd
        prev_val = value_func(jd, ayanamsa)

        while jd < next_sunrise_jd:
            next_jd = min(jd + step, next_sunrise_jd)
            curr_val = value_func(next_jd, ayanamsa)

            if curr_val != prev_val:
                # Bisect to find the exact transition moment
                exact_jd = _bisect_transition(
                    value_func, jd, next_jd, prev_val, ayanamsa,
                )
                transition_dt = jd_to_datetime(exact_jd, timezone_offset)

                transitions.append(
                    TransitionMoment(
                        element=element_name,
                        from_value=prev_val,
                        to_value=curr_val,
                        from_name=names_dict[prev_val],
                        to_name=names_dict[curr_val],
                        transition_time=transition_dt,
                    )
                )
                prev_val = curr_val

            jd = next_jd

    # ── Step 3: Sort all transitions chronologically ────────────────────
    transitions.sort(key=lambda t: t.transition_time)

    return PanchangaTransitions(
        date=datetime(year, month, day),
        sunrise=sunrise_dt,
        next_sunrise=next_sunrise_dt,
        transitions=transitions,
    )
