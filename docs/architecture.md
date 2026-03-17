# Architecture

## Overview

vedic-calc follows a layered architecture with strict dependency boundaries. Every module above the core layer is a pure-function consumer of sidereal longitudes — it never touches the Swiss Ephemeris directly.

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Public API                                 │
│                                                                     │
│  Chart        calculate_chart()  render_south_indian()  render_svg()│
│               calculate_divisional_chart()  calculate_aspects()     │
│               calculate_combustion()  calculate_planet_states()     │
│               analyze_houses()  calculate_transit_chart()           │
│               calculate_special_lagnas()  calculate_upagrahas()     │
│               calculate_sahams()  calculate_sade_sati()             │
│               calculate_chandrashtama()  calculate_functional_nature()│
│               calculate_chalit_chart()  calculate_sudarshana_chakra()│
│               calculate_event_timeline()                            │
│                                                                     │
│  Dasha        calculate_dasha()  get_current_dasha()                │
│               calculate_yogini_dasha()  calculate_ashtottari_dasha()│
│               calculate_narayana_dasha()                            │
│               (levels=4: sookshmadasha, levels=5: pranadasha)       │
│                                                                     │
│  Panchanga    calculate_panchanga()  get_festivals()                │
│               get_anandadi_yoga()  calculate_panchanga_transitions()│
│                                                                     │
│  Yoga/Dosha   detect_yogas()  detect_doshas()                      │
│               score_yogas()  score_doshas()                        │
│                                                                     │
│  Strength     calculate_shadbala()  calculate_ashtakavarga()       │
│                                                                     │
│  Compatibility calculate_compatibility()  calculate_porutham()     │
│               calculate_avakhada()  calculate_papasamyam()         │
│                                                                     │
│  Muhurta      calculate_muhurta()  find_muhurta_windows()          │
│               get_disha_shool()                                    │
│                                                                     │
│  Prashna      cast_prashna_chart()  evaluate_prashna()             │
│               detect_tajika_yogas()                                 │
│                                                                     │
│  Jaimini      calculate_chara_karakas()  calculate_arudha_padas()  │
│                                                                     │
│  Varshaphal   calculate_varshaphal()                               │
│               calculate_panchavargeeya_bala()                      │
│                                                                     │
│  KP System    calculate_kp_chart()  get_kp_sublord()               │
│               get_kp_significators()  get_kp_house_significators() │
│                                                                     │
│  Numerology   calculate_numerology()                               │
├─────────────────────────────────────────────────────────────────────┤
│                       Calculation Layer                              │
│                                                                     │
│  chart/     calculator  renderer  houses  aspects  combustion       │
│             states  transits  divisional  upagrahas  special_lagnas │
│             sahams  sade_sati  chandrashtama  functional  chalit    │
│             relationships  sudarshana  timeline                     │
│                                                                     │
│  dasha/     calculator  yogini  ashtottari  narayana                │
│  panchanga/ calculator  festivals  transitions                      │
│  muhurta/   calculator  solver                                      │
│  prashna/   chart  tajika  evaluator                                │
│  jaimini/   karakas  arudha                                         │
│  kp/        calculator  houses  sublords  significators              │
│  compatibility/ calculator  porutham  avakhada  constants           │
│                 papasamyam                                          │
│  strength/  ashtakavarga  shadbala                                  │
│  dosha/     calculator  scorer                                      │
│  yoga/      calculator  scorer                                      │
│  varshaphal/ calculator                                             │
│  numerology/ calculator                                             │
├─────────────────────────────────────────────────────────────────────┤
│                         Core Layer                                   │
│     types.py  │  constants.py  │  ephemeris.py  │  helpers.py       │
│     search.py                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                    Swiss Ephemeris (pyswisseph)                      │
│                   (NASA JPL ephemeris data)                          │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Boundary: ephemeris.py

The single most important design decision: **only `ephemeris.py` imports pyswisseph**. Everything else works with plain floats (longitudes in degrees).

This gives us:

- **Testability** -- mock `ephemeris.py` to test all chart logic without the Swiss Ephemeris
- **Swappability** -- could replace pyswisseph with another engine (REST API, WASM, etc.)
- **Simplicity** -- pyswisseph has a complex C-style API; we expose clean Python functions

### What ephemeris.py provides

