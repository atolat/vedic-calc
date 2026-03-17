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

## Planetary Dignity and States

A planet's effectiveness depends heavily on **where** it sits in the zodiac. This is called its "dignity" or "state."

### The Dignity Hierarchy (strongest to weakest)

| State | Meaning | Example |
|-------|---------|---------|
| **Exalted** (Uchcha) | At maximum strength. Like a guest of honor. | Sun in Aries, Moon in Taurus |
| **Moolatrikona** | In its "office" — comfortable and productive. | Sun in Leo (1-20 degrees) |
| **Own Sign** (Swakshetra) | At home. Reliable and strong. | Mars in Aries or Scorpio |
| **Friendly Sign** | Visiting an ally. Works well but not at full power. | Jupiter in Moon's sign (Cancer) |
| **Neutral Sign** | In neutral territory. Average strength. | Saturn in Mercury's sign |
| **Enemy Sign** | At a rival's house. Uncomfortable, weakened. | Sun in Saturn's sign |
| **Debilitated** (Neecha) | At minimum strength. Like a prisoner. | Sun in Libra, Moon in Scorpio |

**Formula:** The dignity is determined by matching the planet against its position in the sign using lookup tables from BPHS Ch. 3.

### Vargottama

A special strength indicator: when a planet occupies the **same sign** in both the main chart (D1/Rashi) and the Navamsa chart (D9). This is considered very auspicious — the planet's energy is "confirmed" across divisions.

**Code:** `calculate_planet_states()` → returns `PlanetState` with dignity, is_vargottama, etc.

---

## Aspects (Drishti)

In Vedic astrology, planets "aspect" (look at/influence) other houses and planets. Unlike Western astrology, aspects are **sign-based** (not degree-based) and have **special rules**.

### Universal Aspect

Every planet aspects the **7th house** from its position (the house directly opposite). This is the "opposition" aspect.

### Special Aspects

Three planets have additional aspects beyond the 7th:

| Planet | Aspects | Why |
|--------|---------|-----|
| **Mars** | 4th, 7th, 8th from itself | Mars is aggressive — reaches forward (8th) and behind (4th) |
| **Jupiter** | 5th, 7th, 9th from itself | Jupiter is expansive — blesses trikonas (5th, 9th) |
| **Saturn** | 3rd, 7th, 10th from itself | Saturn is systematic — disciplines through effort (3rd, 10th) |

**How aspects are counted:** From the planet's sign, count forward. If Mars is in sign 1 (Aries), it aspects signs 4 (Cancer), 7 (Libra), and 8 (Scorpio).

**Code:** `calculate_aspects()` → returns `list[AspectInfo]` with aspecting planet, aspected house, type.

---

## Combustion (Astangata)

When a planet gets too close to the Sun in longitude, it becomes **combust** — its significations are "burned up" by the Sun's overwhelming energy. A combust planet is weakened.

### Combustion Thresholds

| Planet | Normal Threshold | Retrograde Threshold |
|--------|:---:|:---:|
| Moon | 12 degrees | 12 degrees |
| Mars | 17 degrees | 8 degrees |
| Mercury | 14 degrees (12 retrograde) | 12 degrees |
| Jupiter | 11 degrees | 11 degrees |
| Venus | 10 degrees (8 retrograde) | 8 degrees |
| Saturn | 15 degrees | 15 degrees |

Retrograde planets have tighter thresholds because retrograde motion brings them closer to their actual position relative to the Sun.

**Note:** Sun, Rahu, and Ketu cannot be combust. The Sun is the source, and the nodes are not physical bodies.

**Code:** `calculate_combustion()` → returns `list[CombustionStatus]` with is_combust, angular_distance.

---

## Divisional Charts (Vargas)

The birth chart (Rashi chart / D1) is the primary chart, but Vedic astrology divides the zodiac further into **16 standard divisional charts**, each revealing a specific life domain in greater detail.

### How They Work

Each division takes a planet's longitude and maps it to a new sign using a specific formula. For example, in the Navamsa (D9), each sign is divided into 9 parts of 3.333 degrees each, and each part maps to a different sign.

### The 16 Divisions (Shodashvarga)

