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
```

CI runs `pytest`, `black --check`, and `flake8` against `solarwindpy/`.
Coverage target is 95%, enforced by `.claude/hooks/coverage-monitor.py`.

Known state: the `tests/solar_activity/` suite has pre-existing failures tied to
network-dependent data loaders. They are unrelated to changes elsewhere.

## Planning workflow

Plans are GitHub Issues, created by scripts that must be **executed**, not
described. The flag syntax is not guessable, so it is recorded here:

```bash
# Overview issue
.claude/scripts/gh-plan-create.sh -p <priority> -d <domain> "Plan Title"
#   priority: critical|high|medium|low
#   domain:   physics|data|plotting|testing|infrastructure|docs

# Phase issues, batch mode
mkdir -p tmp
cat > tmp/phases.conf <<'EOF'
Phase Name|Estimated Duration|Dependencies
Foundation Setup|2-3 hours|None
Core Implementation|4-5 hours|Phase 1
EOF
.claude/scripts/gh-plan-phases.sh -b tmp/phases.conf <issue_number>

.claude/scripts/gh-plan-status.sh            # review open plans
```

If the result is prose instead of a created GitHub Issue, the step did not run.

## Conventions

- NumPy-style docstrings.
- Conventional commit subjects (`fix(core):`, `feat(plotting):`, `chore:`).
- Cite scientific sources in docstrings: DOI or arXiv, and the equation number
  when implementing a specific published result.
- Attribution rules live in `.claude/docs/ATTRIBUTION.md`. In short: note
  "Generated with Claude Code" in commit messages for AI-written code, and
  record URL, license, and modifications in a comment for external code. When
  the provenance of a snippet is unclear, reimplement rather than copy.

## Further documentation

`.claude/docs/` holds the detail beyond this file: `DEVELOPMENT.md`,
`HOOKS.md`, `PLANNING.md`, `TEST_PATTERNS.md`, `MAINTENANCE.md`,
`RELEASING.md`, `ATTRIBUTION.md`.
