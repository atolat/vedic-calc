"""
Birth chart (Kundli) calculator.

This is the main entry point for computing a Vedic birth chart. Given a
birth date, time, and location, it produces a complete BirthChart with
all planetary positions, houses, and nakshatra information.

Example:
    >>> from vedic_calc import calculate_chart
    >>> chart = calculate_chart(
    ...     year=1990, month=3, day=15,
    ...     hour=10, minute=30,
    ...     latitude=19.0760, longitude=72.8777,
    ...     timezone_offset=5.5,
    ... )
    >>> print(chart.ascendant.sign.name)
    'GEMINI'
"""

from __future__ import annotations

from datetime import datetime

from vedic_calc.core.constants import (
    Ayanamsa,
    Nakshatra,
    Planet,
    Sign,
    NAKSHATRA_LORDS,
    NAKSHATRA_SPAN,
    PADA_SPAN,
    SIGN_LORDS,
)
from vedic_calc.core.ephemeris import (
    _to_julian_day,
    get_ascendant,
    get_ayanamsa,
    get_planet_longitude,
)
from vedic_calc.core.types import (
    BirthChart,
    HousePosition,
    NakshatraInfo,
    PlanetPosition,
)


# ---------------------------------------------------------------------------
# Helper functions (pure, no side effects)
# ---------------------------------------------------------------------------

def longitude_to_sign(longitude: float) -> Sign:
    """Convert a sidereal longitude (0-360°) to its zodiac sign.

    Each sign spans 30°: 0-30° = Aries, 30-60° = Taurus, etc.

    Args:
        longitude: Sidereal longitude in degrees (0-360).

    Returns:
        The zodiac Sign.

    Example:
        >>> longitude_to_sign(45.0)
        <Sign.TAURUS: 2>
    """
    sign_index = int(longitude / 30.0) + 1
    # Clamp to valid range (handles exactly 360.0 edge case)
    sign_index = min(sign_index, 12)
    return Sign(sign_index)


def longitude_to_degree_in_sign(longitude: float) -> float:
    """Get the degree within a sign (0-30°) from absolute longitude.

    Args:
        longitude: Sidereal longitude in degrees (0-360).

    Returns:
        Degree within the sign (0 to <30).

    Example:
        >>> longitude_to_degree_in_sign(45.0)
        15.0
    """
    return longitude % 30.0


def longitude_to_nakshatra_info(longitude: float) -> NakshatraInfo:
    """Derive nakshatra, pada, and lord from a sidereal longitude.

    Each nakshatra = 13°20' (13.333°). Each pada = 3°20' (3.333°).
    There are 27 nakshatras and 108 padas in the full 360° zodiac.

    Args:
        longitude: Sidereal longitude in degrees (0-360).

    Returns:
        NakshatraInfo with nakshatra, pada, lord, and degree within nakshatra.

    Example:
        >>> info = longitude_to_nakshatra_info(45.0)
        >>> info.nakshatra
        <Nakshatra.KRITTIKA: 3>
        >>> info.pada
        4
    """
    # Which nakshatra? (0-indexed, then +1 for our 1-indexed enum)
    nak_index = int(longitude / NAKSHATRA_SPAN)
    nak_index = min(nak_index, 26)  # Clamp for edge case at 360°
    nakshatra = Nakshatra(nak_index + 1)

    # Degree within this nakshatra
    degree_in_nak = longitude % NAKSHATRA_SPAN

    # Which pada? (each nakshatra has 4 padas of 3°20' each)
    pada = int(degree_in_nak / PADA_SPAN) + 1
    pada = min(pada, 4)  # Clamp for edge case

    # Ruling planet from the fixed nakshatra-lord table
    lord = NAKSHATRA_LORDS[nakshatra]

    return NakshatraInfo(
        nakshatra=nakshatra,
        pada=pada,
        lord=lord,
        degree_in_nakshatra=round(degree_in_nak, 4),
    )


