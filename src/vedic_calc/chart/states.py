"""
Planet dignity and state calculator.

Determines the comprehensive state of each planet in a birth chart:
dignity (exalted, moolatrikona, own sign, friend, neutral, enemy, debilitated),
combustion status, retrograde status, and vargottama status.

DIGNITY HIERARCHY (checked in this order):
    1. Exalted      — planet is in its exaltation sign (strongest)
    2. Moolatrikona — planet is in its moolatrikona sign AND degree range
    3. Own sign     — planet is in a sign it rules
    4. Friend's sign — sign lord is a natural friend (PLANET_FRIENDSHIP == 2)
    5. Neutral sign  — sign lord is neutral (PLANET_FRIENDSHIP == 1)
    6. Enemy sign    — sign lord is an enemy (PLANET_FRIENDSHIP == 0)
    7. Debilitated   — planet is in its debilitation sign (weakest)

VARGOTTAMA:
    A planet is vargottama when it occupies the same sign in both the
    D1 (Rasi) chart and the D9 (Navamsa) chart. This is considered a
    significant strength — like being "confirmed" in its position.

SOURCE REFERENCES:
    - BPHS Ch. 3: Exaltation, debilitation, moolatrikona
    - BPHS Ch. 3, Verse 49-51: Dignity definitions
    - BPHS Ch. 6: Combustion
    - BPHS Ch. 4: Navamsa calculation

Example:
    >>> from vedic_calc.chart.states import calculate_planet_states
    >>> states = calculate_planet_states(chart)
    >>> for planet, state in states.items():
    ...     print(f"{planet.name}: {state.dignity}, combust={state.is_combust}")
"""

from __future__ import annotations

from vedic_calc.chart.combustion import calculate_combustion
from vedic_calc.core.constants import (
    DEBILITATION,
    EXALTATION,
    MOOLATRIKONA,
    PLANET_FRIENDSHIP,
    SIGN_LORDS,
    Planet,
    Sign,
)
from vedic_calc.core.types import BirthChart, PlanetState


# ---------------------------------------------------------------------------
# Navamsa (D9) helper
# ---------------------------------------------------------------------------

# Starting sign for navamsa calculation, keyed by element.
# Fire signs (1, 5, 9) start from Aries (1).
# Earth signs (2, 6, 10) start from Capricorn (10).
# Air signs (3, 7, 11) start from Libra (7).
# Water signs (4, 8, 12) start from Cancer (4).
_NAVAMSA_START: dict[int, int] = {
    1: 1,   # Fire → Aries
    2: 10,  # Earth → Capricorn
    3: 7,   # Air → Libra
    0: 4,   # Water → Cancer (element index 0 because 4 % 4 == 0, etc.)
}


def _get_navamsa_sign(sign: Sign, degree_in_sign: float) -> Sign:
    """Compute the Navamsa (D9) sign for a given D1 position.

    NAVAMSA FORMULA:
        Each sign (30 degrees) is divided into 9 parts of 3.333... degrees each.
        The part number (0-8) determines which navamsa sign the planet falls in.

        The starting sign depends on the element of the D1 sign:
          - Fire signs (Aries, Leo, Sagittarius) → start from Aries
          - Earth signs (Taurus, Virgo, Capricorn) → start from Capricorn
          - Air signs (Gemini, Libra, Aquarius) → start from Libra
          - Water signs (Cancer, Scorpio, Pisces) → start from Cancer

        navamsa_sign = ((start - 1 + part) % 12) + 1

    Args:
        sign: The D1 (Rasi) sign.
        degree_in_sign: Degree within that sign (0-30).

    Returns:
        The Navamsa (D9) sign.
    """
    # Which of the 9 parts (0-8) does this degree fall in?
    part = int(degree_in_sign / (30.0 / 9.0))
    part = min(part, 8)  # Clamp for edge case at exactly 30.0

    # Determine element: Fire=1, Earth=2, Air=3, Water=0 (mod 4)
    element_key = sign.value % 4
    start = _NAVAMSA_START[element_key]

    navamsa_value = ((start - 1 + part) % 12) + 1
    return Sign(navamsa_value)


# ---------------------------------------------------------------------------
# Dignity determination
# ---------------------------------------------------------------------------

