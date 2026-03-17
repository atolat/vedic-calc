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

## Divisional Charts

### `calculate_divisional_chart()`

Calculate a divisional (varga) chart.

```python
from vedic_calc import calculate_chart, calculate_divisional_chart

chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
navamsa = calculate_divisional_chart(chart, division=9)

for planet, pos in navamsa.planets.items():
    print(f"{planet.name}: {pos.sign.name}")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chart` | `BirthChart` | required | A calculated birth chart |
| `division` | `int` | required | Division number: 2,3,4,7,9,10,12,16,20,24,27,30,40,45,60 |

**Returns:** `DivisionalChart`

---

## Aspects

### `calculate_aspects()`

Calculate planetary aspects (drishti) in a chart.

```python
from vedic_calc import calculate_chart, calculate_aspects

chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
aspects = calculate_aspects(chart)

for a in aspects:
    print(f"{a.aspecting_planet.name} aspects house {a.aspected_house} ({a.aspect_type})")
```

**Returns:** `list[AspectInfo]` — all aspects from all planets, including special aspects of Mars, Jupiter, and Saturn.

---

## Combustion

### `calculate_combustion()`

Check which planets are combust (too close to the Sun).

```python
from vedic_calc import calculate_chart, calculate_combustion

chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
combustion = calculate_combustion(chart)

for c in combustion:
    if c.is_combust:
        print(f"{c.planet.name} is combust ({c.angular_distance:.1f}° from Sun)")
```

**Returns:** `list[CombustionStatus]` — one per planet (excluding Sun, Rahu, Ketu).

---

## Planetary States

### `calculate_planet_states()`

Calculate the dignity and special states of each planet (exalted, debilitated, own sign, vargottama, etc.).

```python
from vedic_calc import calculate_chart, calculate_planet_states

chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
states = calculate_planet_states(chart)

for planet, state in states.items():
    print(f"{planet.name}: {state.dignity}, vargottama={state.is_vargottama}")
```

**Returns:** `dict[Planet, PlanetState]`

---

## House Analysis

### `analyze_houses()`

Get comprehensive analysis for all 12 houses.

```python
from vedic_calc import calculate_chart, analyze_houses

chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
houses = analyze_houses(chart)

for h in houses:
    print(f"House {h.house_number}: {h.sign.name}, lord={h.lord.name}, "
          f"occupants={[p.name for p in h.occupants]}")
```

**Returns:** `list[HouseAnalysis]` — 12 entries with sign, lord, occupants, aspecting planets, house category.

---

## Transits

### `calculate_transit_chart()`

Calculate current planetary positions (transit chart).

```python
from vedic_calc import calculate_transit_chart

transit = calculate_transit_chart(
    year=2026, month=3, day=17,
    hour=12, minute=0,
    latitude=19.076, longitude=72.878,
    timezone_offset=5.5,
)

for planet, pos in transit.planets.items():
    print(f"{planet.name}: {pos.sign.name} {pos.degree_in_sign:.1f}°")
```

**Returns:** `TransitChart`

---

## Yogas

### `detect_yogas()`

Detect ~24 classical yogas in a chart.

```python
from vedic_calc import calculate_chart, detect_yogas

chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
yogas = detect_yogas(chart)

for y in yogas:
    if y.is_present:
        print(f"{y.name} ({y.category}): {y.description}")
```

**Returns:** `list[YogaResult]` — includes both present and absent yogas.

---

## Doshas

### `detect_doshas()`

Detect 6 classical doshas (afflictions) with cancellation checking.

```python
from vedic_calc import calculate_chart, detect_doshas

chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
doshas = detect_doshas(chart)

for d in doshas:
    status = "PRESENT" if d.is_present else "absent"
    cancelled = " (cancelled)" if d.is_cancelled else ""
    print(f"{d.name}: {status}{cancelled}")
```

**Returns:** `list[DoshaResult]` — with is_present, is_cancelled, severity, description.

---

## Compatibility

### `calculate_compatibility()`

Calculate Ashtakoot Milan (8-factor North Indian compatibility).

```python
from vedic_calc import calculate_chart, calculate_compatibility

chart1 = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
chart2 = calculate_chart(1992, 7, 20, 14, 0, 0, 19.076, 72.878, 5.5)

result = calculate_compatibility(chart1, chart2)
print(f"Total: {result.total_points}/36")
for factor in result.factors:
    print(f"  {factor.name}: {factor.obtained}/{factor.maximum}")
```

**Returns:** `CompatibilityResult` — 8 factor scores + total.

### `calculate_porutham()`

Calculate 10-factor South Indian compatibility.

```python
from vedic_calc import calculate_chart, calculate_porutham
result = calculate_porutham(chart1, chart2)
```

**Returns:** `PoruthamResult` — 10 factor results + summary.

---

## Strength

