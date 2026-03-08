"""
Kundali (birth chart) visual renderer.

Generates visual representations of a Vedic birth chart in three formats:
1. North Indian style (diamond pattern) — ASCII art
2. South Indian style (grid pattern) — ASCII art
3. SVG — vector graphics for web/mobile display

NORTH INDIAN vs SOUTH INDIAN CHART STYLES:

    NORTH INDIAN (used in UP, Delhi, Rajasthan, etc.):
        - Diamond-shaped layout with houses arranged around the center
        - The ASCENDANT is always at the top (house positions are fixed)
        - Signs rotate based on the chart — you need to read the sign
          numbers inside each house
        - Houses are numbered counter-clockwise from the top

    SOUTH INDIAN (used in Tamil Nadu, Karnataka, Kerala, etc.):
        - Grid layout (4 × 4 with center empty)
        - SIGNS are always in fixed positions (Pisces top-left, Aries next, etc.)
        - Houses rotate based on the ascendant
        - You look for the "Asc" label to find the 1st house

    Both show the same information — just different visual conventions.

WHAT'S SHOWN IN EACH CELL:
    - The sign abbreviation (Ar, Ta, Ge, etc.)
    - Planet abbreviations placed in their respective houses
    - "Asc" marker for the ascendant house
    - "(R)" suffix for retrograde planets

NO EXTERNAL DEPENDENCIES — just string building for ASCII, and string
concatenation for SVG.
"""

from __future__ import annotations

from vedic_calc.core.constants import (
    Planet,
    Sign,
    PLANET_ABBREVIATIONS,
    SIGN_ABBREVIATIONS,
)
from vedic_calc.core.types import BirthChart


def _planets_in_sign(chart: BirthChart, sign: Sign) -> list[str]:
    """Get abbreviations of all planets in a given sign.

    Checks each of the 9 planets and returns the abbreviated names of
    those whose sign matches the given sign. Retrograde planets get
    a "(R)" suffix.

    Example:
        If Moon and Venus are in Taurus, returns ["Mo", "Ve"].
        If Saturn (retrograde) is in Aquarius, returns ["Sa(R)"].
    """
    result = []
    for planet_enum, pos in chart.planets.items():
        if pos.sign == sign:
            abbr = PLANET_ABBREVIATIONS[planet_enum]
            if pos.is_retrograde and planet_enum not in (Planet.RAHU, Planet.KETU):
                # Rahu/Ketu are always retrograde — don't clutter with (R)
                abbr += "(R)"
            result.append(abbr)
    return result


def _format_cell(sign: Sign, planets: list[str], is_ascendant: bool, width: int = 12) -> list[str]:
    """Format a single house cell for the grid/diamond layout.

    Returns a list of strings (lines) for one cell, showing:
    - Sign abbreviation + "Asc" if ascendant
    - Planets in that house

    Args:
        sign: The zodiac sign in this house.
        planets: List of planet abbreviation strings.
        is_ascendant: Whether this is the ascendant house.
        width: Character width of the cell.

    Returns:
        List of 3 strings, each `width` characters wide.
    """
    sign_abbr = SIGN_ABBREVIATIONS[sign]
    line1 = f"{sign_abbr}" + (" Asc" if is_ascendant else "")
    line2 = " ".join(planets) if planets else ""

    return [
        line1.center(width),
        line2.center(width),
        "".center(width),
    ]