| Division | Name | Span | Domain |
|:---:|------|:---:|--------|
| D1 | Rashi | 30 degrees | Overall life (the main chart) |
| D2 | Hora | 15 degrees | Wealth and financial fortune |
| D3 | Drekkana | 10 degrees | Siblings and courage |
| D4 | Chaturthamsa | 7.5 degrees | Property and fixed assets |
| D7 | Saptamsa | 4.286 degrees | Children and progeny |
| D9 | Navamsa | 3.333 degrees | Marriage, dharma, and soul purpose |
| D10 | Dasamsa | 3 degrees | Career and professional status |
| D12 | Dwadasamsa | 2.5 degrees | Parents |
| D16 | Shodasamsa | 1.875 degrees | Vehicles, comforts, happiness |
| D20 | Vimsamsa | 1.5 degrees | Spiritual progress and worship |
| D24 | Chaturvimsamsa | 1.25 degrees | Education and learning |
| D27 | Bhamsa | 1.111 degrees | Strength and weakness |
| D30 | Trimsamsa | 1 degree | Misfortunes and evils |
| D40 | Khavedamsa | 0.75 degrees | Auspicious/inauspicious effects |
| D45 | Akshavedamsa | 0.667 degrees | General indications |
| D60 | Shashtiamsa | 0.5 degrees | Past life karma (finest division) |

The **Navamsa (D9)** is the most important divisional chart — it's often read alongside the Rashi chart. A strong planet in D1 that is weak in D9 may underdeliver; a weak D1 planet strong in D9 may surprise.

**Code:** `calculate_divisional_chart(chart, division=9)` → returns `DivisionalChart`.

---

## House Analysis

Beyond simply knowing which planets are in which houses, house analysis provides a comprehensive view of each house's condition.

### House Categories

| Category | Houses | Meaning |
|----------|--------|---------|
| **Kendra** (Angular) | 1, 4, 7, 10 | Pillars of the chart. Stability and power. |
| **Trikona** (Trinal) | 1, 5, 9 | Fortune houses. Past merit, present luck, future dharma. |
| **Dusthana** (Difficult) | 6, 8, 12 | Challenges. Enemies, death, losses. |
| **Upachaya** (Growth) | 3, 6, 10, 11 | Improve with age. Malefics do well here. |
| **Maraka** (Death-inflicting) | 2, 7 | Can trigger health crises in certain dashas. |

### What Gets Analyzed Per House

For each of the 12 houses, the analysis determines: the sign, lord, planets occupying it, planets aspecting it, whether it's a kendra/trikona/dusthana, and the functional role of its lord.

**Code:** `analyze_houses()` → returns `list[HouseAnalysis]`.

---

## Yogas (Planetary Combinations)

A **yoga** is a specific planetary configuration that indicates a particular life theme. "Yoga" here means "combination" (not the physical practice). vedic-calc detects ~24 classical yogas.

### Key Yoga Categories

**Pancha Mahapurusha (5 Great Person Yogas):** Mars, Mercury, Jupiter, Venus, or Saturn in own/exalted sign AND in a kendra house. Each produces a specific archetype — warrior (Ruchaka/Mars), scholar (Bhadra/Mercury), sage (Hamsa/Jupiter), artist (Malavya/Venus), leader (Shasha/Saturn).

**Gajakesari:** Jupiter in kendra from Moon — one of the most recognized yogas. Produces fame, intelligence, lasting reputation. "Elephant-lion" yoga.

**Dhana/Lakshmi Yogas:** Wealth combinations involving lords of the 2nd (savings), 11th (income), and 9th (fortune) houses, plus Venus (natural wealth significator).

**Raja Yogas:** Power combinations where a kendra lord and trikona lord conjoin. The 1st house lord is special because it's both kendra AND trikona — it can form Raja Yoga with itself.

**Viparita Raja:** "Inverted" raja yoga — dusthana lord in another dusthana. Two negatives making a positive. Rise through adversity.

**Negative Yogas:** Kemadruma (Moon isolated), Shakata (Jupiter weak from Moon), Daridra (gains lord in dusthana). These have many cancellation conditions that should be checked.

**Code:** `detect_yogas()` → returns `list[YogaResult]` for all yogas checked (both present and absent).

---

## Doshas (Planetary Afflictions)

