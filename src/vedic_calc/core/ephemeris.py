"""
Thin wrapper around pyswisseph (Swiss Ephemeris).

THIS IS THE ONLY MODULE IN VEDIC-CALC THAT IMPORTS PYSWISSEPH.
Everything else works with plain longitude values (floats).

WHY THIS BOUNDARY EXISTS:
    The Swiss Ephemeris has a complex C-style API. By isolating it here,
    the rest of the codebase is pure Python arithmetic on floats — easy
    to test, understand, and (if ever needed) swap to a different engine.

WHAT IS THE SWISS EPHEMERIS?
    A high-precision astronomical calculation library, accurate to
    < 0.001 arcseconds. It's based on NASA JPL's Development Ephemeris
    (DE431) and has been the industry standard since 1997. Every major
    astrology software (JHora, AstroSage, etc.) uses it under the hood.

    It provides planetary positions in the "tropical" zodiac (aligned with
    seasons). We subtract the ayanamsa to convert to the "sidereal" zodiac
    (aligned with fixed stars), which is what Vedic astrology uses.

COORDINATE SYSTEM:
    - All longitudes are in degrees (0° to 360°) along the ecliptic
    - 0° = the First Point of Aries (tropical) or the start of Aries
      constellation (sidereal)
    - Longitude increases counter-clockwise when viewed from north

TIME SYSTEM:
    The Swiss Ephemeris uses Julian Day numbers (JD) — a continuous count
    of days since January 1, 4713 BCE. This avoids calendar complexities
    (leap years, calendar reforms, etc.). All times must be in Universal
    Time (UT/UTC), not local time.
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

    Julian Day is a continuous day count used by astronomers to avoid
    calendar complications. For example:
        January 1, 2000 at noon UT = JD 2451545.0

    Args:
        year: Calendar year (e.g., 1990). Can be negative for BCE dates.
        month: Month (1-12).
        day: Day of month (1-31).
        hour: Hour as decimal in UT (e.g., 10.5 = 10:30 AM UT).
              IMPORTANT: This must be Universal Time, not local time.
              Convert first: ut_hour = local_hour - timezone_offset

    Returns:
        Julian Day number (float).

    Example:
        >>> _to_julian_day(2000, 1, 1, 12.0)  # J2000.0 epoch
        2451545.0
    """
    return swe.julday(year, month, day, hour)


def get_ayanamsa(
    jd: float,
    mode: Ayanamsa = Ayanamsa.LAHIRI,
) -> float:
    """Get the ayanamsa (precession correction) value for a given date.

    The ayanamsa is the angular difference between the tropical zodiac
    (Western astrology) and the sidereal zodiac (Vedic astrology).

    It changes slowly over time (~50.3 arcseconds per year) due to
    Earth's axial precession. Approximate values:
        Year 1900: ~22.4°
        Year 2000: ~23.9°
        Year 2024: ~24.2°

    Formula applied later:
        sidereal_longitude = tropical_longitude - ayanamsa

    Args:
        jd: Julian Day number.
        mode: Which ayanamsa system to use. Defaults to Lahiri
              (the Indian government standard).

    Returns:
        Ayanamsa value in degrees.

    Example:
        >>> jd = _to_julian_day(2000, 1, 1)
        >>> aya = get_ayanamsa(jd, Ayanamsa.LAHIRI)
        >>> 23.0 < aya < 25.0
        True
    """
    # Tell Swiss Ephemeris which ayanamsa mode to use
    swe.set_sid_mode(int(mode))
    # Get the ayanamsa value for this Julian Day
    return swe.get_ayanamsa_ut(jd)


