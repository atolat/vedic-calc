"""
Constants for Vedic astrology calculations.

This module defines all the fundamental enumerations and lookup tables used
throughout the library: planets, signs, nakshatras, and their relationships.

All data comes from classical Vedic astrology texts, primarily:
  - BPHS: Brihat Parashara Hora Shastra (the foundational text of Vedic astrology,
    attributed to sage Parashara, ~1500 BCE). Think of it as the "specification
    document" for Vedic astrology.
  - Surya Siddhanta: An ancient Indian astronomical text (~400 CE) that provides
    the mathematical models for planetary motion.

TERMINOLOGY FOR NEWCOMERS:
  - "Graha" = planet (literally "that which seizes/influences")
  - "Rashi" = zodiac sign (a 30° segment of the sky)
  - "Nakshatra" = lunar mansion (a 13.33° segment, there are 27)
  - "Ayanamsa" = the angular offset between Western and Vedic zodiacs
  - "Dasha" = planetary period (a time-based prediction system)
"""

from enum import IntEnum


# ---------------------------------------------------------------------------
# Planets (Grahas)
# ---------------------------------------------------------------------------
# Vedic astrology uses 9 "planets" (Navagraha = "nine planets"):
#   - 7 visible celestial bodies: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn
#   - 2 lunar nodes: Rahu (north node) and Ketu (south node)
#
# The lunar nodes are not physical bodies — they are the two points where the
# Moon's orbital plane crosses the Earth's orbital plane (the ecliptic). These
# points are where eclipses can occur, which is why ancient astronomers
# considered them important.
#
# Rahu = ascending node (where Moon crosses from south to north of the ecliptic)
# Ketu = descending node (always exactly opposite Rahu, i.e., 180° away)

class Planet(IntEnum):
    """The nine Vedic planets (Navagraha).

    The first seven are physical celestial bodies. Rahu and Ketu are the
    lunar nodes (north and south respectively) — mathematically derived
    points where the Moon's orbit crosses the ecliptic.

    In Vedic astrology, each planet "rules" certain signs, nakshatras,
    and time periods (dashas). Their position in your birth chart is said
    to influence different areas of life.
    """
    SUN = 0       # Surya — represents soul, authority, father
    MOON = 1      # Chandra — represents mind, emotions, mother
    MARS = 2      # Mangala — represents energy, courage, siblings
    MERCURY = 3   # Budha — represents intellect, communication, speech
    JUPITER = 4   # Guru — represents wisdom, expansion, teacher
    VENUS = 5     # Shukra — represents love, beauty, luxury
    SATURN = 6    # Shani — represents discipline, delays, karma
    RAHU = 7      # North lunar node — represents obsession, foreign things
    KETU = 8      # South lunar node — represents detachment, spirituality


# ---------------------------------------------------------------------------
# Planet-to-Swiss-Ephemeris mapping
# ---------------------------------------------------------------------------
# The Swiss Ephemeris (pyswisseph) uses its own integer constants for planets.
# This mapping translates our Planet enum → Swiss Ephemeris constants.
#
# Note: Swiss Ephemeris numbering is different from ours:
#   SE_SUN=0, SE_MOON=1, SE_MERCURY=2, SE_VENUS=3, SE_MARS=4,
#   SE_JUPITER=5, SE_SATURN=6, SE_MEAN_NODE=10
#
# Ketu has no Swiss Ephemeris constant because it's always 180° from Rahu.
# We compute it ourselves: ketu_longitude = (rahu_longitude + 180) % 360

PLANET_TO_SWE = {
    Planet.SUN: 0,       # SE_SUN
    Planet.MOON: 1,      # SE_MOON
    Planet.MARS: 4,      # SE_MARS
    Planet.MERCURY: 2,   # SE_MERCURY
    Planet.JUPITER: 5,   # SE_JUPITER
    Planet.VENUS: 3,     # SE_VENUS
    Planet.SATURN: 6,    # SE_SATURN
    Planet.RAHU: 10,     # SE_MEAN_NODE (mean north lunar node)
    # Ketu is derived: (Rahu longitude + 180) % 360
}