### `calculate_shadbala()`

Calculate six-fold planetary strength (Shadbala).

```python
from vedic_calc import calculate_chart, calculate_shadbala

chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
strengths = calculate_shadbala(chart)

for planet, sb in strengths.items():
    print(f"{planet.name}: total={sb.total_rupas:.2f} rupas "
          f"(required={sb.required_rupas:.2f})")
```

**Returns:** `dict[Planet, ShadbalaResult]` — with all 6 components and total.

### `calculate_ashtakavarga()`

Calculate Ashtakavarga (benefic point grid).

```python
from vedic_calc import calculate_chart, calculate_ashtakavarga

chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
av = calculate_ashtakavarga(chart)

# Sarvashtakavarga (sum across all planets per sign)
for sign, points in av.sarvashtakavarga.items():
    print(f"{sign.name}: {points} bindus")
```

**Returns:** `AshtakavargaResult` — with BAV per planet and SAV totals.

---

## Muhurta

### `calculate_muhurta()`

Calculate daily muhurta windows (Rahu Kalam, Yamagandam, Abhijit, Choghadiya, Hora).

```python
from vedic_calc import calculate_muhurta

m = calculate_muhurta(2026, 3, 17, 19.076, 72.878, 5.5)
rk_start, rk_end = m.rahu_kalam
print(f"Rahu Kalam: {rk_start.strftime('%H:%M')} - {rk_end.strftime('%H:%M')}")
print(f"Abhijit: {m.abhijit_muhurta[0].strftime('%H:%M')} - {m.abhijit_muhurta[1].strftime('%H:%M')}")
```

**Returns:** `MuhurtaInfo`

### `find_muhurta_windows()`

Search for auspicious windows across a date range.

```python
from vedic_calc import find_muhurta_windows

result = find_muhurta_windows(
    activity="marriage",
    start_date=(2026, 4, 1),
    end_date=(2026, 4, 30),
    latitude=19.076, longitude=72.878,
    timezone_offset=5.5,
    natal_moon_nakshatra=4,  # Rohini
    natal_moon_sign=2,       # Taurus
    max_results=5,
)

for w in result.windows:
    print(f"{w.start.date()} score={w.score:.0f}: {', '.join(w.reasoning)}")
```

**Returns:** `MuhurtaSearchResult` — ranked windows with panchanga details and reasoning.

---

## Prashna (Horary)

### `cast_prashna_chart()`

Cast a chart for the moment a question is asked.

```python
from vedic_calc import cast_prashna_chart

chart = cast_prashna_chart(
    year=2026, month=3, day=17,
    hour=14, minute=30,
    latitude=19.076, longitude=72.878,
    timezone_offset=5.5,
)
```

**Returns:** `BirthChart` — same structure as a birth chart, but for the question moment.

### `evaluate_prashna()`

Get a full Prashna verdict (Tajika yogas + chart analysis).

```python
from vedic_calc import cast_prashna_chart, evaluate_prashna

chart = cast_prashna_chart(2026, 3, 17, 14, 30, 0, 19.076, 72.878, 5.5)
verdict = evaluate_prashna(chart, query_house=10)  # Career question

print(f"Verdict: {verdict.verdict}")  # "favorable" / "unfavorable" / "mixed"
for reason in verdict.reasoning:
    print(f"  - {reason}")
```

**Returns:** `PrashnaVerdict` — with verdict, Tajika yogas found, and reasoning.

### `detect_tajika_yogas()`

Detect Tajika yogas between two planets.

```python
from vedic_calc import cast_prashna_chart, detect_tajika_yogas

chart = cast_prashna_chart(2026, 3, 17, 14, 30, 0, 19.076, 72.878, 5.5)
yogas = detect_tajika_yogas(chart, query_house=10)

for y in yogas:
    if y.is_present:
        print(f"{y.name}: {y.significance} — {y.description}")
```

**Returns:** `list[TajikaYoga]`

---

## Jaimini

### `calculate_chara_karakas()`

Calculate the 8 Chara (variable) Karakas.

```python
from vedic_calc import calculate_chart, calculate_chara_karakas

chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
karakas = calculate_chara_karakas(chart)

for k in karakas:
    print(f"{k.karaka_name}: {k.planet.name} ({k.degree_in_sign:.1f}°)")
```

**Returns:** `list[CharaKaraka]` — 8 karakas ranked by degree.

### `calculate_arudha_padas()`

Calculate Arudha Padas for all 12 houses.

```python
from vedic_calc import calculate_chart, calculate_arudha_padas

chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
arudhas = calculate_arudha_padas(chart)

for a in arudhas:
    print(f"A{a.house_number} ({a.name}): {a.sign.name}")
```

**Returns:** `list[ArudhaPada]` — with house number, sign, named pada (AL, A7/Darapada, etc.).

---

