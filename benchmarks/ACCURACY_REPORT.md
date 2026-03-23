# vedic-calc Comprehensive Accuracy Benchmark

**Generated**: 2026-03-23 05:57 UTC
**Charts tested**: 10
**Compatibility pairs**: 5
**Reference APIs**: AstrologyAPI.com (Professional), Prokerala
**Ayanamsa**: Lahiri (all engines)

## Overall Summary

**Total tests: 1010 | Passed: 989 | Failed: 21 | Rate: 97.9%**

| Category | Tests | Passed | Failed | Rate |
|----------|-------|--------|--------|------|
| Anandadi Yoga | 10 | 10 | 0 | 100.0% |
| Ashtakavarga | 70 | 70 | 0 | 100.0% |
| Avakhada | 60 | 52 | 8 | 86.7% **!!** |
| Compatibility | 45 | 45 | 0 | 100.0% |
| Dasha | 110 | 110 | 0 | 100.0% |
| Disha Shool | 10 | 10 | 0 | 100.0% |
| Divisional | 80 | 80 | 0 | 100.0% |
| Dosha | 30 | 21 | 9 | 70.0% **!!** |
| Numerology | 30 | 30 | 0 | 100.0% |
| Panchanga | 50 | 50 | 0 | 100.0% |
| Planets | 490 | 490 | 0 | 100.0% |
| Sade Sati | 20 | 17 | 3 | 85.0% **!!** |
| Yogini Dasha | 5 | 4 | 1 | 80.0% **!!** |

## Anandadi Yoga

**10/10 passed**

## Ashtakavarga

**70/70 passed**

## Avakhada

**52/60 passed**

### Failures

| Chart | Sub | Field | vedic-calc | Reference | Source | Notes |
|-------|-----|-------|-----------|-----------|--------|-------|
| Delhi 1992 | Varna | Varna | `Vaishya` | `Kshatriya` | AstrologyAPI |  |
| NYC 1985 | Varna | Varna | `Kshatriya` | `Vaishya` | AstrologyAPI |  |
| Chennai 2000 | Varna | Varna | `Kshatriya` | `Vaishya` | AstrologyAPI |  |
| London 1975 | Varna | Varna | `Kshatriya` | `Vaishya` | AstrologyAPI |  |
| Varanasi 1988 | Varna | Varna | `Vaishya` | `Kshatriya` | AstrologyAPI |  |
| Jaipur 2005 | Varna | Varna | `Vaishya` | `Kshatriya` | AstrologyAPI |  |
| Jaipur 2005 | Gana | Gana | `Deva` | `Manushya` | AstrologyAPI |  |
| Sydney 1998 | Varna | Varna | `Vaishya` | `Kshatriya` | AstrologyAPI |  |

### Breakdown

| Subcategory | Tests | Passed | Rate |
|-------------|-------|--------|------|
| Gana | 10 | 9 | 90% |
| Nadi | 10 | 10 | 100% |
| Tatva | 10 | 10 | 100% |
| Varna | 10 | 3 | 30% |
| Vashya | 10 | 10 | 100% |
| Yoni | 10 | 10 | 100% |

## Compatibility

**45/45 passed**

### Breakdown

| Subcategory | Tests | Passed | Rate |
|-------------|-------|--------|------|
| Kutta Score | 40 | 40 | 100% |
| Total Score | 5 | 5 | 100% |

## Dasha

**110/110 passed**

### Breakdown

| Subcategory | Tests | Passed | Rate |
|-------------|-------|--------|------|
| Current Major | 10 | 10 | 100% |
| Lord Sequence | 10 | 10 | 100% |
| Start Date | 90 | 90 | 100% |

## Disha Shool

**10/10 passed**

## Divisional

**80/80 passed**

## Dosha

**21/30 passed**

### Failures

| Chart | Sub | Field | vedic-calc | Reference | Source | Notes |
|-------|-----|-------|-----------|-----------|--------|-------|
| Delhi 1992 | Kalsarpa | Present | `False` | `True` | AstrologyAPI |  |
| Delhi 1992 | Sadhesati | Currently Active | `True` | `False` | AstrologyAPI | API moon_sign=Sagittarius, saturn_sign=Pisces |
| Varanasi 1988 | Kalsarpa | Present | `False` | `True` | AstrologyAPI |  |
| Jaipur 2005 | Manglik | Present | `False` | `True` | AstrologyAPI | vc_severity=none, api_status=LESS_EFFECTIVE |
| Jaipur 2005 | Kalsarpa | Present | `False` | `True` | AstrologyAPI |  |
| Jaipur 2005 | Sadhesati | Currently Active | `False` | `True` | AstrologyAPI | API moon_sign=Aries, saturn_sign=Pisces |
| Sydney 1998 | Kalsarpa | Present | `False` | `True` | AstrologyAPI |  |
| Tokyo 2010 | Manglik | Present | `False` | `True` | AstrologyAPI | vc_severity=none, api_status=EFFECTIVE |
| Tokyo 2010 | Sadhesati | Currently Active | `False` | `True` | AstrologyAPI | API moon_sign=Aquarius, saturn_sign=Pisces |

