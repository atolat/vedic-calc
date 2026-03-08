# vedic-calc — Project Conventions

## Code Standards
- All code must be readable, well-commented, and easy to understand
- Every module needs a docstring explaining its purpose
- Every public function needs a docstring with Args, Returns, and Example
- Use type hints everywhere
- Use Pydantic models for all data structures (frozen/immutable where possible)
- Pure functions preferred — no global mutable state
- Only `ephemeris.py` may import pyswisseph — everything else works with abstract values

## Testing
- Every day's output must be testable with a simple `pytest`
- Tests should use known birth chart data verified against external sources
- Test file names: `test_<module>.py`
- Use `uv run pytest` to run tests

## Dependencies
- Use `uv` for dependency management (fast, modern)
- Keep all versions latest stable
- `pyproject.toml` is the single source of truth for deps
- Install: `uv sync` (that's it)

## Structure
- Source: `src/vedic_calc/`
- Tests: `tests/`
- Apache 2.0 license

## Commits
- Only commit when user explicitly approves
- Concise commit messages describing what was added
