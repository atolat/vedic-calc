"""Jaimini Chara Karaka calculation.

Chara karakas ("variable significators") are a cornerstone of Jaimini
astrology. Unlike Parashari sthira (fixed) karakas where each planet has
a permanent signification, chara karakas are assigned based on the actual
degree each planet occupies within its sign in a given birth chart.

The planet with the highest degree in its sign becomes the Atmakaraka
(significator of the self/soul), the next highest becomes the Amatyakaraka
(significator of career/minister), and so on.

This module implements the 8-karaka scheme (including Rahu).
"""

from __future__ import annotations

from vedic_calc.core.constants import CHARA_KARAKA_NAMES, Planet
from vedic_calc.core.types import BirthChart, CharaKaraka

# The 8 planets used in Jaimini chara karaka calculation.
# Ketu is excluded because it always shares the same degree as Rahu
# (they are 180° apart) and including both would create a redundancy.
_JAIMINI_PLANETS: list[Planet] = [
    Planet.SUN,
    Planet.MOON,
    Planet.MARS,
    Planet.MERCURY,
    Planet.JUPITER,
    Planet.VENUS,
    Planet.SATURN,
    Planet.RAHU,
]


def calculate_chara_karakas(chart: BirthChart) -> list[CharaKaraka]:
    """Calculate the eight Jaimini chara karakas from a birth chart.

    The algorithm:
        1. Take the 8 Jaimini planets (Sun through Saturn + Rahu; Ketu excluded).
        2. For Rahu, reverse the degree (30 - degree_in_sign) because Rahu is
           always retrograde — its effective progression within a sign runs
           opposite to the other planets.
        3. Sort descending by degree_in_sign. The highest degree gets the
           first karaka name (Atmakaraka), the next gets the second, etc.
        4. On a tie (same degree_in_sign float value), the planet with the
           lower enum value (natural order) takes priority (higher rank).

    Args:
        chart: A fully computed BirthChart with planet positions.

    Returns:
        A list of 8 CharaKaraka objects ordered from Atmakaraka (index 0)
        to Pitrkaraka (index 7).

    Example:
        >>> karakas = calculate_chara_karakas(chart)
        >>> karakas[0].karaka_name
        'Atmakaraka'
        >>> karakas[0].planet
        <Planet.MARS: 2>
    """
    # Build (effective_degree, planet) pairs for sorting.
    planet_degrees: list[tuple[float, Planet]] = []
    for planet in _JAIMINI_PLANETS:
        pos = chart.planets[planet]
        if planet == Planet.RAHU:
            effective_degree = 30.0 - pos.degree_in_sign
        else:
            effective_degree = pos.degree_in_sign
        planet_degrees.append((effective_degree, planet))

    # Sort descending by degree. On tie, lower Planet enum value wins
    # (should rank higher, i.e., come first), so we use ascending planet
    # value as the secondary key.
    planet_degrees.sort(key=lambda pd: (-pd[0], pd[1]))

    return [
        CharaKaraka(
            karaka_name=CHARA_KARAKA_NAMES[i],
            planet=planet,
            degree_in_sign=degree,
        )
        for i, (degree, planet) in enumerate(planet_degrees)
    ]
