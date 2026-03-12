"""
Transit chart calculator.

Computes planetary positions for any arbitrary date/time/location, returning
a TransitChart (no houses, no birth metadata — just a snapshot of the sky).

Transit charts are used to see where planets are RIGHT NOW (or at any moment),
which is then compared against a birth chart for predictions. For example:
  - "Saturn is transiting your 7th house" (marriage/partnership area)
  - "Jupiter is conjunct your natal Moon" (emotional expansion)

The calculation is identical to the planetary portion of calculate_chart(),
but returns a lighter TransitChart model without houses or birth metadata.

SOURCE REFERENCES:
    - Same ephemeris calculations as calculator.py (Swiss Ephemeris)
    - BPHS Ch. 65: Transit (Gochar) analysis principles

Example:
    >>> from vedic_calc.chart.transits import calculate_transit_chart
    >>> transit = calculate_transit_chart(2026, 3, 12, 10, 0, 0, 19.076, 72.878, 5.5)
    >>> for planet, pos in transit.planets.items():
    ...     print(f"{planet.name}: {pos.sign.name} {pos.degree_in_sign:.1f}")
"""

from __future__ import annotations

from datetime import datetime

from vedic_calc.chart.calculator import (
    longitude_to_degree_in_sign,
    longitude_to_nakshatra_info,
    longitude_to_sign,
)
from vedic_calc.core.constants import Ayanamsa, Planet
from vedic_calc.core.ephemeris import (
    _to_julian_day,
    get_ayanamsa,
    get_planet_longitude,
)
from vedic_calc.core.types import PlanetPosition, TransitChart


def calculate_transit_chart(
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
) -> TransitChart:
    """Calculate a transit chart (planetary positions) for any date/time.

    This is the same calculation as calculate_chart() but returns only
    planetary positions — no ascendant, no houses, no birth metadata.
    Latitude and longitude are accepted for API consistency but do not
    affect planetary positions (only the ascendant depends on location,
    and transit charts omit the ascendant).

    CALCULATION STEPS:
        1. Convert local time to Universal Time (UT)
        2. Convert to Julian Day number
        3. Get ayanamsa for this date
        4. Calculate sidereal longitude for each of the 9 planets
        5. Package into a TransitChart

    Args:
        year: Year (e.g., 2026).
        month: Month (1-12).
        day: Day (1-31).
        hour: Hour in LOCAL time (0-23).
        minute: Minute (0-59).
        second: Second (0-59).
        latitude: Latitude in degrees (not used for planets, kept for API consistency).
        longitude: Longitude in degrees (not used for planets, kept for API consistency).
        timezone_offset: UTC offset in hours (e.g., 5.5 for IST).
        ayanamsa: Which ayanamsa correction to use. Defaults to Lahiri.

    Returns:
        A TransitChart with all 9 planetary positions.

    Example:
        >>> transit = calculate_transit_chart(
        ...     2026, 3, 12, 10, 0, 0,
        ...     latitude=19.076, longitude=72.878,
        ...     timezone_offset=5.5,
        ... )
        >>> len(transit.planets)
        9
    """
    # Step 1: Local time → Universal Time
    hour_decimal = hour + minute / 60.0 + second / 3600.0
    ut_hour = hour_decimal - timezone_offset

    # Step 2: Julian Day number
    jd = _to_julian_day(year, month, day, ut_hour)

    # Step 3: Ayanamsa for this date
    ayanamsa_degrees = get_ayanamsa(jd, ayanamsa)

    # Step 4: Calculate all 9 planetary positions
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

    # Step 5: Package into TransitChart
    transit_dt = datetime(year, month, day, hour, minute, second)

    return TransitChart(
        date=transit_dt,
        planets=planets,
        ayanamsa=ayanamsa,
        ayanamsa_degrees=round(ayanamsa_degrees, 4),
    )
