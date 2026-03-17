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
│   ├── __init__.py              # Public API exports (50+ functions)
│   ├── core/
│   │   ├── constants.py         # Enums + lookup tables (Planet, Sign, Nakshatra, etc.)
│   │   ├── ephemeris.py         # pyswisseph wrapper (ONLY swe import)
│   │   └── types.py             # Pydantic data models (35+ frozen models)
│   ├── chart/
│   │   ├── calculator.py        # Birth chart calculation
│   │   ├── renderer.py          # ASCII + SVG chart rendering
│   │   ├── divisional.py        # Varga charts (D-1 through D-60)
│   │   ├── aspects.py           # Planetary drishti (aspects)
│   │   ├── combustion.py        # Combustion detection
│   │   ├── states.py            # Planetary dignity + dispositors
│   │   ├── houses.py            # House analysis (lord, occupants, strength)
│   │   ├── transits.py          # Transit chart overlays
│   │   ├── special_lagnas.py    # Hora/Ghati/Bhava/Sree Lagna
│   │   ├── upagrahas.py         # Sub-planets (Dhuma, Vyatipata, etc.)
│   │   └── sahams.py            # Arabic parts (lots)
│   ├── dasha/
│   │   ├── calculator.py        # Vimsottari dasha
│   │   ├── yogini.py            # Yogini dasha (36-year cycle)
│   │   ├── ashtottari.py        # Ashtottari dasha (108-year cycle)
│   │   └── narayana.py          # Narayana dasha (sign-based, Jaimini)
│   ├── panchanga/
│   │   ├── calculator.py        # Five-element daily calendar
│   │   └── festivals.py         # Hindu festival detection
│   ├── muhurta/
│   │   ├── calculator.py        # Daily muhurta (Rahu Kalam, Abhijit, etc.)
│   │   └── solver.py            # Muhurta constraint solver
│   ├── prashna/
│   │   ├── chart.py             # Horary chart casting
│   │   ├── tajika.py            # Tajika yoga detection (5 yogas)
│   │   └── evaluator.py         # Prashna verdict engine
│   ├── jaimini/
│   │   ├── karakas.py           # Chara Karaka (variable significators)
│   │   └── arudha.py            # Arudha Pada calculation
│   ├── kp/
│   │   ├── calculator.py        # KP chart (Placidus cusps)
│   │   ├── houses.py            # Placidus house cusp calculation
│   │   └── sublords.py          # KP sublord lookup table
│   ├── compatibility/
│   │   ├── calculator.py        # Ashtakoot (North Indian, 8 factors)
│   │   └── porutham.py          # Porutham (South Indian, 10 factors)
│   ├── strength/
│   │   ├── shadbala.py          # Six-fold planetary strength
│   │   └── ashtakavarga.py      # 8-source benefic point system
│   ├── yoga/
│   │   └── calculator.py        # Classical yoga detection (~20 yogas)
│   ├── dosha/
│   │   └── calculator.py        # Dosha detection (Mangal, Kaal Sarpa, etc.)
│   ├── varshaphal/
│   │   └── calculator.py        # Solar return (annual horoscopy)
│   └── numerology/
│       └── calculator.py        # Chaldean numerology
├── tests/
│   ├── test_accuracy.py         # Cross-validation + astronomical facts
│   ├── test_chart.py            # Birth chart integration
│   ├── test_helpers.py          # Unit tests for helpers
│   ├── test_constants.py        # Lookup table integrity
│   ├── test_renderer.py         # ASCII + SVG rendering
│   ├── test_dasha.py            # Vimsottari dasha
│   ├── test_additional_dashas.py # Yogini, Ashtottari, Narayana
│   ├── test_panchanga.py        # Daily calendar
│   ├── test_divisional.py       # Varga charts
│   ├── test_aspects.py          # Planetary aspects
│   ├── test_combustion.py       # Combustion
│   ├── test_states.py           # Planetary dignity
│   ├── test_houses_analysis.py  # House analysis
│   ├── test_transits.py         # Transit charts
│   ├── test_compatibility.py    # Ashtakoot compatibility
│   ├── test_porutham.py         # South Indian compatibility
│   ├── test_yogas.py            # Yoga detection
│   ├── test_doshas.py           # Dosha detection
│   ├── test_muhurta.py          # Daily muhurta
│   ├── test_muhurta_solver.py   # Muhurta constraint solver
│   ├── test_prashna.py          # Prashna + Tajika
│   ├── test_jaimini.py          # Chara karakas + arudha padas
│   ├── test_strength.py         # Shadbala + Ashtakavarga
│   ├── test_kp.py               # KP system
│   ├── test_varshaphal.py       # Solar return
│   ├── test_numerology.py       # Numerology
│   ├── test_sahams.py           # Arabic parts
│   └── comparison/              # Cross-validation against PyJHora
│       ├── test_compare_divisional.py
│       ├── test_compare_yogas.py
│       ├── test_compare_dasha.py
│       ├── test_compare_aspects.py
│       ├── test_compare_shadbala.py
│       ├── test_compare_ashtakavarga.py
│       ├── test_compare_muhurta.py
│       └── test_compare_doshas.py
├── docs/                        # MkDocs documentation (this site)
├── pyproject.toml               # Dependencies + build config
└── mkdocs.yml                   # Docs site config
```

## Rules

1. **Only `ephemeris.py` may import pyswisseph** -- everything else works with floats
2. **All data models must be frozen Pydantic** -- immutable, JSON-serializable
3. **Pure functions preferred** -- no global mutable state
4. **Every public function needs a docstring** with Args, Returns, Example
5. **Every new feature needs tests** -- run `uv run pytest` before committing

## Adding a New Calculation

1. If it needs raw planetary data, add a function in `ephemeris.py`
2. If it needs new data types, add a Pydantic model in `types.py`
3. If it needs new constants, add to `constants.py`
4. The calculation itself goes in the appropriate module (see project structure above)
5. Export the public function from `__init__.py`
6. Write tests in `tests/`
7. If a PyJHora equivalent exists, add a comparison test in `tests/comparison/`

## Clean-Room Implementation

vedic-calc is a **clean-room implementation** based on published mathematical formulas from classical texts (BPHS, Surya Siddhanta, Phaladeepika, Muhurta Chintamani, Saravali).

The algorithms are mathematical facts, not proprietary code.

!!! warning "Important"
    Do NOT copy code from PyJHora or other AGPL-licensed projects. Implement from the published mathematical specifications. You may study other implementations to understand *what* needs to be calculated, but the *how* must be your own code.
