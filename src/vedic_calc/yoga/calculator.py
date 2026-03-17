"""Vedic yoga (planetary combination) detection engine.

Detects ~30 classical yogas from a birth chart. Each yoga is a specific
planetary configuration that indicates particular life themes. Results
include both present and absent yogas so the caller can see what was checked.

Yoga categories covered:
    - Pancha Mahapurusha (5) — Mars/Mercury/Jupiter/Venus/Saturn in own/exalted + kendra
    - Gajakesari — Jupiter in kendra from Moon
    - Budhaditya — Sun-Mercury conjunction
    - Dhana (wealth) — lords of 2nd/11th conjunct or exchanged; Lakshmi yoga
    - Raja (power) — kendra-trikona lord conjunction
    - Viparita Raja — dusthana lords in dusthana houses
    - Saraswati — Jupiter/Venus/Mercury in kendra/trikona/2nd
    - Lunar yogas — Kemadruma, Sunapha, Anapha, Durudhara
    - Solar yogas — Veshi, Voshi, Ubhayachari
    - Chandra-Mangal, Amala, Shakata, Daridra
    - Neechabhanga Raja — debilitation cancellation

Sources: BPHS (Brihat Parashara Hora Shastra), Saravali, Phaladeepika.
"""

from __future__ import annotations

from vedic_calc.core.constants import (
    DEBILITATION,
    EXALTATION,
    KENDRA_HOUSES,
    SIGN_LORDS,
    TRIKONA_HOUSES,
    Planet,
    Sign,
)
from vedic_calc.core.types import BirthChart, YogaResult


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _planet_house(chart: BirthChart, planet: Planet) -> int:
    """Get the house number (1-12) where a planet is placed.

    Uses the whole-sign house system: the planet's sign is matched against
    the sign assigned to each house.
    """
    planet_sign = chart.planets[planet].sign
    for house in chart.houses:
        if house.sign == planet_sign:
            return house.house_number
    return 1  # fallback — should never happen with valid chart data


def _planets_in_same_sign(chart: BirthChart, p1: Planet, p2: Planet) -> bool:
    """Check whether two planets occupy the same zodiac sign."""
    return chart.planets[p1].sign == chart.planets[p2].sign


def _sign_distance(from_sign: Sign, to_sign: Sign) -> int:
    """Count signs from ``from_sign`` to ``to_sign`` (1-indexed, inclusive).

    Example: Aries to Cancer → 4 (Aries=1, Taurus=2, Gemini=3, Cancer=4).
    """
    return ((int(to_sign) - int(from_sign)) % 12) + 1


def _house_lord(chart: BirthChart, house_number: int) -> Planet:
    """Return the lord of a given house (1-12)."""
    return chart.houses[house_number - 1].lord


def _is_in_own_sign(planet: Planet, sign: Sign) -> bool:
    """Check if a planet is in one of its own signs."""
    return SIGN_LORDS.get(sign) == planet


def _is_exalted(planet: Planet, sign: Sign) -> bool:
    """Check if a planet is exalted in the given sign."""
    if planet in EXALTATION:
        return EXALTATION[planet][0] == sign
    return False


def _is_debilitated(planet: Planet, sign: Sign) -> bool:
    """Check if a planet is debilitated in the given sign."""
    if planet in DEBILITATION:
        return DEBILITATION[planet][0] == sign
    return False


def _is_in_own_or_exalted(planet: Planet, sign: Sign) -> bool:
    """Check if a planet is in its own sign or exalted."""
    return _is_in_own_sign(planet, sign) or _is_exalted(planet, sign)


# Benefic planets used in Amala, Sunapha, etc.
_BENEFICS = {Planet.JUPITER, Planet.VENUS, Planet.MERCURY, Planet.MOON}

# Planets considered for Moon-based yogas (excluding Sun, Rahu, Ketu)
_MOON_YOGA_PLANETS = {
    Planet.MARS, Planet.MERCURY, Planet.JUPITER, Planet.VENUS, Planet.SATURN,
}

# Planets considered for Sun-based yogas (excluding Moon, Rahu, Ketu)
_SUN_YOGA_PLANETS = {
    Planet.MARS, Planet.MERCURY, Planet.JUPITER, Planet.VENUS, Planet.SATURN,
}


# ---------------------------------------------------------------------------
# Individual yoga detectors
# ---------------------------------------------------------------------------

