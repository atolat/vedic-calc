"""South Indian 10-factor compatibility (Porutham / Poruttam).

Computes compatibility between bride and groom based on Moon nakshatra
and Moon sign. This is the traditional South Indian marriage matching
system used primarily in Tamil Nadu, Kerala, and parts of Karnataka.

The 10 factors (each scored 0 or 1):
    1.  Dina        — Star compatibility (nakshatra count mod 9)
    2.  Gana        — Temperament (Deva / Manushya / Rakshasa)
    3.  Mahendra    — Prosperity and progeny
    4.  Stree Dirgha — Bride's welfare / longevity
    5.  Yoni        — Physical / temperamental compatibility
    6.  Rasi        — Moon sign harmony
    7.  Rasiyathipathi — Sign lord friendship
    8.  Vasya       — Mutual attraction / dominance
    9.  Rajju       — Longevity (mangalya balam)
    10. Vedha       — Affliction check

Source: Classical South Indian jyotish texts, Vivaha Porutham traditions.
"""

from __future__ import annotations

from vedic_calc.core.constants import (
    Nakshatra,
    Planet,
    Sign,
    PLANET_FRIENDSHIP,
    SIGN_LORDS,
)
from vedic_calc.core.types import BirthChart, PoruthamFactor, PoruthamResult


# ---------------------------------------------------------------------------
# Lookup tables
# ---------------------------------------------------------------------------

# Gana (temperament) — 1=Deva, 2=Manushya, 3=Rakshasa
_GANA: dict[Nakshatra, int] = {
    Nakshatra.ASHWINI: 1,
    Nakshatra.BHARANI: 2,
    Nakshatra.KRITTIKA: 3,
    Nakshatra.ROHINI: 2,
    Nakshatra.MRIGASHIRA: 1,
    Nakshatra.ARDRA: 2,
    Nakshatra.PUNARVASU: 1,
    Nakshatra.PUSHYA: 1,
    Nakshatra.ASHLESHA: 3,
    Nakshatra.MAGHA: 3,
    Nakshatra.PURVA_PHALGUNI: 2,
    Nakshatra.UTTARA_PHALGUNI: 2,
    Nakshatra.HASTA: 1,
    Nakshatra.CHITRA: 3,
    Nakshatra.SWATI: 1,
    Nakshatra.VISHAKHA: 3,
    Nakshatra.ANURADHA: 1,
    Nakshatra.JYESHTHA: 3,
    Nakshatra.MOOLA: 3,
    Nakshatra.PURVA_ASHADHA: 2,
    Nakshatra.UTTARA_ASHADHA: 2,
    Nakshatra.SHRAVANA: 1,
    Nakshatra.DHANISHTA: 3,
    Nakshatra.SHATABHISHA: 3,
    Nakshatra.PURVA_BHADRAPADA: 2,
    Nakshatra.UTTARA_BHADRAPADA: 2,
    Nakshatra.REVATI: 1,
}

_GANA_NAMES = {1: "Deva", 2: "Manushya", 3: "Rakshasa"}

# Gana compatibility: matched if same gana, Deva+Manushya, or Manushya+Deva.
# Rakshasa+Rakshasa also matches. Deva+Rakshasa and Manushya+Rakshasa do not.
_GANA_COMPAT: dict[tuple[int, int], bool] = {
    (1, 1): True,  (1, 2): True,  (1, 3): False,
    (2, 1): True,  (2, 2): True,  (2, 3): False,
    (3, 1): False, (3, 2): False, (3, 3): True,
}

