# Vedic Astrology Concepts for Developers

This guide explains the core Vedic astrology concepts you need to understand the `vedic-calc` codebase. No prior astrology knowledge required.

---

## The Big Picture

Vedic astrology (Jyotish) is an ancient Indian system that maps celestial positions to human life events. At its core, it's **coordinate geometry on a circle** — the 360° ecliptic (the apparent path of the Sun around the Earth).

Everything in this library boils down to one operation: **take a longitude value (0°–360°) and look things up from it**.

```
longitude = 45.0°

→ Sign:      floor(45 / 30) + 1 = 2 → Taurus
→ Degree:    45 % 30 = 15° → "15° Taurus"
→ Nakshatra: floor(45 / 13.333) + 1 = 4 → Rohini
→ Pada:      floor((45 % 13.333) / 3.333) + 1 = 2 → Pada 2
```

That's it. The hard part is getting accurate longitude values — that's what the Swiss Ephemeris does.

---

## Tropical vs. Sidereal: The Ayanamsa

This is the **#1 thing** that distinguishes Vedic from Western astrology.

### The problem

The Earth's axis wobbles like a top (called **precession**), completing one wobble every ~26,000 years. This means the point where the Sun crosses the equator at the spring equinox (called the "First Point of Aries") slowly drifts backward against the fixed stars.

### Two zodiacs

- **Tropical zodiac** (Western): 0° Aries = spring equinox point. Aligned with seasons. Drifts ~50 arcseconds/year relative to stars.
- **Sidereal zodiac** (Vedic): 0° Aries = aligned with actual star positions. Fixed relative to stars.

### The gap: Ayanamsa

The angular difference between these two systems is called the **ayanamsa**. It's currently about **24°** and grows ~50 arcseconds per year.

```
sidereal_longitude = tropical_longitude - ayanamsa
```

So if Western astrology says your Sun is at 10° Aries (tropical), Vedic astrology would say it's at about 10° - 24° = **346°** → 16° Pisces (sidereal). **This is why your "Vedic sign" is often one sign back from your "Western sign."**

### Which ayanamsa?

There are several competing values (they differ by ~1°):

| Ayanamsa | Used By | Our Default? |
|----------|---------|:---:|
| **Lahiri** | Indian government, most Vedic astrologers | **Yes** |
| Raman | B.V. Raman's school | No |
| Krishnamurti | KP astrology system | No |
| True Chitrapaksha | Some modern astrologers | No |

In code: `Ayanamsa.LAHIRI` (see `constants.py`).

---

## The 9 Planets (Navagraha)

Vedic astrology uses 9 "planets" (grahas). Two of them aren't physical bodies:

| Planet | Sanskrit | What It Actually Is | In Code |
|--------|----------|-------------------|---------|
| Sun | Surya | Star | `Planet.SUN` |
| Moon | Chandra | Earth's satellite | `Planet.MOON` |
| Mars | Mangal | Planet | `Planet.MARS` |
| Mercury | Budh | Planet | `Planet.MERCURY` |
| Jupiter | Guru | Planet | `Planet.JUPITER` |
| Venus | Shukra | Planet | `Planet.VENUS` |
| Saturn | Shani | Planet | `Planet.SATURN` |
| Rahu | — | Moon's north node* | `Planet.RAHU` |
| Ketu | — | Moon's south node* | `Planet.KETU` |

!!! info "What are Rahu and Ketu?"
    The Moon's orbit is tilted ~5° from the ecliptic. The two points where it crosses the ecliptic are called **lunar nodes**. The ascending node = Rahu, the descending node = Ketu. They're always exactly 180° apart. They cause eclipses (hence their mythological association with a demon swallowing the Sun/Moon).

    In the code, Ketu has no Swiss Ephemeris constant — we calculate it as `Rahu + 180°`.

### Retrograde Motion

Planets sometimes appear to move **backward** in the sky. This isn't real — it's an illusion caused by Earth's orbital motion (like a car you're overtaking appearing to go backward). In Vedic astrology, retrograde planets are considered significant.

In code: `is_retrograde = speed < 0` (from Swiss Ephemeris daily speed).

Special case: **Rahu and Ketu are always retrograde** — the lunar nodes naturally move backward through the zodiac.

---

## The 12 Signs (Rashis)

The 360° zodiac is divided into 12 equal signs of 30° each:

| # | Sign | Sanskrit | Range | Lord (Ruler) |
|---|------|----------|-------|------|
| 1 | Aries | Mesha | 0°–30° | Mars |
| 2 | Taurus | Vrishabha | 30°–60° | Venus |
| 3 | Gemini | Mithuna | 60°–90° | Mercury |
| 4 | Cancer | Karka | 90°–120° | Moon |
| 5 | Leo | Simha | 120°–150° | Sun |
| 6 | Virgo | Kanya | 150°–180° | Mercury |
| 7 | Libra | Tula | 180°–210° | Venus |
| 8 | Scorpio | Vrischika | 210°–240° | Mars |
| 9 | Sagittarius | Dhanu | 240°–270° | Jupiter |
| 10 | Capricorn | Makara | 270°–300° | Saturn |
| 11 | Aquarius | Kumbha | 300°–330° | Saturn |
| 12 | Pisces | Meena | 330°–360° | Jupiter |

