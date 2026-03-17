"""
Muhurta (electional astrology) calculations.

Muhurta is the branch of Vedic astrology concerned with selecting auspicious
times for important activities. This module computes daily time-quality
windows — periods that are favorable or unfavorable — based on the position
of the Sun (sunrise/sunset) and traditional slot-based formulas.

KEY CONCEPTS:
    - Rahu Kalam, Yamagandam, Gulika Kalam: Inauspicious time slots that
      divide the day (sunrise to sunset) into 8 equal parts. Which slot is
      inauspicious depends on the weekday.
    - Abhijit Muhurta: A universally auspicious ~48-minute window centered
      on local solar noon (midpoint of sunrise and sunset).
    - Choghadiya: 8 day periods + 8 night periods, each labeled with a
      quality (good/best/bad). Used for quick daily timing decisions.
    - Hora: Planetary hour lord at sunrise, determined by the weekday.

SOURCES:
    - Muhurta Chintamani (the classical text on electional astrology)
    - BPHS Ch. 96-99 (muhurta chapters)
    - Panchanga Siddhanta (traditional almanac computation methods)
    - Standard Indian panchanga practice as codified by DrikPanchang.com
"""

from __future__ import annotations

from datetime import datetime

from vedic_calc.core.constants import (
    CHOGHADIYA_DAY_SEQUENCE,
    CHOGHADIYA_NIGHT_SEQUENCE,
    CHOGHADIYA_TYPES,
    GULIKA_KALAM_SLOT,
    HORA_ORDER,
    RAHU_KALAM_SLOT,
    WEEKDAY_HORA_LORD,
    YAMAGANDAM_SLOT,
    Planet,
)
from vedic_calc.core.ephemeris import (
    _to_julian_day,
    get_sunrise_sunset,
    jd_to_datetime,
)
from vedic_calc.core.types import MuhurtaInfo


def _inauspicious_window(
    sunrise_jd: float,
    sunset_jd: float,
    slot: int,
    timezone_offset: float,
) -> tuple[datetime, datetime]:
    """Compute start/end datetimes for an inauspicious slot.

    The day (sunrise → sunset) is divided into 8 equal parts.
    The *slot* index (0-7) identifies which part is inauspicious.

    Args:
        sunrise_jd: Julian Day of sunrise.
        sunset_jd: Julian Day of sunset.
        slot: Slot index (0-7).
        timezone_offset: UTC offset in hours.

    Returns:
        (start_datetime, end_datetime) in local time.
    """
    day_duration = sunset_jd - sunrise_jd  # in days (fractional)
    slot_duration = day_duration / 8.0
    start_jd = sunrise_jd + slot * slot_duration
    end_jd = start_jd + slot_duration
    return (
        jd_to_datetime(start_jd, timezone_offset),
        jd_to_datetime(end_jd, timezone_offset),
    )


def _build_choghadiya(
    start_jd: float,
    end_jd: float,
    sequence: list[str],
    timezone_offset: float,
) -> list[tuple[str, datetime, datetime, str]]:
    """Build a list of choghadiya periods between two JD boundaries.

    Args:
        start_jd: Julian Day of the period start (sunrise or sunset).
        end_jd: Julian Day of the period end (sunset or next sunrise).
        sequence: List of 8 choghadiya names for this weekday.
        timezone_offset: UTC offset in hours.

    Returns:
        List of (name, start_dt, end_dt, quality) tuples.
    """
    duration = end_jd - start_jd
    slot_duration = duration / 8.0
    periods: list[tuple[str, datetime, datetime, str]] = []
    for i, name in enumerate(sequence):
        s_jd = start_jd + i * slot_duration
        e_jd = s_jd + slot_duration
        quality = CHOGHADIYA_TYPES[name]
        periods.append((
            name,
            jd_to_datetime(s_jd, timezone_offset),
            jd_to_datetime(e_jd, timezone_offset),
            quality,
        ))
    return periods


