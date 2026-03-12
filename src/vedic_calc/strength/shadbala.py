"""
Shadbala (six-fold strength) calculation for Vedic astrology.

Shadbala ("shad" = six, "bala" = strength) quantifies a planet's total
strength by combining six distinct factors. It is one of the most
comprehensive strength metrics in classical Jyotish, described in detail
in BPHS Chapter 27.

The six components (all measured in Shashtiamsas = 1/60 Rupa):
    1. Sthana Bala — Positional strength (sign placement, dignity, etc.)
    2. Dig Bala    — Directional strength (which house the planet occupies)
    3. Kaala Bala  — Temporal strength (day/night birth, planetary hour, etc.)
    4. Chesta Bala — Motional strength (retrograde, direct, stationary)
    5. Naisargika Bala — Natural/inherent strength (fixed per planet)
    6. Drik Bala   — Aspectual strength (benefic/malefic aspects received)

Only the seven visible planets (Sun through Saturn) are included in
Shadbala. Rahu and Ketu, being shadow planets (lunar nodes), are excluded.

Reference: Brihat Parashara Hora Shastra (BPHS), Chapter 27.
"""

from __future__ import annotations

import math
from datetime import datetime

import swisseph as swe

from vedic_calc.chart.divisional import calculate_divisional_chart
from vedic_calc.core.constants import (
    DEBILITATION,
    EXALTATION,
    MOOLATRIKONA,
    NAISARGIKA_BALA,
    PLANET_FRIENDSHIP,
    SIGN_LORDS,
    Planet,
    Sign,
)
from vedic_calc.core.ephemeris import _to_julian_day, get_sunrise_sunset
from vedic_calc.core.types import BirthChart, ShadbalaResult

# The seven planets included in Shadbala (Rahu/Ketu excluded).
_SHADBALA_PLANETS: list[Planet] = [
    Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
    Planet.JUPITER, Planet.VENUS, Planet.SATURN,
]

# Index mapping: Planet -> 0-6 index (same order as PyJHora)
_PLANET_INDEX = {
    Planet.SUN: 0, Planet.MOON: 1, Planet.MARS: 2, Planet.MERCURY: 3,
    Planet.JUPITER: 4, Planet.VENUS: 5, Planet.SATURN: 6,
}

# Per-planet minimum required Shadbala (in Rupas) per BPHS.
# Sun=5, Moon=6, Mars=5, Mercury=7, Jupiter=6.5, Venus=5.5, Saturn=5
_REQUIRED_RUPAS = {
    Planet.SUN: 5.0, Planet.MOON: 6.0, Planet.MARS: 5.0,
    Planet.MERCURY: 7.0, Planet.JUPITER: 6.5,
    Planet.VENUS: 5.5, Planet.SATURN: 5.0,
}

# Saptavargaja: the 7 divisional charts used for dignity evaluation.
# D1 (Rasi), D2 (Hora), D3 (Drekkana), D7 (Saptamsa),
# D9 (Navamsa), D12 (Dwadasamsa), D30 (Trimsamsa)
_SAPTAVARGA_DIVISIONS = [1, 2, 3, 7, 9, 12, 30]

# Saptavargaja dignity scores (Shashtiamsas per varga).
# BPHS Ch. 27: Moolatrikona=45, Own=30, GreatFriend=22.5,
# Friend=15, Neutral=7.5, Enemy=3.75, GreatEnemy=1.875
_DIGNITY_SCORES = {
    "moolatrikona": 45.0,
    "own_sign": 30.0,
    "great_friend": 22.5,
    "friend": 15.0,
    "neutral": 7.5,
    "enemy": 3.75,
    "great_enemy": 1.875,
}

# Powerless houses for Dig Bala (0-indexed house number from ascendant).
# The planet's Dig Bala = 0 at the bhava madhya of these houses.
# Sun/Mars: 4th (nadir), Moon/Venus: 10th (zenith), Mercury/Jupiter: 7th (west),
# Saturn: 1st (east).
# Per BPHS Ch. 27: these are houses OPPOSITE to the directional stronghold.
# Encoded as 0-indexed house offsets from ascendant.
_POWERLESS_HOUSES = {
    Planet.SUN: 3,       # 4th house (opposite 10th)
    Planet.MOON: 9,      # 10th house (opposite 4th)
    Planet.MARS: 3,      # 4th house (opposite 10th)
    Planet.MERCURY: 6,   # 7th house (opposite 1st)
    Planet.JUPITER: 6,   # 7th house (opposite 1st)
    Planet.VENUS: 9,     # 10th house (opposite 4th)
    Planet.SATURN: 0,    # 1st house (opposite 7th)
}