def render_south_indian(chart: BirthChart) -> str:
    """Render a South Indian style chart as ASCII art.

    SOUTH INDIAN LAYOUT:
        Signs are in FIXED positions in a 4×4 grid (center 2×2 empty):

        ┌──────┬──────┬──────┬──────┐
        │  Pi  │  Ar  │  Ta  │  Ge  │
        ├──────┼──────┴──────┼──────┤
        │  Aq  │             │  Cn  │
        │      │   (center)  │      │
        │  Cp  │             │  Le  │
        ├──────┼──────┬──────┼──────┤
        │  Sg  │  Sc  │  Li  │  Vi  │
        └──────┴──────┴──────┴──────┘

        The 12 signs go clockwise from Pisces (top-left corner).

    Planets are placed in their respective sign positions.
    The ascendant's sign is marked with "Asc".

    Args:
        chart: A calculated BirthChart.

    Returns:
        Multi-line string with the ASCII chart.
    """
    asc_sign = chart.ascendant.sign

    # South Indian: fixed sign positions in reading order
    # Row 0: Pi, Ar, Ta, Ge
    # Row 1: Aq, (empty), (empty), Cn
    # Row 2: Cp, (empty), (empty), Le
    # Row 3: Sg, Sc, Li, Vi
    grid_signs = [
        [Sign.PISCES, Sign.ARIES, Sign.TAURUS, Sign.GEMINI],
        [Sign.AQUARIUS, None, None, Sign.CANCER],
        [Sign.CAPRICORN, None, None, Sign.LEO],
        [Sign.SAGITTARIUS, Sign.SCORPIO, Sign.LIBRA, Sign.VIRGO],
    ]

    cell_w = 14
    h_line = "+" + (("-" * cell_w + "+") * 4)

    lines = [h_line]
    for row_idx, row in enumerate(grid_signs):
        cell_lines = [[], [], []]
        for col_idx, sign in enumerate(row):
            if sign is None:
                # Center cells — empty
                if row_idx == 1 and col_idx == 1:
                    cell_lines[0].append("  Birth Chart ".center(cell_w))
                    cell_lines[1].append("".center(cell_w))
                    cell_lines[2].append("".center(cell_w))
                elif row_idx == 1 and col_idx == 2:
                    cell_lines[0].append("".center(cell_w))
                    cell_lines[1].append("".center(cell_w))
                    cell_lines[2].append("".center(cell_w))
                elif row_idx == 2 and col_idx == 1:
                    dt = chart.birth_datetime
                    date_str = dt.strftime("%Y-%m-%d")
                    cell_lines[0].append(date_str.center(cell_w))
                    cell_lines[1].append("".center(cell_w))
                    cell_lines[2].append("".center(cell_w))
                else:
                    for i in range(3):
                        cell_lines[i].append("".center(cell_w))
            else:
                planets = _planets_in_sign(chart, sign)
                is_asc = (sign == asc_sign)
                cell = _format_cell(sign, planets, is_asc, cell_w)
                for i in range(3):
                    cell_lines[i].append(cell[i])

        for cl in cell_lines:
            lines.append("|" + "|".join(cl) + "|")
        lines.append(h_line)

    return "\n".join(lines)