A **dosha** is an unfavorable planetary configuration that indicates a specific vulnerability or challenge. Unlike yogas (which are detected individually), doshas often have **cancellation conditions** — other chart factors that neutralize the affliction.

### The 6 Doshas Detected

| Dosha | Condition | Significance |
|-------|-----------|-------------|
| **Manglik** (Kuja Dosha) | Mars in 1st, 2nd, 4th, 7th, 8th, or 12th house | Marital tension. Mars's aggression affects partnership houses. Checked in both D1 and D9. Has 8+ cancellation conditions. |
| **Kaal Sarpa** | All 7 planets between Rahu and Ketu (hemmed in by the nodes) | Life feels fated or restricted. Sudden reversals. |
| **Pitru Dosha** | Sun afflicted by Rahu/Ketu/Saturn (especially in 9th house) | Ancestral/paternal karma. Obstacles from father's side. |
| **Grahan Dosha** | Sun or Moon conjunct Rahu or Ketu (eclipse combination) | Mental or physical health vulnerability. Sun-Rahu = ego/authority issues; Moon-Rahu = anxiety. |
| **Guru Chandal** | Jupiter conjunct Rahu or Ketu | Wisdom corrupted by illusion. Poor judgment or unconventional spiritual path. Cancelled if Jupiter is in its own/exalted sign. |
| **Shani Dosha** | Saturn in 1st, 4th, 7th, 8th, or 10th house | Delays and restrictions in the house Saturn occupies. Not inherently bad — Saturn rewards discipline. |

**Code:** `detect_doshas()` → returns `list[DoshaResult]` with is_present, cancellation status, severity.

---

## Planetary Strength (Shadbala)

**Shadbala** ("six-fold strength") is the most comprehensive strength measurement system in Vedic astrology. It quantifies a planet's power by summing six independent components, measured in Rupas (1 Rupa = 60 Virupas).

### The Six Components

| Component | What It Measures | Key Factors |
|-----------|-----------------|-------------|
| **Sthana Bala** (Positional) | Strength from zodiacal placement | Dignity (exalted/own/enemy), moolatrikona, drekkana, and more |
| **Dig Bala** (Directional) | Strength from house position | Jupiter/Mercury strong in 1st; Sun/Mars in 10th; Moon/Venus in 4th; Saturn in 7th |
| **Kaala Bala** (Temporal) | Strength from time of birth | Day/night birth, weekday lord, month lord, year lord, hora lord |
| **Chesta Bala** (Motional) | Strength from speed/direction | Retrograde planets get extra strength (they appear brighter) |
| **Naisargika Bala** (Natural) | Inherent strength hierarchy | Fixed: Sun > Moon > Venus > Jupiter > Mercury > Mars > Saturn |
| **Drik Bala** (Aspectual) | Strength from aspects received | Benefic aspects add strength; malefic aspects subtract |

Each planet ends up with a total Shadbala score. The **minimum required strengths** differ by planet (e.g., Sun and Mars need less than Jupiter and Venus because they are naturally forceful).

**Code:** `calculate_shadbala()` → returns `dict[Planet, ShadbalaResult]` with all 6 components.

---

## Ashtakavarga (Transit Strength Grid)

**Ashtakavarga** is a system for evaluating how well a planet performs in each of the 12 signs. It produces a grid of benefic points (bindus) that reveals which signs are supportive and which are hostile for each planet.

### How It Works

For each of the 7 planets (Sun through Saturn — Rahu/Ketu excluded), 8 "contributors" (the 7 planets + ascendant) each give a bindu (benefic point) or nothing to each of the 12 signs, based on fixed rules from BPHS.

- **Bhinnashtakavarga (BAV):** The individual planet's grid (7 planets x 12 signs each).
- **Sarvashtakavarga (SAV):** The sum across all 7 planets for each sign. Maximum possible = 56 per sign (8 contributors x 7 planets). A sign with SAV > 28 is generally supportive.

### Practical Use

Ashtakavarga is primarily used for **transit predictions** — when Saturn transits through a sign with a high bindu count for Saturn, that transit is smoother. Low bindus = difficult transit.

**Code:** `calculate_ashtakavarga()` → returns `AshtakavargaResult` with BAV grids and SAV totals.

---

## Compatibility (Ashtakoot Milan)

