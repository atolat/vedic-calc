"""Dosha (affliction) detection for Vedic birth charts.

Doshas are problematic planetary configurations that indicate challenges
or obstacles in specific areas of life. Unlike yogas (which can be positive
or negative), doshas are specifically negative and often have well-known
cancellation conditions (dosha bhanga).

This module detects 6 classical doshas:
    1. Manglik Dosha (Kuja Dosha) — Mars affliction affecting marriage
    2. Kaal Sarpa Dosha — All planets hemmed between Rahu-Ketu axis
    3. Pitru Dosha — Affliction to the Sun / 9th house (father/ancestors)
    4. Grahan Dosha — Eclipse-related affliction (luminaries with nodes)
    5. Guru Chandal Dosha — Jupiter conjunct Rahu (weakened wisdom)
    6. Shani Dosha — Saturn near natal Moon (Sade Sati indicator)

Each dosha check returns a DoshaResult with is_present, severity, and any
applicable cancellation factors. detect_doshas() always returns all 6 results,
even when a dosha is not present (is_present=False, severity="none").

Source: Brihat Parashara Hora Shastra, Phaladeepika, Jataka Parijata.
"""

from __future__ import annotations

from vedic_calc.core.constants import KENDRA_HOUSES, Planet, Sign, SIGN_LORDS
from vedic_calc.core.helpers import planet_house as _planet_house, sign_distance as _sign_distance
from vedic_calc.core.types import BirthChart, DoshaResult


def _is_in_same_sign(chart: BirthChart, planet1: Planet, planet2: Planet) -> bool:
    """Check whether two planets occupy the same sign."""
    return chart.planets[planet1].sign == chart.planets[planet2].sign


# ---------------------------------------------------------------------------
# 1. Manglik Dosha (Kuja Dosha)
# ---------------------------------------------------------------------------

_MANGLIK_HOUSES = {1, 2, 4, 7, 8, 12}

# Mars has special drishti (aspects) on the 4th, 7th, and 8th houses
# from its position. These aspects effectively extend Mars's influence
# into those houses, so we must check if any aspected house falls in
# a manglik house from each reference point.
_MARS_ASPECT_OFFSETS = (4, 7, 8)


def _detect_manglik(chart: BirthChart) -> DoshaResult:
    """Detect Manglik Dosha (Kuja Dosha).

    Mars in houses 1, 2, 4, 7, 8, or 12 from lagna, Moon, or Venus
    causes Manglik Dosha. Mars's special aspects (4th, 7th, 8th drishti)
    are also considered — if Mars aspects any of these houses from a
    reference point, it counts as affliction (per BPHS Ch. 81 and
    widely-used practitioner conventions).

    Severity depends on how many reference points are afflicted.
    Several classical cancellation conditions are checked.
    """
    mars_sign = chart.planets[Planet.MARS].sign

    # Reference signs: lagna, Moon, Venus
    ref_signs = {
        "Lagna": chart.ascendant.sign,
        "Moon": chart.planets[Planet.MOON].sign,
        "Venus": chart.planets[Planet.VENUS].sign,
    }

    afflicted_refs: list[str] = []
    for ref_name, ref_sign in ref_signs.items():
        house_from_ref = _sign_distance(ref_sign, mars_sign)

        # Direct placement: Mars sits in a manglik house from this reference
        if house_from_ref in _MANGLIK_HOUSES:
            afflicted_refs.append(ref_name)
            continue

        # Aspect-based: Mars's special drishti (4th, 7th, 8th) may land
        # on a manglik house from this reference point. We compute the
        # house number (from the reference) that each Mars aspect hits.
        for offset in _MARS_ASPECT_OFFSETS:
            aspected_house = (house_from_ref + offset - 1) % 12 + 1
            if aspected_house in _MANGLIK_HOUSES:
                afflicted_refs.append(f"{ref_name} (aspect)")
                break

    is_present = len(afflicted_refs) > 0

    if len(afflicted_refs) >= 2:
        severity = "severe"
    elif len(afflicted_refs) == 1:
        severity = "moderate"
    else:
        severity = "none"

    # Cancellation factors
    cancellation: list[str] = []
    if is_present:
        # 1. Mars in own sign (Aries, Scorpio) or exalted (Capricorn)
        if mars_sign in (Sign.ARIES, Sign.SCORPIO, Sign.CAPRICORN):
            cancellation.append("Mars in own/exalted sign reduces severity")

        # 2. Jupiter aspects Mars (Mars in 5th, 7th, or 9th from Jupiter)
        jupiter_sign = chart.planets[Planet.JUPITER].sign
        dist_from_jupiter = _sign_distance(jupiter_sign, mars_sign)
        if dist_from_jupiter in (5, 7, 9):
            cancellation.append("Jupiter aspects Mars")

        # 3. Mars in kendra from Jupiter
        if dist_from_jupiter in (1, 4, 7, 10):
            cancellation.append("Mars in kendra from Jupiter")

        # 4. Venus-Mars conjunction
        if _is_in_same_sign(chart, Planet.VENUS, Planet.MARS):
            cancellation.append("Venus-Mars conjunction can cancel dosha")

    refs_str = ", ".join(afflicted_refs) if afflicted_refs else "none"
    description = (
        f"Manglik Dosha: Mars afflicts marriage houses from {refs_str}."
        if is_present
        else "Manglik Dosha not present."
    )

    return DoshaResult(
        name="Manglik Dosha",
        is_present=is_present,
        severity=severity,
        cancellation_factors=cancellation,
        description=description,
    )


