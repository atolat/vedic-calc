"""
Thin wrapper around pyswisseph (Swiss Ephemeris).

This is the ONLY module in vedic-calc that imports pyswisseph.
Everything else works with plain longitude values (floats).

The Swiss Ephemeris provides high-precision planetary positions used
by professional astronomy and astrology software worldwide.
"""

from __future__ import annotations

import swisseph as swe

from vedic_calc.core.constants import Ayanamsa, Planet, PLANET_TO_SWE


def _to_julian_day(
    year: int,
    month: int,
    day: int,
    hour: float = 0.0,
) -> float:
    """Convert a date/time to Julian Day number.

    Args:
        year: Calendar year.
        month: Month (1-12).
        day: Day of month (1-31).
        hour: Hour as decimal (e.g., 10.5 = 10:30 AM). Should be in UT (UTC).

    Returns:
        Julian Day number (float).
    """
    return swe.julday(year, month, day, hour)


def get_ayanamsa(
    jd: float,
    mode: Ayanamsa = Ayanamsa.LAHIRI,
) -> float:
    """Get the ayanamsa (precession correction) value for a given Julian Day.

    The ayanamsa is the angular difference between the tropical and sidereal
    zodiacs. It increases slowly over centuries (~50.3" per year).

    Args:
        jd: Julian Day number.
        mode: Which ayanamsa system to use. Defaults to Lahiri.

    Returns:
        Ayanamsa value in degrees.

    Example:
        >>> jd = _to_julian_day(2000, 1, 1)
        >>> aya = get_ayanamsa(jd, Ayanamsa.LAHIRI)
        >>> 23.0 < aya < 25.0  # Lahiri ayanamsa is ~23-24° around year 2000
        True
    """
    swe.set_sid_mode(int(mode))
    return swe.get_ayanamsa_ut(jd)


def get_planet_longitude(
    jd: float,
    planet: Planet,
    ayanamsa_mode: Ayanamsa = Ayanamsa.LAHIRI,
) -> tuple[float, bool]:
    """Get a planet's sidereal longitude and retrograde status.

    Args:
        jd: Julian Day number (in UT).
        planet: Which planet to calculate.
        ayanamsa_mode: Ayanamsa for sidereal correction. Defaults to Lahiri.

    Returns:
        Tuple of (sidereal_longitude, is_retrograde).
        Longitude is in degrees (0-360). Retrograde is True if the planet
        appears to move backward.

    Example:
        >>> jd = _to_julian_day(1990, 3, 15, 5.0)  # 10:30 IST = 5:00 UT
        >>> lon, retro = get_planet_longitude(jd, Planet.MOON)
        >>> 0 <= lon < 360
        True
    """
    ayanamsa = get_ayanamsa(jd, ayanamsa_mode)

    if planet == Planet.KETU:
        # Ketu is always exactly opposite Rahu (180°)
        rahu_swe = PLANET_TO_SWE[Planet.RAHU]
        result = swe.calc_ut(jd, rahu_swe)
        tropical_lon = result[0][0]
        sidereal_lon = (tropical_lon - ayanamsa + 180.0) % 360.0
        # Ketu's speed is opposite of Rahu; nodes are always retrograde
        return sidereal_lon, True

    swe_planet = PLANET_TO_SWE[planet]
    result = swe.calc_ut(jd, swe_planet)

    tropical_lon = result[0][0]
    speed = result[0][3]  # Daily speed in longitude (negative = retrograde)

    sidereal_lon = (tropical_lon - ayanamsa) % 360.0
    is_retrograde = speed < 0

    # Rahu is always considered retrograde in Vedic astrology
    if planet == Planet.RAHU:
        is_retrograde = True

    return sidereal_lon, is_retrograde


def get_ascendant(
    jd: float,
    latitude: float,
    longitude: float,
    ayanamsa_mode: Ayanamsa = Ayanamsa.LAHIRI,
) -> float:
    """Get the sidereal ascendant (lagna) longitude.

    The ascendant is the zodiac degree rising on the eastern horizon
    at the time and place of birth.

    Args:
        jd: Julian Day number (in UT).
        latitude: Geographic latitude in degrees (north positive).
        longitude: Geographic longitude in degrees (east positive).
        ayanamsa_mode: Ayanamsa for sidereal correction.

    Returns:
        Sidereal ascendant longitude in degrees (0-360).

    Example:
        >>> jd = _to_julian_day(1990, 3, 15, 5.0)
        >>> asc = get_ascendant(jd, 19.076, 72.878)
        >>> 0 <= asc < 360
        True
    """
    ayanamsa = get_ayanamsa(jd, ayanamsa_mode)

    # swe.houses_ex returns (cusps_tuple, ascmc_tuple)
    # ascmc[0] = ascendant in tropical longitude
    _, ascmc = swe.houses_ex(jd, latitude, longitude, b"W")  # "W" = Whole Sign
    tropical_asc = ascmc[0]

    return (tropical_asc - ayanamsa) % 360.0


def get_sunrise_sunset(
    jd: float,
    latitude: float,
    longitude: float,
) -> tuple[float, float]:
    """Get sunrise and sunset Julian Day numbers for a given date and location.

    Args:
        jd: Julian Day number for the date (typically at midnight UT).
        latitude: Geographic latitude.
        longitude: Geographic longitude.

    Returns:
        Tuple of (sunrise_jd, sunset_jd) as Julian Day numbers.
    """
    # rsmi=1 for sunrise, rsmi=2 for sunset
    # Using atmospheric refraction (SE_BIT_DISC_CENTER not set)
    sunrise_jd = swe.rise_trans(
        jd, swe.SUN, geopos=(longitude, latitude, 0), rsmi=1
    )[1][0]

    sunset_jd = swe.rise_trans(
        jd, swe.SUN, geopos=(longitude, latitude, 0), rsmi=2
    )[1][0]

    return sunrise_jd, sunset_jd
