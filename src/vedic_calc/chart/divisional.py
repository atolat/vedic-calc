"""
Divisional chart (Varga) calculations.

Divisional charts are derived from the D1 (Rasi) birth chart by subdividing
each sign into smaller portions and mapping each planet's position to a new
sign based on formulas specific to each division. They reveal finer layers
of a person's destiny — e.g., D9 (Navamsa) for marriage, D10 (Dasamsa) for
career, D7 (Saptamsa) for children.

THE GENERAL IDEA:
    A planet at, say, 15° Taurus in D1 will land in different signs in
    different divisional charts. The mapping depends on:
      1. Which part of the 30° sign the planet falls in (based on division size)
      2. A starting sign determined by the D1 sign's element or modality
      3. Counting forward from that starting sign by the part number

    For most divisions: part = int(degree_in_sign / (30 / division))
    Then: result_sign = starting_sign + part (mod 12)

SPECIAL CASES:
    D2 (Hora) and D30 (Trimsamsa) use unique formulas that don't follow
    the generic pattern.

SOURCE REFERENCES:
    - Brihat Parashara Hora Shastra (BPHS), Ch. 6: Divisional chart formulas
    - Brihat Jataka, Ch. 1: Navamsa and other vargas
    - Phaladeepika, Ch. 16: Shodasavarga (16-division scheme)

Example:
    >>> from vedic_calc.chart.calculator import calculate_chart
    >>> from vedic_calc.chart.divisional import calculate_divisional_chart
    >>> chart = calculate_chart(1990, 3, 15, 10, 30, latitude=19.076, longitude=72.878, timezone_offset=5.5)
    >>> navamsa = calculate_divisional_chart(chart, 9)
    >>> navamsa.name
    'Navamsa'
    >>> navamsa.planets[Planet.MOON]
    <Sign.LIBRA: 7>
"""

from __future__ import annotations

from vedic_calc.core.constants import Planet, Sign
from vedic_calc.core.types import BirthChart, DivisionalChart


# ---------------------------------------------------------------------------
# Division names — maps division number to its traditional Sanskrit name
# ---------------------------------------------------------------------------

DIVISION_NAMES: dict[int, str] = {
    1: "Rasi",
    2: "Hora",
    3: "Drekkana",
    4: "Chaturthamsa",
    5: "Panchamsa",
    6: "Shashthamsa",
    7: "Saptamsa",
    8: "Ashtamsa",
    9: "Navamsa",
    10: "Dasamsa",
    11: "Ekadasamsa",
    12: "Dwadasamsa",
    16: "Shodasamsa",
    20: "Vimsamsa",
    24: "Chaturvimsamsa",
    27: "Bhamsa",
    30: "Trimsamsa",
    40: "Khavedamsa",
    45: "Akshavedamsa",
    60: "Shashtiamsa",
}


# ---------------------------------------------------------------------------
# Sign classification helpers
# ---------------------------------------------------------------------------

def _sign_element(sign: Sign) -> str:
    """Return the element of a sign: 'fire', 'earth', 'air', or 'water'.

    THE ELEMENT CYCLE (repeats every 4 signs):
        Fire:  Aries(1), Leo(5), Sagittarius(9)
        Earth: Taurus(2), Virgo(6), Capricorn(10)
        Air:   Gemini(3), Libra(7), Aquarius(11)
        Water: Cancer(4), Scorpio(8), Pisces(12)

    Formula: element_index = (sign.value - 1) % 4
             0=fire, 1=earth, 2=air, 3=water
    """
    index = (sign.value - 1) % 4
    return ("fire", "earth", "air", "water")[index]


