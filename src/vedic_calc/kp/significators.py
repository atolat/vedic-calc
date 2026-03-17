"""
KP (Krishnamurti Paddhati) Significator determination.

KP SIGNIFICATORS:
    In KP astrology, each planet signifies certain houses through a 4-level
    hierarchy. This determines which life areas (houses) a planet can
    activate during its dasha/bhukti.

    Level 1: Houses occupied by the planet
    Level 2: Houses occupied by planets in this planet's star (nakshatra
             lord connection — the star lord's occupied houses)
    Level 3: Houses owned/ruled by the planet
    Level 4: Houses owned by the planet's star lord

    The union of all 4 levels gives the complete set of houses a planet
    signifies. When a planet's dasha runs, these are the houses that get
    activated.

SOURCE: K.S. Krishnamurti, KP Reader series.
"""

from __future__ import annotations

from vedic_calc.core.constants import Planet, Sign, SIGN_LORDS
from vedic_calc.core.types import BirthChart, KPSignificatorDetail, KPHouseSignificators
from vedic_calc.core.helpers import planet_house


def _houses_owned_by(planet: Planet, chart: BirthChart) -> list[int]:
    """Get the house numbers owned (lorded) by a planet in the chart.

    A planet owns a house if it is the lord of the sign on that house cusp.
    For whole-sign houses, this means SIGN_LORDS[house.sign] == planet.

    Returns:
        Sorted list of house numbers (1-12) owned by the planet.
    """
    owned: list[int] = []
    for house in chart.houses:
        if SIGN_LORDS[house.sign] == planet:
            owned.append(house.house_number)
    return sorted(owned)


def get_kp_significators(chart: BirthChart) -> list[KPSignificatorDetail]:
    """Get per-planet KP significators at 4 levels.

    For each of the 9 planets, determines which houses it signifies
    through occupation, star-lord connection, ownership, and star-lord
    ownership.

    Args:
        chart: A BirthChart (from calculate_chart, uses whole-sign houses).

    Returns:
        List of 9 KPSignificatorDetail objects, one per planet.
    """
    # Pre-compute: which house does each planet occupy?
    planet_to_house: dict[Planet, int] = {}
    for planet in Planet:
        planet_to_house[planet] = planet_house(chart, planet)

    # Pre-compute: which houses does each planet own?
    planet_to_owned: dict[Planet, list[int]] = {}
    for planet in Planet:
        planet_to_owned[planet] = _houses_owned_by(planet, chart)

    results: list[KPSignificatorDetail] = []

    for planet in Planet:
        # Level 1: Houses occupied by this planet
        level1 = [planet_to_house[planet]]

        # Get the star lord (nakshatra lord) of this planet
        star_lord = chart.planets[planet].nakshatra_info.lord

        # Level 2: Houses occupied by planets whose nakshatra lord is this planet
        # i.e., houses occupied by the star lord of this planet
        level2 = [planet_to_house[star_lord]]

        # Level 3: Houses owned/ruled by this planet
        level3 = planet_to_owned[planet]

        # Level 4: Houses owned by this planet's star lord
        level4 = planet_to_owned[star_lord]

        # Union of all levels (sorted, unique)
        all_houses = sorted(set(level1 + level2 + level3 + level4))

        results.append(KPSignificatorDetail(
            planet=planet,
            level1_houses=level1,
            level2_houses=level2,
            level3_houses=level3,
            level4_houses=level4,
            all_signified_houses=all_houses,
        ))

    return results


def get_kp_house_significators(chart: BirthChart) -> list[KPHouseSignificators]:
    """Get per-house significator planets.

    For each of the 12 houses, determines which planets signify it
    (i.e., which planets have this house in their all_signified_houses).

    Args:
        chart: A BirthChart (from calculate_chart, uses whole-sign houses).

    Returns:
        List of 12 KPHouseSignificators objects, one per house.
    """
    planet_significators = get_kp_significators(chart)

    results: list[KPHouseSignificators] = []

    for house_num in range(1, 13):
        significators: list[Planet] = []
        for ps in planet_significators:
            if house_num in ps.all_signified_houses:
                significators.append(ps.planet)

        results.append(KPHouseSignificators(
            house_number=house_num,
            significators=significators,
        ))

    return results
