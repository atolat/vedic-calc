"""
Birth chart (Kundli) calculator.

This is the main entry point for computing a Vedic birth chart. Given a
birth date, time, and location, it produces a complete BirthChart with
all planetary positions, houses, and nakshatra information.

HIGH-LEVEL FLOW:
    1. Convert local birth time → Universal Time (UT)
    2. Convert UT date/time → Julian Day number (continuous day count)
    3. Ask Swiss Ephemeris for each planet's tropical longitude
    4. Subtract ayanamsa to get sidereal (Vedic) longitude
    5. Map each longitude → sign, degree, nakshatra, pada
    6. Calculate the ascendant (rising sign) for the birth location
    7. Build 12 houses from the ascendant using Whole Sign system
    8. Package everything into a BirthChart model

ALL FORMULAS ARE PURE ARITHMETIC ON LONGITUDE VALUES (0°–360°):
    - Sign:      floor(longitude / 30) + 1       → 1=Aries, 2=Taurus, ...
    - Degree:    longitude % 30                   → 0° to 29.999°
    - Nakshatra: floor(longitude / 13.333) + 1    → 1=Ashvini, 2=Bharani, ...
    - Pada:      floor(degree_in_nakshatra / 3.333) + 1  → 1 to 4
    - Houses:    (ascendant_sign + i - 1) % 12 + 1  → Whole Sign system

SOURCE REFERENCES:
    - Brihat Parashara Hora Shastra (BPHS), Ch. 3-7: Planet-sign-nakshatra mapping
    - Surya Siddhanta: Astronomical calculation methods
    - Swiss Ephemeris documentation: pyswisseph API and precision

Example:
    >>> from vedic_calc import calculate_chart
    >>> chart = calculate_chart(
    ...     year=1990, month=3, day=15,
    ...     hour=10, minute=30,
    ...     latitude=19.0760, longitude=72.8777,
    ...     timezone_offset=5.5,
    ... )
    >>> print(chart.ascendant.sign.name)
    'GEMINI'
"""

from __future__ import annotations

from datetime import datetime

from vedic_calc.core.constants import (
    Ayanamsa,
    Nakshatra,
    Planet,
    Sign,
    NAKSHATRA_LORDS,
    NAKSHATRA_SPAN,
    PADA_SPAN,
    SIGN_LORDS,
)
from vedic_calc.core.ephemeris import (
    _to_julian_day,
    get_ascendant,
    get_ayanamsa,
    get_planet_longitude,
)
from vedic_calc.core.types import (
    BirthChart,
    HousePosition,
    NakshatraInfo,
    PlanetPosition,
)


# ---------------------------------------------------------------------------
# Helper functions (pure arithmetic, no side effects, no external calls)
# ---------------------------------------------------------------------------

def longitude_to_sign(longitude: float) -> Sign:
    """Convert a sidereal longitude (0-360°) to its zodiac sign.

    THE ZODIAC IS A CIRCLE OF 360° DIVIDED INTO 12 SIGNS OF 30° EACH:

        Sign        Range         Value
        ─────────   ──────────    ─────
        Aries       0° – 30°     1
        Taurus      30° – 60°    2
        Gemini      60° – 90°    3
        Cancer      90° – 120°   4
        Leo         120° – 150°  5
        Virgo       150° – 180°  6
        Libra       180° – 210°  7
        Scorpio     210° – 240°  8
        Sagittarius 240° – 270°  9
        Capricorn   270° – 300°  10
        Aquarius    300° – 330°  11
        Pisces      330° – 360°  12

    FORMULA: sign_number = floor(longitude / 30) + 1

    Args:
        longitude: Sidereal longitude in degrees (0-360).

    Returns:
        The zodiac Sign enum.

    Example:
        >>> longitude_to_sign(45.0)   # 45° is in Taurus (30-60°)
        <Sign.TAURUS: 2>
        >>> longitude_to_sign(0.0)    # 0° is start of Aries
        <Sign.ARIES: 1>
        >>> longitude_to_sign(359.9)  # Near end of Pisces
        <Sign.PISCES: 12>
    """
    sign_index = int(longitude / 30.0) + 1
    # Clamp to valid range (handles the edge case where longitude == 360.0)
    sign_index = min(sign_index, 12)
    return Sign(sign_index)