# ---------------------------------------------------------------------------
# 2. Kaal Sarpa Dosha
# ---------------------------------------------------------------------------

def _is_between_clockwise(point: float, start: float, end: float) -> bool:
    """Check if a point is in the arc from start to end going clockwise.

    All values are longitudes in degrees (0-360).
    """
    if start < end:
        return start < point < end
    else:
        # Arc wraps around 360°
        return point > start or point < end


def _detect_kaal_sarpa(chart: BirthChart) -> DoshaResult:
    """Detect Kaal Sarpa Dosha.

    All 7 classical planets (Sun through Saturn) must lie on one side
    of the Rahu-Ketu axis for Kalsarpa to be present.

    Two-tier detection (matching the most widely-used industry definition):

    1. **Full Kalsarpa**: All 7 planets are strictly between Rahu and Ketu
       by degree (no planet conjunct a node). Severity = "severe".

    2. **Partial Kalsarpa**: Planets in the same sign as Rahu or Ketu are
       treated as "on the axis" (they are effectively conjunct a node by
       sign). If all remaining non-axis planets fall on one side of the
       nodal axis, it is a Partial Kalsarpa. Severity = "moderate".
       This matches the common commercial software interpretation where
       planetary conjunction with a node doesn't break the yoga.

    Note: Kalsarpa Dosha is NOT found in BPHS or any classical text.
    It is a later tradition with varying definitions across sources.
    """
    rahu_lon = chart.planets[Planet.RAHU].longitude
    ketu_lon = chart.planets[Planet.KETU].longitude
    rahu_sign = chart.planets[Planet.RAHU].sign
    ketu_sign = chart.planets[Planet.KETU].sign

    classical_planets = [
        Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
        Planet.JUPITER, Planet.VENUS, Planet.SATURN,
    ]

    # ------------------------------------------------------------------
    # Tier 1: Strict degree-based check (Full Kalsarpa)
    # ------------------------------------------------------------------
    in_rahu_ketu_arc = 0
    in_ketu_rahu_arc = 0

    for planet in classical_planets:
        lon = chart.planets[planet].longitude
        if _is_between_clockwise(lon, rahu_lon, ketu_lon):
            in_rahu_ketu_arc += 1
        else:
            in_ketu_rahu_arc += 1

    full = (in_rahu_ketu_arc == 7) or (in_ketu_rahu_arc == 7)

    # ------------------------------------------------------------------
    # Tier 2: Sign-based axis exclusion (Partial Kalsarpa)
    # Planets in the same sign as Rahu or Ketu are treated as "on the
    # axis" — they are conjunct a node by sign and don't break the
    # hemming pattern. If all remaining non-axis planets fall on one
    # side, it is a Partial Kalsarpa.
    # ------------------------------------------------------------------
    partial = False
    on_axis = 0
    side_rk = 0
    side_kr = 0

    if not full:
        for planet in classical_planets:
            lon = chart.planets[planet].longitude
            p_sign = chart.planets[planet].sign

            if p_sign == rahu_sign or p_sign == ketu_sign:
                on_axis += 1
            elif _is_between_clockwise(lon, rahu_lon, ketu_lon):
                side_rk += 1
            else:
                side_kr += 1

        partial = (
            on_axis > 0
            and (side_rk == 0 or side_kr == 0)
        )

    is_present = full or partial

    if full:
        severity = "severe"
        variant = "Full"
    elif partial:
        severity = "moderate"
        variant = "Partial"
    else:
        severity = "none"
        variant = ""

    # Cancellation factors
    cancellation: list[str] = []
    if is_present:
        # 1. Jupiter in kendra
        jupiter_house = _planet_house(chart, Planet.JUPITER)
        if jupiter_house in KENDRA_HOUSES:
            cancellation.append("Jupiter in kendra mitigates")

        # 2. Any planet conjunct Rahu or Ketu (within 5 degrees or same sign)
        if on_axis > 0 or any(
            min(abs(chart.planets[p].longitude - rahu_lon),
                360 - abs(chart.planets[p].longitude - rahu_lon)) <= 5.0
            or min(abs(chart.planets[p].longitude - ketu_lon),
                   360 - abs(chart.planets[p].longitude - ketu_lon)) <= 5.0
            for p in classical_planets
        ):
            cancellation.append("Planet conjunct node weakens the dosha")

    description = (
        f"{variant} Kaal Sarpa Dosha: all planets hemmed between Rahu-Ketu axis."
        if is_present
        else "Kaal Sarpa Dosha not present."
    )

    return DoshaResult(
        name="Kaal Sarpa Dosha",
        is_present=is_present,
        severity=severity,
        cancellation_factors=cancellation,
        description=description,
    )


