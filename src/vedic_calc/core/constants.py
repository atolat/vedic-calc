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


# ---------------------------------------------------------------------------
# Planetary friendship table (Naisargika Maitri)
# ---------------------------------------------------------------------------
# Natural relationship between planets: 2=friend, 1=neutral, 0=enemy.
# Source: BPHS Chapter 3.
# Only 7 classical planets (Sun–Saturn) participate in friendships;
# Rahu and Ketu don't own signs and are excluded.

PLANET_FRIENDSHIP: dict[Planet, dict[Planet, int]] = {
    Planet.SUN: {
        Planet.SUN: 2, Planet.MOON: 2, Planet.MARS: 2, Planet.MERCURY: 1,
        Planet.JUPITER: 2, Planet.VENUS: 0, Planet.SATURN: 0,
    },
    Planet.MOON: {
        Planet.SUN: 2, Planet.MOON: 2, Planet.MARS: 1, Planet.MERCURY: 2,
        Planet.JUPITER: 1, Planet.VENUS: 1, Planet.SATURN: 1,
    },
    Planet.MARS: {
        Planet.SUN: 2, Planet.MOON: 2, Planet.MARS: 2, Planet.MERCURY: 0,
        Planet.JUPITER: 2, Planet.VENUS: 1, Planet.SATURN: 0,
    },
    Planet.MERCURY: {
        Planet.SUN: 2, Planet.MOON: 0, Planet.MARS: 1, Planet.MERCURY: 2,
        Planet.JUPITER: 1, Planet.VENUS: 2, Planet.SATURN: 1,
    },
    Planet.JUPITER: {
        Planet.SUN: 2, Planet.MOON: 2, Planet.MARS: 2, Planet.MERCURY: 0,
        Planet.JUPITER: 2, Planet.VENUS: 0, Planet.SATURN: 1,
    },
    Planet.VENUS: {
        Planet.SUN: 0, Planet.MOON: 1, Planet.MARS: 1, Planet.MERCURY: 2,
        Planet.JUPITER: 1, Planet.VENUS: 2, Planet.SATURN: 2,
    },
    Planet.SATURN: {
        Planet.SUN: 0, Planet.MOON: 0, Planet.MARS: 0, Planet.MERCURY: 2,
        Planet.JUPITER: 1, Planet.VENUS: 2, Planet.SATURN: 2,
    },
}


# ---------------------------------------------------------------------------
# Exaltation and debilitation degrees
# ---------------------------------------------------------------------------
# Each planet has one sign+degree where it is exalted (strongest) and the
# opposite sign+degree where it is debilitated (weakest).
# Format: (sign, exact_degree_in_sign)
# Source: BPHS Chapter 3, Verse 49.

EXALTATION: dict[Planet, tuple["Sign", float]] = {
    Planet.SUN: (Sign.ARIES, 10.0),
    Planet.MOON: (Sign.TAURUS, 3.0),
    Planet.MARS: (Sign.CAPRICORN, 28.0),
    Planet.MERCURY: (Sign.VIRGO, 15.0),
    Planet.JUPITER: (Sign.CANCER, 5.0),
    Planet.VENUS: (Sign.PISCES, 27.0),
    Planet.SATURN: (Sign.LIBRA, 20.0),
    Planet.RAHU: (Sign.TAURUS, 20.0),
    Planet.KETU: (Sign.SCORPIO, 20.0),
}

DEBILITATION: dict[Planet, tuple["Sign", float]] = {
    Planet.SUN: (Sign.LIBRA, 10.0),
    Planet.MOON: (Sign.SCORPIO, 3.0),
    Planet.MARS: (Sign.CANCER, 28.0),
    Planet.MERCURY: (Sign.PISCES, 15.0),
    Planet.JUPITER: (Sign.CAPRICORN, 5.0),
    Planet.VENUS: (Sign.VIRGO, 27.0),
    Planet.SATURN: (Sign.ARIES, 20.0),
    Planet.RAHU: (Sign.SCORPIO, 20.0),
    Planet.KETU: (Sign.TAURUS, 20.0),
}


