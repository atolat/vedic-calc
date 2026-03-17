"""Planet functional nature (benefic/malefic/yogakaraka) based on ascendant."""
from __future__ import annotations

from vedic_calc.core.constants import Planet, Sign, SIGN_LORDS
from vedic_calc.core.types import BirthChart, FunctionalNature

_KENDRA = {1, 4, 7, 10}
_TRIKONA = {1, 5, 9}
_DUSTHANA = {6, 8, 12}
_MARAKA = {2, 7}


def calculate_functional_nature(chart: BirthChart) -> list[FunctionalNature]:
    """Classify each planet as yogakaraka/benefic/malefic/neutral based on house lordship.

    Args:
        chart: A birth chart.

    Returns:
        List of FunctionalNature for all 9 planets.
    """
    # Build house-to-sign and planet-to-ruled-houses maps
    house_signs = {h.house_number: h.sign for h in chart.houses}

    results: list[FunctionalNature] = []

    for planet in Planet:
        # Find which houses this planet lords
        ruled_houses: list[int] = []
        for house_num, sign in house_signs.items():
            if SIGN_LORDS.get(sign) == planet:
                ruled_houses.append(house_num)

        ruled_set = set(ruled_houses)

        # Rahu and Ketu don't own signs
        if not ruled_houses:
            results.append(FunctionalNature(
                planet=planet,
                nature="neutral",
                ruled_houses=[],
                description=f"{planet.name} does not lord any house.",
            ))
            continue

        # Classification
        lords_kendra = bool(ruled_set & _KENDRA)
        lords_trikona = bool(ruled_set & _TRIKONA)
        lords_dusthana = bool(ruled_set & _DUSTHANA)
        lords_maraka = bool(ruled_set & _MARAKA)

        if lords_kendra and lords_trikona:
            # Must lord at least one kendra AND at least one trikona
            # But if 1st house is both kendra and trikona, it needs another qualifying house
            kendra_only = ruled_set & (_KENDRA - _TRIKONA)  # houses that are kendra but not trikona
            trikona_only = ruled_set & (_TRIKONA - _KENDRA)  # houses that are trikona but not kendra
            shared = ruled_set & _KENDRA & _TRIKONA  # house 1 is both

            if (kendra_only and trikona_only) or (kendra_only and shared) or (trikona_only and shared):
                nature = "yogakaraka"
            elif lords_trikona:
                nature = "benefic"
            else:
                nature = "neutral"
        elif lords_trikona and not lords_dusthana:
            nature = "benefic"
        elif lords_dusthana:
            nature = "malefic"
        elif lords_maraka and not lords_trikona:
            nature = "malefic"
        elif lords_kendra and not lords_trikona and not lords_dusthana:
            # Pure kendra lords (4,7,10 without trikona) — Kendradhipati dosha
            # They are considered "neutral" per standard texts
            nature = "neutral"
        else:
            nature = "neutral"

        houses_str = ", ".join(str(h) for h in sorted(ruled_houses))
        results.append(FunctionalNature(
            planet=planet,
            nature=nature,
            ruled_houses=sorted(ruled_houses),
            description=f"{planet.name} lords house(s) {houses_str}.",
        ))

    return results
