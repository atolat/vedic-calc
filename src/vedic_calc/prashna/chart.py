"""Prashna (horary) chart casting.

A Prashna chart IS a regular birth chart, just cast for the moment
the question is asked rather than the moment of birth. This module
provides a thin wrapper around calculate_chart() for clarity.
"""

from __future__ import annotations

from vedic_calc.chart.calculator import calculate_chart
from vedic_calc.core.constants import Ayanamsa
from vedic_calc.core.types import BirthChart


def cast_prashna_chart(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    latitude: float,
    longitude: float,
    timezone_offset: float,
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI,
) -> BirthChart:
    """Cast a Prashna (horary) chart for the moment a question is asked.

    A Prashna chart is identical in structure to a birth chart — the only
    difference is semantic: it represents the "birth" of a question rather
    than a person. The ascendant, houses, and planet positions are all
    computed the same way.

    Args:
        year: Year the question is asked.
        month: Month (1-12).
        day: Day (1-31).
        hour: Hour in local time (0-23).
        minute: Minute (0-59).
        latitude: Location latitude.
        longitude: Location longitude.
        timezone_offset: UTC offset in hours.
        ayanamsa: Ayanamsa system (default Lahiri).

    Returns:
        A BirthChart representing the Prashna chart.
    """
    return calculate_chart(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        latitude=latitude,
        longitude=longitude,
        timezone_offset=timezone_offset,
        ayanamsa=ayanamsa,
    )
