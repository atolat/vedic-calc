"""Constants for Vedic compatibility and Avakhada calculations.

Lookup tables for Ashtakoot Milan and Avakhada birth summary, extracted
from compatibility/calculator.py for reuse across the compatibility module.

Sources: Muhurta Chintamani, Brihat Jataka, BPHS.
"""

from __future__ import annotations

from vedic_calc.core.constants import Nakshatra, Sign


# ---------------------------------------------------------------------------
# Varna (spiritual nature) by Moon sign
# ---------------------------------------------------------------------------
# Brahmin (1, highest) > Kshatriya (2) > Vaishya (3) > Shudra (4)
VARNA = {
    Sign.ARIES: 2,        # Fire -> Kshatriya
    Sign.TAURUS: 3,       # Earth -> Vaishya
    Sign.GEMINI: 4,       # Air -> Shudra
    Sign.CANCER: 1,       # Water -> Brahmin
    Sign.LEO: 2,          # Fire -> Kshatriya
    Sign.VIRGO: 3,        # Earth -> Vaishya
    Sign.LIBRA: 4,        # Air -> Shudra
    Sign.SCORPIO: 1,      # Water -> Brahmin
    Sign.SAGITTARIUS: 2,  # Fire -> Kshatriya
    Sign.CAPRICORN: 3,    # Earth -> Vaishya
    Sign.AQUARIUS: 4,     # Air -> Shudra
    Sign.PISCES: 1,       # Water -> Brahmin
}

VARNA_NAMES = {1: "Brahmin", 2: "Kshatriya", 3: "Vaishya", 4: "Shudra"}

# ---------------------------------------------------------------------------
# Vashya (mutual influence) groups by Moon sign
# ---------------------------------------------------------------------------
# 1=Manava (human), 2=Vanachara (wild), 3=Chatushpada (quadruped),
# 4=Jalchara (water), 5=Keeta (insect)
VASHYA_GROUP = {
    Sign.ARIES: 3,       # Chatushpada
    Sign.TAURUS: 3,      # Chatushpada
    Sign.GEMINI: 1,      # Manava
    Sign.CANCER: 4,      # Jalchara
    Sign.LEO: 2,         # Vanachara
    Sign.VIRGO: 1,       # Manava
    Sign.LIBRA: 1,       # Manava
    Sign.SCORPIO: 5,     # Keeta
    Sign.SAGITTARIUS: 1, # Manava (first half human)
    Sign.CAPRICORN: 4,   # Jalchara (Makara = sea creature)
    Sign.AQUARIUS: 1,    # Manava
    Sign.PISCES: 4,      # Jalchara
}

VASHYA_NAMES = {1: "Manava", 2: "Vanachara", 3: "Chatushpada", 4: "Jalchara", 5: "Keeta"}

# ---------------------------------------------------------------------------
# Yoni (physical/temperamental) by nakshatra
# ---------------------------------------------------------------------------
# Format: (animal_index, gender) where gender: 0=Male, 1=Female
YONI = {
    Nakshatra.ASHWINI: (1, 0),           # Horse M
    Nakshatra.BHARANI: (2, 0),           # Elephant M
    Nakshatra.KRITTIKA: (3, 1),          # Sheep F
    Nakshatra.ROHINI: (4, 0),            # Serpent M
    Nakshatra.MRIGASHIRA: (4, 1),        # Serpent F
    Nakshatra.ARDRA: (5, 1),             # Dog F
    Nakshatra.PUNARVASU: (6, 1),         # Cat F
    Nakshatra.PUSHYA: (3, 0),            # Sheep M
    Nakshatra.ASHLESHA: (6, 0),          # Cat M
    Nakshatra.MAGHA: (7, 0),             # Rat M
    Nakshatra.PURVA_PHALGUNI: (7, 1),    # Rat F
    Nakshatra.UTTARA_PHALGUNI: (8, 0),   # Cow M
    Nakshatra.HASTA: (9, 1),             # Buffalo F
    Nakshatra.CHITRA: (10, 1),           # Tiger F
    Nakshatra.SWATI: (9, 0),             # Buffalo M
    Nakshatra.VISHAKHA: (10, 0),         # Tiger M
    Nakshatra.ANURADHA: (11, 1),         # Deer F
    Nakshatra.JYESHTHA: (11, 0),         # Deer M
    Nakshatra.MOOLA: (5, 0),             # Dog M
    Nakshatra.PURVA_ASHADHA: (12, 0),    # Monkey M
    Nakshatra.UTTARA_ASHADHA: (13, 0),   # Mongoose M
    Nakshatra.SHRAVANA: (12, 1),         # Monkey F
    Nakshatra.DHANISHTA: (14, 1),        # Lion F
    Nakshatra.SHATABHISHA: (1, 1),       # Horse F
    Nakshatra.PURVA_BHADRAPADA: (14, 0), # Lion M
    Nakshatra.UTTARA_BHADRAPADA: (8, 1), # Cow F
    Nakshatra.REVATI: (2, 1),            # Elephant F
}