| Function | Input | Output |
|----------|-------|--------|
| `_to_julian_day()` | year, month, day, hour | Julian Day float |
| `get_ayanamsa()` | Julian Day, mode | degrees (float) |
| `get_planet_longitude()` | Julian Day, planet, ayanamsa | (longitude, is_retrograde) |
| `get_ascendant()` | Julian Day, lat, lon, ayanamsa | longitude (float) |
| `get_sunrise_sunset()` | Julian Day, lat, lon | (sunrise_jd, sunset_jd) |
| `jd_to_datetime()` | Julian Day, timezone_offset | Python datetime |

## Data Flow

### Birth Chart

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

### Dasha (Planetary Periods)

```
BirthChart
    │
    ├── Moon's nakshatra lord → Starting mahadasha planet
    ├── Moon's degree in nakshatra / 13.333 → Elapsed fraction
    │
    ▼
  Vimsottari sequence (rotated to start from birth lord)
    │
    ├── 9 mahadashas (first one partial)
    ├── 81 antardashas (proportional subdivision)
    └── 729 pratyantardashas (one more level)
    │
    ▼
  list[DashaPeriod] (flat, chronological, with level field)
```

Additional dasha systems follow similar flows but use different period sequences:
- **Yogini Dasha** -- 8 yogini deities, 36-year total cycle, nakshatra-based start
- **Ashtottari Dasha** -- 8 planets (no Ketu), 108-year cycle, used when Rahu is in a kendra/trikona
- **Narayana Dasha** -- sign-based (not planet-based), starts from lagna sign, duration depends on sign lord position

### Panchanga

```
Date + Location
    │
    ├── get_sunrise_sunset() → Sunrise JD
    ├── get_planet_longitude(MOON) at sunrise → Moon sidereal lon
    ├── get_planet_longitude(SUN) at sunrise  → Sun sidereal lon
    │
    ▼
  Five computations:
    ├── (Moon - Sun) % 360 / 12  → Tithi (1-30)
    ├── Moon lon / 13.333        → Nakshatra (1-27)
    ├── (Moon + Sun) % 360 / 13.333 → Yoga (1-27)
    ├── (Moon - Sun) % 360 / 6   → Karana (1-60)
    └── datetime.weekday()       → Vara
    │
    ▼
  PanchangaInfo (Pydantic model)
```

### Chart Rendering

```
BirthChart
    │
    ├── Map planets to their signs
    ├── Map houses to grid positions
    │
    ▼
  ASCII (South/North Indian style)
    or
  SVG (South/North Indian style)
```

### Muhurta (Electional Timing)

```
Activity + Date Range + Location
    │
    ├── For each day:
    │     ├── calculate_panchanga()  → tithi, nakshatra, yoga, karana, vara
    │     ├── calculate_muhurta()    → Rahu Kalam, Yamagandam, Abhijit
    │     │
    │     ▼
    │   5-Layer Filter:
    │     ├── Tithi:     skip Rikta tithis (4, 9, 14); score good tithis +20
    │     ├── Vara:      match weekday to activity; score +15
    │     ├── Nakshatra: match to activity; score +20
    │     ├── Yoga:      skip Vyatipata, Vaidhriti; score +10
    │     └── Karana:    skip Vishti/Bhadra; score +10
    │     │
    │     ▼ (optional, if natal Moon provided)
    │   Personal Overlays:
    │     ├── Chandrabala (transit Moon sign from natal) → +15
    │     └── Tarabala (transit Moon nak from natal)     → +10
    │
    ▼
  MuhurtaSearchResult (windows sorted by score, 0-100)
```

### Prashna (Horary Astrology)

```
Question Moment (date, time, location)
    │
    ▼
  calculate_chart()  → BirthChart (for the question moment)
    │
    ├── Classify question → query house (career=10th, marriage=7th, etc.)
    ├── Identify query house lord + lagna lord
    ├── Calculate planetary dignity (exalted, debilitated, etc.)
    │
    ▼
  Tajika Yoga Detection (degree-based aspects, NOT Parashari sign-based):
    ├── Ithasala:  faster planet applying to slower → favorable
    ├── Easarapha: faster separating from slower   → unfavorable
    ├── Induvara:  no aspect between significators  → matter fails
    ├── Kamboola:  Moon transfers light             → success via intermediary
    └── Nakta:     heavier receives from lighter    → partial success
    │
    ▼
  PrashnaVerdict (verdict: favorable / unfavorable / mixed + reasoning)
```

### Strength Assessment

