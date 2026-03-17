"""
Varshaphal (Solar Return / Annual Horoscope) calculator.

THE VARSHAPHAL SYSTEM:
    Varshaphal (literally "fruit of the year") is the Tajika annual chart
    system used extensively in Indian astrology. Each year, when the Sun
    returns to the exact sidereal longitude it occupied at birth, a new
    annual chart is cast. This "solar return" moment defines the annual
    horoscope.

    Key components:
    1. Solar Return Moment — the exact datetime when the transiting Sun
       matches the natal Sun longitude
    2. Annual Chart — a full birth chart cast for the solar return moment
       at the birth location (traditional Varshaphal uses birth place)
    3. Muntha — a progressed point advancing one sign per year from the
       birth ascendant
    4. Year Lord (Varshesha) — the strongest among 5 candidate planets
    5. Mudda Dasha — Vimsottari dasha compressed to one year

SOURCE: Tajika Neelakanthi, Varshaphala texts.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import swisseph as swe

from vedic_calc.core.constants import (
    Ayanamsa,
    DEBILITATION,
    EXALTATION,
    MOOLATRIKONA,
    Nakshatra,
    PLANET_FRIENDSHIP,
    Planet,
    Sign,
    NAKSHATRA_LORDS,
    NAKSHATRA_SPAN,
    PLANET_NAMES,
    SIGN_LORDS,
    SIGN_NAMES,
    VIMSOTTARI_ORDER,
    VIMSOTTARI_YEARS,
    VIMSOTTARI_TOTAL_YEARS,
    WEEKDAY_HORA_LORD,
)
from vedic_calc.core.ephemeris import (
    _to_julian_day,
    get_ayanamsa,
    get_planet_longitude,
)
from vedic_calc.chart.calculator import calculate_chart
from vedic_calc.chart.divisional import calculate_divisional_chart
from vedic_calc.core.types import (
    BirthChart,
    DashaPeriod,
    MunthaInfo,
    PanchavargeeaBala,
    VarshaphalResult,
)


# ---------------------------------------------------------------------------
# Days per year constant (same as dasha module)
# ---------------------------------------------------------------------------
_DAYS_PER_YEAR = 365.25


# ---------------------------------------------------------------------------
# Solar return finder
# ---------------------------------------------------------------------------

def _get_tropical_sun_longitude(jd: float) -> float:
    """Get the Sun's tropical longitude for a given Julian Day.

    We use tropical longitude for the solar return search because that is
    what Swiss Ephemeris natively computes. We compare tropical-to-tropical
    so the ayanamsa cancels out (both natal and transit use the same offset).
    """
    result = swe.calc_ut(jd, swe.SUN)
    return result[0][0]


def _find_solar_return_jd(
    natal_sun_tropical: float,
    approx_jd: float,
    search_window_days: float = 3.0,
) -> float:
    """Find the exact Julian Day when transiting Sun matches natal Sun longitude.

    Uses binary search. The Sun moves ~1 degree/day, so a ±3 day window
    around the approximate birthday is more than sufficient.

    Args:
        natal_sun_tropical: The natal Sun's tropical longitude (degrees).
        approx_jd: Approximate Julian Day of the solar return (near the
                    birthday in the target year).
        search_window_days: Half-width of the search window in days.

    Returns:
        Julian Day of the exact solar return moment.
    """
    # Set up search boundaries
    jd_start = approx_jd - search_window_days
    jd_end = approx_jd + search_window_days

    # Normalize target to 0-360
    target = natal_sun_tropical % 360.0

    # We need to find where sun_lon(jd) == target.
    # The Sun moves forward ~1°/day, so we can use the difference as
    # a monotonic function (after accounting for the 360° wrap).

    def _angle_diff(jd: float) -> float:
        """Signed angular difference: positive means Sun hasn't reached target yet."""
        sun_lon = _get_tropical_sun_longitude(jd)
        diff = (target - sun_lon) % 360.0
        # Convert to signed: if diff > 180, the Sun has passed the target
        if diff > 180.0:
            diff -= 360.0
        return diff

    # Binary search to find the zero crossing
    # First ensure start is before target and end is after
    diff_start = _angle_diff(jd_start)
    diff_end = _angle_diff(jd_end)

    # If the signs are the same, shift the window
    if diff_start * diff_end > 0:
        # Try widening the window
        jd_start = approx_jd - 10.0
        jd_end = approx_jd + 10.0
        diff_start = _angle_diff(jd_start)
        diff_end = _angle_diff(jd_end)

    # Binary search with ~50 iterations gives precision < 1 second
    for _ in range(60):
        jd_mid = (jd_start + jd_end) / 2.0
        diff_mid = _angle_diff(jd_mid)

        if abs(diff_mid) < 1e-8:  # ~0.00004 arcseconds precision
            return jd_mid

        if diff_start * diff_mid > 0:
            jd_start = jd_mid
            diff_start = diff_mid
        else:
            jd_end = jd_mid
            diff_end = diff_mid

    return (jd_start + jd_end) / 2.0


