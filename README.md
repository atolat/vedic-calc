# vedic-calc

Open-source Vedic astrology calculation library built on the Swiss Ephemeris.

Pure functions, Pydantic models, no GUI dependencies. AGPL-3.0 licensed.

## Features

- **Birth chart** -- planetary positions, houses (Whole Sign), nakshatras, padas
- **Divisional charts** -- D-1 through D-60 (Rasi, Navamsa, Dashamsa, all standard vargas)
- **Aspects** -- Vedic drishti with special aspects for Mars, Jupiter, Saturn
- **Planetary states** -- dignity, combustion, retrograde, dispositor chains
- **House analysis** -- lord, occupants, aspects, strength assessment per house
- **Transits** -- current positions overlaid on natal chart
- **Special lagnas** -- Hora, Ghati, Bhava, Sree Lagna
- **Upagrahas** -- Dhuma, Vyatipata, Parivesha, Chapa, Upaketu
- **Sahams** -- 21 Arabic parts (Punya, Vidya, Yasas, etc.)
- **Dasha** -- Vimsottari, Yogini, Ashtottari, Narayana (4 dasha systems)
- **Panchanga** -- daily Vedic calendar (tithi, nakshatra, yoga, karana, vara) + festivals
- **Yogas** -- ~20 classical yogas (Pancha Mahapurusha, Gajakesari, Dhana, Raja, and more)
- **Doshas** -- Mangal, Kaal Sarpa, Pitru, Grahan with severity and remedies
- **Shadbala** -- six-fold planetary strength in rupas
- **Ashtakavarga** -- 8-source benefic point tables
- **Compatibility** -- Ashtakoot Milan (North, 36 points) + Porutham (South, 10 factors)
- **Muhurta** -- Rahu Kalam, Abhijit, Choghadiya + constraint solver for auspicious windows
- **Prashna** -- horary chart casting, Tajika yogas, verdict engine
- **Jaimini** -- Chara Karakas + Arudha Padas
- **Varshaphal** -- solar return chart, Muntha, annual Tajika yogas
- **KP System** -- Placidus cusps, sublord lookup (249 divisions)
- **Numerology** -- Chaldean system (psychic, destiny, name numbers)
- **Rendering** -- South Indian, North Indian (ASCII), and SVG chart diagrams

## Quick Start

```bash
pip install git+https://github.com/atolat/vedic-calc.git
```

## Usage

```python
from vedic_calc import calculate_chart, calculate_dasha, calculate_panchanga
from vedic_calc.core.constants import Planet

# Birth chart
chart = calculate_chart(
    year=1990, month=3, day=15,
    hour=10, minute=30,
    latitude=19.0760, longitude=72.8777,  # Mumbai
    timezone_offset=5.5,                   # IST
)

for planet, pos in chart.planets.items():
    print(f"{planet.name}: {pos.sign.name} {pos.degree_in_sign:.1f}")

# Dasha timeline
from vedic_calc import get_current_dasha
from datetime import datetime
current = get_current_dasha(chart, datetime.now())
for period in current:
    print(f"{period.level}: {period.lord.name}")

# Panchanga
panchanga = calculate_panchanga(2026, 3, 11, 19.076, 72.878, 5.5)
print(f"Tithi: {panchanga.tithi_name}, Nakshatra: {panchanga.nakshatra.name}")

# Compatibility
from vedic_calc import calculate_compatibility
from vedic_calc.core.constants import Nakshatra, Sign
result = calculate_compatibility(
    person1_nakshatra=Nakshatra.ROHINI, person1_sign=Sign.TAURUS,
    person2_nakshatra=Nakshatra.HASTA, person2_sign=Sign.VIRGO,
)
print(f"Score: {result.total_score}/36 -- {result.verdict}")

# Muhurta solver
from vedic_calc import find_muhurta_windows
windows = find_muhurta_windows(
    activity="marriage",
    start_date=datetime(2026, 4, 1),
    end_date=datetime(2026, 4, 30),
    latitude=19.076, longitude=72.878,
    timezone_offset=5.5,
)
for w in windows.windows:
    print(f"{w.start.date()} -- score: {w.score}, {w.tithi_name}, {w.nakshatra_name}")

# Prashna (horary)
from vedic_calc import cast_prashna_chart, evaluate_prashna
prashna_chart = cast_prashna_chart(2026, 3, 17, 14, 30, 19.076, 72.878, 5.5)
verdict = evaluate_prashna(prashna_chart, query_house=10)  # career question
print(f"Verdict: {verdict.verdict}")

# Detect yogas and doshas
from vedic_calc import detect_yogas, detect_doshas
yogas = detect_yogas(chart)
doshas = detect_doshas(chart)
for y in yogas:
    print(f"Yoga: {y.name} ({y.yoga_type})")
```

## Development

```bash
git clone https://github.com/atolat/vedic-calc.git
cd vedic-calc
uv sync --extra dev
uv run pytest -v
```

## Documentation

Full documentation available at the [docs site](https://atolat.github.io/vedic-calc/) or in the `docs/` directory:

- [Concepts](docs/concepts.md) -- Vedic astrology concepts explained for beginners and practitioners
- [API Reference](docs/api.md) -- complete API with code examples for every public function
- [Architecture](docs/architecture.md) -- system design, data flow, and module responsibilities
- [Accuracy & Testing](docs/accuracy.md) -- testing strategy, 461 tests, cross-validation approach
- [Contributing](docs/contributing.md) -- development setup, project structure, rules

## License

AGPL-3.0