## Varshaphal (Solar Return)

### `calculate_varshaphal()`

Calculate annual predictions chart (solar return).

```python
from vedic_calc import calculate_chart, calculate_varshaphal

birth_chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
varsha = calculate_varshaphal(birth_chart, target_year=2026)

print(f"Year Lord: {varsha.year_lord.name}")
print(f"Muntha: {varsha.muntha.sign.name} (house {varsha.muntha.house})")
for md in varsha.mudda_dasha[:3]:
    print(f"  {md.lord.name}: {md.start.date()} - {md.end.date()}")
```

**Returns:** `VarshaphalResult` — with annual chart, muntha, year lord, and mudda dasha periods.

---

## KP (Krishnamurti Paddhati)

### `calculate_kp_chart()`

Calculate a KP chart with Placidus cusps and sub-lords.

```python
from vedic_calc import calculate_chart, calculate_kp_chart

chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
kp = calculate_kp_chart(chart)

for cusp in kp.cusps:
    print(f"House {cusp.house_number}: {cusp.sign.name} {cusp.degree:.1f}° "
          f"(sub-lord: {cusp.sublord.name})")
```

**Returns:** `KPChartResult` — with cusps, planet sub-lords, and significators.

### `get_kp_sublord()`

Get the KP sub-lord for any zodiacal longitude.

```python
from vedic_calc import get_kp_sublord

info = get_kp_sublord(45.0)  # 15° Taurus
print(f"Star lord: {info.star_lord.name}, Sub-lord: {info.sub_lord.name}")
```

**Returns:** `KPSublordInfo`

---

## Numerology

### `calculate_numerology()`

Calculate Chaldean numerology numbers.

```python
from vedic_calc import calculate_numerology

result = calculate_numerology(
    year=1990, month=3, day=15,
    full_name="Rahul Sharma",
)

print(f"Destiny: {result.destiny_number}")
print(f"Radical: {result.radical_number}")
print(f"Name: {result.name_number}")
print(f"Lucky numbers: {result.lucky_numbers}")
```

**Returns:** `NumerologyResult` — with destiny, radical, name numbers, lucky/unlucky numbers, and compatibility.

---

## Additional Dasha Systems

### `calculate_yogini_dasha()`

Calculate Yogini Dasha (36-year cycle).

```python
from vedic_calc import calculate_chart, calculate_yogini_dasha

chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
periods = calculate_yogini_dasha(chart)
```

**Returns:** `list[DashaPeriod]`

### `calculate_ashtottari_dasha()`

Calculate Ashtottari Dasha (108-year cycle, 8 planets).

```python
from vedic_calc import calculate_chart, calculate_ashtottari_dasha

chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
periods = calculate_ashtottari_dasha(chart)
```

**Returns:** `list[DashaPeriod]`

### `calculate_narayana_dasha()`

Calculate Narayana Dasha (Jaimini sign-based).

```python
from vedic_calc import calculate_chart, calculate_narayana_dasha

chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
periods = calculate_narayana_dasha(chart)
```

**Returns:** `list[DashaPeriod]`

---

## Special Calculations

### `calculate_special_lagnas()`

Calculate Bhava Lagna, Hora Lagna, Ghati Lagna, and Vighati Lagna.

```python
from vedic_calc import calculate_chart, calculate_special_lagnas

chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
lagnas = calculate_special_lagnas(chart)

for l in lagnas:
    print(f"{l.name}: {l.sign.name} {l.degree_in_sign:.1f}°")
```

**Returns:** `list[SpecialLagna]`

### `calculate_upagrahas()`

Calculate the 5 Sun-based upagrahas (Dhuma, Vyatipata, Parivesha, Chapa, Upaketu).

```python
from vedic_calc import calculate_chart, calculate_upagrahas

chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
upagrahas = calculate_upagrahas(chart)

for u in upagrahas:
    print(f"{u.name}: {u.sign.name} {u.degree_in_sign:.1f}°")
```

**Returns:** `list[UpagrahaPosition]`

### `calculate_sahams()`

Calculate Arabic Parts / Sahams (Punya, Vidya, Yashas, etc.).

```python
from vedic_calc import calculate_chart, calculate_sahams

chart = calculate_chart(1990, 3, 15, 10, 30, 0, 19.076, 72.878, 5.5)
sahams = calculate_sahams(chart)

for s in sahams:
    print(f"{s.name}: {s.sign.name} {s.degree_in_sign:.1f}°")
```

**Returns:** `list[SahamPosition]`

### `get_festivals()`

Detect Hindu festivals in a given year.

```python
from vedic_calc import get_festivals

festivals = get_festivals(2026, 19.076, 72.878, 5.5)
for f in festivals:
    print(f"{f.date.date()}: {f.name} — {f.description}")
```

**Returns:** `list[FestivalInfo]`

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