def build_houses(ascendant_sign: Sign) -> list[HousePosition]:
    """Build the 12 houses using the Whole Sign house system.

    In Whole Sign houses, the ascendant's sign = 1st house, the next sign
    = 2nd house, and so on. This is the traditional system used in Vedic
    astrology (Parashari method).

    Args:
        ascendant_sign: The zodiac sign of the ascendant (lagna).

    Returns:
        List of 12 HousePosition objects.

    Example:
        >>> houses = build_houses(Sign.GEMINI)
        >>> houses[0].sign
        <Sign.GEMINI: 3>
        >>> houses[6].sign  # 7th house (opposite)
        <Sign.SAGITTARIUS: 9>
    """
    houses = []
    for i in range(12):
        # Signs cycle 1-12, wrapping around
        sign_value = ((ascendant_sign.value - 1 + i) % 12) + 1
        sign = Sign(sign_value)
        houses.append(HousePosition(
            house_number=i + 1,
            sign=sign,
            lord=SIGN_LORDS[sign],
        ))
    return houses


# ---------------------------------------------------------------------------
# Main chart calculation
# ---------------------------------------------------------------------------

def calculate_chart(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
    latitude: float = 0.0,
    longitude: float = 0.0,
    timezone_offset: float = 0.0,
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI,
) -> BirthChart:
    """Calculate a complete Vedic birth chart.

    This is the main entry point for vedic-calc. Given birth details,
    it computes all planetary positions, houses, and nakshatra data.

    Args:
        year: Birth year (e.g., 1990).
        month: Birth month (1-12).
        day: Birth day (1-31).
        hour: Birth hour in local time (0-23).
        minute: Birth minute (0-59).
        second: Birth second (0-59).
        latitude: Birth latitude in degrees (north positive).
        longitude: Birth longitude in degrees (east positive).
        timezone_offset: UTC offset in hours (e.g., 5.5 for IST, -5 for EST).
        ayanamsa: Which ayanamsa to use. Defaults to Lahiri.

    Returns:
        A complete BirthChart with all planetary positions and houses.

    Example:
        >>> chart = calculate_chart(
        ...     year=1990, month=3, day=15,
        ...     hour=10, minute=30,
        ...     latitude=19.0760, longitude=72.8777,
        ...     timezone_offset=5.5,
        ... )
        >>> len(chart.planets)
        9
        >>> len(chart.houses)
        12
    """
    # Convert local time to UT (Universal Time) for Swiss Ephemeris
    hour_decimal = hour + minute / 60.0 + second / 3600.0
    ut_hour = hour_decimal - timezone_offset
    jd = _to_julian_day(year, month, day, ut_hour)

    # Get ayanamsa value for metadata
    ayanamsa_degrees = get_ayanamsa(jd, ayanamsa)

    # Calculate ascendant
    asc_longitude = get_ascendant(jd, latitude, longitude, ayanamsa)
    asc_sign = longitude_to_sign(asc_longitude)
    asc_degree = longitude_to_degree_in_sign(asc_longitude)
    asc_nakshatra = longitude_to_nakshatra_info(asc_longitude)

    ascendant = PlanetPosition(
        planet=Planet.SUN,  # Placeholder — ascendant isn't a planet
        longitude=round(asc_longitude, 4),
        sign=asc_sign,
        degree_in_sign=round(asc_degree, 4),
        nakshatra_info=asc_nakshatra,
        is_retrograde=False,
    )

    # Calculate all 9 planetary positions
    planets: dict[Planet, PlanetPosition] = {}
    for planet in Planet:
        lon, is_retro = get_planet_longitude(jd, planet, ayanamsa)
        sign = longitude_to_sign(lon)
        degree = longitude_to_degree_in_sign(lon)
        nak_info = longitude_to_nakshatra_info(lon)

        planets[planet] = PlanetPosition(
            planet=planet,
            longitude=round(lon, 4),
            sign=sign,
            degree_in_sign=round(degree, 4),
            nakshatra_info=nak_info,
            is_retrograde=is_retro,
        )

    # Build houses using Whole Sign system from the ascendant
    houses = build_houses(asc_sign)

    # Store birth datetime in local time for reference
    birth_dt = datetime(year, month, day, hour, minute, second)

    return BirthChart(
        planets=planets,
        houses=houses,
        ascendant=ascendant,
        ayanamsa=ayanamsa,
        ayanamsa_degrees=round(ayanamsa_degrees, 4),
        birth_datetime=birth_dt,
        latitude=latitude,
        longitude=longitude,
        timezone_offset=timezone_offset,
    )
