# Architecture

## Overview

vedic-calc follows a layered architecture with strict dependency boundaries:

```
┌─────────────────────────────────────────────┐
│              Public API                      │
│         calculate_chart()                    │
│         calculate_dasha()  (Day 2)           │
│         get_panchanga()    (Day 2)           │
├─────────────────────────────────────────────┤
│            Chart Layer                       │
│   calculator.py  │  helpers (sign, nak, etc) │
├─────────────────────────────────────────────┤
│            Core Layer                        │
│   types.py  │  constants.py  │  ephemeris.py │
├─────────────────────────────────────────────┤
│          Swiss Ephemeris (pyswisseph)        │
│         (NASA JPL ephemeris data)            │
└─────────────────────────────────────────────┘
```

## Key Boundary: ephemeris.py

The single most important design decision: **only `ephemeris.py` imports pyswisseph**. Everything else works with plain floats (longitudes in degrees).

This gives us:

- **Testability** — mock `ephemeris.py` to test all chart logic without the Swiss Ephemeris
- **Swappability** — could replace pyswisseph with another engine (REST API, WASM, etc.)
- **Simplicity** — pyswisseph has a complex C-style API; we expose 4 clean Python functions

### What ephemeris.py provides

| Function | Input | Output |
|----------|-------|--------|
| `_to_julian_day()` | year, month, day, hour | Julian Day float |
| `get_ayanamsa()` | Julian Day, mode | degrees (float) |
| `get_planet_longitude()` | Julian Day, planet, ayanamsa | (longitude, is_retrograde) |
| `get_ascendant()` | Julian Day, lat, lon, ayanamsa | longitude (float) |
| `get_sunrise_sunset()` | Julian Day, lat, lon | (sunrise_jd, sunset_jd) |

## Data Flow

```
Birth Details (date, time, lat/lon, timezone)
    │
    ▼
Convert to UT → Julian Day
    │
    ▼
┌───────────────────────────┐
│  Swiss Ephemeris           │
│  (tropical longitudes)     │
└──────────┬────────────────┘
           │  - ayanamsa
           ▼
   Sidereal longitudes (floats)
    │
    ├── longitude / 30    → Sign
    ├── longitude / 13.33 → Nakshatra + Pada
    ├── ascendant sign    → 12 Houses (Whole Sign)
    └── daily speed < 0   → Retrograde flag
    │
    ▼
  BirthChart (Pydantic model, frozen, JSON-serializable)
```

## Module Responsibilities

### `core/constants.py`
All enumerations and lookup tables. Data from BPHS and Surya Siddhanta.

- `Planet` — 9 Navagraha (Sun through Ketu)
- `Sign` — 12 Rashis (Aries through Pisces)
- `Nakshatra` — 27 lunar mansions
- `Ayanamsa` — precession correction modes
- Lookup tables: sign lords, nakshatra lords, Vimsottari years/order

### `core/types.py`
Pydantic models for all data structures. All frozen (immutable).

- `NakshatraInfo` — nakshatra + pada + lord
- `PlanetPosition` — longitude, sign, degree, nakshatra, retrograde
- `HousePosition` — house number, sign, lord
- `BirthChart` — the complete chart
- `DashaPeriod` — planetary period (used by dasha module)
- `PanchangaInfo` — daily calendar (used by panchanga module)

### `core/ephemeris.py`
Thin wrapper around pyswisseph. Only module that imports `swisseph`.

### `chart/calculator.py`
Main entry point. Pure functions that transform longitudes into astrology data.

- `calculate_chart()` — public API, returns `BirthChart`
- `longitude_to_sign()` — 45° → Taurus
- `longitude_to_nakshatra_info()` — 45° → Rohini pada 2
- `build_houses()` — Whole Sign houses from ascendant

## Design Decisions

### Why Pydantic?
- **Immutability** — `frozen=True` prevents accidental mutation
- **Validation** — `Field(ge=1, le=12)` catches invalid house numbers
- **Serialization** — `.model_dump_json()` for API responses, storage
- **Type safety** — full IDE autocomplete and type checking

### Why Whole Sign houses?
Whole Sign is the traditional house system in Vedic astrology (Parashari method). The ascendant's sign = 1st house, next sign = 2nd house, etc. Simple, unambiguous, and the most commonly used system in Jyotish.

### Why Lahiri ayanamsa as default?
Lahiri (Chitrapaksha) is the official ayanamsa of the Indian government, adopted by the Calendar Reform Committee in 1956. It's the most widely used ayanamsa in India and the de facto standard for Vedic astrology.

### Why IntEnum for planets/signs?
Integer enums allow both human-readable code (`Planet.JUPITER`) and mathematical operations when needed. They also serialize cleanly to JSON.
