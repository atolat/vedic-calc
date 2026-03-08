# API Reference

## Chart Calculation

### `calculate_chart()`

Calculate a complete Vedic birth chart.

```python
from vedic_calc import calculate_chart

chart = calculate_chart(
    year=1990,
    month=3,
    day=15,
    hour=10,
    minute=30,
    second=0,
    latitude=19.0760,     # Mumbai
    longitude=72.8777,
    timezone_offset=5.5,  # IST = UTC+5:30
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `year` | `int` | required | Birth year |
| `month` | `int` | required | Birth month (1-12) |
| `day` | `int` | required | Birth day (1-31) |
| `hour` | `int` | `0` | Birth hour, local time (0-23) |
| `minute` | `int` | `0` | Birth minute (0-59) |
| `second` | `int` | `0` | Birth second (0-59) |
| `latitude` | `float` | `0.0` | Geographic latitude (north positive) |
| `longitude` | `float` | `0.0` | Geographic longitude (east positive) |
| `timezone_offset` | `float` | `0.0` | UTC offset in hours (e.g., 5.5 for IST) |
| `ayanamsa` | `Ayanamsa` | `LAHIRI` | Precession correction mode |

**Returns:** `BirthChart`

---

## Dasha Calculation

### `calculate_dasha()`

Calculate Vimsottari dasha (planetary period) timeline from a birth chart.

```python
from vedic_calc import calculate_chart, calculate_dasha

chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
periods = calculate_dasha(chart, levels=2)

# Print mahadashas
for p in periods:
    if p.level == "mahadasha":
        print(f"{p.lord.name}: {p.start.date()} → {p.end.date()} ({p.duration_years:.1f} yrs)")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chart` | `BirthChart` | required | A calculated birth chart |
| `levels` | `int` | `2` | Depth: 1=mahadasha, 2=+antardasha, 3=+pratyantardasha |

**Returns:** `list[DashaPeriod]` — flat list sorted chronologically, with `level` field to distinguish depths.

### `get_current_dasha()`

Get the active dasha periods for a specific date.

```python
from vedic_calc import get_current_dasha
from datetime import datetime

current = get_current_dasha(chart, datetime(2026, 3, 8))
print(f"Mahadasha:       {current[0].lord.name}")   # e.g., SATURN
print(f"Antardasha:      {current[1].lord.name}")   # e.g., VENUS
print(f"Pratyantardasha: {current[2].lord.name}")   # e.g., KETU
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chart` | `BirthChart` | required | A calculated birth chart |
| `date` | `datetime` | `now()` | Date to query |
| `levels` | `int` | `3` | How many levels to return (1-3) |

**Returns:** `list[DashaPeriod]` — one entry per active level.

---

## Panchanga

### `calculate_panchanga()`

Calculate the daily Panchanga (five-element Vedic calendar).

```python
from vedic_calc import calculate_panchanga

p = calculate_panchanga(
    year=2026, month=3, day=8,
    latitude=19.076, longitude=72.878,
    timezone_offset=5.5,
)

print(f"Vara:      {p.vara}")
print(f"Tithi:     {p.tithi_name}")
print(f"Nakshatra: {p.nakshatra.name}")
print(f"Yoga:      {p.yoga_name}")
print(f"Karana:    {p.karana_name}")
print(f"Sunrise:   {p.sunrise}")
print(f"Sunset:    {p.sunset}")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `year` | `int` | required | Calendar year |
| `month` | `int` | required | Month (1-12) |
| `day` | `int` | required | Day (1-31) |
| `latitude` | `float` | required | Geographic latitude |
| `longitude` | `float` | required | Geographic longitude |
| `timezone_offset` | `float` | `0.0` | UTC offset in hours |
| `ayanamsa` | `Ayanamsa` | `LAHIRI` | Precession correction mode |

**Returns:** `PanchangaInfo`

---

## Chart Rendering

### `render_south_indian()`

Render a South Indian style kundali as ASCII art.

```python
from vedic_calc import calculate_chart, render_south_indian

chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
print(render_south_indian(chart))
```

**Returns:** `str` — multi-line ASCII art with signs in fixed positions, planets placed in their signs.

### `render_north_indian()`

Render a North Indian style kundali as ASCII art.

```python
from vedic_calc import render_north_indian
print(render_north_indian(chart))
```

**Returns:** `str` — multi-line ASCII art with houses in fixed positions (H1 at top), signs rotating.

### `render_svg()`

Render a kundali as an SVG image string.

```python
from vedic_calc import render_svg

# South Indian (default)
svg = render_svg(chart, style="south")

# North Indian
svg = render_svg(chart, style="north")

# Save to file
with open("chart.svg", "w") as f:
    f.write(svg)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chart` | `BirthChart` | required | A calculated birth chart |
| `style` | `str` | `"south"` | `"south"` or `"north"` |

**Returns:** `str` — complete SVG markup, ready to embed in HTML or save as `.svg`.

---

## Data Models

All models are **frozen** (immutable) and **JSON-serializable**.

### `BirthChart`

The complete birth chart.

