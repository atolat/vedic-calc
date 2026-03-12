"""
Special lagna (ascendant variant) calculator.

Beyond the standard ascendant (Lagna), Vedic astrology uses several
"special lagnas" — sensitive points derived from the ascendant, Sun,
Moon, and the time elapsed since sunrise. Each special lagna offers
a different lens for chart interpretation.

THE FOUR SPECIAL LAGNAS COMPUTED HERE:

    1. BHAVA LAGNA (BL) — "House Ascendant"
       Moves at the rate of the Sun's daily motion through the zodiac.
       Used in Jaimini and some Parashari techniques for house analysis.
       Formula: BL = Lagna + (ishta_kala_ghatis × mean_sun_daily_motion / 60)

    2. HORA LAGNA (HL) — "Wealth Ascendant"
       Moves through one sign (30°) per hora (hour). Completes two
       full zodiac cycles per day (720° in 24 hours = 30°/hour).
       Key indicator for wealth, financial matters.
       Formula: HL = Sun_at_sunrise + (hours_from_sunrise × 30)

    3. GHATI LAGNA (GL) — "Authority Ascendant"
       Moves through 6° per ghati (24 minutes). Completes five full
       zodiac cycles per day (360° × 5 = 1800° in 60 ghatis).
       Used for power, position, and authority matters.
       Formula: GL = Sun_at_sunrise + (ishta_kala_ghatis × 6)

    4. SREE LAGNA (SL) — "Prosperity Ascendant"
       Combines the Lagna, Moon, and Sun to create a wealth-specific
       reference point. Important in Jaimini astrology.
       Formula: SL = (Lagna + Moon - Sun) mod 360

TIME UNITS:
    - 1 ghati (nadika) = 24 minutes = 2/5 of an hour
    - 60 ghatis = 1 day (24 hours)
    - Ishta Kala = time elapsed from sunrise to birth, in ghatis

SOURCE REFERENCES:
    - Brihat Parashara Hora Shastra (BPHS), Ch. 5
    - Jaimini Sutras
    - Uttara Kalamrita

Example:
    >>> from vedic_calc.chart.special_lagnas import calculate_special_lagnas
    >>> lagnas = calculate_special_lagnas(chart)
    >>> for name, lagna in lagnas.items():
    ...     print(f"{name}: {lagna.degree_in_sign:.2f}° {lagna.sign.name}")
"""

from __future__ import annotations

from vedic_calc.chart.calculator import longitude_to_degree_in_sign, longitude_to_sign
from vedic_calc.core.constants import Ayanamsa, Planet
from vedic_calc.core.ephemeris import _to_julian_day, get_ayanamsa, get_sunrise_sunset
from vedic_calc.core.types import BirthChart, SpecialLagna


# Mean daily motion of the Sun in degrees (~0.9856°/day)
_MEAN_SUN_DAILY_MOTION = 0.9856


def _make_special_lagna(name: str, longitude: float) -> SpecialLagna:
    """Create a SpecialLagna from a name and raw longitude."""
    lon = longitude % 360.0
    return SpecialLagna(
        name=name,
        longitude=round(lon, 4),
        sign=longitude_to_sign(lon),
        degree_in_sign=round(longitude_to_degree_in_sign(lon), 4),
    )


def calculate_special_lagnas(chart: BirthChart) -> dict[str, SpecialLagna]:
    """Calculate the four special lagnas for a birth chart.

    Uses the birth chart's date, time, and location to compute sunrise,
    then derives each special lagna from the elapsed time since sunrise.

    Args:
        chart: A complete BirthChart with planetary positions,
               birth_datetime, latitude, longitude, and timezone_offset.

    Returns:
        A dict mapping lagna name to SpecialLagna:
        {"Bhava Lagna": ..., "Hora Lagna": ..., "Ghati Lagna": ...,
         "Sree Lagna": ...}
    """
    dt = chart.birth_datetime
    tz = chart.timezone_offset

    # --- Step 1: Compute Julian Day at midnight UT for the birth date ---
    # We need this to find sunrise for the day.
    jd_midnight_ut = _to_julian_day(dt.year, dt.month, dt.day, 0.0 - tz)

    # --- Step 2: Get sunrise JD for the birth location ---
    sunrise_jd, _ = get_sunrise_sunset(
        jd_midnight_ut, chart.latitude, chart.longitude
    )

    # --- Step 3: Compute birth JD in UT ---
    birth_hour_decimal = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    birth_jd = _to_julian_day(dt.year, dt.month, dt.day, birth_hour_decimal - tz)

    # --- Step 4: Ishta Kala (time from sunrise) ---
    # In days, then convert to ghatis (60 ghatis per day) and hours.
    ishta_kala_days = birth_jd - sunrise_jd
    ishta_kala_ghatis = ishta_kala_days * 60.0
    ishta_kala_hours = ishta_kala_days * 24.0

    # --- Key longitudes ---
    asc_lon = chart.ascendant.longitude
    sun_lon = chart.planets[Planet.SUN].longitude
    moon_lon = chart.planets[Planet.MOON].longitude

    # --- Approximate Sun's longitude at sunrise ---
    # The chart's Sun longitude is for birth time; sunrise is earlier.
    # Adjust backward by the fraction of a day between sunrise and birth.
    sun_at_sunrise = (sun_lon - ishta_kala_days * _MEAN_SUN_DAILY_MOTION) % 360.0

    # --- Bhava Lagna (BL) ---
    # BL = Ascendant + (ishta_kala_ghatis × Sun_daily_motion / 60)
    bl_lon = asc_lon + (ishta_kala_ghatis * _MEAN_SUN_DAILY_MOTION / 60.0)

    # --- Hora Lagna (HL) ---
    # HL advances 30° per hour from the Sun's position at sunrise.
    # In 24 hours it covers 720° (two full zodiac cycles).
    hl_lon = sun_at_sunrise + (ishta_kala_hours * 30.0)

    # --- Ghati Lagna (GL) ---
    # GL advances 6° per ghati from the Sun's position at sunrise.
    # In 60 ghatis (1 day) it covers 360° (one full zodiac cycle).
    gl_lon = sun_at_sunrise + (ishta_kala_ghatis * 6.0)

    # --- Sree Lagna (SL) ---
    # SL = Ascendant + Moon - Sun (a luni-solar prosperity point).
    sl_lon = asc_lon + moon_lon - sun_lon

    return {
        "Bhava Lagna": _make_special_lagna("Bhava Lagna", bl_lon),
        "Hora Lagna": _make_special_lagna("Hora Lagna", hl_lon),
        "Ghati Lagna": _make_special_lagna("Ghati Lagna", gl_lon),
        "Sree Lagna": _make_special_lagna("Sree Lagna", sl_lon),
    }