**Ashtakoot Milan** (North Indian system) compares two birth charts for marriage compatibility by evaluating 8 factors based on the Moon's nakshatra and sign in each chart.

### The 8 Factors (Kuttas)

| Factor | Points | What It Compares |
|--------|:---:|-----------------|
| **Varna** (Caste) | 1 | Social compatibility — Brahmin > Kshatriya > Vaishya > Shudra |
| **Vashya** (Dominance) | 2 | Power dynamics — who influences whom |
| **Tara** (Birth Star) | 3 | Nakshatra-based health and destiny compatibility |
| **Yoni** (Nature) | 4 | Sexual and temperamental compatibility (animal symbolism) |
| **Graha Maitri** (Friendship) | 5 | Mental and intellectual compatibility (Moon sign lords) |
| **Gana** (Temperament) | 6 | Deva (divine), Manushya (human), or Rakshasa (demon) |
| **Bhakoot** (Sign relation) | 7 | Financial and health compatibility (sign distance) |
| **Nadi** (Pulse) | 8 | Genetic/physiological compatibility (nakshatra group) |
| **Total** | **36** | 18+ is considered acceptable. 24+ is good. 30+ is excellent. |

**Code:** `calculate_compatibility()` → returns `CompatibilityResult` with all 8 scores and total.

### South Indian System: Porutham

The South Indian equivalent uses **10 factors** (poruthams) instead of 8, with different rules. Both systems use the Moon's nakshatra as the primary input.

**Code:** `calculate_porutham()` → returns `PoruthamResult` with all 10 factors.

---

## Muhurta (Electional Astrology)

**Muhurta** is the branch of Jyotish concerned with **choosing auspicious times** for important activities — weddings, business launches, travel, surgeries, etc.

### Daily Time Windows

Each day (sunrise to sunset) is divided into slots. Three specific slots are considered inauspicious:

- **Rahu Kalam:** A ~1.5 hour slot ruled by Rahu. Which slot depends on the weekday (a fixed rotation). Universally avoided for starting new activities.
- **Yamagandam:** A ~1.5 hour slot ruled by Yama (god of death). Also avoided.
- **Gulika Kalam:** A ~1.5 hour slot associated with Saturn's son. Less universally avoided but still considered inauspicious.

**Abhijit Muhurta:** A universally auspicious ~48-minute window centered on local solar noon. Overrides other inauspicious indicators.

### Muhurta Solver (Finding Auspicious Windows)

The solver finds optimal windows across a date range using a **5-layer filter**:

1. **Tithi** — is today's tithi favorable for this activity?
2. **Vara** (weekday) — is this weekday suitable?
3. **Nakshatra** — is the Moon's nakshatra supportive?
4. **Yoga** — is today's luni-solar yoga auspicious?
5. **Karana** — is the current half-tithi favorable?

Days that pass all 5 filters are scored (0-100) and ranked. Personal overlays (Chandrabala and Tarabala based on natal Moon) add further refinement.

**Code:** `calculate_muhurta()` → daily windows. `find_muhurta_windows()` → ranked search across a date range.

---

## Prashna (Horary Astrology)

**Prashna** (literally "question") is horary astrology — a chart cast for the **moment a question is asked**, not for a person's birth. It answers specific yes/no questions without requiring birth data.

### How It Works

1. A chart is cast for the current date, time, and location (the "birth" of the question)
2. The question is mapped to a **house** (career = 10th, marriage = 7th, money = 2nd, etc.)
3. **Tajika yogas** (degree-based aspect geometries) are evaluated between the ascendant lord and the query house lord

### Tajika Yogas

Unlike regular Parashari aspects (which are sign-based), Tajika yogas use **precise degree orbs** (borrowed from Tajika/Hellenistic tradition):

| Yoga | Condition | Verdict |
|------|-----------|---------|
| **Ithasala** | Faster planet applying to slower within orb | Favorable — matter progresses |
| **Easarapha** | Faster separating from slower | Unfavorable — opportunity slipping |
| **Induvara** | No applying aspect between significators | Unfavorable — matter fails |
| **Kamboola** | Moon applies to significator aspecting query lord | Favorable via intermediary |
| **Nakta** | Heavier planet receives aspect from lighter | Partial success with effort |

**Code:** `cast_prashna_chart()` → chart. `detect_tajika_yogas()` → yogas. `evaluate_prashna()` → full verdict.