# ---------------------------------------------------------------------------
# 3. Pitru Dosha
# ---------------------------------------------------------------------------

def _detect_pitru(chart: BirthChart) -> DoshaResult:
    """Detect Pitru Dosha (affliction to father/ancestors).

    Conditions (any one triggers the dosha):
        - Sun conjunct Rahu or Ketu (same sign)
        - Sun in the 9th house
        - Lord of the 9th house conjunct Rahu or Ketu
        - Sun and Saturn conjunct (same sign)
    """
    conditions_met: list[str] = []

    # 1. Sun conjunct Rahu or Ketu
    if _is_in_same_sign(chart, Planet.SUN, Planet.RAHU):
        conditions_met.append("Sun conjunct Rahu")
    if _is_in_same_sign(chart, Planet.SUN, Planet.KETU):
        conditions_met.append("Sun conjunct Ketu")

    # 2. Sun in the 9th house
    sun_house = _planet_house(chart, Planet.SUN)
    if sun_house == 9:
        conditions_met.append("Sun in 9th house")

    # 3. Lord of 9th house conjunct Rahu or Ketu
    ninth_house_sign = chart.houses[8].sign  # 0-indexed
    ninth_lord = SIGN_LORDS[ninth_house_sign]
    if _is_in_same_sign(chart, ninth_lord, Planet.RAHU):
        conditions_met.append("9th lord conjunct Rahu")
    if _is_in_same_sign(chart, ninth_lord, Planet.KETU):
        conditions_met.append("9th lord conjunct Ketu")

    # 4. Sun and Saturn conjunct
    if _is_in_same_sign(chart, Planet.SUN, Planet.SATURN):
        conditions_met.append("Sun-Saturn conjunction")

    is_present = len(conditions_met) > 0

    if len(conditions_met) >= 2:
        severity = "severe"
    elif len(conditions_met) == 1:
        severity = "moderate"
    else:
        severity = "none"

    description = (
        f"Pitru Dosha: {'; '.join(conditions_met)}."
        if is_present
        else "Pitru Dosha not present."
    )

    return DoshaResult(
        name="Pitru Dosha",
        is_present=is_present,
        severity=severity,
        cancellation_factors=[],
        description=description,
    )


# ---------------------------------------------------------------------------
# 4. Grahan Dosha
# ---------------------------------------------------------------------------