```
BirthChart
    │
    ├── Shadbala (6-fold strength):
    │     ├── Sthana Bala   → positional (sign, house, exaltation, etc.)
    │     ├── Dig Bala      → directional (Sun strong in 10th, etc.)
    │     ├── Kala Bala     → temporal (day/night, hora, year lord, etc.)
    │     ├── Cheshta Bala  → motional (speed, retrograde bonus)
    │     ├── Naisargika    → natural (Sun=60, Moon=51.43, etc.)
    │     └── Drik Bala     → aspectual (benefic/malefic aspect balance)
    │     │
    │     ▼
    │   ShadbalaResult per planet (total in rupas, is_strong flag)
    │
    ├── Ashtakavarga (8-source transit strength):
    │     ├── For each planet: 12 signs × 8 contributors → benefic dots
    │     ├── Sarvashtakavarga: sum across all planets per sign
    │     │
    │     ▼
    │   AshtakavargaResult (per-planet tables + sarva table)
```

### Compatibility

```
Chart A + Chart B
    │
    ├── Ashtakoot (North Indian, 8 factors, max 36 points):
    │     ├── Varna (1)  ├── Vasya (2)  ├── Tara (3)  ├── Yoni (4)
    │     ├── Graha Maitri (5)  ├── Gana (6)  ├── Bhakoot (7)
    │     └── Nadi (8)
    │     │
    │     ▼
    │   Total score / 36, compatibility level, Mangal Dosha check
    │
    ├── Porutham (South Indian, 10 factors):
    │     ├── Dina  ├── Gana  ├── Mahendra  ├── Stree Dirgha
    │     ├── Yoni  ├── Rasi  ├── Rasiyathipathi  ├── Vasya
    │     ├── Rajju  └── Vedha
    │     │
    │     ▼
    │   PoruthamResult (factor-by-factor pass/fail + overall assessment)
```

### Varshaphal (Solar Return)

```
BirthChart + Target Year
    │
    ├── Find exact Sun return moment (same sidereal longitude as birth)
    ├── Cast chart for that moment at current location
    ├── Calculate Muntha (progressed ascendant: birth lagna + years elapsed)
    ├── Detect Tajika yogas in the annual chart
    │
    ▼
  VarshaphalResult (annual chart + Muntha + Tajika yogas)
```

### KP System (Krishnamurti Paddhati)

```
Birth Details
    │
    ├── Calculate Placidus house cusps (not Whole Sign)
    ├── For each cusp and planet longitude:
    │     ├── Sign lord (standard)
    │     ├── Star lord (nakshatra lord)
    │     └── Sub lord (KP sublord from unequal subdivision table)
    │
    ▼
  KPChartResult (cusps with 3-level lordship + planets with sub-lords)
```

## Module Responsibilities

### Core Layer

#### `core/constants.py`
All enumerations and lookup tables. Data sourced from BPHS, Surya Siddhanta, Muhurta Chintamani, and standard panchanga practice.

- `Planet` -- 9 Navagraha (Sun through Ketu)
- `Sign` -- 12 Rashis (Aries through Pisces)
- `Nakshatra` -- 27 lunar mansions
- `Ayanamsa` -- precession correction modes (Lahiri, Raman, KP, True Chitrapaksha)
- Chart tables: sign lords, nakshatra lords, exaltation/debilitation degrees, moolatrikona
- Vimsottari tables: dasha years, dasha order, nakshatra-to-lord mapping
- Yogini/Ashtottari tables: period sequences and durations
- Panchanga tables: tithi names, yoga names, karana names, vara names
- Muhurta tables: Rahu Kalam slots, Yamagandam slots, Gulika Kalam slots, Choghadiya sequences
- Muhurta rules: good tithis/nakshatras/varas per activity, bad tithis/yogas/karanas
- Tajika tables: aspect orbs (conjunction, opposition, trine, square, sextile)
- Compatibility tables: Ashtakoot scoring tables, yoni pairs, gana compatibility
- Porutham tables: 10 South Indian compatibility factors
- Shadbala tables: dig bala, naisargika bala, kala bala weights
- Ashtakavarga tables: benefic-point maps for each planet
- KP tables: sublord division table (249 sub-divisions of the zodiac)
- Rendering tables: planet abbreviations, sign abbreviations, grid positions

#### `core/types.py`
Pydantic models for all data structures. All frozen (immutable), JSON-serializable.