---

## Jaimini System

**Jaimini astrology** is a distinct system within Vedic astrology, attributed to sage Jaimini (a student of Vyasa). It differs from the mainstream Parashari system in using **sign-based** dashas and **degree-based** planet rankings.

### Chara Karakas (Variable Significators)

In Parashari astrology, each planet has fixed significations (Sun = father, Moon = mother, etc.). Jaimini adds **chara (variable) karakas** — planets are ranked by their degree within their sign, and the ranking determines what they signify in YOUR specific chart.

| Rank | Karaka | Signifies |
|------|--------|-----------|
| Highest degree | Atmakaraka (AK) | Self, soul — the MOST important planet in Jaimini |
| 2nd highest | Amatyakaraka (AmK) | Career, profession |
| 3rd highest | Bhratrikaraka (BK) | Siblings |
| 4th highest | Matrikaraka (MK) | Mother |
| 5th highest | Pitrikaraka (PiK) | Father |
| 6th highest | Putrakaraka (PuK) | Children |
| 7th highest | Gnatikaraka (GK) | Enemies, disease |
| Lowest degree | Darakaraka (DK) | Spouse — always the planet at the lowest degree |

**Note:** Rahu's degree is counted in reverse (30 - degree) because Rahu moves backward.

### Arudha Padas

An **Arudha Pada** is the "image" or "perception" of a house — how the world SEES the house's themes, as opposed to the actual reality. The formula: count the distance from a house to its lord, then count the same distance forward from the lord.

The most important Arudha is **Arudha Lagna (AL)** — the public image. How the world perceives you, which may differ from your actual self (1st house).

**Code:** `calculate_chara_karakas()` → ranked karakas. `calculate_arudha_padas()` → all 12 arudha padas.

---

## Varshaphal (Annual Chart / Solar Return)

**Varshaphal** (literally "fruit of the year") is the Vedic solar return — a chart cast for the exact moment the Sun returns to its birth longitude each year. It provides predictions for the year ahead.

### Key Components

- **Annual Chart:** Planetary positions at the exact solar return moment
- **Muntha:** A progressed point that advances one sign per year from birth (current_year - birth_year) % 12 signs forward. Its house placement indicates the year's focus area.
- **Year Lord:** The planet ruling the year, determined by a 5-candidate evaluation (Muntha lord, Janma lagna lord, Varsha lagna lord, Tri-rashi lord, and Dina lord).
- **Mudda Dasha:** A compressed dasha system for the year, proportional to Vimsottari but fitting within 365 days.

**Code:** `calculate_varshaphal()` → returns `VarshaphalResult` with chart, muntha, year lord, and mudda dasha.

---

## KP System (Krishnamurti Paddhati)

**KP** is a modern (20th century) system developed by Prof. K.S. Krishnamurti. It uses **Placidus house cusps** (instead of Whole Sign) and a unique **sub-lord** subdivision of nakshatras.

### How KP Differs From Parashari

| Feature | Parashari | KP |
|---------|-----------|-----|
| House system | Whole Sign | Placidus (unequal cusps) |
| Key factor | Sign lord | Sub-lord |
| Subdivisions | Nakshatra + Pada | Nakshatra + Sub + Sub-sub |
| Prediction method | Dasha + transit | Significator theory |

### Sub-Lord System

Each nakshatra (13.333 degrees) is divided unequally into 9 sub-divisions using the Vimsottari dasha proportions. So within Ashwini (ruled by Ketu, 7 years), the first sub-division belongs to Ketu (proportional to 7/120), then Venus (20/120), Sun (6/120), etc.

### Significator Theory

KP determines results through 4 levels of significators:
1. **Planets in the star of occupants** of a house
2. **Occupants** of the house
3. **Planets in the star of the house lord**
4. **The house lord** itself

**Code:** `calculate_kp_chart()` → cusps + sub-lords. `get_kp_sublord()` → sub-lord for any longitude.

---

## Numerology (Chaldean System)

vedic-calc includes **Chaldean numerology** — the oldest numerological system, predating Pythagorean. It assigns numbers to letters differently and considers compound (multi-digit) numbers significant.

### Three Core Numbers

