"""
Arudha Pada calculator (Jaimini astrology).

WHAT ARE ARUDHA PADAS?
    Arudha Padas are a key concept in Jaimini astrology. The word "Arudha"
    means "mounted upon" or "projected image." An Arudha Pada is the
    reflection or external image of a house — how the world perceives the
    matters of that house, as opposed to the house itself which represents
    the actual reality.

    For example:
    - The 1st house shows who you really are.
    - The Arudha of the 1st house (Arudha Lagna / AL) shows how the
      world perceives you — your public image.
    - The 7th house shows your actual marriage/partnership.
    - The Arudha of the 7th house (Darapada / A7) shows how your
      marriage appears to the outside world.

FORMULA (from Brihat Parashara Hora Shastra, Ch. 29):
    For each house H:
    1. Find the lord of house H's sign.
    2. Find which sign the lord occupies in the chart.
    3. Count from house H's sign to the lord's sign (inclusive).
    4. Count the same number forward from the lord's sign.
       That sign is the Arudha Pada.
    5. Exception: If the Arudha falls in the same sign as house H,
       use the 10th sign from house H instead.
    6. Exception: If the Arudha falls in the 7th from house H,
       use the 4th sign from house H instead.

SOURCE: BPHS Ch. 29 (Arudha Padas / Padas of Houses).
"""

from __future__ import annotations

from vedic_calc.core.constants import Planet, Sign, SIGN_LORDS
from vedic_calc.core.types import ArudhaPada, BirthChart


# Names for specific Arudha Padas that have traditional designations.
_ARUDHA_NAMES: dict[int, str] = {
    1: "Arudha Lagna (AL)",
    2: "Dhana Pada (A2)",
    4: "Sukha Pada (A4)",
    5: "Mantra Pada (A5)",
    7: "Darapada (A7)",
    9: "Bhagya Pada (A9)",
    10: "Rajya Pada (A10)",
}


def calculate_arudha_padas(chart: BirthChart) -> list[ArudhaPada]:
    """Calculate the Arudha Pada for each of the 12 houses.

    ALGORITHM (for each house H = 1..12):
        1. house_sign = sign occupying house H
        2. lord = SIGN_LORDS[house_sign]   (always Sun-Saturn, never Rahu/Ketu)
        3. lord_sign = chart.planets[lord].sign
        4. count = ((lord_sign - house_sign) % 12) + 1
           This is the number of signs from house_sign to lord_sign (inclusive).
        5. arudha_sign = ((lord_sign - 1 + count - 1) % 12) + 1
           Count the same distance forward from lord_sign.
        6. If arudha_sign == house_sign  ->  use 10th from house_sign
        7. If arudha_sign == 7th from house_sign  ->  use 4th from house_sign

    Args:
        chart: A calculated BirthChart.

    Returns:
        List of 12 ArudhaPada objects (one per house).

    Example:
        >>> from vedic_calc import calculate_chart
        >>> chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
        >>> padas = calculate_arudha_padas(chart)
        >>> len(padas)
        12
        >>> padas[0].pada_name
        'Arudha Lagna (AL)'
    """
    padas: list[ArudhaPada] = []

    for house in chart.houses:
        house_sign = house.sign
        lord = house.lord  # Already from SIGN_LORDS, so always Sun-Saturn

        # Where is the lord placed in the chart?
        lord_sign = chart.planets[lord].sign

        # Count from house sign to lord's sign (inclusive, 1-based)
        count = ((lord_sign.value - house_sign.value) % 12) + 1

        # Count the same number forward from the lord's sign
        arudha_sign_value = ((lord_sign.value - 1 + count - 1) % 12) + 1
        arudha_sign = Sign(arudha_sign_value)

        # Exception 1: Arudha falls in the same sign as the house
        # -> use the 10th sign from the house sign instead
        if arudha_sign == house_sign:
            arudha_sign_value = ((house_sign.value - 1 + 9) % 12) + 1
            arudha_sign = Sign(arudha_sign_value)

        # Exception 2: Arudha falls in the 7th from the house sign
        # -> use the 4th sign from the house sign instead
        seventh_from_house = Sign(((house_sign.value - 1 + 6) % 12) + 1)
        if arudha_sign == seventh_from_house:
            arudha_sign_value = ((house_sign.value - 1 + 3) % 12) + 1
            arudha_sign = Sign(arudha_sign_value)

        # Determine the name for this Arudha Pada
        pada_name = _ARUDHA_NAMES.get(house.house_number, f"A{house.house_number}")

        padas.append(ArudhaPada(
            house_number=house.house_number,
            sign=arudha_sign,
            pada_name=pada_name,
        ))

    return padas