def _sign_modality(sign: Sign) -> str:
    """Return the modality of a sign: 'movable', 'fixed', or 'dual'.

    THE MODALITY CYCLE (repeats every 3 signs):
        Movable (Chara):  Aries(1), Cancer(4), Libra(7), Capricorn(10)
        Fixed (Sthira):   Taurus(2), Leo(5), Scorpio(8), Aquarius(11)
        Dual (Dvisvabhava): Gemini(3), Virgo(6), Sagittarius(9), Pisces(12)

    Formula: modality_index = (sign.value - 1) % 3
             0=movable, 1=fixed, 2=dual
    """
    index = (sign.value - 1) % 3
    return ("movable", "fixed", "dual")[index]


def _is_odd_sign(sign: Sign) -> bool:
    """Return True if the sign is odd-numbered (Aries, Gemini, Leo, ...)."""
    return sign.value % 2 == 1


def _count_signs(from_sign: Sign, count: int) -> Sign:
    """Count forward from a sign by `count` signs (0 = same sign).

    Uses modular arithmetic to wrap around the 12-sign zodiac.

    Examples:
        _count_signs(ARIES, 0)  → ARIES
        _count_signs(ARIES, 4)  → LEO
        _count_signs(PISCES, 1) → ARIES  (wraps around)
    """
    return Sign(((from_sign.value - 1 + count) % 12) + 1)


# ---------------------------------------------------------------------------
# Special division formulas
# ---------------------------------------------------------------------------

def _d2_hora(sign: Sign, degree: float) -> Sign:
    """D2 (Hora) — divides each sign into two halves of 15°.

    FORMULA (Parashari):
        Odd signs:  0-15° → Leo (Sun's hora), 15-30° → Cancer (Moon's hora)
        Even signs: 0-15° → Cancer (Moon's hora), 15-30° → Leo (Sun's hora)

    The Hora chart has only two possible signs: Leo and Cancer, representing
    the Sun and Moon respectively — the two luminaries that govern prosperity.
    """
    first_half = degree < 15.0
    if _is_odd_sign(sign):
        return Sign.LEO if first_half else Sign.CANCER
    else:
        return Sign.CANCER if first_half else Sign.LEO


def _d3_drekkana(sign: Sign, degree: float) -> Sign:
    """D3 (Drekkana) — divides each sign into three parts of 10°.

    FORMULA:
        Part 1 (0-10°):  Same sign (1st from sign)
        Part 2 (10-20°): 5th from sign
        Part 3 (20-30°): 9th from sign

    These correspond to the trinal relationship: self, 5th, 9th — the
    three signs of the same element. E.g., for Aries (fire): Aries, Leo,
    Sagittarius. The Drekkana chart is used for siblings and courage.
    """
    part = int(degree / 10.0)
    part = min(part, 2)  # clamp for degree == 30.0 edge case
    offsets = (0, 4, 8)  # same, 5th, 9th (0-indexed offsets)
    return _count_signs(sign, offsets[part])


def _d30_trimsamsa(sign: Sign, degree: float) -> Sign:
    """D30 (Trimsamsa) — uses unequal divisions based on Parashari rules.

    FORMULA (standard Parashari):
        For odd signs (Aries, Gemini, Leo, ...):
            0-5°:   Mars      → Aries
            5-10°:  Saturn    → Aquarius
            10-18°: Jupiter   → Sagittarius
            18-25°: Mercury   → Gemini
            25-30°: Venus     → Libra

        For even signs (Taurus, Cancer, Virgo, ...):
            0-5°:   Venus     → Taurus
            5-12°:  Mercury   → Virgo
            12-20°: Jupiter   → Pisces
            20-25°: Saturn    → Capricorn
            25-30°: Mars      → Scorpio

    The mapping uses the odd sign of each planet's rulership for odd D1
    signs, and the even sign for even D1 signs.
    """
    if _is_odd_sign(sign):
        if degree < 5.0:
            return Sign.ARIES
        elif degree < 10.0:
            return Sign.AQUARIUS
        elif degree < 18.0:
            return Sign.SAGITTARIUS
        elif degree < 25.0:
            return Sign.GEMINI
        else:
            return Sign.LIBRA
    else:
        if degree < 5.0:
            return Sign.TAURUS
        elif degree < 12.0:
            return Sign.VIRGO
        elif degree < 20.0:
            return Sign.PISCES
        elif degree < 25.0:
            return Sign.CAPRICORN
        else:
            return Sign.SCORPIO


