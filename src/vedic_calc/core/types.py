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


# ---------------------------------------------------------------------------
# Divisional chart types
# ---------------------------------------------------------------------------

class DivisionalChart(BaseModel, frozen=True):
    """A divisional chart (Varga) showing planet-to-sign mapping.

    Divisional charts are derived from the D1 (Rasi) chart by dividing
    each sign into sub-divisions and mapping the planet's position to
    a new sign based on formulas specific to each division.

    Common divisions: D9 (Navamsa), D2 (Hora), D3 (Drekkana), D10 (Dasamsa).

    Attributes:
        division: The varga number (e.g., 9 for Navamsa).
        name: Human-readable name (e.g., "Navamsa").
        planets: Mapping of each planet to its sign in this divisional chart.
        ascendant_sign: The ascendant sign in this divisional chart.
    """
    division: int = Field(ge=1, le=60)
    name: str
    planets: dict[Planet, Sign]
    ascendant_sign: Sign


class AspectInfo(BaseModel, frozen=True):
    """Information about a planetary aspect (Graha Drishti).

    In Vedic astrology, planets "aspect" (cast influence on) other
    planets and houses. All planets aspect the 7th house from them;
    Mars, Jupiter, and Saturn have additional special aspects.

    Attributes:
        aspecting_planet: The planet casting the aspect.
        aspected_planet: The planet receiving the aspect (None if empty house).
        aspected_house: The house number being aspected (1-12).
        aspect_type: "full", "three_quarter", "half", or "quarter".
        is_special: Whether this is a special aspect (not the universal 7th).
    """
    aspecting_planet: Planet
    aspected_planet: Planet | None = None
    aspected_house: int = Field(ge=1, le=12)
    aspect_type: str = "full"
    is_special: bool = False


class CombustionStatus(BaseModel, frozen=True):
    """Whether a planet is combust (too close to the Sun).

    A combust planet is weakened — its significations suffer.
    The threshold varies per planet (e.g., Moon=12°, Jupiter=11°).

    Attributes:
        planet: The planet being checked.
        is_combust: Whether the planet is within the combustion threshold.
        distance_from_sun: Angular distance from the Sun in degrees.
        threshold: The combustion threshold used (depends on retro status).
    """
    planet: Planet
    is_combust: bool
    distance_from_sun: float
    threshold: float


class PlanetState(BaseModel, frozen=True):
    """Comprehensive state/dignity of a planet in a chart.

    Combines multiple assessments: dignity (own sign, exalted, etc.),
    combustion, retrograde status, and vargottama status.

    Attributes:
        planet: The planet.
        dignity: One of "exalted", "moolatrikona", "own_sign", "friend",
                 "neutral", "enemy", "debilitated".
        is_combust: Whether the planet is combust.
        is_retrograde: Whether the planet is retrograde.
        is_vargottama: Whether the planet is in the same sign in D1 and D9.
        sign: The sign the planet occupies in D1.
        sign_lord: The lord of the sign the planet occupies.
    """
    planet: Planet
    dignity: str
    is_combust: bool
    is_retrograde: bool
    is_vargottama: bool
    sign: Sign
    sign_lord: Planet


class TransitChart(BaseModel, frozen=True):
    """Planetary positions for an arbitrary date/time (transit chart).

    Unlike a BirthChart, this has no birth metadata — it's a snapshot
    of the sky at any moment, used for transit analysis.

    Attributes:
        date: The date/time of the transit.
        planets: Positions of all 9 planets.
        ayanamsa: Which ayanamsa system was used.
        ayanamsa_degrees: The ayanamsa value in degrees.
    """
    date: datetime
    planets: dict[Planet, PlanetPosition]
    ayanamsa: Ayanamsa
    ayanamsa_degrees: float


