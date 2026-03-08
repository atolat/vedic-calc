# Accuracy & Testing

## Testing Strategy

vedic-calc uses a three-layer testing approach to ensure calculation accuracy.

### Layer 1: Cross-Validation Against Raw Swiss Ephemeris

The most important accuracy test. We compute planetary positions **two independent ways**:

1. Through `calculate_chart()` (our full code path)
2. Through raw `swe.calc_ut()` calls (bypassing our abstraction)

If both produce the same result (within 0.01°), our code on top of pyswisseph is correct.

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
- Ketu derivation (Rahu + 180°)
- Ascendant calculation
- Any sign/nakshatra arithmetic errors

### Layer 2: Astronomical Fact Checks

Verify against known astronomical events:

| Test | What it checks |
|------|---------------|
| Full moon (Mar 11, 1990) | Sun-Moon separation ≈ 180° |
| New moon (Mar 26, 1990) | Sun-Moon separation ≈ 0° |
| Mesha Sankranti (Apr 14) | Sun in sidereal Aries |
| Makar Sankranti (Jan 14) | Sun in sidereal Capricorn |

These are facts any astrologer or astronomer would recognize — if they fail, something fundamental is wrong.

### Layer 3: Arithmetic Consistency

For multiple birth dates across different years, verify:

- `sign == floor(longitude / 30) + 1`
- `nakshatra == floor(longitude / 13.333) + 1`
- `degree_in_sign == longitude % 30`

This catches off-by-one errors, rounding issues, and edge cases at sign/nakshatra boundaries.

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

Different ayanamsa modes (Lahiri, Raman, KP) will produce slightly different sign placements for planets near sign boundaries. This is expected and correct — it's a matter of which ayanamsa standard you follow, not a calculation error.

## Running Tests

```bash
# Run all tests
uv run pytest -v

# Run only accuracy tests
uv run pytest tests/test_accuracy.py -v

# Run with coverage
uv run pytest --cov=vedic_calc --cov-report=term-missing
```

## Current Test Count

| Test File | Tests | Focus |
|-----------|-------|-------|
| `test_constants.py` | 5 | Lookup table integrity |
| `test_helpers.py` | 13 | Sign/nakshatra/house helpers |
| `test_chart.py` | 11 | Full chart integration |
| `test_accuracy.py` | 10 | Cross-validation + astronomical facts |
| **Total** | **48** | |