# ---------------------------------------------------------------------------
# Moolatrikona signs and degree ranges
# ---------------------------------------------------------------------------
# Each planet has a moolatrikona range — a zone of special strength,
# slightly less than exaltation but more than own sign.
# Format: (sign, start_degree, end_degree)
# Source: BPHS Chapter 3, Verse 50-51.

MOOLATRIKONA: dict[Planet, tuple["Sign", float, float]] = {
    Planet.SUN: (Sign.LEO, 0.0, 20.0),
    Planet.MOON: (Sign.TAURUS, 3.0, 30.0),
    Planet.MARS: (Sign.ARIES, 0.0, 12.0),
    Planet.MERCURY: (Sign.VIRGO, 15.0, 20.0),
    Planet.JUPITER: (Sign.SAGITTARIUS, 0.0, 10.0),
    Planet.VENUS: (Sign.LIBRA, 0.0, 15.0),
    Planet.SATURN: (Sign.AQUARIUS, 0.0, 20.0),
}


# ---------------------------------------------------------------------------
# Combustion thresholds (degrees from Sun)
# ---------------------------------------------------------------------------
# A planet within this distance from the Sun is "combust" (asta) and weakened.
# Retrograde planets have slightly different thresholds (shown as second value).
# Format: (direct_threshold, retrograde_threshold)
# Source: BPHS Chapter 25.
# Sun, Rahu, Ketu are excluded (Sun is the combustor; nodes are shadow planets).

COMBUSTION_THRESHOLD: dict[Planet, tuple[float, float]] = {
    Planet.MOON: (12.0, 12.0),
    Planet.MARS: (17.0, 17.0),
    Planet.MERCURY: (14.0, 12.0),
    Planet.JUPITER: (11.0, 11.0),
    Planet.VENUS: (10.0, 8.0),
    Planet.SATURN: (15.0, 15.0),
}


# ---------------------------------------------------------------------------
# Graha Drishti (planetary aspect) rules
# ---------------------------------------------------------------------------
# All planets cast a full aspect on the 7th house from their position.
# Mars, Jupiter, and Saturn have additional special aspects.
# Values are the house offsets (1-indexed) each planet aspects.
# Source: BPHS Chapter 26.

GRAHA_DRISHTI: dict[Planet, list[int]] = {
    Planet.SUN: [7],
    Planet.MOON: [7],
    Planet.MARS: [4, 7, 8],
    Planet.MERCURY: [7],
    Planet.JUPITER: [5, 7, 9],
    Planet.VENUS: [7],
    Planet.SATURN: [3, 7, 10],
    Planet.RAHU: [7],
    Planet.KETU: [7],
}

# Rashi Drishti (sign-based aspects for Jaimini)
# Movable signs aspect fixed signs (except adjacent), and vice versa.
# Dual signs aspect other dual signs.
# Format: sign → list of signs it aspects.
RASHI_DRISHTI: dict["Sign", list["Sign"]] = {
    Sign.ARIES: [Sign.SCORPIO, Sign.LEO, Sign.AQUARIUS],
    Sign.TAURUS: [Sign.LIBRA, Sign.SAGITTARIUS, Sign.AQUARIUS],
    Sign.GEMINI: [Sign.VIRGO, Sign.SAGITTARIUS, Sign.PISCES],
    Sign.CANCER: [Sign.AQUARIUS, Sign.SCORPIO, Sign.TAURUS],
    Sign.LEO: [Sign.SCORPIO, Sign.TAURUS, Sign.AQUARIUS],
    Sign.VIRGO: [Sign.GEMINI, Sign.SAGITTARIUS, Sign.PISCES],
    Sign.LIBRA: [Sign.TAURUS, Sign.LEO, Sign.AQUARIUS],
    Sign.SCORPIO: [Sign.LEO, Sign.ARIES, Sign.AQUARIUS],
    Sign.SAGITTARIUS: [Sign.GEMINI, Sign.VIRGO, Sign.PISCES],
    Sign.CAPRICORN: [Sign.ARIES, Sign.CANCER, Sign.LIBRA],
    Sign.AQUARIUS: [Sign.CANCER, Sign.ARIES, Sign.LIBRA],
    Sign.PISCES: [Sign.GEMINI, Sign.VIRGO, Sign.SAGITTARIUS],
}