YONI_ANIMAL_NAMES = {
    1: "Horse", 2: "Elephant", 3: "Sheep", 4: "Serpent", 5: "Dog",
    6: "Cat", 7: "Rat", 8: "Cow", 9: "Buffalo", 10: "Tiger",
    11: "Deer", 12: "Monkey", 13: "Mongoose", 14: "Lion",
}

# ---------------------------------------------------------------------------
# Gana (temperament) by nakshatra
# ---------------------------------------------------------------------------
# 1=Deva, 2=Manushya, 3=Rakshasa
GANA = {
    Nakshatra.ASHWINI: 1,          # Deva
    Nakshatra.BHARANI: 2,          # Manushya
    Nakshatra.KRITTIKA: 3,         # Rakshasa
    Nakshatra.ROHINI: 2,           # Manushya
    Nakshatra.MRIGASHIRA: 1,       # Deva
    Nakshatra.ARDRA: 2,            # Manushya
    Nakshatra.PUNARVASU: 1,        # Deva
    Nakshatra.PUSHYA: 1,           # Deva
    Nakshatra.ASHLESHA: 3,         # Rakshasa
    Nakshatra.MAGHA: 3,            # Rakshasa
    Nakshatra.PURVA_PHALGUNI: 2,   # Manushya
    Nakshatra.UTTARA_PHALGUNI: 2,  # Manushya
    Nakshatra.HASTA: 1,            # Deva
    Nakshatra.CHITRA: 3,           # Rakshasa
    Nakshatra.SWATI: 1,            # Deva
    Nakshatra.VISHAKHA: 3,         # Rakshasa
    Nakshatra.ANURADHA: 1,         # Deva
    Nakshatra.JYESHTHA: 3,         # Rakshasa
    Nakshatra.MOOLA: 3,            # Rakshasa
    Nakshatra.PURVA_ASHADHA: 2,    # Manushya
    Nakshatra.UTTARA_ASHADHA: 2,   # Manushya
    Nakshatra.SHRAVANA: 1,         # Deva
    Nakshatra.DHANISHTA: 3,        # Rakshasa
    Nakshatra.SHATABHISHA: 3,      # Rakshasa
    Nakshatra.PURVA_BHADRAPADA: 2, # Manushya
    Nakshatra.UTTARA_BHADRAPADA: 2,# Manushya
    Nakshatra.REVATI: 1,           # Deva
}

GANA_NAMES = {1: "Deva", 2: "Manushya", 3: "Rakshasa"}

# ---------------------------------------------------------------------------
# Nadi (health/constitution) by nakshatra
# ---------------------------------------------------------------------------
# 1=Aadi (Vata), 2=Madhya (Pitta), 3=Antya (Kapha)
# Pattern: zigzag 1-2-3-3-2-1 repeating every 6 nakshatras (BPHS standard).
NADI = {
    Nakshatra.ASHWINI: 1,           # Aadi (Vata)
    Nakshatra.BHARANI: 2,           # Madhya (Pitta)
    Nakshatra.KRITTIKA: 3,          # Antya (Kapha)
    Nakshatra.ROHINI: 3,            # Antya
    Nakshatra.MRIGASHIRA: 2,        # Madhya
    Nakshatra.ARDRA: 1,             # Aadi
    Nakshatra.PUNARVASU: 1,         # Aadi
    Nakshatra.PUSHYA: 2,            # Madhya
    Nakshatra.ASHLESHA: 3,          # Antya
    Nakshatra.MAGHA: 3,             # Antya
    Nakshatra.PURVA_PHALGUNI: 2,    # Madhya
    Nakshatra.UTTARA_PHALGUNI: 1,   # Aadi
    Nakshatra.HASTA: 1,             # Aadi
    Nakshatra.CHITRA: 2,            # Madhya
    Nakshatra.SWATI: 3,             # Antya
    Nakshatra.VISHAKHA: 3,          # Antya
    Nakshatra.ANURADHA: 2,          # Madhya
    Nakshatra.JYESHTHA: 1,          # Aadi
    Nakshatra.MOOLA: 1,             # Aadi
    Nakshatra.PURVA_ASHADHA: 2,     # Madhya
    Nakshatra.UTTARA_ASHADHA: 3,    # Antya
    Nakshatra.SHRAVANA: 3,          # Antya
    Nakshatra.DHANISHTA: 2,         # Madhya
    Nakshatra.SHATABHISHA: 1,       # Aadi
    Nakshatra.PURVA_BHADRAPADA: 1,  # Aadi
    Nakshatra.UTTARA_BHADRAPADA: 2, # Madhya
    Nakshatra.REVATI: 3,            # Antya
}

NADI_NAMES = {1: "Aadi (Vata)", 2: "Madhya (Pitta)", 3: "Antya (Kapha)"}


