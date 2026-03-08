# vedic-calc — Project Conventions

## Code Standards
- All code must be readable, well-commented, and easy to understand
- **Heavy commenting is mandatory** — every formula must cite its source (BPHS chapter, Surya Siddhanta, etc.)
- Explain Vedic/astrological terminology inline for developers who are new to the domain
- Every module needs a docstring explaining its purpose, what concepts it implements, and why
- Every public function needs a docstring with Args, Returns, and Example
- Include worked examples in comments (e.g., "45° → floor(45/30)+1 = 2 → Taurus")
- Use type hints everywhere
- Use Pydantic models for all data structures (frozen/immutable where possible)
- Pure functions preferred — no global mutable state
- Only `ephemeris.py` may import pyswisseph — everything else works with abstract values

## Testing
- **Every new feature must have tests** — no exceptions
- Every day's output must be testable with a simple `pytest`
- Tests should use known birth chart data verified against external sources
- Test file names: `test_<module>.py`
- Use `uv run pytest` to run tests
- Cross-validate calculations against raw pyswisseph where possible

## Documentation
- **Keep docs updated with every code change** — docs are not an afterthought
- Update `docs/concepts.md` when new Vedic concepts are introduced
- Update `docs/api.md` when new public functions are added
- Update `docs/architecture.md` when new modules are added
- Run `uv run mkdocs build --strict` to verify docs build

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
