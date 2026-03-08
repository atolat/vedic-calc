# vedic-calc

Open-source Vedic astrology calculation library built on the Swiss Ephemeris.

## Quick Start

```bash
uv sync --extra dev   # Install dependencies
uv run pytest         # Run tests
```

## Usage

```python
from vedic_calc import calculate_chart

chart = calculate_chart(
    year=1990, month=3, day=15,
    hour=10, minute=30,
    latitude=19.0760, longitude=72.8777,  # Mumbai
    timezone_offset=5.5,                   # IST
)

# Planetary positions
for planet, pos in chart.planets.items():
    print(f"{planet.name}: {pos.sign.name} {pos.degree_in_sign:.1f}°")

# Houses
for house in chart.houses:
    print(f"House {house.house_number}: {house.sign.name} (lord: {house.lord.name})")
```

## License

Apache 2.0