def _get_natal_sun_tropical(chart: BirthChart) -> float:
    """Get the natal Sun's tropical longitude from the birth chart.

    We recalculate the tropical longitude from the birth chart metadata
    rather than adding ayanamsa back (which could introduce rounding errors).
    """
    hour_decimal = (
        chart.birth_datetime.hour
        + chart.birth_datetime.minute / 60.0
        + chart.birth_datetime.second / 3600.0
    )
    ut_hour = hour_decimal - chart.timezone_offset

    jd = _to_julian_day(
        chart.birth_datetime.year,
        chart.birth_datetime.month,
        chart.birth_datetime.day,
        ut_hour,
    )
    return _get_tropical_sun_longitude(jd)


# ---------------------------------------------------------------------------
# Muntha calculation
# ---------------------------------------------------------------------------

def _calculate_muntha(
    birth_ascendant_sign: int,
    age: int,
    annual_ascendant_sign: int,
) -> MunthaInfo:
    """Calculate the Muntha position for a given year.

    Muntha progresses one sign per year from the birth ascendant.
    Formula: muntha_sign = ((birth_asc_sign - 1 + age) % 12) + 1

    Args:
        birth_ascendant_sign: Sign number (1-12) of the birth ascendant.
        age: Age in the varshaphal year.
        annual_ascendant_sign: Sign number (1-12) of the annual chart ascendant.

    Returns:
        MunthaInfo with sign, lord, and benefic placement assessment.
    """
    muntha_sign_num = ((birth_ascendant_sign - 1 + age) % 12) + 1
    muntha_sign = Sign(muntha_sign_num)
    muntha_lord = SIGN_LORDS[muntha_sign]

    # Check if Muntha is in kendra (1,4,7,10) or trikona (1,5,9) from annual lagna
    house_from_lagna = ((muntha_sign_num - annual_ascendant_sign) % 12) + 1
    kendra_trikona = {1, 4, 5, 7, 9, 10}
    is_benefic = house_from_lagna in kendra_trikona

    return MunthaInfo(
        sign=muntha_sign_num,
        sign_name=SIGN_NAMES[muntha_sign],
        lord=muntha_lord.value,
        is_benefic_placement=is_benefic,
    )


# ---------------------------------------------------------------------------
# Year Lord (Varshesha) determination
# ---------------------------------------------------------------------------

def _planet_in_kendra_trikona_count(planet: Planet, chart: BirthChart) -> int:
    """Count how many kendra/trikona houses a planet occupies or lords in the chart.

    This is a simplified strength measure for year lord selection.
    """
    asc_sign_val = chart.ascendant.sign.value
    score = 0

    kendra_trikona = {1, 4, 5, 7, 9, 10}

    # Check if planet is placed in a kendra/trikona
    if planet in chart.planets:
        planet_sign_val = chart.planets[planet].sign.value
        house_num = ((planet_sign_val - asc_sign_val) % 12) + 1
        if house_num in kendra_trikona:
            score += 2  # Strong placement bonus

    # Check if planet lords a kendra/trikona
    for house in chart.houses:
        if house.lord == planet and house.house_number in kendra_trikona:
            score += 1

    return score