def _detect_ruchaka(chart: BirthChart) -> YogaResult:
    """Ruchaka Yoga — Mars in own/exalted sign in a kendra house.

    WHY THIS WORKS: A planet in its own or exalted sign is at peak strength
    (full dignity). A kendra (1st/4th/7th/10th) is an "angular" house — the
    most prominent positions in a chart (like the 4 cardinal directions).
    Mars specifically signifies courage, physical strength, and military
    leadership. When Mars is both dignified AND prominently placed, it
    produces exceptional courage and command — hence "Ruchaka" (brilliance).

    Source: BPHS Ch. 75; Phaladeepika Ch. 7.
    """
    planet = Planet.MARS
    sign = chart.planets[planet].sign
    house = _planet_house(chart, planet)
    present = _is_in_own_or_exalted(planet, sign) and house in KENDRA_HOUSES
    return YogaResult(
        name="Ruchaka",
        category="pancha_mahapurusha",
        involved_planets=[planet],
        description="Mars in own/exalted sign in kendra — courage, military prowess, leadership.",
        is_present=present,
    )


def _detect_bhadra(chart: BirthChart) -> YogaResult:
    """Bhadra Yoga — Mercury in own/exalted sign in a kendra house.

    WHY THIS WORKS: Mercury governs intellect, speech, and commerce. When
    dignified (own/exalted sign) and in a kendra, Mercury's significations
    manifest powerfully — sharp analytical mind, persuasive speech, and
    business success. Named "Bhadra" (auspicious/noble).

    Source: BPHS Ch. 75; Phaladeepika Ch. 7.
    """
    planet = Planet.MERCURY
    sign = chart.planets[planet].sign
    house = _planet_house(chart, planet)
    present = _is_in_own_or_exalted(planet, sign) and house in KENDRA_HOUSES
    return YogaResult(
        name="Bhadra",
        category="pancha_mahapurusha",
        involved_planets=[planet],
        description="Mercury in own/exalted sign in kendra — intellect, eloquence, business acumen.",
        is_present=present,
    )


def _detect_hamsa(chart: BirthChart) -> YogaResult:
    """Hamsa Yoga — Jupiter in own/exalted sign in a kendra house.

    WHY THIS WORKS: Jupiter is the "great benefic" — teacher, wisdom, dharma.
    Dignified Jupiter in a kendra produces a person drawn to knowledge,
    spirituality, and righteous conduct. "Hamsa" (swan) symbolizes the
    mythical bird that can separate milk from water — discernment and purity.

    Source: BPHS Ch. 75; Phaladeepika Ch. 7.
    """
    planet = Planet.JUPITER
    sign = chart.planets[planet].sign
    house = _planet_house(chart, planet)
    present = _is_in_own_or_exalted(planet, sign) and house in KENDRA_HOUSES
    return YogaResult(
        name="Hamsa",
        category="pancha_mahapurusha",
        involved_planets=[planet],
        description="Jupiter in own/exalted sign in kendra — wisdom, spiritual inclination, fortune.",
        is_present=present,
    )


def _detect_malavya(chart: BirthChart) -> YogaResult:
    """Malavya Yoga — Venus in own/exalted sign in a kendra house.

    WHY THIS WORKS: Venus rules beauty, art, love, and material comfort.
    Dignified Venus in a kendra gives prominence to these themes — the
    person enjoys luxury, has refined aesthetic sensibilities, and attracts
    harmonious relationships. Named after the Malava region (prosperous).

    Source: BPHS Ch. 75; Phaladeepika Ch. 7.
    """
    planet = Planet.VENUS
    sign = chart.planets[planet].sign
    house = _planet_house(chart, planet)
    present = _is_in_own_or_exalted(planet, sign) and house in KENDRA_HOUSES
    return YogaResult(
        name="Malavya",
        category="pancha_mahapurusha",
        involved_planets=[planet],
        description="Venus in own/exalted sign in kendra — luxury, artistic talent, beauty.",
        is_present=present,
    )