def longitude_to_degree_in_sign(longitude: float) -> float:
    """Get the degree within a sign (0-30°) from absolute longitude.

    FORMULA: degree_in_sign = longitude % 30

    A planet at longitude 75° is in Gemini (60-90°), and its degree
    within Gemini is 75 % 30 = 15°. So we'd say "15° Gemini".

    Args:
        longitude: Sidereal longitude in degrees (0-360).

    Returns:
        Degree within the sign (0 to <30).

    Example:
        >>> longitude_to_degree_in_sign(45.0)   # 45° → 15° in Taurus
        15.0
        >>> longitude_to_degree_in_sign(0.0)    # 0° → 0° in Aries
        0.0
        >>> longitude_to_degree_in_sign(359.5)  # → 29.5° in Pisces
        29.5
    """
    return longitude % 30.0


def longitude_to_nakshatra_info(longitude: float) -> NakshatraInfo:
    """Derive nakshatra, pada, and lord from a sidereal longitude.

    THE 27 NAKSHATRAS DIVIDE THE 360° ZODIAC INTO EQUAL SEGMENTS:

        360° ÷ 27 nakshatras = 13.333° per nakshatra (= 13°20')
        13.333° ÷ 4 padas = 3.333° per pada (= 3°20')

        So the full zodiac has 27 × 4 = 108 padas.

    FORMULA:
        nakshatra_number = floor(longitude / 13.333) + 1
        degree_in_nakshatra = longitude % 13.333
        pada = floor(degree_in_nakshatra / 3.333) + 1

    EXAMPLE WALKTHROUGH:
        longitude = 45.0°
        nakshatra = floor(45.0 / 13.333) + 1 = floor(3.375) + 1 = 3 + 1 = 4
        → Nakshatra #4 = Rohini (but wait — we use 0-indexed then +1)
        Actually: floor(45.0 / 13.333) = 3, so nakshatra = 3+1 = 4... but
        our enum starts at 1, so index 3 = Nakshatra(4) = Rohini.

        Let's re-check: 0-13.333 = Ashvini(1), 13.333-26.667 = Bharani(2),
        26.667-40.0 = Krittika(3), 40.0-53.333 = Rohini(4) ← 45° is here ✓

        degree_in_nak = 45.0 % 13.333 = 5.001°
        pada = floor(5.001 / 3.333) + 1 = 1 + 1 = 2

    Args:
        longitude: Sidereal longitude in degrees (0-360).

    Returns:
        NakshatraInfo with nakshatra, pada, lord, and degree within nakshatra.

    Example:
        >>> info = longitude_to_nakshatra_info(45.0)
        >>> info.nakshatra
        <Nakshatra.KRITTIKA: 3>
        >>> info.pada
        4
    """
    # Which nakshatra? (0-indexed from the division, then +1 for our 1-indexed enum)
    nak_index = int(longitude / NAKSHATRA_SPAN)
    nak_index = min(nak_index, 26)  # Clamp for edge case at exactly 360°
    nakshatra = Nakshatra(nak_index + 1)

    # Degree within this nakshatra (0 to 13.333°)
    degree_in_nak = longitude % NAKSHATRA_SPAN

    # Which pada? Each nakshatra has 4 padas of 3.333° each
    pada = int(degree_in_nak / PADA_SPAN) + 1
    pada = min(pada, 4)  # Clamp for edge case

    # Ruling planet from the fixed nakshatra-lord lookup table
    # (see constants.py for the Ketu→Venus→Sun→...→Mercury cycle)
    lord = NAKSHATRA_LORDS[nakshatra]

    return NakshatraInfo(
        nakshatra=nakshatra,
        pada=pada,
        lord=lord,
        degree_in_nakshatra=round(degree_in_nak, 4),
    )


