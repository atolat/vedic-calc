"""Prashna verdict evaluator.

Combines query house lord dignity, Tajika yogas, and chart factors
to produce an overall favorable / unfavorable / mixed verdict.

Source: Prashna Marga, Tajika Neelakanthi.
"""

from __future__ import annotations

from vedic_calc.chart.states import calculate_planet_states
from vedic_calc.core.constants import (
    KENDRA_HOUSES,
    SIGN_LORDS,
    Planet,
)
from vedic_calc.core.types import BirthChart, PrashnaVerdict
from vedic_calc.prashna.tajika import _get_house_number, detect_tajika_yogas


def evaluate_prashna(
    chart: BirthChart,
    query_house: int,
) -> PrashnaVerdict:
    """Evaluate a Prashna chart and produce a verdict.

    Algorithm:
    1. Identify query house lord and its dignity/placement.
    2. Identify lagna lord.
    3. Run Tajika yoga detection.
    4. Score factors:
       - Ithasala between lagna lord and query lord → favorable
       - Induvara (no aspect) → unfavorable
       - Strong query lord (exalted/own_sign/moolatrikona) → favorable
       - Query lord in kendra → favorable
       - Kamboola (Moon intermediary) → favorable
       - Easarapha (separating) → unfavorable
    5. Tally and produce verdict + reasoning.

    Args:
        chart: The Prashna chart.
        query_house: House number for the question (1-12).

    Returns:
        PrashnaVerdict with verdict, yogas, and reasoning.
    """
    states = calculate_planet_states(chart)
    yogas = detect_tajika_yogas(chart, query_house)

    lagna_sign = chart.houses[0].sign
    lagna_lord = SIGN_LORDS[lagna_sign]
    query_sign = chart.houses[query_house - 1].sign
    query_lord = SIGN_LORDS[query_sign]

    query_state = states.get(query_lord)
    lagna_state = states.get(lagna_lord)

    reasoning: list[str] = []
    score = 0  # positive = favorable, negative = unfavorable

    # --- Factor 1: Tajika yogas ---
    yoga_map = {y.name: y for y in yogas}

    if yoga_map["Ithasala"].is_present:
        score += 3
        reasoning.append(
            f"Ithasala yoga present — {yoga_map['Ithasala'].description}"
        )

    if yoga_map["Easarapha"].is_present:
        score -= 2
        reasoning.append(
            f"Easarapha yoga present — {yoga_map['Easarapha'].description}"
        )

    if yoga_map["Induvara"].is_present:
        score -= 3
        reasoning.append(
            f"Induvara yoga present — {yoga_map['Induvara'].description}"
        )

    if yoga_map["Kamboola"].is_present:
        score += 2
        reasoning.append(
            f"Kamboola yoga present — {yoga_map['Kamboola'].description}"
        )

    if yoga_map["Nakta"].is_present:
        score += 1
        reasoning.append(
            f"Nakta yoga present — {yoga_map['Nakta'].description}"
        )

    # --- Factor 2: Query lord dignity ---
    strong_dignities = {"exalted", "moolatrikona", "own_sign"}
    weak_dignities = {"debilitated", "enemy"}

    if query_state:
        if query_state.dignity in strong_dignities:
            score += 2
            reasoning.append(
                f"Query lord {query_lord.name} is {query_state.dignity} — strong."
            )
        elif query_state.dignity in weak_dignities:
            score -= 2
            reasoning.append(
                f"Query lord {query_lord.name} is {query_state.dignity} — weak."
            )
        else:
            reasoning.append(
                f"Query lord {query_lord.name} is in {query_state.dignity} dignity."
            )

        if query_state.is_combust:
            score -= 1
            reasoning.append(
                f"Query lord {query_lord.name} is combust — weakened."
            )

        if query_state.is_retrograde:
            reasoning.append(
                f"Query lord {query_lord.name} is retrograde — delays possible."
            )

    # --- Factor 3: Query lord in kendra ---
    query_lord_house = _get_house_number(query_lord, chart)
    if query_lord_house in KENDRA_HOUSES:
        score += 1
        reasoning.append(
            f"Query lord {query_lord.name} in house {query_lord_house} (kendra) — "
            f"strong angular position."
        )

    # --- Factor 4: Lagna lord strength ---
    if lagna_state:
        if lagna_state.dignity in strong_dignities:
            score += 1
            reasoning.append(
                f"Lagna lord {lagna_lord.name} is {lagna_state.dignity} — "
                f"querent is in a strong position."
            )
        elif lagna_state.dignity in weak_dignities:
            score -= 1
            reasoning.append(
                f"Lagna lord {lagna_lord.name} is {lagna_state.dignity} — "
                f"querent's position is weak."
            )

    # --- Determine verdict ---
    if score >= 2:
        verdict = "favorable"
    elif score <= -2:
        verdict = "unfavorable"
    else:
        verdict = "mixed"

    reasoning.append(f"Overall score: {score} → {verdict}.")

    return PrashnaVerdict(
        chart_time=chart.birth_datetime,
        query_house=query_house,
        query_house_lord=query_lord,
        tajika_yogas=yogas,
        verdict=verdict,
        reasoning=reasoning,
    )
