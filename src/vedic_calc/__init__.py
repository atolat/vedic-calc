"""
vedic-calc: Open-source Vedic astrology calculation library.

Built on the Swiss Ephemeris (pyswisseph) for precise astronomical calculations,
with a clean Pythonic API using Pydantic models.

Quick start:
    >>> from vedic_calc import calculate_chart
    >>> chart = calculate_chart(
    ...     year=1990, month=3, day=15,
    ...     hour=10, minute=30,
    ...     latitude=19.0760, longitude=72.8777,  # Mumbai
    ...     timezone_offset=5.5,  # IST
    ... )
    >>> print(chart.ascendant.sign)
    <Sign.GEMINI: 3>
"""

from vedic_calc.core.types import (
    BirthChart,
    DashaPeriod,
    NakshatraInfo,
    PanchangaInfo,
    PlanetPosition,
)
from vedic_calc.chart.calculator import calculate_chart