| Model | Purpose |
|-------|---------|
| `NakshatraInfo` | Nakshatra + pada + lord |
| `PlanetPosition` | Longitude, sign, degree, nakshatra, retrograde flag |
| `HousePosition` | House number, sign, lord |
| `BirthChart` | Complete chart: planets, houses, ascendant, metadata |
| `DashaPeriod` | Planetary period with start/end dates and level |
| `PanchangaInfo` | Daily five-element calendar + sunrise/sunset |
| `DivisionalChart` | Varga chart with remapped sign placements |
| `AspectInfo` | Planetary aspect with type, orb, and strength |
| `CombustionStatus` | Planet's combustion state relative to the Sun |
| `PlanetState` | Dignity, combustion, retrograde, dispositor chain |
| `TransitChart` | Current sky positions relative to a natal chart |
| `HouseAnalysis` | House lord, occupants, aspects, strength assessment |
| `YogaResult` | Detected yoga with name, type, involved planets |
| `DoshaResult` | Detected dosha with severity and remedies |
| `MuhurtaInfo` | Daily Rahu Kalam, Yamagandam, Abhijit, Choghadiya |
| `MuhurtaWindow` | Scored auspicious window with panchanga breakdown |
| `MuhurtaSearchResult` | Ranked list of muhurta windows for an activity |
| `UpagrahaPosition` | Sub-planet (Dhuma, Vyatipata, etc.) position |
| `SpecialLagna` | Hora Lagna, Ghati Lagna, etc. with longitude |
| `CharaKaraka` | Jaimini variable significator (planet + karaka role) |
| `ArudhaPada` | Arudha pada for a house (sign placement) |
| `AshtakavargaResult` | Per-planet and sarva bindus per sign |
| `ShadbalaResult` | Six-fold strength breakdown per planet (in rupas) |
| `PoruthamFactor` | Single South Indian compatibility factor result |
| `PoruthamResult` | All 10 factors + overall compatibility assessment |
| `SahamPosition` | Arabic part (lot) position and sign |
| `FestivalInfo` | Festival name, date, type, and panchanga basis |
| `TajikaYoga` | Tajika aspect yoga (name, planets, significance) |
| `PrashnaVerdict` | Horary verdict with query house, yogas, reasoning |
| `MunthaInfo` | Progressed ascendant for varshaphal |
| `VarshaphalResult` | Solar return chart + Muntha + annual Tajika yogas |
| `KPSublordInfo` | Star lord + sub lord for a longitude |
| `KPHouseCusp` | Placidus cusp with sign/star/sub lords |
| `KPPlanetInfo` | Planet with KP-style lordship chain |
| `KPChartResult` | Full KP chart with cusps and planet sub-lords |
| `NumerologyResult` | Name/birth numbers with Chaldean analysis |
| `SadeSatiResult` | Sade Sati status, phase, and period dates |
| `ChandrashtamaResult` | Chandrashtama active flag and window times |
| `AvakhadaInfo` | Birth summary (Varna, Vasya, Yoni, Gana, Nadi) |
| `DishaShoolInfo` | Inauspicious travel direction for the day |
| `AnandadiYogaInfo` | Anandadi yoga from tithi-vara combination |
| `PlanetRelationshipResult` | Natural, temporal, compound relationships |
| `FunctionalNature` | Functional benefic/malefic status per planet |
| `ChalitChart` | Bhava Chalit house cusps and planet placements |
| `TransitionMoment` | Exact datetime of a panchanga element change |
| `PanchangaTransitions` | All transition times within a day |
| `ScoredYogaResult` | Yoga with strength score (0-100) |
| `ScoredDoshaResult` | Dosha with severity score (0-100) |
| `TimelineEvent` | Single event in a chronological timeline |
| `EventTimeline` | Merged, sorted list of life events |
| `KPSignificatorDetail` | 4-level KP significators for a planet |
| `KPHouseSignificators` | Significator planets for a KP house |
| `SudarshanaChakra` | 3-ring house overlay from Lagna/Moon/Sun |
| `PapasamyamResult` | Malefic balance comparison for two charts |
| `PanchavargeeaBala` | 5-fold Varshaphal strength assessment |

#### `core/ephemeris.py`
Thin wrapper around pyswisseph. **Only module that imports `swisseph`.** All other modules receive plain floats (degrees) and Python datetimes.

#### `core/helpers.py`
Shared utilities used across multiple modules. Includes `sign_distance()`, `planet_house()`, degree normalization, and other common calculations.

#### `core/search.py`
Bisection search utilities for astronomical transitions. Given a function that changes value between two Julian Days, finds the exact transition moment to a configurable precision.

---

### Chart Module (`chart/`)

#### `chart/calculator.py`
Main birth chart entry point. Pure functions that transform longitudes into structured astrology data.

