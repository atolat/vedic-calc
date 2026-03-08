# API Reference

## Main Function

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
    SIGN_LORDS,        # {Sign.ARIES: Planet.MARS, ...}
    NAKSHATRA_LORDS,   # {Nakshatra.ASHWINI: Planet.KETU, ...}
    PLANET_NAMES,      # {Planet.SUN: "Sun (Surya)", ...}
    SIGN_NAMES,        # {Sign.ARIES: "Aries (Mesha)", ...}
    NAKSHATRA_NAMES,   # {Nakshatra.ASHWINI: "Ashwini", ...}
    VIMSOTTARI_YEARS,  # {Planet.KETU: 7, Planet.VENUS: 20, ...}
    VIMSOTTARI_ORDER,  # [Planet.KETU, Planet.VENUS, Planet.SUN, ...]
)
```