```python
chart.planets          # dict[Planet, PlanetPosition] — all 9 planets
chart.houses           # list[HousePosition] — 12 houses
chart.ascendant        # PlanetPosition — the rising sign
chart.ayanamsa         # Ayanamsa — which mode was used
chart.ayanamsa_degrees # float — ayanamsa value in degrees
chart.birth_datetime   # datetime — birth date/time (local)
chart.latitude         # float
chart.longitude        # float
chart.timezone_offset  # float

# Serialize to JSON
json_str = chart.model_dump_json(indent=2)

# Convert to dict
data = chart.model_dump()
```

### `PlanetPosition`

A planet's position in the sidereal zodiac.

```python
pos = chart.planets[Planet.MOON]

pos.planet            # Planet.MOON
pos.longitude         # 192.55 (sidereal degrees, 0-360)
pos.sign              # Sign.LIBRA
pos.degree_in_sign    # 12.55 (degrees within the sign, 0-30)
pos.nakshatra_info    # NakshatraInfo (see below)
pos.is_retrograde     # False
```

### `NakshatraInfo`

Nakshatra (lunar mansion) details.

```python
nak = pos.nakshatra_info

nak.nakshatra            # Nakshatra.SWATI
nak.pada                 # 2 (quarter, 1-4)
nak.lord                 # Planet.RAHU (ruling planet)
nak.degree_in_nakshatra  # 5.88 (degrees within this nakshatra)
```

### `HousePosition`

A house in the chart (Whole Sign system).

```python
house = chart.houses[0]  # 1st house

house.house_number  # 1
house.sign          # Sign.TAURUS
house.lord          # Planet.VENUS
```

### `DashaPeriod`

A single planetary period.

```python
period.lord            # Planet.SATURN
period.level           # "mahadasha", "antardasha", or "pratyantardasha"
period.start           # datetime(2016, 4, 4, ...)
period.end             # datetime(2035, 4, 5, ...)
period.duration_years  # 19.0
```

### `PanchangaInfo`

Daily five-element Vedic calendar.

```python
p.date            # datetime — the date
p.vara            # "Sunday (Ravivara)"
p.tithi_number    # 20 (1-30)
p.tithi_name      # "Krishna Panchami"
p.nakshatra       # Nakshatra.SWATI
p.yoga_number     # 12 (1-27)
p.yoga_name       # "Dhruva"
p.karana_number   # 39 (1-60)
p.karana_name     # "Kaulava"
p.sunrise         # datetime or None
p.sunset          # datetime or None
```

---

## Enumerations

### `Planet`

```python
from vedic_calc.core.constants import Planet

Planet.SUN      # 0
Planet.MOON     # 1
Planet.MARS     # 2
Planet.MERCURY  # 3
Planet.JUPITER  # 4
Planet.VENUS    # 5
Planet.SATURN   # 6
Planet.RAHU     # 7
Planet.KETU     # 8
```

### `Sign`

```python
from vedic_calc.core.constants import Sign

Sign.ARIES       # 1
Sign.TAURUS      # 2
# ... through ...
Sign.PISCES      # 12
```

### `Nakshatra`

```python
from vedic_calc.core.constants import Nakshatra

Nakshatra.ASHWINI   # 1
Nakshatra.BHARANI   # 2
# ... through ...
Nakshatra.REVATI    # 27
```

### `Ayanamsa`

```python
from vedic_calc.core.constants import Ayanamsa

Ayanamsa.LAHIRI              # 1 — most common in India
Ayanamsa.RAMAN               # 3
Ayanamsa.KP                  # 5 — Krishnamurti Paddhati
Ayanamsa.TRUE_CHITRAPAKSHA   # 27
```

---

## Lookup Tables

```python
from vedic_calc.core.constants import (
    SIGN_LORDS,            # {Sign.ARIES: Planet.MARS, ...}
    NAKSHATRA_LORDS,       # {Nakshatra.ASHWINI: Planet.KETU, ...}
    PLANET_NAMES,          # {Planet.SUN: "Sun (Surya)", ...}
    SIGN_NAMES,            # {Sign.ARIES: "Aries (Mesha)", ...}
    NAKSHATRA_NAMES,       # {Nakshatra.ASHWINI: "Ashwini", ...}
    VIMSOTTARI_YEARS,      # {Planet.KETU: 7, Planet.VENUS: 20, ...}
    VIMSOTTARI_ORDER,      # [Planet.KETU, Planet.VENUS, Planet.SUN, ...]
    TITHI_NAMES,           # {1: "Shukla Pratipada", ..., 30: "Amavasya"}
    YOGA_NAMES,            # {1: "Vishkambha", ..., 27: "Vaidhriti"}
    KARANA_NAMES,          # {1: "Kimstughna", ..., 60: "Nagava"}
    VARA_NAMES,            # {0: "Monday (Somavara)", ..., 6: "Sunday (Ravivara)"}
    PLANET_ABBREVIATIONS,  # {Planet.SUN: "Su", ...}
    SIGN_ABBREVIATIONS,    # {Sign.ARIES: "Ar", ...}
)
```
