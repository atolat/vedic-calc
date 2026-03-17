"""
KP (Krishnamurti Paddhati) astrology module.

KP is a refined predictive system developed by Prof. K.S. Krishnamurti
(1908-1972) that combines Vedic astrology with Western house cusps.
It is especially popular in South India for precise event timing.

Key features:
    - Sub-lord system: finer than nakshatra-level analysis
    - Placidus house cusps: unequal houses based on birth location
    - Significator-based prediction: systematic house signification
    - Ruling planets: timing tool for event prediction

Usage:
    >>> from vedic_calc.kp import calculate_kp_chart, get_kp_sublord
    >>> result = calculate_kp_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.8777, 5.5)
    >>> sublord = get_kp_sublord(45.0)
"""

from vedic_calc.kp.sublords import get_kp_sublord
from vedic_calc.kp.houses import calculate_kp_houses
from vedic_calc.kp.calculator import calculate_kp_chart

__all__ = [
    "get_kp_sublord",
    "calculate_kp_houses",
    "calculate_kp_chart",
]