# Yoni — animal and gender for each nakshatra
# Animals: 1=Horse, 2=Elephant, 3=Sheep, 4=Serpent, 5=Dog,
#          6=Cat, 7=Rat, 8=Cow, 9=Buffalo, 10=Tiger,
#          11=Deer, 12=Monkey, 13=Mongoose, 14=Lion
_YONI: dict[Nakshatra, tuple[int, int]] = {
    Nakshatra.ASHWINI: (1, 0),
    Nakshatra.BHARANI: (2, 0),
    Nakshatra.KRITTIKA: (3, 1),
    Nakshatra.ROHINI: (4, 0),
    Nakshatra.MRIGASHIRA: (4, 1),
    Nakshatra.ARDRA: (5, 1),
    Nakshatra.PUNARVASU: (6, 1),
    Nakshatra.PUSHYA: (3, 0),
    Nakshatra.ASHLESHA: (6, 0),
    Nakshatra.MAGHA: (7, 0),
    Nakshatra.PURVA_PHALGUNI: (7, 1),
    Nakshatra.UTTARA_PHALGUNI: (8, 0),
    Nakshatra.HASTA: (9, 1),
    Nakshatra.CHITRA: (10, 1),
    Nakshatra.SWATI: (9, 0),
    Nakshatra.VISHAKHA: (10, 0),
    Nakshatra.ANURADHA: (11, 1),
    Nakshatra.JYESHTHA: (11, 0),
    Nakshatra.MOOLA: (5, 0),
    Nakshatra.PURVA_ASHADHA: (12, 0),
    Nakshatra.UTTARA_ASHADHA: (13, 0),
    Nakshatra.SHRAVANA: (12, 1),
    Nakshatra.DHANISHTA: (14, 1),
    Nakshatra.SHATABHISHA: (1, 1),
    Nakshatra.PURVA_BHADRAPADA: (14, 0),
    Nakshatra.UTTARA_BHADRAPADA: (8, 1),
    Nakshatra.REVATI: (2, 1),
}

_YONI_ENEMIES: set[frozenset[int]] = {
    frozenset({1, 9}),    # Horse vs Buffalo
    frozenset({2, 14}),   # Elephant vs Lion
    frozenset({3, 12}),   # Sheep vs Monkey
    frozenset({4, 13}),   # Serpent vs Mongoose
    frozenset({5, 11}),   # Dog vs Deer
    frozenset({6, 7}),    # Cat vs Rat
    frozenset({8, 10}),   # Cow vs Tiger
}

# Vasya groups by Moon sign
# 1=Quadruped, 2=Human, 3=Water, 4=Wild, 5=Insect
_VASYA_GROUP: dict[Sign, int] = {
    Sign.ARIES: 1,
    Sign.TAURUS: 1,
    Sign.GEMINI: 2,
    Sign.CANCER: 3,
    Sign.LEO: 4,
    Sign.VIRGO: 2,
    Sign.LIBRA: 2,
    Sign.SCORPIO: 5,
    Sign.SAGITTARIUS: 2,
    Sign.CAPRICORN: 3,
    Sign.AQUARIUS: 2,
    Sign.PISCES: 3,
}

_VASYA_GROUP_NAMES = {
    1: "Quadruped", 2: "Human", 3: "Water", 4: "Wild", 5: "Insect",
}

# Vasya compatibility: same group or human-quadruped are compatible.
# Wild and insect are incompatible with everything except themselves.
_VASYA_COMPAT: dict[tuple[int, int], bool] = {
    (1, 1): True,  (1, 2): True,  (1, 3): False, (1, 4): False, (1, 5): False,
    (2, 1): True,  (2, 2): True,  (2, 3): True,  (2, 4): False, (2, 5): False,
    (3, 1): False, (3, 2): True,  (3, 3): True,  (3, 4): False, (3, 5): False,
    (4, 1): False, (4, 2): False, (4, 3): False, (4, 4): True,  (4, 5): False,
    (5, 1): False, (5, 2): False, (5, 3): False, (5, 4): False, (5, 5): True,
}

