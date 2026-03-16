"""Tajika yoga detection for Prashna (horary) astrology.

Tajika yogas are degree-based aspect geometries between the lagna lord
and the query house lord. They determine whether a queried matter will
succeed (Ithasala), fail (Easarapha/Induvara), or partially succeed
(Kamboola/Nakta).

Unlike Parashari aspects (sign-based, from GRAHA_DRISHTI), Tajika uses
exact degree orbs — a planet at 15° Aries aspects a planet at 75° Gemini
only if |75 - 15| = 60° is within the sextile orb of ±4°.

Source: Tajika Neelakanthi, Tajika Shastra, Prashna Marga.
"""

from __future__ import annotations

from vedic_calc.core.constants import (
    KENDRA_HOUSES,
    Planet,
    PLANET_SPEED_ORDER,
    SIGN_LORDS,
    TAJIKA_ASPECT_ORBS,
)
from vedic_calc.core.types import BirthChart, TajikaYoga


def _angular_distance(lon1: float, lon2: float) -> float:
    """Minimum angular distance between two longitudes (0-180°)."""
    diff = abs(lon1 - lon2) % 360.0
    return min(diff, 360.0 - diff)


def _is_faster(planet_a: Planet, planet_b: Planet) -> bool:
    """Return True if planet_a is naturally faster than planet_b."""
    return PLANET_SPEED_ORDER[planet_a] < PLANET_SPEED_ORDER[planet_b]


def _has_tajika_aspect(lon1: float, lon2: float) -> str | None:
    """Check if two longitudes form any Tajika aspect within orb.

    Returns the aspect name if within orb, else None.
    """
    dist = _angular_distance(lon1, lon2)
    for name, (exact, orb) in TAJIKA_ASPECT_ORBS.items():
        if abs(dist - exact) <= orb:
            return name
    return None


def _is_applying(
    faster_lon: float,
    slower_lon: float,
    faster_retro: bool,
) -> bool:
    """Check if the faster planet is applying to (moving toward) the slower.

    A direct (non-retrograde) faster planet applies if it is behind the
    slower planet in the zodiac (i.e., its longitude is less, modulo 360).
    A retrograde faster planet applies if it is ahead.

    This is a simplified check — it determines the general direction of
    application based on current positions.
    """
    diff = (slower_lon - faster_lon) % 360.0
    if faster_retro:
        # Retrograde: applying if faster is ahead (diff > 180)
        return diff > 180.0
    else:
        # Direct: applying if faster is behind (diff < 180)
        return diff < 180.0


def _get_house_number(planet: Planet, chart: BirthChart) -> int:
    """Get the house number (1-12) a planet occupies in the chart."""
    planet_sign = chart.planets[planet].sign
    for house in chart.houses:
        if house.sign == planet_sign:
            return house.house_number
    return 1  # fallback


