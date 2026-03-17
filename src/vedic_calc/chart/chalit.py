"""Chalit (Bhava Chalit) chart calculator."""
from __future__ import annotations

from vedic_calc.core.constants import Planet, Sign
from vedic_calc.core.types import BirthChart, ChalitChart, ChalitHouse


def _normalize(deg: float) -> float:
    """Normalize longitude to 0-360."""
    return deg % 360.0


def _is_in_arc(lon: float, start: float, end: float) -> bool:
    """Check if longitude is in the arc from start to end (going forward)."""
    lon = _normalize(lon)
    start = _normalize(start)
    end = _normalize(end)
    if start < end:
        return start <= lon < end
    else:
        return lon >= start or lon < end


def calculate_chalit_chart(chart: BirthChart) -> ChalitChart:
    """Calculate the Chalit (Bhava) chart.

    Uses equal-house cusps based on ascendant degree.
    Bhav Madhya of house N = ascendant_longitude + (N-1)*30°
    Bhav Sandhi between house N and N+1 = midpoint of their Bhav Madhyas = asc + (N-1)*30 + 15°

    Args:
        chart: A birth chart.

    Returns:
        ChalitChart with house cusps and planet placements.
    """
    asc_lon = chart.ascendant.longitude

    houses: list[ChalitHouse] = []
    for i in range(12):
        bhav_madhya = _normalize(asc_lon + i * 30.0)
        sandhi_start = _normalize(bhav_madhya - 15.0)
        sandhi_end = _normalize(bhav_madhya + 15.0)
        sign = Sign(int(bhav_madhya / 30.0) + 1)
        houses.append(ChalitHouse(
            house_number=i + 1,
            bhav_madhya=round(bhav_madhya, 4),
            bhav_sandhi_start=round(sandhi_start, 4),
            bhav_sandhi_end=round(sandhi_end, 4),
            sign=sign,
        ))

    # Place planets in chalit houses
    planet_houses: dict[Planet, int] = {}
    for planet in Planet:
        lon = chart.planets[planet].longitude
        placed = False
        for house in houses:
            if _is_in_arc(lon, house.bhav_sandhi_start, house.bhav_sandhi_end):
                planet_houses[planet] = house.house_number
                placed = True
                break
        if not placed:
            # Fallback to whole-sign house (should not happen with correct logic)
            planet_houses[planet] = 1

    return ChalitChart(houses=houses, planet_houses=planet_houses)
