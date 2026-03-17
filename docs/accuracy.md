# Accuracy & Testing

## Testing Strategy

vedic-calc uses a multi-layer testing approach to ensure calculation accuracy across all 14 modules.

### Layer 1: Cross-Validation Against Raw Swiss Ephemeris

The most important accuracy test. We compute planetary positions **two independent ways**:

1. Through `calculate_chart()` (our full code path)
2. Through raw `swe.calc_ut()` calls (bypassing our abstraction)

If both produce the same result (within 0.01 degrees), our code on top of pyswisseph is correct.

```python
# From test_accuracy.py
def test_all_planets_match_raw_swisseph(self):
    """Every planet's longitude should exactly match raw pyswisseph."""
    # Compute via raw pyswisseph
    result = swe.calc_ut(jd, swe_planet_id)
    raw_sidereal = (result[0][0] - ayanamsa) % 360.0

    # Compare against our calculate_chart()
    chart = calculate_chart(...)
    our_longitude = chart.planets[planet].longitude

    assert abs(raw_sidereal - our_longitude) < 0.01
```

This catches bugs in:

- Ayanamsa subtraction
- Ketu derivation (Rahu + 180 degrees)
- Ascendant calculation
- Any sign/nakshatra arithmetic errors

### Layer 2: Astronomical Fact Checks

Verify against known astronomical events:

| Test | What it checks |
|------|---------------|
| Full moon (Mar 11, 1990) | Sun-Moon separation is approximately 180 degrees |
| New moon (Mar 26, 1990) | Sun-Moon separation is approximately 0 degrees |
| Mesha Sankranti (Apr 14) | Sun in sidereal Aries |
| Makar Sankranti (Jan 14) | Sun in sidereal Capricorn |

These are facts any astrologer or astronomer would recognize -- if they fail, something fundamental is wrong.

### Layer 3: Arithmetic Consistency

For multiple birth dates across different years, verify:

- `sign == floor(longitude / 30) + 1`
- `nakshatra == floor(longitude / 13.333) + 1`
- `degree_in_sign == longitude % 30`

This catches off-by-one errors, rounding issues, and edge cases at sign/nakshatra boundaries.

### Layer 4: Cross-Validation Against PyJHora

Comparison tests validate our results against PyJHora (an independent Vedic astrology implementation) for:

| Comparison Area | What it checks |
|----------------|---------------|
| Divisional charts | Varga placements (D-2 through D-60) match |
| Yoga detection | Same yogas detected for the same chart |
| Dasha periods | Mahadasha/antardasha dates within tolerance |
| Aspects | Same aspects identified between planets |
| Shadbala | Six-fold strength values within tolerance |
| Ashtakavarga | Bindu counts match per planet per sign |
| Muhurta | Rahu Kalam / Yamagandam times match |
| Doshas | Same doshas detected for the same chart |

### Layer 5: Feature-Specific Unit Tests

Every module has dedicated tests covering:

- **Edge cases** -- sign/nakshatra boundaries, zero-degree placements, retrograde transitions
- **Known charts** -- verified against published examples in classical texts
- **Round-trip consistency** -- e.g., dasha periods cover exactly the expected lifespan
- **Structural validation** -- all returned models have valid field ranges

## Why Swiss Ephemeris?

The [Swiss Ephemeris](https://www.astro.com/swisseph/) is the industry standard for astronomical calculations:

- Accuracy: **< 0.001 arcseconds** (far beyond what astrology needs)
- Based on NASA JPL Development Ephemeris (DE431)
- Used by professional observatories and all major astrology software
- Maintained since 1997 by Astrodienst (Zurich)
- The same engine powers JHora, AstroSage, and most commercial Vedic astrology software

## What About Ayanamsa Accuracy?

The ayanamsa (precession correction) is computed by pyswisseph using the same algorithms as the Swiss Ephemeris C library. For Lahiri specifically:

- Defined by the Indian Calendar Reform Committee (1956)
- Based on the position of the star Spica (Chitra) at the autumnal equinox
- The official ayanamsa of the Indian government
- pyswisseph's implementation matches the standard precisely

Different ayanamsa modes (Lahiri, Raman, KP) will produce slightly different sign placements for planets near sign boundaries. This is expected and correct -- it is a matter of which ayanamsa standard you follow, not a calculation error.

## Running Tests

```bash
# Run all tests
uv run pytest -v

# Run only accuracy tests
uv run pytest tests/test_accuracy.py -v

# Run comparison tests (cross-validation against PyJHora)
uv run pytest tests/comparison/ -v

# Run with coverage
uv run pytest --cov=vedic_calc --cov-report=term-missing
```

## Current Test Count

| Test File | Tests | Focus |
|-----------|-------|-------|
| `test_accuracy.py` | 10 | Cross-validation + astronomical facts |
| `test_chart.py` | 16 | Full chart integration |
| `test_helpers.py` | 17 | Sign/nakshatra/house helpers |
| `test_constants.py` | 5 | Lookup table integrity |
| `test_renderer.py` | 13 | ASCII + SVG chart rendering |
| `test_dasha.py` | 15 | Vimsottari dasha periods |
| `test_additional_dashas.py` | 8 | Yogini, Ashtottari, Narayana dashas |
| `test_panchanga.py` | 16 | Five-element daily calendar |
| `test_divisional.py` | 8 | Varga chart placements |
| `test_aspects.py` | 7 | Planetary drishti (aspects) |
| `test_combustion.py` | 7 | Combustion detection |
| `test_states.py` | 5 | Planetary dignity + dispositors |
| `test_houses_analysis.py` | 7 | House analysis (lord, occupants, aspects) |
| `test_transits.py` | 4 | Transit chart overlays |
| `test_compatibility.py` | 10 | Ashtakoot (8-factor) compatibility |
| `test_porutham.py` | 3 | South Indian 10-factor compatibility |
| `test_yogas.py` | 6 | Classical yoga detection |
| `test_doshas.py` | 6 | Dosha detection + severity |
| `test_muhurta.py` | 5 | Daily muhurta (Rahu Kalam, Abhijit, etc.) |
| `test_muhurta_solver.py` | 20 | Muhurta constraint solver |
| `test_prashna.py` | 32 | Prashna chart + Tajika yogas + verdict |
| `test_jaimini.py` | 10 | Chara karakas + arudha padas |
| `test_strength.py` | 12 | Shadbala + Ashtakavarga |
| `test_kp.py` | 16 | KP chart + sublords |
| `test_varshaphal.py` | 21 | Solar return + Muntha + annual Tajika |
| `test_numerology.py` | 43 | Chaldean numerology |
| `test_sahams.py` | 4 | Arabic parts (lots) |
| **Comparison tests** | | |
| `comparison/test_compare_divisional.py` | 45 | Divisional charts vs PyJHora |
| `comparison/test_compare_yogas.py` | 24 | Yoga detection vs PyJHora |
| `comparison/test_compare_dasha.py` | 12 | Dasha periods vs PyJHora |
| `comparison/test_compare_aspects.py` | 9 | Aspects vs PyJHora |
| `comparison/test_compare_shadbala.py` | 12 | Shadbala vs PyJHora |
| `comparison/test_compare_ashtakavarga.py` | 12 | Ashtakavarga vs PyJHora |
| `comparison/test_compare_muhurta.py` | 12 | Muhurta times vs PyJHora |
| `comparison/test_compare_doshas.py` | 9 | Dosha detection vs PyJHora |
| **Total** | **461** | |