class HouseAnalysis(BaseModel, frozen=True):
    """Detailed analysis of a single house in the birth chart.

    Attributes:
        house_number: House number (1-12).
        sign: The zodiac sign occupying this house.
        lord: The planet ruling this house's sign.
        lord_sign: The sign where the house lord is placed.
        lord_house: The house number where the house lord is placed.
        occupants: Planets occupying this house.
        aspected_by: Planets aspecting this house.
        category: House category — "kendra", "trikona", "dusthana",
                  "upachaya", "maraka", or "neutral".
    """
    house_number: int = Field(ge=1, le=12)
    sign: Sign
    lord: Planet
    lord_sign: Sign
    lord_house: int = Field(ge=1, le=12)
    occupants: list[Planet]
    aspected_by: list[Planet]
    category: str


# ---------------------------------------------------------------------------
# Yoga and Dosha types
# ---------------------------------------------------------------------------

class YogaResult(BaseModel, frozen=True):
    """Result of a yoga (auspicious/inauspicious combination) check.

    Yogas are specific planetary combinations that indicate particular
    life themes or events. They are deterministic — either present or not.

    Attributes:
        name: Yoga name (e.g., "Gajakesari", "Ruchaka").
        category: Category (e.g., "pancha_mahapurusha", "dhana", "raja").
        involved_planets: Planets that form this yoga.
        description: Brief description of the yoga's significance.
        is_present: Whether this yoga is formed in the chart.
    """
    name: str
    category: str
    involved_planets: list[Planet]
    description: str
    is_present: bool


class DoshaResult(BaseModel, frozen=True):
    """Result of a dosha (affliction) check.

    Doshas are problematic planetary configurations. Some have
    cancellation conditions (dosha bhanga).

    Attributes:
        name: Dosha name (e.g., "Manglik", "Kaal Sarpa").
        is_present: Whether this dosha is present in the chart.
        severity: "none", "mild", "moderate", or "severe".
        cancellation_factors: Reasons why the dosha may be cancelled.
        description: Brief description.
    """
    name: str
    is_present: bool
    severity: str
    cancellation_factors: list[str]
    description: str


# ---------------------------------------------------------------------------
# Muhurta types
# ---------------------------------------------------------------------------

class MuhurtaInfo(BaseModel, frozen=True):
    """Muhurta (electional astrology) information for a given date.

    Contains auspicious/inauspicious time periods for the day.

    Attributes:
        date: The date.
        rahu_kalam: Tuple of (start, end) datetimes for Rahu Kalam.
        yamagandam: Tuple of (start, end) datetimes for Yamagandam.
        gulika_kalam: Tuple of (start, end) datetimes for Gulika Kalam.
        abhijit_muhurta: Tuple of (start, end) for Abhijit Muhurta (midday auspicious).
        choghadiya_day: List of (name, start, end, quality) for daytime periods.
        choghadiya_night: List of (name, start, end, quality) for nighttime periods.
        hora: Current planetary hour lord at sunrise.
    """
    date: datetime
    rahu_kalam: tuple[datetime, datetime]
    yamagandam: tuple[datetime, datetime]
    gulika_kalam: tuple[datetime, datetime]
    abhijit_muhurta: tuple[datetime, datetime]
    choghadiya_day: list[tuple[str, datetime, datetime, str]]
    choghadiya_night: list[tuple[str, datetime, datetime, str]]
    hora: Planet


# ---------------------------------------------------------------------------
# Upagraha and Special Lagna types
# ---------------------------------------------------------------------------

class UpagrahaPosition(BaseModel, frozen=True):
    """Position of an upagraha (sub-planet).

    Upagrahas are mathematically derived points (not physical bodies).

    Attributes:
        name: Upagraha name (e.g., "Dhuma", "Gulika", "Mandi").
        longitude: Sidereal longitude (0-360).
        sign: Zodiac sign.
        degree_in_sign: Degree within the sign (0-30).
    """
    name: str
    longitude: float = Field(ge=0.0, lt=360.0)
    sign: Sign
    degree_in_sign: float = Field(ge=0.0, lt=30.0)


