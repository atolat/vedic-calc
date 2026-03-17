"""
KP (Krishnamurti Paddhati) chart calculator.

This is the main entry point for KP analysis. It combines:
    1. Standard birth chart calculation (reuses vedic-calc's calculate_chart)
    2. Placidus house cusps (via Swiss Ephemeris)
    3. KP sub-lord computation for all planets and cusps
    4. KP significator determination for each house
    5. Ruling planets calculation

KP SIGNIFICATORS:
    A planet signifies (influences) certain houses based on:
    Level 1 (strongest): The house the planet OCCUPIES
    Level 2: Houses occupied by planets whose nakshatra (star) this planet is in
             (i.e., the star lord's occupied house)
    Level 3: The house(s) the planet OWNS/RULES
    Level 4: Houses owned by the planet's star lord

    In practice, the simplified approach is:
    - Planet occupies house H -> signifies H
    - Planet's star lord occupies house H2 -> signifies H2
    - Planet owns/rules houses -> signifies those houses
    - Planet's star lord owns houses -> signifies those houses

RULING PLANETS:
    At the moment of judgment (birth/query), the ruling planets are:
    - Ascendant sign lord
    - Ascendant star lord (nakshatra lord)
    - Ascendant sub lord
    - Moon sign lord
    - Moon star lord (nakshatra lord)
    - Moon sub lord
    - Day lord (planet ruling the weekday)
"""

from __future__ import annotations

from vedic_calc.core.constants import (
    Ayanamsa,
    Planet,
    Sign,
    NAKSHATRA_LORDS,
    SIGN_LORDS,
)
from vedic_calc.core.ephemeris import _to_julian_day, get_ayanamsa
from vedic_calc.core.types import KPChartResult, KPPlanetInfo
from vedic_calc.chart.calculator import calculate_chart
from vedic_calc.kp.sublords import get_kp_sublord
from vedic_calc.kp.houses import calculate_kp_houses


# Day lords: Sunday=Sun, Monday=Moon, Tuesday=Mars, Wednesday=Mercury,
# Thursday=Jupiter, Friday=Venus, Saturday=Saturn
_DAY_LORDS = [
    Planet.MOON,      # 0 = Monday (Python weekday)
    Planet.MARS,      # 1 = Tuesday
    Planet.MERCURY,   # 2 = Wednesday
    Planet.JUPITER,   # 3 = Thursday
    Planet.VENUS,     # 4 = Friday
    Planet.SATURN,    # 5 = Saturday
    Planet.SUN,       # 6 = Sunday
]


def _get_planet_house(planet_longitude: float, cusps: list) -> int:
    """Determine which Placidus house a planet occupies.

    A planet is in house N if its longitude falls between cusp N and cusp N+1.

    Args:
        planet_longitude: Sidereal longitude of the planet (0-360).
        cusps: List of 12 cusp objects with cusp_longitude attribute.

    Returns:
        House number (1-12).
    """
    cusp_longs = [c.cusp_longitude for c in cusps]

    for i in range(12):
        start = cusp_longs[i]
        end = cusp_longs[(i + 1) % 12]

        if start < end:
            # Normal case: cusp doesn't cross 0 degrees
            if start <= planet_longitude < end:
                return i + 1
        else:
            # Cusp crosses 0 degrees (e.g., 350 to 10)
            if planet_longitude >= start or planet_longitude < end:
                return i + 1

    # Fallback: assign to house 12 if nothing matched (edge case)
    return 12


def _get_houses_owned(planet: Planet) -> list[int]:
    """Get the house numbers (1-12) owned by a planet based on sign rulership.

    This returns the sign numbers ruled by the planet, which in a generic
    sense map to house numbers. In actual KP usage, we need to check which
    houses have signs ruled by this planet based on the cusp signs.
    """
    owned = []
    for sign in Sign:
        if SIGN_LORDS[sign] == planet:
            owned.append(sign.value)
    return owned


def _get_cusp_houses_owned(planet: Planet, cusps: list) -> list[int]:
    """Get house numbers where the cusp sign is ruled by this planet.

    In KP, a planet 'owns' a house if the sign on that house's cusp
    is ruled by that planet.

    Args:
        planet: The planet to check.
        cusps: List of KPHouseCusp objects.

    Returns:
        List of house numbers (1-12) owned by this planet.
    """
    owned = []
    for cusp in cusps:
        if cusp.sign_lord == planet.value:
            owned.append(cusp.house_number)
    return owned


