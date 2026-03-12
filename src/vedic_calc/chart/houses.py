"""
House analysis module.

Provides detailed analysis of all 12 houses in a birth chart: which planets
occupy each house, which planets aspect it, where the house lord is placed,
and what category the house belongs to.

HOUSE CATEGORIES (from classical Vedic astrology):
    - Kendra (angular):  1, 4, 7, 10 — pillars of the chart, strongest houses
    - Trikona (trinal):  1, 5, 9 — most auspicious houses (dharma, fortune)
    - Dusthana (malefic): 6, 8, 12 — houses of difficulty (enemies, death, loss)
    - Upachaya (growth): 3, 6, 10, 11 — houses that improve over time
    - Maraka (death):    2, 7 — houses associated with longevity threats

    Note: House 1 is both kendra AND trikona. When multiple categories apply,
    priority is: kendra > trikona > dusthana > upachaya > maraka > "neutral".

ASPECTS (Graha Drishti):
    All planets aspect the 7th house from their position. Additionally:
    - Mars aspects the 4th and 8th houses
    - Jupiter aspects the 5th and 9th houses
    - Saturn aspects the 3rd and 10th houses
    - Rahu/Ketu aspect the 5th and 9th houses (like Jupiter)

SOURCE REFERENCES:
    - BPHS Ch. 7: House significations
    - BPHS Ch. 26: Planetary aspects (Graha Drishti)

Example:
    >>> from vedic_calc.chart.houses import analyze_houses
    >>> analyses = analyze_houses(chart)
    >>> for h in analyses:
    ...     print(f"House {h.house_number}: {h.sign.name}, lord in house {h.lord_house}")
"""

from __future__ import annotations

from vedic_calc.core.constants import (
    DUSTHANA_HOUSES,
    GRAHA_DRISHTI,
    KENDRA_HOUSES,
    MARAKA_HOUSES,
    SIGN_LORDS,
    TRIKONA_HOUSES,
    UPACHAYA_HOUSES,
    Planet,
    Sign,
)
from vedic_calc.core.types import BirthChart, HouseAnalysis


def _get_house_category(house_number: int) -> str:
    """Determine the category of a house based on its number.

    Priority when a house belongs to multiple categories:
    kendra > trikona > dusthana > upachaya > maraka > "neutral".

    Args:
        house_number: House number (1-12).

    Returns:
        Category string: "kendra", "trikona", "dusthana", "upachaya",
        "maraka", or "neutral".
    """
    if house_number in KENDRA_HOUSES:
        return "kendra"
    if house_number in TRIKONA_HOUSES:
        return "trikona"
    if house_number in DUSTHANA_HOUSES:
        return "dusthana"
    if house_number in UPACHAYA_HOUSES:
        return "upachaya"
    if house_number in MARAKA_HOUSES:
        return "maraka"
    return "neutral"


def analyze_houses(chart: BirthChart) -> list[HouseAnalysis]:
    """Analyze all 12 houses in a birth chart.

    For each house, determines:
      - sign: which zodiac sign occupies the house
      - lord: ruling planet of that sign
      - lord_sign: which sign the lord is currently placed in
      - lord_house: which house the lord is placed in
      - occupants: which planets are sitting in this house
      - aspected_by: which planets cast an aspect on this house
      - category: kendra, trikona, dusthana, upachaya, maraka, or neutral

    Args:
        chart: A complete BirthChart with planetary positions and houses.

    Returns:
        A list of 12 HouseAnalysis objects (one per house, ordered 1-12).

    Example:
        >>> analyses = analyze_houses(chart)
        >>> analyses[0].house_number
        1
        >>> analyses[0].category
        'kendra'
    """
    # Build a lookup: sign → house number (for finding which house a planet is in)
    sign_to_house: dict[Sign, int] = {}
    for house in chart.houses:
        sign_to_house[house.sign] = house.house_number

    # Build a lookup: planet → house number (based on which house's sign matches)
    planet_house: dict[Planet, int] = {}
    for planet in Planet:
        pos = chart.planets[planet]
        if pos.sign in sign_to_house:
            planet_house[planet] = sign_to_house[pos.sign]

    results: list[HouseAnalysis] = []

    for house in chart.houses:
        house_num = house.house_number
        sign = house.sign
        lord = house.lord

        # Where is the lord placed?
        lord_pos = chart.planets[lord]
        lord_sign = lord_pos.sign
        lord_house = planet_house.get(lord, house_num)

        # Which planets occupy this house? (planet's sign == house's sign)
        occupants: list[Planet] = [
            planet for planet in Planet
            if chart.planets[planet].sign == sign
        ]

        # Which planets aspect this house?
        # For each planet, compute the house offset from the planet's house
        # to this house. If that offset is in the planet's GRAHA_DRISHTI list,
        # the planet aspects this house.
        aspected_by: list[Planet] = []
        for planet in Planet:
            if planet not in planet_house:
                continue
            p_house = planet_house[planet]
            # House offset: how many houses forward from the planet's house
            # to the target house (1-indexed, so same house = 0 is not an aspect).
            offset = ((house_num - p_house) % 12)
            if offset == 0:
                # Offset 0 means same house — not an aspect
                continue
            if planet in GRAHA_DRISHTI and offset in GRAHA_DRISHTI[planet]:
                aspected_by.append(planet)

        # House category
        category = _get_house_category(house_num)

        results.append(HouseAnalysis(
            house_number=house_num,
            sign=sign,
            lord=lord,
            lord_sign=lord_sign,
            lord_house=lord_house,
            occupants=occupants,
            aspected_by=aspected_by,
            category=category,
        ))

    return results