# Drekkana bala planet groupings by decanate (BPHS Ch. 27).
# 1st decanate (0-10): Male planets (Sun=0, Mars=2, Jupiter=4)
# 2nd decanate (10-20): Neutral planets (Mercury=3, Saturn=6)
# 3rd decanate (20-30): Female planets (Moon=1, Venus=5)
_DREKKANA_GROUPS = [
    {Planet.SUN, Planet.MARS, Planet.JUPITER},     # 1st decanate
    {Planet.MERCURY, Planet.SATURN},                # 2nd decanate
    {Planet.MOON, Planet.VENUS},                    # 3rd decanate
]

# Planetary weekday rulers (0=Sun, 1=Moon, 2=Mars, 3=Mercury, 4=Jupiter,
# 5=Venus, 6=Saturn) mapped to Planet enum.
_WEEKDAY_PLANETS = [
    Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
    Planet.JUPITER, Planet.VENUS, Planet.SATURN,
]

# Hora order: Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon
# (descending Chaldean order, used for planetary hours)
_HORA_ORDER = [
    Planet.SATURN, Planet.JUPITER, Planet.MARS, Planet.SUN,
    Planet.VENUS, Planet.MERCURY, Planet.MOON,
]


# ---------------------------------------------------------------------------
# Helper: compute absolute longitude from sign + degree
# ---------------------------------------------------------------------------

def _absolute_longitude(sign: Sign, degree: float) -> float:
    """Convert a (sign, degree_in_sign) pair to absolute longitude (0-360)."""
    return (int(sign) - 1) * 30.0 + degree


def _sign_from_longitude(longitude: float) -> Sign:
    """Get the Sign from an absolute longitude."""
    return Sign(int(longitude / 30.0) % 12 + 1)


# ---------------------------------------------------------------------------
# Helper: get dignity of a planet in a given sign (for saptavargaja)
# ---------------------------------------------------------------------------

def _get_varga_dignity(planet: Planet, sign: Sign, degree_in_sign: float,
                       is_d1: bool = False) -> str:
    """Return the dignity of a planet in a divisional chart sign.

    For D1 chart, checks moolatrikona. For all charts, checks own sign
    and friendship with the sign lord.

    Returns one of: 'moolatrikona', 'own_sign', 'great_friend', 'friend',
    'neutral', 'enemy', 'great_enemy'.
    """
    sign_lord = SIGN_LORDS[sign]

    # Moolatrikona only in D1 (rasi chart)
    if is_d1 and planet in MOOLATRIKONA:
        mt_sign, mt_start, mt_end = MOOLATRIKONA[planet]
        if sign == mt_sign and mt_start <= degree_in_sign < mt_end:
            return "moolatrikona"

    # Own sign (planet is the lord of this sign)
    if sign_lord == planet:
        return "own_sign"

    # Friendship with sign lord
    if planet in PLANET_FRIENDSHIP and sign_lord in PLANET_FRIENDSHIP[planet]:
        friendship = PLANET_FRIENDSHIP[planet][sign_lord]
        if friendship == 2:
            return "great_friend"
        if friendship == 1:
            return "neutral"
        return "enemy"

    return "neutral"


# ---------------------------------------------------------------------------
# Helper: compute bhava madhya (house midpoints) using whole-sign houses
# ---------------------------------------------------------------------------

def _bhava_madhya_longitudes(chart: BirthChart) -> list[float]:
    """Return the midpoint longitude of each house (0-11 indexed).

    Uses Placidus house cusps from Swiss Ephemeris (same as PyJHora's
    KP method) and applies Sripati-style interpolation for intermediate
    houses. This gives unequal house sizes based on the actual MC/IC axis.
    """
    dt = chart.birth_datetime
    ut_hour = (dt.hour + dt.minute / 60.0 + dt.second / 3600.0) - chart.timezone_offset
    jd = _to_julian_day(dt.year, dt.month, dt.day, ut_hour)

    # Get sidereal house cusps using Placidus
    from vedic_calc.core.constants import Ayanamsa
    swe.set_sid_mode(int(Ayanamsa.LAHIRI))
    cusps, _ = swe.houses_ex(jd, chart.latitude, chart.longitude,
                              flags=swe.FLG_SIDEREAL)
    # cusps is a 12-element tuple of house cusp longitudes
    # Apply Sripati modification: interpolate intermediate houses
    bm = list(cusps)
    # Sripati: houses 1,4,7,10 are anchors; 2,3 interpolated between 1-4, etc.
    anchors = [0, 3, 6, 9, 12]  # indices (12 wraps to 0)
    for i in range(1, len(anchors)):
        bi1 = anchors[i - 1] % 12
        bi2 = anchors[i] % 12
        b1 = bm[bi1]
        b2 = bm[bi2]
        if b2 < b1:
            b2 += 360.0
        bd = abs(b2 - b1) / 3.0
        bm[(bi1 + 1) % 12] = (bm[bi1 % 12] + bd) % 360.0
        bm[(bi2 - 1) % 12] = (bm[bi2 % 12] - bd) % 360.0

    return bm


# ---------------------------------------------------------------------------
# 1. Sthana Bala (Positional Strength) — BPHS Ch. 27
# ---------------------------------------------------------------------------

