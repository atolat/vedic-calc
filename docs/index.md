# vedic-calc

**Open-source Vedic astrology calculation library built on the Swiss Ephemeris.**

vedic-calc provides accurate astronomical calculations for Vedic (sidereal) astrology -- planetary positions, birth charts, nakshatras, divisional charts, dasha periods, panchanga, compatibility, muhurta, prashna, and more -- with a clean, type-safe Python API.

## Why vedic-calc?

| Feature | vedic-calc | PyJHora | pyswisseph (raw) |
|---------|-----------|---------|------------------|
| License | Apache 2.0 | AGPL (restrictive) | Modified BSD |
| GUI dependencies | None | Requires PyQt6 | None |
| API design | Pydantic models, pure functions | GUI-coupled, global state | Low-level C bindings |
| Vedic astrology | Built-in (14 modules) | Built-in | DIY |
| JSON serializable | Yes (all models) | No | No |

## Features

**Chart Calculation**

- Birth chart -- planetary positions, houses (Whole Sign), nakshatras, padas
- Divisional charts -- D-1 through D-60 (Rasi, Navamsa, Dashamsa, and all standard vargas)
- Aspects -- Vedic drishti (sign-based aspects with special aspects for Mars, Jupiter, Saturn)
- Combustion -- proximity-based combustion detection with planet-specific orbs
- Planetary states -- dignity (own sign, exaltation, debilitation, moolatrikona, friend/enemy), retrograde, dispositor chains
- House analysis -- lord placement, occupants, aspecting planets, strength assessment
- Transits -- current sky positions overlaid on natal chart
- Special lagnas -- Hora Lagna, Ghati Lagna, Bhava Lagna, Sree Lagna
- Upagrahas -- Dhuma, Vyatipata, Parivesha, Chapa, Upaketu
- Sahams -- 21 Arabic parts (Punya Saham, Vidya Saham, etc.)
- Rendering -- South Indian, North Indian (ASCII), and SVG chart diagrams

**Planetary Periods**

- Vimsottari Dasha -- mahadasha, antardasha, pratyantardasha (120-year cycle)
- Yogini Dasha -- 8 yogini deities (36-year cycle)
- Ashtottari Dasha -- 8 planets excluding Ketu (108-year cycle)
- Narayana Dasha -- Jaimini sign-based periods

**Panchanga (Daily Calendar)**

- Five elements -- tithi, nakshatra, yoga, karana, vara
- Sunrise/sunset for any location
- Hindu festival detection

**Yoga and Dosha Detection**

- Yogas -- ~20 classical yogas (Pancha Mahapurusha, Gajakesari, Dhana, Lakshmi, Budhaditya, Raja, Viparita Raja, Saraswati, Kemadruma, and more)
- Doshas -- Mangal Dosha, Kaal Sarpa Dosha, Pitru Dosha, Grahan Dosha with severity levels and remedies

**Strength Analysis**

- Shadbala -- six-fold planetary strength (positional, directional, temporal, motional, natural, aspectual)
- Ashtakavarga -- 8-source benefic point system (per-planet and sarvashtakavarga)

**Compatibility**

- Ashtakoot Milan -- North Indian 8-factor scoring (max 36 points) with Mangal Dosha check
- Porutham -- South Indian 10-factor compatibility (Dina, Gana, Rajju, Vedha, etc.)

**Muhurta (Electional Astrology)**

- Daily muhurta -- Rahu Kalam, Yamagandam, Gulika Kalam, Abhijit Muhurta, Choghadiya, Hora
- Muhurta solver -- find auspicious windows for any activity within a date range, with 5-layer panchanga filtering and personal overlays (Chandrabala, Tarabala)

**Prashna (Horary Astrology)**

- Prashna chart casting -- chart for the moment a question is asked
- Tajika yogas -- degree-based aspect patterns (Ithasala, Easarapha, Induvara, Kamboola, Nakta)
- Verdict engine -- favorable/unfavorable/mixed with reasoning

**Jaimini System**

- Chara Karakas -- 7 variable significators based on planetary degrees
- Arudha Padas -- image/projection of each house

**Annual Predictions**

- Varshaphal -- solar return chart, Muntha (progressed ascendant), annual Tajika yogas

**KP System (Krishnamurti Paddhati)**

- KP chart -- Placidus house cusps with sign lord, star lord, sub lord
- Sublord lookup -- 249-division KP sublord table

**Numerology**

- Chaldean system -- psychic number, destiny number, name number with interpretation

## Quick Start

```bash
# Install
pip install vedic-calc

# Or with uv
uv add vedic-calc
```

```python
from vedic_calc import calculate_chart

chart = calculate_chart(
    year=1990, month=3, day=15,
    hour=10, minute=30,
    latitude=19.0760, longitude=72.8777,  # Mumbai
    timezone_offset=5.5,                   # IST
)

# Access planetary positions
for planet, pos in chart.planets.items():
    print(f"{planet.name}: {pos.sign.name} {pos.degree_in_sign:.1f}")

# JSON export
print(chart.model_dump_json(indent=2))
```

## Design Principles

1. **Accuracy first** -- Swiss Ephemeris for positions, cross-validated against astronomical facts and PyJHora
2. **Pure functions** -- no global state, no side effects, easy to test
3. **Immutable data** -- all models are frozen Pydantic BaseModels
4. **Thin abstraction** -- only `ephemeris.py` touches pyswisseph, everything else is pure Python
5. **Zero GUI dependencies** -- headless library, not a desktop app
