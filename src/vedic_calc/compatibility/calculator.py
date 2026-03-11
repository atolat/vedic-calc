"""Ashtakoot Milan (8-fold compatibility) calculator.

Computes compatibility between two people based on their Moon nakshatras
and Moon signs. This is the traditional Vedic marriage compatibility system.

The 8 kuttas (dimensions) and their maximum points:
    1. Varna (1 pt)      — Spiritual/nature compatibility
    2. Vashya (2 pts)     — Mutual attraction/influence
    3. Tara (3 pts)       — Birth star harmony
    4. Yoni (4 pts)       — Physical/temperamental compatibility
    5. Graha Maitri (5 pts) — Planetary friendship (Moon sign lords)
    6. Gana (6 pts)       — Temperament match
    7. Bhakoot (7 pts)    — Moon sign relative position
    8. Nadi (8 pts)       — Health/constitutional compatibility

Total: 36 points. Traditionally, 18+ is considered acceptable for marriage.

Source: Muhurta Chintamani, Brihat Jataka, various classical texts.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from vedic_calc.core.constants import Nakshatra, Planet, Sign, SIGN_LORDS


# ---------------------------------------------------------------------------
# Lookup tables for Ashtakoot computation
# ---------------------------------------------------------------------------

# VARNA (spiritual nature) — 4 groups, repeating across 27 nakshatras
# Brahmin (highest) > Kshatriya > Vaishya > Shudra
# Assigned cyclically in groups of nakshatras.
# Source: Classical Ashtakoot tables.
_VARNA = {
    Nakshatra.ASHWINI: 3,       # Kshatriya
    Nakshatra.BHARANI: 4,       # Shudra
    Nakshatra.KRITTIKA: 1,      # Brahmin
    Nakshatra.ROHINI: 4,        # Shudra
    Nakshatra.MRIGASHIRA: 2,    # Vaishya
    Nakshatra.ARDRA: 4,         # Shudra
    Nakshatra.PUNARVASU: 2,     # Vaishya
    Nakshatra.PUSHYA: 3,        # Kshatriya
    Nakshatra.ASHLESHA: 4,      # Shudra
    Nakshatra.MAGHA: 3,         # Kshatriya
    Nakshatra.PURVA_PHALGUNI: 1,# Brahmin
    Nakshatra.UTTARA_PHALGUNI: 3,# Kshatriya
    Nakshatra.HASTA: 2,         # Vaishya
    Nakshatra.CHITRA: 4,        # Shudra
    Nakshatra.SWATI: 4,         # Shudra
    Nakshatra.VISHAKHA: 1,      # Brahmin
    Nakshatra.ANURADHA: 4,      # Shudra
    Nakshatra.JYESHTHA: 2,      # Vaishya
    Nakshatra.MOOLA: 4,         # Shudra
    Nakshatra.PURVA_ASHADHA: 1, # Brahmin
    Nakshatra.UTTARA_ASHADHA: 3,# Kshatriya
    Nakshatra.SHRAVANA: 4,      # Shudra
    Nakshatra.DHANISHTA: 2,     # Vaishya
    Nakshatra.SHATABHISHA: 4,   # Shudra
    Nakshatra.PURVA_BHADRAPADA: 1,# Brahmin
    Nakshatra.UTTARA_BHADRAPADA: 3,# Kshatriya
    Nakshatra.REVATI: 4,        # Shudra
}

_VARNA_NAMES = {1: "Brahmin", 2: "Vaishya", 3: "Kshatriya", 4: "Shudra"}

# VASHYA (mutual influence) groups — based on Moon sign
# Each sign belongs to one of 5 groups:
#   1=Manava (human), 2=Vanachara (wild), 3=Chatushpada (quadruped),
#   4=Jalchara (water), 5=Keeta (insect)
_VASHYA_GROUP = {
    Sign.ARIES: 3,       # Chatushpada
    Sign.TAURUS: 3,      # Chatushpada
    Sign.GEMINI: 1,      # Manava
    Sign.CANCER: 4,      # Jalchara
    Sign.LEO: 2,         # Vanachara
    Sign.VIRGO: 1,       # Manava
    Sign.LIBRA: 1,       # Manava
    Sign.SCORPIO: 5,     # Keeta
    Sign.SAGITTARIUS: 1, # Manava (first half human)
    Sign.CAPRICORN: 4,   # Jalchara (Makara = sea creature)
    Sign.AQUARIUS: 1,    # Manava
    Sign.PISCES: 4,      # Jalchara
}

# Vashya compatibility matrix: (group1, group2) -> points (0, 1, or 2)
# Same group = 2, food chain friendly = 1, hostile = 0
_VASHYA_SCORE = {
    (1, 1): 2, (1, 2): 0, (1, 3): 1, (1, 4): 1, (1, 5): 0,
    (2, 1): 0, (2, 2): 2, (2, 3): 1, (2, 4): 0, (2, 5): 0,
    (3, 1): 1, (3, 2): 0, (3, 3): 2, (3, 4): 1, (3, 5): 0,
    (4, 1): 1, (4, 2): 0, (4, 3): 1, (4, 4): 2, (4, 5): 0,
    (5, 1): 0, (5, 2): 0, (5, 3): 0, (5, 4): 0, (5, 5): 2,
}

# YONI (physical/temperamental compatibility)
# Each nakshatra is assigned an animal and gender (M/F).
# Format: (animal_index, gender) where gender: 0=Male, 1=Female
# Animals: 1=Horse, 2=Elephant, 3=Sheep, 4=Serpent, 5=Dog,
#          6=Cat, 7=Rat, 8=Cow, 9=Buffalo, 10=Tiger,
#          11=Deer, 12=Monkey, 13=Mongoose, 14=Lion
_YONI = {
    Nakshatra.ASHWINI: (1, 0),           # Horse M
    Nakshatra.BHARANI: (2, 0),           # Elephant M
    Nakshatra.KRITTIKA: (3, 1),          # Sheep F
    Nakshatra.ROHINI: (4, 0),            # Serpent M
    Nakshatra.MRIGASHIRA: (4, 1),        # Serpent F
    Nakshatra.ARDRA: (5, 1),             # Dog F
    Nakshatra.PUNARVASU: (6, 1),         # Cat F
    Nakshatra.PUSHYA: (3, 0),            # Sheep M
    Nakshatra.ASHLESHA: (6, 0),          # Cat M
    Nakshatra.MAGHA: (7, 0),             # Rat M
    Nakshatra.PURVA_PHALGUNI: (7, 1),    # Rat F
    Nakshatra.UTTARA_PHALGUNI: (8, 0),   # Cow M
    Nakshatra.HASTA: (9, 1),             # Buffalo F
    Nakshatra.CHITRA: (10, 1),           # Tiger F
    Nakshatra.SWATI: (9, 0),             # Buffalo M
    Nakshatra.VISHAKHA: (10, 0),         # Tiger M
    Nakshatra.ANURADHA: (11, 1),         # Deer F
    Nakshatra.JYESHTHA: (11, 0),         # Deer M
    Nakshatra.MOOLA: (5, 0),             # Dog M
    Nakshatra.PURVA_ASHADHA: (12, 0),    # Monkey M
    Nakshatra.UTTARA_ASHADHA: (13, 0),   # Mongoose M
    Nakshatra.SHRAVANA: (12, 1),         # Monkey F
    Nakshatra.DHANISHTA: (14, 1),        # Lion F
    Nakshatra.SHATABHISHA: (1, 1),       # Horse F
    Nakshatra.PURVA_BHADRAPADA: (14, 0), # Lion M
    Nakshatra.UTTARA_BHADRAPADA: (8, 1), # Cow F
    Nakshatra.REVATI: (2, 1),            # Elephant F
}

_YONI_ANIMAL_NAMES = {
    1: "Horse", 2: "Elephant", 3: "Sheep", 4: "Serpent", 5: "Dog",
    6: "Cat", 7: "Rat", 8: "Cow", 9: "Buffalo", 10: "Tiger",
    11: "Deer", 12: "Monkey", 13: "Mongoose", 14: "Lion",
}

# Yoni enemy pairs — natural enemies get 0 points
_YONI_ENEMIES = {
    frozenset({1, 9}),    # Horse vs Buffalo
    frozenset({2, 14}),   # Elephant vs Lion
    frozenset({3, 12}),   # Sheep vs Monkey
    frozenset({4, 13}),   # Serpent vs Mongoose
    frozenset({5, 11}),   # Dog vs Deer
    frozenset({6, 7}),    # Cat vs Rat
    frozenset({8, 10}),   # Cow vs Tiger
}

# GANA (temperament) — 3 types: Deva (divine), Manushya (human), Rakshasa (demon)
_GANA = {
    Nakshatra.ASHWINI: 1,          # Deva
    Nakshatra.BHARANI: 1,          # Deva  (Note: some texts say Manushya)
    Nakshatra.KRITTIKA: 3,         # Rakshasa
    Nakshatra.ROHINI: 2,           # Manushya
    Nakshatra.MRIGASHIRA: 1,       # Deva
    Nakshatra.ARDRA: 2,            # Manushya
    Nakshatra.PUNARVASU: 1,        # Deva
    Nakshatra.PUSHYA: 1,           # Deva
    Nakshatra.ASHLESHA: 3,         # Rakshasa
    Nakshatra.MAGHA: 3,            # Rakshasa
    Nakshatra.PURVA_PHALGUNI: 2,   # Manushya
    Nakshatra.UTTARA_PHALGUNI: 2,  # Manushya
    Nakshatra.HASTA: 1,            # Deva
    Nakshatra.CHITRA: 3,           # Rakshasa
    Nakshatra.SWATI: 1,            # Deva
    Nakshatra.VISHAKHA: 3,         # Rakshasa
    Nakshatra.ANURADHA: 1,         # Deva
    Nakshatra.JYESHTHA: 3,         # Rakshasa
    Nakshatra.MOOLA: 3,            # Rakshasa
    Nakshatra.PURVA_ASHADHA: 2,    # Manushya
    Nakshatra.UTTARA_ASHADHA: 2,   # Manushya
    Nakshatra.SHRAVANA: 1,         # Deva
    Nakshatra.DHANISHTA: 3,        # Rakshasa
    Nakshatra.SHATABHISHA: 3,      # Rakshasa
    Nakshatra.PURVA_BHADRAPADA: 2, # Manushya
    Nakshatra.UTTARA_BHADRAPADA: 2,# Manushya
    Nakshatra.REVATI: 1,           # Deva
}

_GANA_NAMES = {1: "Deva", 2: "Manushya", 3: "Rakshasa"}

# Gana compatibility: (groom_gana, bride_gana) -> points
_GANA_SCORE = {
    (1, 1): 6, (1, 2): 6, (1, 3): 1,
    (2, 1): 5, (2, 2): 6, (2, 3): 0,
    (3, 1): 1, (3, 2): 0, (3, 3): 6,
}

# NADI (health/constitution) — 3 types: Aadi (Vata), Madhya (Pitta), Antya (Kapha)
# Same nadi = 0 points (dosham — health risk), different = 8 points
_NADI = {
    Nakshatra.ASHWINI: 1,           # Aadi (Vata)
    Nakshatra.BHARANI: 2,           # Madhya (Pitta)
    Nakshatra.KRITTIKA: 3,          # Antya (Kapha)
    Nakshatra.ROHINI: 3,            # Antya
    Nakshatra.MRIGASHIRA: 2,        # Madhya
    Nakshatra.ARDRA: 1,             # Aadi
    Nakshatra.PUNARVASU: 1,         # Aadi
    Nakshatra.PUSHYA: 2,            # Madhya
    Nakshatra.ASHLESHA: 3,          # Antya
    Nakshatra.MAGHA: 1,             # Aadi
    Nakshatra.PURVA_PHALGUNI: 2,    # Madhya
    Nakshatra.UTTARA_PHALGUNI: 3,   # Antya
    Nakshatra.HASTA: 3,             # Antya
    Nakshatra.CHITRA: 2,            # Madhya
    Nakshatra.SWATI: 1,             # Aadi
    Nakshatra.VISHAKHA: 1,          # Aadi
    Nakshatra.ANURADHA: 2,          # Madhya
    Nakshatra.JYESHTHA: 3,          # Antya
    Nakshatra.MOOLA: 1,             # Aadi
    Nakshatra.PURVA_ASHADHA: 2,     # Madhya
    Nakshatra.UTTARA_ASHADHA: 3,    # Antya
    Nakshatra.SHRAVANA: 3,          # Antya
    Nakshatra.DHANISHTA: 2,         # Madhya
    Nakshatra.SHATABHISHA: 1,       # Aadi
    Nakshatra.PURVA_BHADRAPADA: 1,  # Aadi
    Nakshatra.UTTARA_BHADRAPADA: 2, # Madhya
    Nakshatra.REVATI: 3,            # Antya
}

_NADI_NAMES = {1: "Aadi (Vata)", 2: "Madhya (Pitta)", 3: "Antya (Kapha)"}

# GRAHA MAITRI — planetary friendship table
# 0=enemy, 1=neutral, 2=friend
_FRIENDSHIP = {
    Planet.SUN: {Planet.SUN: 2, Planet.MOON: 2, Planet.MARS: 2, Planet.MERCURY: 1,
                 Planet.JUPITER: 2, Planet.VENUS: 0, Planet.SATURN: 0},
    Planet.MOON: {Planet.SUN: 2, Planet.MOON: 2, Planet.MARS: 1, Planet.MERCURY: 2,
                  Planet.JUPITER: 1, Planet.VENUS: 1, Planet.SATURN: 1},
    Planet.MARS: {Planet.SUN: 2, Planet.MOON: 2, Planet.MARS: 2, Planet.MERCURY: 0,
                  Planet.JUPITER: 2, Planet.VENUS: 1, Planet.SATURN: 0},
    Planet.MERCURY: {Planet.SUN: 2, Planet.MOON: 0, Planet.MARS: 1, Planet.MERCURY: 2,
                     Planet.JUPITER: 1, Planet.VENUS: 2, Planet.SATURN: 1},
    Planet.JUPITER: {Planet.SUN: 2, Planet.MOON: 2, Planet.MARS: 2, Planet.MERCURY: 0,
                     Planet.JUPITER: 2, Planet.VENUS: 0, Planet.SATURN: 1},
    Planet.VENUS: {Planet.SUN: 0, Planet.MOON: 1, Planet.MARS: 1, Planet.MERCURY: 2,
                   Planet.JUPITER: 1, Planet.VENUS: 2, Planet.SATURN: 2},
    Planet.SATURN: {Planet.SUN: 0, Planet.MOON: 0, Planet.MARS: 0, Planet.MERCURY: 2,
                    Planet.JUPITER: 1, Planet.VENUS: 2, Planet.SATURN: 2},
}

# BHAKOOT — unfavorable Moon sign combinations (0 points)
# These sign distance pairs (counted from person1 to person2) are inauspicious:
#   2/12, 5/9, 6/8
_BHAKOOT_BAD_PAIRS = {
    frozenset({2, 12}),   # 2nd/12th from each other
    frozenset({5, 9}),    # 5th/9th
    frozenset({6, 8}),    # 6th/8th
}


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------

class KuttaScore(BaseModel, frozen=True):
    """Score for one of the 8 kuttas (dimensions)."""
    name: str
    obtained: float = Field(ge=0.0)
    maximum: float
    description: str = ""


class CompatibilityResult(BaseModel, frozen=True):
    """Result of Ashtakoot Milan compatibility analysis.

    Contains individual scores for all 8 kuttas and an overall assessment.
    Traditionally, 18+ out of 36 is considered acceptable for marriage.

    Score interpretation:
        0-17:  Not recommended — significant incompatibilities
        18-24: Acceptable — moderate compatibility
        25-32: Good — strong compatibility
        33-36: Excellent — exceptional compatibility
    """
    person1_nakshatra: Nakshatra
    person1_sign: Sign
    person2_nakshatra: Nakshatra
    person2_sign: Sign
    kuttas: list[KuttaScore]
    total_score: float = Field(ge=0.0, le=36.0)
    max_score: float = 36.0
    verdict: str


# ---------------------------------------------------------------------------
# Kutta calculators
# ---------------------------------------------------------------------------

def _calc_varna(nk1: Nakshatra, nk2: Nakshatra) -> KuttaScore:
    """Varna kutta: person1 varna >= person2 varna → 1 point."""
    v1, v2 = _VARNA[nk1], _VARNA[nk2]
    # Lower number = higher varna. Person1 (groom) should be >= person2 (bride).
    score = 1.0 if v1 <= v2 else 0.0
    return KuttaScore(
        name="Varna",
        obtained=score,
        maximum=1.0,
        description=f"{_VARNA_NAMES[v1]} & {_VARNA_NAMES[v2]}",
    )


def _calc_vashya(s1: Sign, s2: Sign) -> KuttaScore:
    """Vashya kutta: mutual influence based on Moon sign groups."""
    g1, g2 = _VASHYA_GROUP[s1], _VASHYA_GROUP[s2]
    score = float(_VASHYA_SCORE.get((g1, g2), 0))
    return KuttaScore(name="Vashya", obtained=score, maximum=2.0)


def _calc_tara(nk1: Nakshatra, nk2: Nakshatra) -> KuttaScore:
    """Tara kutta: birth star harmony.

    Count from person1's nakshatra to person2's, modulo 9.
    Remainders 3, 5, 7 are inauspicious. Check both directions.
    """
    diff_fwd = ((nk2 - nk1) % 27) + 1
    diff_rev = ((nk1 - nk2) % 27) + 1
    rem_fwd = diff_fwd % 9
    rem_rev = diff_rev % 9
    bad = {3, 5, 7}
    fwd_ok = rem_fwd not in bad
    rev_ok = rem_rev not in bad
    if fwd_ok and rev_ok:
        score = 3.0
    elif fwd_ok or rev_ok:
        score = 1.5
    else:
        score = 0.0
    return KuttaScore(name="Tara", obtained=score, maximum=3.0)


def _calc_yoni(nk1: Nakshatra, nk2: Nakshatra) -> KuttaScore:
    """Yoni kutta: physical/temperamental compatibility based on animal symbols."""
    a1, g1 = _YONI[nk1]
    a2, g2 = _YONI[nk2]
    animal1 = _YONI_ANIMAL_NAMES[a1]
    animal2 = _YONI_ANIMAL_NAMES[a2]
    desc = f"{animal1} & {animal2}"

    if a1 == a2:
        # Same animal — check gender
        score = 4.0 if g1 != g2 else 3.0
    elif frozenset({a1, a2}) in _YONI_ENEMIES:
        score = 0.0
    else:
        score = 2.0  # Neutral

    return KuttaScore(name="Yoni", obtained=score, maximum=4.0, description=desc)


def _calc_graha_maitri(s1: Sign, s2: Sign) -> KuttaScore:
    """Graha Maitri kutta: friendship between Moon sign lords."""
    lord1 = SIGN_LORDS[s1]
    lord2 = SIGN_LORDS[s2]

    if lord1 == lord2:
        score = 5.0
    else:
        f12 = _FRIENDSHIP.get(lord1, {}).get(lord2, 1)
        f21 = _FRIENDSHIP.get(lord2, {}).get(lord1, 1)
        total = f12 + f21
        if total >= 4:       # Both friends
            score = 5.0
        elif total == 3:     # One friend, one neutral
            score = 4.0
        elif total == 2:     # Both neutral
            score = 3.0
        elif total == 1:     # One neutral, one enemy
            score = 1.0
        else:                # Both enemies
            score = 0.0

    return KuttaScore(name="Graha Maitri", obtained=score, maximum=5.0)


def _calc_gana(nk1: Nakshatra, nk2: Nakshatra) -> KuttaScore:
    """Gana kutta: temperament match (Deva, Manushya, Rakshasa)."""
    g1, g2 = _GANA[nk1], _GANA[nk2]
    score = float(_GANA_SCORE.get((g1, g2), 0))
    return KuttaScore(
        name="Gana",
        obtained=score,
        maximum=6.0,
        description=f"{_GANA_NAMES[g1]} & {_GANA_NAMES[g2]}",
    )


def _calc_bhakoot(s1: Sign, s2: Sign) -> KuttaScore:
    """Bhakoot kutta: relative position of Moon signs.

    Certain sign distances (2/12, 5/9, 6/8) are considered inauspicious.
    Uses inclusive Jyotish counting: Aries to Aries = 1, Aries to Taurus = 2.
    """
    # Inclusive count: Aries(1) to Taurus(2) = 2nd
    diff = ((s2 - s1) % 12) + 1  # 1-12 inclusive
    rev_diff = ((s1 - s2) % 12) + 1
    # Normalize: if diff=13 (same sign), it's 1
    if diff > 12:
        diff = 1
    if rev_diff > 12:
        rev_diff = 1
    pair = frozenset({diff, rev_diff})

    if pair in _BHAKOOT_BAD_PAIRS:
        score = 0.0
    else:
        score = 7.0

    return KuttaScore(name="Bhakoot", obtained=score, maximum=7.0)


def _calc_nadi(nk1: Nakshatra, nk2: Nakshatra) -> KuttaScore:
    """Nadi kutta: health/constitutional compatibility.

    Same nadi = Nadi Dosha (0 points). Different nadi = 8 points.
    """
    n1, n2 = _NADI[nk1], _NADI[nk2]
    score = 0.0 if n1 == n2 else 8.0
    desc = f"{_NADI_NAMES[n1]} & {_NADI_NAMES[n2]}"
    if n1 == n2:
        desc += " (Nadi Dosha)"
    return KuttaScore(name="Nadi", obtained=score, maximum=8.0, description=desc)


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------

def calculate_compatibility(
    person1_nakshatra: Nakshatra,
    person1_sign: Sign,
    person2_nakshatra: Nakshatra,
    person2_sign: Sign,
) -> CompatibilityResult:
    """Calculate Ashtakoot Milan compatibility between two people.

    Computes all 8 kuttas (dimensions) and returns a detailed result.
    Both people's Moon nakshatra and Moon sign are required.

    Args:
        person1_nakshatra: Moon nakshatra of person 1 (traditionally groom).
        person1_sign: Moon sign of person 1.
        person2_nakshatra: Moon nakshatra of person 2 (traditionally bride).
        person2_sign: Moon sign of person 2.

    Returns:
        CompatibilityResult with all 8 kutta scores and total.
    """
    kuttas = [
        _calc_varna(person1_nakshatra, person2_nakshatra),
        _calc_vashya(person1_sign, person2_sign),
        _calc_tara(person1_nakshatra, person2_nakshatra),
        _calc_yoni(person1_nakshatra, person2_nakshatra),
        _calc_graha_maitri(person1_sign, person2_sign),
        _calc_gana(person1_nakshatra, person2_nakshatra),
        _calc_bhakoot(person1_sign, person2_sign),
        _calc_nadi(person1_nakshatra, person2_nakshatra),
    ]

    total = sum(k.obtained for k in kuttas)

    if total >= 33:
        verdict = "Excellent — exceptional compatibility"
    elif total >= 25:
        verdict = "Good — strong compatibility"
    elif total >= 18:
        verdict = "Acceptable — moderate compatibility"
    else:
        verdict = "Not recommended — significant incompatibilities"

    return CompatibilityResult(
        person1_nakshatra=person1_nakshatra,
        person1_sign=person1_sign,
        person2_nakshatra=person2_nakshatra,
        person2_sign=person2_sign,
        kuttas=kuttas,
        total_score=total,
        verdict=verdict,
    )
