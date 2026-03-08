# vedic-calc

**Open-source Vedic astrology calculation library built on the Swiss Ephemeris.**

vedic-calc provides accurate astronomical calculations for Vedic (sidereal) astrology — planetary positions, birth charts, nakshatras, dasha periods, and panchanga — with a clean, type-safe Python API.

## Why vedic-calc?

| Feature | vedic-calc | PyJHora | pyswisseph (raw) |
|---------|-----------|---------|------------------|
| License | Apache 2.0 | AGPL (restrictive) | Modified BSD |
| GUI dependencies | None | Requires PyQt6 | None |
| API design | Pydantic models, pure functions | GUI-coupled, global state | Low-level C bindings |
| Vedic astrology | Built-in | Built-in | DIY |
| JSON serializable | Yes (all models) | No | No |

## Quick Start

```bash
# Install
pip install vedic-calc

# Or with uv
uv add vedic-calc
```

```python
from vedic_calc import calculate_chart

chart = calculate_chart(
    year=1990, month=3, day=15,
    hour=10, minute=30,
    latitude=19.0760, longitude=72.8777,  # Mumbai
    timezone_offset=5.5,                   # IST
)

# Access planetary positions
for planet, pos in chart.planets.items():
    print(f"{planet.name}: {pos.sign.name} {pos.degree_in_sign:.1f}°")

# JSON export
print(chart.model_dump_json(indent=2))
```

## Design Principles

1. **Accuracy first** — Swiss Ephemeris for positions, cross-validated against astronomical facts
2. **Pure functions** — no global state, no side effects, easy to test
3. **Immutable data** — all models are frozen Pydantic BaseModels
4. **Thin abstraction** — only `ephemeris.py` touches pyswisseph, everything else is pure Python
5. **Zero GUI dependencies** — headless library, not a desktop app