def _sthana_bala(planet: Planet, chart: BirthChart) -> float:
    """Compute Sthana Bala as the sum of five positional sub-strengths.

    Sub-components:
      (a) Uchcha Bala — distance from deep debilitation point (max 60)
      (b) Saptavargaja Bala — dignity across 7 divisional charts
      (c) Ojhayugma Bala — odd/even sign in D1 and D9 (max 30)
      (d) Kendradi Bala — angular house strength (60/30/15)
      (e) Drekkana Bala — decanate gender match (15 or 0)
    """
    pos = chart.planets[planet]

    # (a) Uchcha Bala — Saravali formula: dist_from_debilitation / 3
    deb_sign, deb_deg = DEBILITATION[planet]
    deb_longitude = _absolute_longitude(deb_sign, deb_deg)
    dist = abs(pos.longitude - deb_longitude)
    if dist > 180.0:
        dist = 360.0 - dist
    uchcha_bala = dist / 3.0  # max 60 when 180 deg from debilitation

    # (b) Saptavargaja Bala — dignity evaluated in 7 divisional charts
    saptavargaja_bala = 0.0
    for div in _SAPTAVARGA_DIVISIONS:
        if div == 1:
            # D1: use the rasi chart directly
            dignity = _get_varga_dignity(planet, pos.sign, pos.degree_in_sign,
                                         is_d1=True)
        else:
            # Compute divisional chart and get the sign
            div_chart = calculate_divisional_chart(chart, div)
            div_sign = div_chart.planets[planet]
            # For non-D1, degree_in_sign is not meaningful for MT check
            dignity = _get_varga_dignity(planet, div_sign, 0.0, is_d1=False)
        saptavargaja_bala += _DIGNITY_SCORES.get(dignity, 7.5)

    # (c) Ojhayugma Bala — odd/even sign in D1 and D9
    # Moon and Venus get 15 in even signs, others get 15 in odd signs.
    # Checked in both D1 (rasi) and D9 (navamsa), max 30.
    d9 = calculate_divisional_chart(chart, 9)
    ojhayugma_bala = 0.0
    rasi_sign_val = int(pos.sign)
    navamsa_sign_val = int(d9.planets[planet])
    is_even_rasi = (rasi_sign_val % 2 == 0)
    is_even_navamsa = (navamsa_sign_val % 2 == 0)

    if planet in (Planet.MOON, Planet.VENUS):
        if is_even_rasi:
            ojhayugma_bala += 15.0
        if is_even_navamsa:
            ojhayugma_bala += 15.0
    else:
        if not is_even_rasi:
            ojhayugma_bala += 15.0
        if not is_even_navamsa:
            ojhayugma_bala += 15.0

    # (d) Kendradi Bala — based on house type (kendra/panaphara/apoklima)
    planet_house = _planet_house_number(pos.sign, chart)
    if planet_house in (1, 4, 7, 10):
        kendradi_bala = 60.0
    elif planet_house in (2, 5, 8, 11):
        kendradi_bala = 30.0
    else:
        kendradi_bala = 15.0

    # (e) Drekkana Bala — decanate/gender match
    deg = pos.degree_in_sign
    decanate = min(int(deg / 10.0), 2)  # 0, 1, or 2
    drekkana_bala = 15.0 if planet in _DREKKANA_GROUPS[decanate] else 0.0

    return uchcha_bala + saptavargaja_bala + ojhayugma_bala + kendradi_bala + drekkana_bala


def _planet_house_number(planet_sign: Sign, chart: BirthChart) -> int:
    """Return the house number (1-12) for a planet in the given sign."""
    for house in chart.houses:
        if house.sign == planet_sign:
            return house.house_number
    return 1


# ---------------------------------------------------------------------------
# 2. Dig Bala (Directional Strength) — BPHS Ch. 27
# ---------------------------------------------------------------------------

def _dig_bala(planet: Planet, chart: BirthChart) -> float:
    """Compute Dig Bala using longitude-based distance from powerless bhava madhya.

    Per BPHS Ch. 27: A planet gets 0 Dig Bala at the midpoint of its
    powerless house and maximum (60) at the midpoint of its directional
    stronghold (180 degrees away). Formula: abs(distance) / 3.

    Uses bhava madhya (house midpoints) based on the ascendant longitude.
    """
    pos = chart.planets[planet]
    p_long = pos.longitude

    # Get bhava madhya longitudes (Sripati/Placidus based)
    bm = _bhava_madhya_longitudes(chart)

    # Get the powerless house midpoint longitude
    powerless_idx = _POWERLESS_HOUSES[planet]
    powerless_long = bm[powerless_idx]

    # Distance from powerless point.
    # Note: PyJHora does NOT cap the distance at 180 degrees, allowing
    # dig bala values up to ~120 Shashtiamsas. This follows from a
    # direct reading of the BPHS formula without the circular distance
    # reduction that many implementations apply.
    dist = abs(p_long - powerless_long)

    return dist / 3.0


