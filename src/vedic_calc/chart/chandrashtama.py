"""Chandrashtama (Moon in 8th from natal Moon) calculator."""

from __future__ import annotations

from datetime import datetime

from vedic_calc.core.constants import Ayanamsa, Planet, Sign
from vedic_calc.core.ephemeris import _to_julian_day, get_planet_longitude, jd_to_datetime
from vedic_calc.core.types import ChandrashtamaResult, ChandrashtamaWindow


def _moon_sign_at(jd: float, ayanamsa: Ayanamsa) -> int:
    """Get Moon's sign number (1-12) at a given JD."""
    lon, _ = get_planet_longitude(jd, Planet.MOON, ayanamsa)
    return int(lon / 30.0) + 1


def calculate_chandrashtama(
    natal_moon_sign: Sign,
    start_date: datetime,
    end_date: datetime,
    latitude: float = 0.0,
    longitude: float = 0.0,
    timezone_offset: float = 5.5,
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI,
) -> ChandrashtamaResult:
    """Calculate all Chandrashtama windows in a date range.

    Chandrashtama = Moon transiting the 8th sign from natal Moon sign.
    This is considered inauspicious (~2.25 days every ~27 days).

    Args:
        natal_moon_sign: The natal Moon sign.
        start_date: Start of range to scan.
        end_date: End of range to scan.
        latitude: Location latitude (not used for Moon sign, kept for API consistency).
        longitude: Location longitude (not used).
        timezone_offset: UTC offset in hours.
        ayanamsa: Ayanamsa for calculations.

    Returns:
        ChandrashtamaResult with all windows.
    """
    moon_num = int(natal_moon_sign)
    # 8th sign from natal Moon (inclusive count)
    chandrashtama_sign_num = ((moon_num + 6) % 12) + 1
    chandrashtama_sign = Sign(chandrashtama_sign_num)

    tz = timezone_offset
    jd_start = _to_julian_day(start_date.year, start_date.month, start_date.day,
                              start_date.hour + start_date.minute / 60.0 - tz)
    jd_end = _to_julian_day(end_date.year, end_date.month, end_date.day,
                            end_date.hour + end_date.minute / 60.0 - tz)

    windows: list[ChandrashtamaWindow] = []

    # Moon moves ~13 deg/day. Scan every 0.25 days (6 hours) for sign changes.
    step = 0.25
    precision = 0.0005  # ~43 seconds

    jd = jd_start
    prev_sign = _moon_sign_at(jd, ayanamsa)
    in_target = prev_sign == chandrashtama_sign_num
    window_start_jd = jd if in_target else None

    while True:
        prev_jd = jd
        jd += step
        at_end = False
        if jd >= jd_end:
            jd = jd_end
            at_end = True

        sign = _moon_sign_at(jd, ayanamsa)

        if sign != prev_sign:
            # Bisect for exact transition
            lo, hi = prev_jd, jd
            while (hi - lo) > precision:
                mid = (lo + hi) / 2.0
                if _moon_sign_at(mid, ayanamsa) == prev_sign:
                    lo = mid
                else:
                    hi = mid
            transition_jd = hi

            if in_target:
                # Exiting Chandrashtama sign
                windows.append(ChandrashtamaWindow(
                    start=jd_to_datetime(window_start_jd, tz),
                    end=jd_to_datetime(transition_jd, tz),
                    transit_sign=chandrashtama_sign,
                ))
                in_target = False

            if sign == chandrashtama_sign_num:
                # Entering Chandrashtama sign
                window_start_jd = transition_jd
                in_target = True

        prev_sign = sign

        if at_end:
            break

    # Close any open window at end of range
    if in_target and window_start_jd is not None:
        windows.append(ChandrashtamaWindow(
            start=jd_to_datetime(window_start_jd, tz),
            end=jd_to_datetime(jd_end, tz),
            transit_sign=chandrashtama_sign,
        ))

    return ChandrashtamaResult(
        natal_moon_sign=natal_moon_sign,
        chandrashtama_sign=chandrashtama_sign,
        windows=windows,
    )
