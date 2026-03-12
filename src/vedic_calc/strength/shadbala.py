"""
Shadbala (six-fold strength) calculation for Vedic astrology.

Shadbala ("shad" = six, "bala" = strength) quantifies a planet's total
strength by combining six distinct factors. It is one of the most
comprehensive strength metrics in classical Jyotish, described in detail
in BPHS Chapter 27.

The six components (all measured in Shashtiamsas = 1/60 Rupa):
    1. Sthana Bala — Positional strength (sign placement, dignity, etc.)
    2. Dig Bala    — Directional strength (which house the planet occupies)
    3. Kaala Bala  — Temporal strength (day/night birth, planetary hour, etc.)
    4. Chesta Bala — Motional strength (retrograde, direct, stationary)
    5. Naisargika Bala — Natural/inherent strength (fixed per planet)
    6. Drik Bala   — Aspectual strength (benefic/malefic aspects received)

Only the seven visible planets (Sun through Saturn) are included in
Shadbala. Rahu and Ketu, being shadow planets (lunar nodes), are excluded.

Reference: Brihat Parashara Hora Shastra (BPHS), Chapter 27.
"""

from __future__ import annotations

from vedic_calc.core.constants import (
    DEBILITATION,
    DIG_BALA_HOUSES,
    EXALTATION,
    GRAHA_DRISHTI,
    MOOLATRIKONA,
    NAISARGIKA_BALA,
    PLANET_FRIENDSHIP,
    SIGN_LORDS,
    Planet,
    Sign,
)
from vedic_calc.core.types import BirthChart, ShadbalaResult

# The seven planets included in Shadbala (Rahu/Ketu excluded).
_SHADBALA_PLANETS: list[Planet] = [
    Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
    Planet.JUPITER, Planet.VENUS, Planet.SATURN,
]

# Minimum required Shadbala (in Shashtiamsas) for a planet to be
# considered "strong". A simplified uniform threshold is used here;
# classical texts prescribe per-planet minimums (Sun=390, Moon=360, etc.).
_STRENGTH_THRESHOLD: float = 300.0


# ---------------------------------------------------------------------------
# Helper: find which house a planet occupies
# ---------------------------------------------------------------------------

def _planet_house(planet_sign: Sign, houses: list) -> int:
    """Return the house number (1-12) occupied by a planet in the given sign."""
    for house in houses:
        if house.sign == planet_sign:
            return house.house_number
    # Fallback (should not happen with a valid chart).
    return 1


# ---------------------------------------------------------------------------
# Helper: compute the absolute longitude from sign + degree
# ---------------------------------------------------------------------------

def _absolute_longitude(sign: Sign, degree: float) -> float:
    """Convert a (sign, degree_in_sign) pair to absolute longitude (0-360)."""
    return (int(sign) - 1) * 30.0 + degree


# ---------------------------------------------------------------------------
# Helper: determine a planet's dignity in its current sign
# ---------------------------------------------------------------------------

def _get_dignity(planet: Planet, sign: Sign, degree_in_sign: float) -> str:
    """Return the dignity of a planet: one of 'exalted', 'moolatrikona',
    'own_sign', 'friend', 'neutral', 'enemy', or 'debilitated'.
    """
    # Check exaltation
    if planet in EXALTATION:
        exalt_sign, _ = EXALTATION[planet]
        if sign == exalt_sign:
            return "exalted"

    # Check debilitation
    if planet in DEBILITATION:
        deb_sign, _ = DEBILITATION[planet]
        if sign == deb_sign:
            return "debilitated"

    # Check moolatrikona
    if planet in MOOLATRIKONA:
        mt_sign, mt_start, mt_end = MOOLATRIKONA[planet]
        if sign == mt_sign and mt_start <= degree_in_sign < mt_end:
            return "moolatrikona"

    # Check own sign
    sign_lord = SIGN_LORDS[sign]
    if sign_lord == planet:
        return "own_sign"

    # Check friendship with sign lord
    if planet in PLANET_FRIENDSHIP and sign_lord in PLANET_FRIENDSHIP[planet]:
        friendship = PLANET_FRIENDSHIP[planet][sign_lord]
        if friendship == 2:
            return "friend"
        if friendship == 1:
            return "neutral"
        return "enemy"

    return "neutral"


# ---------------------------------------------------------------------------
# 1. Sthana Bala (Positional Strength)
# ---------------------------------------------------------------------------

