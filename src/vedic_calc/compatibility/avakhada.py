"""Avakhada (birth summary) table calculator.

The Avakhada table is a standalone birth summary extracted from the Moon's
nakshatra, pada, and sign. It provides key attributes used in compatibility
matching and traditional naming.

Source: Standard Jyotish Avakhada Chakra references.
"""

from __future__ import annotations

from vedic_calc.core.constants import Nakshatra, Planet, Sign, SIGN_LORDS
from vedic_calc.core.types import AvakhadaInfo
from vedic_calc.compatibility.constants import (
    GANA,
    GANA_NAMES,
    NADI,
    NADI_NAMES,
    NAKSHATRA_LORDS,
    NAKSHATRA_NAME_LETTERS,
    PAYA,
    TATVA,
    VARNA,
    VARNA_NAMES,
    VASHYA_GROUP,
    VASHYA_NAMES,
    YONI,
    YONI_ANIMAL_NAMES,
)


def calculate_avakhada(nakshatra: Nakshatra, pada: int, sign: Sign) -> AvakhadaInfo:
    """Calculate the Avakhada (birth summary) table for a given nakshatra, pada, and sign.

    The Avakhada table summarises key birth attributes derived purely from the
    Moon's nakshatra/pada and sign. It is used for compatibility analysis,
    traditional naming, and quick chart summaries.

    Args:
        nakshatra: Moon's birth nakshatra (1-27).
        pada: Pada (quarter) within the nakshatra (1-4).
        sign: Moon's zodiac sign.

    Returns:
        AvakhadaInfo with all birth summary attributes.

    Example:
        >>> from vedic_calc.core.constants import Nakshatra, Sign
        >>> info = calculate_avakhada(Nakshatra.ASHWINI, 1, Sign.ARIES)
        >>> info.varna
        'Kshatriya'
        >>> info.name_letter
        'Chu'
    """
    if not 1 <= pada <= 4:
        msg = f"pada must be 1-4, got {pada}"
        raise ValueError(msg)

    nak_num = int(nakshatra)  # 1-27
    sign_num = int(sign)      # 1-12

    # Varna (from sign)
    varna = VARNA_NAMES[VARNA[sign]]

    # Vashya (from sign)
    vashya = VASHYA_NAMES[VASHYA_GROUP[sign]]

    # Yoni (from nakshatra)
    animal_idx, _gender = YONI[nakshatra]
    yoni = YONI_ANIMAL_NAMES[animal_idx]

    # Gana (from nakshatra)
    gana = GANA_NAMES[GANA[nakshatra]]

    # Nadi (from nakshatra)
    nadi = NADI_NAMES[NADI[nakshatra]]

    # Nakshatra lord
    nakshatra_lord = Planet(NAKSHATRA_LORDS[nak_num])

    # Sign lord
    sign_lord = SIGN_LORDS[sign]

    # Name letter
    name_letter = NAKSHATRA_NAME_LETTERS[(nak_num, pada)]

    # Tatva (element from sign)
    tatva = TATVA[sign_num]

    # Yunja (based on pada)
    if pada == 1:
        yunja = "Poorva"
    elif pada in (2, 3):
        yunja = "Madhya"
    else:
        yunja = "Antya"

    # Paya (from nakshatra)
    paya = PAYA[nak_num]

    return AvakhadaInfo(
        varna=varna,
        vashya=vashya,
        yoni=yoni,
        gana=gana,
        nadi=nadi,
        nakshatra_lord=nakshatra_lord,
        sign_lord=sign_lord,
        name_letter=name_letter,
        tatva=tatva,
        yunja=yunja,
        paya=paya,
    )
