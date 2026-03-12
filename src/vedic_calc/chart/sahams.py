"""
Saham (Arabic Part / Sensitive Point) calculator.

WHAT ARE SAHAMS?
    Sahams (also called "Arabic Parts" or "Lots") are sensitive points in
    a chart, calculated by combining the longitudes of three chart factors
    (typically two planets and the ascendant) using simple arithmetic:

        Saham = A + B - C   (mod 360)

    Each Saham represents a specific life theme. For example:
    - Punya Saham (Spiritual Merit) = Moon + Sun - Ascendant
    - Vivaha Saham (Marriage)       = Venus + Saturn - Ascendant

    Sahams originated in Hellenistic astrology and were later adopted into
    Tajika (Indo-Persian) astrology, which became an important branch of
    Indian astrology from the medieval period onward.

WHY THEY MATTER:
    The sign and degree where a Saham falls indicates influences on that
    life area. Transits and dashas activating the Saham's sign can trigger
    events related to its theme.

SOURCE: Tajika Neelakanthi, various Tajika texts.
"""

from __future__ import annotations

from vedic_calc.chart.calculator import longitude_to_degree_in_sign, longitude_to_sign
from vedic_calc.core.constants import Planet, SAHAM_FORMULAS
from vedic_calc.core.types import BirthChart, SahamPosition


def _get_longitude(chart: BirthChart, name: str) -> float:
    """Resolve a formula component name to a longitude value.

    Args:
        chart: The birth chart.
        name: One of "SUN", "MOON", "MARS", etc. or "ASC" for the ascendant.

    Returns:
        The sidereal longitude in degrees (0-360).
    """
    if name == "ASC":
        return chart.ascendant.longitude
    return chart.planets[Planet[name]].longitude


def calculate_sahams(chart: BirthChart) -> list[SahamPosition]:
    """Calculate all Sahams (Arabic Parts) for a birth chart.

    FORMULA:
        For each (name, A, B, C) in SAHAM_FORMULAS:
            saham_longitude = (longitude_of_A + longitude_of_B - longitude_of_C) % 360

    The formula components are planet names ("SUN", "MOON", etc.) or "ASC"
    for the ascendant. See SAHAM_FORMULAS in constants.py for all definitions.

    Args:
        chart: A calculated BirthChart.

    Returns:
        List of SahamPosition objects, one per formula in SAHAM_FORMULAS.

    Example:
        >>> from vedic_calc import calculate_chart
        >>> chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
        >>> sahams = calculate_sahams(chart)
        >>> len(sahams) > 0
        True
        >>> sahams[0].name
        'Punya'
    """
    results: list[SahamPosition] = []

    for name, a_name, b_name, c_name in SAHAM_FORMULAS:
        lon_a = _get_longitude(chart, a_name)
        lon_b = _get_longitude(chart, b_name)
        lon_c = _get_longitude(chart, c_name)

        saham_longitude = (lon_a + lon_b - lon_c) % 360.0

        results.append(SahamPosition(
            name=name,
            longitude=round(saham_longitude, 4),
            sign=longitude_to_sign(saham_longitude),
            degree_in_sign=round(longitude_to_degree_in_sign(saham_longitude), 4),
        ))

    return results