def calculate_muhurta(
    year: int,
    month: int,
    day: int,
    latitude: float,
    longitude: float,
    timezone_offset: float,
) -> MuhurtaInfo:
    """Calculate muhurta (electional astrology) data for a given date and place.

    Returns inauspicious windows (Rahu Kalam, Yamagandam, Gulika Kalam),
    the auspicious Abhijit Muhurta, day and night Choghadiya periods, and
    the hora (planetary hour) lord at sunrise.

    Args:
        year: Calendar year.
        month: Month (1-12).
        day: Day of month (1-31).
        latitude: Geographic latitude in degrees (north positive).
        longitude: Geographic longitude in degrees (east positive).
        timezone_offset: UTC offset in hours (e.g. 5.5 for IST).

    Returns:
        A MuhurtaInfo model with all muhurta data for the day.

    Example:
        >>> info = calculate_muhurta(2026, 3, 12, 19.076, 72.878, 5.5)
        >>> info.rahu_kalam  # (start, end) datetimes
        >>> info.choghadiya_day[0][3]  # quality of first day period
    """
    # ------------------------------------------------------------------
    # 1. Sunrise and sunset
    # ------------------------------------------------------------------
    # Convert local midnight to UT for the JD calculation.
    # Local midnight = 0:00 local ⇒ UT hour = 0 - timezone_offset.
    # _to_julian_day handles negative hours correctly (rolls to previous day).
    jd = _to_julian_day(year, month, day, -timezone_offset)
    sunrise_jd, sunset_jd = get_sunrise_sunset(jd, latitude, longitude)

    sunrise = jd_to_datetime(sunrise_jd, timezone_offset)
    sunset = jd_to_datetime(sunset_jd, timezone_offset)

    # ------------------------------------------------------------------
    # 2. Day duration (in fractional days)
    # ------------------------------------------------------------------
    day_duration = sunset_jd - sunrise_jd

    # ------------------------------------------------------------------
    # 3. Weekday (0=Monday .. 6=Sunday, matching Python's weekday())
    # ------------------------------------------------------------------
    weekday = datetime(year, month, day).weekday()

    # ------------------------------------------------------------------
    # 4. Rahu Kalam, Yamagandam, Gulika Kalam
    # ------------------------------------------------------------------
    rahu_kalam = _inauspicious_window(
        sunrise_jd, sunset_jd, RAHU_KALAM_SLOT[weekday], timezone_offset,
    )
    yamagandam = _inauspicious_window(
        sunrise_jd, sunset_jd, YAMAGANDAM_SLOT[weekday], timezone_offset,
    )
    gulika_kalam = _inauspicious_window(
        sunrise_jd, sunset_jd, GULIKA_KALAM_SLOT[weekday], timezone_offset,
    )

    # ------------------------------------------------------------------
    # 5. Abhijit Muhurta
    # ------------------------------------------------------------------
    # Abhijit Muhurta is centered on local solar noon (midpoint of
    # sunrise and sunset).  Its duration is one muhurta = day_duration / 15.
    # It spans from half a muhurta before noon to half a muhurta after noon,
    # i.e. noon ± (day_duration / 30).
    local_noon_jd = (sunrise_jd + sunset_jd) / 2.0
    half_muhurta = day_duration / 30.0
    abhijit_start = jd_to_datetime(local_noon_jd - half_muhurta, timezone_offset)
    abhijit_end = jd_to_datetime(local_noon_jd + half_muhurta, timezone_offset)

    # ------------------------------------------------------------------
    # 6. Choghadiya — day (sunrise → sunset)
    # ------------------------------------------------------------------
    choghadiya_day = _build_choghadiya(
        sunrise_jd, sunset_jd,
        CHOGHADIYA_DAY_SEQUENCE[weekday],
        timezone_offset,
    )

    # ------------------------------------------------------------------
    # 7. Choghadiya — night (sunset → next sunrise)
    # ------------------------------------------------------------------
    # Get next day's sunrise for accurate night boundaries.
    next_sunrise_jd, _ = get_sunrise_sunset(jd + 1.0, latitude, longitude)
    choghadiya_night = _build_choghadiya(
        sunset_jd, next_sunrise_jd,
        CHOGHADIYA_NIGHT_SEQUENCE[weekday],
        timezone_offset,
    )

    # ------------------------------------------------------------------
    # 8. Hora — planetary hour lord at sunrise
    # ------------------------------------------------------------------
    hora = WEEKDAY_HORA_LORD[weekday]

    # ------------------------------------------------------------------
    # Build result
    # ------------------------------------------------------------------
    return MuhurtaInfo(
        date=datetime(year, month, day),
        rahu_kalam=rahu_kalam,
        yamagandam=yamagandam,
        gulika_kalam=gulika_kalam,
        abhijit_muhurta=(abhijit_start, abhijit_end),
        choghadiya_day=choghadiya_day,
        choghadiya_night=choghadiya_night,
        hora=hora,
    )