def get_planet_longitude(
    jd: float,
    planet: Planet,
    ayanamsa_mode: Ayanamsa = Ayanamsa.LAHIRI,
) -> tuple[float, bool]:
    """Get a planet's sidereal longitude and retrograde status.

    CALCULATION STEPS:
        1. Call Swiss Ephemeris to get the tropical (Western) longitude
        2. Get the ayanamsa for this date
        3. Subtract ayanamsa to convert to sidereal (Vedic) longitude:
           sidereal = (tropical - ayanamsa) % 360
        4. Check if the planet's daily motion is negative (= retrograde)

    RETROGRADE:
        Planets sometimes appear to move backward in the sky (an illusion
        caused by Earth overtaking slower outer planets, or inner planets
        lapping Earth). This is called "retrograde" motion and is considered
        significant in astrology. We detect it by checking if the planet's
        daily speed in longitude is negative.

    SPECIAL CASES:
        - Rahu: Always considered retrograde in Vedic astrology (the lunar
          nodes naturally move backward through the zodiac)
        - Ketu: Always exactly 180° from Rahu, always retrograde

    Args:
        jd: Julian Day number (in UT).
        planet: Which planet to calculate.
        ayanamsa_mode: Ayanamsa for sidereal correction.

    Returns:
        Tuple of (sidereal_longitude, is_retrograde).
        - longitude: degrees (0-360), where 0° = start of Aries (sidereal)
        - is_retrograde: True if planet appears to move backward

    Example:
        >>> jd = _to_julian_day(1990, 3, 15, 5.0)  # 10:30 IST = 5:00 UT
        >>> lon, retro = get_planet_longitude(jd, Planet.MOON)
        >>> 0 <= lon < 360
        True
    """
    ayanamsa = get_ayanamsa(jd, ayanamsa_mode)

    # --- Special case: Ketu ---
    # Ketu has no Swiss Ephemeris constant. It's always exactly opposite Rahu.
    # Formula: ketu_sidereal = (rahu_tropical - ayanamsa + 180°) % 360°
    if planet == Planet.KETU:
        rahu_swe = PLANET_TO_SWE[Planet.RAHU]
        result = swe.calc_ut(jd, rahu_swe)
        tropical_lon = result[0][0]
        sidereal_lon = (tropical_lon - ayanamsa + 180.0) % 360.0
        return sidereal_lon, True  # Nodes are always retrograde

    # --- Normal planets ---
    swe_planet = PLANET_TO_SWE[planet]
    # swe.calc_ut returns a tuple: ((lon, lat, dist, speed_lon, speed_lat, speed_dist), flags)
    # We need result[0][0] = tropical longitude and result[0][3] = daily speed
    result = swe.calc_ut(jd, swe_planet)

    tropical_lon = result[0][0]   # Tropical longitude in degrees
    speed = result[0][3]          # Daily speed in longitude (°/day)

    # Convert tropical → sidereal by subtracting ayanamsa
    # The % 360 handles wraparound (e.g., if tropical=5° and ayanamsa=24°,
    # we get 5-24 = -19°, which wraps to 341° = Pisces)
    sidereal_lon = (tropical_lon - ayanamsa) % 360.0

    # Retrograde = planet appears to move backward = negative daily speed
    is_retrograde = speed < 0

    # Rahu's mathematical speed can be positive, but in Vedic astrology
    # the nodes are ALWAYS considered retrograde (they naturally move
    # backward through the zodiac over ~18.6 years)
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

    WHAT IS THE ASCENDANT?
        The ascendant (or "lagna" in Sanskrit) is the zodiac degree that
        was rising on the eastern horizon at the exact moment and place
        of birth. It changes roughly every 2 hours (since the Earth
        rotates 360° in 24 hours, and there are 12 signs).

        The ascendant is considered the most important point in a Vedic
        birth chart — it determines which sign becomes your 1st house,
        and all other houses follow from there.

    WHY LOCATION MATTERS:
        Unlike planetary positions (which are the same worldwide at any
        given moment), the ascendant depends on your geographic latitude
        and longitude because it's about what's on YOUR horizon.

    Args:
        jd: Julian Day number (in UT).
        latitude: Geographic latitude in degrees (north = positive).
        longitude: Geographic longitude in degrees (east = positive).
        ayanamsa_mode: Ayanamsa for sidereal correction.

    Returns:
        Sidereal ascendant longitude in degrees (0-360).

    Example:
        >>> jd = _to_julian_day(1990, 3, 15, 5.0)  # 10:30 IST = 5:00 UT
        >>> asc = get_ascendant(jd, 19.076, 72.878)  # Mumbai
        >>> 0 <= asc < 360
        True
    """
    ayanamsa = get_ayanamsa(jd, ayanamsa_mode)

    # swe.houses_ex calculates house cusps and special points.
    # Arguments: (julian_day, latitude, longitude, house_system)
    #   house_system = b"W" for Whole Sign (the standard Vedic system)
    #
    # Returns: (cusps_tuple, ascmc_tuple)
    #   ascmc[0] = ascendant (tropical longitude)
    #   ascmc[1] = MC (midheaven)
    #   ascmc[2] = ARMC
    #   ascmc[3] = vertex
    _, ascmc = swe.houses_ex(jd, latitude, longitude, b"W")
    tropical_asc = ascmc[0]

    # Convert tropical → sidereal (same formula as planets)
    return (tropical_asc - ayanamsa) % 360.0


def get_sunrise_sunset(
    jd: float,
    latitude: float,
    longitude: float,
) -> tuple[float, float]:
    """Get sunrise and sunset times for a given date and location.

    Used by the panchanga (daily calendar) module to determine the
    Vedic day boundaries. In Vedic astrology, a "day" runs from
    sunrise to the next sunrise (not midnight to midnight).

    Args:
        jd: Julian Day number for the date (typically at midnight UT).
        latitude: Geographic latitude in degrees.
        longitude: Geographic longitude in degrees.

    Returns:
        Tuple of (sunrise_jd, sunset_jd) as Julian Day numbers.
        Convert back to clock time using the Swiss Ephemeris revjul function.
    """
    # swe.rise_trans calculates rise/set times for celestial bodies.
    # rsmi=1 → sunrise (upper limb of Sun crosses horizon)
    # rsmi=2 → sunset (upper limb of Sun crosses horizon)
    # geopos = (longitude, latitude, altitude_in_meters)
    # Note: geopos takes longitude FIRST, then latitude (unusual order)
    sunrise_jd = swe.rise_trans(
        jd, swe.SUN, geopos=(longitude, latitude, 0), rsmi=1
    )[1][0]

    sunset_jd = swe.rise_trans(
        jd, swe.SUN, geopos=(longitude, latitude, 0), rsmi=2
    )[1][0]

    return sunrise_jd, sunset_jd