def _determine_year_lord(
    annual_chart: BirthChart,
    muntha_sign: int,
    birth_ascendant_sign: int,
    solar_return_weekday: int,
) -> Planet:
    """Determine the Year Lord (Varshesha) from the 5 candidates.

    Candidates:
    1. Lord of the annual ascendant
    2. Lord of the Muntha sign
    3. Lord of the birth ascendant
    4. Lord of the Sun's sign in the annual chart
    5. Day lord of the solar return weekday

    Strength: planet with most kendra/trikona placements in annual chart.
    Tiebreaker: highest Vimsottari dasha years.

    Args:
        annual_chart: The annual (solar return) chart.
        muntha_sign: The Muntha sign number (1-12).
        birth_ascendant_sign: Birth chart ascendant sign number (1-12).
        solar_return_weekday: Weekday of solar return (0=Monday ... 6=Sunday).

    Returns:
        The Year Lord planet.
    """
    # Gather the 5 candidates (may have duplicates — use a set for uniqueness)
    candidates: set[Planet] = set()

    # 1. Lord of annual ascendant
    candidates.add(SIGN_LORDS[annual_chart.ascendant.sign])

    # 2. Lord of Muntha sign
    candidates.add(SIGN_LORDS[Sign(muntha_sign)])

    # 3. Lord of birth ascendant
    candidates.add(SIGN_LORDS[Sign(birth_ascendant_sign)])

    # 4. Lord of Sun's sign in annual chart
    sun_sign = annual_chart.planets[Planet.SUN].sign
    candidates.add(SIGN_LORDS[sun_sign])

    # 5. Day lord of solar return weekday
    candidates.add(WEEKDAY_HORA_LORD[solar_return_weekday])

    # Score each candidate
    best_planet = None
    best_score = -1
    best_dasha_years = -1

    for planet in candidates:
        score = _planet_in_kendra_trikona_count(planet, annual_chart)
        dasha_years = VIMSOTTARI_YEARS.get(planet, 0)

        if (score > best_score) or (score == best_score and dasha_years > best_dasha_years):
            best_planet = planet
            best_score = score
            best_dasha_years = dasha_years

    return best_planet  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Mudda Dasha (annual Vimsottari compressed to 1 year)
# ---------------------------------------------------------------------------

def _calculate_mudda_dasha(
    annual_chart: BirthChart,
    solar_return_dt: datetime,
    levels: int = 1,
) -> list[DashaPeriod]:
    """Calculate Mudda Dasha periods for the annual chart.

    Mudda Dasha is the Vimsottari dasha system compressed to fit within
    one year (365.25 days). The starting lord is determined by the Moon's
    nakshatra in the annual chart.

    Same sequence: Ketu -> Venus -> Sun -> Moon -> Mars -> Rahu -> Jupiter -> Saturn -> Mercury
    Duration: planet_years / 120 * 365.25 days

    Args:
        annual_chart: The annual (solar return) chart.
        solar_return_dt: The datetime of the solar return.
        levels: 1 = mahadasha only, 2 = + antardashas.

    Returns:
        List of DashaPeriod objects for the Mudda Dasha periods.
    """
    moon = annual_chart.planets[Planet.MOON]
    nak_info = moon.nakshatra_info
    starting_lord = nak_info.lord

    # Elapsed fraction of the first dasha period
    elapsed_fraction = nak_info.degree_in_nakshatra / NAKSHATRA_SPAN

    # Build the dasha sequence starting from the Moon's nakshatra lord
    idx = VIMSOTTARI_ORDER.index(starting_lord)
    sequence = VIMSOTTARI_ORDER[idx:] + VIMSOTTARI_ORDER[:idx]

    periods: list[DashaPeriod] = []

    # The first mudda dasha started before the solar return
    first_full_days = (VIMSOTTARI_YEARS[starting_lord] / VIMSOTTARI_TOTAL_YEARS) * _DAYS_PER_YEAR
    elapsed_days = first_full_days * elapsed_fraction
    current_start = solar_return_dt - timedelta(days=elapsed_days)

    for lord in sequence:
        full_days = (VIMSOTTARI_YEARS[lord] / VIMSOTTARI_TOTAL_YEARS) * _DAYS_PER_YEAR
        duration_days = full_days
        duration_years = duration_days / _DAYS_PER_YEAR

        end = current_start + timedelta(days=duration_days)

        periods.append(DashaPeriod(
            lord=lord,
            level="mudda_dasha",
            start=current_start,
            end=end,
            duration_years=round(duration_years, 6),
        ))

        # ─── Mudda Dasha Antardashas (sub-periods) ───
        if levels >= 2:
            antar_start = current_start
            # Sub-period sequence starts from the mahadasha lord
            antar_idx = VIMSOTTARI_ORDER.index(lord)
            antar_sequence = VIMSOTTARI_ORDER[antar_idx:] + VIMSOTTARI_ORDER[:antar_idx]

            for antar_lord in antar_sequence:
                antar_days = duration_days * (
                    VIMSOTTARI_YEARS[antar_lord] / VIMSOTTARI_TOTAL_YEARS
                )
                antar_years = antar_days / _DAYS_PER_YEAR
                antar_end = antar_start + timedelta(days=antar_days)

                periods.append(DashaPeriod(
                    lord=antar_lord,
                    level="mudda_antardasha",
                    start=antar_start,
                    end=antar_end,
                    duration_years=round(antar_years, 6),
                ))

                antar_start = antar_end

        current_start = end

    return periods