# ---------------------------------------------------------------------------
# Generic division formula
# ---------------------------------------------------------------------------

# Starting signs for divisions that depend on the D1 sign's element.
# Format: {division: {element: starting_sign}}
_ELEMENT_STARTS: dict[int, dict[str, Sign]] = {
    9: {
        "fire": Sign.ARIES,
        "earth": Sign.CAPRICORN,
        "air": Sign.LIBRA,
        "water": Sign.CANCER,
    },
    27: {
        "fire": Sign.ARIES,
        "earth": Sign.CANCER,
        "air": Sign.LIBRA,
        "water": Sign.CAPRICORN,
    },
}

# Starting signs for divisions that depend on the D1 sign's modality.
# Format: {division: {modality: starting_sign}}
_MODALITY_STARTS: dict[int, dict[str, Sign]] = {
    16: {
        "movable": Sign.ARIES,
        "fixed": Sign.LEO,
        "dual": Sign.SAGITTARIUS,
    },
    20: {
        "movable": Sign.ARIES,
        "fixed": Sign.SAGITTARIUS,
        "dual": Sign.LEO,
    },
    45: {
        "movable": Sign.ARIES,
        "fixed": Sign.LEO,
        "dual": Sign.SAGITTARIUS,
    },
}

# Starting signs for divisions that depend on odd/even D1 sign.
# Format: {division: (odd_start, even_start)}
_ODD_EVEN_STARTS: dict[int, tuple[Sign, Sign]] = {
    7: (Sign.ARIES, Sign.ARIES),    # odd: from sign, even: from 7th — handled specially
    10: (Sign.ARIES, Sign.ARIES),   # odd: from sign, even: from 9th — handled specially
    24: (Sign.LEO, Sign.CANCER),
    40: (Sign.ARIES, Sign.LIBRA),
}


