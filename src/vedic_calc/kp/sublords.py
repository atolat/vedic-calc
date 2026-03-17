"""
KP (Krishnamurti Paddhati) Sub-Lord calculation.

In KP astrology, each nakshatra (13°20') is divided into 9 unequal
sub-divisions. The size of each sub is proportional to the Vimsottari
dasha years of the ruling planet:

    Ketu=7, Venus=20, Sun=6, Moon=10, Mars=7,
    Rahu=18, Jupiter=16, Saturn=19, Mercury=17  (total=120)

The sub-lord sequence within a nakshatra starts from the nakshatra's
own lord and follows the Vimsottari order cyclically.

Example for Ashwini (lord = Ketu):
    Sub sequence: Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury
    Sub spans:    (7/120)*13.333, (20/120)*13.333, (6/120)*13.333, ...

Example for Bharani (lord = Venus):
    Sub sequence: Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury, Ketu
    (starts from Venus, wraps around)

The sub-sub lord is computed by applying the same proportional division
one level deeper within the sub.
"""

from __future__ import annotations

from vedic_calc.core.constants import (
    Nakshatra,
    Planet,
    Sign,
    NAKSHATRA_LORDS,
    NAKSHATRA_SPAN,
    SIGN_LORDS,
    VIMSOTTARI_ORDER,
    VIMSOTTARI_YEARS,
    VIMSOTTARI_TOTAL_YEARS,
)
from vedic_calc.core.types import KPSublordInfo


def _get_vimsottari_sequence_from(start_lord: Planet) -> list[Planet]:
    """Return the 9-planet Vimsottari sequence starting from a given lord.

    The sequence wraps around cyclically. For example, if start_lord is
    Jupiter, the sequence is:
        Jupiter, Saturn, Mercury, Ketu, Venus, Sun, Moon, Mars, Rahu
    """
    idx = VIMSOTTARI_ORDER.index(start_lord)
    return [VIMSOTTARI_ORDER[(idx + i) % 9] for i in range(9)]


def _find_sub_lord(degree_in_nakshatra: float, star_lord: Planet) -> tuple[Planet, float, float]:
    """Find the sub-lord for a degree within a nakshatra.

    Args:
        degree_in_nakshatra: Position within the nakshatra (0 to ~13.333).
        star_lord: The nakshatra lord (determines the sub sequence start).

    Returns:
        Tuple of (sub_lord, degree_within_sub, sub_span_degrees).
    """
    sequence = _get_vimsottari_sequence_from(star_lord)
    accumulated = 0.0
    for planet in sequence:
        sub_span = (VIMSOTTARI_YEARS[planet] / VIMSOTTARI_TOTAL_YEARS) * NAKSHATRA_SPAN
        if accumulated + sub_span > degree_in_nakshatra or planet == sequence[-1]:
            degree_in_sub = degree_in_nakshatra - accumulated
            return planet, degree_in_sub, sub_span
        accumulated += sub_span
    # Fallback (should not reach here)
    return sequence[-1], 0.0, 0.0  # pragma: no cover


def _find_sub_sub_lord(degree_in_sub: float, sub_span: float, sub_lord: Planet) -> Planet:
    """Find the sub-sub-lord within a sub-division.

    Same proportional logic applied one level deeper: the sub is divided
    into 9 parts proportional to Vimsottari years, starting from the sub-lord.

    Args:
        degree_in_sub: Position within the sub (0 to sub_span).
        sub_span: Total span of the sub in degrees.
        sub_lord: The sub-lord (determines the sub-sub sequence start).

    Returns:
        The sub-sub-lord Planet.
    """
    sequence = _get_vimsottari_sequence_from(sub_lord)
    accumulated = 0.0
    for planet in sequence:
        sub_sub_span = (VIMSOTTARI_YEARS[planet] / VIMSOTTARI_TOTAL_YEARS) * sub_span
        if accumulated + sub_sub_span > degree_in_sub or planet == sequence[-1]:
            return planet
        accumulated += sub_sub_span
    return sequence[-1]  # pragma: no cover


def get_kp_sublord(longitude: float) -> KPSublordInfo:
    """Get the sign lord, star lord, sub lord, and sub-sub lord for a longitude.

    This is the core KP calculation. For any sidereal longitude (0-360),
    it determines the four levels of lordship:
        1. Sign lord (rashi lord) -- which of the 12 signs
        2. Star lord (nakshatra lord) -- which of the 27 nakshatras
        3. Sub lord -- which sub-division within the nakshatra
        4. Sub-sub lord -- which sub-sub-division within the sub

    Args:
        longitude: Sidereal longitude in degrees (0-360).

    Returns:
        KPSublordInfo with all four lord levels.

    Example:
        >>> info = get_kp_sublord(0.0)  # 0 degrees Aries
        >>> info.sign_lord  # Mars rules Aries
        4  # Planet.MARS
    """
    # Normalize longitude
    longitude = longitude % 360.0

    # Sign
    sign_index = min(int(longitude / 30.0) + 1, 12)
    sign = Sign(sign_index)
    sign_lord = SIGN_LORDS[sign]

    # Nakshatra (star)
    nak_index = min(int(longitude / NAKSHATRA_SPAN), 26)
    nakshatra = Nakshatra(nak_index + 1)
    star_lord = NAKSHATRA_LORDS[nakshatra]

    # Degree within nakshatra
    degree_in_nak = longitude - (nak_index * NAKSHATRA_SPAN)

    # Sub lord
    sub_lord, degree_in_sub, sub_span = _find_sub_lord(degree_in_nak, star_lord)

    # Sub-sub lord
    sub_sub_lord = _find_sub_sub_lord(degree_in_sub, sub_span, sub_lord)

    return KPSublordInfo(
        longitude=round(longitude, 4),
        sign=sign.value,
        sign_lord=sign_lord.value,
        star_lord=star_lord.value,
        sub_lord=sub_lord.value,
        sub_sub_lord=sub_sub_lord.value,
    )