def _detect_shasha(chart: BirthChart) -> YogaResult:
    """Shasha Yoga — Saturn in own/exalted sign in a kendra house.

    WHY THIS WORKS: Saturn governs discipline, longevity, and authority over
    large organizations. Most people experience Saturn as delays and hardship,
    but when Saturn is dignified AND prominently placed, its constructive side
    emerges — systematic thinking, political power, and enduring legacy.
    "Shasha" (rabbit) — deceptively gentle, surprisingly powerful.

    Source: BPHS Ch. 75; Phaladeepika Ch. 7.
    """
    planet = Planet.SATURN
    sign = chart.planets[planet].sign
    house = _planet_house(chart, planet)
    present = _is_in_own_or_exalted(planet, sign) and house in KENDRA_HOUSES
    return YogaResult(
        name="Shasha",
        category="pancha_mahapurusha",
        involved_planets=[planet],
        description="Saturn in own/exalted sign in kendra — authority, discipline, political power.",
        is_present=present,
    )


def _detect_gajakesari(chart: BirthChart) -> YogaResult:
    """Gajakesari Yoga — Jupiter in kendra (1/4/7/10) from Moon.

    WHY THIS WORKS: The Moon represents the mind, and Jupiter represents
    wisdom and expansion. When Jupiter is in an angular house FROM the Moon,
    Jupiter's wisdom directly supports the mind — producing intelligence,
    good judgment, and the ability to inspire others. "Gajakesari" means
    "elephant-lion" — the grandeur of an elephant combined with the
    courage of a lion. One of the most commonly cited and recognized yogas.

    NOTE: This yoga is measured from Moon (not from the ascendant), making
    it a "chandra yoga" — its effects relate to the mind and public image.

    Source: Phaladeepika Ch. 6; Saravali Ch. 33.
    """
    moon_sign = chart.planets[Planet.MOON].sign
    jup_sign = chart.planets[Planet.JUPITER].sign
    distance = _sign_distance(moon_sign, jup_sign)
    present = distance in {1, 4, 7, 10}
    return YogaResult(
        name="Gajakesari",
        category="lunar",
        involved_planets=[Planet.MOON, Planet.JUPITER],
        description="Jupiter in kendra from Moon — fame, intelligence, lasting reputation.",
        is_present=present,
    )


def _detect_budhaditya(chart: BirthChart) -> YogaResult:
    """Budhaditya Yoga — Sun and Mercury in the same sign.

    WHY THIS WORKS: Sun = authority and self-expression; Mercury = intellect
    and communication. Their conjunction combines charisma with articulation.
    The person can express ideas with authority — scholars, writers, public
    speakers. "Budha" (Mercury) + "Aditya" (Sun) = enlightened intellect.

    CAVEAT: This yoga is extremely common because Mercury is never more than
    ~28 degrees from the Sun (inner planet), so they're often in the same
    sign. Its strength depends heavily on whether Mercury is combust (too
    close to the Sun, typically < 14 degrees). A combust Mercury weakens
    the yoga significantly. Check combustion status separately.

    Source: Phaladeepika Ch. 6.
    """
    present = _planets_in_same_sign(chart, Planet.SUN, Planet.MERCURY)
    return YogaResult(
        name="Budhaditya",
        category="solar",
        involved_planets=[Planet.SUN, Planet.MERCURY],
        description="Sun-Mercury conjunction — sharp intellect, fame through learning.",
        is_present=present,
    )


def _detect_dhana_basic(chart: BirthChart) -> YogaResult:
    """Dhana Yoga (basic) — Lords of 2nd and 11th conjunct or exchanged.

    WHY THIS WORKS: The 2nd house governs accumulated wealth (bank balance,
    family assets, food) and the 11th house governs income/gains (salary,
    profits, wishes fulfilled). When their lords conjoin or exchange houses,
    the wealth-accumulation and income-generation themes merge — money flows
    in and stays. "Dhana" = wealth.

    Source: BPHS Ch. 41 (Dhana Yoga chapter).
    """
    lord_2 = _house_lord(chart, 2)
    lord_11 = _house_lord(chart, 11)

    # Conjunction: both in the same sign
    conjunct = _planets_in_same_sign(chart, lord_2, lord_11)

    # Exchange: lord of 2nd in 11th house AND lord of 11th in 2nd house
    exchanged = (
        _planet_house(chart, lord_2) == 11
        and _planet_house(chart, lord_11) == 2
    )

    present = (lord_2 != lord_11) and (conjunct or exchanged)
    return YogaResult(
        name="Dhana",
        category="dhana",
        involved_planets=[lord_2, lord_11],
        description="Lords of 2nd and 11th conjunct or exchanged — wealth accumulation.",
        is_present=present,
    )