def _sthana_bala(planet: Planet, chart: BirthChart) -> float:
    """Compute Sthana Bala — the sum of five positional sub-strengths."""
    pos = chart.planets[planet]

    # (a) Uchcha Bala — distance from debilitation point
    deb_sign, deb_deg = DEBILITATION[planet]
    deb_longitude = _absolute_longitude(deb_sign, deb_deg)
    dist = abs(pos.longitude - deb_longitude)
    if dist > 180.0:
        dist = 360.0 - dist
    uchcha_bala = dist / 3.0  # max 60 when 180° from debilitation

    # (b) Saptavargaja Bala — simplified dignity-based score
    dignity = _get_dignity(planet, pos.sign, pos.degree_in_sign)
    dignity_scores = {
        "exalted": 45.0,
        "own_sign": 30.0,
        "moolatrikona": 22.5,
        "friend": 15.0,
        "neutral": 7.5,
        "enemy": 3.75,
        "debilitated": 1.875,
    }
    saptavargaja_bala = dignity_scores.get(dignity, 7.5)

    # (c) Ojhayugma Bala — odd/even sign strength
    sign_value = int(pos.sign)
    is_even_sign = (sign_value % 2 == 0)
    if planet in (Planet.MOON, Planet.VENUS):
        ojhayugma_bala = 15.0 if is_even_sign else 0.0
    else:
        ojhayugma_bala = 15.0 if not is_even_sign else 0.0

    # (d) Kendradi Bala — angular house strength
    house_num = _planet_house(pos.sign, chart.houses)
    if house_num in (1, 4, 7, 10):
        kendradi_bala = 60.0
    elif house_num in (2, 5, 8, 11):
        kendradi_bala = 30.0
    else:
        kendradi_bala = 15.0

    # (e) Drekkana Bala — decanate strength
    deg = pos.degree_in_sign
    if deg < 10.0:
        drekkana = 1
    elif deg < 20.0:
        drekkana = 2
    else:
        drekkana = 3

    # Male planets strong in 1st drekkana, neutral in 2nd, female in 3rd
    if planet in (Planet.SUN, Planet.MARS, Planet.JUPITER):
        drekkana_bala = 15.0 if drekkana == 1 else 0.0
    elif planet in (Planet.MERCURY, Planet.SATURN):
        drekkana_bala = 15.0 if drekkana == 2 else 0.0
    else:  # Moon, Venus
        drekkana_bala = 15.0 if drekkana == 3 else 0.0

    return uchcha_bala + saptavargaja_bala + ojhayugma_bala + kendradi_bala + drekkana_bala


# ---------------------------------------------------------------------------
# 2. Dig Bala (Directional Strength)
# ---------------------------------------------------------------------------

def _dig_bala(planet: Planet, chart: BirthChart) -> float:
    """Compute Dig Bala — strength based on house placement relative to
    the planet's directional stronghold.
    """
    pos = chart.planets[planet]
    planet_house = _planet_house(pos.sign, chart.houses)
    best_house = DIG_BALA_HOUSES[planet]

    # Minimum circular distance between two houses (1-12)
    diff = abs(planet_house - best_house)
    if diff > 6:
        diff = 12 - diff

    # Max 60 when diff=0 (in best house), min 0 when diff=6 (opposite)
    return (6 - diff) * 10.0


# ---------------------------------------------------------------------------
# 3. Kaala Bala (Temporal Strength)
# ---------------------------------------------------------------------------

def _kaala_bala(planet: Planet, chart: BirthChart) -> float:
    """Compute Kaala Bala — temporal strength.

    Only Nathonnatha Bala (day/night) is computed precisely; the remaining
    sub-components (Paksha, Tribhaga, Varsha/Masa/Dina/Hora) use simplified
    default values.
    """
    birth_hour = chart.birth_datetime.hour + chart.birth_datetime.minute / 60.0
    is_day_birth = 6.0 <= birth_hour < 18.0

    # Day planets: Sun, Jupiter, Venus. Night planets: Moon, Mars, Saturn.
    # Mercury is always strong (benefic day and night).
    day_planets = {Planet.SUN, Planet.JUPITER, Planet.VENUS}
    night_planets = {Planet.MOON, Planet.MARS, Planet.SATURN}

    if planet == Planet.MERCURY:
        nathonnatha = 60.0
    elif is_day_birth:
        nathonnatha = 60.0 if planet in day_planets else 0.0
    else:
        nathonnatha = 60.0 if planet in night_planets else 0.0

    # Simplified sub-components
    paksha_bala = 30.0
    tribhaga_bala = 20.0
    other_bala = 15.0  # Varsha + Masa + Dina + Hora combined simplified

    return nathonnatha + paksha_bala + tribhaga_bala + other_bala