# ---------------------------------------------------------------------------
# Ashtakavarga benefic points
# ---------------------------------------------------------------------------
# For each planet, the houses (counted from other planets and the lagna)
# where that planet contributes a benefic point.
# 7 contributing planets (Sun-Saturn) + Lagna, for 7 receiver planets.
# Source: BPHS Chapter 66-72.
# Format: receiver_planet → {contributor → list of houses where benefic}

ASHTAKAVARGA_BENEFIC: dict[Planet, dict[Planet | str, list[int]]] = {
    Planet.SUN: {
        Planet.SUN: [1, 2, 4, 7, 8, 9, 10, 11],
        Planet.MOON: [3, 6, 10, 11],
        Planet.MARS: [1, 2, 4, 7, 8, 9, 10, 11],
        Planet.MERCURY: [3, 5, 6, 9, 10, 11, 12],
        Planet.JUPITER: [5, 6, 9, 11],
        Planet.VENUS: [6, 7, 12],
        Planet.SATURN: [1, 2, 4, 7, 8, 9, 10, 11],
        "lagna": [3, 4, 6, 10, 11, 12],
    },
    Planet.MOON: {
        Planet.SUN: [3, 6, 7, 8, 10, 11],
        Planet.MOON: [1, 3, 6, 7, 10, 11],
        Planet.MARS: [2, 3, 5, 6, 9, 10, 11],
        Planet.MERCURY: [1, 3, 4, 5, 7, 8, 10, 11],
        Planet.JUPITER: [1, 4, 7, 8, 10, 11, 12],
        Planet.VENUS: [3, 4, 5, 7, 9, 10, 11],
        Planet.SATURN: [3, 5, 6, 11],
        "lagna": [3, 6, 10, 11],
    },
    Planet.MARS: {
        Planet.SUN: [3, 5, 6, 10, 11],
        Planet.MOON: [3, 6, 11],
        Planet.MARS: [1, 2, 4, 7, 8, 10, 11],
        Planet.MERCURY: [3, 5, 6, 11],
        Planet.JUPITER: [6, 10, 11, 12],
        Planet.VENUS: [6, 8, 11, 12],
        Planet.SATURN: [1, 4, 7, 8, 9, 10, 11],
        "lagna": [1, 3, 6, 10, 11],
    },
    Planet.MERCURY: {
        Planet.SUN: [5, 6, 9, 11, 12],
        Planet.MOON: [2, 4, 6, 8, 10, 11],
        Planet.MARS: [1, 2, 4, 7, 8, 9, 10, 11],
        Planet.MERCURY: [1, 3, 5, 6, 9, 10, 11, 12],
        Planet.JUPITER: [6, 8, 11, 12],
        Planet.VENUS: [1, 2, 3, 4, 5, 8, 9, 11],
        Planet.SATURN: [1, 2, 4, 7, 8, 9, 10, 11],
        "lagna": [1, 2, 4, 6, 8, 10, 11],
    },
    Planet.JUPITER: {
        Planet.SUN: [1, 2, 3, 4, 7, 8, 9, 10, 11],
        Planet.MOON: [2, 5, 7, 9, 11],
        Planet.MARS: [1, 2, 4, 7, 8, 10, 11],
        Planet.MERCURY: [1, 2, 4, 5, 6, 9, 10, 11],
        Planet.JUPITER: [1, 2, 3, 4, 7, 8, 10, 11],
        Planet.VENUS: [2, 5, 6, 9, 10, 11],
        Planet.SATURN: [3, 5, 6, 12],
        "lagna": [1, 2, 4, 5, 6, 7, 9, 10, 11],
    },
    Planet.VENUS: {
        Planet.SUN: [8, 11, 12],
        Planet.MOON: [1, 2, 3, 4, 5, 8, 9, 11, 12],
        Planet.MARS: [3, 5, 6, 9, 11, 12],  # BPHS: house 5 (not 4) — verified via AstrologyAPI
        Planet.MERCURY: [3, 5, 6, 9, 11],
        Planet.JUPITER: [5, 8, 9, 10, 11],
        Planet.VENUS: [1, 2, 3, 4, 5, 8, 9, 10, 11],
        Planet.SATURN: [3, 4, 5, 8, 9, 10, 11],
        "lagna": [1, 2, 3, 4, 5, 8, 9, 11],
    },
    Planet.SATURN: {
        Planet.SUN: [1, 2, 4, 7, 8, 10, 11],
        Planet.MOON: [3, 6, 11],
        Planet.MARS: [3, 5, 6, 10, 11, 12],
        Planet.MERCURY: [6, 8, 9, 10, 11, 12],
        Planet.JUPITER: [5, 6, 11, 12],
        Planet.VENUS: [6, 11, 12],
        Planet.SATURN: [3, 5, 6, 11],
        "lagna": [1, 3, 4, 6, 10, 11],
    },
}