# Human-readable names in English (Sanskrit name in parentheses)
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
# The zodiac is a 360° band of sky through which the Sun, Moon, and planets
# appear to move. It is divided into 12 equal segments of 30° each, called
# signs (rashis).
#
# IMPORTANT — TROPICAL vs SIDEREAL:
#   Western astrology uses the "tropical" zodiac, anchored to the seasons
#   (0° Aries = spring equinox). Vedic astrology uses the "sidereal" zodiac,
#   anchored to the fixed stars. Due to Earth's axial precession (a slow
#   wobble over ~26,000 years), these two zodiacs have drifted apart by ~24°.
#   This drift is called the "ayanamsa" (see Ayanamsa section below).
#
#   In practice: if Western astrology says your Sun is in Aries, Vedic
#   astrology might say it's in Pisces (shifted back by ~24°).
#
# Each sign has a "lord" (ruling planet) that is said to influence the
# qualities of that sign. Source: BPHS Chapter 4, Verse 3.

class Sign(IntEnum):
    """The 12 zodiac signs (Rashis) in sidereal order.

    Numbering starts at 1 (Aries) to match traditional Vedic convention.
    Each sign spans exactly 30° of the 360° zodiac.

    Think of signs as 12 equal "zones" in the sky:
        Aries = 0°-30°, Taurus = 30°-60°, ..., Pisces = 330°-360°

    Formula: sign_number = floor(longitude / 30) + 1
    """
    ARIES = 1        # Mesha      — Fire sign, ruled by Mars
    TAURUS = 2       # Vrishabha  — Earth sign, ruled by Venus
    GEMINI = 3       # Mithuna    — Air sign, ruled by Mercury
    CANCER = 4       # Karka      — Water sign, ruled by Moon
    LEO = 5          # Simha      — Fire sign, ruled by Sun
    VIRGO = 6        # Kanya      — Earth sign, ruled by Mercury
    LIBRA = 7        # Tula       — Air sign, ruled by Venus
    SCORPIO = 8      # Vrishchika — Water sign, ruled by Mars
    SAGITTARIUS = 9  # Dhanu      — Fire sign, ruled by Jupiter
    CAPRICORN = 10   # Makara     — Earth sign, ruled by Saturn
    AQUARIUS = 11    # Kumbha     — Air sign, ruled by Saturn
    PISCES = 12      # Meena      — Water sign, ruled by Jupiter


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

# Which planet rules ("lords over") each sign.
# Source: BPHS Chapter 4, Verse 3.
#
# Note: Mars rules both Aries and Scorpio, Venus rules Taurus and Libra, etc.
# This is because there are 12 signs but only 7 visible planets (excluding
# Rahu/Ketu which don't rule signs). Sun and Moon each rule one sign;
# the other 5 planets each rule two signs.
SIGN_LORDS = {
    Sign.ARIES: Planet.MARS,          # Mars rules Aries
    Sign.TAURUS: Planet.VENUS,        # Venus rules Taurus
    Sign.GEMINI: Planet.MERCURY,      # Mercury rules Gemini
    Sign.CANCER: Planet.MOON,         # Moon rules Cancer
    Sign.LEO: Planet.SUN,             # Sun rules Leo
    Sign.VIRGO: Planet.MERCURY,       # Mercury rules Virgo (2nd sign)
    Sign.LIBRA: Planet.VENUS,         # Venus rules Libra (2nd sign)
    Sign.SCORPIO: Planet.MARS,        # Mars rules Scorpio (2nd sign)
    Sign.SAGITTARIUS: Planet.JUPITER, # Jupiter rules Sagittarius
    Sign.CAPRICORN: Planet.SATURN,    # Saturn rules Capricorn
    Sign.AQUARIUS: Planet.SATURN,     # Saturn rules Aquarius (2nd sign)
    Sign.PISCES: Planet.JUPITER,      # Jupiter rules Pisces (2nd sign)
}


# ---------------------------------------------------------------------------
# Nakshatras (Lunar Mansions)
# ---------------------------------------------------------------------------
# Nakshatras are a uniquely Vedic concept — they divide the zodiac into 27
# segments (instead of 12 signs). Each nakshatra spans 13°20' (13.3333°).
#
# WHY 27?
#   The Moon takes ~27.3 days to orbit the Earth (sidereal month). Ancient
#   Indian astronomers divided the sky into 27 segments so the Moon passes
#   through roughly one nakshatra per day. This makes the Moon's nakshatra
#   a natural "daily clock" in the sky.
#
# PADAS (quarters):
#   Each nakshatra is further divided into 4 equal parts called "padas"
#   (quarters), each spanning 3°20' (3.3333°). There are 27 × 4 = 108
#   padas in total. The number 108 is sacred in Hinduism.
#
# WHY NAKSHATRAS MATTER:
#   - The Moon's nakshatra at birth determines your Vimsottari dasha
#     starting period (a major predictive tool — see dasha module)
#   - Each nakshatra has a ruling planet (used for dasha calculation)
#   - Nakshatras provide finer granularity than signs (13.3° vs 30°)
#
# Formula: nakshatra_number = floor(longitude / 13.3333) + 1
# Formula: pada = floor((longitude % 13.3333) / 3.3333) + 1