**Formula:** `sign = floor(longitude / 30) + 1`

Each sign has a **lord** (ruling planet). Notice that Sun and Moon rule one sign each, while the other 5 planets rule two signs each. Rahu and Ketu don't rule any signs.

---

## The 27 Nakshatras (Lunar Mansions)

This is the **oldest layer** of Vedic astrology, predating the 12-sign system. The zodiac is divided into 27 nakshatras, each spanning **13°20' (13.333°)**.

**Formula:** `nakshatra = floor(longitude / 13.333) + 1`

Each nakshatra is further divided into **4 padas (quarters)** of **3°20' (3.333°)** each, giving **108 padas** total.

### Nakshatra Lords (the 9-planet cycle)

Each nakshatra is ruled by one of the 9 planets, cycling in this fixed order:

```
Ketu → Venus → Sun → Moon → Mars → Rahu → Jupiter → Saturn → Mercury
```

This 9-planet cycle repeats 3 times across the 27 nakshatras (9 × 3 = 27).

| # | Nakshatra | Lord | # | Nakshatra | Lord | # | Nakshatra | Lord |
|---|-----------|------|---|-----------|------|---|-----------|------|
| 1 | Ashvini | Ketu | 10 | Magha | Ketu | 19 | Moola | Ketu |
| 2 | Bharani | Venus | 11 | P.Phalguni | Venus | 20 | P.Ashadha | Venus |
| 3 | Krittika | Sun | 12 | U.Phalguni | Sun | 21 | U.Ashadha | Sun |
| 4 | Rohini | Moon | 13 | Hasta | Moon | 22 | Shravana | Moon |
| 5 | Mrigashira | Mars | 14 | Chitra | Mars | 23 | Dhanishta | Mars |
| 6 | Ardra | Rahu | 15 | Swati | Rahu | 24 | Shatabhisha | Rahu |
| 7 | Punarvasu | Jupiter | 16 | Vishakha | Jupiter | 25 | P.Bhadrapada | Jupiter |
| 8 | Pushya | Saturn | 17 | Anuradha | Saturn | 26 | U.Bhadrapada | Saturn |
| 9 | Ashlesha | Mercury | 18 | Jyeshtha | Mercury | 27 | Revati | Mercury |

### Why Nakshatras Matter

The Moon's nakshatra at birth (**Janma Nakshatra**) determines:

1. Which **dasha period** you start life in
2. Your **birth star** — used for name selection and compatibility matching
3. The starting point for many predictive calculations

---

## The Ascendant (Lagna)

The **ascendant** is the zodiac degree rising on the eastern horizon at the exact moment and place of birth. It's the **most important point** in a Vedic chart.

### Why it's special

- Unlike planets (which are the same everywhere on Earth at a given time), the ascendant **depends on your location** because it's about YOUR local horizon.
- It changes roughly every **2 hours** (Earth rotates 360° in 24 hours, so ~30° per 2 hours = one sign).
- The ascendant's sign becomes the **1st house**, and all houses follow from there.

### Why birth time accuracy matters

Because the ascendant changes a sign every ~2 hours, even a small error in birth time can shift the entire house structure. This is why astrologers insist on accurate birth times.

---

## The 12 Houses (Bhavas)

Houses represent **areas of life**. In the Whole Sign system (used by vedic-calc):

```
Ascendant's sign = 1st house → Self
Next sign        = 2nd house → Wealth
Next sign        = 3rd house → Siblings
...and so on for all 12
```

| House | Area of Life | Key Themes |
|:-----:|-------------|------------|
| 1 | Self | Personality, body, overall life direction |
| 2 | Wealth | Money, speech, family, food |
| 3 | Courage | Siblings, communication, short trips |
| 4 | Home | Mother, property, emotional peace, vehicles |
| 5 | Children | Creativity, intelligence, romance, past merit |
| 6 | Enemies | Disease, debts, obstacles, service |
| 7 | Marriage | Spouse, partnerships, business deals |
| 8 | Transformation | Death/longevity, sudden events, inheritance |
| 9 | Fortune | Father, dharma, higher education, long journeys |
| 10 | Career | Profession, reputation, public life |
| 11 | Gains | Income, friends, wishes fulfilled |
| 12 | Losses | Expenses, foreign lands, spirituality, sleep |

**House Lord:** The planet that rules the sign occupying a house. If Gemini (ruled by Mercury) is your 7th house, then Mercury is your "7th lord" — and Mercury's condition in the chart tells you about your marriage/partnerships.

---

## The Dasha System (Planetary Periods)