def render_north_indian(chart: BirthChart) -> str:
    """Render a North Indian style chart as ASCII art.

    NORTH INDIAN LAYOUT:
        Houses are in fixed positions; signs rotate based on the ascendant.
        The ascendant (1st house) is always at the top center.

        Layout with house numbers:

            ┌────────────────────────────┐
            │         ╱ H1  ╲            │
            │  H12  ╱        ╲  H2       │
            │     ╱            ╲         │
            ├───╱    ╱────╲     ╲────────┤
            │  H11 ╱  H10  ╲  H3        │
            │     ╱          ╲           │
            │    ╱            ╲          │
            │   ╲              ╱         │
            │    ╲            ╱          │
            │  H9 ╲   H4    ╱  H5       │
            ├──────╲ ╱────╲ ╱────────────┤
            │  H8   ╲      ╱   H6       │
            │        ╲ H7 ╱             │
            └─────────╲  ╱──────────────┘

    For simplicity in ASCII, we use a grid approximation where houses
    are arranged in a readable layout.

    Args:
        chart: A calculated BirthChart.

    Returns:
        Multi-line string with the ASCII chart.
    """
    # Get signs for each house (1-12)
    house_signs = {h.house_number: h.sign for h in chart.houses}

    def _house_content(house_num: int) -> tuple[str, str]:
        """Return (sign_label, planets_label) for a house."""
        sign = house_signs[house_num]
        sign_abbr = SIGN_ABBREVIATIONS[sign]
        label = f"H{house_num}:{sign_abbr}"
        if house_num == 1:
            label += "*"  # Mark ascendant
        planets = _planets_in_sign(chart, sign)
        planet_str = " ".join(planets) if planets else ""
        return label, planet_str

    # Build a 3×4 grid approximation of the North Indian diamond:
    #
    #   [H12]  [ H1 ]  [ H2 ]
    #   [H11]  [    ]  [ H3 ]
    #   [H10]  [    ]  [ H4 ]
    #   [ H9]  [ H8 ]  [ H7 ]  [ H6 ]  [ H5 ]
    #
    # Actually, a better visual is to map 12 houses into a diamond-like grid.
    # We'll use a 4-row layout:
    #
    #   Row 0:  H12  |  H1   |  H2   |  H3
    #   Row 1:  H11  |       center  |  H4
    #   Row 2:  H10  |       center  |  H5
    #   Row 3:  H9   |  H8   |  H7   |  H6

    grid_houses = [
        [12, 1, 2, 3],
        [11, 0, 0, 4],  # 0 = center
        [10, 0, 0, 5],
        [9, 8, 7, 6],
    ]

    cell_w = 14
    h_line = "+" + (("-" * cell_w + "+") * 4)

    lines = [h_line]
    for row_idx, row in enumerate(grid_houses):
        cell_lines = [[], [], []]
        for col_idx, house_num in enumerate(row):
            if house_num == 0:
                # Center cells
                if row_idx == 1 and col_idx == 1:
                    cell_lines[0].append("  North Indian".center(cell_w))
                    cell_lines[1].append("".center(cell_w))
                    cell_lines[2].append("".center(cell_w))
                elif row_idx == 1 and col_idx == 2:
                    cell_lines[0].append("".center(cell_w))
                    cell_lines[1].append("".center(cell_w))
                    cell_lines[2].append("".center(cell_w))
                elif row_idx == 2 and col_idx == 1:
                    dt = chart.birth_datetime
                    cell_lines[0].append(dt.strftime("%Y-%m-%d").center(cell_w))
                    cell_lines[1].append("".center(cell_w))
                    cell_lines[2].append("".center(cell_w))
                else:
                    for i in range(3):
                        cell_lines[i].append("".center(cell_w))
            else:
                label, planet_str = _house_content(house_num)
                cell_lines[0].append(label.center(cell_w))
                cell_lines[1].append(planet_str.center(cell_w))
                cell_lines[2].append("".center(cell_w))

        for cl in cell_lines:
            lines.append("|" + "|".join(cl) + "|")
        lines.append(h_line)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# SVG Renderer
# ---------------------------------------------------------------------------

# South Indian grid layout: fixed sign positions
# Each tuple is (row, col) in a 4×4 grid where center 2×2 is empty
_SI_SIGN_POSITIONS: dict[Sign, tuple[int, int]] = {
    Sign.PISCES: (0, 0),
    Sign.ARIES: (0, 1),
    Sign.TAURUS: (0, 2),
    Sign.GEMINI: (0, 3),
    Sign.AQUARIUS: (1, 0),
    Sign.CANCER: (1, 3),
    Sign.CAPRICORN: (2, 0),
    Sign.LEO: (2, 3),
    Sign.SAGITTARIUS: (3, 0),
    Sign.SCORPIO: (3, 1),
    Sign.LIBRA: (3, 2),
    Sign.VIRGO: (3, 3),
}


def render_svg(chart: BirthChart, style: str = "south") -> str:
    """Render a birth chart as an SVG string.

    Generates a self-contained SVG that can be:
    - Embedded directly in HTML (<div>{svg_string}</div>)
    - Saved as a .svg file
    - Displayed in Jupyter notebooks

    No external dependencies — pure string concatenation.

    Args:
        chart: A calculated BirthChart.
        style: "south" for South Indian grid, "north" for North Indian.

    Returns:
        Complete SVG string (starts with <svg, ends with </svg>).

    Example:
        >>> chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
        >>> svg = render_svg(chart, style="south")
        >>> svg.startswith("<svg")
        True
    """
    if style == "north":
        return _render_svg_north(chart)
    return _render_svg_south(chart)