# ---------------------------------------------------------------------------
# Panchavargeeya Bala (5-fold dignity strength)
# ---------------------------------------------------------------------------

# Dignity scoring: points for each dignity level
_DIGNITY_POINTS: dict[str, float] = {
    "exalted": 4.0,
    "moolatrikona": 3.5,
    "own": 3.0,
    "friend": 2.0,
    "neutral": 1.5,
    "enemy": 1.0,
    "debilitated": 0.5,
}


def _get_dignity(planet: Planet, sign: Sign) -> str:
    """Determine the dignity of a planet in a given sign.

    Checks in order: exalted, debilitated, moolatrikona, own sign,
    then uses the friendship table for friend/neutral/enemy.

    Args:
        planet: The planet to check.
        sign: The sign the planet is placed in.

    Returns:
        One of: "exalted", "moolatrikona", "own", "friend", "neutral",
                "enemy", "debilitated".
    """
    # Check exaltation (sign match only — degree ignored for varga dignity)
    if planet in EXALTATION and EXALTATION[planet][0] == sign:
        return "exalted"

    # Check debilitation
    if planet in DEBILITATION and DEBILITATION[planet][0] == sign:
        return "debilitated"

    # Check moolatrikona (sign match only for varga assessment)
    if planet in MOOLATRIKONA and MOOLATRIKONA[planet][0] == sign:
        return "moolatrikona"

    # Check own sign
    sign_lord = SIGN_LORDS[sign]
    if sign_lord == planet:
        return "own"

    # Use friendship table for classical planets
    if planet in PLANET_FRIENDSHIP and sign_lord in PLANET_FRIENDSHIP.get(planet, {}):
        friendship = PLANET_FRIENDSHIP[planet][sign_lord]
        if friendship == 2:
            return "friend"
        elif friendship == 1:
            return "neutral"
        else:
            return "enemy"

    # Rahu/Ketu: treat as neutral by default
    return "neutral"


