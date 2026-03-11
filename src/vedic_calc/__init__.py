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

    >>> from vedic_calc import calculate_dasha
    >>> periods = calculate_dasha(chart)
    >>> periods[0].lord  # First mahadasha planet
    <Planet.MOON: 1>

    >>> from vedic_calc import calculate_panchanga
    >>> p = calculate_panchanga(2026, 3, 8, 19.076, 72.878, 5.5)
    >>> p.tithi_name
    'Shukla Dashami'

    >>> from vedic_calc import render_south_indian
    >>> print(render_south_indian(chart))
    ... (ASCII chart)
"""

from vedic_calc.core.types import (
    BirthChart,
    DashaPeriod,
    NakshatraInfo,
    PanchangaInfo,
    PlanetPosition,
)
from vedic_calc.chart.calculator import calculate_chart
from vedic_calc.chart.renderer import render_north_indian, render_south_indian, render_svg
from vedic_calc.dasha.calculator import calculate_dasha, get_current_dasha
from vedic_calc.panchanga.calculator import calculate_panchanga
from vedic_calc.compatibility.calculator import calculate_compatibility, CompatibilityResult
