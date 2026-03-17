"""Probabilistic dosha scoring.

Converts categorical dosha severity (none/mild/moderate/severe) into a
0-100 numeric score, refined by cancellation factors, Shadbala of the
afflicting planets, and house placement.
"""

from __future__ import annotations

from vedic_calc.core.constants import KENDRA_HOUSES, Planet
from vedic_calc.core.helpers import planet_house
from vedic_calc.core.types import BirthChart, ScoredDoshaResult, ScoringFactor
from vedic_calc.dosha.calculator import detect_doshas
from vedic_calc.strength.shadbala import calculate_shadbala


# Shadbala totals are in Shashtiamsas (1/60 Rupa).
_SHASHTIAMSA_PER_RUPA = 60.0

# Required Rupas per planet (BPHS).
_REQUIRED_RUPAS: dict[Planet, float] = {
    Planet.SUN: 5.0,
    Planet.MOON: 6.0,
    Planet.MARS: 5.0,
    Planet.MERCURY: 7.0,
    Planet.JUPITER: 6.5,
    Planet.VENUS: 5.5,
    Planet.SATURN: 5.0,
}

_SEVERITY_BASE: dict[str, float] = {
    "none": 0.0,
    "mild": 25.0,
    "moderate": 50.0,
    "severe": 75.0,
}

# Map dosha names to their primary afflicting planets.
# These are the planets whose strength and placement matter for scoring.
_DOSHA_PLANETS: dict[str, list[Planet]] = {
    "Manglik": [Planet.MARS],
    "Kaal Sarpa": [Planet.RAHU, Planet.KETU],
    "Pitru": [Planet.SUN],
    "Grahan": [Planet.RAHU, Planet.KETU],
    "Guru Chandal": [Planet.JUPITER, Planet.RAHU],
    "Shani": [Planet.SATURN],
}

# Planets with Shadbala computed (Sun-Saturn, excludes nodes).
_SHADBALA_PLANETS = {
    Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
    Planet.JUPITER, Planet.VENUS, Planet.SATURN,
}


def score_doshas(chart: BirthChart) -> list[ScoredDoshaResult]:
    """Score every dosha detected in *chart* on a 0-100 severity scale.

    Doshas that are not present receive severity_score=0.  Present doshas
    start from a base determined by their categorical severity, then get
    adjustments for cancellation factors, afflicting-planet Shadbala, and
    house placement.
    """
    doshas = detect_doshas(chart)
    shadbala = calculate_shadbala(chart)

    results: list[ScoredDoshaResult] = []

    for dosha in doshas:
        if not dosha.is_present:
            results.append(
                ScoredDoshaResult(
                    name=dosha.name,
                    is_present=False,
                    severity_score=0.0,
                    factors=[],
                    description=dosha.description,
                )
            )
            continue

        factors: list[ScoringFactor] = []
        base = _SEVERITY_BASE.get(dosha.severity, 50.0)
        score = base

        factors.append(
            ScoringFactor(
                name="base_severity",
                value=round(base / 100, 2),
                description=f"Base {base:.0f} for '{dosha.severity}' severity",
            )
        )

        # --- Cancellation relief (-15 per factor) ---
        if dosha.cancellation_factors:
            relief = -15.0 * len(dosha.cancellation_factors)
            score += relief
            factors.append(
                ScoringFactor(
                    name="cancellation",
                    value=round(relief / 100, 2),
                    description=(
                        f"{relief:.0f} cancellation relief "
                        f"({len(dosha.cancellation_factors)} factor(s))"
                    ),
                )
            )

        # --- Shadbala of afflicting planets ---
        afflicting = _DOSHA_PLANETS.get(dosha.name, [])
        sb_planets = [p for p in afflicting if p in _SHADBALA_PLANETS]
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
                # Strong malefics make doshas worse: up to +15
                sb_penalty = min((avg_ratio - 1.0) * 15.0, 15.0)
                score += sb_penalty
                factors.append(
                    ScoringFactor(
                        name="shadbala",
                        value=round(sb_penalty / 100, 2),
                        description=(
                            f"+{sb_penalty:.1f} for strong afflicting planet(s) "
                            f"(avg ratio {avg_ratio:.2f})"
                        ),
                    )
                )

        # --- House placement of afflicting planets ---
        kendra_set = set(KENDRA_HOUSES)
        in_kendra = any(
            planet_house(chart, p) in kendra_set for p in afflicting
        )
        if in_kendra:
            score += 10.0
            factors.append(
                ScoringFactor(
                    name="house_placement",
                    value=0.10,
                    description="+10 for afflicting planet in kendra house",
                )
            )

        # Clamp to 0-100
        severity_score = max(0.0, min(100.0, score))

        results.append(
            ScoredDoshaResult(
                name=dosha.name,
                is_present=True,
                severity_score=round(severity_score, 1),
                factors=factors,
                description=dosha.description,
            )
        )

    return results