# Rajju groups — nakshatras classified into 5 body parts.
# If both nakshatras are in the same group, the match FAILS (inauspicious).
_RAJJU: dict[Nakshatra, str] = {
    Nakshatra.ASHWINI: "pada",
    Nakshatra.BHARANI: "kati",
    Nakshatra.KRITTIKA: "nabhi",
    Nakshatra.ROHINI: "kantha",
    Nakshatra.MRIGASHIRA: "siro",
    Nakshatra.ARDRA: "kantha",
    Nakshatra.PUNARVASU: "nabhi",
    Nakshatra.PUSHYA: "kati",
    Nakshatra.ASHLESHA: "pada",
    Nakshatra.MAGHA: "pada",
    Nakshatra.PURVA_PHALGUNI: "kati",
    Nakshatra.UTTARA_PHALGUNI: "nabhi",
    Nakshatra.HASTA: "kantha",
    Nakshatra.CHITRA: "siro",
    Nakshatra.SWATI: "kantha",
    Nakshatra.VISHAKHA: "nabhi",
    Nakshatra.ANURADHA: "kati",
    Nakshatra.JYESHTHA: "pada",
    Nakshatra.MOOLA: "pada",
    Nakshatra.PURVA_ASHADHA: "kati",
    Nakshatra.UTTARA_ASHADHA: "nabhi",
    Nakshatra.SHRAVANA: "kantha",
    Nakshatra.DHANISHTA: "siro",
    Nakshatra.SHATABHISHA: "kantha",
    Nakshatra.PURVA_BHADRAPADA: "nabhi",
    Nakshatra.UTTARA_BHADRAPADA: "kati",
    Nakshatra.REVATI: "pada",
}

_RAJJU_DISPLAY = {
    "pada": "Pada (foot)",
    "kati": "Kati (waist)",
    "nabhi": "Nabhi (navel)",
    "kantha": "Kantha (neck)",
    "siro": "Siro (head)",
}

# Vedha (affliction) pairs — if bride & groom nakshatras form a vedha
# pair, the match FAILS. Note: Hasta (13) has no vedha counterpart.
_VEDHA_PAIRS: set[frozenset[int]] = {
    frozenset({1, 18}),   # Ashwini — Jyeshtha
    frozenset({2, 17}),   # Bharani — Anuradha
    frozenset({3, 16}),   # Krittika — Vishakha
    frozenset({4, 15}),   # Rohini — Swati
    frozenset({5, 23}),   # Mrigashira — Dhanishta
    frozenset({6, 22}),   # Ardra — Shravana
    frozenset({7, 21}),   # Punarvasu — U.Ashadha
    frozenset({8, 20}),   # Pushya — P.Ashadha
    frozenset({9, 19}),   # Ashlesha — Moola
    frozenset({10, 27}),  # Magha — Revati
    frozenset({11, 26}),  # P.Phalguni — U.Bhadrapada
    frozenset({12, 25}),  # U.Phalguni — P.Bhadrapada
    frozenset({14, 24}),  # Chitra — Shatabhisha
}


# ---------------------------------------------------------------------------
# Individual factor calculators
# ---------------------------------------------------------------------------

def _dina_porutham(bride_nak: Nakshatra, groom_nak: Nakshatra) -> PoruthamFactor:
    """Dina Porutham: star compatibility via nakshatra count modulo 9.

    Count from bride's nakshatra to groom's. If remainder (mod 9) is
    2, 4, 6, 8, or 0 the factor is matched.
    """
    count = ((int(groom_nak) - int(bride_nak)) % 27) + 1
    remainder = count % 9
    matched = remainder in {0, 2, 4, 6, 8}
    return PoruthamFactor(
        name="Dina",
        matched=matched,
        score=1.0 if matched else 0.0,
        max_score=1.0,
        description=f"Count {count}, remainder {remainder}",
    )


def _gana_porutham(bride_nak: Nakshatra, groom_nak: Nakshatra) -> PoruthamFactor:
    """Gana Porutham: temperament match (Deva / Manushya / Rakshasa).

    Same gana, Deva+Manushya, or Rakshasa+Rakshasa are compatible.
    Deva+Rakshasa and Manushya+Rakshasa are not.
    """
    g_bride = _GANA[bride_nak]
    g_groom = _GANA[groom_nak]
    matched = _GANA_COMPAT[(g_bride, g_groom)]
    return PoruthamFactor(
        name="Gana",
        matched=matched,
        score=1.0 if matched else 0.0,
        max_score=1.0,
        description=f"{_GANA_NAMES[g_bride]} & {_GANA_NAMES[g_groom]}",
    )