def _get_divisional_sign(sign: Sign, degree: float, division: int) -> Sign:
    """Calculate the divisional chart sign for a planet.

    This is the core mapping function. Given a planet's D1 sign, its degree
    within that sign, and the division number, it returns the sign the planet
    occupies in that divisional chart.

    GENERAL ALGORITHM:
        1. Compute part = int(degree / (30 / division))
        2. Determine the starting sign based on D1 sign properties
        3. Result = starting_sign + part (mod 12)

    Args:
        sign: The planet's D1 (Rasi) sign.
        degree: The planet's degree within the D1 sign (0-30).
        division: The varga number (1, 2, 3, 4, 7, 9, 10, 12, etc.).

    Returns:
        The Sign the planet occupies in the specified divisional chart.
    """
    # ── Special cases with unique formulas ──
    if division == 1:
        return sign

    if division == 2:
        return _d2_hora(sign, degree)

    if division == 3:
        return _d3_drekkana(sign, degree)

    if division == 30:
        return _d30_trimsamsa(sign, degree)

    # ── Generic formula: compute which part of the sign ──
    part_size = 30.0 / division
    part = int(degree / part_size)
    part = min(part, division - 1)  # clamp for degree == 30.0 edge case

    # ── D4 (Chaturthamsa): Part n → (n * 3) signs forward from sign ──
    if division == 4:
        return _count_signs(sign, part * 3)

    # ── D7 (Saptamsa): Odd signs count from sign, even from 7th sign ──
    if division == 7:
        if _is_odd_sign(sign):
            return _count_signs(sign, part)
        else:
            return _count_signs(sign, 6 + part)  # 7th from sign = +6

    # ── D9 (Navamsa): Start based on element of D1 sign ──
    if division in _ELEMENT_STARTS:
        element = _sign_element(sign)
        start = _ELEMENT_STARTS[division][element]
        return _count_signs(start, part)

    # ── D10 (Dasamsa): Odd signs from sign, even from 9th sign ──
    if division == 10:
        if _is_odd_sign(sign):
            return _count_signs(sign, part)
        else:
            return _count_signs(sign, 8 + part)  # 9th from sign = +8

    # ── D12 (Dwadasamsa): Always count from same sign ──
    if division == 12:
        return _count_signs(sign, part)

    # ── D16, D20, D45: Start based on modality of D1 sign ──
    if division in _MODALITY_STARTS:
        modality = _sign_modality(sign)
        start = _MODALITY_STARTS[division][modality]
        return _count_signs(start, part)

    # ── D24 (Chaturvimsamsa): Odd signs from Leo, even from Cancer ──
    if division in _ODD_EVEN_STARTS:
        odd_start, even_start = _ODD_EVEN_STARTS[division]
        start = odd_start if _is_odd_sign(sign) else even_start
        return _count_signs(start, part)

    # ── D60 (Shashtiamsa) and all other divisions: count from same sign ──
    return _count_signs(sign, part)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_divisional_chart(chart: BirthChart, division: int) -> DivisionalChart:
    """Calculate a divisional (Varga) chart from a birth chart.

    Takes a D1 birth chart and a division number, and produces a DivisionalChart
    showing each planet's sign placement in that varga.

    SUPPORTED DIVISIONS:
        D1  (Rasi)            — same as birth chart
        D2  (Hora)            — wealth, sustenance
        D3  (Drekkana)        — siblings, courage
        D4  (Chaturthamsa)    — fortune, property
        D7  (Saptamsa)        — children, progeny
        D9  (Navamsa)         — marriage, dharma (most important varga)
        D10 (Dasamsa)         — career, profession
        D12 (Dwadasamsa)      — parents, ancestry
        D16 (Shodasamsa)      — vehicles, comforts
        D20 (Vimsamsa)        — spiritual progress
        D24 (Chaturvimsamsa)  — education, learning
        D27 (Bhamsa)          — strength, stamina
        D30 (Trimsamsa)       — misfortune, evil
        D40 (Khavedamsa)      — auspicious/inauspicious effects
        D45 (Akshavedamsa)    — general indications
        D60 (Shashtiamsa)     — past-life karma (finest varga)

    Any other division (1-60) is computed using the generic count-from-sign
    formula, which is the Parivritti (cyclic) method.

    Args:
        chart: A BirthChart (D1) with all planetary positions.
        division: The varga number (1-60).

    Returns:
        A DivisionalChart with the division number, name, planet-to-sign
        mapping, and ascendant sign.

    Raises:
        ValueError: If division is not between 1 and 60.

    Example:
        >>> navamsa = calculate_divisional_chart(chart, 9)
        >>> navamsa.name
        'Navamsa'
        >>> navamsa.planets[Planet.SUN]
        <Sign.LEO: 5>
    """
    if division < 1 or division > 60:
        raise ValueError(f"Division must be between 1 and 60, got {division}")

    # Map each planet to its sign in this divisional chart
    planets: dict[Planet, Sign] = {}
    for planet, position in chart.planets.items():
        planets[planet] = _get_divisional_sign(
            position.sign,
            position.degree_in_sign,
            division,
        )

    # Calculate the ascendant sign in the divisional chart
    ascendant_sign = _get_divisional_sign(
        chart.ascendant.sign,
        chart.ascendant.degree_in_sign,
        division,
    )

    # Look up human-readable name, defaulting to "D{n}" for unnamed divisions
    name = DIVISION_NAMES.get(division, f"D{division}")

    return DivisionalChart(
        division=division,
        name=name,
        planets=planets,
        ascendant_sign=ascendant_sign,
    )