# ---------------------------------------------------------------------------
# Naisargika Bala (natural strength) — used in Shadbala
# ---------------------------------------------------------------------------
# Natural strength values in Shashtiamsas (1/60th of a Rupa).
# Source: BPHS Chapter 27.
NAISARGIKA_BALA: dict[Planet, float] = {
    Planet.SUN: 60.0,
    Planet.MOON: 51.43,
    Planet.MARS: 17.14,
    Planet.MERCURY: 25.71,
    Planet.JUPITER: 34.29,
    Planet.VENUS: 42.86,
    Planet.SATURN: 8.57,
}

# Dig Bala (directional strength) — which house gives max strength.
# Source: BPHS Chapter 27.
# Format: planet → house number where it gets maximum Dig Bala.
DIG_BALA_HOUSES: dict[Planet, int] = {
    Planet.SUN: 10,      # Sun is strong in 10th (zenith)
    Planet.MOON: 4,      # Moon is strong in 4th (nadir)
    Planet.MARS: 10,     # Mars is strong in 10th
    Planet.MERCURY: 1,   # Mercury is strong in 1st (east)
    Planet.JUPITER: 1,   # Jupiter is strong in 1st
    Planet.VENUS: 4,     # Venus is strong in 4th
    Planet.SATURN: 7,    # Saturn is strong in 7th (west)
}


# ---------------------------------------------------------------------------
# Choghadiya (day/night auspicious period) names
# ---------------------------------------------------------------------------
# 7 choghadiyas per day and 7 per night, named after planets.
# Day sequence varies by weekday; night is the reverse.
# Source: Muhurta Chintamani.

CHOGHADIYA_TYPES: dict[str, str] = {
    "Udyog": "good",        # Mercury — good for work
    "Amrit": "best",        # Moon — best, auspicious
    "Char": "good",         # Venus — good for travel
    "Labh": "good",         # Jupiter — good for gains
    "Shubh": "good",        # Jupiter — auspicious
    "Rog": "bad",           # Mars — inauspicious, disease
    "Kaal": "bad",          # Saturn — inauspicious, death
}

# Day choghadiya sequence by weekday (0=Monday to 6=Sunday)
CHOGHADIYA_DAY_SEQUENCE: dict[int, list[str]] = {
    0: ["Amrit", "Kaal", "Shubh", "Rog", "Udyog", "Char", "Labh", "Amrit"],
    1: ["Rog", "Udyog", "Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog"],
    2: ["Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udyog", "Char", "Labh"],
    3: ["Shubh", "Rog", "Udyog", "Char", "Labh", "Amrit", "Kaal", "Shubh"],
    4: ["Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udyog", "Char"],
    5: ["Kaal", "Shubh", "Rog", "Udyog", "Char", "Labh", "Amrit", "Kaal"],
    6: ["Udyog", "Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udyog"],
}