# ---------------------------------------------------------------------------
# Avakhada-specific constants
# ---------------------------------------------------------------------------

# Name letter (first syllable) by (nakshatra_number, pada)
NAKSHATRA_NAME_LETTERS: dict[tuple[int, int], str] = {
    (1, 1): "Chu", (1, 2): "Che", (1, 3): "Cho", (1, 4): "La",
    (2, 1): "Li", (2, 2): "Lu", (2, 3): "Le", (2, 4): "Lo",
    (3, 1): "A", (3, 2): "I", (3, 3): "U", (3, 4): "E",
    (4, 1): "O", (4, 2): "Va", (4, 3): "Vi", (4, 4): "Vu",
    (5, 1): "Ve", (5, 2): "Vo", (5, 3): "Ka", (5, 4): "Ki",
    (6, 1): "Ku", (6, 2): "Gha", (6, 3): "Ng", (6, 4): "Chh",
    (7, 1): "Ke", (7, 2): "Ko", (7, 3): "Ha", (7, 4): "Hi",
    (8, 1): "Hu", (8, 2): "He", (8, 3): "Ho", (8, 4): "Da",
    (9, 1): "Di", (9, 2): "Du", (9, 3): "De", (9, 4): "Do",
    (10, 1): "Ma", (10, 2): "Mi", (10, 3): "Mu", (10, 4): "Me",
    (11, 1): "Mo", (11, 2): "Ta", (11, 3): "Ti", (11, 4): "Tu",
    (12, 1): "Te", (12, 2): "To", (12, 3): "Pa", (12, 4): "Pi",
    (13, 1): "Pu", (13, 2): "Sha", (13, 3): "Na", (13, 4): "Tha",
    (14, 1): "Pe", (14, 2): "Po", (14, 3): "Ra", (14, 4): "Ri",
    (15, 1): "Ru", (15, 2): "Re", (15, 3): "Ro", (15, 4): "Ta",
    (16, 1): "Ti", (16, 2): "Tu", (16, 3): "Te", (16, 4): "To",
    (17, 1): "Na", (17, 2): "Ni", (17, 3): "Nu", (17, 4): "Ne",
    (18, 1): "No", (18, 2): "Ya", (18, 3): "Yi", (18, 4): "Yu",
    (19, 1): "Ye", (19, 2): "Yo", (19, 3): "Bha", (19, 4): "Bhi",
    (20, 1): "Bhu", (20, 2): "Dha", (20, 3): "Pha", (20, 4): "Dha",
    (21, 1): "Bhe", (21, 2): "Bho", (21, 3): "Ja", (21, 4): "Ji",
    (22, 1): "Ju", (22, 2): "Je", (22, 3): "Jo", (22, 4): "Gha",
    (23, 1): "Ga", (23, 2): "Gi", (23, 3): "Gu", (23, 4): "Ge",
    (24, 1): "Go", (24, 2): "Sa", (24, 3): "Si", (24, 4): "Su",
    (25, 1): "Se", (25, 2): "So", (25, 3): "Da", (25, 4): "Di",
    (26, 1): "Du", (26, 2): "Tha", (26, 3): "Jha", (26, 4): "Da",
    (27, 1): "De", (27, 2): "Do", (27, 3): "Cha", (27, 4): "Chi",
}

# Tatva (element) by sign number (1-12)
TATVA: dict[int, str] = {
    1: "Fire", 2: "Earth", 3: "Air", 4: "Water",
    5: "Fire", 6: "Earth", 7: "Air", 8: "Water",
    9: "Fire", 10: "Earth", 11: "Air", 12: "Water",
}

# Paya (footfall) by nakshatra number (1-27)
PAYA: dict[int, str] = {
    1: "Gold", 2: "Gold", 3: "Gold", 4: "Silver", 5: "Silver", 6: "Silver",
    7: "Copper", 8: "Copper", 9: "Copper", 10: "Iron", 11: "Iron", 12: "Iron",
    13: "Gold", 14: "Gold", 15: "Gold", 16: "Silver", 17: "Silver", 18: "Silver",
    19: "Copper", 20: "Copper", 21: "Copper", 22: "Iron", 23: "Iron", 24: "Iron",
    25: "Gold", 26: "Gold", 27: "Gold",
}

# Nakshatra lords by nakshatra number (1-27) -> Planet enum value
# Cycle: Ketu(8), Venus(5), Sun(0), Moon(1), Mars(2), Rahu(7), Jupiter(4), Saturn(6), Mercury(3)
NAKSHATRA_LORDS: dict[int, int] = {
    1: 8, 2: 5, 3: 0, 4: 1, 5: 2, 6: 7, 7: 4, 8: 6, 9: 3,
    10: 8, 11: 5, 12: 0, 13: 1, 14: 2, 15: 7, 16: 4, 17: 6, 18: 3,
    19: 8, 20: 5, 21: 0, 22: 1, 23: 2, 24: 7, 25: 4, 26: 6, 27: 3,
}
