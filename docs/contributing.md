# Contributing

## Development Setup

```bash
# Clone the repo
git clone https://github.com/atolat/vedic-calc.git
cd vedic-calc

# Install dependencies (requires uv)
uv sync --extra dev --extra docs

# Run tests
uv run pytest -v

# Serve docs locally
uv run mkdocs serve
```

## Project Structure

```
vedic-calc/
├── src/vedic_calc/
│   ├── __init__.py            # Public API exports
│   ├── core/
│   │   ├── constants.py       # Enums + lookup tables
│   │   ├── ephemeris.py       # pyswisseph wrapper (ONLY swe import)
│   │   └── types.py           # Pydantic data models
│   ├── chart/
│   │   └── calculator.py      # Birth chart calculation
│   ├── dasha/                 # Planetary period calculations
│   └── panchanga/             # Daily calendar calculations
├── tests/
│   ├── test_accuracy.py       # Cross-validation + astronomical facts
│   ├── test_chart.py          # Integration tests
│   ├── test_constants.py      # Lookup table tests
│   └── test_helpers.py        # Unit tests for helpers
├── docs/                      # MkDocs documentation (this site)
├── pyproject.toml             # Dependencies + build config
└── mkdocs.yml                 # Docs site config
```

## Rules

1. **Only `ephemeris.py` may import pyswisseph** — everything else works with floats
2. **All data models must be frozen Pydantic** — immutable, JSON-serializable
3. **Pure functions preferred** — no global mutable state
4. **Every public function needs a docstring** with Args, Returns, Example
5. **Every new feature needs tests** — run `uv run pytest` before committing

## Adding a New Calculation

1. If it needs raw planetary data → add a function in `ephemeris.py`
2. If it needs new data types → add a Pydantic model in `types.py`
3. If it needs new constants → add to `constants.py`
4. The calculation itself goes in the appropriate module (`chart/`, `dasha/`, `panchanga/`)
5. Write tests in `tests/`

## Clean-Room Implementation

vedic-calc is a **clean-room implementation** based on published mathematical formulas from classical texts (BPHS, Surya Siddhanta). The algorithms are mathematical facts, not proprietary code.

!!! warning "Important"
    Do NOT copy code from PyJHora or other AGPL-licensed projects. Implement from the published mathematical specifications. You may study other implementations to understand *what* needs to be calculated, but the *how* must be your own code.