# Night choghadiya sequence by weekday
CHOGHADIYA_NIGHT_SEQUENCE: dict[int, list[str]] = {
    0: ["Shubh", "Amrit", "Char", "Rog", "Kaal", "Labh", "Udyog", "Shubh"],
    1: ["Char", "Rog", "Kaal", "Labh", "Udyog", "Shubh", "Amrit", "Char"],
    2: ["Kaal", "Labh", "Udyog", "Shubh", "Amrit", "Char", "Rog", "Kaal"],
    3: ["Labh", "Udyog", "Shubh", "Amrit", "Char", "Rog", "Kaal", "Labh"],
    4: ["Udyog", "Shubh", "Amrit", "Char", "Rog", "Kaal", "Labh", "Udyog"],
    5: ["Amrit", "Char", "Rog", "Kaal", "Labh", "Udyog", "Shubh", "Amrit"],
    6: ["Rog", "Kaal", "Labh", "Udyog", "Shubh", "Amrit", "Char", "Rog"],
}


# ---------------------------------------------------------------------------
# Hora (planetary hour) lord sequence
# ---------------------------------------------------------------------------
# The 24 hours of a day (starting from sunrise) are ruled by planets
# in this order, starting from the weekday lord.
# Sunday=Sun, Monday=Moon, Tuesday=Mars, etc.
HORA_ORDER: list[Planet] = [
    Planet.SUN, Planet.VENUS, Planet.MERCURY, Planet.MOON,
    Planet.SATURN, Planet.JUPITER, Planet.MARS,
]

# Weekday → starting hora lord
WEEKDAY_HORA_LORD: dict[int, Planet] = {
    0: Planet.MOON,      # Monday
    1: Planet.MARS,      # Tuesday
    2: Planet.MERCURY,   # Wednesday
    3: Planet.JUPITER,   # Thursday
    4: Planet.VENUS,     # Friday
    5: Planet.SATURN,    # Saturday
    6: Planet.SUN,       # Sunday
}


# ---------------------------------------------------------------------------
# Rahu Kalam, Yamagandam, Gulika Kalam time slots
# ---------------------------------------------------------------------------
# These inauspicious periods are portions of the day (sunrise to sunset),
# divided into 8 equal parts. The slot number (0-7) for each weekday:
# Source: Traditional South Indian Panchanga.

RAHU_KALAM_SLOT: dict[int, int] = {
    0: 1,  # Monday: 2nd slot
    1: 6,  # Tuesday: 7th slot
    2: 4,  # Wednesday: 5th slot
    3: 5,  # Thursday: 6th slot
    4: 3,  # Friday: 4th slot
    5: 2,  # Saturday: 3rd slot
    6: 7,  # Sunday: 8th slot
}

YAMAGANDAM_SLOT: dict[int, int] = {
    0: 3,  # Monday: 4th slot
    1: 2,  # Tuesday: 3rd slot
    2: 1,  # Wednesday: 2nd slot
    3: 0,  # Thursday: 1st slot
    4: 6,  # Friday: 7th slot
    5: 5,  # Saturday: 6th slot
    6: 4,  # Sunday: 5th slot
}

GULIKA_KALAM_SLOT: dict[int, int] = {
    0: 5,  # Monday: 6th slot
    1: 4,  # Tuesday: 5th slot
    2: 3,  # Wednesday: 4th slot
    3: 2,  # Thursday: 3rd slot
    4: 1,  # Friday: 2nd slot
    5: 0,  # Saturday: 1st slot
    6: 6,  # Sunday: 7th slot
}


# ---------------------------------------------------------------------------
# Saham (Arabic Parts / Sensitive Points) formulas
# ---------------------------------------------------------------------------
# Each saham is computed as: A + B - C (modulo 360°).
# For day birth (Sun above horizon): use the formula as-is.
# For night birth: swap A and B.
# Format: (name, planet_A, planet_B, planet_C) where values are Planet enums
# or "ASC" for ascendant longitude.
# Source: Brihat Jataka, Jataka Parijata.