def detect_tajika_yogas(
    chart: BirthChart,
    query_house: int,
) -> list[TajikaYoga]:
    """Detect Tajika yogas between the lagna lord and the query house lord.

    Checks the 5 most critical Tajika yogas:
    1. Ithasala — faster planet applying to slower within orb → favorable
    2. Easarapha — faster separating from slower → unfavorable
    3. Induvara — no applying aspect between significators → fails
    4. Kamboola — Moon applies to significator who aspects query lord → favorable via intermediary
    5. Nakta — heavier planet receives aspect from lighter → partial success with effort

    Args:
        chart: The Prashna chart.
        query_house: The house number relevant to the question (1-12).

    Returns:
        List of TajikaYoga results (all 5, with is_present flag).
    """
    yogas: list[TajikaYoga] = []

    # Identify significators
    lagna_sign = chart.houses[0].sign
    lagna_lord = SIGN_LORDS[lagna_sign]

    query_sign = chart.houses[query_house - 1].sign
    query_lord = SIGN_LORDS[query_sign]

    lagna_lord_pos = chart.planets[lagna_lord]
    query_lord_pos = chart.planets[query_lord]

    lagna_lon = lagna_lord_pos.longitude
    query_lon = query_lord_pos.longitude

    moon_pos = chart.planets[Planet.MOON]
    moon_lon = moon_pos.longitude

    # Determine faster/slower between lagna lord and query lord
    if lagna_lord == query_lord:
        # Same planet rules both houses — special case
        # Check if planet is in kendra from lagna → favorable
        planet_house = _get_house_number(lagna_lord, chart)
        in_kendra = planet_house in KENDRA_HOUSES
        yogas.append(TajikaYoga(
            name="Ithasala",
            is_present=in_kendra,
            involved_planets=[lagna_lord],
            description="Lagna lord and query lord are the same planet"
            + (" in a kendra — matter progresses." if in_kendra
               else " but not in a kendra."),
            significance="favorable" if in_kendra else "mixed",
        ))
        # Fill remaining yogas as not present
        for name, desc, sig in [
            ("Easarapha", "Not applicable — same lord.", "unfavorable"),
            ("Induvara", "Not applicable — same lord.", "unfavorable"),
            ("Kamboola", "Not applicable — same lord.", "favorable"),
            ("Nakta", "Not applicable — same lord.", "mixed"),
        ]:
            yogas.append(TajikaYoga(
                name=name, is_present=False,
                involved_planets=[lagna_lord],
                description=desc, significance=sig,
            ))
        return yogas

    faster = lagna_lord if _is_faster(lagna_lord, query_lord) else query_lord
    slower = query_lord if faster == lagna_lord else lagna_lord
    faster_pos = chart.planets[faster]
    slower_pos = chart.planets[slower]

    aspect = _has_tajika_aspect(faster_pos.longitude, slower_pos.longitude)
    applying = False
    if aspect:
        applying = _is_applying(
            faster_pos.longitude, slower_pos.longitude, faster_pos.is_retrograde,
        )

    # --- 1. Ithasala ---
    ithasala_present = aspect is not None and applying
    yogas.append(TajikaYoga(
        name="Ithasala",
        is_present=ithasala_present,
        involved_planets=[faster, slower],
        description=(
            f"Faster planet ({faster.name}) applies to slower ({slower.name}) "
            f"via {aspect} aspect — matter progresses toward completion."
            if ithasala_present
            else f"No applying aspect between {faster.name} and {slower.name}."
        ),
        significance="favorable" if ithasala_present else "neutral",
    ))

    # --- 2. Easarapha (Ishrafa) ---
    easarapha_present = aspect is not None and not applying
    yogas.append(TajikaYoga(
        name="Easarapha",
        is_present=easarapha_present,
        involved_planets=[faster, slower],
        description=(
            f"Faster planet ({faster.name}) separates from slower ({slower.name}) "
            f"via {aspect} aspect — matter is slipping away."
            if easarapha_present
            else f"No separating aspect between {faster.name} and {slower.name}."
        ),
        significance="unfavorable" if easarapha_present else "neutral",
    ))

    # --- 3. Induvara ---
    induvara_present = aspect is None
    yogas.append(TajikaYoga(
        name="Induvara",
        is_present=induvara_present,
        involved_planets=[lagna_lord, query_lord],
        description=(
            f"No Tajika aspect between {lagna_lord.name} and {query_lord.name} "
            f"— question lacks connection, matter unlikely to materialize."
            if induvara_present
            else f"Aspect exists between {lagna_lord.name} and {query_lord.name}."
        ),
        significance="unfavorable" if induvara_present else "neutral",
    ))

    # --- 4. Kamboola ---
    # Moon applies to one significator who aspects the other
    moon_aspect_lagna = _has_tajika_aspect(moon_lon, lagna_lon)
    moon_aspect_query = _has_tajika_aspect(moon_lon, query_lon)
    moon_applying_lagna = (
        moon_aspect_lagna is not None
        and _is_applying(moon_lon, lagna_lon, moon_pos.is_retrograde)
    )
    moon_applying_query = (
        moon_aspect_query is not None
        and _is_applying(moon_lon, query_lon, moon_pos.is_retrograde)
    )

    kamboola_present = False
    kamboola_desc = "Moon does not connect lagna lord and query lord."
    if moon_applying_lagna and moon_aspect_query:
        kamboola_present = True
        kamboola_desc = (
            f"Moon applies to {lagna_lord.name} and aspects {query_lord.name} "
            f"— matter progresses through an intermediary."
        )
    elif moon_applying_query and moon_aspect_lagna:
        kamboola_present = True
        kamboola_desc = (
            f"Moon applies to {query_lord.name} and aspects {lagna_lord.name} "
            f"— matter progresses through an intermediary."
        )

    yogas.append(TajikaYoga(
        name="Kamboola",
        is_present=kamboola_present,
        involved_planets=[Planet.MOON, lagna_lord, query_lord],
        description=kamboola_desc,
        significance="favorable" if kamboola_present else "neutral",
    ))

    # --- 5. Nakta ---
    # Heavier (slower) planet receives aspect from lighter (faster) planet,
    # but the slower planet does NOT apply back — partial success with effort.
    nakta_present = False
    nakta_desc = "No Nakta yoga detected."
    if aspect is not None:
        # Faster applies to slower, but slower is retrograde or not reciprocating
        slower_applies_back = _is_applying(
            slower_pos.longitude, faster_pos.longitude, slower_pos.is_retrograde,
        )
        if applying and not slower_applies_back:
            nakta_present = True
            nakta_desc = (
                f"Faster {faster.name} applies to slower {slower.name}, "
                f"but {slower.name} does not reciprocate — "
                f"partial success with effort and delays."
            )

    yogas.append(TajikaYoga(
        name="Nakta",
        is_present=nakta_present,
        involved_planets=[faster, slower],
        description=nakta_desc,
        significance="mixed" if nakta_present else "neutral",
    ))

    return yogas