class Nakshatra(IntEnum):
    """The 27 Nakshatras (lunar mansions).

    Each nakshatra spans 13°20' (13.3333°) of the zodiac.
    Numbering starts at 1 (Ashwini at 0° Aries).

    The Moon moves through roughly one nakshatra per day. Your birth
    nakshatra (the Moon's nakshatra at birth) is considered very important
    in Vedic astrology — it determines your dasha starting period.
    """
    ASHWINI = 1           # 0°00' - 13°20' Aries
    BHARANI = 2           # 13°20' - 26°40' Aries
    KRITTIKA = 3          # 26°40' Aries - 10°00' Taurus
    ROHINI = 4            # 10°00' - 23°20' Taurus
    MRIGASHIRA = 5        # 23°20' Taurus - 6°40' Gemini
    ARDRA = 6             # 6°40' - 20°00' Gemini
    PUNARVASU = 7         # 20°00' Gemini - 3°20' Cancer
    PUSHYA = 8            # 3°20' - 16°40' Cancer
    ASHLESHA = 9          # 16°40' - 30°00' Cancer
    MAGHA = 10            # 0°00' - 13°20' Leo
    PURVA_PHALGUNI = 11   # 13°20' - 26°40' Leo
    UTTARA_PHALGUNI = 12  # 26°40' Leo - 10°00' Virgo
    HASTA = 13            # 10°00' - 23°20' Virgo
    CHITRA = 14           # 23°20' Virgo - 6°40' Libra
    SWATI = 15            # 6°40' - 20°00' Libra
    VISHAKHA = 16         # 20°00' Libra - 3°20' Scorpio
    ANURADHA = 17         # 3°20' - 16°40' Scorpio
    JYESHTHA = 18         # 16°40' - 30°00' Scorpio
    MOOLA = 19            # 0°00' - 13°20' Sagittarius
    PURVA_ASHADHA = 20    # 13°20' - 26°40' Sagittarius
    UTTARA_ASHADHA = 21   # 26°40' Sagittarius - 10°00' Capricorn
    SHRAVANA = 22         # 10°00' - 23°20' Capricorn
    DHANISHTA = 23        # 23°20' Capricorn - 6°40' Aquarius
    SHATABHISHA = 24      # 6°40' - 20°00' Aquarius
    PURVA_BHADRAPADA = 25 # 20°00' Aquarius - 3°20' Pisces
    UTTARA_BHADRAPADA = 26 # 3°20' - 16°40' Pisces
    REVATI = 27           # 16°40' - 30°00' Pisces


# ---------------------------------------------------------------------------
# Nakshatra ruling planets
# ---------------------------------------------------------------------------
# Each nakshatra is ruled by one of the 9 planets. This ruling planet
# determines which dasha (planetary period) you are in.
#
# The sequence of ruling planets repeats every 9 nakshatras:
#   Ketu → Venus → Sun → Moon → Mars → Rahu → Jupiter → Saturn → Mercury
#
# This means:
#   Nakshatras 1, 10, 19 are all ruled by Ketu
#   Nakshatras 2, 11, 20 are all ruled by Venus
#   ... and so on.
#
# Source: BPHS Chapter 46 (Vimsottari Dasha).