def build_houses(ascendant_sign: Sign) -> list[HousePosition]:
    """Build the 12 houses using the Whole Sign house system.

    WHOLE SIGN HOUSES (THE VEDIC DEFAULT):
        The sign containing the ascendant = the entire 1st house.
        The next sign = the entire 2nd house. And so on for all 12.

        This is the simplest house system and the one used by classical
        Vedic astrology (Parashari method from BPHS).

    FORMULA:
        house_sign = (ascendant_sign_value - 1 + house_index) % 12 + 1

        Example with Gemini (3) ascendant:
        House 1: (3-1+0) % 12 + 1 = 2%12+1 = 3 → Gemini  ✓
        House 2: (3-1+1) % 12 + 1 = 3%12+1 = 4 → Cancer
        House 7: (3-1+6) % 12 + 1 = 8%12+1 = 9 → Sagittarius (opposite)
        House 12: (3-1+11) % 12 + 1 = 1%12+1 = 2 → Taurus (previous sign)

    HOUSE LORD:
        Each house's lord = the planet that rules the sign occupying it.
        See SIGN_LORDS in constants.py (e.g., Mars rules Aries, Venus
        rules Taurus, etc.).

    Args:
        ascendant_sign: The zodiac sign of the ascendant (lagna).

    Returns:
        List of 12 HousePosition objects.

    Example:
        >>> houses = build_houses(Sign.GEMINI)
        >>> houses[0].sign         # 1st house
        <Sign.GEMINI: 3>
        >>> houses[6].sign         # 7th house (opposite)
        <Sign.SAGITTARIUS: 9>
    """
    houses = []
    for i in range(12):
        # Signs cycle 1-12, wrapping around with modular arithmetic
        sign_value = ((ascendant_sign.value - 1 + i) % 12) + 1
        sign = Sign(sign_value)
        houses.append(HousePosition(
            house_number=i + 1,
            sign=sign,
            lord=SIGN_LORDS[sign],
        ))
    return houses


# ---------------------------------------------------------------------------
# Main chart calculation — the public API entry point
# ---------------------------------------------------------------------------