- `calculate_chart()` -- public API, returns `BirthChart`
- `longitude_to_sign()` -- 45.0 degrees to Taurus
- `longitude_to_nakshatra_info()` -- 45.0 degrees to Rohini pada 2
- `build_houses()` -- Whole Sign houses from ascendant

#### `chart/renderer.py`
Visual chart rendering. No external dependencies.

- `render_south_indian()` -- ASCII art, signs in fixed positions (standard South Indian grid)
- `render_north_indian()` -- ASCII art, houses in fixed positions (diamond layout)
- `render_svg()` -- SVG markup for web/mobile display

#### `chart/divisional.py`
Divisional chart (varga) computation. Takes a BirthChart and divides each planet's longitude by the varga factor to produce a remapped chart.

- `calculate_divisional_chart()` -- supports D-1 through D-60 (Rasi, Hora, Drekkana, Chaturthamsa, Saptamsa, Navamsa, Dashamsa, Dwadashamsa, Shodashamsa, Vimshamsa, Chaturvimshamsa, Saptavimshamsa, Trimshamsa, Khavedamsa, Akshavedamsa, Shastiamsha)

#### `chart/aspects.py`
Planetary aspect (drishti) calculation. Vedic aspects are sign-based, not degree-based (unlike Western astrology). Every planet aspects the 7th house from it; Mars also aspects 4th and 8th; Jupiter also aspects 5th and 9th; Saturn also aspects 3rd and 10th.

- `calculate_aspects()` -- returns list of `AspectInfo` for all active aspects in a chart

#### `chart/combustion.py`
Combustion detection. A planet is combust when it is too close to the Sun (within specific orb limits that vary per planet). Combust planets lose strength.

- `calculate_combustion()` -- returns `CombustionStatus` for each planet

#### `chart/states.py`
Planetary dignity and state assessment. Evaluates each planet's condition: own sign, exaltation, debilitation, moolatrikona, friend/enemy sign, retrograde status, combustion, and dispositor chain.

- `calculate_planet_states()` -- returns `PlanetState` for each planet

#### `chart/houses.py`
House-level analysis. For each house, identifies the lord, occupants, aspecting planets, and produces a qualitative strength assessment.

- `analyze_houses()` -- returns `HouseAnalysis` for all 12 houses

#### `chart/transits.py`
Transit chart computation. Calculates current planetary positions and overlays them on a natal chart to identify active transits.

- `calculate_transit_chart()` -- returns `TransitChart` with transit-to-natal relationships

#### `chart/special_lagnas.py`
Special ascendant calculations used in Jaimini and advanced Parashari analysis.

- `calculate_special_lagnas()` -- computes Hora Lagna, Ghati Lagna, Bhava Lagna, Sree Lagna, Vighati Lagna

#### `chart/upagrahas.py`
Sub-planet (upagraha) calculations. These are mathematically derived shadow points, not physical bodies. Includes Dhuma, Vyatipata, Parivesha, Chapa (Indrachapa), and Upaketu.

- `calculate_upagrahas()` -- returns positions of all 5 standard upagrahas

#### `chart/sahams.py`
Arabic parts (sahams/lots). Mathematical points calculated from the longitudes of three chart factors (typically ascendant, planet A, planet B). Used in Tajika and Varshaphal.

- `calculate_sahams()` -- returns common sahams (Punya, Vidya, Yasas, Mitra, Mahatmya, Asha, Samartha, Bhratri, Gaurava, Pitri, Rajya, Matri, Putra, Jeeva, Karma, Roga, Kali, Sastra, Bandhu, Mrityu, Paradesa)

#### `chart/sade_sati.py`
Sade Sati detection and period calculation. Identifies when Saturn transits through the 12th, 1st, and 2nd signs from the natal Moon.

- `calculate_sade_sati()` -- returns `SadeSatiResult`

#### `chart/chandrashtama.py`
Chandrashtama window detection. Identifies when the Moon transits the 8th sign from the natal Moon (inauspicious ~2.5 day window).

- `calculate_chandrashtama()` -- returns `ChandrashtamaResult`

#### `chart/relationships.py`
Panchadha Maitri (5-fold planet relationships). Computes natural, temporal, and compound relationships between all planet pairs.

- Returns `PlanetRelationshipResult`

#### `chart/functional.py`
Functional nature of planets per ascendant. Classifies each planet as functional benefic, malefic, or neutral based on the houses it rules from the ascendant sign.

