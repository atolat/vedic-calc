"""Shared helper functions for chart analysis."""
from __future__ import annotations

from vedic_calc.core.constants import Planet, Sign
from vedic_calc.core.types import BirthChart


def sign_distance(from_sign: Sign, to_sign: Sign) -> int:
    """Inclusive Jyotish count from one sign to another (1-12).

    Aries to Aries = 1, Aries to Taurus = 2, etc.
    """
    return ((int(to_sign) - int(from_sign)) % 12) + 1


def planet_house(chart: BirthChart, planet: Planet) -> int:
    """Get the house number (1-12) where a planet is placed (whole-sign)."""
    planet_sign = chart.planets[planet].sign
    for house in chart.houses:
        if house.sign == planet_sign:
            return house.house_number
    return 1  # pragma: no cover
