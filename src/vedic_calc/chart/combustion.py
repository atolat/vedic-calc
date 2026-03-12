"""
Planetary combustion (Asta) calculator.

A planet is "combust" (asta) when it is too close to the Sun. The Sun's
intense brilliance overwhelms the planet's significations, weakening it.
Each planet has a specific angular threshold — if the planet is within
that many degrees of the Sun, it is considered combust.

RETROGRADE MATTERS:
    Some planets have different combustion thresholds when retrograde.
    For example, Mercury's threshold is 14° direct but 12° retrograde.
    Retrograde planets are closer to Earth (and thus brighter), so they
    can withstand the Sun's influence at a slightly closer distance.

WHICH PLANETS CAN BE COMBUST?
    Only Moon, Mars, Mercury, Jupiter, Venus, and Saturn. The Sun itself
    cannot be combust (it IS the combustion source), and Rahu/Ketu are
    shadow planets (mathematical points, not physical bodies).

SOURCE REFERENCES:
    - BPHS Ch. 6, verses 6-9: Combustion thresholds
    - Surya Siddhanta: Angular distance calculations

Example:
    >>> from vedic_calc.chart.combustion import calculate_combustion
    >>> statuses = calculate_combustion(chart)
    >>> for s in statuses:
    ...     print(f"{s.planet.name}: combust={s.is_combust}, dist={s.distance_from_sun:.1f}°")
"""

from __future__ import annotations

from vedic_calc.core.constants import COMBUSTION_THRESHOLD, Planet
from vedic_calc.core.types import BirthChart, CombustionStatus


def calculate_combustion(chart: BirthChart) -> list[CombustionStatus]:
    """Calculate combustion status for all applicable planets.

    Computes the angular distance between each planet and the Sun,
    compares it to the planet-specific threshold (adjusted for
    retrograde status), and returns a CombustionStatus for each.

    Args:
        chart: A complete BirthChart with planetary positions.

    Returns:
        A list of CombustionStatus for Moon, Mars, Mercury, Jupiter,
        Venus, and Saturn (in Planet enum order).
    """
    sun_lon = chart.planets[Planet.SUN].longitude
    results: list[CombustionStatus] = []

    for planet, (direct_threshold, retro_threshold) in COMBUSTION_THRESHOLD.items():
        pos = chart.planets[planet]
        planet_lon = pos.longitude

        # Angular distance on the circle (always 0-180).
        raw_diff = abs(planet_lon - sun_lon)
        distance = min(raw_diff, 360.0 - raw_diff)

        threshold = retro_threshold if pos.is_retrograde else direct_threshold

        results.append(
            CombustionStatus(
                planet=planet,
                is_combust=distance < threshold,
                distance_from_sun=round(distance, 4),
                threshold=threshold,
            )
        )

    return results