def _detect_lakshmi(chart: BirthChart) -> YogaResult:
    """Lakshmi Yoga — Lord of 9th in kendra + Venus in own/exalted sign.

    WHY THIS WORKS: The 9th house = fortune, dharma, and past-life merit.
    Venus = luxury, wealth, and the goddess Lakshmi herself. When the 9th
    lord is prominently placed (kendra) AND Venus is dignified, fortune and
    material abundance combine. Named after Lakshmi, goddess of wealth —
    this yoga indicates both material prosperity and divine grace.

    Source: Phaladeepika Ch. 6.
    """
    lord_9 = _house_lord(chart, 9)
    lord_9_house = _planet_house(chart, lord_9)
    venus_sign = chart.planets[Planet.VENUS].sign
    present = (
        lord_9_house in KENDRA_HOUSES
        and _is_in_own_or_exalted(Planet.VENUS, venus_sign)
    )
    return YogaResult(
        name="Lakshmi",
        category="dhana",
        involved_planets=[lord_9, Planet.VENUS],
        description="Lord of 9th in kendra with Venus in own/exalted — great wealth, luxury.",
        is_present=present,
    )


def _detect_raja_yoga(chart: BirthChart) -> YogaResult:
    """Raja Yoga — A kendra lord and a trikona lord conjunct.

    Checks all combinations of kendra lords (1,4,7,10) and trikona lords
    (1,5,9). When two different planets that respectively lord a kendra
    and a trikona are in the same sign, Raja Yoga is formed.
    """
    kendra_lords = {_house_lord(chart, h) for h in KENDRA_HOUSES}
    trikona_lords = {_house_lord(chart, h) for h in TRIKONA_HOUSES}

    involved: list[Planet] = []
    present = False

    for kl in kendra_lords:
        for tl in trikona_lords:
            if kl != tl and _planets_in_same_sign(chart, kl, tl):
                present = True
                if kl not in involved:
                    involved.append(kl)
                if tl not in involved:
                    involved.append(tl)

    if not involved:
        # Provide representative planets even when absent
        involved = [_house_lord(chart, 1)]

    return YogaResult(
        name="Raja",
        category="raja",
        involved_planets=involved,
        description="Kendra and trikona lords conjunct — power, authority, high status.",
        is_present=present,
    )


def _detect_viparita_raja(chart: BirthChart) -> YogaResult:
    """Viparita Raja Yoga — Lord of 6th, 8th, or 12th placed in 6, 8, or 12.

    WHY THIS WORKS: Houses 6, 8, and 12 are "dusthana" (difficult houses) —
    enemies, death, and losses respectively. Normally, their lords cause
    trouble wherever they sit. But when a dusthana lord sits in ANOTHER
    dusthana, the two negatives cancel out — "the enemy of my enemy is my
    friend." This produces unexpected gains through adversity: winning
    lawsuits (6th), receiving inheritance (8th), or gaining from foreign
    lands (12th). "Viparita" = reversed/inverted.

    Source: BPHS Ch. 40.
    """
    dusthana = [6, 8, 12]
    involved: list[Planet] = []
    present = False

    for h in dusthana:
        lord = _house_lord(chart, h)
        lord_h = _planet_house(chart, lord)
        if lord_h in dusthana:
            present = True
            if lord not in involved:
                involved.append(lord)

    if not involved:
        involved = [_house_lord(chart, 6)]

    return YogaResult(
        name="Viparita Raja",
        category="raja",
        involved_planets=involved,
        description="Dusthana lord in dusthana — rise through adversity, unexpected gains.",
        is_present=present,
    )


def _detect_saraswati(chart: BirthChart) -> YogaResult:
    """Saraswati Yoga — Jupiter, Venus, Mercury all in kendras, trikonas, or 2nd.

    WHY THIS WORKS: Jupiter (wisdom), Venus (art/beauty), and Mercury
    (intellect/speech) are the three planets of learning and creative
    expression. When ALL three are well-placed (in kendras, trikonas, or the
    2nd house of speech/education), the person excels in knowledge, writing,
    music, and eloquence. Named after Saraswati, goddess of learning.

    The 2nd house is specifically included because it governs speech and
    formal education — critical for expressing knowledge.

    Source: BPHS Ch. 75; Saravali.
    """
    good_houses = set(KENDRA_HOUSES) | set(TRIKONA_HOUSES) | {2}
    planets = [Planet.JUPITER, Planet.VENUS, Planet.MERCURY]
    present = all(_planet_house(chart, p) in good_houses for p in planets)
    return YogaResult(
        name="Saraswati",
        category="knowledge",
        involved_planets=planets,
        description="Jupiter, Venus, Mercury in kendra/trikona/2nd — learning, arts, eloquence.",
        is_present=present,
    )


