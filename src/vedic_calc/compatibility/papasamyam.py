"""
Papasamyam (malefic balance) compatibility calculator.

PAPASAMYAM:
    Papasamyam ("equal malefics") is a South Indian compatibility check
    that compares the malefic burden in two charts. The idea is that if
    one person has significantly more malefic influence than the other,
    the marriage may face difficulties.

    The check examines malefic planets in specific houses (1, 2, 4, 7, 8, 12)
    counted from three reference points:
    1. Lagna (ascendant)
    2. Moon sign
    3. Venus sign

    Each malefic contributes points based on its strength:
    - Sun: 0.5 (weak malefic)
    - Mars: 1.0
    - Saturn: 1.0
    - Rahu: 1.0
    - Ketu: 0.5 (weak malefic)

    If both charts have similar totals (within 50% of each other, or both
    under 5 points), the match is considered balanced.

SOURCE: South Indian Jyotish compatibility tradition (Dasavidha Porutham).
"""

from __future__ import annotations

from vedic_calc.core.constants import Planet, Sign
from vedic_calc.core.types import BirthChart, PapasamyamChart, PapasamyamResult
from vedic_calc.core.helpers import sign_distance


NATURAL_MALEFICS = {Planet.SUN, Planet.MARS, Planet.SATURN, Planet.RAHU, Planet.KETU}
PAPASAMYAM_HOUSES = {1, 2, 4, 7, 8, 12}  # Houses checked for malefic placement

# Points per malefic: Sun and Ketu are weak malefics (0.5), rest are full (1.0)
_MALEFIC_POINTS: dict[Planet, float] = {
    Planet.SUN: 0.5,
    Planet.MARS: 1.0,
    Planet.SATURN: 1.0,
    Planet.RAHU: 1.0,
    Planet.KETU: 0.5,
}


def _score_from_reference(chart: BirthChart, reference_sign: Sign) -> float:
    """Calculate malefic points from a single reference sign.

    For each malefic planet, check if it falls in houses 1, 2, 4, 7, 8, or 12
    from the reference sign. If so, add the malefic's point value.

    Args:
        chart: The birth chart.
        reference_sign: The sign to count houses from.

    Returns:
        Total malefic points from this reference.
    """
    score = 0.0
    for malefic in NATURAL_MALEFICS:
        malefic_sign = chart.planets[malefic].sign
        house_from_ref = sign_distance(reference_sign, malefic_sign)
        if house_from_ref in PAPASAMYAM_HOUSES:
            score += _MALEFIC_POINTS[malefic]
    return score


def _calculate_papa_points(chart: BirthChart) -> PapasamyamChart:
    """Calculate malefic points from Lagna, Moon, and Venus.

    Args:
        chart: The birth chart.

    Returns:
        PapasamyamChart with scores from each reference and total.
    """
    lagna_sign = chart.ascendant.sign
    moon_sign = chart.planets[Planet.MOON].sign
    venus_sign = chart.planets[Planet.VENUS].sign

    lagna_score = _score_from_reference(chart, lagna_sign)
    moon_score = _score_from_reference(chart, moon_sign)
    venus_score = _score_from_reference(chart, venus_sign)

    total = lagna_score + moon_score + venus_score

    return PapasamyamChart(
        lagna_score=lagna_score,
        moon_score=moon_score,
        venus_score=venus_score,
        total=total,
    )


def calculate_papasamyam(chart1: BirthChart, chart2: BirthChart) -> PapasamyamResult:
    """Compare malefic balance between two charts.

    Two charts are considered balanced if:
    - Both totals are below 5 points, OR
    - The difference between totals is within 50% of the larger total

    Args:
        chart1: First person's birth chart.
        chart2: Second person's birth chart.

    Returns:
        PapasamyamResult with scores, balance assessment, and description.

    Example:
        >>> chart1 = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
        >>> chart2 = calculate_chart(1992, 7, 20, 14, 0, 0, 19.076, 72.878, 5.5)
        >>> result = calculate_papasamyam(chart1, chart2)
        >>> result.is_balanced
        True
    """
    person1 = _calculate_papa_points(chart1)
    person2 = _calculate_papa_points(chart2)

    difference = abs(person1.total - person2.total)
    max_total = max(person1.total, person2.total)

    # Balanced if both totals are low, or within 50% of each other
    if person1.total < 5.0 and person2.total < 5.0:
        is_balanced = True
    elif max_total > 0:
        is_balanced = difference <= (max_total * 0.5)
    else:
        is_balanced = True

    # Build description
    if is_balanced:
        description = (
            f"Papasamyam is balanced. Person 1: {person1.total:.1f} points, "
            f"Person 2: {person2.total:.1f} points (difference: {difference:.1f})."
        )
    else:
        higher = "Person 1" if person1.total > person2.total else "Person 2"
        description = (
            f"Papasamyam is imbalanced. {higher} has significantly more "
            f"malefic influence ({person1.total:.1f} vs {person2.total:.1f}, "
            f"difference: {difference:.1f}). Remedial measures may be advised."
        )

    return PapasamyamResult(
        person1=person1,
        person2=person2,
        is_balanced=is_balanced,
        difference=round(difference, 2),
        description=description,
    )
