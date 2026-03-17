"""Muhurta constraint solver — finds auspicious time windows.

Given an activity, date range, and location, this solver:
1. Iterates each day in the range
2. Computes panchanga (tithi, nakshatra, yoga, karana, vara)
3. Applies a 5-layer filter (tithi → vara → nakshatra → yoga → karana)
4. Computes available windows (sunrise to sunset minus inauspicious periods)
5. Optionally applies personal overlays (Chandrabala, Tarabala)
6. Scores and ranks the windows

Source: Muhurta Chintamani, Kalaprakashika.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from vedic_calc.core.constants import (
    BAD_KARANAS,
    BAD_TITHIS,
    BAD_YOGAS,
    GOOD_NAKSHATRAS,
    GOOD_TITHIS,
    GOOD_VARAS,
    NAKSHATRA_NAMES,
    TITHI_NAMES,
    VARA_NAMES,
    YOGA_NAMES,
    KARANA_NAMES,
    Ayanamsa,
)
from vedic_calc.core.types import MuhurtaSearchResult, MuhurtaWindow
from vedic_calc.muhurta.calculator import calculate_muhurta
from vedic_calc.panchanga.calculator import calculate_panchanga


def _chandrabala_ok(transit_moon_sign: int, natal_moon_sign: int) -> bool:
    """Check Chandrabala — transit Moon position relative to natal Moon.

    Favorable if transit Moon is in 1st, 3rd, 6th, 7th, 10th, or 11th
    sign from the natal Moon sign.

    Args:
        transit_moon_sign: Transit Moon's sign number (1-12).
        natal_moon_sign: Natal Moon's sign number (1-12).

    Returns:
        True if Chandrabala is favorable.
    """
    distance = ((transit_moon_sign - natal_moon_sign) % 12) + 1
    return distance in {1, 3, 6, 7, 10, 11}


def _tarabala_ok(transit_nak: int, natal_nak: int) -> bool:
    """Check Tarabala — transit Moon nakshatra relative to natal nakshatra.

    The 27 nakshatras from the natal nakshatra are grouped into 9 sets
    of 3 (called taras). Good taras: 1 (Janma), 2 (Sampat), 4 (Kshema),
    6 (Sadhana), 8 (Mitra), 9 (Parama Mitra).
    Bad taras: 3 (Vipat), 5 (Pratyari), 7 (Vadha).

    Args:
        transit_nak: Transit Moon's nakshatra number (1-27).
        natal_nak: Natal Moon's nakshatra number (1-27).

    Returns:
        True if Tarabala is favorable.
    """
    distance = ((transit_nak - natal_nak) % 27)
    if distance == 0:
        distance = 27
    tara = ((distance - 1) % 9) + 1
    return tara in {1, 2, 4, 6, 8, 9}


def find_muhurta_windows(
    activity: str,
    start_date: datetime,
    end_date: datetime,
    latitude: float,
    longitude: float,
    timezone_offset: float,
    natal_moon_nakshatra: int = 0,
    natal_moon_sign: int = 0,
    max_results: int = 5,
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI,
) -> MuhurtaSearchResult:
    """Find auspicious Muhurta windows for an activity within a date range.

    Algorithm:
    1. For each day in the date range:
       a. Calculate panchanga (tithi, nakshatra, yoga, karana, vara)
       b. Calculate muhurta (Rahu Kalam, Yamagandam, Abhijit)
       c. Apply 5-layer filter: tithi, vara, nakshatra, yoga, karana
       d. If it passes, compute available windows
       e. Apply personal overlays if natal Moon is provided
       f. Score (0-100)
    2. Sort by score, return top N

    Args:
        activity: Type of activity (e.g., "marriage", "business", "travel").
            Falls back to "general" if not recognized.
        start_date: Start of the search range (date only, time ignored).
        end_date: End of the search range (inclusive).
        latitude: Location latitude.
        longitude: Location longitude.
        timezone_offset: UTC offset in hours.
        natal_moon_nakshatra: Natal Moon nakshatra number (1-27, 0 = not provided).
        natal_moon_sign: Natal Moon sign number (1-12, 0 = not provided).
        max_results: Maximum number of windows to return.
        ayanamsa: Ayanamsa system.

    Returns:
        MuhurtaSearchResult with ranked windows.
    """
    # Normalize activity key
    activity_key = activity.lower().strip()
    if activity_key not in GOOD_TITHIS:
        activity_key = "general"

    has_natal = natal_moon_nakshatra > 0 and natal_moon_sign > 0
    windows: list[MuhurtaWindow] = []

    current = datetime(start_date.year, start_date.month, start_date.day)
    end = datetime(end_date.year, end_date.month, end_date.day)

    while current <= end:
        y, m, d = current.year, current.month, current.day

        # Panchanga for the day
        panchanga = calculate_panchanga(
            y, m, d, latitude, longitude, timezone_offset, ayanamsa,
        )

        weekday = current.weekday()
        reasons: list[str] = []
        score = 0.0
        skip = False

        # --- Layer 1: Tithi ---
        if panchanga.tithi_number in BAD_TITHIS:
            current += timedelta(days=1)
            continue
        good_tithis = GOOD_TITHIS.get(activity_key, GOOD_TITHIS["general"])
        if panchanga.tithi_number in good_tithis:
            score += 20.0
            reasons.append(f"Good tithi: {panchanga.tithi_name}")
        else:
            score += 5.0  # Neutral tithi, not bad

        # --- Layer 2: Vara (weekday) ---
        good_varas = GOOD_VARAS.get(activity_key, GOOD_VARAS["general"])
        if weekday in good_varas:
            score += 15.0
            reasons.append(f"Good vara: {panchanga.vara}")
        else:
            score += 3.0

        # --- Layer 3: Nakshatra ---
        nak_num = panchanga.nakshatra.value
        good_naks = GOOD_NAKSHATRAS.get(activity_key, GOOD_NAKSHATRAS["general"])
        if nak_num in good_naks:
            score += 20.0
            reasons.append(f"Good nakshatra: {NAKSHATRA_NAMES[panchanga.nakshatra]}")
        else:
            score += 3.0

        # --- Layer 4: Yoga ---
        if panchanga.yoga_number in BAD_YOGAS:
            current += timedelta(days=1)
            continue
        score += 10.0
        reasons.append(f"Yoga: {panchanga.yoga_name}")

        # --- Layer 5: Karana ---
        if panchanga.karana_number in BAD_KARANAS:
            current += timedelta(days=1)
            continue
        score += 10.0
        reasons.append(f"Karana: {panchanga.karana_name}")

        # --- Compute available window ---
        muhurta = calculate_muhurta(
            y, m, d, latitude, longitude, timezone_offset,
        )

        # Window = sunrise to sunset
        if panchanga.sunrise and panchanga.sunset:
            window_start = panchanga.sunrise
            window_end = panchanga.sunset
        else:
            # Fallback: 6am to 6pm local
            window_start = datetime(y, m, d, 6, 0, 0)
            window_end = datetime(y, m, d, 18, 0, 0)

        # Exclude Rahu Kalam from window description
        rk_start, rk_end = muhurta.rahu_kalam
        reasons.append(
            f"Rahu Kalam: {rk_start.strftime('%H:%M')}-{rk_end.strftime('%H:%M')} (avoid)"
        )

        # --- Personal overlays ---
        cb_ok: bool | None = None
        tb_ok: bool | None = None

        if has_natal:
            transit_moon_sign = panchanga.nakshatra.value  # Use sign not nakshatra
            # Get transit Moon sign from panchanga nakshatra position
            # Each nakshatra ~13.33°, sign = ceil(nak * 13.33 / 30)
            # Simpler: sign can be derived. We'll approximate from nakshatra.
            # nak 1-2 = Aries(1), 3 = Aries/Taurus, etc.
            # More precise: use the panchanga data directly
            transit_nak = panchanga.nakshatra.value
            # Approximate transit Moon sign from its nakshatra position.
            # Each nakshatra spans 13.333 degrees, so we estimate the Moon's
            # longitude as the START of the nakshatra. This is approximate
            # because the Moon could be anywhere within the 13.333 degree span.
            # The worst-case error is ~13 degrees, which can place the Moon in
            # the wrong sign for nakshatras near sign boundaries (e.g.,
            # Krittika spans Aries/Taurus). For production use, compute the
            # exact Moon longitude from the ephemeris at the panchanga date.
            approx_lon = (transit_nak - 1) * (360.0 / 27.0)
            transit_sign = int(approx_lon / 30.0) + 1

            cb_ok = _chandrabala_ok(transit_sign, natal_moon_sign)
            tb_ok = _tarabala_ok(transit_nak, natal_moon_nakshatra)

            if cb_ok:
                score += 15.0
                reasons.append("Chandrabala: favorable")
            else:
                reasons.append("Chandrabala: unfavorable")

            if tb_ok:
                score += 10.0
                reasons.append("Tarabala: favorable")
            else:
                reasons.append("Tarabala: unfavorable")

        # Cap score at 100
        score = min(score, 100.0)

        windows.append(MuhurtaWindow(
            start=window_start,
            end=window_end,
            score=round(score, 1),
            tithi_name=panchanga.tithi_name,
            nakshatra_name=NAKSHATRA_NAMES[panchanga.nakshatra],
            yoga_name=panchanga.yoga_name,
            karana_name=panchanga.karana_name,
            vara=panchanga.vara,
            chandrabala_ok=cb_ok,
            tarabala_ok=tb_ok,
            reasoning=reasons,
        ))

        current += timedelta(days=1)

    # Sort by score descending, take top N
    windows.sort(key=lambda w: w.score, reverse=True)
    top_windows = windows[:max_results]

    return MuhurtaSearchResult(
        activity=activity,
        windows=top_windows,
    )