def _detect_kemadruma(chart: BirthChart) -> YogaResult:
    """Kemadruma Yoga (negative) — No planet in 2nd or 12th from Moon.

    WHY THIS WORKS: The Moon represents the mind and emotional stability.
    Planets adjacent to the Moon (2nd and 12th from it) act as "support" —
    they give the mind something to lean on. When NO planet flanks the Moon,
    the mind feels isolated and unsupported. This can manifest as loneliness,
    financial instability, and emotional vulnerability.

    This is the inverse of Sunapha/Anapha/Durudhara yogas. Only "real"
    planets are considered (Mars, Mercury, Jupiter, Venus, Saturn) — Sun is
    excluded because it's always near its own trajectory, and Rahu/Ketu are
    shadow planets without physical substance.

    IMPORTANT: Many cancellation conditions exist (Moon in kendra, aspected
    by Jupiter, etc.) that are not checked here. A raw Kemadruma finding
    should be qualified by checking for cancellations.

    Source: Phaladeepika Ch. 6; Saravali Ch. 33.
    """
    moon_sign = chart.planets[Planet.MOON].sign
    has_2nd = False
    has_12th = False

    for p in _MOON_YOGA_PLANETS:
        dist = _sign_distance(moon_sign, chart.planets[p].sign)
        if dist == 2:
            has_2nd = True
        elif dist == 12:
            has_12th = True

    present = not has_2nd and not has_12th
    return YogaResult(
        name="Kemadruma",
        category="negative",
        involved_planets=[Planet.MOON],
        description="No planet in 2nd or 12th from Moon — poverty, struggles, loneliness.",
        is_present=present,
    )


def _detect_shakata(chart: BirthChart) -> YogaResult:
    """Shakata Yoga (negative) — Jupiter in 6th, 8th, or 12th from Moon.

    WHY THIS WORKS: This is the opposite of Gajakesari. Jupiter is the great
    benefic and protector of the mind (Moon). When Jupiter is in the 6th,
    8th, or 12th from Moon (dusthana positions), Jupiter's protective
    influence is blocked. The mind lacks the stabilizing wisdom that Jupiter
    provides, leading to fluctuating fortunes — ups and downs like a cart
    wheel. "Shakata" = cart (the wheel goes up, then down, cyclically).

    Source: Phaladeepika Ch. 6.
    """
    moon_sign = chart.planets[Planet.MOON].sign
    jup_sign = chart.planets[Planet.JUPITER].sign
    distance = _sign_distance(moon_sign, jup_sign)
    present = distance in {6, 8, 12}
    return YogaResult(
        name="Shakata",
        category="negative",
        involved_planets=[Planet.MOON, Planet.JUPITER],
        description="Jupiter in 6/8/12 from Moon — fluctuating fortunes, instability.",
        is_present=present,
    )


def _detect_daridra(chart: BirthChart) -> YogaResult:
    """Daridra Yoga (negative) — Lord of 11th in 6th, 8th, or 12th house.

    WHY THIS WORKS: The 11th house is the house of gains, income, and wishes
    fulfilled. When its lord falls into a dusthana (6th = enemies/debts,
    8th = sudden losses, 12th = expenses/foreign lands), the income-generating
    capacity is damaged. Money comes but goes to debts (6th), is lost suddenly
    (8th), or is spent/sent abroad (12th). "Daridra" = poverty.

    Source: Phaladeepika Ch. 6.
    """
    lord_11 = _house_lord(chart, 11)
    lord_11_house = _planet_house(chart, lord_11)
    present = lord_11_house in {6, 8, 12}
    return YogaResult(
        name="Daridra",
        category="negative",
        involved_planets=[lord_11],
        description="Lord of 11th in dusthana — financial difficulties, obstructed gains.",
        is_present=present,
    )


