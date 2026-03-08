"""
Constants for Vedic astrology calculations.

This module defines all the fundamental enumerations and lookup tables used
throughout the library: planets, signs, nakshatras, and their relationships.

All data comes from classical Vedic astrology texts (BPHS, Surya Siddhanta).
"""

from enum import IntEnum


# ---------------------------------------------------------------------------
# Planets (Grahas)
# ---------------------------------------------------------------------------

class Planet(IntEnum):
    """The nine Vedic planets (Navagraha).

    The first seven are physical celestial bodies. Rahu and Ketu are the
    lunar nodes (north and south respectively) — mathematically derived
    points where the Moon's orbit crosses the ecliptic.
    """
    SUN = 0
    MOON = 1
    MARS = 2
    MERCURY = 3
    JUPITER = 4
    VENUS = 5
    SATURN = 6
    RAHU = 7      # North lunar node (mean node)
    KETU = 8      # South lunar node (always 180° from Rahu)


# Mapping from our Planet enum to Swiss Ephemeris planet constants.
# Only used by ephemeris.py — kept here so the mapping is visible.
# Rahu uses SE_MEAN_NODE (10); Ketu is computed as Rahu + 180°.
PLANET_TO_SWE = {
    Planet.SUN: 0,       # SE_SUN
    Planet.MOON: 1,      # SE_MOON
    Planet.MARS: 4,      # SE_MARS
    Planet.MERCURY: 2,   # SE_MERCURY
    Planet.JUPITER: 5,   # SE_JUPITER
    Planet.VENUS: 3,     # SE_VENUS
    Planet.SATURN: 6,    # SE_SATURN
    Planet.RAHU: 10,     # SE_MEAN_NODE (Rahu = mean north node)
    # Ketu is derived: (Rahu longitude + 180) % 360
}

# Human-readable names for display
PLANET_NAMES = {
    Planet.SUN: "Sun (Surya)",
    Planet.MOON: "Moon (Chandra)",
    Planet.MARS: "Mars (Mangala)",
    Planet.MERCURY: "Mercury (Budha)",
    Planet.JUPITER: "Jupiter (Guru)",
    Planet.VENUS: "Venus (Shukra)",
    Planet.SATURN: "Saturn (Shani)",
    Planet.RAHU: "Rahu",
    Planet.KETU: "Ketu",
}


# ---------------------------------------------------------------------------
# Signs (Rashis)
# ---------------------------------------------------------------------------

class Sign(IntEnum):
    """The 12 zodiac signs (Rashis) in sidereal order.

    Numbering starts at 1 (Aries) to match traditional Vedic convention.
    """
    ARIES = 1
    TAURUS = 2
    GEMINI = 3
    CANCER = 4
    LEO = 5
    VIRGO = 6
    LIBRA = 7
    SCORPIO = 8
    SAGITTARIUS = 9
    CAPRICORN = 10
    AQUARIUS = 11
    PISCES = 12


SIGN_NAMES = {
    Sign.ARIES: "Aries (Mesha)",
    Sign.TAURUS: "Taurus (Vrishabha)",
    Sign.GEMINI: "Gemini (Mithuna)",
    Sign.CANCER: "Cancer (Karka)",
    Sign.LEO: "Leo (Simha)",
    Sign.VIRGO: "Virgo (Kanya)",
    Sign.LIBRA: "Libra (Tula)",
    Sign.SCORPIO: "Scorpio (Vrishchika)",
    Sign.SAGITTARIUS: "Sagittarius (Dhanu)",
    Sign.CAPRICORN: "Capricorn (Makara)",
    Sign.AQUARIUS: "Aquarius (Kumbha)",
    Sign.PISCES: "Pisces (Meena)",
}

# Which planet rules each sign (BPHS Chapter 4)
SIGN_LORDS = {
    Sign.ARIES: Planet.MARS,
    Sign.TAURUS: Planet.VENUS,
    Sign.GEMINI: Planet.MERCURY,
    Sign.CANCER: Planet.MOON,
    Sign.LEO: Planet.SUN,
    Sign.VIRGO: Planet.MERCURY,
    Sign.LIBRA: Planet.VENUS,
    Sign.SCORPIO: Planet.MARS,
    Sign.SAGITTARIUS: Planet.JUPITER,
    Sign.CAPRICORN: Planet.SATURN,
    Sign.AQUARIUS: Planet.SATURN,
    Sign.PISCES: Planet.JUPITER,
}


# ---------------------------------------------------------------------------
# Nakshatras (Lunar Mansions)
# ---------------------------------------------------------------------------

class Nakshatra(IntEnum):
    """The 27 Nakshatras (lunar mansions).

    Each nakshatra spans 13°20' (13.3333°) of the zodiac.
    Numbering starts at 1 (Ashwini at 0° Aries).
    """
    ASHWINI = 1
    BHARANI = 2
    KRITTIKA = 3
    ROHINI = 4
    MRIGASHIRA = 5
    ARDRA = 6
    PUNARVASU = 7
    PUSHYA = 8
    ASHLESHA = 9
    MAGHA = 10
    PURVA_PHALGUNI = 11
    UTTARA_PHALGUNI = 12
    HASTA = 13
    CHITRA = 14
    SWATI = 15
    VISHAKHA = 16
    ANURADHA = 17
    JYESHTHA = 18
    MOOLA = 19
    PURVA_ASHADHA = 20
    UTTARA_ASHADHA = 21
    SHRAVANA = 22
    DHANISHTA = 23
    SHATABHISHA = 24
    PURVA_BHADRAPADA = 25
    UTTARA_BHADRAPADA = 26
    REVATI = 27


