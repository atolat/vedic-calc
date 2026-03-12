"""Ashtakavarga calculation — benefic point analysis for each sign.

Ashtakavarga ("eight divisions of strength") is a system from BPHS that
assigns benefic points (bindus) to each of the 12 signs for each planet.
Eight contributors (7 planets + lagna) each either grant or withhold a
point based on classical lookup tables.

Two levels of analysis:
  - Bhinnashtakavarga: Individual benefic-point table per planet (0-8 per sign).
  - Sarvashtakavarga: Sum of all 7 individual tables (0-56 per sign).

Only 7 planets participate (Sun through Saturn). Rahu and Ketu are excluded
from classical Ashtakavarga.

Reference: Brihat Parashara Hora Shastra, Chapters 66-72.
"""

from __future__ import annotations

from vedic_calc.core.constants import ASHTAKAVARGA_BENEFIC, Planet
from vedic_calc.core.types import AshtakavargaResult, BirthChart

# The 7 planets that participate in Ashtakavarga (no Rahu/Ketu).
_ASHTAKAVARGA_PLANETS: list[Planet] = [
    Planet.SUN,
    Planet.MOON,
    Planet.MARS,
    Planet.MERCURY,
    Planet.JUPITER,
    Planet.VENUS,
    Planet.SATURN,
]


def calculate_ashtakavarga(chart: BirthChart) -> AshtakavargaResult:
    """Calculate Ashtakavarga (benefic point tables) for a birth chart.

    For each of the 7 receiver planets (Sun-Saturn), this builds a 12-element
    list where each element is the count of benefic points (bindus) for the
    corresponding sign (index 0 = Aries, index 11 = Pisces).

    Eight contributors (Sun-Saturn + Lagna) are evaluated per receiver.
    A contributor grants a point to each sign that is at the specified house
    distance from the contributor's position, as defined in
    ``ASHTAKAVARGA_BENEFIC``.

    Args:
        chart: A fully calculated birth chart.

    Returns:
        AshtakavargaResult with ``bhinna`` (per-planet tables) and ``sarva``
        (combined table).

    Example:
        >>> result = calculate_ashtakavarga(chart)
        >>> result.bhinna[Planet.SUN]   # 12 ints, one per sign
        [3, 5, 2, 4, 6, 3, 5, 4, 3, 6, 5, 2]
        >>> sum(result.sarva)            # always equals sum of all bhinna
        337
    """
    bhinna: dict[Planet, list[int]] = {}

    for receiver in _ASHTAKAVARGA_PLANETS:
        points = [0] * 12  # index 0 → Aries (sign 1), index 11 → Pisces (sign 12)
        contributor_table = ASHTAKAVARGA_BENEFIC[receiver]

        for contributor, benefic_houses in contributor_table.items():
            # Determine the contributor's sign value (1-12).
            if contributor == "lagna":
                contributor_sign = int(chart.ascendant.sign)
            else:
                contributor_sign = int(chart.planets[contributor].sign)

            for house_number in benefic_houses:
                # The h-th sign from the contributor is:
                #   ((contributor_sign - 1) + (house_number - 1)) % 12 + 1
                benefic_sign = ((contributor_sign - 1 + house_number - 1) % 12) + 1
                points[benefic_sign - 1] += 1

        bhinna[receiver] = points

    # Sarvashtakavarga: sum across all 7 planets for each sign.
    sarva = [
        sum(bhinna[planet][i] for planet in _ASHTAKAVARGA_PLANETS)
        for i in range(12)
    ]

    return AshtakavargaResult(bhinna=bhinna, sarva=sarva)