def calculate_kp_chart(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
    latitude: float = 0.0,
    longitude: float = 0.0,
    timezone_offset: float = 0.0,
) -> KPChartResult:
    """Full KP analysis: planets with sub-lords, Placidus cusps, significators, ruling planets.

    Args:
        year: Birth year.
        month: Birth month (1-12).
        day: Birth day (1-31).
        hour: Birth hour in local time (0-23).
        minute: Birth minute (0-59).
        second: Birth second (0-59).
        latitude: Geographic latitude (north positive).
        longitude: Geographic longitude (east positive).
        timezone_offset: UTC offset in hours (e.g., 5.5 for IST).

    Returns:
        KPChartResult with planets, cusps, significators, and ruling planets.

    Example:
        >>> result = calculate_kp_chart(
        ...     1990, 3, 15, 10, 30, 0, 19.076, 72.8777, 5.5
        ... )
        >>> len(result.planets)
        9
        >>> len(result.cusps)
        12
    """
    # Step 1: Calculate standard birth chart (reuse existing calculator)
    chart = calculate_chart(
        year, month, day, hour, minute, second,
        latitude, longitude, timezone_offset,
    )

    # Step 2: Calculate Julian Day and ayanamsa
    hour_decimal = hour + minute / 60.0 + second / 3600.0
    ut_hour = hour_decimal - timezone_offset
    jd = _to_julian_day(year, month, day, ut_hour)
    ayanamsa_value = get_ayanamsa(jd, Ayanamsa.LAHIRI)

    # Step 3: Calculate Placidus house cusps
    cusps = calculate_kp_houses(jd, latitude, longitude, ayanamsa_value)

    # Step 4: For each planet, compute KP sub-lord info and determine house occupation
    planet_houses: dict[Planet, int] = {}  # planet -> house it occupies
    kp_planet_infos: list[KPPlanetInfo] = []

    for planet in Planet:
        pos = chart.planets[planet]
        kp_info = get_kp_sublord(pos.longitude)
        house_num = _get_planet_house(pos.longitude, cusps)
        planet_houses[planet] = house_num

        # Significator houses will be filled in Step 5
        kp_planet_infos.append(KPPlanetInfo(
            planet=planet.value,
            longitude=pos.longitude,
            sign=kp_info.sign,
            sign_lord=kp_info.sign_lord,
            star_lord=kp_info.star_lord,
            sub_lord=kp_info.sub_lord,
            sub_sub_lord=kp_info.sub_sub_lord,
            significator_houses=[],  # placeholder
        ))

    # Step 5: Determine KP significators
    # For each planet, compute which houses it signifies:
    #   1. House it occupies (strongest)
    #   2. Houses occupied by planets for whom this planet is the star lord
    #      -> Actually: houses of the star lord's occupation and ownership
    #   3. Houses it owns (cusp sign lord)
    #   4. Houses owned by its star lord
    significator_table: dict[str, list[int]] = {str(h): [] for h in range(1, 13)}

    updated_planet_infos: list[KPPlanetInfo] = []
    for kp_pi in kp_planet_infos:
        planet = Planet(kp_pi.planet)
        star_lord = Planet(kp_pi.star_lord)

        sig_houses: set[int] = set()

        # Level 1: House this planet occupies
        occupied_house = planet_houses[planet]
        sig_houses.add(occupied_house)

        # Level 2: House occupied by the star lord
        star_lord_house = planet_houses[star_lord]
        sig_houses.add(star_lord_house)

        # Level 3: Houses this planet owns (based on cusp signs)
        owned_houses = _get_cusp_houses_owned(planet, cusps)
        sig_houses.update(owned_houses)

        # Level 4: Houses owned by the star lord
        star_lord_owned = _get_cusp_houses_owned(star_lord, cusps)
        sig_houses.update(star_lord_owned)

        sig_list = sorted(sig_houses)

        # Add this planet to the significator table for each house it signifies
        for h in sig_list:
            significator_table[str(h)].append(planet.value)

        # Rebuild KPPlanetInfo with significator_houses filled in
        updated_planet_infos.append(KPPlanetInfo(
            planet=kp_pi.planet,
            longitude=kp_pi.longitude,
            sign=kp_pi.sign,
            sign_lord=kp_pi.sign_lord,
            star_lord=kp_pi.star_lord,
            sub_lord=kp_pi.sub_lord,
            sub_sub_lord=kp_pi.sub_sub_lord,
            significator_houses=sig_list,
        ))

    # Step 6: Calculate ruling planets at birth moment
    # Ruling planets = unique set of:
    #   - Ascendant sign lord, star lord, sub lord
    #   - Moon sign lord, star lord, sub lord
    #   - Day lord
    asc_kp = get_kp_sublord(chart.ascendant.longitude)
    moon_pos = chart.planets[Planet.MOON]
    moon_kp = get_kp_sublord(moon_pos.longitude)

    # Day lord from weekday
    from datetime import datetime
    birth_dt = datetime(year, month, day, hour, minute, second)
    day_lord = _DAY_LORDS[birth_dt.weekday()]

    ruling_set: list[int] = []
    seen: set[int] = set()
    for p_val in [
        asc_kp.sign_lord, asc_kp.star_lord, asc_kp.sub_lord,
        moon_kp.sign_lord, moon_kp.star_lord, moon_kp.sub_lord,
        day_lord.value,
    ]:
        if p_val not in seen:
            ruling_set.append(p_val)
            seen.add(p_val)

    return KPChartResult(
        planets=updated_planet_infos,
        cusps=cusps,
        significators=significator_table,
        ruling_planets=ruling_set,
    )