SAHAM_FORMULAS: list[tuple[str, str, str, str]] = [
    ("Punya", "MOON", "SUN", "ASC"),          # Spiritual merit
    ("Vidya", "SUN", "MOON", "ASC"),           # Education
    ("Yasas", "JUPITER", "MOON", "ASC"),       # Fame
    ("Mitra", "JUPITER", "MOON", "ASC"),       # Friendship
    ("Mahatmya", "SUN", "MARS", "ASC"),        # Greatness
    ("Sastra", "JUPITER", "SATURN", "ASC"),    # Weapons/scriptures
    ("Gaurava", "JUPITER", "MOON", "SUN"),     # Respect
    ("Pitri", "SATURN", "SUN", "ASC"),         # Father
    ("Matri", "MOON", "VENUS", "ASC"),         # Mother
    ("Putra", "JUPITER", "MOON", "ASC"),       # Children
    ("Jeeva", "SATURN", "JUPITER", "ASC"),     # Vitality
    ("Karma", "MARS", "MERCURY", "ASC"),       # Profession
    ("Roga", "ASC", "MARS", "SATURN"),         # Disease
    ("Kali", "JUPITER", "MARS", "ASC"),        # Strife
    ("Paradesa", "ASC", "SUN", "SATURN"),      # Foreign travel
    ("Vivaha", "VENUS", "SATURN", "ASC"),      # Marriage
    ("Santapa", "SATURN", "MOON", "ASC"),      # Sorrow
    ("Apamrityu", "MARS", "SATURN", "ASC"),    # Accidental death
    ("Paradara", "VENUS", "SUN", "ASC"),       # Adultery (partner's fidelity)
    ("Bandhana", "SATURN", "MOON", "MERCURY"), # Imprisonment
]


# ---------------------------------------------------------------------------
# Yogini Dasha constants
# ---------------------------------------------------------------------------
# 8 yoginis, each ruled by a planet, with fixed year durations.
# Total cycle: 36 years. Sequence determined by birth nakshatra.
# Source: Jataka Parijata.

YOGINI_DASHA_YEARS: dict[str, tuple[Planet, int]] = {
    "Mangala": (Planet.MOON, 1),
    "Pingala": (Planet.SUN, 2),
    "Dhanya": (Planet.JUPITER, 3),
    "Bhramari": (Planet.MARS, 4),
    "Bhadrika": (Planet.MERCURY, 5),
    "Ulka": (Planet.SATURN, 6),
    "Siddha": (Planet.VENUS, 7),
    "Sankata": (Planet.RAHU, 8),
}

YOGINI_DASHA_ORDER: list[str] = [
    "Mangala", "Pingala", "Dhanya", "Bhramari",
    "Bhadrika", "Ulka", "Siddha", "Sankata",
]

YOGINI_DASHA_TOTAL_YEARS: int = 36


# ---------------------------------------------------------------------------
# Ashtottari Dasha constants
# ---------------------------------------------------------------------------
# 8 planets (no Ketu), 108-year cycle.
# Source: BPHS Chapter 47.

ASHTOTTARI_YEARS: dict[Planet, int] = {
    Planet.SUN: 6,
    Planet.MOON: 15,
    Planet.MARS: 8,
    Planet.MERCURY: 17,
    Planet.SATURN: 10,
    Planet.JUPITER: 19,
    Planet.RAHU: 12,
    Planet.VENUS: 21,
}

ASHTOTTARI_ORDER: list[Planet] = [
    Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
    Planet.SATURN, Planet.JUPITER, Planet.RAHU, Planet.VENUS,
]

ASHTOTTARI_TOTAL_YEARS: int = 108


# ---------------------------------------------------------------------------
# Chara Karaka order
# ---------------------------------------------------------------------------
# Jaimini's 8 chara (variable) karakas, ordered by decreasing longitude
# within sign. The planet with the highest degree_in_sign = Atmakaraka, etc.
# Source: Jaimini Sutras.