# ---------------------------------------------------------------------------
# 3. Kaala Bala (Temporal Strength) — BPHS Ch. 27
# ---------------------------------------------------------------------------

def _kaala_bala(planet: Planet, chart: BirthChart) -> float:
    """Compute Kaala Bala as the sum of temporal sub-strengths.

    Sub-components:
      (a) Nathonnatha Bala — day/night strength based on birth time
      (b) Paksha Bala — lunar phase strength
      (c) Tribhaga Bala — 1/3 day/night division strength
      (d) Abda Bala — year lord (15)
      (e) Masa Bala — month lord (30)
      (f) Vaara Bala — weekday lord (45)
      (g) Hora Bala — hour lord (60)
      (h) Ayana Bala — declination-based strength
      (i) Yuddha Bala — planetary war (simplified to 0)
    """
    # Compute Julian Day for this birth
    dt = chart.birth_datetime
    ut_hour = (dt.hour + dt.minute / 60.0 + dt.second / 3600.0) - chart.timezone_offset
    jd = _to_julian_day(dt.year, dt.month, dt.day, ut_hour)

    # Get sunrise/sunset for the birth date
    # Use JD at midnight UT for the day
    jd_midnight = _to_julian_day(dt.year, dt.month, dt.day, 0.0)
    try:
        sunrise_jd, sunset_jd = get_sunrise_sunset(
            jd_midnight, chart.latitude, chart.longitude
        )
        # Convert to local decimal hours
        sunrise_h = (swe.revjul(sunrise_jd)[3] + chart.timezone_offset) % 24.0
        sunset_h = (swe.revjul(sunset_jd)[3] + chart.timezone_offset) % 24.0
    except Exception:
        sunrise_h = 6.0
        sunset_h = 18.0

    birth_hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0

    # (a) Nathonnatha Bala — Based on distance from midnight.
    # Per BPHS: Day planets (Sun, Jupiter, Venus) get strength proportional
    # to distance from midnight. Night planets (Moon, Mars, Saturn) get
    # strength proportional to proximity to midnight. Mercury always gets 60.
    # Formula: t_diff = |birth_time - midnight| * 60 / 12
    midnight_h = _compute_midnight(sunrise_h, sunset_h)

    # Circular distance from midnight in hours (0-12 range)
    dist_from_midnight = abs(birth_hour - midnight_h)
    if dist_from_midnight > 12.0:
        dist_from_midnight = 24.0 - dist_from_midnight
    t_diff = dist_from_midnight * 60.0 / 12.0

    # Clamp to 0-60
    t_diff = max(0.0, min(60.0, t_diff))

    if planet == Planet.MERCURY:
        nathonnatha_bala = 60.0
    elif planet in (Planet.SUN, Planet.JUPITER, Planet.VENUS):
        nathonnatha_bala = t_diff
    else:  # Moon, Mars, Saturn
        nathonnatha_bala = 60.0 - t_diff

    # (b) Paksha Bala — Based on Sun-Moon angular distance.
    # Benefics get strength in Shukla Paksha (waxing), malefics in Krishna.
    sun_long = chart.planets[Planet.SUN].longitude
    moon_long = chart.planets[Planet.MOON].longitude
    sun_moon_dist = abs(moon_long - sun_long)
    if sun_moon_dist > 360.0:
        sun_moon_dist = sun_moon_dist % 360.0

    paksha_raw = sun_moon_dist / 3.0  # Max 60 at full moon (180 deg)
    if paksha_raw > 60.0:
        paksha_raw = (360.0 - sun_moon_dist) / 3.0

    # Determine benefic/malefic status for paksha bala.
    # PyJHora uses chart-specific benefic/malefic determination:
    # Tithi determines if Moon is benefic (waxing) or malefic (waning).
    # Then benefics get paksha_raw, malefics get (60 - paksha_raw).
    # Moon always gets 2x its paksha value.
    tithi_angle = (moon_long - sun_long) % 360.0
    is_waxing = tithi_angle <= 180.0

    # Determine chart-specific benefics/malefics
    # Natural benefics: Jupiter, Venus, Mercury (unafflicted)
    # Natural malefics: Sun, Mars, Saturn
    # Moon: benefic if waxing, malefic if waning
    cht_benefics = {Planet.JUPITER, Planet.VENUS, Planet.MERCURY}
    cht_malefics = {Planet.SUN, Planet.MARS, Planet.SATURN}
    if is_waxing:
        cht_benefics.add(Planet.MOON)
    else:
        cht_malefics.add(Planet.MOON)

    # Assign paksha bala based on classification
    if planet in cht_benefics:
        paksha_bala = paksha_raw
    else:  # malefic
        paksha_bala = 60.0 - paksha_raw

    # Moon always gets 2x paksha bala per BPHS
    if planet == Planet.MOON:
        paksha_bala *= 2.0

    # (c) Tribhaga Bala — Which third of day/night is the birth in?
    # Day is divided into 3 equal parts, night into 3 equal parts.
    # 1st part of day: Mercury=60. 2nd: Sun=60. 3rd: Saturn=60.
    # 1st part of night: Moon=60. 2nd: Venus=60. 3rd: Mars=60.
    # Jupiter always gets 60.
    day_length = sunset_h - sunrise_h
    if day_length <= 0:
        day_length += 24.0
    night_length = 24.0 - day_length
    day_third = day_length / 3.0
    night_third = night_length / 3.0

    tribhaga_bala = 0.0
    if planet == Planet.JUPITER:
        tribhaga_bala = 60.0
    elif birth_hour >= sunrise_h and birth_hour < sunrise_h + day_third:
        if planet == Planet.MERCURY:
            tribhaga_bala = 60.0
    elif birth_hour >= sunrise_h + day_third and birth_hour < sunrise_h + 2 * day_third:
        if planet == Planet.SUN:
            tribhaga_bala = 60.0
    elif birth_hour >= sunrise_h + 2 * day_third and birth_hour < sunset_h:
        if planet == Planet.SATURN:
            tribhaga_bala = 60.0
    elif birth_hour >= sunset_h and birth_hour < sunset_h + night_third:
        if planet == Planet.MOON:
            tribhaga_bala = 60.0
    elif ((birth_hour >= sunset_h + night_third and birth_hour < 24.0) or
          (birth_hour >= 0 and birth_hour < sunrise_h - night_third)):
        if planet == Planet.VENUS:
            tribhaga_bala = 60.0
    elif birth_hour >= sunrise_h - night_third and birth_hour < sunrise_h:
        if planet == Planet.MARS:
            tribhaga_bala = 60.0

    # (d-g) Abda/Masa/Vaara/Hora Bala
    # Uses Ahargana-based calculation per B.V. Raman / BPHS.

    # Ahargana weekday mapping: starts from Tuesday
    _abda_weekdays = [Planet.MARS, Planet.MERCURY, Planet.JUPITER,
                      Planet.VENUS, Planet.SATURN, Planet.SUN, Planet.MOON]

    # Compute Ahargana (days from epoch)
    elapsed_days_in_year = int(jd - _to_julian_day(dt.year, 1, 1, 0.0) + 1)
    ahargana = _days_elapsed_since_base(dt.year - 1) + elapsed_days_in_year

    # Abda (year lord) Bala: 15
    abda_idx = (int(ahargana // 360) * 3 + 1) % 7
    abda_lord = _abda_weekdays[abda_idx]
    abda_bala = 15.0 if planet == abda_lord else 0.0

    # Masa (month lord) Bala: 30
    masa_idx = (int(ahargana // 30) * 2 + 1) % 7
    masa_lord = _abda_weekdays[masa_idx]
    masa_bala = 30.0 if planet == masa_lord else 0.0

    # Vaara (weekday lord) Bala: 45
    # Use Ahargana with a different base epoch for vaara
    ahargana_vaara = _days_elapsed_since_base(
        dt.year - 1, base_year=1827, base_days=244) + elapsed_days_in_year
    if birth_hour < sunrise_h:
        ahargana_vaara -= 1
    vaara_idx = int(ahargana_vaara) % 7
    vaara_lord = _abda_weekdays[vaara_idx]
    vaara_bala = 45.0 if planet == vaara_lord else 0.0

    # Hora (planetary hour) Bala: 60
    # Use JD-based weekday (same as PyJHora's drik.vaara)
    # JD weekday: (int(jd + 1.5) % 7) gives 0=Mon, but we use
    # a simpler approach: JD 0 was Monday, so (jd + 1.5) % 7 = weekday
    # Convert to 0=Sun: PyJHora vaara = int(ceil(jd+1)) % 7 where 0=Sun
    day_sun = int(math.ceil(jd + 1)) % 7  # 0=Sun in JD system
    tobh = birth_hour
    if tobh < sunrise_h:
        day_sun = (day_sun - 1) % 7
        tobh += 24.0
    # Hora planet order: Saturn(6), Jupiter(4), Mars(2), Sun(0), Venus(5), Mercury(3), Moon(1)
    # Using planet indices (0-6)
    hora_order_idx = [6, 4, 2, 0, 5, 3, 1]
    hora_idx = (int(tobh - sunrise_h) + day_sun + 1) % 7
    hora_planet_idx = hora_order_idx[hora_idx]
    hora_lord = _SHADBALA_PLANETS[hora_planet_idx]
    hora_bala = 60.0 if planet == hora_lord else 0.0

    # (h) Ayana Bala — based on planetary declination.
    # Formula: (24 + declination) * 1.25, doubled for Sun.
    # Use Swiss Ephemeris to get declination.
    try:
        ayana_bala = _ayana_bala_for_planet(planet, jd)
    except Exception:
        ayana_bala = 30.0  # fallback

    # (i) Yuddha Bala — planetary war. Simplified to 0 for now.
    yuddha_bala = 0.0

    total = (nathonnatha_bala + paksha_bala + tribhaga_bala +
             abda_bala + masa_bala + vaara_bala + hora_bala +
             ayana_bala + yuddha_bala)

    return total


def _compute_midnight(sunrise_h: float, sunset_h: float) -> float:
    """Compute local midnight hour as the midpoint of the night.

    Night runs from sunset to next sunrise. Midnight is the midpoint.
    """
    # Night duration: from sunset to next day's sunrise
    # Assuming sunrise_h and sunset_h are for the same day
    night_half = (24.0 - sunset_h + sunrise_h) / 2.0
    midnight = (sunset_h + night_half) % 24.0
    return midnight


def _days_elapsed_since_base(year: int, base_year: int = 1951,
                              base_days: int = 174) -> int:
    """Calculate Ahargana (elapsed days) from a base epoch.

    Based on B.V. Raman's Bhava and Graha Bala Table I.
    """
    total_years = year - base_year
    leap_years = len([
        y for y in range(base_year + 1, year + 1)
        if (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)
    ])
    non_leap_years = total_years - leap_years
    return base_days + (leap_years * 366) + (non_leap_years * 365)


def _ayana_bala_for_planet(planet: Planet, jd: float) -> float:
    """Compute Ayana Bala based on planetary declination.

    Uses the Surya Siddhanta method: compute the bhuja (reduced longitude),
    then use a declination table with interpolation.

    Per BPHS: Ayana Bala = (24 + declination) * 1.25
    Sun gets double ayana bala.
    """
    from vedic_calc.core.constants import PLANET_TO_SWE, Ayanamsa
    from vedic_calc.core.ephemeris import get_ayanamsa, get_planet_longitude

    try:
        # Get sidereal longitude
        sid_lon, _ = get_planet_longitude(jd, planet, Ayanamsa.LAHIRI)
        ayanamsa = get_ayanamsa(jd, Ayanamsa.LAHIRI)

        # Convert back to tropical for declination calculation
        trop_lon = (sid_lon + ayanamsa) % 360.0

        # Compute bhuja (reduced tropical longitude to 0-90 range)
        if 0.0 <= trop_lon <= 90.0:
            bhuja = trop_lon
        elif 90.0 < trop_lon <= 180.0:
            bhuja = 180.0 - trop_lon
        elif 180.0 < trop_lon <= 270.0:
            bhuja = trop_lon - 180.0
        else:
            bhuja = 360.0 - trop_lon

        # Surya Siddhanta declination table (same as PyJHora)
        # Declination values at bhuja angles 0, 15, 30, 45, 60, 75, 90
        decl_values = [0, 362 / 60.0, 703 / 60.0, 1002 / 60.0, 1238 / 60.0,
                       1388 / 60.0, 1440 / 60.0]
        bhuja_angles = [i * 15 for i in range(7)]

        # Lagrange interpolation: find declination at given bhuja angle
        decl = _lagrange_interpolate(bhuja_angles, decl_values, bhuja)

        # Determine north/south sign based on planet and ecliptic hemisphere.
        # Per Surya Siddhanta / BPHS convention:
        # In northern hemisphere (0-180 tropical):
        #   Sun, Mars, Jupiter, Venus benefit (sign = +1)
        #   Others get sign = -1
        # In southern hemisphere (180-360 tropical):
        #   Moon, Saturn benefit (sign = +1)
        #   Others get sign = -1
        # Mercury always gets sign = +1
        p_idx = _PLANET_INDEX[planet]
        if trop_lon >= 0.0 and trop_lon < 180.0:
            north_south = -1
            if p_idx in [0, 2, 4, 5]:  # Sun, Mars, Jupiter, Venus
                north_south = 1
        else:
            north_south = -1
            if p_idx in [1, 6]:  # Moon, Saturn
                north_south = 1
        if p_idx == 3:  # Mercury always positive
            north_south = 1

        signed_decl = north_south * decl
    except Exception:
        signed_decl = 0.0

    ab = (24.0 + signed_decl) * 1.25
    if planet == Planet.SUN:
        ab *= 2.0
    return ab


def _lagrange_interpolate(x: list[float], y: list[float], xi: float) -> float:
    """Lagrange interpolation: given (x,y) data points, find y value at xi."""
    n = len(x)
    result = 0.0
    for i in range(n):
        term = y[i]
        for j in range(n):
            if i != j:
                if abs(x[i] - x[j]) < 1e-10:
                    continue
                term *= (xi - x[j]) / (x[i] - x[j])
        result += term
    return result


# ---------------------------------------------------------------------------
# 4. Chesta Bala (Motional Strength) — BPHS Ch. 27
# ---------------------------------------------------------------------------

def _chesta_bala(planet: Planet, chart: BirthChart) -> float:
    """Compute Chesta Bala based on the planet's chesta kendra.

    Sun and Moon always get 0 chesta bala (they have no retrograde motion).
    For other planets:
      1. Compute the planet's mean longitude using orbital period
      2. For superior planets (Mars, Jupiter, Saturn):
         sheeghrochcha = Sun's mean longitude
      3. For inferior planets (Mercury, Venus):
         sheeghrochcha = planet's mean longitude, mean = Sun's mean longitude
      4. chesta_kendra = |sheeghrochcha - average(true_long, mean_long)|
      5. chesta_bala = chesta_kendra / 3 (max 60)
    """
    # Sun and Moon: 0 chesta bala per BPHS
    if planet in (Planet.SUN, Planet.MOON):
        return 0.0

    dt = chart.birth_datetime
    ut_hour = (dt.hour + dt.minute / 60.0 + dt.second / 3600.0) - chart.timezone_offset
    jd = _to_julian_day(dt.year, dt.month, dt.day, ut_hour)

    # Get Sun's mean longitude
    sun_mean = _get_mean_longitude(jd, Planet.SUN)

    # Get planet's mean longitude
    planet_mean = _get_mean_longitude(jd, planet)

    # Determine sheeghrochcha and mean based on planet type
    if planet in (Planet.MERCURY, Planet.VENUS):
        # Inner planets: sheeghrochcha = planet's mean, mean = Sun's mean
        sheeghrochcha = planet_mean
        mean_long = sun_mean
    else:
        # Outer planets: sheeghrochcha = Sun's mean
        sheeghrochcha = sun_mean
        mean_long = planet_mean

    # True longitude
    true_long = chart.planets[planet].longitude

    # Average of true and mean longitude
    ave_long = 0.5 * (true_long + mean_long)

    # Reduced chesta kendra — note: per BPHS and PyJHora convention,
    # no 180-degree wrapping is applied. Chesta kendra can range 0-360,
    # giving chesta bala 0-120 Shashtiamsas.
    chesta_kendra = abs(sheeghrochcha - ave_long)

    return chesta_kendra / 3.0


def _get_mean_longitude(jd: float, planet: Planet) -> float:
    """Compute sidereal mean longitude using standard orbital elements.

    Uses tropical J2000.0 elements and subtracts the Lahiri ayanamsa
    to get sidereal mean longitudes (matching the convention used by
    PyJHora and classical texts like Surya Siddhanta).
    """
    if planet == Planet.MOON:
        return 0.0  # Moon has no chesta bala

    # J2000.0 epoch mean longitudes and daily motions (tropical)
    j2000 = 2451545.0  # Jan 1, 2000 12:00 UT
    d = jd - j2000  # days from J2000

    # Source: Meeus, Astronomical Algorithms / standard orbital elements
    _elements = {
        Planet.SUN: (280.4664567, 0.9856473354),
        Planet.MARS: (355.4533, 0.5240208),
        Planet.MERCURY: (252.2509, 4.0923388),
        Planet.JUPITER: (34.3515, 0.0831294),
        Planet.VENUS: (181.9798, 1.6021687),
        Planet.SATURN: (50.0774, 0.0334442),
    }

    if planet not in _elements:
        return 0.0

    l0, daily_motion = _elements[planet]
    tropical_mean = (l0 + daily_motion * d) % 360.0

    # Convert to sidereal by subtracting ayanamsa
    from vedic_calc.core.ephemeris import get_ayanamsa
    from vedic_calc.core.constants import Ayanamsa
    ayanamsa = get_ayanamsa(jd, Ayanamsa.LAHIRI)
    sidereal_mean = (tropical_mean - ayanamsa) % 360.0

    return sidereal_mean


# ---------------------------------------------------------------------------
# 5. Naisargika Bala (Natural Strength) — BPHS Ch. 27
# ---------------------------------------------------------------------------

def _naisargika_bala(planet: Planet) -> float:
    """Return the natural (inherent) strength from the constants table."""
    return NAISARGIKA_BALA[planet]


# ---------------------------------------------------------------------------
# 6. Drik Bala (Aspectual Strength) — BPHS Ch. 27
# ---------------------------------------------------------------------------

def _drik_bala(planet: Planet, chart: BirthChart) -> float:
    """Compute Drik Bala using longitude-based aspect strength.

    Per BPHS: Each planet's aspect on another is computed based on their
    angular distance. The aspect strength follows a slab-based formula
    (0-60 scale with special aspects for Mars, Jupiter, Saturn).
    Benefic aspects add, malefic aspects subtract. Total divided by 4.
    Result can be negative.
    """
    pos = chart.planets[planet]
    p_long = pos.longitude

    # Determine benefics and malefics for this chart
    # Use natural classification (simplified)
    sun_long = chart.planets[Planet.SUN].longitude
    moon_long = chart.planets[Planet.MOON].longitude
    tithi_angle = (moon_long - sun_long) % 360.0
    is_waxing = tithi_angle <= 180.0

    # Natural benefics: Jupiter, Venus, waxing Moon, unafflicted Mercury
    # Natural malefics: Sun, Mars, Saturn, waning Moon
    benefics = {Planet.JUPITER, Planet.VENUS}
    malefics = {Planet.SUN, Planet.MARS, Planet.SATURN}
    # Mercury: benefic when alone or with benefics (simplified: always benefic)
    benefics.add(Planet.MERCURY)
    if is_waxing:
        benefics.add(Planet.MOON)
    else:
        malefics.add(Planet.MOON)

    # Compute aspect strengths from all other planets onto this planet
    drik_positive = 0.0
    drik_negative = 0.0

    for other_planet in _SHADBALA_PLANETS:
        if other_planet == planet:
            continue
        other_pos = chart.planets[other_planet]
        other_long = other_pos.longitude

        # Angular distance: target - aspector (how far target is ahead of aspector)
        angle = (p_long - other_long + 360.0) % 360.0

        # Compute aspect strength using the slab formula
        aspect_value = _aspect_strength(angle, other_planet)

        if other_planet in benefics:
            drik_positive += aspect_value
        elif other_planet in malefics:
            drik_negative += aspect_value

    # Final drik bala = (benefic - malefic) / 4
    return (drik_positive - drik_negative) / 4.0


def _aspect_strength(angle: float, aspector: Planet) -> float:
    """Compute aspect strength based on angular distance using the slab formula.

    The aspect strength varies from 0 to 60 based on the angular distance
    between two planets. Special aspects (Mars 4th/8th, Jupiter 5th/9th,
    Saturn 3rd/10th) get bonus strength.

    Per BPHS and standard Drik Bala calculation (B.V. Raman's method).
    """
    a = angle

    if 0 <= a <= 30:
        value = 0.0
    elif 30 < a <= 60:
        value = 0.5 * (a - 30.0)
    elif 60 < a <= 90:
        value = (a - 60.0) + 15.0
        if aspector == Planet.SATURN:  # Saturn's 3rd house aspect (60-90 deg)
            value += 45.0
    elif 90 < a <= 120:
        value = 0.5 * (120.0 - a) + 30.0
        if aspector == Planet.MARS:  # Mars's 4th house aspect (90-120 deg)
            value += 15.0
    elif 120 < a <= 150:
        value = (150.0 - a)
        if aspector == Planet.JUPITER:  # Jupiter's 5th house aspect (120-150 deg)
            value += 30.0
    elif 150 < a <= 180:
        value = 2.0 * (a - 150.0)
    elif 180 < a <= 300:
        value = 0.5 * (300.0 - a)
        # Special aspects in the second half
        if aspector == Planet.MARS and 210 < a <= 240:  # Mars 8th aspect
            value += 15.0
        if aspector == Planet.JUPITER and 240 < a <= 270:  # Jupiter 9th aspect
            value += 30.0
        if aspector == Planet.SATURN and 270 < a <= 300:  # Saturn 10th aspect
            value += 45.0
    else:  # > 300
        value = 0.0

    return value


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def calculate_shadbala(chart: BirthChart) -> dict[Planet, ShadbalaResult]:
    """Calculate Shadbala (six-fold strength) for the seven visible planets.

    Shadbala quantifies a planet's total strength by summing six distinct
    components, each measuring a different dimension of planetary power.
    All values are in Shashtiamsas (1/60 Rupa).

    Only Sun through Saturn are computed; Rahu and Ketu are excluded
    from Shadbala per classical tradition.

    Args:
        chart: A fully computed BirthChart with planets and houses.

    Returns:
        A dictionary mapping each of the seven planets to its ShadbalaResult,
        containing the six component strengths, total, and is_strong flag.

    Example:
        >>> from vedic_calc.chart.calculator import calculate_chart
        >>> chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
        >>> results = calculate_shadbala(chart)
        >>> results[Planet.JUPITER].total
        345.28
        >>> results[Planet.JUPITER].is_strong
        True
    """
    results: dict[Planet, ShadbalaResult] = {}

    for planet in _SHADBALA_PLANETS:
        sthana = _sthana_bala(planet, chart)
        dig = _dig_bala(planet, chart)
        kaala = _kaala_bala(planet, chart)
        chesta = _chesta_bala(planet, chart)
        naisargika = _naisargika_bala(planet)
        drik = _drik_bala(planet, chart)

        total = sthana + dig + kaala + chesta + naisargika + drik

        # Per BPHS, the required minimum is per-planet (in Rupas = total/60)
        required_rupas = _REQUIRED_RUPAS[planet]
        is_strong = (total / 60.0) >= required_rupas

        results[planet] = ShadbalaResult(
            planet=planet,
            sthana_bala=round(sthana, 2),
            dig_bala=round(dig, 2),
            kaala_bala=round(kaala, 2),
            chesta_bala=round(chesta, 2),
            naisargika_bala=round(naisargika, 2),
            drik_bala=round(drik, 2),
            total=round(total, 2),
            is_strong=is_strong,
        )

    return results