def _mahendra_porutham(
    bride_nak: Nakshatra, groom_nak: Nakshatra,
) -> PoruthamFactor:
    """Mahendra Porutham: prosperity and progeny.

    Count from bride's nakshatra to groom's. Matched if count is
    4, 7, 10, 13, 16, 19, 22, or 25.
    """
    count = ((int(groom_nak) - int(bride_nak)) % 27) + 1
    matched = count in {4, 7, 10, 13, 16, 19, 22, 25}
    return PoruthamFactor(
        name="Mahendra",
        matched=matched,
        score=1.0 if matched else 0.0,
        max_score=1.0,
        description=f"Count {count}",
    )


def _stree_dirgha_porutham(
    bride_nak: Nakshatra, groom_nak: Nakshatra,
) -> PoruthamFactor:
    """Stree Dirgha Porutham: bride's welfare and longevity.

    Groom's nakshatra should be at least 9 nakshatras ahead of the
    bride's (counting forward), or they should share the same nakshatra.
    """
    count = (int(groom_nak) - int(bride_nak)) % 27
    matched = count >= 9 or count == 0
    return PoruthamFactor(
        name="Stree Dirgha",
        matched=matched,
        score=1.0 if matched else 0.0,
        max_score=1.0,
        description=f"Forward distance {count}",
    )


def _yoni_porutham(bride_nak: Nakshatra, groom_nak: Nakshatra) -> PoruthamFactor:
    """Yoni Porutham: physical / temperamental compatibility.

    Each nakshatra is assigned an animal symbol. Enemy animal pairs
    cause the factor to fail; all others pass.
    """
    a1, _ = _YONI[bride_nak]
    a2, _ = _YONI[groom_nak]
    is_enemy = frozenset({a1, a2}) in _YONI_ENEMIES
    matched = not is_enemy
    return PoruthamFactor(
        name="Yoni",
        matched=matched,
        score=1.0 if matched else 0.0,
        max_score=1.0,
        description="Enemy pair" if is_enemy else "Compatible",
    )


def _rasi_porutham(bride_sign: Sign, groom_sign: Sign) -> PoruthamFactor:
    """Rasi Porutham: Moon sign harmony.

    Count from bride's sign to groom's sign (inclusive Jyotish counting).
    Matched if the count is 1, 2, 3, 4, 5, or 7.
    Counts of 6, 8, 9, 10, 11, or 12 are not matched.
    """
    diff = ((int(groom_sign) - int(bride_sign)) % 12) + 1
    matched = diff in {1, 2, 3, 4, 5, 7}
    return PoruthamFactor(
        name="Rasi",
        matched=matched,
        score=1.0 if matched else 0.0,
        max_score=1.0,
        description=f"Sign distance {diff}",
    )


def _rasiyathipathi_porutham(
    bride_sign: Sign, groom_sign: Sign,
) -> PoruthamFactor:
    """Rasiyathipathi Porutham: sign lord friendship.

    The lords of both Moon signs should be the same planet, or mutually
    friendly / neutral (friendship >= 1 in both directions).
    """
    lord1 = SIGN_LORDS[bride_sign]
    lord2 = SIGN_LORDS[groom_sign]

    if lord1 == lord2:
        matched = True
        desc = f"Same lord ({lord1.name.title()})"
    else:
        f12 = PLANET_FRIENDSHIP.get(lord1, {}).get(lord2, 1)
        f21 = PLANET_FRIENDSHIP.get(lord2, {}).get(lord1, 1)
        matched = f12 >= 1 and f21 >= 1
        desc = f"{lord1.name.title()} & {lord2.name.title()}"

    return PoruthamFactor(
        name="Rasiyathipathi",
        matched=matched,
        score=1.0 if matched else 0.0,
        max_score=1.0,
        description=desc,
    )