def _render_svg_south(chart: BirthChart) -> str:
    """Generate South Indian style SVG."""
    cell = 100  # pixels per cell
    size = cell * 4  # 400×400

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'width="{size}" height="{size}" style="font-family:monospace;font-size:12px">',
        f'<rect width="{size}" height="{size}" fill="white" stroke="black" stroke-width="2"/>',
    ]

    # Draw grid lines
    for i in range(1, 4):
        parts.append(f'<line x1="{i*cell}" y1="0" x2="{i*cell}" y2="{size}" stroke="black" stroke-width="1"/>')
        parts.append(f'<line x1="0" y1="{i*cell}" x2="{size}" y2="{i*cell}" stroke="black" stroke-width="1"/>')

    # Clear center (draw white rect over center 2×2)
    parts.append(f'<rect x="{cell}" y="{cell}" width="{cell*2}" height="{cell*2}" fill="white" stroke="black" stroke-width="1"/>')

    # Center text
    parts.append(f'<text x="{size//2}" y="{size//2 - 10}" text-anchor="middle" font-size="14" font-weight="bold">Birth Chart</text>')
    dt_str = chart.birth_datetime.strftime("%Y-%m-%d %H:%M")
    parts.append(f'<text x="{size//2}" y="{size//2 + 10}" text-anchor="middle" font-size="11">{dt_str}</text>')

    asc_sign = chart.ascendant.sign

    # Draw sign cells
    for sign, (row, col) in _SI_SIGN_POSITIONS.items():
        x = col * cell
        y = row * cell

        # Sign abbreviation
        sign_abbr = SIGN_ABBREVIATIONS[sign]
        label = sign_abbr
        if sign == asc_sign:
            label += " Asc"
        parts.append(f'<text x="{x+5}" y="{y+15}" font-size="11" font-weight="bold" fill="#d84315">{label}</text>')

        # Planets in this sign
        planets = _planets_in_sign(chart, sign)
        for pi, p_abbr in enumerate(planets):
            py_offset = 35 + pi * 16
            parts.append(f'<text x="{x+10}" y="{y+py_offset}" font-size="12">{p_abbr}</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def _render_svg_north(chart: BirthChart) -> str:
    """Generate North Indian style SVG (diamond approximation using grid)."""
    cell = 100
    size = cell * 4

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'width="{size}" height="{size}" style="font-family:monospace;font-size:12px">',
        f'<rect width="{size}" height="{size}" fill="white" stroke="black" stroke-width="2"/>',
    ]

    # Grid lines
    for i in range(1, 4):
        parts.append(f'<line x1="{i*cell}" y1="0" x2="{i*cell}" y2="{size}" stroke="black" stroke-width="1"/>')
        parts.append(f'<line x1="0" y1="{i*cell}" x2="{size}" y2="{i*cell}" stroke="black" stroke-width="1"/>')

    # Center label
    parts.append(f'<rect x="{cell}" y="{cell}" width="{cell*2}" height="{cell*2}" fill="white" stroke="black" stroke-width="1"/>')
    parts.append(f'<text x="{size//2}" y="{size//2 - 10}" text-anchor="middle" font-size="14" font-weight="bold">North Indian</text>')
    dt_str = chart.birth_datetime.strftime("%Y-%m-%d %H:%M")
    parts.append(f'<text x="{size//2}" y="{size//2 + 10}" text-anchor="middle" font-size="11">{dt_str}</text>')

    # House positions in the grid (same layout as ASCII)
    house_grid = [
        [12, 1, 2, 3],
        [11, 0, 0, 4],
        [10, 0, 0, 5],
        [9, 8, 7, 6],
    ]

    house_signs = {h.house_number: h.sign for h in chart.houses}

    for row_idx, row in enumerate(house_grid):
        for col_idx, house_num in enumerate(row):
            if house_num == 0:
                continue
            x = col_idx * cell
            y = row_idx * cell
            sign = house_signs[house_num]
            sign_abbr = SIGN_ABBREVIATIONS[sign]
            label = f"H{house_num}:{sign_abbr}"
            if house_num == 1:
                label += "*"
            parts.append(f'<text x="{x+5}" y="{y+15}" font-size="11" font-weight="bold" fill="#d84315">{label}</text>')

            planets = _planets_in_sign(chart, sign)
            for pi, p_abbr in enumerate(planets):
                py_offset = 35 + pi * 16
                parts.append(f'<text x="{x+10}" y="{y+py_offset}" font-size="12">{p_abbr}</text>')

    parts.append("</svg>")
    return "\n".join(parts)
