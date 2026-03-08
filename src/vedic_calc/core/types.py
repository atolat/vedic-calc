"""
Pydantic models for all Vedic astrology data structures.

These are the primary data types returned by vedic-calc functions.
All models are frozen (immutable) and JSON-serializable.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from vedic_calc.core.constants import Ayanamsa, Nakshatra, Planet, Sign


class NakshatraInfo(BaseModel, frozen=True):
    """Information about a nakshatra position.

    Attributes:
        nakshatra: The nakshatra (1-27).
        pada: The pada/quarter within the nakshatra (1-4).
        lord: The ruling planet of this nakshatra.
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

    Attributes:
        planet: Which planet.
        longitude: Sidereal longitude in degrees (0-360).
        sign: Which zodiac sign the planet occupies.
        degree_in_sign: Degrees within the sign (0-30).
        nakshatra_info: The nakshatra and pada this planet falls in.
        is_retrograde: Whether the planet is in retrograde motion.

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

    In the Whole Sign house system (default for Vedic astrology),
    the ascendant's sign becomes the 1st house, the next sign is
    the 2nd house, and so on.

    Attributes:
        house_number: House number (1-12).
        sign: The zodiac sign occupying this house.
        lord: The planet that rules this house's sign.
    """
    house_number: int = Field(ge=1, le=12)
    sign: Sign
    lord: Planet


class BirthChart(BaseModel, frozen=True):
    """A complete Vedic birth chart (Kundli / Janma Patri).

    Contains all planetary positions, house placements, and metadata
    about the chart calculation.

    Attributes:
        planets: Positions of all 9 planets.
        houses: The 12 houses with their signs and lords.
        ascendant: The ascendant (lagna) position — also the 1st house cusp.
        ayanamsa: Which ayanamsa was used for calculation.
        ayanamsa_degrees: The ayanamsa value in degrees at the time of birth.
        birth_datetime: The birth date and time (local time).
        latitude: Birth latitude.
        longitude: Birth longitude.
        timezone_offset: UTC offset in hours (e.g., 5.5 for IST).

    Example:
        >>> chart = calculate_chart(1990, 3, 15, 10, 30, 19.076, 72.878, 5.5)
        >>> chart.ascendant.sign
        <Sign.GEMINI: 3>
        >>> chart.planets[Planet.MOON].nakshatra_info.nakshatra
        <Nakshatra.ROHINI: 4>
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

    Attributes:
        lord: The ruling planet of this period.
        level: "mahadasha", "antardasha", or "pratyantardasha".
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

    Attributes:
        date: The date this panchanga is for.
        vara: Weekday name (e.g., "Sunday" / "Ravivara").
        tithi_number: Tithi number (1-30). 1-15 are Shukla Paksha, 16-30 Krishn Paksha.
        tithi_name: Human-readable tithi name.
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