def _detect_grahan(chart: BirthChart) -> DoshaResult:
    """Detect Grahan Dosha (eclipse affliction).

    Sun or Moon in the same sign as Rahu or Ketu indicates an
    eclipse-related affliction. Severity is "severe" if both
    luminaries are affected, "moderate" if only one.
    """
    afflictions: list[str] = []

    # Sun with nodes
    if _is_in_same_sign(chart, Planet.SUN, Planet.RAHU):
        afflictions.append("Surya Grahan Dosha (Sun-Rahu)")
    if _is_in_same_sign(chart, Planet.SUN, Planet.KETU):
        afflictions.append("Surya Grahan Dosha (Sun-Ketu)")

    # Moon with nodes
    if _is_in_same_sign(chart, Planet.MOON, Planet.RAHU):
        afflictions.append("Chandra Grahan Dosha (Moon-Rahu)")
    if _is_in_same_sign(chart, Planet.MOON, Planet.KETU):
        afflictions.append("Chandra Grahan Dosha (Moon-Ketu)")

    is_present = len(afflictions) > 0

    # Check if both luminaries affected
    sun_affected = any("Surya" in a for a in afflictions)
    moon_affected = any("Chandra" in a for a in afflictions)

    if sun_affected and moon_affected:
        severity = "severe"
    elif is_present:
        severity = "moderate"
    else:
        severity = "none"

    description = (
        f"Grahan Dosha: {'; '.join(afflictions)}."
        if is_present
        else "Grahan Dosha not present."
    )

    return DoshaResult(
        name="Grahan Dosha",
        is_present=is_present,
        severity=severity,
        cancellation_factors=[],
        description=description,
    )


# ---------------------------------------------------------------------------
# 5. Guru Chandal Dosha
# ---------------------------------------------------------------------------

def _detect_guru_chandal(chart: BirthChart) -> DoshaResult:
    """Detect Guru Chandal Dosha (Jupiter conjunct Rahu).

    Jupiter and Rahu in the same sign weakens Jupiter's benefic
    effects. Severity is always "moderate" when present. Cancellation
    applies if Jupiter is in own sign (Sagittarius, Pisces) or
    exalted (Cancer).
    """
    is_present = _is_in_same_sign(chart, Planet.JUPITER, Planet.RAHU)

    cancellation: list[str] = []
    if is_present:
        jupiter_sign = chart.planets[Planet.JUPITER].sign
        if jupiter_sign in (Sign.SAGITTARIUS, Sign.PISCES):
            cancellation.append("Jupiter in own sign")
        if jupiter_sign == Sign.CANCER:
            cancellation.append("Jupiter is exalted")

    return DoshaResult(
        name="Guru Chandal Dosha",
        is_present=is_present,
        severity="moderate" if is_present else "none",
        cancellation_factors=cancellation,
        description=(
            "Guru Chandal Dosha: Jupiter conjunct Rahu weakens Jupiter's beneficence."
            if is_present
            else "Guru Chandal Dosha not present."
        ),
    )


# ---------------------------------------------------------------------------
# 6. Shani Dosha (Sade Sati natal indicator)
# ---------------------------------------------------------------------------

def _detect_shani(chart: BirthChart) -> DoshaResult:
    """Detect Shani Dosha (natal Sade Sati indicator).

    Saturn in the 12th, 1st, or 2nd house from the Moon's sign at birth.
    This is primarily a transit phenomenon, but its presence in the natal
    chart is noted as a mild indicator.
    """
    moon_sign = chart.planets[Planet.MOON].sign
    saturn_sign = chart.planets[Planet.SATURN].sign

    dist = _sign_distance(moon_sign, saturn_sign)
    # 12th, 1st (same sign), or 2nd from Moon
    is_present = dist in (1, 2, 12)

    position_map = {1: "same sign as", 2: "2nd from", 12: "12th from"}

    return DoshaResult(
        name="Shani Dosha",
        is_present=is_present,
        severity="mild" if is_present else "none",
        cancellation_factors=[],
        description=(
            f"Shani Dosha: Saturn {position_map.get(dist, '')} Moon (natal Sade Sati indicator)."
            if is_present
            else "Shani Dosha not present."
        ),
    )


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------

def detect_doshas(chart: BirthChart) -> list[DoshaResult]:
    """Detect all classical doshas in a birth chart.

    Checks for 6 doshas: Manglik, Kaal Sarpa, Pitru, Grahan,
    Guru Chandal, and Shani. Always returns all 6 results — doshas
    not present will have is_present=False and severity="none".

    Args:
        chart: A complete birth chart with planet positions and houses.

    Returns:
        List of 6 DoshaResult objects, one for each dosha.

    Example:
        >>> from vedic_calc.chart.calculator import calculate_chart
        >>> chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
        >>> doshas = detect_doshas(chart)
        >>> for d in doshas:
        ...     if d.is_present:
        ...         print(f"{d.name}: {d.severity}")
    """
    return [
        _detect_manglik(chart),
        _detect_kaal_sarpa(chart),
        _detect_pitru(chart),
        _detect_grahan(chart),
        _detect_guru_chandal(chart),
        _detect_shani(chart),
    ]