# ---------------------------------------------------------------------------
# 4. Chesta Bala (Motional Strength)
# ---------------------------------------------------------------------------

def _chesta_bala(planet: Planet, chart: BirthChart) -> float:
    """Compute Chesta Bala — motional strength.

    Retrograde planets receive maximum strength (60). Sun and Moon, which
    are never retrograde, receive a fixed 30 each.
    """
    if planet in (Planet.SUN, Planet.MOON):
        return 30.0

    pos = chart.planets[planet]
    if pos.is_retrograde:
        return 60.0

    # Direct motion (simplified: assume moderate speed)
    return 30.0


# ---------------------------------------------------------------------------
# 5. Naisargika Bala (Natural Strength)
# ---------------------------------------------------------------------------

def _naisargika_bala(planet: Planet) -> float:
    """Return the natural (inherent) strength from the constants table."""
    return NAISARGIKA_BALA[planet]


# ---------------------------------------------------------------------------
# 6. Drik Bala (Aspectual Strength)
# ---------------------------------------------------------------------------

def _drik_bala(planet: Planet, chart: BirthChart) -> float:
    """Compute Drik Bala — strength from aspects received.

    Benefic aspects (Jupiter, Venus, waxing Moon) add +15 each.
    Malefic aspects (Saturn, Mars, Sun, Rahu, Ketu) subtract -15 each.
    Mercury is treated as mildly benefic (+15).
    The result is clamped to a minimum of 0.
    """
    benefics = {Planet.JUPITER, Planet.VENUS, Planet.MERCURY, Planet.MOON}
    malefics = {Planet.SUN, Planet.MARS, Planet.SATURN, Planet.RAHU, Planet.KETU}

    pos = chart.planets[planet]
    target_house = _planet_house(pos.sign, chart.houses)

    score = 0.0

    # Check every planet in the chart (including Rahu/Ketu as aspectors)
    for other_planet, other_pos in chart.planets.items():
        if other_planet == planet:
            continue
        if other_planet not in GRAHA_DRISHTI:
            continue

        other_house = _planet_house(other_pos.sign, chart.houses)

        # Check if other_planet's aspects reach the target house
        for offset in GRAHA_DRISHTI[other_planet]:
            aspected_house = ((other_house - 1 + offset) % 12) + 1
            if aspected_house == target_house:
                if other_planet in benefics:
                    score += 15.0
                elif other_planet in malefics:
                    score -= 15.0
                break  # Each planet aspects a given house at most once

    return max(score, 0.0)


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def calculate_shadbala(chart: BirthChart) -> dict[Planet, ShadbalaResult]:
    """Calculate Shadbala (six-fold strength) for the seven visible planets.

    Shadbala quantifies a planet's total strength by summing six distinct
    components, each measuring a different dimension of planetary power.
    All values are in Shashtiamsas (1/60 Rupa).

    Only Sun through Saturn are computed; Rahu and Ketu are excluded
    from Shadbala per classical tradition.

    Args:
        chart: A fully computed BirthChart with planets and houses.

    Returns:
        A dictionary mapping each of the seven planets to its ShadbalaResult,
        containing the six component strengths, total, and is_strong flag.

    Example:
        >>> from vedic_calc.chart.calculator import calculate_chart
        >>> chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
        >>> results = calculate_shadbala(chart)
        >>> results[Planet.JUPITER].total
        345.28
        >>> results[Planet.JUPITER].is_strong
        True
    """
    results: dict[Planet, ShadbalaResult] = {}

    for planet in _SHADBALA_PLANETS:
        sthana = _sthana_bala(planet, chart)
        dig = _dig_bala(planet, chart)
        kaala = _kaala_bala(planet, chart)
        chesta = _chesta_bala(planet, chart)
        naisargika = _naisargika_bala(planet)
        drik = _drik_bala(planet, chart)

        total = sthana + dig + kaala + chesta + naisargika + drik

        results[planet] = ShadbalaResult(
            planet=planet,
            sthana_bala=round(sthana, 2),
            dig_bala=round(dig, 2),
            kaala_bala=round(kaala, 2),
            chesta_bala=round(chesta, 2),
            naisargika_bala=round(naisargika, 2),
            drik_bala=round(drik, 2),
            total=round(total, 2),
            is_strong=total >= _STRENGTH_THRESHOLD,
        )

    return results