- `calculate_functional_nature()` -- returns `FunctionalNature` per planet

#### `chart/chalit.py`
Bhava Chalit chart with equal-house cusps. Redistributes planets into bhavas based on mid-cusp boundaries (can differ from Whole Sign placement).

- `calculate_chalit_chart()` -- returns `ChalitChart`

#### `chart/sudarshana.py`
3-ring Sudarshana Chakra from Lagna, Moon, and Sun. Overlays three reference frames for combined house analysis.

- `calculate_sudarshana_chakra()` -- returns `SudarshanaChakra`

#### `chart/timeline.py`
Chronological event timeline. Merges dasha periods, Sade Sati windows, Saturn/Jupiter returns, and other timed events into a single sorted timeline.

- `calculate_event_timeline()` -- returns `EventTimeline`

---

### Dasha Module (`dasha/`)

#### `dasha/calculator.py`
Vimsottari Dasha -- the most widely used planetary period system. 120-year cycle based on the Moon's nakshatra at birth.

- `calculate_dasha()` -- full dasha timeline (mahadasha + antardasha + pratyantardasha)
- `get_current_dasha()` -- active periods for a specific date

#### `dasha/yogini.py`
Yogini Dasha -- 36-year cycle based on 8 yogini deities. Shorter cycle makes it useful for timing events in shorter lifespans or for confirmation alongside Vimsottari.

- `calculate_yogini_dasha()` -- full Yogini period timeline

#### `dasha/ashtottari.py`
Ashtottari Dasha -- 108-year cycle using 8 planets (excludes Ketu). Traditionally used when Rahu occupies a kendra or trikona from the lagna lord.

- `calculate_ashtottari_dasha()` -- full Ashtottari period timeline

#### `dasha/narayana.py`
Narayana Dasha -- Jaimini's sign-based dasha system. Unlike planet-based dashas, periods are ruled by signs (not planets), and the sequence depends on whether the lagna is odd or even.

- `calculate_narayana_dasha()` -- sign-based period timeline

---

### Panchanga Module (`panchanga/`)

#### `panchanga/calculator.py`
Daily Vedic calendar (panchanga) computation. The five limbs: Tithi, Nakshatra, Yoga, Karana, Vara. All computed at the sunrise moment for the given location.

- `calculate_panchanga()` -- computes all five panchanga elements for a date/location

#### `panchanga/festivals.py`
Hindu festival detection based on panchanga data. Maps specific tithi + month combinations to festival names (e.g., Chaitra Shukla 9 = Rama Navami).

- `get_festivals()` -- returns festivals for a given date/panchanga

#### `panchanga/transitions.py`
Exact panchanga element transition times. Uses bisection search to find the precise moment each tithi, nakshatra, yoga, and karana changes within a day.

- `calculate_panchanga_transitions()` -- returns `PanchangaTransitions`

---

### Muhurta Module (`muhurta/`)

#### `muhurta/calculator.py`
Daily muhurta (electional timing) calculations. Computes inauspicious windows and auspicious periods from sunrise/sunset.

- `calculate_muhurta()` -- returns Rahu Kalam, Yamagandam, Gulika Kalam, Abhijit Muhurta, Choghadiya (day + night), Hora lord

#### `muhurta/solver.py`
Muhurta constraint solver. Given an activity, date range, and location, iterates each day, applies a 5-layer panchanga filter, optionally applies personal overlays (Chandrabala, Tarabala), and returns scored/ranked auspicious windows.

- `find_muhurta_windows()` -- returns `MuhurtaSearchResult` with top-N windows

---

### Prashna Module (`prashna/`)

#### `prashna/chart.py`
Prashna (horary) chart casting. A Prashna chart is structurally identical to a birth chart -- the only difference is that it represents the moment a question is asked, not the moment of birth.

- `cast_prashna_chart()` -- thin wrapper around `calculate_chart()` for the question moment

#### `prashna/tajika.py`
Tajika yoga detection for Prashna and Varshaphal. Tajika yogas use degree-based aspects with specific orbs (unlike Parashari sign-based aspects). Implements the 5 most critical verdict-determining yogas.

- `detect_tajika_yogas()` -- detects Ithasala, Easarapha, Induvara, Kamboola, Nakta

#### `prashna/evaluator.py`
Prashna verdict engine. Combines the query house, house lord dignity, and detected Tajika yogas into a favorable/unfavorable/mixed verdict with reasoning.

- `evaluate_prashna()` -- returns `PrashnaVerdict`

---