def _detect_chandra_mangal(chart: BirthChart) -> YogaResult:
    """Chandra-Mangal Yoga — Moon and Mars in the same sign.

    WHY THIS WORKS: Moon = mind/emotions, Mars = action/drive/courage.
    Their conjunction creates an emotionally driven, action-oriented
    personality — someone who channels feelings into enterprise. This is
    particularly associated with self-made wealth because the person has
    both the emotional motivation (Moon) and the courage to act (Mars).

    Source: Saravali Ch. 33.
    """
    present = _planets_in_same_sign(chart, Planet.MOON, Planet.MARS)
    return YogaResult(
        name="Chandra-Mangal",
        category="wealth",
        involved_planets=[Planet.MOON, Planet.MARS],
        description="Moon-Mars conjunction — wealth through self-effort, business acumen.",
        is_present=present,
    )


def _detect_amala(chart: BirthChart) -> YogaResult:
    """Amala Yoga — A benefic (Jupiter, Venus, Mercury, Moon) in the 10th from lagna.

    WHY THIS WORKS: The 10th house is the most visible house — career, public
    reputation, actions in the world. When a natural benefic (Jupiter, Venus,
    Mercury, or Moon) occupies this house, the person's public actions and
    career are colored by benefic qualities: ethics, generosity, beauty, or
    intelligence. "Amala" = spotless/pure — their public record is clean.

    Source: Phaladeepika Ch. 6.
    """
    involved: list[Planet] = []
    present = False

    for p in _BENEFICS:
        if _planet_house(chart, p) == 10:
            present = True
            involved.append(p)

    if not involved:
        involved = [Planet.JUPITER]  # representative planet

    return YogaResult(
        name="Amala",
        category="benefic",
        involved_planets=involved,
        description="Benefic in 10th house — spotless reputation, virtuous career.",
        is_present=present,
    )


def _detect_sunapha(chart: BirthChart) -> YogaResult:
    """Sunapha Yoga — A planet (not Sun, Rahu, Ketu) in the 2nd from Moon.

    WHY THIS WORKS: The 2nd from Moon represents what "follows" the mind —
    resources, speech, and accumulated intelligence. A planet here gives the
    Moon tangible support on its forward path. The person is self-made
    (not dependent on inheritance) with good intellect and material comfort.
    The specific planet in the 2nd colors the effect (Mars = wealth through
    effort, Jupiter = through wisdom, Venus = through art/beauty, etc.).

    Source: Phaladeepika Ch. 6; Saravali Ch. 33.
    """
    moon_sign = chart.planets[Planet.MOON].sign
    involved: list[Planet] = []
    present = False

    for p in _MOON_YOGA_PLANETS:
        if _sign_distance(moon_sign, chart.planets[p].sign) == 2:
            present = True
            involved.append(p)

    if not involved:
        involved = [Planet.MOON]

    return YogaResult(
        name="Sunapha",
        category="lunar",
        involved_planets=involved,
        description="Planet in 2nd from Moon — self-made wealth, good intellect.",
        is_present=present,
    )


def _detect_anapha(chart: BirthChart) -> YogaResult:
    """Anapha Yoga — A planet (not Sun, Rahu, Ketu) in the 12th from Moon.

    WHY THIS WORKS: The 12th from Moon represents what "precedes" the mind —
    the subconscious, past experiences, and inner world. A planet here gives
    the Moon depth and spiritual substance. The person has a magnetic
    personality, spiritual inclinations, and a rich inner life. They may
    appear reserved but carry quiet authority.

    Source: Phaladeepika Ch. 6; Saravali Ch. 33.
    """
    moon_sign = chart.planets[Planet.MOON].sign
    involved: list[Planet] = []
    present = False

    for p in _MOON_YOGA_PLANETS:
        if _sign_distance(moon_sign, chart.planets[p].sign) == 12:
            present = True
            involved.append(p)

    if not involved:
        involved = [Planet.MOON]

    return YogaResult(
        name="Anapha",
        category="lunar",
        involved_planets=involved,
        description="Planet in 12th from Moon — magnetic personality, spiritual bent.",
        is_present=present,
    )


