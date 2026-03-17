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
from vedic_calc.compatibility.constants import (
    GANA as _GANA,
    GANA_NAMES as _GANA_NAMES,
    NADI as _NADI,
    NADI_NAMES as _NADI_NAMES,
    VARNA as _VARNA,
    VARNA_NAMES as _VARNA_NAMES,
    VASHYA_GROUP as _VASHYA_GROUP,
    YONI as _YONI,
    YONI_ANIMAL_NAMES as _YONI_ANIMAL_NAMES,
)

# Vashya compatibility matrix: (group1, group2) -> points (0, 1, or 2)
# Same group = 2, food chain friendly = 1, hostile = 0
_VASHYA_SCORE = {
    (1, 1): 2, (1, 2): 0, (1, 3): 1, (1, 4): 0.5, (1, 5): 0,
    (2, 1): 0, (2, 2): 2, (2, 3): 1, (2, 4): 0, (2, 5): 0,
    (3, 1): 1, (3, 2): 0, (3, 3): 2, (3, 4): 1, (3, 5): 0,
    (4, 1): 0.5, (4, 2): 0, (4, 3): 1, (4, 4): 2, (4, 5): 0,
    (5, 1): 0, (5, 2): 0, (5, 3): 0, (5, 4): 0, (5, 5): 2,
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

# Yoni unfriendly pairs — not enemies, but predator/prey or hostile → 1 point
# (Non-enemy, non-same pairs not in this set get 2 points)
_YONI_UNFRIENDLY = {
    frozenset({1, 8}),    # Horse vs Cow
    frozenset({1, 10}),   # Horse vs Tiger
    frozenset({1, 11}),   # Horse vs Deer
    frozenset({1, 14}),   # Horse vs Lion
    frozenset({3, 6}),    # Sheep vs Cat
    frozenset({3, 10}),   # Sheep vs Tiger
    frozenset({3, 14}),   # Sheep vs Lion
    frozenset({4, 6}),    # Serpent vs Cat
    frozenset({4, 7}),    # Serpent vs Rat
    frozenset({4, 8}),    # Serpent vs Cow
    frozenset({4, 9}),    # Serpent vs Buffalo
    frozenset({5, 7}),    # Dog vs Rat
    frozenset({5, 8}),    # Dog vs Cow
    frozenset({5, 10}),   # Dog vs Tiger
    frozenset({5, 14}),   # Dog vs Lion
    frozenset({6, 10}),   # Cat vs Tiger
    frozenset({6, 14}),   # Cat vs Lion
    frozenset({8, 11}),   # Cow vs Deer
    frozenset({8, 14}),   # Cow vs Lion
    frozenset({9, 10}),   # Buffalo vs Tiger
    frozenset({10, 11}),  # Tiger vs Deer
    frozenset({10, 13}),  # Tiger vs Mongoose
    frozenset({10, 14}),  # Tiger vs Lion
}

# Gana compatibility: (groom_gana, bride_gana) -> points
_GANA_SCORE = {
    (1, 1): 6, (1, 2): 6, (1, 3): 1,
    (2, 1): 5, (2, 2): 6, (2, 3): 0,
    (3, 1): 1, (3, 2): 0, (3, 3): 6,
}

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

def _calc_varna(s1: Sign, s2: Sign) -> KuttaScore:
    """Varna kutta: person1 varna >= person2 varna → 1 point."""
    v1, v2 = _VARNA[s1], _VARNA[s2]
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
    elif frozenset({a1, a2}) in _YONI_UNFRIENDLY:
        score = 1.0  # Unfriendly but not enemy
    else:
        score = 2.0  # Friendly/neutral

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
            score = 0.5
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
        _calc_varna(person1_sign, person2_sign),
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