CHARA_KARAKA_NAMES: list[str] = [
    "Atmakaraka",       # Self, soul
    "Amatyakaraka",     # Minister, career
    "Bhratrikaraka",    # Siblings
    "Matrikaraka",      # Mother
    "Putrakaraka",      # Children
    "Gnatikaraka",      # Relatives, diseases
    "Darakaraka",       # Spouse
    "Pitrkaraka",       # Father (8-karaka scheme only)
]


# ---------------------------------------------------------------------------
# House categories
# ---------------------------------------------------------------------------
KENDRA_HOUSES: list[int] = [1, 4, 7, 10]        # Angular houses
TRIKONA_HOUSES: list[int] = [1, 5, 9]            # Trinal houses
DUSTHANA_HOUSES: list[int] = [6, 8, 12]          # Malefic houses
UPACHAYA_HOUSES: list[int] = [3, 6, 10, 11]      # Growth houses
MARAKA_HOUSES: list[int] = [2, 7]                # Death-inflicting houses


# ---------------------------------------------------------------------------
# Natural benefics / malefics
# ---------------------------------------------------------------------------
# Source: BPHS Ch. 3 — natural disposition of planets.
# Jupiter, Venus, waxing Moon, and well-associated Mercury are benefics.
# Sun, Mars, Saturn, Rahu, Ketu, waning Moon are malefics.
# For simplicity we classify Moon as benefic (traditional default) and
# Mercury as benefic (assuming no malefic association without chart context).

BENEFICS: set[Planet] = {Planet.JUPITER, Planet.VENUS, Planet.MOON, Planet.MERCURY}
MALEFICS: set[Planet] = {Planet.SUN, Planet.MARS, Planet.SATURN, Planet.RAHU, Planet.KETU}


# ---------------------------------------------------------------------------
# Tajika aspect orbs (degree-based, used in Prashna/Horary astrology)
# ---------------------------------------------------------------------------
# Tajika (Greco-Arabic influence on Indian astrology) uses degree-based aspects
# with orbs, unlike Parashari sign-based aspects. These are the 5 Ptolemaic
# aspects with their standard Tajika orbs.
#
# Format: aspect_name -> (exact_degrees, orb_degrees)
# A planet at longitude X "aspects" a planet at longitude Y if:
#   abs(angular_distance(X, Y) - exact_degrees) <= orb_degrees
#
# Source: Tajika Neelakanthi, Tajika Shastra

TAJIKA_ASPECT_ORBS: dict[str, tuple[float, float]] = {
    "conjunction": (0.0, 8.0),
    "opposition": (180.0, 8.0),
    "trine": (120.0, 6.0),
    "square": (90.0, 6.0),
    "sextile": (60.0, 4.0),
}

# ---------------------------------------------------------------------------
# Prashna: Question category → house mapping
# ---------------------------------------------------------------------------
# Maps common question topics to the house that signifies that area.
# The house lord and its condition determine the outcome of the query.
# Source: Prashna Marga, Ch. 1-3.

QUESTION_TO_HOUSE: dict[str, int] = {
    "career": 10, "job": 10, "promotion": 10, "business": 10,
    "marriage": 7, "relationship": 7, "partner": 7, "spouse": 7,
    "health": 6, "disease": 6, "illness": 6,
    "wealth": 2, "money": 2, "finance": 2, "income": 11,
    "education": 4, "study": 4, "exam": 5,
    "children": 5, "pregnancy": 5, "fertility": 5,
    "travel": 3, "short_travel": 3, "foreign": 9, "abroad": 9,
    "property": 4, "home": 4, "real_estate": 4,
    "legal": 6, "court": 6, "litigation": 6,
    "spiritual": 9, "religion": 9, "guru": 9,
    "general": 1,
}

# ---------------------------------------------------------------------------
# Planetary speed order (for Tajika: faster planet applies to slower)
# ---------------------------------------------------------------------------
# Average daily sidereal motion, fastest to slowest.
# Moon > Mercury > Venus > Sun > Mars > Jupiter > Saturn > Rahu > Ketu
# Source: Surya Siddhanta (mean daily motions)