def _detect_durudhara(chart: BirthChart) -> YogaResult:
    """Durudhara Yoga — Planets in both 2nd and 12th from Moon.

    WHY THIS WORKS: This combines Sunapha (2nd from Moon) and Anapha (12th
    from Moon). The Moon is "flanked" — supported from both sides, like a
    king with guards on each flank. The person has both material support
    (2nd = resources ahead) and inner depth (12th = spiritual substance
    behind). This is the strongest of the three lunar yogas — it produces
    wealth, fame, and a generous, well-rounded personality.

    Source: Phaladeepika Ch. 6; Saravali Ch. 33.
    """
    moon_sign = chart.planets[Planet.MOON].sign
    in_2nd: list[Planet] = []
    in_12th: list[Planet] = []

    for p in _MOON_YOGA_PLANETS:
        dist = _sign_distance(moon_sign, chart.planets[p].sign)
        if dist == 2:
            in_2nd.append(p)
        elif dist == 12:
            in_12th.append(p)

    present = len(in_2nd) > 0 and len(in_12th) > 0
    involved = in_2nd + in_12th if present else [Planet.MOON]
    return YogaResult(
        name="Durudhara",
        category="lunar",
        involved_planets=involved,
        description="Planets flanking Moon (2nd and 12th) — wealth, fame, generous nature.",
        is_present=present,
    )


def _detect_veshi(chart: BirthChart) -> YogaResult:
    """Veshi Yoga — A planet (not Moon, Rahu, Ketu) in the 2nd from Sun.

    WHY THIS WORKS: The Sun represents the soul, authority, and ego. A planet
    in the 2nd from Sun supports the Sun's significations going forward —
    giving the person a balanced temperament, good memory, and the ability
    to earn through their authority. This is the solar equivalent of Sunapha.
    Moon is excluded because it's too close to the Sun to be meaningful here.

    Source: Phaladeepika Ch. 6.
    """
    sun_sign = chart.planets[Planet.SUN].sign
    involved: list[Planet] = []
    present = False

    for p in _SUN_YOGA_PLANETS:
        if _sign_distance(sun_sign, chart.planets[p].sign) == 2:
            present = True
            involved.append(p)

    if not involved:
        involved = [Planet.SUN]

    return YogaResult(
        name="Veshi",
        category="solar",
        involved_planets=involved,
        description="Planet in 2nd from Sun — balanced temperament, good memory.",
        is_present=present,
    )


def _detect_voshi(chart: BirthChart) -> YogaResult:
    """Voshi Yoga — A planet (not Moon, Rahu, Ketu) in the 12th from Sun.

    WHY THIS WORKS: The 12th from Sun represents what precedes the ego —
    selfless giving, spiritual aspiration, and skill acquired in past lives.
    A planet here adds depth to the Sun's authority, making the person
    charitable, skillful, and learned rather than merely powerful. Solar
    equivalent of Anapha.

    Source: Phaladeepika Ch. 6.
    """
    sun_sign = chart.planets[Planet.SUN].sign
    involved: list[Planet] = []
    present = False

    for p in _SUN_YOGA_PLANETS:
        if _sign_distance(sun_sign, chart.planets[p].sign) == 12:
            present = True
            involved.append(p)

    if not involved:
        involved = [Planet.SUN]

    return YogaResult(
        name="Voshi",
        category="solar",
        involved_planets=involved,
        description="Planet in 12th from Sun — charitable, skillful, learned.",
        is_present=present,
    )


def _detect_ubhayachari(chart: BirthChart) -> YogaResult:
    """Ubhayachari Yoga — Planets in both 2nd and 12th from Sun.

    WHY THIS WORKS: The Sun is flanked by planets on both sides — supported
    from ahead (2nd) and behind (12th). This is the solar equivalent of
    Durudhara. The person's authority (Sun) is bolstered from all directions,
    producing kingly status, eloquent speech, and the ability to command
    respect. "Ubhayachari" = moving on both sides.

    Source: Phaladeepika Ch. 6.
    """
    sun_sign = chart.planets[Planet.SUN].sign
    in_2nd: list[Planet] = []
    in_12th: list[Planet] = []

    for p in _SUN_YOGA_PLANETS:
        dist = _sign_distance(sun_sign, chart.planets[p].sign)
        if dist == 2:
            in_2nd.append(p)
        elif dist == 12:
            in_12th.append(p)

    present = len(in_2nd) > 0 and len(in_12th) > 0
    involved = in_2nd + in_12th if present else [Planet.SUN]
    return YogaResult(
        name="Ubhayachari",
        category="solar",
        involved_planets=involved,
        description="Planets flanking Sun (2nd and 12th) — kingly status, eloquence.",
        is_present=present,
    )


