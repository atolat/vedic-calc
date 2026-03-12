"""
Planetary aspect (Graha Drishti) calculator.

In Vedic astrology, planets cast aspects (drishti) on other planets and
houses. Every planet aspects the 7th house from its position (the "universal"
aspect). Mars, Jupiter, Saturn, Rahu, and Ketu have additional "special"
aspects on specific houses.

HOW ASPECTS WORK:
    1. Determine which house (1-12) the aspecting planet occupies.
    2. Look up the house offsets the planet aspects (from GRAHA_DRISHTI).
       An offset of 7 means "the 7th house counted from the planet's house."
    3. Compute the aspected house number:
           aspected_house = ((planet_house - 1 + offset - 1) % 12) + 1
       This wraps correctly around the 12-house cycle.
    4. Check if any planets occupy the aspected house.
    5. The 7th-house aspect is the universal aspect (is_special=False).
       All other offsets (Mars 4th/8th, Jupiter 5th/9th, Saturn 3rd/10th,
       Rahu/Ketu 5th/9th) are special aspects (is_special=True).

SOURCE REFERENCES:
    - BPHS Ch. 26-28: Graha Drishti (planetary aspects)
    - All classical texts agree on the special aspects.

Example:
    >>> from vedic_calc.chart.aspects import calculate_aspects
    >>> aspects = calculate_aspects(chart)
    >>> for a in aspects:
    ...     print(f"{a.aspecting_planet.name} → house {a.aspected_house}")
"""

from __future__ import annotations

from vedic_calc.core.constants import GRAHA_DRISHTI, Planet
from vedic_calc.core.types import AspectInfo, BirthChart


def _get_planet_house(chart: BirthChart, planet: Planet) -> int:
    """Return the house number (1-12) a planet occupies.

    Uses the planet's sign and the house list to find the matching house.
    Each house in the whole-sign system corresponds to exactly one sign.
    """
    planet_sign = chart.planets[planet].sign
    for house in chart.houses:
        if house.sign == planet_sign:
            return house.house_number
    # Should never happen with a valid chart, but defensive fallback.
    msg = f"No house found for {planet.name} in sign {planet_sign.name}"
    raise ValueError(msg)


def _get_planets_in_house(chart: BirthChart, house_number: int) -> list[Planet]:
    """Return all planets occupying the given house number."""
    house_sign = chart.houses[house_number - 1].sign
    return [
        planet
        for planet, pos in chart.planets.items()
        if pos.sign == house_sign
    ]


def calculate_aspects(chart: BirthChart) -> list[AspectInfo]:
    """Calculate all planetary aspects (Graha Drishti) in a birth chart.

    For each planet, computes which houses it aspects (based on GRAHA_DRISHTI
    offsets), identifies any planets in those houses, and returns a sorted
    list of AspectInfo objects.

    Args:
        chart: A complete BirthChart with planets and houses.

    Returns:
        A list of AspectInfo sorted by (aspecting_planet, aspected_house).
    """
    aspects: list[AspectInfo] = []

    for planet in chart.planets:
        planet_house = _get_planet_house(chart, planet)
        offsets = GRAHA_DRISHTI.get(planet, [7])

        for offset in offsets:
            aspected_house = ((planet_house - 1 + offset - 1) % 12) + 1
            is_special = offset != 7
            occupants = _get_planets_in_house(chart, aspected_house)

            if occupants:
                for target in occupants:
                    aspects.append(
                        AspectInfo(
                            aspecting_planet=planet,
                            aspected_planet=target,
                            aspected_house=aspected_house,
                            aspect_type="full",
                            is_special=is_special,
                        )
                    )
            else:
                aspects.append(
                    AspectInfo(
                        aspecting_planet=planet,
                        aspected_planet=None,
                        aspected_house=aspected_house,
                        aspect_type="full",
                        is_special=is_special,
                    )
                )

    aspects.sort(key=lambda a: (a.aspecting_planet, a.aspected_house))
    return aspects