def _determine_dignity(planet: Planet, sign: Sign, degree_in_sign: float) -> str:
    """Determine the dignity of a planet based on its sign and degree.

    Checks in order: exalted, moolatrikona, own sign, friend/neutral/enemy,
    debilitated. For Rahu/Ketu (no friendship data), only exaltation and
    debilitation are checked; otherwise defaults to "neutral".

    Args:
        planet: The planet to evaluate.
        sign: The sign the planet occupies.
        degree_in_sign: The degree within the sign (0-30).

    Returns:
        One of: "exalted", "moolatrikona", "own_sign", "friend",
        "neutral", "enemy", "debilitated".
    """
    # 1. Exalted — planet is in its exaltation sign
    if planet in EXALTATION and EXALTATION[planet][0] == sign:
        return "exalted"

    # 7. Debilitated — check early so Rahu/Ketu can return quickly
    #    (placed here in code but logically the lowest priority for
    #    Sun-Saturn; for Rahu/Ketu it's checked after exaltation)
    is_debilitated = (
        planet in DEBILITATION and DEBILITATION[planet][0] == sign
    )

    # For Rahu/Ketu: no friendship data, so only exalt/debilitate/neutral
    if planet in (Planet.RAHU, Planet.KETU):
        return "debilitated" if is_debilitated else "neutral"

    # 2. Moolatrikona — planet is in its moolatrikona sign AND degree range
    if planet in MOOLATRIKONA:
        mt_sign, mt_start, mt_end = MOOLATRIKONA[planet]
        if sign == mt_sign and mt_start <= degree_in_sign < mt_end:
            return "moolatrikona"

    # 3. Own sign — planet rules this sign
    sign_lord = SIGN_LORDS[sign]
    if sign_lord == planet:
        return "own_sign"

    # 4-6. Friend / neutral / enemy — based on natural friendship
    if planet in PLANET_FRIENDSHIP and sign_lord in PLANET_FRIENDSHIP[planet]:
        friendship = PLANET_FRIENDSHIP[planet][sign_lord]
        if friendship == 2:
            return "friend"
        if friendship == 1:
            return "neutral"
        if friendship == 0:
            # But check debilitation first — it takes lowest priority
            # conceptually, yet an enemy sign that is also the debilitation
            # sign should be "debilitated" (debilitation is worse).
            if is_debilitated:
                return "debilitated"
            return "enemy"

    # 7. Debilitated (fallback if not caught above)
    if is_debilitated:
        return "debilitated"

    # Default (should not normally be reached for Sun-Saturn)
    return "neutral"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def calculate_planet_states(chart: BirthChart) -> dict[Planet, PlanetState]:
    """Calculate the comprehensive state/dignity of every planet in a chart.

    For each of the 9 Vedic planets, this function determines:
      - dignity (exalted, moolatrikona, own_sign, friend, neutral, enemy, debilitated)
      - combustion status (is the planet too close to the Sun?)
      - retrograde status (is the planet moving backward?)
      - vargottama status (same sign in D1 and D9?)

    Args:
        chart: A complete BirthChart with planetary positions.

    Returns:
        A dict mapping each Planet to its PlanetState.

    Example:
        >>> states = calculate_planet_states(chart)
        >>> states[Planet.JUPITER].dignity
        'exalted'
        >>> states[Planet.SATURN].is_vargottama
        True
    """
    # Pre-compute combustion for all planets (returns list for Moon-Saturn)
    combustion_list = calculate_combustion(chart)
    combustion_map: dict[Planet, bool] = {}
    for status in combustion_list:
        combustion_map[status.planet] = status.is_combust

    results: dict[Planet, PlanetState] = {}

    for planet in Planet:
        pos = chart.planets[planet]
        sign = pos.sign
        degree_in_sign = pos.degree_in_sign
        sign_lord = SIGN_LORDS[sign]

        # Dignity
        dignity = _determine_dignity(planet, sign, degree_in_sign)

        # Combustion (Sun, Rahu, Ketu are never combust)
        is_combust = combustion_map.get(planet, False)

        # Vargottama: D1 sign == D9 (Navamsa) sign
        navamsa_sign = _get_navamsa_sign(sign, degree_in_sign)
        is_vargottama = sign == navamsa_sign

        results[planet] = PlanetState(
            planet=planet,
            dignity=dignity,
            is_combust=is_combust,
            is_retrograde=pos.is_retrograde,
            is_vargottama=is_vargottama,
            sign=sign,
            sign_lord=sign_lord,
        )

    return results