NAKSHATRA_LORDS = {
    Nakshatra.ASHWINI: Planet.KETU,            # Group 1: Ketu rules 1, 10, 19
    Nakshatra.BHARANI: Planet.VENUS,           # Group 2: Venus rules 2, 11, 20
    Nakshatra.KRITTIKA: Planet.SUN,            # Group 3: Sun rules 3, 12, 21
    Nakshatra.ROHINI: Planet.MOON,             # Group 4: Moon rules 4, 13, 22
    Nakshatra.MRIGASHIRA: Planet.MARS,         # Group 5: Mars rules 5, 14, 23
    Nakshatra.ARDRA: Planet.RAHU,              # Group 6: Rahu rules 6, 15, 24
    Nakshatra.PUNARVASU: Planet.JUPITER,       # Group 7: Jupiter rules 7, 16, 25
    Nakshatra.PUSHYA: Planet.SATURN,           # Group 8: Saturn rules 8, 17, 26
    Nakshatra.ASHLESHA: Planet.MERCURY,        # Group 9: Mercury rules 9, 18, 27
    Nakshatra.MAGHA: Planet.KETU,              # Group 1 repeat
    Nakshatra.PURVA_PHALGUNI: Planet.VENUS,    # Group 2 repeat
    Nakshatra.UTTARA_PHALGUNI: Planet.SUN,     # Group 3 repeat
    Nakshatra.HASTA: Planet.MOON,              # Group 4 repeat
    Nakshatra.CHITRA: Planet.MARS,             # Group 5 repeat
    Nakshatra.SWATI: Planet.RAHU,              # Group 6 repeat
    Nakshatra.VISHAKHA: Planet.JUPITER,        # Group 7 repeat
    Nakshatra.ANURADHA: Planet.SATURN,         # Group 8 repeat
    Nakshatra.JYESHTHA: Planet.MERCURY,        # Group 9 repeat
    Nakshatra.MOOLA: Planet.KETU,              # Group 1 repeat
    Nakshatra.PURVA_ASHADHA: Planet.VENUS,     # Group 2 repeat
    Nakshatra.UTTARA_ASHADHA: Planet.SUN,      # Group 3 repeat
    Nakshatra.SHRAVANA: Planet.MOON,           # Group 4 repeat
    Nakshatra.DHANISHTA: Planet.MARS,          # Group 5 repeat
    Nakshatra.SHATABHISHA: Planet.RAHU,        # Group 6 repeat
    Nakshatra.PURVA_BHADRAPADA: Planet.JUPITER, # Group 7 repeat
    Nakshatra.UTTARA_BHADRAPADA: Planet.SATURN, # Group 8 repeat
    Nakshatra.REVATI: Planet.MERCURY,          # Group 9 repeat
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
# This is used to convert a longitude to its nakshatra index.
NAKSHATRA_SPAN = 360.0 / 27.0

# Degrees per pada (quarter of a nakshatra): 360° / 108 = 3°20' = 3.3333°
# Each nakshatra has 4 padas, so 27 × 4 = 108 total padas in the zodiac.
PADA_SPAN = 360.0 / 108.0


# ---------------------------------------------------------------------------
# Vimsottari Dasha constants
# ---------------------------------------------------------------------------
# The Vimsottari Dasha is the most widely used prediction system in Vedic
# astrology. "Vimsottari" means "120" — the full cycle spans 120 years.
#
# HOW IT WORKS (high level):
#   1. Look at where the Moon was at birth → determine the nakshatra
#   2. Each nakshatra has a ruling planet (see NAKSHATRA_LORDS above)
#   3. That planet's dasha (period) is active at birth
#   4. After it ends, the next planet in the sequence takes over
#   5. The sequence repeats: Ketu→Venus→Sun→Moon→Mars→Rahu→Jupiter→Saturn→Mercury
#
# Each planet's period has a fixed duration (in years):
#   Ketu=7, Venus=20, Sun=6, Moon=10, Mars=7, Rahu=18, Jupiter=16, Saturn=19, Mercury=17
#   Total: 7+20+6+10+7+18+16+19+17 = 120 years
#
# Source: BPHS Chapter 46.

VIMSOTTARI_YEARS = {
    Planet.KETU: 7,       # Ketu dasha lasts 7 years
    Planet.VENUS: 20,     # Venus dasha lasts 20 years (longest)
    Planet.SUN: 6,        # Sun dasha lasts 6 years (shortest)
    Planet.MOON: 10,      # Moon dasha lasts 10 years
    Planet.MARS: 7,       # Mars dasha lasts 7 years
    Planet.RAHU: 18,      # Rahu dasha lasts 18 years
    Planet.JUPITER: 16,   # Jupiter dasha lasts 16 years
    Planet.SATURN: 19,    # Saturn dasha lasts 19 years
    Planet.MERCURY: 17,   # Mercury dasha lasts 17 years
}

# The fixed sequence of dasha lords (repeats cyclically after 120 years)
VIMSOTTARI_ORDER = [
    Planet.KETU, Planet.VENUS, Planet.SUN, Planet.MOON, Planet.MARS,
    Planet.RAHU, Planet.JUPITER, Planet.SATURN, Planet.MERCURY,
]

# Sum of all mahadasha periods = 120 years
VIMSOTTARI_TOTAL_YEARS = 120


# ---------------------------------------------------------------------------
# Ayanamsa modes
# ---------------------------------------------------------------------------
# WHAT IS AYANAMSA?
#
# The Earth's axis wobbles slowly (like a spinning top) over a ~26,000-year
# cycle. This is called "precession of the equinoxes." Because of this:
#
#   - The spring equinox point (0° Aries in Western/tropical astrology)
#     slowly drifts backward through the constellations
#   - As of 2024, it has drifted ~24° from where the actual constellation
#     Aries begins
#
# Western astrology ignores this drift (tropical zodiac = tied to seasons).
# Vedic astrology accounts for it (sidereal zodiac = tied to fixed stars).
#
# The "ayanamsa" is the angular difference between the two systems:
#   sidereal_longitude = tropical_longitude - ayanamsa
#
# Different scholars have slightly different values for the ayanamsa
# (they disagree on the exact "zero point" of the sidereal zodiac).
# The most common in India is Lahiri (~24° in 2024).
#
# Source: Indian Calendar Reform Committee (1956) for Lahiri.
#
# The integer values below correspond to Swiss Ephemeris ayanamsa mode
# constants (passed to swe.set_sid_mode()).

# ---------------------------------------------------------------------------
# Panchanga constants
# ---------------------------------------------------------------------------
# The Panchanga (five-limbed calendar) requires name lookups for its
# five elements: tithi, nakshatra, yoga, karana, and vara.
#
# Source: Surya Siddhanta, various panchanga reference tables.

# TITHI NAMES (30 lunar days per month)
# Tithis 1-15 = Shukla Paksha (waxing/bright half: new moon → full moon)
# Tithis 16-30 = Krishna Paksha (waning/dark half: full moon → new moon)
# Each tithi = 12° of Moon-Sun angular separation.
# Formula: tithi_number = floor((moon_lon - sun_lon) % 360 / 12) + 1
#
# The 15 tithi names repeat in both pakshas, except:
#   - Tithi 15 = Purnima (full moon) instead of "Panchami"
#   - Tithi 30 = Amavasya (new moon) instead of "Panchami"
TITHI_NAMES: dict[int, str] = {
    1: "Shukla Pratipada",
    2: "Shukla Dwitiya",
    3: "Shukla Tritiya",
    4: "Shukla Chaturthi",
    5: "Shukla Panchami",
    6: "Shukla Shashthi",
    7: "Shukla Saptami",
    8: "Shukla Ashtami",
    9: "Shukla Navami",
    10: "Shukla Dashami",
    11: "Shukla Ekadashi",
    12: "Shukla Dwadashi",
    13: "Shukla Trayodashi",
    14: "Shukla Chaturdashi",
    15: "Purnima",             # Full moon
    16: "Krishna Pratipada",
    17: "Krishna Dwitiya",
    18: "Krishna Tritiya",
    19: "Krishna Chaturthi",
    20: "Krishna Panchami",
    21: "Krishna Shashthi",
    22: "Krishna Saptami",
    23: "Krishna Ashtami",
    24: "Krishna Navami",
    25: "Krishna Dashami",
    26: "Krishna Ekadashi",
    27: "Krishna Dwadashi",
    28: "Krishna Trayodashi",
    29: "Krishna Chaturdashi",
    30: "Amavasya",            # New moon
}

# YOGA NAMES (27 nitya yogas)
# Yoga = a luni-solar combination based on the SUM of Moon and Sun longitudes.
# Each yoga spans 13°20' (same span as a nakshatra, but completely different concept).
# Formula: yoga_number = floor((moon_lon + sun_lon) % 360 / 13.333) + 1
#
# Some yogas are considered auspicious (e.g., Siddhi, Shubha, Shiva)
# and some inauspicious (e.g., Vyatipata, Vaidhriti, Ganda).
# Source: Surya Siddhanta.
YOGA_NAMES: dict[int, str] = {
    1: "Vishkambha",
    2: "Priti",
    3: "Ayushman",
    4: "Saubhagya",
    5: "Shobhana",
    6: "Atiganda",
    7: "Sukarma",
    8: "Dhriti",
    9: "Shoola",
    10: "Ganda",
    11: "Vriddhi",
    12: "Dhruva",
    13: "Vyaghata",
    14: "Harshana",
    15: "Vajra",
    16: "Siddhi",
    17: "Vyatipata",
    18: "Variyan",
    19: "Parigha",
    20: "Shiva",
    21: "Siddha",
    22: "Sadhya",
    23: "Shubha",
    24: "Shukla",
    25: "Brahma",
    26: "Indra",
    27: "Vaidhriti",
}

# KARANA NAMES (60 karanas per lunar month)
# A karana is half a tithi (each tithi has 2 karanas).
# Each karana = 6° of Moon-Sun angular separation.
# Formula: karana_number = floor((moon_lon - sun_lon) % 360 / 6) + 1
#
# There are 11 karana types:
#   4 FIXED karanas (appear once per month at specific positions):
#     - Kimstughna: karana 1 (second half of Amavasya/first half of Shukla Pratipada)
#     - Shakuni: karana 58
#     - Chatushpada: karana 59
#     - Nagava: karana 60
#
#   7 REPEATING karanas (cycle 8 times through positions 2-57):
#     Bava → Balava → Kaulava → Taitila → Garaja → Vanija → Vishti
#
# Vishti (also called "Bhadra") is considered inauspicious.
# Source: Surya Siddhanta, various Panchanga references.

# Build the karana name lookup programmatically
_REPEATING_KARANAS = [
    "Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti",
]
KARANA_NAMES: dict[int, str] = {1: "Kimstughna"}
for i in range(2, 58):
    KARANA_NAMES[i] = _REPEATING_KARANAS[(i - 2) % 7]
KARANA_NAMES[58] = "Shakuni"
KARANA_NAMES[59] = "Chatushpada"
KARANA_NAMES[60] = "Nagava"

# VARA NAMES (weekdays, named after planets)
# In Vedic tradition, each day of the week is ruled by a planet:
#   Sunday = Sun (Ravi), Monday = Moon (Soma), Tuesday = Mars (Mangala),
#   Wednesday = Mercury (Budha), Thursday = Jupiter (Guru),
#   Friday = Venus (Shukra), Saturday = Saturn (Shani)
#
# Keyed by Python's datetime.weekday() (0=Monday, 6=Sunday).
VARA_NAMES: dict[int, str] = {
    0: "Monday (Somavara)",       # Moon
    1: "Tuesday (Mangalavara)",   # Mars
    2: "Wednesday (Budhavara)",   # Mercury
    3: "Thursday (Guruvara)",     # Jupiter
    4: "Friday (Shukravara)",     # Venus
    5: "Saturday (Shanivara)",    # Saturn
    6: "Sunday (Ravivara)",       # Sun
}

# Planet abbreviations for chart rendering
# Used by the kundali renderer to display planets compactly in chart cells.
PLANET_ABBREVIATIONS: dict["Planet", str] = {
    Planet.SUN: "Su",
    Planet.MOON: "Mo",
    Planet.MARS: "Ma",
    Planet.MERCURY: "Me",
    Planet.JUPITER: "Ju",
    Planet.VENUS: "Ve",
    Planet.SATURN: "Sa",
    Planet.RAHU: "Ra",
    Planet.KETU: "Ke",
}

# Sign abbreviations for chart rendering
SIGN_ABBREVIATIONS: dict["Sign", str] = {
    Sign.ARIES: "Ar",
    Sign.TAURUS: "Ta",
    Sign.GEMINI: "Ge",
    Sign.CANCER: "Cn",
    Sign.LEO: "Le",
    Sign.VIRGO: "Vi",
    Sign.LIBRA: "Li",
    Sign.SCORPIO: "Sc",
    Sign.SAGITTARIUS: "Sg",
    Sign.CAPRICORN: "Cp",
    Sign.AQUARIUS: "Aq",
    Sign.PISCES: "Pi",
}


# ---------------------------------------------------------------------------
# Ayanamsa modes
# ---------------------------------------------------------------------------
class Ayanamsa(IntEnum):
    """Supported ayanamsa (precession correction) modes.

    The ayanamsa is subtracted from tropical longitudes to get sidereal
    positions. Different modes differ by ~1-2°, which can change sign
    placement for planets near sign boundaries.

    Lahiri is the most commonly used in India and is the default.
    """
    LAHIRI = 1              # Chitrapaksha — official Indian standard (~23.7° in 1990)
    RAMAN = 3               # B.V. Raman's ayanamsa
    KP = 5                  # Krishnamurti Paddhati (a sub-system of Vedic astrology)
    TRUE_CHITRAPAKSHA = 27  # True Chitrapaksha (fixes Spica at exactly 0° Libra)