PLANET_SPEED_ORDER: dict[Planet, int] = {
    Planet.MOON: 0,      # ~13.2°/day (fastest)
    Planet.MERCURY: 1,   # ~1.4°/day
    Planet.VENUS: 2,     # ~1.2°/day
    Planet.SUN: 3,       # ~1.0°/day
    Planet.MARS: 4,      # ~0.5°/day
    Planet.JUPITER: 5,   # ~0.08°/day
    Planet.SATURN: 6,    # ~0.03°/day
    Planet.RAHU: 7,      # ~0.05°/day (retrograde)
    Planet.KETU: 8,      # ~0.05°/day (retrograde)
}


# ---------------------------------------------------------------------------
# Muhurta solver: activity-specific good/bad panchanga elements
# ---------------------------------------------------------------------------
# Source: Muhurta Chintamani, Kalaprakashika, and traditional panchanga guides.

# Universally bad tithis — Rikta tithis (4th, 9th, 14th of each paksha)
BAD_TITHIS: set[int] = {4, 9, 14, 19, 24, 29}  # Both shukla and krishna

# Activity-specific good tithis (tithi numbers 1-30)
GOOD_TITHIS: dict[str, set[int]] = {
    "marriage": {2, 3, 5, 7, 10, 11, 13, 17, 22, 25, 27},
    "business": {2, 3, 5, 7, 10, 11, 13, 15, 17},
    "travel": {2, 3, 5, 7, 10, 11, 13},
    "education": {2, 3, 5, 7, 10, 11, 13},
    "property": {2, 3, 5, 7, 10, 11, 13, 15},
    "medical": {2, 3, 5, 7, 10, 11, 13},
    "general": {1, 2, 3, 5, 6, 7, 10, 11, 12, 13, 15},
}

# Activity-specific good nakshatras (nakshatra numbers 1-27)
GOOD_NAKSHATRAS: dict[str, set[int]] = {
    "marriage": {4, 7, 8, 11, 12, 13, 15, 17, 21, 22, 26, 27},  # Rohini, Punarvasu, Pushya, etc.
    "business": {1, 4, 7, 8, 11, 12, 13, 15, 17, 21, 22, 27},
    "travel": {1, 4, 7, 8, 11, 13, 15, 21, 22, 27},
    "education": {1, 4, 7, 8, 12, 13, 15, 21, 22, 27},
    "property": {4, 7, 8, 11, 12, 13, 15, 17, 21, 22, 26, 27},
    "medical": {1, 4, 7, 8, 11, 12, 13, 22, 27},
    "general": {1, 4, 7, 8, 11, 12, 13, 15, 17, 21, 22, 26, 27},
}

# Universally bad yogas (panchanga yoga, not chart yoga)
BAD_YOGAS: set[int] = {17, 27}  # Vyatipata (17), Vaidhriti (27)

# Bad karanas — Vishti/Bhadra (repeating karana #4 in each set of 7)
# Vishti occurs as every 7th karana. Numbers: 4, 11, 18, 25, 32, 39, 46, 53
BAD_KARANAS: set[int] = {4, 11, 18, 25, 32, 39, 46, 53}

# Activity-specific good weekdays (0=Monday .. 6=Sunday, Python weekday())
GOOD_VARAS: dict[str, set[int]] = {
    "marriage": {0, 2, 3, 4},   # Mon, Wed, Thu, Fri
    "business": {0, 2, 3, 4},   # Mon, Wed, Thu, Fri
    "travel": {0, 2, 3, 4},     # Mon, Wed, Thu, Fri
    "education": {0, 2, 3, 4},  # Mon, Wed, Thu, Fri
    "property": {0, 3, 4},      # Mon, Thu, Fri
    "medical": {0, 2, 3},       # Mon, Wed, Thu
    "general": {0, 2, 3, 4},    # Mon, Wed, Thu, Fri
}