| Number | Derivation | Meaning |
|--------|-----------|---------|
| **Destiny Number** | Sum of full birth date digits | Life path and overall purpose |
| **Radical Number** | Birth day only (1-31) | Core personality and approach |
| **Name Number** | Sum of name letter values (Chaldean mapping) | Social identity and vibration |

### Chaldean Letter-Number Mapping

Unlike Pythagorean (which assigns 1-9 sequentially), Chaldean assigns based on sound vibration. Notably, **9 is not assigned to any letter** — it's considered sacred.

**Master Numbers** (11, 22, 33) are preserved and not reduced to single digits, as they carry special significance.

**Code:** `calculate_numerology()` → returns `NumerologyResult` with all numbers, lucky numbers, and compatibility.

---

## Additional Dasha Systems

Beyond Vimsottari, vedic-calc implements three alternative dasha systems:

### Ashtottari Dasha (108-year cycle)

Uses 8 planets (excludes Ketu). Total cycle = 108 years. Applicable when Rahu is in a kendra or trikona from the lagna lord. Different nakshatra-to-planet mapping than Vimsottari.

### Yogini Dasha (36-year cycle)

The shortest major dasha system. 8 yoginis mapped to 8 planets. Very popular in North India for timing events. Starting yogini determined by: (birth nakshatra number + 3) modulo 8.

### Narayana Dasha (sign-based)

A Jaimini sign-based dasha (not nakshatra-based). Each sign gets a dasha period based on the position of its lord. Unlike Vimsottari where planets rule periods, here SIGNS rule periods. The direction (forward/backward) depends on whether the starting sign is odd or even.

**Code:** `calculate_ashtottari_dasha()`, `calculate_yogini_dasha()`, `calculate_narayana_dasha()`.

---

## Transits (Gochara)

A **transit chart** shows where the planets are NOW (or at any specified time), compared to where they were at birth. Transit analysis is one of the most common practical applications.

### How Transits Work

The same calculation pipeline as a birth chart runs for the query date/time/location. The resulting planetary positions are then compared to the birth chart to understand current influences.

### Key Transit Considerations

- **Saturn transit** through a house lasts ~2.5 years. Saturn through the 12th, 1st, and 2nd from natal Moon is called **Sade Sati** (7.5-year Saturn cycle).
- **Jupiter transit** through a house lasts ~1 year. Generally beneficial.
- **Rahu/Ketu transits** last ~1.5 years per sign. Often bring sudden changes.

**Code:** `calculate_transit_chart()` → returns `TransitChart`.

---

## Special Lagnas

Beyond the main ascendant (Udaya Lagna), Vedic astrology defines several **special ascendant points** computed from time-based formulas. Each reveals a different dimension of life.

| Lagna | Meaning | What It Reveals |
|-------|---------|----------------|
| **Bhava Lagna** | Time-proportional lagna | Fine-tuned house beginnings |
| **Hora Lagna** | Wealth lagna | Financial potential and prosperity |
| **Ghati Lagna** | Fame lagna | Public recognition and reputation |
| **Vighati Lagna** | Sub-minute lagna | Very fine-grained analysis |

These use **ghati** (a Vedic time unit: 1 ghati = 24 minutes, 60 ghatis = 1 day). The formulas involve multiplying elapsed ghatis since sunrise by planetary constants.

**Code:** `calculate_special_lagnas()` → returns `list[SpecialLagna]`.

---

## Upagrahas (Shadow Planets)

**Upagrahas** are computed points (not physical bodies) derived from the Sun's position. They provide additional nuance, particularly about karmic and hidden influences.

The five Sun-based upagrahas form a chain, each 4.286 degrees (one nakshatra pada equivalent) apart:

| Upagraha | Derivation | Influence |
|----------|-----------|-----------|
| **Dhuma** | Sun longitude + 133.333 degrees | Smoky, inauspicious |
| **Vyatipata** | 360 - Dhuma | Calamity, accidents |
| **Parivesha** | Vyatipata + 180 degrees | Halo, obstruction |
| **Chapa** | 360 - Parivesha | Bow, restlessness |
| **Upaketu** | Chapa + 16.667 degrees | Smoke flag, endings |

**Code:** `calculate_upagrahas()` → returns `list[UpagrahaPosition]`.

---

## Sahams (Arabic Parts / Sensitive Points)