def _vasya_porutham(bride_sign: Sign, groom_sign: Sign) -> PoruthamFactor:
    """Vasya Porutham: mutual attraction / dominance.

    Based on the vasya group of each Moon sign. Same group or
    compatible groups (e.g. Human + Quadruped) pass.
    """
    g1 = _VASYA_GROUP[bride_sign]
    g2 = _VASYA_GROUP[groom_sign]
    matched = _VASYA_COMPAT.get((g1, g2), False)
    return PoruthamFactor(
        name="Vasya",
        matched=matched,
        score=1.0 if matched else 0.0,
        max_score=1.0,
        description=(
            f"{_VASYA_GROUP_NAMES[g1]} & {_VASYA_GROUP_NAMES[g2]}"
        ),
    )


def _rajju_porutham(bride_nak: Nakshatra, groom_nak: Nakshatra) -> PoruthamFactor:
    """Rajju Porutham: longevity / mangalya balam.

    Nakshatras fall into 5 rajju groups (body parts). If both bride
    and groom share the SAME group, the factor FAILS (inauspicious).
    Different groups are auspicious.
    """
    r1 = _RAJJU[bride_nak]
    r2 = _RAJJU[groom_nak]
    matched = r1 != r2
    return PoruthamFactor(
        name="Rajju",
        matched=matched,
        score=1.0 if matched else 0.0,
        max_score=1.0,
        description=(
            f"{_RAJJU_DISPLAY[r1]} & {_RAJJU_DISPLAY[r2]}"
            + ("" if matched else " (same rajju — inauspicious)")
        ),
    )


def _vedha_porutham(bride_nak: Nakshatra, groom_nak: Nakshatra) -> PoruthamFactor:
    """Vedha Porutham: affliction check.

    Certain nakshatra pairs are mutually afflicting (vedha). If the
    bride's and groom's nakshatras form such a pair, the factor FAILS.
    """
    pair = frozenset({int(bride_nak), int(groom_nak)})
    is_vedha = pair in _VEDHA_PAIRS
    matched = not is_vedha
    return PoruthamFactor(
        name="Vedha",
        matched=matched,
        score=1.0 if matched else 0.0,
        max_score=1.0,
        description="Vedha pair (affliction)" if is_vedha else "No vedha",
    )


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------

def calculate_porutham(chart1: BirthChart, chart2: BirthChart) -> PoruthamResult:
    """Calculate South Indian 10-factor compatibility (Porutham).

    Evaluates all 10 porutham factors between two birth charts using
    the Moon nakshatra and Moon sign of each person. In the traditional
    system, chart1 is the bride and chart2 is the groom.

    Args:
        chart1: Birth chart of the bride.
        chart2: Birth chart of the groom.

    Returns:
        PoruthamResult with 10 factors, each scored 0 or 1.
    """
    moon1 = chart1.planets[Planet.MOON]
    moon2 = chart2.planets[Planet.MOON]

    bride_nak = moon1.nakshatra_info.nakshatra
    bride_sign = moon1.sign
    groom_nak = moon2.nakshatra_info.nakshatra
    groom_sign = moon2.sign

    factors: list[PoruthamFactor] = [
        _dina_porutham(bride_nak, groom_nak),
        _gana_porutham(bride_nak, groom_nak),
        _mahendra_porutham(bride_nak, groom_nak),
        _stree_dirgha_porutham(bride_nak, groom_nak),
        _yoni_porutham(bride_nak, groom_nak),
        _rasi_porutham(bride_sign, groom_sign),
        _rasiyathipathi_porutham(bride_sign, groom_sign),
        _vasya_porutham(bride_sign, groom_sign),
        _rajju_porutham(bride_nak, groom_nak),
        _vedha_porutham(bride_nak, groom_nak),
    ]

    matched_count = sum(1 for f in factors if f.matched)

    return PoruthamResult(
        factors=factors,
        matched_count=matched_count,
    )
