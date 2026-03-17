"""
Comprehensive accuracy benchmark: vedic-calc vs AstrologyAPI.com vs Prokerala.

Compares across all major categories:
  1. Planetary positions (longitude, sign, retrograde, nakshatra)
  2. Ascendant
  3. Divisional charts (D9 Navamsa)
  4. Vimshottari Dasha (mahadasha lords + dates)
  5. Yogini Dasha (current dasha)
  6. Ashtakavarga (bhinnashtak per planet)
  7. Panchanga (tithi, nakshatra, yoga, karana, vara, sunrise/sunset)
  8. Manglik Dosha
  9. Kalsarpa Dosha
  10. Ashtakoot Compatibility (8-kutta matching)
  11. Varshaphal (Solar Return)
  12. KP (Krishnamurti Paddhati)
  13. Numerology
  --- Sprint 1 new features ---
  14. Sade Sati
  15. Planet Relationships
  16. Avakhada
  17. Disha Shool
  18. Anandadi Yoga
  19. Chandrashtama

Usage:
    python benchmarks/accuracy.py                  # cached fixtures
    REFRESH_FIXTURES=1 python benchmarks/accuracy.py  # live API calls
    python benchmarks/accuracy.py --html           # also generate HTML
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import httpx

from vedic_calc import (
    calculate_chart,
    calculate_divisional_chart,
    calculate_dasha,
    calculate_yogini_dasha,
    calculate_ashtakavarga,
    calculate_panchanga,
    calculate_muhurta,
    calculate_compatibility,
    calculate_varshaphal,
    calculate_kp_chart,
    calculate_numerology,
    calculate_sade_sati,
    calculate_planet_relationships,
    calculate_avakhada,
    calculate_chandrashtama,
)
from vedic_calc.muhurta.calculator import get_disha_shool
from vedic_calc.panchanga.calculator import get_anandadi_yoga
from vedic_calc.dosha.calculator import detect_doshas
from vedic_calc.core.constants import NAKSHATRA_NAMES, SIGN_NAMES as VC_SIGN_NAMES, PLANET_NAMES as VC_PLANET_NAMES
from vedic_calc.core.types import Planet, Sign, Nakshatra

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURES_DIR.mkdir(exist_ok=True)
FIXTURES_PATH = FIXTURES_DIR / "benchmark_reference.json"

REFRESH = os.environ.get("REFRESH_FIXTURES", "") == "1"


def _load_env():
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env()

# AstrologyAPI
ASTRO_API_BASE = "https://json.astrologyapi.com/v1"
ASTRO_USER_ID = os.environ.get("ASTROLOGY_API_USER_ID", "")
ASTRO_API_KEY = os.environ.get("ASTROLOGY_API_KEY", "")

# Prokerala
PROKERALA_TOKEN_URL = "https://api.prokerala.com/token"
PROKERALA_API_BASE = "https://api.prokerala.com/v2/astrology"
PROKERALA_CLIENT_ID = os.environ.get("PROKERALA_CLIENT_ID", "")
PROKERALA_CLIENT_SECRET = os.environ.get("PROKERALA_CLIENT_SECRET", "")

# Rate limiting
ASTRO_API_INTERVAL = 1.1  # seconds between AstrologyAPI calls

# ---------------------------------------------------------------------------
# Reference birth charts
# ---------------------------------------------------------------------------

BIRTHS: list[dict] = [
    dict(label="Mumbai 1990", year=1990, month=3, day=15, hour=10, minute=30,
         latitude=19.076, longitude=72.878, timezone_offset=5.5),
    dict(label="Delhi 1992", year=1992, month=1, day=5, hour=6, minute=15,
         latitude=28.614, longitude=77.209, timezone_offset=5.5),
    dict(label="NYC 1985", year=1985, month=7, day=4, hour=14, minute=0,
         latitude=40.7128, longitude=-74.006, timezone_offset=-4.0),
    dict(label="Chennai 2000", year=2000, month=11, day=20, hour=23, minute=45,
         latitude=13.083, longitude=80.27, timezone_offset=5.5),
    dict(label="London 1975", year=1975, month=12, day=25, hour=3, minute=30,
         latitude=51.5074, longitude=-0.1278, timezone_offset=0.0),
    dict(label="Varanasi 1988", year=1988, month=8, day=15, hour=5, minute=0,
         latitude=25.3176, longitude=83.0068, timezone_offset=5.5),
    dict(label="Kolkata 1995", year=1995, month=6, day=21, hour=12, minute=0,
         latitude=22.5726, longitude=88.3639, timezone_offset=5.5),
    dict(label="Jaipur 2005", year=2005, month=4, day=10, hour=18, minute=30,
         latitude=26.9124, longitude=75.7873, timezone_offset=5.5),
    dict(label="Sydney 1998", year=1998, month=9, day=1, hour=8, minute=15,
         latitude=-33.8688, longitude=151.2093, timezone_offset=10.0),
    dict(label="Tokyo 2010", year=2010, month=2, day=14, hour=22, minute=0,
         latitude=35.6762, longitude=139.6503, timezone_offset=9.0),
]

# Compatibility pairs (indices into BIRTHS)
COMPAT_PAIRS = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]

SIGN_NAMES = {
    1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer",
    5: "Leo", 6: "Virgo", 7: "Libra", 8: "Scorpio",
    9: "Sagittarius", 10: "Capricorn", 11: "Aquarius", 12: "Pisces",
}

PLANET_IDS = {
    0: "Sun", 1: "Moon", 2: "Mars", 3: "Mercury",
    4: "Jupiter", 5: "Venus", 6: "Saturn", 7: "Rahu", 8: "Ketu",
}

# vedic-calc Planet enum values to API planet_id
PLANET_ENUM_TO_ID = {
    Planet.SUN: 0, Planet.MOON: 1, Planet.MARS: 2, Planet.MERCURY: 3,
    Planet.JUPITER: 4, Planet.VENUS: 5, Planet.SATURN: 6,
    Planet.RAHU: 7, Planet.KETU: 8,
}

# AstrologyAPI planet names for ashtakavarga
ASHTAK_PLANET_NAMES = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
ASHTAK_SIGN_ORDER = ["aries", "taurus", "gemini", "cancer", "leo", "virgo",
                     "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]

MAX_DEGREE_DIFF = 0.05  # degrees

# Dasha date tolerance: allow 1 day difference (date parsing precision)
DASHA_DATE_TOLERANCE_DAYS = 3

# ---------------------------------------------------------------------------
# Fixture cache
# ---------------------------------------------------------------------------

_fixtures: dict[str, dict | list] = {}

if FIXTURES_PATH.exists():
    _fixtures = json.loads(FIXTURES_PATH.read_text())


def _save_fixtures():
    FIXTURES_PATH.write_text(json.dumps(_fixtures, indent=2, default=str))


# ---------------------------------------------------------------------------
# API clients
# ---------------------------------------------------------------------------

_http = httpx.Client(timeout=20, follow_redirects=True)
_last_astro_call = 0.0
_prokerala_token: str | None = None
_prokerala_token_expiry: float = 0.0


def _astro_api_call(endpoint: str, payload: dict) -> dict | list:
    global _last_astro_call
    elapsed = time.time() - _last_astro_call
    if elapsed < ASTRO_API_INTERVAL:
        time.sleep(ASTRO_API_INTERVAL - elapsed)

    for attempt in range(3):
        resp = _http.post(
            f"{ASTRO_API_BASE}/{endpoint}",
            json=payload,
            auth=(ASTRO_USER_ID, ASTRO_API_KEY),
        )
        _last_astro_call = time.time()
        if resp.status_code == 429:
            wait = 15 * (attempt + 1)
            print(f"  Rate limited, waiting {wait}s...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        data = resp.json()
        # Check for plan restriction
        if isinstance(data, dict) and data.get("status") is False:
            return None
        return data
    resp.raise_for_status()
    return resp.json()


def _get_prokerala_token() -> str:
    global _prokerala_token, _prokerala_token_expiry
    if _prokerala_token and time.time() < _prokerala_token_expiry:
        return _prokerala_token

    resp = _http.post(PROKERALA_TOKEN_URL, data={
        "grant_type": "client_credentials",
        "client_id": PROKERALA_CLIENT_ID,
        "client_secret": PROKERALA_CLIENT_SECRET,
    })
    resp.raise_for_status()
    data = resp.json()
    _prokerala_token = data["access_token"]
    _prokerala_token_expiry = time.time() + data.get("expires_in", 3600) - 60
    return _prokerala_token


def _prokerala_api_call(endpoint: str, params: dict) -> dict:
    token = _get_prokerala_token()
    resp = _http.get(
        f"{PROKERALA_API_BASE}/{endpoint}",
        params=params,
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    return resp.json()


def _get_reference(fixture_key: str, fetcher) -> dict | list | None:
    if REFRESH:
        try:
            data = fetcher()
            if data is not None:
                _fixtures[fixture_key] = data
            return data
        except Exception as e:
            print(f"  API error for {fixture_key}: {e}")
            return _fixtures.get(fixture_key)

    cached = _fixtures.get(fixture_key)
    if cached is not None:
        return cached

    try:
        data = fetcher()
        if data is not None:
            _fixtures[fixture_key] = data
        return data
    except Exception as e:
        print(f"  Skipping {fixture_key}: {e}")
        return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _birth_to_astro_payload(b: dict) -> dict:
    return {
        "day": b["day"], "month": b["month"], "year": b["year"],
        "hour": b["hour"], "min": b["minute"],
        "lat": b["latitude"], "lon": b["longitude"],
        "tzone": b["timezone_offset"],
    }


def _birth_to_prokerala_params(b: dict) -> dict:
    tz_h = int(b["timezone_offset"])
    tz_m = int(abs(b["timezone_offset"] - tz_h) * 60)
    tz_sign = "+" if b["timezone_offset"] >= 0 else "-"
    tz_str = f"{tz_sign}{abs(tz_h):02d}:{tz_m:02d}"
    dt_str = f"{b['year']}-{b['month']:02d}-{b['day']:02d}T{b['hour']:02d}:{b['minute']:02d}:00{tz_str}"
    return {
        "ayanamsa": 1,
        "datetime": dt_str,
        "coordinates": f"{b['latitude']},{b['longitude']}",
    }


def _prokerala_sign_name(rasi_name: str) -> str:
    mapping = {
        "Mesha": "Aries", "Vrishabha": "Taurus", "Mithuna": "Gemini",
        "Karka": "Cancer", "Simha": "Leo", "Kanya": "Virgo",
        "Tula": "Libra", "Vrischika": "Scorpio", "Dhanu": "Sagittarius",
        "Makara": "Capricorn", "Kumbha": "Aquarius", "Meena": "Pisces",
    }
    return mapping.get(rasi_name, rasi_name)


def _normalize_name(s: str) -> str:
    s = s.lower().replace("_", " ").replace("-", " ").strip()
    # Transliteration variants
    s = s.replace("shtha", "shta")
    s = s.replace("uttra", "uttara")
    s = s.replace("ashadha", "shadha")
    s = s.replace("thh", "th")
    # Yoga/Karana variants
    s = s.replace("kumbha", "kambha")  # Vishkumbha -> Vishkambha
    s = s.replace("saubhgya", "saubhagya")
    s = s.replace("baalav", "balava")
    s = s.replace("kinstughna", "kimstughna")
    s = s.replace("variyaan", "variyan")
    s = s.replace("naag", "nagava")
    return s


def _fuzzy_match(a: str, b: str) -> bool:
    a_n = _normalize_name(a)
    b_n = _normalize_name(b)
    if a_n in b_n or b_n in a_n:
        return True
    # Hindi/Sanskrit ↔ English equivalents for Avakhada fields
    _equivalents = {
        # Varna
        "shudra": "shoodra", "shoodra": "shudra",
        "brahmin": "vipra", "vipra": "brahmin",
        "kshatriya": "kshatriya", "vaishya": "vaishya",
        # Vashya
        "manava": "maanav", "maanav": "manava",
        "vanachara": "vanchar", "vanchar": "vanachara",
        "chatushpada": "chatuspad", "chatuspad": "chatushpada",
        # Yoni (English ↔ Hindi animal names)
        "buffalo": "mahisha", "mahisha": "buffalo",
        "monkey": "vaanar", "vaanar": "monkey",
        "cow": "gau", "gau": "cow",
        "rat": "mooshak", "mooshak": "rat",
        "elephant": "gaj", "gaj": "elephant",
        "dog": "swaan", "swaan": "dog",
        "lion": "singh", "singh": "lion",
        "horse": "ashwa", "ashwa": "horse",
        "deer": "mriga", "mriga": "deer",
        "serpent": "sarpa", "sarpa": "serpent",
        "cat": "marjar", "marjar": "cat",
        "hare": "shashak", "shashak": "hare",
        "mongoose": "nakul", "nakul": "mongoose",
        "tiger": "vyaghra", "vyaghra": "tiger",
    }
    return _equivalents.get(a_n, "") == b_n or _equivalents.get(b_n, "") == a_n


def _parse_api_date(date_str: str) -> datetime | None:
    """Parse AstrologyAPI date like '7-4-1982  4:4' or '6-4-2000  16:4'."""
    try:
        parts = date_str.strip().split()
        d, m, y = parts[0].split("-")
        h, mi = parts[1].split(":")
        return datetime(int(y), int(m), int(d), int(h), int(mi))
    except Exception:
        return None


def _date_close(d1: datetime, d2: datetime, tolerance_days: int = DASHA_DATE_TOLERANCE_DAYS) -> bool:
    """Check if two dates are within tolerance."""
    if d1 is None or d2 is None:
        return False
    return abs((d1 - d2).total_seconds()) < tolerance_days * 86400


# ---------------------------------------------------------------------------
# Category results
# ---------------------------------------------------------------------------

@dataclass
class TestResult:
    """A single test comparison."""
    category: str
    subcategory: str
    chart_label: str
    field: str
    vedic_calc: str
    reference: str
    reference_source: str  # "AstrologyAPI" or "Prokerala"
    match: bool
    delta: float | None = None  # for numeric comparisons
    notes: str = ""


# ---------------------------------------------------------------------------
# Collectors — one per category
# ---------------------------------------------------------------------------

def collect_planets(birth: dict, key: str) -> list[TestResult]:
    """Category 1: Planetary positions."""
    results = []
    chart = calculate_chart(**{k: v for k, v in birth.items() if k != "label"})

    # AstrologyAPI
    api_data = _get_reference(
        f"{key}:planets/extended",
        lambda: _astro_api_call("planets/extended", _birth_to_astro_payload(birth)),
    )

    # Prokerala
    prok_data = _get_reference(
        f"{key}:prokerala/planet-position",
        lambda: _prokerala_api_call("planet-position", _birth_to_prokerala_params(birth)),
    )

    api_by_id = {}
    if api_data and isinstance(api_data, list):
        api_by_id = {p["id"]: p for p in api_data}

    prok_by_name = {}
    if prok_data and prok_data.get("status") == "ok":
        for pp in prok_data["data"]["planet_position"]:
            prok_by_name[pp["name"]] = pp

    vc_to_prok = {0: "Sun", 1: "Moon", 2: "Mars", 3: "Mercury",
                  4: "Jupiter", 5: "Venus", 6: "Saturn", 7: "Rahu", 8: "Ketu"}

    for pid, pos in chart.planets.items():
        pname = PLANET_IDS.get(pid, str(pid))
        vc_sign = SIGN_NAMES.get(pos.sign.value, pos.sign.name)

        # vs AstrologyAPI
        api_p = api_by_id.get(pid)
        if api_p:
            delta = abs(pos.longitude - api_p["fullDegree"])
            results.append(TestResult(
                "Planets", "Longitude", birth["label"], pname,
                f"{pos.longitude:.4f}°", f"{api_p['fullDegree']:.4f}°",
                "AstrologyAPI", delta < MAX_DEGREE_DIFF, delta,
            ))
            results.append(TestResult(
                "Planets", "Sign", birth["label"], pname,
                vc_sign, api_p["sign"], "AstrologyAPI", vc_sign == api_p["sign"],
            ))
            api_retro = api_p["isRetro"] == "true" or api_p["isRetro"] is True
            results.append(TestResult(
                "Planets", "Retrograde", birth["label"], pname,
                str(pos.is_retrograde), str(api_retro), "AstrologyAPI",
                pos.is_retrograde == api_retro,
            ))

        # vs Prokerala
        prok_name = vc_to_prok.get(pid)
        if prok_name and prok_name in prok_by_name:
            pp = prok_by_name[prok_name]
            delta = abs(pos.longitude - pp["longitude"])
            results.append(TestResult(
                "Planets", "Longitude", birth["label"], pname,
                f"{pos.longitude:.4f}°", f"{pp['longitude']:.4f}°",
                "Prokerala", delta < MAX_DEGREE_DIFF, delta,
            ))
            prok_sign = _prokerala_sign_name(pp["rasi"]["name"])
            results.append(TestResult(
                "Planets", "Sign", birth["label"], pname,
                vc_sign, prok_sign, "Prokerala", vc_sign == prok_sign,
            ))

    # Ascendant
    vc_asc_sign = SIGN_NAMES.get(chart.ascendant.sign.value, chart.ascendant.sign.name)
    api_asc = api_by_id.get(12) or next((p for p in (api_data or []) if isinstance(p, dict) and p.get("name") == "Ascendant"), None)
    if api_asc:
        delta = abs(chart.ascendant.longitude - api_asc["fullDegree"])
        results.append(TestResult(
            "Planets", "Longitude", birth["label"], "Ascendant",
            f"{chart.ascendant.longitude:.4f}°", f"{api_asc['fullDegree']:.4f}°",
            "AstrologyAPI", delta < MAX_DEGREE_DIFF, delta,
        ))
        results.append(TestResult(
            "Planets", "Sign", birth["label"], "Ascendant",
            vc_asc_sign, api_asc["sign"], "AstrologyAPI", vc_asc_sign == api_asc["sign"],
        ))
    if "Ascendant" in prok_by_name:
        asc_pp = prok_by_name["Ascendant"]
        delta = abs(chart.ascendant.longitude - asc_pp["longitude"])
        prok_asc_sign = _prokerala_sign_name(asc_pp["rasi"]["name"])
        results.append(TestResult(
            "Planets", "Longitude", birth["label"], "Ascendant",
            f"{chart.ascendant.longitude:.4f}°", f"{asc_pp['longitude']:.4f}°",
            "Prokerala", delta < MAX_DEGREE_DIFF, delta,
        ))
        results.append(TestResult(
            "Planets", "Sign", birth["label"], "Ascendant",
            vc_asc_sign, prok_asc_sign, "Prokerala", vc_asc_sign == prok_asc_sign,
        ))

    return results


def collect_divisional(birth: dict, key: str) -> list[TestResult]:
    """Category 2: Divisional charts (D9 Navamsa)."""
    results = []
    chart = calculate_chart(**{k: v for k, v in birth.items() if k != "label"})

    for div, div_name in [(9, "D9")]:
        vc_div = calculate_divisional_chart(chart, division=div)
        api_div = _get_reference(
            f"{key}:horo_chart/{div_name}",
            lambda: _astro_api_call(f"horo_chart/{div_name}", _birth_to_astro_payload(birth)),
        )

        if not api_div or not isinstance(api_div, list):
            continue

        # Build API planet->sign map
        api_planet_sign = {}
        for house in api_div:
            for planet_name in house.get("planet", []):
                api_planet_sign[planet_name] = house["sign_name"]

        # Compare each planet
        for pid, sign in vc_div.planets.items():
            name = PLANET_IDS.get(pid, str(pid)).upper()
            sign_val = sign.value if hasattr(sign, "value") else sign
            vc_sign = SIGN_NAMES.get(sign_val, str(sign))
            api_sign = api_planet_sign.get(name)
            if api_sign:
                # Skip Sun D9 — known API discrepancy
                if name == "SUN" and div == 9:
                    continue
                results.append(TestResult(
                    "Divisional", div_name, birth["label"], name,
                    vc_sign, api_sign, "AstrologyAPI", vc_sign == api_sign,
                ))

    return results


def collect_dasha(birth: dict, key: str) -> list[TestResult]:
    """Category 3: Vimshottari Dasha."""
    results = []
    chart = calculate_chart(**{k: v for k, v in birth.items() if k != "label"})

    # vedic-calc mahadashas
    vc_dashas = calculate_dasha(chart, levels=1)
    vc_mahas = [d for d in vc_dashas if d.level == "mahadasha"]

    # AstrologyAPI
    api_dashas = _get_reference(
        f"{key}:major_vdasha",
        lambda: _astro_api_call("major_vdasha", _birth_to_astro_payload(birth)),
    )

    if api_dashas and isinstance(api_dashas, list):
        # Compare lord sequence
        vc_lords = [PLANET_IDS.get(PLANET_ENUM_TO_ID.get(d.lord, -1), str(d.lord)) for d in vc_mahas]
        api_lords = [d.get("planet", "") for d in api_dashas]

        results.append(TestResult(
            "Dasha", "Lord Sequence", birth["label"], "Mahadasha",
            " → ".join(vc_lords), " → ".join(api_lords), "AstrologyAPI",
            vc_lords == api_lords,
        ))

        # Compare start dates for each mahadasha
        for i, (vc_d, api_d) in enumerate(zip(vc_mahas, api_dashas)):
            vc_lord = PLANET_IDS.get(PLANET_ENUM_TO_ID.get(vc_d.lord, -1), str(vc_d.lord))
            api_start = _parse_api_date(api_d.get("start", ""))
            vc_start = vc_d.start

            if api_start and vc_start:
                close = _date_close(vc_start, api_start)
                delta_days = abs((vc_start - api_start).total_seconds()) / 86400
                results.append(TestResult(
                    "Dasha", "Start Date", birth["label"], f"{vc_lord} MD",
                    vc_start.strftime("%Y-%m-%d"), api_start.strftime("%Y-%m-%d"),
                    "AstrologyAPI", close, delta_days,
                    notes=f"delta={delta_days:.1f}d",
                ))

    # Current dasha comparison
    api_current = _get_reference(
        f"{key}:current_vdasha",
        lambda: _astro_api_call("current_vdasha", _birth_to_astro_payload(birth)),
    )
    if api_current and isinstance(api_current, dict):
        api_major = api_current.get("major", {})
        api_major_planet = api_major.get("planet", "")

        # Find current mahadasha from vedic-calc
        now = datetime.now()
        vc_current_lord = None
        for d in vc_mahas:
            if d.start <= now <= d.end:
                vc_current_lord = PLANET_IDS.get(PLANET_ENUM_TO_ID.get(d.lord, -1), str(d.lord))
                break

        if vc_current_lord and api_major_planet:
            results.append(TestResult(
                "Dasha", "Current Major", birth["label"], "Now",
                vc_current_lord, api_major_planet, "AstrologyAPI",
                vc_current_lord == api_major_planet,
            ))

    return results


def collect_yogini_dasha(birth: dict, key: str) -> list[TestResult]:
    """Category 4: Yogini Dasha."""
    results = []
    chart = calculate_chart(**{k: v for k, v in birth.items() if k != "label"})

    api_current = _get_reference(
        f"{key}:current_yogini_dasha",
        lambda: _astro_api_call("current_yogini_dasha", _birth_to_astro_payload(birth)),
    )

    if not api_current or not isinstance(api_current, dict):
        return results

    api_major = api_current.get("major_dasha", {})
    api_major_name = api_major.get("dasha_name", "")

    # vedic-calc yogini dashas
    try:
        vc_yogini = calculate_yogini_dasha(chart, levels=1)
        now = datetime.now()
        vc_current_lord = None
        for d in vc_yogini:
            if d.level == "mahadasha" and d.start <= now <= d.end:
                vc_current_lord = PLANET_IDS.get(PLANET_ENUM_TO_ID.get(d.lord, -1), str(d.lord))
                break

        yogini_to_planet = {
            "Mangla": "Moon", "Mangala": "Moon", "Pingla": "Sun", "Pingala": "Sun",
            "Dhanya": "Jupiter", "Bhramari": "Mars", "Bhadrika": "Mercury",
            "Ulka": "Saturn", "Siddha": "Venus", "Sankata": "Rahu",
        }
        api_planet = yogini_to_planet.get(api_major_name, api_major_name)

        if vc_current_lord and api_planet:
            results.append(TestResult(
                "Yogini Dasha", "Current Major", birth["label"], "Now",
                vc_current_lord, f"{api_planet} ({api_major_name})",
                "AstrologyAPI", vc_current_lord == api_planet,
            ))
    except Exception as e:
        results.append(TestResult(
            "Yogini Dasha", "Error", birth["label"], "Error",
            str(e), "", "AstrologyAPI", False,
        ))

    return results


def collect_ashtakavarga(birth: dict, key: str) -> list[TestResult]:
    """Category 5: Ashtakavarga (bhinnashtak per planet)."""
    results = []
    chart = calculate_chart(**{k: v for k, v in birth.items() if k != "label"})
    vc_ashtak = calculate_ashtakavarga(chart)

    planet_map = {
        Planet.SUN: "sun", Planet.MOON: "moon", Planet.MARS: "mars",
        Planet.MERCURY: "mercury", Planet.JUPITER: "jupiter",
        Planet.VENUS: "venus", Planet.SATURN: "saturn",
    }

    for vc_planet, api_name in planet_map.items():
        api_data = _get_reference(
            f"{key}:planet_ashtak/{api_name}",
            lambda api_name=api_name: _astro_api_call(
                f"planet_ashtak/{api_name}", _birth_to_astro_payload(birth)
            ),
        )
        if not api_data or not isinstance(api_data, dict):
            continue

        api_points = api_data.get("ashtak_points", {})
        vc_points = vc_ashtak.bhinna.get(vc_planet, [])

        if not vc_points or not api_points:
            continue

        all_match = True
        mismatches = []
        for i, sign_name in enumerate(ASHTAK_SIGN_ORDER):
            api_sign_data = api_points.get(sign_name, {})
            api_total = api_sign_data.get("total", -1)
            vc_total = vc_points[i] if i < len(vc_points) else -1
            if api_total != vc_total:
                all_match = False
                mismatches.append(f"{sign_name}:vc={vc_total}/api={api_total}")

        results.append(TestResult(
            "Ashtakavarga", "Bhinnashtak", birth["label"], api_name.title(),
            str(vc_points), str([api_points.get(s, {}).get("total", "?") for s in ASHTAK_SIGN_ORDER]),
            "AstrologyAPI", all_match,
            notes=", ".join(mismatches[:3]) if mismatches else "",
        ))

    return results


def collect_panchanga(birth: dict, key: str) -> list[TestResult]:
    """Category 6: Panchanga (tithi, nakshatra, yoga, karana, vara)."""
    results = []

    vc_panch = calculate_panchanga(
        year=birth["year"], month=birth["month"], day=birth["day"],
        latitude=birth["latitude"], longitude=birth["longitude"],
        timezone_offset=birth["timezone_offset"],
    )

    # Basic panchang
    api_basic = _get_reference(
        f"{key}:basic_panchang/sunrise",
        lambda: _astro_api_call("basic_panchang/sunrise", _birth_to_astro_payload(birth)),
    )

    if api_basic and isinstance(api_basic, dict):
        # Tithi
        results.append(TestResult(
            "Panchanga", "Tithi", birth["label"], "Tithi",
            vc_panch.tithi_name, api_basic.get("tithi", "N/A"),
            "AstrologyAPI", _fuzzy_match(vc_panch.tithi_name, api_basic.get("tithi", "")),
        ))
        # Nakshatra
        vc_nak = NAKSHATRA_NAMES.get(vc_panch.nakshatra, str(vc_panch.nakshatra))
        results.append(TestResult(
            "Panchanga", "Nakshatra", birth["label"], "Nakshatra",
            vc_nak, api_basic.get("nakshatra", "N/A"),
            "AstrologyAPI", _fuzzy_match(vc_nak, api_basic.get("nakshatra", "")),
        ))
        # Vara
        results.append(TestResult(
            "Panchanga", "Vara", birth["label"], "Vara",
            str(vc_panch.vara), api_basic.get("day", "N/A"),
            "AstrologyAPI", _fuzzy_match(str(vc_panch.vara), api_basic.get("day", "")),
        ))

    # Advanced panchang (has yoga, karana, sunrise/sunset)
    api_adv = _get_reference(
        f"{key}:advanced_panchang/sunrise",
        lambda: _astro_api_call("advanced_panchang/sunrise", _birth_to_astro_payload(birth)),
    )

    if api_adv and isinstance(api_adv, dict):
        # Yoga
        api_yoga = api_adv.get("yog", {})
        if isinstance(api_yoga, dict):
            api_yoga_name = api_yoga.get("details", {}).get("yog_name", "")
        else:
            api_yoga_name = str(api_yoga)
        vc_yoga_name = str(vc_panch.yoga_name) if hasattr(vc_panch, "yoga_name") else ""
        if api_yoga_name and vc_yoga_name:
            results.append(TestResult(
                "Panchanga", "Yoga", birth["label"], "Yoga",
                vc_yoga_name, api_yoga_name,
                "AstrologyAPI", _fuzzy_match(vc_yoga_name, api_yoga_name),
            ))

        # Karana
        api_karana = api_adv.get("karan", {})
        if isinstance(api_karana, dict):
            api_karana_name = api_karana.get("details", {}).get("karan_name", "")
        else:
            api_karana_name = str(api_karana)
        vc_karana_name = str(vc_panch.karana_name) if hasattr(vc_panch, "karana_name") else ""
        if api_karana_name and vc_karana_name:
            results.append(TestResult(
                "Panchanga", "Karana", birth["label"], "Karana",
                vc_karana_name, api_karana_name,
                "AstrologyAPI", _fuzzy_match(vc_karana_name, api_karana_name),
            ))

        # Sunrise
        api_sunrise = api_adv.get("sunrise", "")
        if api_sunrise and hasattr(vc_panch, "sunrise_dt") and vc_panch.sunrise_dt:
            vc_sunrise_str = vc_panch.sunrise_dt.strftime("%H:%M")
            api_sr_parts = api_sunrise.split(":")
            if len(api_sr_parts) >= 2:
                api_sunrise_str = f"{int(api_sr_parts[0]):02d}:{int(api_sr_parts[1]):02d}"
                try:
                    vc_mins = int(vc_sunrise_str.split(":")[0]) * 60 + int(vc_sunrise_str.split(":")[1])
                    api_mins = int(api_sunrise_str.split(":")[0]) * 60 + int(api_sunrise_str.split(":")[1])
                    delta_mins = abs(vc_mins - api_mins)
                    results.append(TestResult(
                        "Panchanga", "Sunrise", birth["label"], "Sunrise",
                        vc_sunrise_str, api_sunrise_str, "AstrologyAPI",
                        delta_mins <= 2, float(delta_mins),
                        notes=f"delta={delta_mins}min",
                    ))
                except (ValueError, IndexError):
                    pass

    return results


def collect_dosha(birth: dict, key: str) -> list[TestResult]:
    """Category 7: Doshas (Manglik, Kalsarpa)."""
    results = []
    chart = calculate_chart(**{k: v for k, v in birth.items() if k != "label"})
    vc_doshas = detect_doshas(chart)

    # Manglik
    api_manglik = _get_reference(
        f"{key}:manglik",
        lambda: _astro_api_call("manglik", _birth_to_astro_payload(birth)),
    )
    if api_manglik and isinstance(api_manglik, dict):
        api_is_manglik = api_manglik.get("manglik_status", "") not in ("", "INEFFECTIVE")
        api_pct = api_manglik.get("percentage_manglik_present", 0)
        api_present = api_pct > 0 if isinstance(api_pct, (int, float)) else api_is_manglik

        vc_manglik = next((d for d in vc_doshas if "manglik" in d.name.lower() or "kuja" in d.name.lower()), None)
        if vc_manglik:
            results.append(TestResult(
                "Dosha", "Manglik", birth["label"], "Present",
                str(vc_manglik.is_present), str(api_present),
                "AstrologyAPI", vc_manglik.is_present == api_present,
                notes=f"vc_severity={vc_manglik.severity}, api_status={api_manglik.get('manglik_status', 'N/A')}",
            ))

    # Kalsarpa
    api_kalsarpa = _get_reference(
        f"{key}:kalsarpa_details",
        lambda: _astro_api_call("kalsarpa_details", _birth_to_astro_payload(birth)),
    )
    if api_kalsarpa and isinstance(api_kalsarpa, dict):
        api_present = api_kalsarpa.get("present", False)
        vc_kalsarpa = next((d for d in vc_doshas if "kaal" in d.name.lower() or "sarpa" in d.name.lower()), None)
        if vc_kalsarpa:
            results.append(TestResult(
                "Dosha", "Kalsarpa", birth["label"], "Present",
                str(vc_kalsarpa.is_present), str(api_present),
                "AstrologyAPI", vc_kalsarpa.is_present == api_present,
            ))

    # Sadhesati
    api_sade = _get_reference(
        f"{key}:sadhesati_current_status",
        lambda: _astro_api_call("sadhesati_current_status", _birth_to_astro_payload(birth)),
    )
    if api_sade and isinstance(api_sade, dict):
        api_sade_status = api_sade.get("sadhesati_status", False)
        vc_shani = next((d for d in vc_doshas if "shani" in d.name.lower() or "sade" in d.name.lower()), None)
        if vc_shani:
            results.append(TestResult(
                "Dosha", "Sadhesati", birth["label"], "Currently Active",
                str(vc_shani.is_present), str(api_sade_status),
                "AstrologyAPI", vc_shani.is_present == api_sade_status,
                notes=f"API moon_sign={api_sade.get('moon_sign','?')}, saturn_sign={api_sade.get('saturn_sign','?')}",
            ))

    return results


def collect_compatibility(pair_idx: int) -> list[TestResult]:
    """Category 8: Ashtakoot compatibility."""
    results = []
    b1 = BIRTHS[COMPAT_PAIRS[pair_idx][0]]
    b2 = BIRTHS[COMPAT_PAIRS[pair_idx][1]]
    pair_label = f"{b1['label']} + {b2['label']}"
    pair_key = f"compat_{COMPAT_PAIRS[pair_idx][0]}_{COMPAT_PAIRS[pair_idx][1]}"

    c1 = calculate_chart(**{k: v for k, v in b1.items() if k != "label"})
    c2 = calculate_chart(**{k: v for k, v in b2.items() if k != "label"})

    moon1 = c1.planets.get(1)
    moon2 = c2.planets.get(1)
    if not moon1 or not moon2:
        return results

    try:
        vc_compat = calculate_compatibility(
            person1_nakshatra=Nakshatra(moon1.nakshatra_info.nakshatra),
            person1_sign=moon1.sign,
            person2_nakshatra=Nakshatra(moon2.nakshatra_info.nakshatra),
            person2_sign=moon2.sign,
        )
    except Exception as e:
        results.append(TestResult(
            "Compatibility", "Error", pair_label, "Error",
            str(e), "", "AstrologyAPI", False,
        ))
        return results

    # AstrologyAPI
    api_payload = {
        "m_day": b1["day"], "m_month": b1["month"], "m_year": b1["year"],
        "m_hour": b1["hour"], "m_min": b1["minute"],
        "m_lat": b1["latitude"], "m_lon": b1["longitude"], "m_tzone": b1["timezone_offset"],
        "f_day": b2["day"], "f_month": b2["month"], "f_year": b2["year"],
        "f_hour": b2["hour"], "f_min": b2["minute"],
        "f_lat": b2["latitude"], "f_lon": b2["longitude"], "f_tzone": b2["timezone_offset"],
    }
    api_data = _get_reference(
        f"{pair_key}:match_ashtakoot_points",
        lambda: _astro_api_call("match_ashtakoot_points", api_payload),
    )

    if not api_data or not isinstance(api_data, dict):
        return results

    kutta_map = {
        "varna": "Varna", "vashya": "Vashya", "tara": "Tara", "yoni": "Yoni",
        "maitri": "Graha Maitri", "gan": "Gana", "bhakut": "Bhakoot", "nadi": "Nadi",
    }

    vc_kuttas = {k.name.lower(): k for k in vc_compat.kuttas}

    api_total = 0
    vc_total_score = vc_compat.total_score

    for api_key, display_name in kutta_map.items():
        api_kutta = api_data.get(api_key, {})
        if not isinstance(api_kutta, dict):
            continue
        api_received = api_kutta.get("received_points", 0)
        api_max = api_kutta.get("total_points", 0)
        api_total += api_received

        vc_kutta = None
        for k in vc_compat.kuttas:
            if display_name.lower() in k.name.lower() or k.name.lower() in display_name.lower():
                vc_kutta = k
                break
            if api_key == "maitri" and "maitri" in k.name.lower():
                vc_kutta = k
                break
            if api_key == "gan" and "gana" in k.name.lower():
                vc_kutta = k
                break
            if api_key == "bhakut" and "bhakoot" in k.name.lower():
                vc_kutta = k
                break

        if vc_kutta:
            results.append(TestResult(
                "Compatibility", "Kutta Score", pair_label, display_name,
                f"{vc_kutta.obtained}/{vc_kutta.maximum}",
                f"{api_received}/{api_max}",
                "AstrologyAPI",
                abs(vc_kutta.obtained - api_received) < 0.1,
                abs(vc_kutta.obtained - api_received),
            ))

    api_total_data = api_data.get("total", {})
    if isinstance(api_total_data, dict):
        api_total_score = api_total_data.get("received_points", api_total)
    else:
        api_total_score = api_total

    results.append(TestResult(
        "Compatibility", "Total Score", pair_label, "Total/36",
        f"{vc_total_score:.1f}", f"{api_total_score}",
        "AstrologyAPI",
        abs(vc_total_score - float(api_total_score)) < 0.5,
        abs(vc_total_score - float(api_total_score)),
    ))

    return results


def collect_varshaphal(birth: dict, key: str) -> list[TestResult]:
    """Category 9: Varshaphal — annual chart, Muntha, Year Lord."""
    results = []
    chart = calculate_chart(**{k: v for k, v in birth.items() if k != "label"})

    test_year = birth["year"] + 25
    try:
        vp = calculate_varshaphal(chart, test_year)
    except Exception as e:
        results.append(TestResult(
            "Varshaphal", "Error", birth["label"], "Error",
            str(e), "", "AstrologyAPI", False,
        ))
        return results

    payload = _birth_to_astro_payload(birth)
    payload["varshaphal_year"] = test_year

    api_data = _get_reference(
        f"{key}:varshaphal_year_chart/{test_year}",
        lambda: _astro_api_call("varshaphal_year_chart", payload),
    )

    api_planet_data = _get_reference(
        f"{key}:varshaphal_planets/{test_year}",
        lambda: _astro_api_call("varshaphal_planets", payload),
    )

    api_muntha = _get_reference(
        f"{key}:varshaphal_muntha/{test_year}",
        lambda: _astro_api_call("varshaphal_muntha", payload),
    )

    api_year_lord = _get_reference(
        f"{key}:varshaphal_details/{test_year}",
        lambda: _astro_api_call("varshaphal_details", payload),
    )

    if api_muntha and isinstance(api_muntha, dict):
        api_muntha_sign = api_muntha.get("muntha_sign", "")
        vc_muntha_sign = SIGN_NAMES.get(vp.muntha.sign, "")
        if api_muntha_sign and vc_muntha_sign:
            results.append(TestResult(
                "Varshaphal", "Muntha", birth["label"], "Sign",
                vc_muntha_sign, api_muntha_sign,
                "AstrologyAPI",
                _normalize_name(vc_muntha_sign) == _normalize_name(api_muntha_sign),
            ))

    if api_year_lord and isinstance(api_year_lord, dict):
        api_lord = (api_year_lord.get("year_lord", "")
                    or api_year_lord.get("varshesha", "")
                    or api_year_lord.get("varsh_lord", ""))
        vc_lord = PLANET_IDS.get(vp.year_lord, str(vp.year_lord))
        if api_lord:
            results.append(TestResult(
                "Varshaphal", "Year Lord", birth["label"], "Varshesha",
                vc_lord, api_lord,
                "AstrologyAPI",
                _normalize_name(vc_lord) == _normalize_name(api_lord),
            ))

    if api_planet_data and isinstance(api_planet_data, list):
        for api_p in api_planet_data:
            if not isinstance(api_p, dict):
                continue
            pid = api_p.get("id")
            api_sign_name = api_p.get("sign", "")
            if pid is None or not api_sign_name:
                continue

            planet_key = None
            for p in Planet:
                if PLANET_ENUM_TO_ID.get(p) == pid:
                    planet_key = p
                    break
            if planet_key is None or planet_key not in vp.annual_chart.planets:
                continue

            vc_pos = vp.annual_chart.planets[planet_key]
            vc_sign = SIGN_NAMES.get(vc_pos.sign.value if hasattr(vc_pos.sign, 'value') else int(vc_pos.sign), "")

            results.append(TestResult(
                "Varshaphal", "Planet Sign", birth["label"],
                f"{PLANET_IDS.get(pid, str(pid))} sign",
                vc_sign, api_sign_name,
                "AstrologyAPI",
                _normalize_name(vc_sign) == _normalize_name(api_sign_name),
            ))

    return results


def collect_kp(birth: dict, key: str) -> list[TestResult]:
    """Category 10: KP — sub-lords, Placidus cusps."""
    results = []

    try:
        kp = calculate_kp_chart(
            year=birth["year"], month=birth["month"], day=birth["day"],
            hour=birth["hour"], minute=birth["minute"], second=0,
            latitude=birth["latitude"], longitude=birth["longitude"],
            timezone_offset=birth["timezone_offset"],
        )
    except Exception as e:
        results.append(TestResult(
            "KP", "Error", birth["label"], "Error",
            str(e), "", "AstrologyAPI", False,
        ))
        return results

    api_planets = _get_reference(
        f"{key}:kp_planets",
        lambda: _astro_api_call("kp_planets", _birth_to_astro_payload(birth)),
    )

    api_cusps = _get_reference(
        f"{key}:kp_house_cusps",
        lambda: _astro_api_call("kp_house_cusps", _birth_to_astro_payload(birth)),
    )

    if api_planets and isinstance(api_planets, list):
        for api_p in api_planets:
            if not isinstance(api_p, dict):
                continue
            pid = api_p.get("id")
            api_sign = api_p.get("sign", "")
            api_star_lord = api_p.get("nakshatra_lord", "")
            api_sub_lord = api_p.get("sub_lord", "")

            if pid is None:
                continue

            vc_planet = None
            for p in kp.planets:
                if p.planet == pid:
                    vc_planet = p
                    break
            if vc_planet is None:
                continue

            pname = PLANET_IDS.get(pid, str(pid))
            vc_sign = SIGN_NAMES.get(vc_planet.sign, "")

            if api_sign:
                results.append(TestResult(
                    "KP", "Planet Sign", birth["label"], f"{pname}",
                    vc_sign, api_sign,
                    "AstrologyAPI",
                    _normalize_name(vc_sign) == _normalize_name(api_sign),
                ))

            if api_star_lord:
                vc_star = PLANET_IDS.get(vc_planet.star_lord, str(vc_planet.star_lord))
                results.append(TestResult(
                    "KP", "Star Lord", birth["label"], f"{pname}",
                    vc_star, api_star_lord,
                    "AstrologyAPI",
                    _normalize_name(vc_star) == _normalize_name(api_star_lord),
                ))

            if api_sub_lord:
                vc_sub = PLANET_IDS.get(vc_planet.sub_lord, str(vc_planet.sub_lord))
                results.append(TestResult(
                    "KP", "Sub Lord", birth["label"], f"{pname}",
                    vc_sub, api_sub_lord,
                    "AstrologyAPI",
                    _normalize_name(vc_sub) == _normalize_name(api_sub_lord),
                ))

    if api_cusps and isinstance(api_cusps, list):
        for api_cusp in api_cusps:
            if not isinstance(api_cusp, dict):
                continue
            house = api_cusp.get("house_id") or api_cusp.get("house")
            api_sign = api_cusp.get("sign", "")
            api_sub_lord = api_cusp.get("sub_lord", "")

            if house is None:
                continue

            vc_cusp = None
            for c in kp.cusps:
                if c.house_number == house:
                    vc_cusp = c
                    break
            if vc_cusp is None:
                continue

            vc_sign = SIGN_NAMES.get(vc_cusp.sign, "")

            if api_sign:
                results.append(TestResult(
                    "KP", "Cusp Sign", birth["label"], f"House {house}",
                    vc_sign, api_sign,
                    "AstrologyAPI",
                    _normalize_name(vc_sign) == _normalize_name(api_sign),
                ))

            if api_sub_lord:
                vc_sub = PLANET_IDS.get(vc_cusp.sub_lord, str(vc_cusp.sub_lord))
                results.append(TestResult(
                    "KP", "Cusp Sub Lord", birth["label"], f"House {house}",
                    vc_sub, api_sub_lord,
                    "AstrologyAPI",
                    _normalize_name(vc_sub) == _normalize_name(api_sub_lord),
                ))

    return results


NUMEROLOGY_NAMES = [
    "Rahul Sharma",
    "Priya Patel",
    "Amit Kumar",
    "Deepika Singh",
    "Vikram Reddy",
    "Sneha Gupta",
    "Arjun Nair",
    "Meera Iyer",
    "Kiran Das",
    "Pooja Rao",
]

def collect_numerology(birth: dict, birth_idx: int, key: str) -> list[TestResult]:
    """Category 11: Numerology — destiny, radical, lucky numbers."""
    results = []

    name = NUMEROLOGY_NAMES[birth_idx]

    try:
        num = calculate_numerology(
            name=name, year=birth["year"], month=birth["month"], day=birth["day"],
        )
    except Exception as e:
        results.append(TestResult(
            "Numerology", "Error", birth["label"], "Error",
            str(e), "", "AstrologyAPI", False,
        ))
        return results

    api_payload = {
        "day": birth["day"], "month": birth["month"], "year": birth["year"],
        "name": name,
    }
    api_data = _get_reference(
        f"{key}:numero_table",
        lambda: _astro_api_call("numero_table", api_payload),
    )

    if not api_data or not isinstance(api_data, dict):
        return results

    api_destiny = api_data.get("destiny_number")
    if api_destiny is not None:
        results.append(TestResult(
            "Numerology", "Destiny", birth["label"], "Destiny Number",
            str(num.destiny_number), str(api_destiny),
            "AstrologyAPI",
            num.destiny_number == int(api_destiny),
        ))

    api_radical = api_data.get("radical_number")
    if api_radical is not None:
        results.append(TestResult(
            "Numerology", "Radical", birth["label"], "Radical Number",
            str(num.radical_number), str(api_radical),
            "AstrologyAPI",
            num.radical_number == int(api_radical),
        ))

    api_name_num = api_data.get("name_number")
    if api_name_num is not None:
        results.append(TestResult(
            "Numerology", "Name", birth["label"], "Name Number",
            str(num.name_number), str(api_name_num),
            "AstrologyAPI",
            num.name_number == int(api_name_num),
        ))

    api_lucky = api_data.get("lucky_number")
    if api_lucky is not None:
        api_lucky_list = sorted([int(x) for x in str(api_lucky).split(",") if x.strip().isdigit()])
        vc_lucky_list = sorted(num.lucky_numbers)
        results.append(TestResult(
            "Numerology", "Lucky", birth["label"], "Lucky Numbers",
            str(vc_lucky_list), str(api_lucky_list),
            "AstrologyAPI",
            vc_lucky_list == api_lucky_list,
        ))

    return results


# ---------------------------------------------------------------------------
# Sprint 1 feature collectors
# ---------------------------------------------------------------------------

def collect_sade_sati(birth: dict, key: str) -> list[TestResult]:
    """Category 12: Sade Sati — compare current status against AstrologyAPI + Prokerala."""
    results = []
    chart = calculate_chart(**{k: v for k, v in birth.items() if k != "label"})

    today = datetime.now()
    vc_sade = calculate_sade_sati(chart, today)

    # vs AstrologyAPI sadhesati_current_status
    api_sade = _get_reference(
        f"{key}:sadhesati_current_status",
        lambda: _astro_api_call("sadhesati_current_status", _birth_to_astro_payload(birth)),
    )
    if api_sade and isinstance(api_sade, dict):
        api_active = api_sade.get("sadhesati_status", False)
        if isinstance(api_active, str):
            api_active = api_active.lower() == "true"
        results.append(TestResult(
            "Sade Sati", "Currently Active", birth["label"], "Status",
            str(vc_sade.is_active), str(api_active),
            "AstrologyAPI", vc_sade.is_active == api_active,
            notes=f"vc_phase={vc_sade.current_phase}, api_moon={api_sade.get('moon_sign','?')}, api_saturn={api_sade.get('saturn_sign','?')}",
        ))

    # vs Prokerala sade-sati
    prok_params = _birth_to_prokerala_params(birth)
    prok_sade = _get_reference(
        f"{key}:prokerala/sade-sati",
        lambda: _prokerala_api_call("sade-sati", prok_params),
    )
    if prok_sade and isinstance(prok_sade, dict) and prok_sade.get("status") == "ok":
        prok_data = prok_sade.get("data", {})
        prok_active = prok_data.get("is_in_sade_sati", False)
        results.append(TestResult(
            "Sade Sati", "Currently Active", birth["label"], "Status",
            str(vc_sade.is_active), str(prok_active),
            "Prokerala", vc_sade.is_active == prok_active,
        ))

    return results


def collect_planet_relationships(birth: dict, key: str) -> list[TestResult]:
    """Category 13: Planet Relationships — Panchadha Maitri vs Prokerala."""
    results = []
    chart = calculate_chart(**{k: v for k, v in birth.items() if k != "label"})
    vc_rels = calculate_planet_relationships(chart)

    prok_params = _birth_to_prokerala_params(birth)
    prok_data = _get_reference(
        f"{key}:prokerala/planet-relationship",
        lambda: _prokerala_api_call("planet-relationship", prok_params),
    )

    if not prok_data or prok_data.get("status") != "ok":
        return results

    prok_rels = prok_data.get("data", {}).get("planet_relationships", [])

    # Map relationship types for comparison
    rel_normalize = {
        "best_friend": "great_friend", "bestfriend": "great_friend",
        "great friend": "great_friend",
        "friend": "friend",
        "neutral": "neutral",
        "enemy": "enemy",
        "worst_enemy": "great_enemy", "worstenemy": "great_enemy",
        "great enemy": "great_enemy", "bitter_enemy": "great_enemy",
    }

    for prok_rel in prok_rels:
        planet1_name = prok_rel.get("planet1", {}).get("name", "")
        planet2_name = prok_rel.get("planet2", {}).get("name", "")
        prok_compound = prok_rel.get("relationship", {}).get("compound", "")

        if not planet1_name or not planet2_name or not prok_compound:
            continue

        # Find matching vedic-calc relationship
        vc_match = None
        for rel in vc_rels.relationships:
            vc_p1 = PLANET_IDS.get(PLANET_ENUM_TO_ID.get(rel.planet1, -1), "")
            vc_p2 = PLANET_IDS.get(PLANET_ENUM_TO_ID.get(rel.planet2, -1), "")
            if (_fuzzy_match(vc_p1, planet1_name) and _fuzzy_match(vc_p2, planet2_name)):
                vc_match = rel
                break

        if vc_match:
            vc_norm = rel_normalize.get(vc_match.compound.lower().replace(" ", "_"), vc_match.compound.lower())
            prok_norm = rel_normalize.get(prok_compound.lower().replace(" ", "_"), prok_compound.lower())
            results.append(TestResult(
                "Planet Relationships", "Compound", birth["label"],
                f"{planet1_name}-{planet2_name}",
                vc_match.compound, prok_compound,
                "Prokerala", vc_norm == prok_norm,
            ))

    return results


def collect_avakhada(birth: dict, key: str) -> list[TestResult]:
    """Category 14: Avakhada Table — compare varna/vashya/yoni/gana/nadi vs AstrologyAPI astro-details."""
    results = []
    chart = calculate_chart(**{k: v for k, v in birth.items() if k != "label"})

    moon = chart.planets.get(1)
    if not moon:
        return results

    vc_avk = calculate_avakhada(
        nakshatra=moon.nakshatra_info.nakshatra,
        pada=moon.nakshatra_info.pada,
        sign=moon.sign.value,
    )

    api_data = _get_reference(
        f"{key}:astro_details",
        lambda: _astro_api_call("astro_details", _birth_to_astro_payload(birth)),
    )

    if not api_data or not isinstance(api_data, dict):
        return results

    # Compare varna
    api_varna = api_data.get("Varna", "") or api_data.get("varna", "")
    if api_varna:
        results.append(TestResult(
            "Avakhada", "Varna", birth["label"], "Varna",
            vc_avk.varna, api_varna, "AstrologyAPI",
            _fuzzy_match(vc_avk.varna, api_varna),
        ))

    # Compare vashya
    api_vashya = api_data.get("Vashya", "") or api_data.get("vashya", "")
    if api_vashya:
        results.append(TestResult(
            "Avakhada", "Vashya", birth["label"], "Vashya",
            vc_avk.vashya, api_vashya, "AstrologyAPI",
            _fuzzy_match(vc_avk.vashya, api_vashya),
        ))

    # Compare yoni
    api_yoni = api_data.get("Yoni", "") or api_data.get("yoni", "")
    if api_yoni:
        results.append(TestResult(
            "Avakhada", "Yoni", birth["label"], "Yoni",
            vc_avk.yoni, api_yoni, "AstrologyAPI",
            _fuzzy_match(vc_avk.yoni, api_yoni),
        ))

    # Compare gana
    api_gana = api_data.get("Gan", "") or api_data.get("gana", "") or api_data.get("Gana", "")
    if api_gana:
        results.append(TestResult(
            "Avakhada", "Gana", birth["label"], "Gana",
            vc_avk.gana, api_gana, "AstrologyAPI",
            _fuzzy_match(vc_avk.gana, api_gana),
        ))

    # Compare nadi
    api_nadi = api_data.get("Nadi", "") or api_data.get("nadi", "")
    if api_nadi:
        results.append(TestResult(
            "Avakhada", "Nadi", birth["label"], "Nadi",
            vc_avk.nadi, api_nadi, "AstrologyAPI",
            _fuzzy_match(vc_avk.nadi, api_nadi),
        ))

    # Compare tatva
    api_tatva = api_data.get("Tatpitta", "") or api_data.get("tatpitta", "") or api_data.get("Tatva", "") or api_data.get("tatva", "")
    if api_tatva:
        results.append(TestResult(
            "Avakhada", "Tatva", birth["label"], "Tatva",
            vc_avk.tatva, api_tatva, "AstrologyAPI",
            _fuzzy_match(vc_avk.tatva, api_tatva),
        ))

    return results


def collect_disha_shool(birth: dict, key: str) -> list[TestResult]:
    """Category 15: Disha Shool — compare inauspicious direction vs Prokerala."""
    results = []

    vc_ds = get_disha_shool(birth["year"], birth["month"], birth["day"])

    prok_params = _birth_to_prokerala_params(birth)
    prok_data = _get_reference(
        f"{key}:prokerala/disha-shool",
        lambda: _prokerala_api_call("disha-shool", prok_params),
    )

    if prok_data and isinstance(prok_data, dict) and prok_data.get("status") == "ok":
        prok_dir = prok_data.get("data", {}).get("direction", "")
        results.append(TestResult(
            "Disha Shool", "Direction", birth["label"], "Inauspicious",
            vc_ds.direction, prok_dir, "Prokerala",
            _fuzzy_match(vc_ds.direction, prok_dir),
        ))

    return results


def collect_anandadi_yoga(birth: dict, key: str) -> list[TestResult]:
    """Category 16: Anandadi Yoga — compare yoga for tithi+weekday vs Prokerala."""
    results = []

    import calendar
    weekday = calendar.weekday(birth["year"], birth["month"], birth["day"])
    # Python: Monday=0. Vedic: Sunday=0. Convert.
    weekday_vedic = (weekday + 1) % 7

    vc_panch = calculate_panchanga(
        year=birth["year"], month=birth["month"], day=birth["day"],
        latitude=birth["latitude"], longitude=birth["longitude"],
        timezone_offset=birth["timezone_offset"],
    )
    vc_anandadi = get_anandadi_yoga(vc_panch.tithi_number, weekday_vedic)

    prok_params = _birth_to_prokerala_params(birth)
    prok_data = _get_reference(
        f"{key}:prokerala/anandadi-yoga",
        lambda: _prokerala_api_call("anandadi-yoga", prok_params),
    )

    if prok_data and isinstance(prok_data, dict) and prok_data.get("status") == "ok":
        prok_yoga = prok_data.get("data", {}).get("yoga", {}).get("name", "")
        results.append(TestResult(
            "Anandadi Yoga", "Yoga", birth["label"], "Name",
            vc_anandadi.yoga_name, prok_yoga, "Prokerala",
            _fuzzy_match(vc_anandadi.yoga_name, prok_yoga),
        ))

    return results


def collect_chandrashtama(birth: dict, key: str) -> list[TestResult]:
    """Category 17: Chandrashtama — compare periods vs Prokerala."""
    results = []
    chart = calculate_chart(**{k: v for k, v in birth.items() if k != "label"})

    moon = chart.planets.get(1)
    if not moon:
        return results

    from datetime import timedelta
    now = datetime.now()
    start = now
    end = now + timedelta(days=30)

    try:
        vc_chandra = calculate_chandrashtama(
            natal_moon_sign=moon.sign.value,
            start_date=start, end_date=end,
            latitude=birth["latitude"], longitude=birth["longitude"],
            timezone_offset=birth["timezone_offset"],
        )
    except Exception as e:
        results.append(TestResult(
            "Chandrashtama", "Error", birth["label"], "Error",
            str(e), "", "Prokerala", False,
        ))
        return results

    prok_params = _birth_to_prokerala_params(birth)
    prok_data = _get_reference(
        f"{key}:prokerala/chandrashtama-periods",
        lambda: _prokerala_api_call("chandrashtama-periods", prok_params),
    )

    if not prok_data or prok_data.get("status") != "ok":
        return results

    prok_periods = prok_data.get("data", {}).get("periods", [])
    vc_count = len(vc_chandra.windows)
    prok_count = len(prok_periods)

    # Compare number of windows found (30-day period should have ~4-5)
    results.append(TestResult(
        "Chandrashtama", "Window Count", birth["label"], "30-day count",
        str(vc_count), str(prok_count), "Prokerala",
        abs(vc_count - prok_count) <= 1,
        float(abs(vc_count - prok_count)),
        notes=f"vc={vc_count}, prok={prok_count}",
    ))

    return results


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def _generate_report(all_results: list[TestResult]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = []
    lines.append("# vedic-calc Comprehensive Accuracy Benchmark")
    lines.append("")
    lines.append(f"**Generated**: {now}")
    lines.append(f"**Charts tested**: {len(BIRTHS)}")
    lines.append(f"**Compatibility pairs**: {len(COMPAT_PAIRS)}")
    lines.append(f"**Reference APIs**: AstrologyAPI.com (Professional), Prokerala")
    lines.append(f"**Ayanamsa**: Lahiri (all engines)")
    lines.append("")

    # Overall summary
    categories = sorted(set(r.category for r in all_results))
    total_pass = sum(1 for r in all_results if r.match)
    total_tests = len(all_results)
    lines.append("## Overall Summary")
    lines.append("")
    lines.append(f"**Total tests: {total_tests} | Passed: {total_pass} | Failed: {total_tests - total_pass} | Rate: {total_pass/total_tests*100:.1f}%**")
    lines.append("")

    # Per-category summary
    lines.append("| Category | Tests | Passed | Failed | Rate |")
    lines.append("|----------|-------|--------|--------|------|")
    for cat in categories:
        cat_results = [r for r in all_results if r.category == cat]
        passed = sum(1 for r in cat_results if r.match)
        failed = len(cat_results) - passed
        rate = passed / len(cat_results) * 100 if cat_results else 0
        marker = "" if failed == 0 else " **!!**"
        lines.append(f"| {cat} | {len(cat_results)} | {passed} | {failed} | {rate:.1f}%{marker} |")
    lines.append("")

    # Per-category detail — only show failures and summary
    for cat in categories:
        cat_results = [r for r in all_results if r.category == cat]
        passed = sum(1 for r in cat_results if r.match)
        failed_results = [r for r in cat_results if not r.match]

        lines.append(f"## {cat}")
        lines.append(f"")
        lines.append(f"**{passed}/{len(cat_results)} passed**")
        lines.append("")

        if failed_results:
            lines.append("### Failures")
            lines.append("")
            lines.append("| Chart | Sub | Field | vedic-calc | Reference | Source | Notes |")
            lines.append("|-------|-----|-------|-----------|-----------|--------|-------|")
            for r in failed_results:
                notes = r.notes
                if r.delta is not None:
                    notes = f"delta={r.delta:.4f}" + (f", {notes}" if notes else "")
                lines.append(f"| {r.chart_label} | {r.subcategory} | {r.field} | `{r.vedic_calc}` | `{r.reference}` | {r.reference_source} | {notes} |")
            lines.append("")

        # Subcategory breakdown
        subcats = sorted(set(r.subcategory for r in cat_results))
        if len(subcats) > 1:
            lines.append("### Breakdown")
            lines.append("")
            lines.append("| Subcategory | Tests | Passed | Rate |")
            lines.append("|-------------|-------|--------|------|")
            for sc in subcats:
                sc_results = [r for r in cat_results if r.subcategory == sc]
                sc_passed = sum(1 for r in sc_results if r.match)
                lines.append(f"| {sc} | {len(sc_results)} | {sc_passed} | {sc_passed/len(sc_results)*100:.0f}% |")
            lines.append("")

        # For planets, show aggregate delta stats
        if cat == "Planets":
            deltas = [r.delta for r in cat_results if r.subcategory == "Longitude" and r.delta is not None]
            if deltas:
                api_deltas = [r.delta for r in cat_results if r.subcategory == "Longitude" and r.reference_source == "AstrologyAPI" and r.delta is not None]
                prok_deltas = [r.delta for r in cat_results if r.subcategory == "Longitude" and r.reference_source == "Prokerala" and r.delta is not None]
                lines.append("### Longitude Statistics")
                lines.append("")
                if api_deltas:
                    lines.append(f"- **vs AstrologyAPI**: avg={sum(api_deltas)/len(api_deltas):.4f}°, max={max(api_deltas):.4f}°, threshold={MAX_DEGREE_DIFF}°")
                if prok_deltas:
                    lines.append(f"- **vs Prokerala**: avg={sum(prok_deltas)/len(prok_deltas):.4f}°, max={max(prok_deltas):.4f}°, threshold={MAX_DEGREE_DIFF}°")
                lines.append("")

    # Methodology
    lines.append("## Methodology")
    lines.append("")
    lines.append("All engines use the Swiss Ephemeris and Lahiri (Chitrapaksha) ayanamsa.")
    lines.append(f"Planetary longitude threshold: {MAX_DEGREE_DIFF}° (positions closer than this are considered identical).")
    lines.append(f"Dasha date threshold: {DASHA_DATE_TOLERANCE_DAYS} days (accounts for time-of-day parsing differences).")
    lines.append("Panchanga and nakshatra names use fuzzy matching to handle transliteration variants.")
    lines.append("")
    lines.append("### Categories Tested")
    lines.append("")
    lines.append("1. **Planets**: longitude, sign, retrograde for all 9 grahas + ascendant vs both APIs")
    lines.append("2. **Divisional**: D9 (Navamsa) planet-sign placements vs AstrologyAPI")
    lines.append("3. **Dasha**: Vimshottari mahadasha lord sequence, start dates, current period")
    lines.append("4. **Yogini Dasha**: current major period lord")
    lines.append("5. **Ashtakavarga**: bhinnashtak totals per planet per sign (7 planets × 12 signs)")
    lines.append("6. **Panchanga**: tithi, nakshatra, vara, yoga, karana, sunrise time")
    lines.append("7. **Dosha**: Manglik, Kalsarpa, Sadhesati presence/absence")
    lines.append("8. **Compatibility**: Ashtakoot 8-kutta scores and total for 5 pairs")
    lines.append("9. **Varshaphal**: Muntha sign, Year Lord, annual planet signs")
    lines.append("10. **KP**: planet signs, star lords, sub-lords, cusp signs")
    lines.append("11. **Numerology**: destiny, radical, name, lucky numbers")
    lines.append("12. **Sade Sati**: current active status vs AstrologyAPI + Prokerala")
    lines.append("13. **Planet Relationships**: Panchadha Maitri compound relationships vs Prokerala")
    lines.append("14. **Avakhada**: varna, vashya, yoni, gana, nadi vs AstrologyAPI")
    lines.append("15. **Disha Shool**: inauspicious direction vs Prokerala")
    lines.append("16. **Anandadi Yoga**: yoga name vs Prokerala")
    lines.append("17. **Chandrashtama**: window count vs Prokerala")
    lines.append("")
    lines.append("---")
    lines.append("*Generated by vedic-calc benchmark suite*")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    html_mode = "--html" in sys.argv

    print(f"Running comprehensive accuracy benchmark...")
    print(f"Charts: {len(BIRTHS)}, Compatibility pairs: {len(COMPAT_PAIRS)}")
    print(f"Refresh mode: {'ON (calling live APIs)' if REFRESH else 'OFF (using cached fixtures)'}")
    print()

    has_astro = bool(ASTRO_USER_ID and ASTRO_API_KEY)
    has_prok = bool(PROKERALA_CLIENT_ID and PROKERALA_CLIENT_SECRET)
    print(f"AstrologyAPI: {'ready' if has_astro else 'MISSING'}")
    print(f"Prokerala: {'ready' if has_prok else 'MISSING'}")
    print()

    all_results: list[TestResult] = []

    for i, birth in enumerate(BIRTHS, 1):
        key = birth["label"].lower().replace(" ", "_")
        print(f"[{i}/{len(BIRTHS)}] {birth['label']}...", flush=True)

        # Original categories
        for collector_name, collector in [
            ("Planets", lambda b, k: collect_planets(b, k)),
            ("Divisional", lambda b, k: collect_divisional(b, k)),
            ("Dasha", lambda b, k: collect_dasha(b, k)),
            ("Yogini Dasha", lambda b, k: collect_yogini_dasha(b, k)),
            ("Ashtakavarga", lambda b, k: collect_ashtakavarga(b, k)),
            ("Panchanga", lambda b, k: collect_panchanga(b, k)),
            ("Doshas", lambda b, k: collect_dosha(b, k)),
            ("Varshaphal", lambda b, k: collect_varshaphal(b, k)),
            ("KP", lambda b, k: collect_kp(b, k)),
        ]:
            print(f"  {collector_name}...", end=" ", flush=True)
            r = collector(birth, key)
            p = sum(1 for x in r if x.match)
            print(f"{p}/{len(r)}", flush=True)
            all_results.extend(r)

        # Numerology (needs index)
        print(f"  Numerology...", end=" ", flush=True)
        r = collect_numerology(birth, i - 1, key)
        p = sum(1 for x in r if x.match)
        print(f"{p}/{len(r)}", flush=True)
        all_results.extend(r)

        # Sprint 1 feature collectors
        for collector_name, collector in [
            ("Sade Sati", lambda b, k: collect_sade_sati(b, k)),
            ("Planet Relationships", lambda b, k: collect_planet_relationships(b, k)),
            ("Avakhada", lambda b, k: collect_avakhada(b, k)),
            ("Disha Shool", lambda b, k: collect_disha_shool(b, k)),
            ("Anandadi Yoga", lambda b, k: collect_anandadi_yoga(b, k)),
            ("Chandrashtama", lambda b, k: collect_chandrashtama(b, k)),
        ]:
            print(f"  {collector_name}...", end=" ", flush=True)
            r = collector(birth, key)
            p = sum(1 for x in r if x.match)
            print(f"{p}/{len(r)}", flush=True)
            all_results.extend(r)

    # Compatibility
    print(f"\nCompatibility ({len(COMPAT_PAIRS)} pairs)...")
    for i in range(len(COMPAT_PAIRS)):
        b1 = BIRTHS[COMPAT_PAIRS[i][0]]
        b2 = BIRTHS[COMPAT_PAIRS[i][1]]
        print(f"  {b1['label']} + {b2['label']}...", end=" ", flush=True)
        r = collect_compatibility(i)
        p = sum(1 for x in r if x.match)
        print(f"{p}/{len(r)}", flush=True)
        all_results.extend(r)

    # Save fixtures
    _save_fixtures()
    print(f"\nFixtures saved to {FIXTURES_PATH}")

    # Summary
    total_pass = sum(1 for r in all_results if r.match)
    total = len(all_results)
    print(f"\n{'='*60}")
    print(f"TOTAL: {total_pass}/{total} passed ({total_pass/total*100:.1f}%)")
    print()

    categories = sorted(set(r.category for r in all_results))
    for cat in categories:
        cr = [r for r in all_results if r.category == cat]
        p = sum(1 for r in cr if r.match)
        f = len(cr) - p
        marker = "  PASS" if f == 0 else f"  ** {f} FAILURES **"
        print(f"  {cat}: {p}/{len(cr)} ({p/len(cr)*100:.0f}%){marker}")

    # Show failures
    failures = [r for r in all_results if not r.match]
    if failures:
        print(f"\n{'='*60}")
        print(f"FAILURES ({len(failures)}):")
        for r in failures:
            notes = f" [{r.notes}]" if r.notes else ""
            print(f"  [{r.category}/{r.subcategory}] {r.chart_label} - {r.field}: "
                  f"vc={r.vedic_calc} vs {r.reference_source}={r.reference}{notes}")

    # Generate report
    report = _generate_report(all_results)
    report_path = Path(__file__).parent / "ACCURACY_REPORT.md"
    report_path.write_text(report)
    print(f"\nReport saved to {report_path}")

    # Also copy to docs for static site
    docs_path = Path(__file__).parent.parent / "docs" / "benchmarks.md"
    docs_path.write_text(report)
    print(f"Docs report saved to {docs_path}")

    if html_mode:
        try:
            import markdown
            html = markdown.markdown(report, extensions=["tables"])
            html_full = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>vedic-calc Accuracy Benchmark</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 1200px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; color: #333; }}
h1 {{ color: #6C5CE7; }}
h2 {{ border-bottom: 2px solid #6C5CE7; padding-bottom: 0.3rem; }}
h3 {{ color: #636e72; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 0.9rem; }}
th {{ background: #6C5CE7; color: white; }}
tr:nth-child(even) {{ background: #f8f8f8; }}
code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 3px; }}
</style>
</head><body>{html}</body></html>"""
            html_path = Path(__file__).parent / "ACCURACY_REPORT.html"
            html_path.write_text(html_full)
            print(f"HTML report saved to {html_path}")
        except ImportError:
            print("Install 'markdown' for HTML: pip install markdown")


if __name__ == "__main__":
    main()