def calculate_chart(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
    latitude: float = 0.0,
    longitude: float = 0.0,
    timezone_offset: float = 0.0,
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI,
) -> BirthChart:
    """Calculate a complete Vedic birth chart.

    This is the main entry point for vedic-calc. Given birth details,
    it computes all planetary positions, houses, and nakshatra data.

    STEP-BY-STEP CALCULATION:

        1. LOCAL TIME → UNIVERSAL TIME (UT)
           The Swiss Ephemeris needs UT (≈ UTC), not local time.
           Formula: ut_hour = local_hour - timezone_offset
           Example: 10:30 IST → 10.5 - 5.5 = 5.0 UT

        2. UT → JULIAN DAY NUMBER
           Julian Day is a continuous day count used by astronomers.
           Example: Jan 1, 2000 at noon UT = JD 2451545.0
           This is handled by _to_julian_day() in ephemeris.py.

        3. PLANETARY POSITIONS (for each of the 9 Vedic planets)
           a. Swiss Ephemeris returns tropical (Western) longitude
           b. We subtract the ayanamsa (~24°) to get sidereal (Vedic) longitude
           c. From the sidereal longitude, we derive:
              - Sign (which 30° segment)
              - Degree within sign (position in that segment)
              - Nakshatra and pada (which 13.333° lunar mansion)
           d. We check if the planet is retrograde (negative daily speed)

        4. ASCENDANT (LAGNA)
           The rising degree on the eastern horizon at birth, which depends
           on both the time AND the geographic location (unlike planets,
           which are the same worldwide at any given moment).

        5. HOUSES
           Using Whole Sign: ascendant's sign = 1st house, next sign = 2nd, etc.

    Args:
        year: Birth year (e.g., 1990).
        month: Birth month (1-12).
        day: Birth day (1-31).
        hour: Birth hour in LOCAL time (0-23). Not UT!
        minute: Birth minute (0-59).
        second: Birth second (0-59).
        latitude: Birth latitude in degrees (north = positive, south = negative).
                  Example: Mumbai = 19.076, Sydney = -33.868
        longitude: Birth longitude in degrees (east = positive, west = negative).
                   Example: Mumbai = 72.878, New York = -74.006
        timezone_offset: UTC offset in hours.
                         Example: IST = +5.5, EST = -5, JST = +9
        ayanamsa: Which ayanamsa correction to use. Defaults to Lahiri
                  (the Indian government standard, used by ~90% of Vedic astrologers).

    Returns:
        A complete BirthChart with all planetary positions and houses.

    Example:
        >>> chart = calculate_chart(
        ...     year=1990, month=3, day=15,
        ...     hour=10, minute=30,
        ...     latitude=19.0760, longitude=72.8777,
        ...     timezone_offset=5.5,
        ... )
        >>> len(chart.planets)   # 9 Vedic planets
        9
        >>> len(chart.houses)    # 12 houses
        12
    """
    # ─── Step 1: Convert local time to Universal Time (UT) ───
    # Swiss Ephemeris requires UT, not local time.
    # We combine hour + minute + second into a decimal hour,
    # then subtract the timezone offset to get UT.
    hour_decimal = hour + minute / 60.0 + second / 3600.0
    ut_hour = hour_decimal - timezone_offset
    # Note: ut_hour can be negative (meaning the UT date is the previous day).
    # The _to_julian_day function handles this correctly.

    # ─── Step 2: Convert to Julian Day number ───
    # This gives us a single float that the Swiss Ephemeris uses internally.
    jd = _to_julian_day(year, month, day, ut_hour)

    # ─── Step 3a: Get the ayanamsa value for this date ───
    # This is the tropical-to-sidereal correction (~24° in 2024).
    # We store it in the chart for reference/debugging.
    ayanamsa_degrees = get_ayanamsa(jd, ayanamsa)

    # ─── Step 3b: Calculate the ascendant (lagna) ───
    # Unlike planets, the ascendant depends on geographic location because
    # it's the degree rising on YOUR local horizon at the moment of birth.
    asc_longitude = get_ascendant(jd, latitude, longitude, ayanamsa)
    asc_sign = longitude_to_sign(asc_longitude)
    asc_degree = longitude_to_degree_in_sign(asc_longitude)
    asc_nakshatra = longitude_to_nakshatra_info(asc_longitude)

    ascendant = PlanetPosition(
        planet=Planet.SUN,  # Placeholder — ascendant isn't a planet, but we
        # reuse PlanetPosition for consistency. The planet field is ignored
        # when this is used as chart.ascendant.
        longitude=round(asc_longitude, 4),
        sign=asc_sign,
        degree_in_sign=round(asc_degree, 4),
        nakshatra_info=asc_nakshatra,
        is_retrograde=False,
    )

    # ─── Step 4: Calculate all 9 planetary positions ───
    # Loop through Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu.
    # Each call to get_planet_longitude():
    #   1. Gets tropical longitude from Swiss Ephemeris
    #   2. Subtracts ayanamsa → sidereal longitude
    #   3. Returns (longitude, is_retrograde)
    planets: dict[Planet, PlanetPosition] = {}
    for planet in Planet:
        lon, is_retro = get_planet_longitude(jd, planet, ayanamsa)

        # Derive sign, degree, and nakshatra from the sidereal longitude
        sign = longitude_to_sign(lon)
        degree = longitude_to_degree_in_sign(lon)
        nak_info = longitude_to_nakshatra_info(lon)

        planets[planet] = PlanetPosition(
            planet=planet,
            longitude=round(lon, 4),
            sign=sign,
            degree_in_sign=round(degree, 4),
            nakshatra_info=nak_info,
            is_retrograde=is_retro,
        )

    # ─── Step 5: Build houses using Whole Sign system ───
    # The ascendant's sign = 1st house. All other houses follow sequentially.
    houses = build_houses(asc_sign)

    # ─── Step 6: Package everything into a BirthChart ───
    # Store birth datetime in LOCAL time (not UT) for human readability.
    birth_dt = datetime(year, month, day, hour, minute, second)

    return BirthChart(
        planets=planets,
        houses=houses,
        ascendant=ascendant,
        ayanamsa=ayanamsa,
        ayanamsa_degrees=round(ayanamsa_degrees, 4),
        birth_datetime=birth_dt,
        latitude=latitude,
        longitude=longitude,
        timezone_offset=timezone_offset,
    )
