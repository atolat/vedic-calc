"""Probabilistic yoga scoring.

Converts binary yoga detection into a 0-100 strength score by weighing
planetary dignity, Shadbala, combustion, retrograde status, and house
placement of the involved planets.
"""

from __future__ import annotations

from vedic_calc.chart.combustion import calculate_combustion
from vedic_calc.core.constants import (
    BENEFICS,
    EXALTATION,
    KENDRA_HOUSES,
    SIGN_LORDS,
    TRIKONA_HOUSES,
    Planet,
)
from vedic_calc.core.helpers import planet_house
from vedic_calc.core.types import BirthChart, ScoredYogaResult, ScoringFactor
from vedic_calc.strength.shadbala import calculate_shadbala
from vedic_calc.yoga.calculator import detect_yogas


# Shadbala totals are in Shashtiamsas (1/60 Rupa).
_SHASHTIAMSA_PER_RUPA = 60.0

# Planets that have Shadbala computed (Sun-Saturn, no nodes).
_SHADBALA_PLANETS = {
    Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
    Planet.JUPITER, Planet.VENUS, Planet.SATURN,
}

# Minimum required Rupas per planet (BPHS). Used to normalise the ratio.
_REQUIRED_RUPAS: dict[Planet, float] = {
    Planet.SUN: 5.0,
    Planet.MOON: 6.0,
    Planet.MARS: 5.0,
    Planet.MERCURY: 7.0,
    Planet.JUPITER: 6.5,
    Planet.VENUS: 5.5,
    Planet.SATURN: 5.0,
}


def _is_own_sign(planet: Planet, sign: "Sign") -> bool:  # noqa: F821
    """True if *planet* is the lord of *sign* (own-sign placement)."""
    return SIGN_LORDS.get(sign) == planet


def _is_exalted(planet: Planet, sign: "Sign") -> bool:  # noqa: F821
    """True if *planet* is in its exaltation sign."""
    ex = EXALTATION.get(planet)
    return ex is not None and ex[0] == sign


def score_yogas(chart: BirthChart) -> list[ScoredYogaResult]:
    """Score every yoga detected in *chart* on a 0-100 strength scale.

    Yogas that are not present receive strength=0 with no scoring factors.
    Present yogas are evaluated using dignity, Shadbala, combustion,
    retrograde status, and house placement of the involved planets.
    """
    yogas = detect_yogas(chart)
    shadbala = calculate_shadbala(chart)
    combustion_list = calculate_combustion(chart)
    combust_planets: set[Planet] = {
        cs.planet for cs in combustion_list if cs.is_combust
    }

    results: list[ScoredYogaResult] = []

    for yoga in yogas:
        if not yoga.is_present:
            results.append(
                ScoredYogaResult(
                    name=yoga.name,
                    category=yoga.category,
                    is_present=False,
                    strength=0.0,
                    factors=[],
                    description=yoga.description,
                )
            )
            continue

        factors: list[ScoringFactor] = []
        score = 50.0

        # --- 1. Base score ---
        factors.append(
            ScoringFactor(name="base", value=0.5, description="Yoga is present")
        )

        # --- 2. Dignity bonus (0-20) ---
        dignity_bonus = 0.0
        for p in yoga.involved_planets:
            p_sign = chart.planets[p].sign
            if _is_exalted(p, p_sign):
                dignity_bonus += 10.0
            elif _is_own_sign(p, p_sign):
                dignity_bonus += 10.0
        dignity_bonus = min(dignity_bonus, 20.0)
        if dignity_bonus > 0:
            score += dignity_bonus
            factors.append(
                ScoringFactor(
                    name="dignity",
                    value=round(dignity_bonus / 100, 2),
                    description=f"+{dignity_bonus:.0f} for exalted/own-sign planets",
                )
            )

        # --- 3. Shadbala bonus (0-15) ---
        sb_planets = [
            p for p in yoga.involved_planets if p in _SHADBALA_PLANETS
        ]
        if sb_planets:
            avg_ratio = 0.0
            for p in sb_planets:
                sb = shadbala.get(p)
                if sb is not None:
                    rupas = sb.total / _SHASHTIAMSA_PER_RUPA
                    req = _REQUIRED_RUPAS.get(p, 5.0)
                    avg_ratio += rupas / req
            avg_ratio /= len(sb_planets)

            if avg_ratio > 1.0:
                # Scale: ratio 1.0 -> 0, ratio 2.0 -> 15 (linear, clamped)
                sb_bonus = min((avg_ratio - 1.0) * 15.0, 15.0)
                score += sb_bonus
                factors.append(
                    ScoringFactor(
                        name="shadbala",
                        value=round(sb_bonus / 100, 2),
                        description=f"+{sb_bonus:.1f} for strong Shadbala (avg ratio {avg_ratio:.2f})",
                    )
                )

        # --- 4. Combustion penalty (-15) ---
        combust_involved = [
            p for p in yoga.involved_planets if p in combust_planets
        ]
        if combust_involved:
            score -= 15.0
            names = ", ".join(p.name.title() for p in combust_involved)
            factors.append(
                ScoringFactor(
                    name="combustion",
                    value=-0.15,
                    description=f"-15 for combust planet(s): {names}",
                )
            )

        # --- 5. Retrograde modifier (-5 to +5) ---
        retro_mod = 0.0
        for p in yoga.involved_planets:
            if chart.planets[p].is_retrograde:
                if p in BENEFICS:
                    retro_mod -= 5.0
                else:
                    retro_mod += 5.0
        if retro_mod != 0.0:
            score += retro_mod
            factors.append(
                ScoringFactor(
                    name="retrograde",
                    value=round(retro_mod / 100, 2),
                    description=f"{retro_mod:+.0f} retrograde modifier",
                )
            )

        # --- 6. House placement bonus (0-10) ---
        kendra_trikona = set(KENDRA_HOUSES) | set(TRIKONA_HOUSES)
        in_kt = any(
            planet_house(chart, p) in kendra_trikona
            for p in yoga.involved_planets
        )
        if in_kt:
            score += 10.0
            factors.append(
                ScoringFactor(
                    name="house_placement",
                    value=0.10,
                    description="+10 for planet(s) in kendra/trikona houses",
                )
            )

        # Clamp to 0-100
        strength = max(0.0, min(100.0, score))

        results.append(
            ScoredYogaResult(
                name=yoga.name,
                category=yoga.category,
                is_present=True,
                strength=round(strength, 1),
                factors=factors,
                description=yoga.description,
            )
        )

    return results
