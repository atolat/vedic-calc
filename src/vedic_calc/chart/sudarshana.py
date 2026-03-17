"""
Sudarshana Chakra (three-ring chart) calculator.

THE SUDARSHANA CHAKRA:
    Sudarshana Chakra ("beautiful to see") is a three-ring concentric chart
    used for timing predictions. Each ring is a full 12-house chart counted
    from a different reference point:

    1. Lagna Ring — houses counted from the Ascendant sign
    2. Moon Ring — houses counted from the Moon's sign
    3. Sun Ring — houses counted from the Sun's sign

    For annual predictions, each ring advances one house per year of age.
    Planets and transits are overlaid on all three rings simultaneously.

    When a house is activated in all three rings simultaneously (e.g., the
    2nd house from Lagna, Moon, and Sun all have the same transit), the
    results are amplified.

SOURCE: BPHS Chapter 31 (Sudarshana Chakra Dasha).
"""

from __future__ import annotations

from vedic_calc.core.constants import Planet, Sign
from vedic_calc.core.types import BirthChart, SudarshanaChakra, SudarshanaHouse


def _build_ring(chart: BirthChart, reference_sign: Sign) -> list[SudarshanaHouse]:
    """Build a 12-house ring starting from a reference sign.

    House 1 = reference sign, House 2 = next sign, etc. (modular 12).
    For each house, collect planets whose sign matches.

    Args:
        chart: The birth chart with planet positions.
        reference_sign: The starting sign for house 1.

    Returns:
        List of 12 SudarshanaHouse objects.
    """
    houses: list[SudarshanaHouse] = []

    for i in range(12):
        # Sign for this house: reference_sign + i (modular, 1-indexed)
        sign_value = ((reference_sign.value - 1 + i) % 12) + 1
        sign = Sign(sign_value)

        # Collect planets in this sign
        planets_in_sign: list[Planet] = []
        for planet, position in chart.planets.items():
            if position.sign == sign:
                planets_in_sign.append(planet)

        houses.append(SudarshanaHouse(
            house_number=i + 1,
            sign=sign,
            planets=planets_in_sign,
        ))

    return houses


def calculate_sudarshana_chakra(chart: BirthChart) -> SudarshanaChakra:
    """Calculate the Sudarshana Chakra (three concentric rings).

    Builds three 12-house rings from the Lagna (ascendant), Moon, and Sun
    signs respectively, each with planets placed according to their sign.

    Args:
        chart: A calculated BirthChart (from calculate_chart()).

    Returns:
        SudarshanaChakra with lagna_ring, moon_ring, and sun_ring.

    Example:
        >>> chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
        >>> chakra = calculate_sudarshana_chakra(chart)
        >>> len(chakra.lagna_ring)
        12
    """
    lagna_sign = chart.ascendant.sign
    moon_sign = chart.planets[Planet.MOON].sign
    sun_sign = chart.planets[Planet.SUN].sign

    return SudarshanaChakra(
        lagna_ring=_build_ring(chart, lagna_sign),
        moon_ring=_build_ring(chart, moon_sign),
        sun_ring=_build_ring(chart, sun_sign),
    )