def _detect_neechabhanga_raja(chart: BirthChart) -> YogaResult:
    """Neechabhanga Raja Yoga — Debilitated planet whose debilitation is cancelled.

    Cancellation condition checked: the lord of the sign where the planet
    is debilitated is in a kendra from lagna or from Moon.
    """
    lagna_sign = chart.ascendant.sign
    moon_sign = chart.planets[Planet.MOON].sign
    involved: list[Planet] = []
    present = False

    for planet in Planet:
        if planet not in DEBILITATION:
            continue
        deb_sign = DEBILITATION[planet][0]
        if chart.planets[planet].sign != deb_sign:
            continue

        # Planet is debilitated — check cancellation
        sign_lord = SIGN_LORDS[deb_sign]
        sign_lord_sign = chart.planets[sign_lord].sign

        # Lord of debilitation sign in kendra from lagna?
        dist_from_lagna = _sign_distance(lagna_sign, sign_lord_sign)
        in_kendra_from_lagna = dist_from_lagna in {1, 4, 7, 10}

        # Lord of debilitation sign in kendra from Moon?
        dist_from_moon = _sign_distance(moon_sign, sign_lord_sign)
        in_kendra_from_moon = dist_from_moon in {1, 4, 7, 10}

        # Also check: lord of exaltation sign of the debilitated planet
        # is in kendra from lagna or Moon
        exalt_sign = EXALTATION[planet][0]
        exalt_lord = SIGN_LORDS[exalt_sign]
        exalt_lord_sign = chart.planets[exalt_lord].sign

        exalt_dist_lagna = _sign_distance(lagna_sign, exalt_lord_sign)
        exalt_dist_moon = _sign_distance(moon_sign, exalt_lord_sign)
        exalt_in_kendra = exalt_dist_lagna in {1, 4, 7, 10} or exalt_dist_moon in {1, 4, 7, 10}

        if in_kendra_from_lagna or in_kendra_from_moon or exalt_in_kendra:
            present = True
            if planet not in involved:
                involved.append(planet)

    if not involved:
        involved = [Planet.SUN]  # representative

    return YogaResult(
        name="Neechabhanga Raja",
        category="raja",
        involved_planets=involved,
        description="Debilitation cancelled — rise from humble beginnings, unexpected success.",
        is_present=present,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_yogas(chart: BirthChart) -> list[YogaResult]:
    """Detect all classical yogas in a birth chart.

    Runs ~30 yoga checks and returns results for every yoga — including
    those not present (``is_present=False``), so the caller can see the
    full list of what was evaluated.

    Args:
        chart: A fully computed :class:`BirthChart`.

    Returns:
        A list of :class:`YogaResult` objects, one per yoga checked.

    Example:
        >>> from vedic_calc.chart.calculator import calculate_chart
        >>> chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
        >>> yogas = detect_yogas(chart)
        >>> present = [y for y in yogas if y.is_present]
        >>> for y in present:
        ...     print(f"{y.name}: {y.description}")
    """
    return [
        # Pancha Mahapurusha Yogas (5)
        _detect_ruchaka(chart),
        _detect_bhadra(chart),
        _detect_hamsa(chart),
        _detect_malavya(chart),
        _detect_shasha(chart),
        # Jupiter-Moon
        _detect_gajakesari(chart),
        # Sun-Mercury
        _detect_budhaditya(chart),
        # Dhana (wealth) yogas
        _detect_dhana_basic(chart),
        _detect_lakshmi(chart),
        # Raja (power) yogas
        _detect_raja_yoga(chart),
        _detect_viparita_raja(chart),
        # Knowledge
        _detect_saraswati(chart),
        # Negative yogas
        _detect_kemadruma(chart),
        _detect_shakata(chart),
        _detect_daridra(chart),
        # Conjunction yogas
        _detect_chandra_mangal(chart),
        # Benefic placement
        _detect_amala(chart),
        # Lunar yogas (Sunapha / Anapha / Durudhara)
        _detect_sunapha(chart),
        _detect_anapha(chart),
        _detect_durudhara(chart),
        # Solar yogas (Veshi / Voshi / Ubhayachari)
        _detect_veshi(chart),
        _detect_voshi(chart),
        _detect_ubhayachari(chart),
        # Debilitation cancellation
        _detect_neechabhanga_raja(chart),
    ]