def calculate_panchavargeeya_bala(
    annual_chart: BirthChart,
) -> list[PanchavargeeaBala]:
    """Calculate Panchavargeeya Bala (5-fold dignity strength) for annual chart planets.

    Evaluates each planet's dignity in 5 divisional charts:
    D1 (Rasi), D2 (Hora), D3 (Drekkana), D9 (Navamsa), D12 (Dwadasamsa).

    Total points range from 0 to 20 (5 divisions x max 4 points each).

    Args:
        annual_chart: The annual (solar return) chart.

    Returns:
        List of PanchavargeeaBala objects, one per planet.
    """
    # Calculate the 5 divisional charts
    d2 = calculate_divisional_chart(annual_chart, 2)
    d3 = calculate_divisional_chart(annual_chart, 3)
    d9 = calculate_divisional_chart(annual_chart, 9)
    d12 = calculate_divisional_chart(annual_chart, 12)

    results: list[PanchavargeeaBala] = []

    for planet in Planet:
        # D1: use the planet's sign from the annual chart itself
        d1_sign = annual_chart.planets[planet].sign
        d1_dignity = _get_dignity(planet, d1_sign)

        # D2, D3, D9, D12: use the divisional chart planet-sign mapping
        d2_sign = d2.planets[planet]
        d2_dignity = _get_dignity(planet, d2_sign)

        d3_sign = d3.planets[planet]
        d3_dignity = _get_dignity(planet, d3_sign)

        d9_sign = d9.planets[planet]
        d9_dignity = _get_dignity(planet, d9_sign)

        d12_sign = d12.planets[planet]
        d12_dignity = _get_dignity(planet, d12_sign)

        total = (
            _DIGNITY_POINTS[d1_dignity]
            + _DIGNITY_POINTS[d2_dignity]
            + _DIGNITY_POINTS[d3_dignity]
            + _DIGNITY_POINTS[d9_dignity]
            + _DIGNITY_POINTS[d12_dignity]
        )

        results.append(PanchavargeeaBala(
            planet=planet,
            d1_dignity=d1_dignity,
            d2_dignity=d2_dignity,
            d3_dignity=d3_dignity,
            d9_dignity=d9_dignity,
            d12_dignity=d12_dignity,
            total_points=round(total, 1),
        ))

    return results


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def calculate_varshaphal(
    chart: BirthChart,
    year: int,
) -> VarshaphalResult:
    """Calculate the Varshaphal (Solar Return / Annual Horoscope) for a given year.

    The Varshaphal is the Tajika annual chart system. It finds the exact
    moment when the transiting Sun returns to the natal Sun longitude,
    then casts a chart for that moment at the birth location.

    Args:
        chart: The natal birth chart (from calculate_chart()).
        year: The year for which to calculate the Varshaphal. This is the
              calendar year in which the solar return occurs. For example,
              for someone born in 1990, year=2025 gives the annual chart
              for their 35th year.

    Returns:
        VarshaphalResult with the annual chart, Muntha, year lord, and
        Mudda Dasha periods.

    Example:
        >>> from vedic_calc import calculate_chart
        >>> chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
        >>> result = calculate_varshaphal(chart, 2025)
        >>> result.age
        35
        >>> result.year_lord_name
        'Sun (Surya)'
    """
    # ─── Step 1: Find the natal Sun's tropical longitude ───
    natal_sun_tropical = _get_natal_sun_tropical(chart)

    # ─── Step 2: Find the solar return moment ───
    # Approximate JD: use the birthday in the target year
    birth_dt = chart.birth_datetime
    approx_hour_ut = (
        birth_dt.hour + birth_dt.minute / 60.0 + birth_dt.second / 3600.0
        - chart.timezone_offset
    )
    approx_jd = _to_julian_day(year, birth_dt.month, birth_dt.day, approx_hour_ut)

    solar_return_jd = _find_solar_return_jd(natal_sun_tropical, approx_jd)

    # ─── Step 3: Convert solar return JD to datetime ───
    # Convert JD back to date/time in UT, then apply timezone
    yr, mo, dy, hr_ut = swe.revjul(solar_return_jd)
    hr_local = hr_ut + chart.timezone_offset

    # Handle day rollover
    day_offset = 0
    if hr_local >= 24.0:
        hr_local -= 24.0
        day_offset = 1
    elif hr_local < 0.0:
        hr_local += 24.0
        day_offset = -1

    hours = int(hr_local)
    remainder = (hr_local - hours) * 60
    minutes = int(remainder)
    seconds = int((remainder - minutes) * 60)

    solar_return_dt = datetime(int(yr), int(mo), int(dy), hours, minutes, seconds)
    if day_offset != 0:
        solar_return_dt += timedelta(days=day_offset)

    # ─── Step 4: Cast the annual chart at birth location ───
    annual_chart = calculate_chart(
        year=solar_return_dt.year,
        month=solar_return_dt.month,
        day=solar_return_dt.day,
        hour=solar_return_dt.hour,
        minute=solar_return_dt.minute,
        second=solar_return_dt.second,
        latitude=chart.latitude,
        longitude=chart.longitude,
        timezone_offset=chart.timezone_offset,
        ayanamsa=chart.ayanamsa,
    )

    # ─── Step 5: Calculate age and Muntha ───
    age = year - birth_dt.year
    birth_asc_sign = chart.ascendant.sign.value
    annual_asc_sign = annual_chart.ascendant.sign.value

    muntha = _calculate_muntha(birth_asc_sign, age, annual_asc_sign)

    # ─── Step 6: Determine the Year Lord ───
    # Get the weekday of the solar return (Python: 0=Monday, 6=Sunday)
    solar_return_weekday = solar_return_dt.weekday()
    year_lord = _determine_year_lord(
        annual_chart, muntha.sign, birth_asc_sign, solar_return_weekday,
    )

    # ─── Step 7: Calculate Mudda Dasha ───
    mudda_dasha = _calculate_mudda_dasha(annual_chart, solar_return_dt)

    return VarshaphalResult(
        birth_year=birth_dt.year,
        varshaphal_year=year,
        age=age,
        solar_return_datetime=solar_return_dt,
        annual_chart=annual_chart,
        muntha=muntha,
        year_lord=year_lord.value,
        year_lord_name=PLANET_NAMES[year_lord],
        mudda_dasha=mudda_dasha,
    )