### Jaimini Module (`jaimini/`)

#### `jaimini/karakas.py`
Chara Karaka (variable significator) calculation. In Jaimini's system, the 7 karakas (Atmakaraka through Darakaraka) are assigned to planets based on their degree within their sign -- the planet with the highest degree becomes Atmakaraka (soul significator).

- `calculate_chara_karakas()` -- returns 7 karakas sorted by degree

#### `jaimini/arudha.py`
Arudha Pada calculation. The Arudha (image/projection) of a house is found by counting the same distance from the house lord as the lord is from the house. Arudha Lagna (AL) is the most important -- it represents how the world perceives the native.

- `calculate_arudha_padas()` -- returns Arudha Pada for all 12 houses

---

### Compatibility Module (`compatibility/`)

#### `compatibility/calculator.py`
Ashtakoot (North Indian) compatibility scoring. Compares Moon positions of two charts across 8 factors totaling 36 points. Also checks Mangal Dosha (Mars affliction) for both charts.

- `calculate_compatibility()` -- returns factor-by-factor scores + total + Mangal Dosha status

#### `compatibility/porutham.py`
Porutham (South Indian) compatibility analysis. Uses 10 factors (vs. North Indian 8). Includes Rajju (longevity compatibility) and Vedha (obstruction check), which are unique to the South Indian system.

- `calculate_porutham()` -- returns `PoruthamResult` with 10 factor pass/fail

#### `compatibility/avakhada.py`
Avakhada birth summary table. Computes the traditional birth profile (Varna, Vasya, Yoni, Gana, Nadi, etc.) from the Moon's nakshatra -- used as input for compatibility scoring.

- `calculate_avakhada()` -- returns `AvakhadaInfo`

#### `compatibility/papasamyam.py`
Malefic balance (Papasamyam) compatibility check. Compares the malefic influence on the 1st, 7th, and 8th houses of both charts to ensure the affliction is balanced.

- `calculate_papasamyam()` -- returns `PapasamyamResult`

---

### Strength Module (`strength/`)

#### `strength/shadbala.py`
Shadbala (6-fold strength) computation. Quantifies planetary strength in rupas (units) across 6 dimensions: positional, directional, temporal, motional, natural, and aspectual. A planet needs at least 1 rupa to be considered strong.

- `calculate_shadbala()` -- returns `ShadbalaResult` per planet

#### `strength/ashtakavarga.py`
Ashtakavarga (8-source) benefic-point system. For each planet, each of the 8 contributors (7 planets + ascendant) either contributes a benefic point (bindu) or not in each of the 12 signs. Signs with more bindus are stronger for that planet's transit.

- `calculate_ashtakavarga()` -- returns per-planet and sarvashtakavarga tables

---

### Yoga Module (`yoga/`)

#### `yoga/calculator.py`
Yoga (planetary combination) detection. Scans a chart for classical yogas -- specific planetary configurations that indicate life patterns. Implements ~20 major yogas from BPHS, Phaladeepika, and Saravali, including:

- Pancha Mahapurusha (Ruchaka, Bhadra, Hamsa, Malavya, Shasha)
- Wealth yogas (Dhana, Lakshmi)
- Wisdom yogas (Budhaditya, Saraswati, Gajakesari)
- Affliction yogas (Kemadruma, Shakata, Daridra)
- Moon-based yogas (Sunapha, Anapha, Durudhara, Chandra-Mangal)
- Sun-based yogas (Veshi, Voshi, Ubhayachari)
- Raja and Viparita Raja yogas

Function: `detect_yogas()` -- returns list of `YogaResult`

#### `yoga/scorer.py`
Probabilistic yoga strength scoring (0-100). Evaluates how strongly a detected yoga manifests based on planetary strength, house lordship, and aspects.

- `score_yogas()` -- returns list of `ScoredYogaResult`

---

### Dosha Module (`dosha/`)

#### `dosha/calculator.py`
Dosha (affliction) detection. Identifies chart-level doshas that indicate specific life challenges. Each dosha includes severity (mild/moderate/severe) and traditional remedial measures.

- Mangal Dosha (Kuja Dosha) -- Mars in 1st, 2nd, 4th, 7th, 8th, or 12th house
- Kaal Sarpa Dosha -- all planets hemmed between Rahu and Ketu
- Pitru Dosha -- Sun afflicted by Rahu/Saturn (ancestor karma)
- Grahan Dosha -- luminaries conjunct Rahu/Ketu (eclipse yoga)

Function: `detect_doshas()` -- returns list of `DoshaResult`

