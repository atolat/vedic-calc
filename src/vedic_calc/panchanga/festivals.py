"""
Hindu festival detector.

Detects major Hindu festivals for a given year by computing panchanga
(tithi, nakshatra) for targeted date ranges and checking for specific
lunar conditions that define each festival.

APPROACH:
    Rather than scanning all 365 days (expensive — each panchanga call
    involves Swiss Ephemeris computations), we scan narrow date windows
    where each festival is expected. Total: ~50-60 panchanga calculations
    per year.

    Most Hindu festivals are defined by their tithi (lunar day):
    - Shukla Paksha tithis 1-15 (waxing moon, new moon to full moon)
    - Krishna Paksha tithis 16-30 (waning moon, full moon to new moon)

    One exception: Makar Sankranti is a solar festival (Sun entering
    Capricorn), so we check the Sun's longitude directly.

SOURCE: Traditional Hindu Panchanga / Panchang references.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from vedic_calc.core.constants import Ayanamsa, Planet
from vedic_calc.core.ephemeris import _to_julian_day, get_ayanamsa, get_planet_longitude
from vedic_calc.core.types import FestivalInfo
from vedic_calc.panchanga.calculator import calculate_panchanga


# ---------------------------------------------------------------------------
# Festival definitions: (name, month_start, month_end, target_tithi,
#                        festival_type, description)
# month_start/month_end define the scanning window.
# target_tithi is the tithi number (1-30) that triggers the festival.
# ---------------------------------------------------------------------------

_TITHI_FESTIVALS: list[tuple[str, int, int, int, str, str]] = [
    (
        "Maha Shivaratri",
        2, 3, 29,
        "major",
        "Night of Lord Shiva. Krishna Chaturdashi (14th of waning moon) "
        "in Magha/Phalguna month.",
    ),
    (
        "Holi",
        2, 3, 15,
        "major",
        "Festival of colors. Phalguna Purnima (full moon).",
    ),
    (
        "Ram Navami",
        3, 4, 9,
        "major",
        "Birthday of Lord Rama. Chaitra Shukla Navami.",
    ),
    (
        "Akshaya Tritiya",
        4, 5, 3,
        "major",
        "Auspicious day for new beginnings. Vaishakha Shukla Tritiya.",
    ),
    (
        "Guru Purnima",
        6, 7, 15,
        "major",
        "Day of honoring the Guru. Ashadha Purnima.",
    ),
    (
        "Raksha Bandhan",
        7, 8, 15,
        "major",
        "Festival of the sacred thread. Shravana Purnima.",
    ),
    (
        "Janmashtami",
        7, 9, 23,
        "major",
        "Birthday of Lord Krishna. Bhadrapada Krishna Ashtami.",
    ),
    (
        "Ganesh Chaturthi",
        8, 9, 4,
        "major",
        "Birthday of Lord Ganesha. Bhadrapada Shukla Chaturthi.",
    ),
    (
        "Navaratri",
        9, 10, 1,
        "major",
        "Nine nights of Goddess Durga. Ashwin Shukla Pratipada.",
    ),
    (
        "Dussehra",
        9, 10, 10,
        "major",
        "Victory of good over evil. Ashwin Shukla Dashami (Vijayadashami).",
    ),
    (
        "Diwali",
        10, 11, 30,
        "major",
        "Festival of lights. Kartik Amavasya (new moon).",
    ),
]


def _find_first_tithi_in_range(
    target_tithi: int,
    start_date: datetime,
    end_date: datetime,
    latitude: float,
    longitude: float,
    timezone_offset: float,
) -> datetime | None:
    """Scan a date range and return the first date matching the target tithi.

    Args:
        target_tithi: The tithi number to search for (1-30).
        start_date: Start of the scanning window.
        end_date: End of the scanning window.
        latitude: Geographic latitude.
        longitude: Geographic longitude.
        timezone_offset: UTC offset in hours.

    Returns:
        The datetime of the first matching date, or None if not found.
    """
    current = start_date
    while current <= end_date:
        panchanga = calculate_panchanga(
            current.year, current.month, current.day,
            latitude, longitude, timezone_offset,
        )
        if panchanga.tithi_number == target_tithi:
            return datetime(current.year, current.month, current.day)
        current += timedelta(days=1)
    return None


def _find_makar_sankranti(
    year: int,
    latitude: float,
    longitude: float,
    timezone_offset: float,
) -> FestivalInfo | None:
    """Detect Makar Sankranti — the day the Sun enters Capricorn (270 deg sidereal).

    The Sun typically enters Capricorn around January 14-15. We check
    each day from January 13 to January 16 and look for the longitude
    crossing 270 degrees.

    Args:
        year: Calendar year.
        latitude: Geographic latitude (unused, but kept for consistency).
        longitude: Geographic longitude (unused).
        timezone_offset: UTC offset in hours.

    Returns:
        FestivalInfo for Makar Sankranti, or None if not detected.
    """
    for day in range(13, 17):
        # Get Sun's longitude at ~noon local time
        ut_hour = 12.0 - timezone_offset
        jd = _to_julian_day(year, 1, day, ut_hour)
        sun_lon, _ = get_planet_longitude(jd, Planet.SUN, Ayanamsa.LAHIRI)

        # Check if Sun is in very early Capricorn (just crossed 270 deg)
        # Capricorn spans 270-300 degrees. We want the day it enters.
        if 270.0 <= sun_lon < 275.0:
            return FestivalInfo(
                name="Makar Sankranti",
                date=datetime(year, 1, day),
                festival_type="major",
                description=(
                    "Sun enters Capricorn (Makara). Harvest festival celebrated "
                    "across India as Pongal, Lohri, Bihu, Uttarayan."
                ),
            )

    return None


def get_festivals(
    year: int,
    latitude: float = 19.076,
    longitude: float = 72.878,
    timezone_offset: float = 5.5,
) -> list[FestivalInfo]:
    """Detect major Hindu festivals for a given year.

    Uses a targeted scanning approach: for each known festival, scans
    only the 2-3 month window where it is expected to occur, checking
    the panchanga tithi each day. This keeps the total number of
    panchanga calculations to ~50-60 per year.

    Festivals detected:
    - Makar Sankranti (solar: Sun enters Capricorn)
    - Maha Shivaratri (Krishna Chaturdashi in Feb/Mar)
    - Holi (Phalguna Purnima in Feb/Mar)
    - Ram Navami (Chaitra Shukla Navami in Mar/Apr)
    - Akshaya Tritiya (Vaishakha Shukla Tritiya in Apr/May)
    - Guru Purnima (Ashadha Purnima in Jun/Jul)
    - Raksha Bandhan (Shravana Purnima in Jul/Aug)
    - Janmashtami (Krishna Ashtami in Jul/Sep)
    - Ganesh Chaturthi (Bhadrapada Shukla Chaturthi in Aug/Sep)
    - Navaratri (Ashwin Shukla Pratipada in Sep/Oct)
    - Dussehra (Ashwin Shukla Dashami in Sep/Oct)
    - Diwali (Kartik Amavasya in Oct/Nov)

    Args:
        year: Calendar year to scan.
        latitude: Geographic latitude. Defaults to Mumbai (19.076 N).
        longitude: Geographic longitude. Defaults to Mumbai (72.878 E).
        timezone_offset: UTC offset in hours. Defaults to IST (5.5).

    Returns:
        List of FestivalInfo objects sorted by date.

    Example:
        >>> festivals = get_festivals(2026)
        >>> len(festivals) > 0
        True
        >>> any(f.name == "Diwali" for f in festivals)
        True
    """
    festivals: list[FestivalInfo] = []

    # --- Makar Sankranti (solar event, not tithi-based) ---
    sankranti = _find_makar_sankranti(year, latitude, longitude, timezone_offset)
    if sankranti is not None:
        festivals.append(sankranti)

    # --- Tithi-based festivals ---
    for name, month_start, month_end, target_tithi, ftype, description in _TITHI_FESTIVALS:
        start_date = datetime(year, month_start, 1)
        # End date: last day of month_end
        if month_end == 12:
            end_date = datetime(year, 12, 31)
        else:
            end_date = datetime(year, month_end + 1, 1) - timedelta(days=1)

        match_date = _find_first_tithi_in_range(
            target_tithi, start_date, end_date,
            latitude, longitude, timezone_offset,
        )
        if match_date is not None:
            festivals.append(FestivalInfo(
                name=name,
                date=match_date,
                festival_type=ftype,
                description=description,
            ))

    # Sort by date
    festivals.sort(key=lambda f: f.date)

    return festivals
