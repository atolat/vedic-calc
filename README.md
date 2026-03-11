# vedic-calc

Open-source Vedic astrology calculation library built on the Swiss Ephemeris.

Pure functions, Pydantic models, no GUI dependencies. Apache 2.0 licensed.

## Features

- **Birth chart** — planetary positions, houses (whole sign), nakshatras, padas
- **Dasha** — Vimsottari mahadasha/antardasha/pratyantardasha timeline
- **Panchanga** — daily Vedic calendar (tithi, nakshatra, yoga, karana, vara)
- **Compatibility** — Ashtakoot Milan (8-fold, 36-point scale)
- **Rendering** — South Indian, North Indian (ASCII), and SVG chart diagrams

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
    print(f"{planet.name}: {pos.sign.name} {pos.degree_in_sign:.1f}°")

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
print(f"Score: {result.total_score}/36 — {result.verdict}")
for k in result.kuttas:
    print(f"  {k.name}: {k.obtained}/{k.maximum}")
```

## Development

```bash
git clone https://github.com/atolat/vedic-calc.git
cd vedic-calc
pip install -e ".[dev]"
pytest
```

## License

Apache 2.0