class SpecialLagna(BaseModel, frozen=True):
    """A special lagna (ascendant variant).

    Attributes:
        name: Lagna name (e.g., "Bhava Lagna", "Hora Lagna").
        longitude: Sidereal longitude (0-360).
        sign: Zodiac sign.
        degree_in_sign: Degree within the sign (0-30).
    """
    name: str
    longitude: float = Field(ge=0.0, lt=360.0)
    sign: Sign
    degree_in_sign: float = Field(ge=0.0, lt=30.0)


# ---------------------------------------------------------------------------
# Jaimini types
# ---------------------------------------------------------------------------

class CharaKaraka(BaseModel, frozen=True):
    """A Jaimini chara (variable) karaka.

    Attributes:
        karaka_name: Karaka name (e.g., "Atmakaraka").
        planet: The planet assigned this karaka role.
        degree_in_sign: The planet's degree within its sign (used for ranking).
    """
    karaka_name: str
    planet: Planet
    degree_in_sign: float


class ArudhaPada(BaseModel, frozen=True):
    """An Arudha Pada (Jaimini concept).

    Attributes:
        house_number: The original house (1-12).
        sign: The sign of the Arudha Pada.
        pada_name: Name (e.g., "Arudha Lagna (AL)" for house 1).
    """
    house_number: int = Field(ge=1, le=12)
    sign: Sign
    pada_name: str


# ---------------------------------------------------------------------------
# Strength types
# ---------------------------------------------------------------------------

class AshtakavargaResult(BaseModel, frozen=True):
    """Result of Ashtakavarga calculation.

    Bhinnashtakavarga: Individual benefic point tables for each planet.
    Sarvashtakavarga: Combined points across all planets.

    Attributes:
        bhinna: For each planet, list of 12 ints (benefic points per sign, 0-8).
        sarva: List of 12 ints (total benefic points per sign, 0-56).
    """
    bhinna: dict[Planet, list[int]]
    sarva: list[int]


class ShadbalaResult(BaseModel, frozen=True):
    """Six-fold strength (Shadbala) result for a planet.

    Attributes:
        planet: The planet.
        sthana_bala: Positional strength (in Shashtiamsas).
        dig_bala: Directional strength.
        kaala_bala: Temporal strength.
        chesta_bala: Motional strength.
        naisargika_bala: Natural strength.
        drik_bala: Aspectual strength.
        total: Sum of all six components.
        is_strong: Whether total exceeds the required minimum.
    """
    planet: Planet
    sthana_bala: float
    dig_bala: float
    kaala_bala: float
    chesta_bala: float
    naisargika_bala: float
    drik_bala: float
    total: float
    is_strong: bool


# ---------------------------------------------------------------------------
# Compatibility extension types
# ---------------------------------------------------------------------------

class PoruthamFactor(BaseModel, frozen=True):
    """A single South Indian compatibility factor."""
    name: str
    matched: bool
    score: float
    max_score: float
    description: str = ""


class PoruthamResult(BaseModel, frozen=True):
    """South Indian 10-factor compatibility result.

    Attributes:
        factors: List of 10 PoruthamFactor results.
        matched_count: How many factors matched.
        total_factors: Total factors (10).
    """
    factors: list[PoruthamFactor]
    matched_count: int
    total_factors: int = 10


# ---------------------------------------------------------------------------
# Saham and Festival types
# ---------------------------------------------------------------------------

class SahamPosition(BaseModel, frozen=True):
    """Position of a Saham (Arabic Part / Sensitive Point).

    Attributes:
        name: Saham name (e.g., "Punya Saham").
        longitude: Sidereal longitude (0-360).
        sign: Zodiac sign.
        degree_in_sign: Degree within the sign (0-30).
    """
    name: str
    longitude: float = Field(ge=0.0, lt=360.0)
    sign: Sign
    degree_in_sign: float = Field(ge=0.0, lt=30.0)


class FestivalInfo(BaseModel, frozen=True):
    """Information about a Hindu festival or astronomical event.

    Attributes:
        name: Festival name.
        date: Date of the festival.
        festival_type: Type (e.g., "major", "minor", "astronomical").
        description: Brief description.
    """
    name: str
    date: datetime
    festival_type: str
    description: str