#### `dosha/scorer.py`
Probabilistic dosha severity scoring (0-100). Evaluates actual impact of a detected dosha based on cancellation conditions, planetary strength, and mitigating factors.

- `score_doshas()` -- returns list of `ScoredDoshaResult`

---

### Varshaphal Module (`varshaphal/`)

#### `varshaphal/calculator.py`
Varshaphal (Solar Return / Annual Horoscopy). Casts a chart for the exact moment the Sun returns to its natal sidereal longitude each year. Includes Muntha (progressed ascendant) and applies Tajika yogas for annual predictions.

- `calculate_varshaphal()` -- returns `VarshaphalResult`

---

### KP System Module (`kp/`)

#### `kp/calculator.py`
Krishnamurti Paddhati chart calculation. KP uses Placidus house cusps (not Whole Sign) and a unique sublord system that subdivides each nakshatra unequally based on Vimsottari dasha proportions.

- `calculate_kp_chart()` -- returns `KPChartResult`

#### `kp/houses.py`
Placidus house cusp calculation for KP. Computes the 12 house cusps using the Placidus system via the Swiss Ephemeris.

#### `kp/sublords.py`
KP sublord lookup. Each degree of the zodiac maps to a sign lord, star lord (nakshatra lord), and sub lord. The sub lord is determined by dividing the nakshatra's 13.333 degrees into unequal parts proportional to Vimsottari dasha years.

- `get_kp_sublord()` -- returns `KPSublordInfo` for a given longitude

#### `kp/significators.py`
KP 4-level significators per planet and house. Determines planet-to-house signification through occupancy, lordship, star-lordship, and sub-lordship chains.

- `get_kp_significators()` -- returns `KPSignificatorDetail` per planet
- `get_kp_house_significators()` -- returns `KPHouseSignificators` per house

---

### Numerology Module (`numerology/`)

#### `numerology/calculator.py`
Vedic numerology (Chaldean system). Computes the psychic number (birth day), destiny number (full birth date), and name number (Chaldean letter-to-number mapping). Includes compatibility between numbers and basic interpretation.

- `calculate_numerology()` -- returns `NumerologyResult`

---

## Design Decisions

### Why Pydantic?
- **Immutability** -- `frozen=True` prevents accidental mutation
- **Validation** -- `Field(ge=1, le=12)` catches invalid house numbers
- **Serialization** -- `.model_dump_json()` for API responses, storage
- **Type safety** -- full IDE autocomplete and type checking

### Why Whole Sign houses?
Whole Sign is the traditional house system in Vedic astrology (Parashari method). The ascendant's sign = 1st house, next sign = 2nd house, etc. Simple, unambiguous, and the most commonly used system in Jyotish. (The KP module uses Placidus cusps separately, as required by that system.)

### Why Lahiri ayanamsa as default?
Lahiri (Chitrapaksha) is the official ayanamsa of the Indian government, adopted by the Calendar Reform Committee in 1956. It's the most widely used ayanamsa in India and the de facto standard for Vedic astrology.

### Why IntEnum for planets/signs?
Integer enums allow both human-readable code (`Planet.JUPITER`) and mathematical operations when needed. They also serialize cleanly to JSON.

### Why flat list for dashas?
A flat `list[DashaPeriod]` (instead of nested trees) is simpler to serialize, filter, and iterate. The `level` field on each period distinguishes mahadasha/antardasha/pratyantardasha. To find "all antardashas within Jupiter mahadasha", filter by date range. This applies to all four dasha systems.

### Why sunrise-based panchanga?
The Vedic "day" (ahoratra) begins at sunrise, not midnight. All panchanga elements are computed at the sunrise moment for the given location, following traditional practice.

### Why Tajika aspects are separate from Parashari aspects?
Parashari aspects (in `chart/aspects.py`) are sign-based: "Mars in Aries aspects Libra" (7th sign). Tajika aspects (in `prashna/tajika.py`) are degree-based with specific orbs: "Mars at 15 Aries applies to Jupiter at 18 Libra within 8 degree orb." They serve different analytical traditions -- Parashari for natal analysis, Tajika for Prashna and Varshaphal.

### Why both Ashtakoot and Porutham?
North Indian and South Indian traditions use different compatibility frameworks. Ashtakoot (8 factors, max 36 points) is dominant in North India. Porutham (10 factors, pass/fail) is dominant in Tamil Nadu, Kerala, and Karnataka. Both are provided because the user base spans all of India.
