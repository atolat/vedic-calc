"""
KP Placidus house cusp calculation.

KP astrology uses the Placidus house system instead of the whole-sign
system used in traditional Vedic (Parashari) astrology. Placidus cusps
are unequal and depend on birth latitude/longitude.

The Swiss Ephemeris provides Placidus cusps via swe.houses(). We then
apply the ayanamsa correction to get sidereal cusps, and compute
KP sub-lord information for each cusp.
"""

from __future__ import annotations

import swisseph as swe

from vedic_calc.core.constants import Sign, SIGN_LORDS
from vedic_calc.core.types import KPHouseCusp
from vedic_calc.kp.sublords import get_kp_sublord


def calculate_kp_houses(
    jd: float, latitude: float, longitude: float, ayanamsa_value: float
) -> list[KPHouseCusp]:
    """Calculate Placidus house cusps with KP sub-lord info.

    Uses the Swiss Ephemeris to compute Placidus house cusps (tropical),
    then subtracts the ayanamsa to convert to sidereal, and computes
    KP sub-lord information for each cusp.

    Args:
        jd: Julian Day number (in UT).
        latitude: Geographic latitude in degrees (north positive).
        longitude: Geographic longitude in degrees (east positive).
        ayanamsa_value: The ayanamsa value in degrees for sidereal correction.

    Returns:
        List of 12 KPHouseCusp objects (houses 1-12).
    """
    # swe.houses returns (cusps, ascmc)
    # cusps is a tuple of 13 values: cusps[0] is unused, cusps[1]-cusps[12] are houses 1-12
    # house system b'P' = Placidus
    cusps_tuple, _ascmc = swe.houses(jd, latitude, longitude, b'P')

    house_cusps: list[KPHouseCusp] = []
    for i in range(12):
        # cusps_tuple[i] for i=0..11 corresponds to houses 1..12
        tropical_cusp = cusps_tuple[i]
        sidereal_cusp = (tropical_cusp - ayanamsa_value) % 360.0

        # Get KP sub-lord info for this cusp longitude
        kp_info = get_kp_sublord(sidereal_cusp)

        house_cusps.append(KPHouseCusp(
            house_number=i + 1,
            cusp_longitude=round(sidereal_cusp, 4),
            sign=kp_info.sign,
            sign_lord=kp_info.sign_lord,
            star_lord=kp_info.star_lord,
            sub_lord=kp_info.sub_lord,
        ))

    return house_cusps
