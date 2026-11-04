# SolarWindPy

In-situ solar wind plasma analysis. The author owns the physics and the public API.

## Environment

- Run every Python tool inside the `solarwindpy` conda env: `conda run -n solarwindpy <command>`,
  or activate the env first. Outside it, `python` is the base install and `pytest` and
  `lint-imports` are not on PATH.
- A stale env produces failures that look like code bugs. Before debugging a surprising failure,
  check that the env imports this checkout and a pandas inside the `pyproject.toml` range:
  `conda run -n solarwindpy python -c "import solarwindpy, pandas; print(solarwindpy.__file__, pandas.__version__)"`
- The editable install maps `solarwindpy` to one checkout's `src/`. `pytest` (and so the commit
  hook) puts this checkout's `src/` first through `pythonpath` in `pyproject.toml`, but `python -c`
  and `lint-imports` do not: in another worktree, prefix those with `PYTHONPATH=$PWD/src`.
- Rebuild the env: `solarwindpy.yml` leaves the Python version to CI, so pin it in a copy
  (`python=3.12`) and run `conda env create -f <copy>`, then
  `conda run -n solarwindpy pip install -e ".[dev]"`. Plain `pip install -e .` leaves out
  import-linter and pre-commit.
- Install the git hooks once per clone:
  `conda run -n solarwindpy pre-commit install --hook-type pre-commit --hook-type commit-msg`.

## Checks

- Full suite: `conda run -n solarwindpy pytest -q` (about one minute).
- One file: `conda run -n solarwindpy pytest -q tests/core/test_plasma.py`
- Network and slow tests are skipped unless you pass `--run-drift` or set `SWP_RUN_DRIFT=1`.
- Import layering: `conda run -n solarwindpy lint-imports`
- Format and lint at the versions CI pins:
  `conda run -n solarwindpy pre-commit run ruff-check --files <paths>` and
  `conda run -n solarwindpy pre-commit run ruff-format --files <paths>`.
- Doctests: `conda run -n solarwindpy pytest --doctest-modules src/solarwindpy -q`
- The pre-commit hook runs the full suite with a coverage floor in
  `.claude/hooks/pre-commit-tests.sh`. The floor is a ratchet below measured coverage, not a
  target; raise it as coverage rises.

## Data model

- Columns are a three-level MultiIndex named `M` (measurement), `C` (component), `S` (species).
  An empty string means no component or no species.
- Select columns with `.xs()`, which shares the parent's data instead of copying it; the package
  relies on this to keep memory down. Do not add `.copy(deep=True)` in load or compute paths.
  Under pandas 3 copy-on-write, writing to an `.xs()` result does not change the parent.

## Conventions

- Extract shared logic at the second copy. In this repository that overrides the general
  three-examples rule.
- Cite scientific sources in docstrings: DOI or arXiv, plus the equation number when you implement
  a specific published result.
- External code: record its URL, license, and modifications in a comment. Copy only MIT, BSD,
  Apache 2.0, or public-domain code. When provenance or license is unclear, reimplement.
- Commit subjects follow Conventional Commits (`fix(core):`, `feat(plotting):`, `chore:`); the
  commit-msg hook rejects others.
- Renaming a public name, changing a column label, or changing a physical result is the author's
  decision: propose it, do not make it.
- Tests follow `.claude/docs/TEST_PATTERNS.md`. Read it before writing or reviewing a test.
- Changes are test-first. Before a stage, list the tests it touches and classify each as guard
  (passes unchanged before and after), update, delete, or fragile (a pinned number with no
  source; rewrite it as a relation or a cited reference value). Land the target tests first as
  `pytest.mark.xfail(strict=True)`, then the code change that removes the marker.
- Release work follows `.claude/docs/RELEASING.md`.
- Branches: commit to the current branch, including master. Branch only when the work needs
  isolation: a risky migration, a spike, or parallel worktrees.

## Gotchas

- `tests/test_hooks.py` checks `.claude/settings.json`: documented keys only, no hooks
  registered, and pushes ask first. Change both together.
- Untracked directories inside `src/solarwindpy/` belong to the author. Do not edit, move, or commit
  them.