# Each nakshatra's ruling planet, in order (used for Vimsottari dasha).
# This sequence repeats every 9 nakshatras: Ketu, Venus, Sun, Moon, Mars,
# Rahu, Jupiter, Saturn, Mercury.
NAKSHATRA_LORDS = {
    Nakshatra.ASHWINI: Planet.KETU,
    Nakshatra.BHARANI: Planet.VENUS,
    Nakshatra.KRITTIKA: Planet.SUN,
    Nakshatra.ROHINI: Planet.MOON,
    Nakshatra.MRIGASHIRA: Planet.MARS,
    Nakshatra.ARDRA: Planet.RAHU,
    Nakshatra.PUNARVASU: Planet.JUPITER,
    Nakshatra.PUSHYA: Planet.SATURN,
    Nakshatra.ASHLESHA: Planet.MERCURY,
    Nakshatra.MAGHA: Planet.KETU,
    Nakshatra.PURVA_PHALGUNI: Planet.VENUS,
    Nakshatra.UTTARA_PHALGUNI: Planet.SUN,
    Nakshatra.HASTA: Planet.MOON,
    Nakshatra.CHITRA: Planet.MARS,
    Nakshatra.SWATI: Planet.RAHU,
    Nakshatra.VISHAKHA: Planet.JUPITER,
    Nakshatra.ANURADHA: Planet.SATURN,
    Nakshatra.JYESHTHA: Planet.MERCURY,
    Nakshatra.MOOLA: Planet.KETU,
    Nakshatra.PURVA_ASHADHA: Planet.VENUS,
    Nakshatra.UTTARA_ASHADHA: Planet.SUN,
    Nakshatra.SHRAVANA: Planet.MOON,
    Nakshatra.DHANISHTA: Planet.MARS,
    Nakshatra.SHATABHISHA: Planet.RAHU,
    Nakshatra.PURVA_BHADRAPADA: Planet.JUPITER,
    Nakshatra.UTTARA_BHADRAPADA: Planet.SATURN,
    Nakshatra.REVATI: Planet.MERCURY,
}

NAKSHATRA_NAMES = {
    Nakshatra.ASHWINI: "Ashwini",
    Nakshatra.BHARANI: "Bharani",
    Nakshatra.KRITTIKA: "Krittika",
    Nakshatra.ROHINI: "Rohini",
    Nakshatra.MRIGASHIRA: "Mrigashira",
    Nakshatra.ARDRA: "Ardra",
    Nakshatra.PUNARVASU: "Punarvasu",
    Nakshatra.PUSHYA: "Pushya",
    Nakshatra.ASHLESHA: "Ashlesha",
    Nakshatra.MAGHA: "Magha",
    Nakshatra.PURVA_PHALGUNI: "Purva Phalguni",
    Nakshatra.UTTARA_PHALGUNI: "Uttara Phalguni",
    Nakshatra.HASTA: "Hasta",
    Nakshatra.CHITRA: "Chitra",
    Nakshatra.SWATI: "Swati",
    Nakshatra.VISHAKHA: "Vishakha",
    Nakshatra.ANURADHA: "Anuradha",
    Nakshatra.JYESHTHA: "Jyeshtha",
    Nakshatra.MOOLA: "Moola",
    Nakshatra.PURVA_ASHADHA: "Purva Ashadha",
    Nakshatra.UTTARA_ASHADHA: "Uttara Ashadha",
    Nakshatra.SHRAVANA: "Shravana",
    Nakshatra.DHANISHTA: "Dhanishta",
    Nakshatra.SHATABHISHA: "Shatabhisha",
    Nakshatra.PURVA_BHADRAPADA: "Purva Bhadrapada",
    Nakshatra.UTTARA_BHADRAPADA: "Uttara Bhadrapada",
    Nakshatra.REVATI: "Revati",
}


# ---------------------------------------------------------------------------
# Derived constants
# ---------------------------------------------------------------------------

# Degrees per nakshatra: 360° / 27 = 13°20' = 13.3333...°
NAKSHATRA_SPAN = 360.0 / 27.0

# Degrees per pada (quarter of a nakshatra): 360° / 108 = 3°20'
PADA_SPAN = 360.0 / 108.0

# Vimsottari dasha total cycle = 120 years
# Each planet's mahadasha duration in years
VIMSOTTARI_YEARS = {
    Planet.KETU: 7,
    Planet.VENUS: 20,
    Planet.SUN: 6,
    Planet.MOON: 10,
    Planet.MARS: 7,
    Planet.RAHU: 18,
    Planet.JUPITER: 16,
    Planet.SATURN: 19,
    Planet.MERCURY: 17,
}

# The fixed sequence of dasha lords (repeats cyclically)
VIMSOTTARI_ORDER = [
    Planet.KETU, Planet.VENUS, Planet.SUN, Planet.MOON, Planet.MARS,
    Planet.RAHU, Planet.JUPITER, Planet.SATURN, Planet.MERCURY,
]

VIMSOTTARI_TOTAL_YEARS = 120  # Sum of all mahadasha periods


# ---------------------------------------------------------------------------
# Ayanamsa modes
# ---------------------------------------------------------------------------

class Ayanamsa(IntEnum):
    """Supported ayanamsa (precession correction) modes.

    The ayanamsa is subtracted from tropical longitudes to get sidereal
    positions. Lahiri is the most commonly used in India (adopted by the
    Indian government's calendar reform committee).
    """
    LAHIRI = 1          # Chitrapaksha — most common in India
    RAMAN = 3           # B.V. Raman's ayanamsa
    KP = 5              # Krishnamurti Paddhati
    TRUE_CHITRAPAKSHA = 27  # True Chitrapaksha (Spica at 0° Libra)