**Sahams** are computed points using the formula: **A + B - C**, where A, B, and C are specific planetary or house longitudes. They originated in Hellenistic astrology and were adopted into Tajika (annual) Vedic astrology.

Each saham represents a focused life theme:

| Saham | Formula | Theme |
|-------|---------|-------|
| Punya (Fortune) | Ascendant + Moon - Sun | Overall luck |
| Vidya (Knowledge) | Ascendant + Sun - Moon | Education |
| Yashas (Fame) | Ascendant + Jupiter - Sun | Reputation |
| Mitra (Friends) | Ascendant + Jupiter - Moon | Friendships |
| Mahatmya (Greatness) | Ascendant + Sun - Saturn | Authority |
| And others... | Various | Various themes |

**Code:** `calculate_sahams()` → returns `list[SahamPosition]`.

---

## Festivals (Panchanga-Based)

vedic-calc can detect major Hindu festivals by scanning panchanga data for the specific tithi/nakshatra/solar conditions that define each festival.

### Festivals Detected

Makar Sankranti (solar), Maha Shivaratri, Holi, Ram Navami, Hanuman Jayanti, Guru Purnima, Raksha Bandhan, Krishna Janmashtami, Ganesh Chaturthi, Navaratri, Diwali, and Kartik Purnima.

Most festivals are **tithi-based** (e.g., Krishna Janmashtami = Krishna Paksha Ashtami in the month of Shravan). Makar Sankranti is the exception — it's **solar-based** (Sun entering sidereal Capricorn, around January 14).

**Code:** `get_festivals(year, latitude, longitude, timezone_offset)` → returns `list[FestivalInfo]`.

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
| Ayanamsa | Tropical→Sidereal correction | ~24° (2026) |
| Ascendant | Rising degree | Changes every ~2 hours |
| House | Area of life | = Sign in Whole Sign system |
| Mahadasha | Major planetary period | 7–20 years each |
| Tithi | Lunar day | Moon-Sun distance ÷ 12° |
| Yoga (Panchanga) | Luni-solar combination | Moon+Sun distance ÷ 13.333° |
| Yoga (Chart) | Planetary combination | Specific configuration rules |
| Dosha | Planetary affliction | Configuration + cancellation rules |
| Shadbala | Six-fold strength | 6 components summed in Rupas |
| Ashtakavarga | Transit strength grid | 8 contributors × 12 signs per planet |
| Divisional Chart | Zodiac subdivision | D1=30° through D60=0.5° |
| Drishti (Aspect) | Planetary influence | 7th universal + special aspects |
| Combustion | Too close to Sun | Planet-specific degree thresholds |
| Muhurta | Auspicious timing | 5-layer panchanga filter |
| Prashna | Horary chart | Tajika degree-based yogas |
| Tajika | Degree-based aspects | Orbs: 4°–8° depending on aspect |
| Chara Karaka | Variable significator | Ranked by degree in sign |
| Arudha Pada | House "image" | Count lord distance, mirror it |
| Varshaphal | Solar return chart | Sun returns to birth longitude |
| Sub-lord (KP) | Nakshatra sub-division | Vimsottari proportions within 13.333° |

---

## Further Reading

- **Brihat Parashara Hora Shastra (BPHS)**: The foundational text of Vedic astrology (~1500 BCE, attributed to sage Parashara). Covers planetary positions, houses, aspects, yogas, doshas, dashas, muhurta, and more. Think of it as the "specification document" for Vedic astrology.
- **Phaladeepika** by Mantreshwara: A concise, practical text covering yogas, planetary effects, and compatibility. More accessible than BPHS.
- **Saravali** by Kalyana Varma: Detailed coverage of planetary combinations and effects by house placement.
- **Muhurta Chintamani**: The classical text on electional astrology (choosing auspicious times).
- **Jaimini Sutras**: Sage Jaimini's aphoristic text on chara karakas, arudha padas, and sign-based dashas.
- **Surya Siddhanta**: Classical Indian astronomical text (~400 CE) with the mathematical models for planetary motion.
- **Swiss Ephemeris documentation**: Technical details of the planetary calculation engine used under the hood.
- **KP Reader** by K.S. Krishnamurti: Introduction to the Krishnamurti Paddhati (KP) system.
