"""
Pydantic models for all Vedic astrology data structures.

These are the primary data types returned by vedic-calc functions.
All models are frozen (immutable) and JSON-serializable.

WHY FROZEN (IMMUTABLE)?
    A birth chart, once calculated, should never change. Making models
    frozen (via `frozen=True`) enforces this at runtime — any attempt to
    modify a field after creation raises an error. This prevents subtle
    bugs where chart data is accidentally mutated.

WHY PYDANTIC?
    Pydantic gives us automatic validation (e.g., longitude must be 0-360),
    JSON serialization (for APIs), and clean type hints — all for free.
    These models are the "contract" between the calculation engine and
    any consuming application (API, CLI, agent, etc.).

GLOSSARY FOR NEWCOMERS:
    - Kundli / Janma Patri = birth chart
    - Graha = planet (9 in Vedic astrology, including Rahu/Ketu)
    - Rashi = zodiac sign (12 signs, each 30°)
    - Nakshatra = lunar mansion (27 divisions, each 13°20')
    - Pada = quarter of a nakshatra (each 3°20', 108 total)
    - Bhava = house (12 houses in a chart)
    - Lagna = ascendant (the rising sign at birth)
    - Dasha = planetary period (time periods ruled by planets)
    - Panchanga = five-limbed daily calendar (tithi, nakshatra, yoga, karana, vara)
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from vedic_calc.core.constants import Ayanamsa, Nakshatra, Planet, Sign


class NakshatraInfo(BaseModel, frozen=True):
    """Information about a nakshatra (lunar mansion) position.

    WHAT IS A NAKSHATRA?
        The zodiac is divided into 27 nakshatras (lunar mansions), each
        spanning 13°20' (13.333°). These are the oldest layer of Vedic
        astrology, predating the 12-sign zodiac. The Moon moves through
        roughly one nakshatra per day (~13.3° daily motion).

        Each nakshatra has:
        - A ruling planet (lord) — cycles through Ketu, Venus, Sun, Moon,
          Mars, Rahu, Jupiter, Saturn, Mercury (repeating 3x for 27)
        - 4 padas (quarters) of 3°20' (3.333°) each — used for finer
          predictions and for determining the first syllable of a person's
          name in Indian tradition

    WHY IT MATTERS:
        The Moon's birth nakshatra (Janma Nakshatra) determines which
        planetary period (dasha) you're born into. It's also used for
        compatibility matching (Ashtakoot) in marriages.

    Attributes:
        nakshatra: The nakshatra (1-27). See constants.py for all 27.
        pada: The pada/quarter within the nakshatra (1-4).
        lord: The ruling planet of this nakshatra (from the fixed cycle).
        degree_in_nakshatra: How far into this nakshatra (0° to 13.333°).

    Example:
        >>> info = NakshatraInfo(
        ...     nakshatra=Nakshatra.ROHINI, pada=2,
        ...     lord=Planet.MOON, degree_in_nakshatra=5.5,
        ... )
    """
    nakshatra: Nakshatra
    pada: int = Field(ge=1, le=4)
    lord: Planet
    degree_in_nakshatra: float = Field(ge=0.0, lt=13.334)


class PlanetPosition(BaseModel, frozen=True):
    """A planet's position in the sidereal zodiac.

    WHAT DOES A PLANET POSITION CONTAIN?
        When we say "Mars is at 15° Taurus", we mean:
        - sign = Taurus (the 30° segment of the zodiac)
        - degree_in_sign = 15° (where within that 30° segment)
        - longitude = 45° (absolute position: Aries 0-30 + 15 = 45°)
        - nakshatra = Rohini (the 13.333° lunar mansion it falls in)

        We also track whether the planet is retrograde (appearing to
        move backward in the sky — see ephemeris.py for details).

    HOW TO INTERPRET:
        - longitude: The "master" value. Everything else derives from it.
        - sign + degree_in_sign: Human-readable version of longitude.
          Formula: sign = floor(longitude / 30) + 1
                   degree_in_sign = longitude % 30
        - nakshatra_info: Finer subdivision of the same longitude.
          Formula: nakshatra = floor(longitude / 13.333) + 1

    Attributes:
        planet: Which planet (Sun, Moon, Mars, etc.).
        longitude: Sidereal longitude in degrees (0-360).
        sign: Which zodiac sign the planet occupies (derived from longitude).
        degree_in_sign: Degrees within the sign (0-30, derived from longitude).
        nakshatra_info: The nakshatra and pada (derived from longitude).
        is_retrograde: Whether the planet appears to move backward.

    Example:
        >>> pos = PlanetPosition(
        ...     planet=Planet.MOON, longitude=45.5,
        ...     sign=Sign.TAURUS, degree_in_sign=15.5,
        ...     nakshatra_info=NakshatraInfo(...),
        ...     is_retrograde=False,
        ... )
    """
    planet: Planet
    longitude: float = Field(ge=0.0, lt=360.0)
    sign: Sign
    degree_in_sign: float = Field(ge=0.0, lt=30.0)
    nakshatra_info: NakshatraInfo
    is_retrograde: bool = False


class HousePosition(BaseModel, frozen=True):
    """A house (bhava) in the birth chart.

    WHAT ARE HOUSES?
        The 12 houses represent different areas of life:
        - 1st house (Lagna): Self, personality, physical body
        - 2nd house: Wealth, speech, family
        - 3rd house: Siblings, courage, communication
        - 4th house: Mother, home, emotional peace
        - 5th house: Children, creativity, intelligence
        - 6th house: Enemies, disease, debts
        - 7th house: Marriage, partnerships, business
        - 8th house: Longevity, sudden events, transformation
        - 9th house: Fortune, father, dharma (purpose)
        - 10th house: Career, reputation, karma (actions)
        - 11th house: Gains, income, elder siblings
        - 12th house: Losses, spirituality, foreign lands

    WHOLE SIGN HOUSE SYSTEM:
        In Vedic astrology's traditional (Parashari) method, the
        ascendant's sign = entire 1st house, the next sign = entire
        2nd house, and so on. Each house is exactly one sign (30°).

        Example: If the ascendant is at 15° Gemini:
        - 1st house = all of Gemini (0-30°)
        - 2nd house = all of Cancer (30-60°)
        - 7th house = all of Sagittarius (opposite sign)
        - ...and so on

    Attributes:
        house_number: House number (1-12).
        sign: The zodiac sign occupying this house.
        lord: The planet that rules this house's sign (e.g., Mars rules Aries).
    """
    house_number: int = Field(ge=1, le=12)
    sign: Sign
    lord: Planet


class BirthChart(BaseModel, frozen=True):
    """A complete Vedic birth chart (Kundli / Janma Patri).

    THE BIRTH CHART:
        A birth chart is a snapshot of the sky at the exact moment and
        place of birth. It shows where each planet was positioned in the
        zodiac, which sign was rising on the eastern horizon (ascendant),
        and which signs occupy which houses.

        Everything in Vedic astrology — predictions, compatibility,
        timing of events — is derived from this chart.

    WHAT THIS MODEL CONTAINS:
        1. planets: All 9 planetary positions (Sun through Ketu)
        2. houses: The 12 houses with their signs and ruling planets
        3. ascendant: The rising sign/degree (most important point)
        4. Metadata: ayanamsa used, birth time/place, timezone

    HOW TO USE:
        >>> chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
        >>> # What sign is the Moon in?
        >>> chart.planets[Planet.MOON].sign
        <Sign.TAURUS: 2>
        >>> # What nakshatra is the Moon in?
        >>> chart.planets[Planet.MOON].nakshatra_info.nakshatra
        <Nakshatra.ROHINI: 4>
        >>> # What sign is rising (ascendant)?
        >>> chart.ascendant.sign
        <Sign.GEMINI: 3>
        >>> # What planet rules the 7th house (marriage)?
        >>> chart.houses[6].lord  # 0-indexed, so house 7 = index 6
        <Planet.JUPITER: 5>
        >>> # Serialize to JSON for an API response
        >>> chart.model_dump_json()

    Attributes:
        planets: Positions of all 9 planets (keyed by Planet enum).
        houses: The 12 houses with their signs and lords.
        ascendant: The ascendant (lagna) position — also the 1st house cusp.
        ayanamsa: Which ayanamsa system was used for calculation.
        ayanamsa_degrees: The ayanamsa value in degrees at birth time.
        birth_datetime: The birth date and time (in local time, not UT).
        latitude: Birth latitude in degrees.
        longitude: Birth longitude in degrees.
        timezone_offset: UTC offset in hours (e.g., 5.5 for IST).
    """
    planets: dict[Planet, PlanetPosition]
    houses: list[HousePosition]
    ascendant: PlanetPosition  # Reuses PlanetPosition for the lagna point
    ayanamsa: Ayanamsa
    ayanamsa_degrees: float
    birth_datetime: datetime
    latitude: float
    longitude: float
    timezone_offset: float


class DashaPeriod(BaseModel, frozen=True):
    """A single dasha (planetary period) with start and end dates.

    WHAT IS THE DASHA SYSTEM?
        Vedic astrology divides a person's life into periods ruled by
        different planets. The Vimsottari dasha system (the most widely
        used) divides 120 years into 9 major periods (mahadashas):

        Ketu=7, Venus=20, Sun=6, Moon=10, Mars=7, Rahu=18,
        Jupiter=16, Saturn=19, Mercury=17 (total = 120 years)

        Each mahadasha is subdivided into sub-periods (antardashas),
        which are further divided into sub-sub-periods (pratyantardashas).
        The subdivision uses the same proportional ratios.

    HOW IS YOUR STARTING DASHA DETERMINED?
        The Moon's nakshatra at birth determines which planet's dasha
        you're born into, and how much of it remains. For example, if
        the Moon is in Rohini (ruled by Moon), you start in Moon dasha.
        How far the Moon has traversed through Rohini determines how
        much of the 10-year Moon dasha has already elapsed at birth.

    Attributes:
        lord: The ruling planet of this period.
        level: "mahadasha" (major), "antardasha" (sub), or "pratyantardasha" (sub-sub).
        start: When this period begins.
        end: When this period ends.
        duration_years: Duration in decimal years.

    Example:
        >>> period = DashaPeriod(
        ...     lord=Planet.JUPITER, level="mahadasha",
        ...     start=datetime(2020, 1, 1), end=datetime(2036, 1, 1),
        ...     duration_years=16.0,
        ... )
    """
    lord: Planet
    level: str  # "mahadasha", "antardasha", "pratyantardasha"
    start: datetime
    end: datetime
    duration_years: float


class PanchangaInfo(BaseModel, frozen=True):
    """Daily Panchanga — the five elements of a Vedic day.

    WHAT IS PANCHANGA?
        "Pancha" = five, "Anga" = limb. The Panchanga is a daily Vedic
        calendar that tracks five astronomical elements:

        1. TITHI (Lunar Day) — 30 per month
           Based on the angular distance between Moon and Sun.
           Each tithi = 12° of Moon-Sun separation.
           Tithis 1-15 = Shukla Paksha (waxing, bright half)
           Tithis 16-30 = Krishna Paksha (waning, dark half)
           Formula: tithi = floor((moon_lon - sun_lon) / 12) + 1

        2. NAKSHATRA (Moon's Lunar Mansion) — 27 total
           Which of the 27 nakshatras the Moon is transiting today.
           The Moon spends roughly one day in each nakshatra.

        3. YOGA (Luni-Solar Combination) — 27 total
           Based on the SUM of Moon and Sun longitudes.
           Each yoga = 13°20' of (moon_lon + sun_lon).
           Formula: yoga = floor((moon_lon + sun_lon) / 13.333) + 1
           Despite the similar span, yogas are unrelated to nakshatras.

        4. KARANA (Half-Tithi) — 60 per month
           Each tithi has 2 karanas. There are 11 types:
           4 fixed karanas (appear once each per month) +
           7 repeating karanas (cycle through the remaining slots).

        5. VARA (Weekday) — 7 total
           The weekday, named after planets:
           Sunday=Sun, Monday=Moon, Tuesday=Mars, Wednesday=Mercury,
           Thursday=Jupiter, Friday=Venus, Saturday=Saturn.

    WHY PANCHANGA MATTERS:
        Hindus consult the Panchanga daily to determine auspicious
        (shubh) and inauspicious (ashubh) timings for activities like
        starting a business, travel, ceremonies, etc. The concept of
        "Muhurta" (electional astrology) is based on Panchanga elements.

    Attributes:
        date: The date this panchanga is for.
        vara: Weekday name (e.g., "Sunday" / "Ravivara").
        tithi_number: Tithi number (1-30). 1-15 = Shukla, 16-30 = Krishna.
        tithi_name: Human-readable tithi name (e.g., "Shukla Dashami").
        nakshatra: Moon's nakshatra for the day.
        yoga_number: Nitya yoga number (1-27).
        yoga_name: Nitya yoga name.
        karana_number: Karana number (1-60).
        karana_name: Karana name.
        sunrise: Approximate sunrise time (local).
        sunset: Approximate sunset time (local).

    Example:
        >>> panchanga = get_panchanga(2026, 3, 8, 19.076, 72.878, 5.5)
        >>> panchanga.tithi_name
        'Shukla Dashami'
    """
    date: datetime
    vara: str
    tithi_number: int = Field(ge=1, le=30)
    tithi_name: str
    nakshatra: Nakshatra
    yoga_number: int = Field(ge=1, le=27)
    yoga_name: str
    karana_number: int = Field(ge=1, le=60)
    karana_name: str
    sunrise: datetime | None = None
    sunset: datetime | None = None
