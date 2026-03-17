"""Planet relationship calculator — Natural, Temporal, and Compound (Panchadha Maitri).

Vedic astrology defines three levels of planetary relationship:

1. **Natural (Naisargika)** — Fixed relationships from classical texts (BPHS).
   Each pair of planets has a permanent relationship: friend (2), neutral (1),
   or enemy (0). These never change regardless of the chart.

2. **Temporal (Tatkalika)** — Based on actual chart positions. A planet in
   houses 2, 3, 4, 10, 11, 12 from planet P is P's temporal friend. A planet
   in houses 1, 5, 6, 7, 8, 9 from P is P's temporal enemy.

3. **Compound (Panchadha Maitri)** — The sum of natural + temporal values,
   yielding five levels:
     - 4 = great_friend (natural friend + temporal friend)
     - 3 = friend (natural neutral + temporal friend)
     - 2 = neutral (natural friend + temporal enemy, OR natural enemy + temporal friend)
     - 1 = enemy (natural neutral + temporal enemy)
     - 0 = great_enemy (natural enemy + temporal enemy)

Only the 7 classical planets (Sun through Saturn) participate. Rahu and Ketu
are excluded from the friendship system per classical rules.

Reference: BPHS Ch. 3, Shloka 55-60.
"""

from __future__ import annotations

from vedic_calc.core.constants import PLANET_FRIENDSHIP, Planet
from vedic_calc.core.helpers import sign_distance
from vedic_calc.core.types import BirthChart, PlanetRelationship, PlanetRelationshipResult

# Only the 7 classical planets participate (Rahu/Ketu excluded)
_CLASSICAL_PLANETS = [
    Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
    Planet.JUPITER, Planet.VENUS, Planet.SATURN,
]

_NATURAL_LABELS = {0: "enemy", 1: "neutral", 2: "friend"}
_TEMPORAL_FRIEND_HOUSES = {2, 3, 4, 10, 11, 12}
_COMPOUND_LABELS = {0: "great_enemy", 1: "enemy", 2: "neutral", 3: "friend", 4: "great_friend"}


def calculate_planet_relationships(chart: BirthChart) -> PlanetRelationshipResult:
    """Calculate natural, temporal, and compound relationships between all classical planets.

    Only the 7 classical planets (Sun-Saturn) are included. Rahu and Ketu don't
    participate in the friendship system.

    Args:
        chart: A birth chart.

    Returns:
        PlanetRelationshipResult with relationships for each classical planet.

    Example:
        >>> from vedic_calc import calculate_chart, calculate_planet_relationships
        >>> from vedic_calc.core.constants import Planet
        >>> chart = calculate_chart(1990, 3, 15, 10, 30, latitude=19.076, longitude=72.878, timezone_offset=5.5)
        >>> result = calculate_planet_relationships(chart)
        >>> sun_rels = result.relationships[Planet.SUN]
        >>> sun_rels[0].compound  # Sun's compound relationship with Moon
        'great_friend'
    """
    relationships: dict[Planet, list[PlanetRelationship]] = {}

    for planet in _CLASSICAL_PLANETS:
        planet_rels: list[PlanetRelationship] = []
        planet_sign = chart.planets[planet].sign

        for other in _CLASSICAL_PLANETS:
            if other == planet:
                continue

            other_sign = chart.planets[other].sign

            # Natural relationship — fixed from PLANET_FRIENDSHIP table
            natural_val = PLANET_FRIENDSHIP[planet][other]
            natural_label = _NATURAL_LABELS[natural_val]

            # Temporal relationship — based on sign distance in the chart
            dist = sign_distance(planet_sign, other_sign)
            temporal_val = 2 if dist in _TEMPORAL_FRIEND_HOUSES else 0
            temporal_label = "friend" if temporal_val == 2 else "enemy"

            # Compound (Panchadha Maitri) — sum of natural + temporal
            compound_val = natural_val + temporal_val
            compound_label = _COMPOUND_LABELS[compound_val]

            planet_rels.append(PlanetRelationship(
                planet=planet,
                other_planet=other,
                natural=natural_label,
                temporal=temporal_label,
                compound=compound_label,
            ))

        relationships[planet] = planet_rels

    return PlanetRelationshipResult(relationships=relationships)