The **Vimsottari Dasha** is a timing system that divides 120 years into periods ruled by different planets:

```
Ketu:    7 years
Venus:  20 years
Sun:     6 years
Moon:   10 years
Mars:    7 years
Rahu:   18 years
Jupiter:16 years
Saturn: 19 years
Mercury:17 years
─────────────────
Total: 120 years
```

### How it starts

Your **birth nakshatra's lord** determines which dasha you're born into. How far the Moon has traveled through that nakshatra determines how much of that dasha remains.

**Example:** Moon at birth is at 45° → Rohini nakshatra → lord is Moon → you start in Moon dasha. Moon has traversed 5° of Rohini's 13.333° span = 37.5% used. Moon dasha is 10 years, so 6.25 years remain at birth.

### Sub-periods

Each mahadasha is divided into **antardashas** (sub-periods) using the same planet sequence and proportional durations:

```
Moon mahadasha (10 years) contains:
  Moon-Moon:   10 × (10/120) = 0.833 years
  Moon-Mars:   10 × (7/120)  = 0.583 years
  Moon-Rahu:   10 × (18/120) = 1.500 years
  ...etc for all 9 planets
```

---

## Panchanga (Daily Calendar)

"Pancha" = five, "Anga" = limb. The Panchanga tracks 5 daily elements:

### 1. Tithi (Lunar Day)

The angular distance between Moon and Sun, divided into 30 parts:

```
tithi = floor((moon_longitude - sun_longitude) / 12°) + 1
```

- Tithis 1–15: **Shukla Paksha** (waxing/bright half, new moon → full moon)
- Tithis 16–30: **Krishna Paksha** (waning/dark half, full moon → new moon)

### 2. Nakshatra

Which nakshatra the Moon is in today (same formula as birth nakshatra).

### 3. Yoga

Based on the **sum** of Moon and Sun longitudes:

```
yoga = floor((moon_longitude + sun_longitude) / 13.333°) + 1
```

There are 27 yogas (Vishkambha through Vaidhriti). Despite spanning 13.333° like nakshatras, they are a completely different concept.

### 4. Karana

Half a tithi. Each tithi has 2 karanas = 60 karanas per month.

### 5. Vara

Weekday. Named after planets: Sunday = Sun, Monday = Moon, etc.

---

## The Code Architecture

Here's how these concepts map to the codebase:

```
constants.py  →  All the lookup tables (signs, nakshatras, lords, dasha years)
ephemeris.py  →  Swiss Ephemeris wrapper (the ONLY file that talks to the C library)
types.py      →  Pydantic models (BirthChart, PlanetPosition, etc.)
calculator.py →  The glue: gets longitudes, does arithmetic, builds the chart
```

### The calculation pipeline

```
Birth details (date, time, place)
    │
    ▼
calculator.py: calculate_chart()
    │
    ├── ephemeris.py: _to_julian_day()          →  JD number
    ├── ephemeris.py: get_ayanamsa()            →  ~24° correction
    ├── ephemeris.py: get_ascendant()           →  rising degree
    ├── ephemeris.py: get_planet_longitude() ×9  →  9 planet positions
    │
    ├── calculator.py: longitude_to_sign()       →  floor(lon/30)+1
    ├── calculator.py: longitude_to_nakshatra()  →  floor(lon/13.333)+1
    ├── calculator.py: build_houses()            →  12 houses from ascendant
    │
    └── types.py: BirthChart(...)               →  frozen, JSON-serializable result
```

### Key insight

The Swiss Ephemeris (via `ephemeris.py`) does the **hard astronomy** — calculating where planets actually are using NASA JPL data. Everything else is **simple arithmetic** on the resulting longitude values. This separation is intentional: if you ever wanted to swap the calculation engine, you'd only need to change `ephemeris.py`.

---

## Quick Reference Card

| Term | What It Is | Formula/Size |
|------|-----------|--------------|
| Ecliptic | Sun's apparent path | 360° circle |
| Sign (Rashi) | 1/12 of zodiac | 30° each |
| Nakshatra | 1/27 of zodiac | 13.333° each |
| Pada | 1/4 of nakshatra | 3.333° each |
| Ayanamsa | Tropical→Sidereal correction | ~24° (2024) |
| Ascendant | Rising degree | Changes every ~2 hours |
| House | Area of life | = Sign in Whole Sign system |
| Mahadasha | Major planetary period | 7–20 years each |
| Tithi | Lunar day | Moon-Sun distance ÷ 12° |
| Yoga | Luni-solar combination | Moon+Sun distance ÷ 13.333° |

---

## Further Reading

- **Brihat Parashara Hora Shastra (BPHS)**: The foundational text of Vedic astrology. Chapters 3-7 cover the concepts implemented in vedic-calc.
- **Surya Siddhanta**: Classical Indian astronomical text with the mathematical foundations.
- **Swiss Ephemeris documentation**: Technical details of the planetary calculation engine we use under the hood.