### Breakdown

| Subcategory | Tests | Passed | Rate |
|-------------|-------|--------|------|
| Kalsarpa | 10 | 6 | 60% |
| Manglik | 10 | 8 | 80% |
| Sadhesati | 10 | 7 | 70% |

## Numerology

**30/30 passed**

### Breakdown

| Subcategory | Tests | Passed | Rate |
|-------------|-------|--------|------|
| Destiny | 10 | 10 | 100% |
| Name | 10 | 10 | 100% |
| Radical | 10 | 10 | 100% |

## Panchanga

**50/50 passed**

### Breakdown

| Subcategory | Tests | Passed | Rate |
|-------------|-------|--------|------|
| Karana | 10 | 10 | 100% |
| Nakshatra | 10 | 10 | 100% |
| Tithi | 10 | 10 | 100% |
| Vara | 10 | 10 | 100% |
| Yoga | 10 | 10 | 100% |

## Planets

**490/490 passed**

### Breakdown

| Subcategory | Tests | Passed | Rate |
|-------------|-------|--------|------|
| Longitude | 200 | 200 | 100% |
| Retrograde | 90 | 90 | 100% |
| Sign | 200 | 200 | 100% |

### Longitude Statistics

- **vs AstrologyAPI**: avg=0.0030°, max=0.0051°, threshold=0.05°
- **vs Prokerala**: avg=0.0000°, max=0.0002°, threshold=0.05°

## Sade Sati

**17/20 passed**

### Failures

| Chart | Sub | Field | vedic-calc | Reference | Source | Notes |
|-------|-----|-------|-----------|-----------|--------|-------|
| Delhi 1992 | Currently Active | Status | `False` | `True` | Prokerala |  |
| Varanasi 1988 | Currently Active | Status | `False` | `True` | Prokerala |  |
| Sydney 1998 | Currently Active | Status | `False` | `True` | Prokerala |  |

## Yogini Dasha

**4/5 passed**

### Failures

| Chart | Sub | Field | vedic-calc | Reference | Source | Notes |
|-------|-----|-------|-----------|-----------|--------|-------|
| Jaipur 2005 | Current Major | Now | `Saturn` | `Rahu (Sankata)` | AstrologyAPI |  |

## Methodology

All engines use the Swiss Ephemeris and Lahiri (Chitrapaksha) ayanamsa.
Planetary longitude threshold: 0.05° (positions closer than this are considered identical).
Dasha date threshold: 3 days (accounts for time-of-day parsing differences).
Panchanga and nakshatra names use fuzzy matching to handle transliteration variants.

### Categories Tested

1. **Planets**: longitude, sign, retrograde for all 9 grahas + ascendant vs both APIs
2. **Divisional**: D9 (Navamsa) planet-sign placements vs AstrologyAPI
3. **Dasha**: Vimshottari mahadasha lord sequence, start dates, current period
4. **Yogini Dasha**: current major period lord
5. **Ashtakavarga**: bhinnashtak totals per planet per sign (7 planets × 12 signs)
6. **Panchanga**: tithi, nakshatra, vara, yoga, karana, sunrise time
7. **Dosha**: Manglik, Kalsarpa, Sadhesati presence/absence
8. **Compatibility**: Ashtakoot 8-kutta scores and total for 5 pairs
9. **Varshaphal**: Muntha sign, Year Lord, annual planet signs
10. **KP**: planet signs, star lords, sub-lords, cusp signs
11. **Numerology**: destiny, radical, name, lucky numbers
12. **Sade Sati**: current active status vs AstrologyAPI + Prokerala
13. **Planet Relationships**: Panchadha Maitri compound relationships vs Prokerala
14. **Avakhada**: varna, vashya, yoni, gana, nadi vs AstrologyAPI
15. **Disha Shool**: inauspicious direction vs Prokerala
16. **Anandadi Yoga**: yoga name vs Prokerala
17. **Chandrashtama**: window count vs Prokerala

---
*Generated by vedic-calc benchmark suite*