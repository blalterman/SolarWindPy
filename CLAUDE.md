# CLAUDE.md

Guidance for Claude Code working in the SolarWindPy repository.

## What this package is

SolarWindPy analyzes in-situ solar wind plasma measurements. The public surface
lives under `solarwindpy/`: `core/` (data model and physics), `fitfunctions/`
(curve fitting), `plotting/`, `instabilities/`, `solar_activity/`, `tools/`.

## Data model

Measurements are held in a single pandas DataFrame with a three-level column
MultiIndex named `M`, `C`, `S`:

- `M` — measurement (e.g. `n`, `v`, `w`, `b`)
- `C` — component (e.g. `x`, `y`, `z`, or empty for scalars)
- `S` — species (e.g. `p1`, `p2`, `a`, or empty for spacecraft-frame quantities)

See the docstring at `solarwindpy/core/plasma.py:102` for a constructed example.

**Access columns with `.xs()`, and do not `.copy(deep=True)`.** The codebase
relies on `.xs()` returning a view to keep memory down; this is stated at
`solarwindpy/core/units_constants.py:16`. Introducing a deep copy in a hot path
is a real regression, not a style preference.

Key classes: `Plasma` (the container, `core/plasma.py`), `Ion` (per-species,
`core/ions.py`), `Base` (abstract, `core/base.py`). Physical constants come from
`scipy.constants` via `core/units_constants.py`, which also provides a `Units`
converter for every quantity `Plasma` stores.

## Commands

```bash
pytest -q                                  # full suite
pytest tests/core -q                       # one subpackage
.claude/hooks/test-runner.sh --changed     # only tests for changed files
.claude/hooks/test-runner.sh --physics     # physics validation subset

black solarwindpy/ tests/                  # format (CI runs black --check)
flake8 solarwindpy/ tests/                 # lint
lint-imports                               # layering contract in pyproject.toml
```

**Invoke the bare `pytest` binary, not `python3 -m pytest`.** The `-m` form
prepends the working directory to `sys.path`, shadowing the installed package;
the suite then reports ~25 spurious failures in import and inheritance tests.
Under `pytest` the suite is green.

CI runs `pytest`, `black --check`, `flake8`, and `lint-imports` against
`solarwindpy/`.

The `solarwindpy-physics` pre-commit hook runs the full suite with
`--cov-fail-under=92` on any commit touching a `.py` file. Measured coverage is
~94%, so this is a regression ratchet rather than a target; raise it as coverage
rises. `.claude/hooks/coverage-monitor.py` separately reports per-module
coverage from a `Stop` hook — those numbers are advisory and block nothing.

## Conventions

- NumPy-style docstrings.
- Conventional commit subjects (`fix(core):`, `feat(plotting):`, `chore:`).
- Put reusable logic in one shared method that every caller uses; do not copy
  lines between call sites. Extract at the second copy: in this repository this
  overrides the global "three examples before abstracting" rule.
- Cite scientific sources in docstrings: DOI or arXiv, and the equation number
  when implementing a specific published result.
- Attribution rules live in `.claude/docs/ATTRIBUTION.md`. In short: note
  "Generated with Claude Code" in commit messages for AI-written code, and
  record URL, license, and modifications in a comment for external code. When
  the provenance of a snippet is unclear, reimplement rather than copy.

## Further documentation

`.claude/docs/` holds the detail beyond this file: `DEVELOPMENT.md`,
`HOOKS.md`, `TEST_PATTERNS.md`, `MAINTENANCE.md`,
`RELEASING.md`, `ATTRIBUTION.md`.
