"""
Panchanga (five-limbed daily calendar) calculator.

WHAT IS PANCHANGA?
    "Pancha" = five, "Anga" = limb. The Panchanga is a daily Vedic
    calendar that tracks 5 astronomical elements, all computed from
    the positions of the Sun and Moon:

    1. TITHI (Lunar Day) — Moon-Sun angular separation ÷ 12°
    2. NAKSHATRA — Which lunar mansion the Moon is in
    3. YOGA — (Moon + Sun longitude) ÷ 13.333°
    4. KARANA — Half a tithi (Moon-Sun separation ÷ 6°)
    5. VARA — Weekday (derived from the calendar date)

    In Vedic tradition, the "day" begins at SUNRISE, not midnight.
    So panchanga calculations are done at sunrise time for the location.

WHY PANCHANGA MATTERS:
    Hindus consult the panchanga daily for:
    - Choosing auspicious times (muhurta) for ceremonies, business, travel
    - Knowing festival dates (most Hindu festivals follow the lunar calendar)
    - Agricultural planning (traditional farming follows lunar phases)
    - Religious observances (fasting days like Ekadashi = 11th tithi)

CALCULATION OVERVIEW:
    1. Find sunrise time for the given date and location
    2. Calculate Moon and Sun sidereal longitudes at sunrise
    3. Compute the 5 elements from these two longitude values

SOURCE: Surya Siddhanta (astronomical formulas), various panchanga references.
"""

from __future__ import annotations

from datetime import datetime

from vedic_calc.core.constants import (
    Ayanamsa,
    Nakshatra,
    Planet,
    KARANA_NAMES,
    NAKSHATRA_SPAN,
    TITHI_NAMES,
    VARA_NAMES,
    YOGA_NAMES,
)
from vedic_calc.core.ephemeris import (
    _to_julian_day,
    get_planet_longitude,
    get_sunrise_sunset,
    jd_to_datetime,
)
from vedic_calc.core.types import PanchangaInfo


def calculate_panchanga(
    year: int,
    month: int,
    day: int,
    latitude: float,
    longitude: float,
    timezone_offset: float = 0.0,
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI,
) -> PanchangaInfo:
    """Calculate the Panchanga (five-element daily calendar) for a given date.

    STEP-BY-STEP:
        1. Convert the date to a Julian Day at midnight UT
        2. Find the exact sunrise time for the location
        3. Get Moon and Sun sidereal longitudes at sunrise
        4. Compute tithi, nakshatra, yoga, karana from those longitudes
        5. Determine the weekday (vara)

    Args:
        year: Calendar year.
        month: Month (1-12).
        day: Day (1-31).
        latitude: Geographic latitude (north = positive).
        longitude: Geographic longitude (east = positive).
        timezone_offset: UTC offset in hours (e.g., 5.5 for IST).
        ayanamsa: Which ayanamsa to use. Defaults to Lahiri.

    Returns:
        PanchangaInfo with all 5 elements + sunrise/sunset times.

    Example:
        >>> p = calculate_panchanga(2026, 3, 8, 19.076, 72.878, 5.5)
        >>> p.vara
        'Sunday (Ravivara)'
        >>> "Shukla" in p.tithi_name or "Krishna" in p.tithi_name or "Purnima" in p.tithi_name or "Amavasya" in p.tithi_name
        True
    """
    # ─── Step 1: Get Julian Day at midnight UT for this date ───
    # We need a starting JD to find sunrise. Midnight UT is a good start.
    ut_hour = 0.0 - timezone_offset  # Midnight local → UT
    jd_midnight = _to_julian_day(year, month, day, ut_hour)

    # ─── Step 2: Find sunrise and sunset ───
    # In Vedic tradition, the day starts at sunrise.
    # get_sunrise_sunset returns JD values for sunrise/sunset.
    sunrise_jd: float | None = None
    sunset_jd: float | None = None
    sunrise_dt: datetime | None = None
    sunset_dt: datetime | None = None

    try:
        sunrise_jd, sunset_jd = get_sunrise_sunset(jd_midnight, latitude, longitude)
        sunrise_dt = jd_to_datetime(sunrise_jd, timezone_offset)
        sunset_dt = jd_to_datetime(sunset_jd, timezone_offset)
    except Exception:
        # Sunrise/sunset may fail at extreme latitudes (polar regions).
        # Fall back to using noon for calculations.
        pass

    # ─── Step 3: Get Moon and Sun positions at sunrise (or noon fallback) ───
    calc_jd = sunrise_jd if sunrise_jd is not None else jd_midnight + 0.5

    moon_lon, _ = get_planet_longitude(calc_jd, Planet.MOON, ayanamsa)
    sun_lon, _ = get_planet_longitude(calc_jd, Planet.SUN, ayanamsa)

    # ─── Step 4a: TITHI ───
    # Tithi = angular distance of Moon from Sun, divided into 12° segments.
    # The Moon moves ~12° per day relative to the Sun, so roughly one tithi/day.
    #
    # Formula: tithi_number = floor(((moon - sun) % 360) / 12) + 1
    #
    # Tithis 1-15 = Shukla Paksha (waxing, new moon → full moon)
    # Tithis 16-30 = Krishna Paksha (waning, full moon → new moon)
    moon_sun_diff = (moon_lon - sun_lon) % 360.0
    tithi_number = int(moon_sun_diff / 12.0) + 1
    tithi_number = min(tithi_number, 30)  # Clamp edge case
    tithi_name = TITHI_NAMES[tithi_number]

    # ─── Step 4b: NAKSHATRA ───
    # Which of the 27 nakshatras the Moon is in at sunrise.
    # Same formula as birth nakshatra: floor(moon_lon / 13.333) + 1
    nak_index = int(moon_lon / NAKSHATRA_SPAN)
    nak_index = min(nak_index, 26)
    nakshatra = Nakshatra(nak_index + 1)

    # ─── Step 4c: YOGA ───
    # Yoga is based on the SUM of Moon and Sun longitudes.
    # There are 27 yogas, each spanning 13°20' (same as nakshatras but
    # computed from the sum, not just Moon position).
    #
    # Formula: yoga_number = floor(((moon + sun) % 360) / 13.333) + 1
    #
    # Despite the same 13.333° span, yogas are completely unrelated to nakshatras.
    yoga_sum = (moon_lon + sun_lon) % 360.0
    yoga_number = int(yoga_sum / NAKSHATRA_SPAN) + 1
    yoga_number = min(yoga_number, 27)
    yoga_name = YOGA_NAMES[yoga_number]

    # ─── Step 4d: KARANA ───
    # Karana = half a tithi = 6° of Moon-Sun separation.
    # Each tithi has 2 karanas, giving 60 karanas per lunar month.
    #
    # Formula: karana_number = floor(((moon - sun) % 360) / 6) + 1
    karana_number = int(moon_sun_diff / 6.0) + 1
    karana_number = min(karana_number, 60)
    karana_name = KARANA_NAMES[karana_number]

    # ─── Step 5: VARA (weekday) ───
    # Derived from the calendar date using Python's datetime.
    dt = datetime(year, month, day)
    vara = VARA_NAMES[dt.weekday()]

    return PanchangaInfo(
        date=dt,
        vara=vara,
        tithi_number=tithi_number,
        tithi_name=tithi_name,
        nakshatra=nakshatra,
        yoga_number=yoga_number,
        yoga_name=yoga_name,
        karana_number=karana_number,
        karana_name=karana_name,
        sunrise=sunrise_dt,
        sunset=sunset_dt,
    )
