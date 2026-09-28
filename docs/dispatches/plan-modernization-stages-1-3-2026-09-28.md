<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# Plan: execute dispatch-solarwindpy-modernization-phases-2026-09-28 (Stages 1 to 3)

## Context

The dispatch at `docs/dispatches/dispatch-solarwindpy-modernization-phases-2026-09-28.md` is the
work order: make the three remaining W1 gates able to fail, make every declared Python/pandas
version one the package has run (W3), and write the phase-4 `/batch` instruction for W4/W5/W6.
Done-definition adopted: every Acceptance Criterion in that dispatch returns its stated value,
and the closing protocol (empirical findings, reap) runs. Anything short of that is reported as
unfinished with the failing AC named.

## Author decisions (2026-09-27)

- Push master at both checkpoints and merge the lockfile PR after local verification: authorized.
- Sphinx `-W` lands now; docs CI red and deploy paused until the phase-4 docs-warnings unit,
  which the phase-4 instruction flags for early review. The author distrusts the existing docs
  build and `usage.rst` (early generative-model output), so the red build is the honest signal.
- `usage.rst` collected and marked strict xfail from `docs/source/conftest.py`.

## State verification (run 2026-09-27, read-only)

- Suites green: pandas 2.3.3 / py3.13 → 2253 passed, 20 skipped, 9 xfailed; pandas 3.0.5 /
  py3.12 → 2234 passed, 18 skipped, 12 xfailed. Both 0 failed.
- `pytest --doctest-modules solarwindpy` → 3 failed, 22 passed, 37 skipped (composite
  `GaussianPlusHeavySide`, core `FitFunction.residuals`, spiral `plot_contours` NameError).
- **Divergence:** local master is 2 ahead of origin (`37799ac1` TEST_PATTERNS, `9d4f88f0` the
  dispatch). Resolved by the push checkpoint below.
- `staged-recipes-fork/`: no unpushed commits, no dirty files, no stash. Safe to delete.
- Dependabot pip entry already has `directory: "/"`, so the AC holds today; the intent change is
  the update strategy (see Stage 2.4).
- `scripts/`: 6 black failures, ~185 flake8 violations outside the runner (mostly W293, F541,
  F401, E226; mechanical).
- `usage.rst` holds 13 `>>>` lines, 3 of whose imports fail (program plan W5).

## Stage 1, W1 gates (three commits)

Commit route for every commit: explicit-path `git add`, then `conda run -n solarwindpy git commit`.
Never `-A`, never `--no-verify`; retry on `index.lock`.

1. **Doctests under pytest.**
   - Positive control first: run the old runner (reports 100%) and pytest (3 failed); record both.
   - Fix the 3 failures inside their docstrings where output is derivable; otherwise strict xfail
     with reason (via `pytest_collection_modifyitems` in a `conftest.py`, since doctest items take
     no decorators).
   - `usage.rst`: collected by `--doctest-glob='*.rst' docs/source`, marked strict xfail from a new
     `docs/source/conftest.py` naming the W5 usage rewrite as what retires it.
   - Rewrite `.github/workflows/doctest_validation.yml`: py3.12, run
     `pytest --doctest-modules solarwindpy` and `pytest --doctest-glob='*.rst' docs/source`; drop the
     runner-based summary/PR-comment/spot-check jobs; keep `drift-detection` on 3.12.
   - Delete `scripts/simple_doc_validation/`; repoint `CONTRIBUTING.md:44-88` to the pytest commands.
   - Demonstration in commit message: inject a wrong expected value into one docstring in a scratch
     edit, show pytest exits non-zero, revert.
2. **`docs/Makefile:4` `SPHINXOPTS ?=`.** Demonstration: inject a broken `:func:` ref into a scratch
   rst; `SPHINXOPTS='-W --keep-going -n' make -C docs html` exits 0 before and non-zero after;
   record exit codes and the error line. Revert the scratch ref.
3. **pre-commit covers `scripts/`.** Extend black and flake8 `files:` to
   `^(solarwindpy|tests|scripts|\.claude)/.*\.py$`. Demonstration: `pre-commit run black --files`
   on an unformatted `scripts/` file fails before. Then `black scripts/` and fix flake8 by hand
   (no blanket `noqa`); `pre-commit run black --all-files` and `flake8` both pass.

## Stage 2, W3 declarations

1. **Python floor + consistency test (one commit).** Write `tests/test_declared_versions.py` with
   test names containing `requires_python`. It reads `requires-python` with `packaging` and
   asserts each declared version satisfies it and each declared floor equals it: classifiers,
   `tox.ini` envlist, `.readthedocs.yaml`, `recipe/meta.yaml` `python >=`, and every
   `python-version`/`PYTHON_VERSION` value in `.github/workflows/*.yml` (yaml walk, skipping
   `${{ }}` expressions). Set `requires-python = ">=3.12,<4"`, run the test, and record the drift
   list it reports as the positive control. Then sweep: classifiers 3.12/3.13, tox
   `py312, py313`, RTD `"3.12"`, recipe `python >=3.12`, CI matrix `['3.12','3.13']`,
   `PYTHON_VERSION`, publish, sync-requirements (required: pip-compile on 3.11 cannot resolve a
   3.12-floor project), doctest workflow. Test passes.
2. **pandas floor by measurement.** Python 3.12 bounds candidates to pandas ≥2.1.1. In throwaway
   conda envs (py3.12, numpy<2, `pip install -e . --no-deps`), run the suite on the lowest patch of
   2.1 and, if it fails, 2.2. Floor = lowest passing; range `pandas>=<floor>,<4`. Commit with the
   measured table in the message. Remove the throwaway envs afterwards.
3. **RTD image.** Verify via Read the Docs build docs that `ubuntu-22.04` offers `python: "3.12"`;
   change the image in the same commit as 2.1 if not.
4. **Dependabot.** Keep `directory: "/"`; add `versioning-strategy: increase` so pip bumps raise
   the bound in `pyproject.toml` rather than editing lockfiles alone. Verify the option's pip
   semantics against GitHub's docs before committing; report residual uncertainty.
5. **Single recipe.** `git rm -r conda-recipe/`; update `.claude/settings.json:57` and
   `docs/MIGRATION-DEPENDENCY-OVERHAUL.md:32`. `rm -rf staged-recipes-fork/` after re-running the
   three emptiness checks immediately before.
6. **Push checkpoint + lockfiles.** Run both suites, then push master. The push
   touches `pyproject.toml`, which triggers `sync-requirements.yml`. Its PR is opened with
   `GITHUB_TOKEN`, so CI does not run on it: verify locally by building a fresh py3.12 env from the
   PR's `requirements-dev.lock`, running the suite, rerunning the pandas-3 suite, and confirming
   the three lockfiles agree on numpy/pandas/astropy/scipy. Merge only then, and pull.

## Stage 3, phase-4 batch instruction

Write `docs/dispatches/batch-phase4-2026-09-28.md`: W4/W5/W6 governance triples from the program
plan, `.claude/docs/TEST_PATTERNS.md` by path, one unit per directory/document set with a single
`OWNS:` line (directories end `/`), a long-runner list (hist2d-class rebuilds: remaining
`tests/plotting/`, `tests/solar_activity/` root, instabilities), per-unit baselines each with its
command, and the commit route (`conda run -n solarwindpy git commit`, explicit staging, push
branch, open PR, no merge). Inventory comes from re-deriving the plan's W4/W5/W6 lists against
the tree. Excluded per Anti-Patterns: `lnlambda` 29.9, `gh-plan-create.sh` and `.claude/hooks/plan-*.py`.
Includes the three stale TEST_PATTERNS references, the D205 at `tests/core/test_ions.py:223`,
the `import-linter` replacement for `tests/test_circular_imports.py`, `docs/transition-guide-doc-validation.md`
(runner doc, W6), and whichever unit owns `usage.rst` also owns `docs/source/conftest.py`.
Check disjointness with the AC's `uniq -d` pipeline. Commit, then push (second push checkpoint)
so `origin/master..master` is 0. Stop.

## Verification

The dispatch's § Verification block, plus every Acceptance Criterion command run verbatim.
Then the closing protocol: `/session:empirical-findings` on the dispatch, `/session:reap` on it.
The program plan is not written up (phase 4 remains).

---

## Empirical Findings (2026-09-28 trial run)

### End-state metrics

- Suites after all stages: `conda run -n solarwindpy pytest -q` 2254 passed, 0 failed (pandas 3.0.6, numpy 2.3.5, Python 3.13); pandas-3 env 2238 passed, 0 failed (pandas 3.0.5, Python 3.12).
- Doctests: `pytest --doctest-modules solarwindpy -q` 24 passed, 1 xfailed, 0 failed (plan predicted 3 failures to repair; 22 passed at start).
- Sphinx warnings under `-W --keep-going -n`: 2309, against the plan's 83 (the 83 was measured without `-n`).
- pandas floor measured at 2.2 (2.1.1: 1 failed on the `"ME"` offset alias; 2.2.0: 0 failed), then raised to 3 by author decision.
- GitHub CI on `41d26ec1`: CI success, Doctest Validation success, Documentation failure (accepted until the phase-4 docs-build unit).

### Acceptance Criteria

The plan carries no Acceptance Criteria of its own; it defers to the dispatch's, whose outcomes are recorded in that dispatch's findings at `754e6327` (`git show 754e6327:docs/dispatches/dispatch-solarwindpy-modernization-phases-2026-09-28.md`).

| Plan stage | Status | Evidence |
|---|---|---|
| Stage 1, W1 gates | PASS | `93337e07`, `ca29eda5`, `2ddc52c6`; each commit message records its failing demonstration |
| Stage 2, W3 declarations | PASS | `c4c849b1` through `0742fd6a`, superseded in part by `6dddeb70`, `5447dc8e`, `a66de393` |
| Stage 2.6, lockfile PR merged | SUPERSEDED | PR #440 failed local verification (pins disagreed; `solarwindpy.yml` lost dev tools) and was closed unmerged; lockfiles retired in `5447dc8e` |
| Stage 3, phase-4 instruction | PASS | `36d3eaaa`; `grep -oE '^OWNS: .*' docs/dispatches/batch-phase4-2026-09-28.md \| tr ' ,' '\n\n' \| grep -v '^OWNS:' \| grep . \| sort \| uniq -d` prints nothing, with 25 `OWNS:` lines present as the positive control |
| Origin in sync before phase 4 | PASS | `git rev-list --count origin/master..master` → 0 after `41d26ec1` |

### Deviations from plan

- Dependabot uses `versioning-strategy: widen`, not `increase`: GitHub's docs say `increase` raises the floor to each new release, which would overwrite measured floors.
- The author set the dependency model to a single source: `pyproject.toml` only, pandas `>=3,<4`, no lockfiles, no in-repo conda recipe (conda-forge's feedstock is the recipe), `solarwindpy.yml` kept as the unversioned dev environment.
- Retiring the lockfiles let CI install black 26.5.1 against pre-commit's 25.1.0, turning CI red; fixed by pinning black 26.5.1 once in `.pre-commit-config.yaml` and routing CI through pre-commit (`3d0f83fd`), with the reformat isolated in `ec080c75` and listed in `.git-blame-ignore-revs`.
- The local `solarwindpy` env moved to pandas 3 through conda-forge with numpy held below 2.4 for numba compatibility.
- `staged-recipes-fork/` was deleted by the author after the unpushed/dirty/stash checks came back empty.
- `/session:reap` Gate 2 aborts on any file entry in its scan list; a fix is dispatched in the plugin repo (`67d15b1` there).

### Commits

- `93337e07` ci(docs): run doctests under pytest and retire the standalone runner
- `ca29eda5` fix(docs): let SPHINXOPTS from the environment reach sphinx-build
- `2ddc52c6` ci(pre-commit): extend black and flake8 to scripts/, and lint scripts/
- `c4c849b1` build!: require Python 3.12 and check every declared version against it
- `f1563729` build: set the pandas range from measurement, >=2.2,<4
- `a7ac9693` ci(dependabot): route pip updates through pyproject.toml ranges
- `0742fd6a` build(conda): keep recipe/meta.yaml as the single conda recipe
- `36d3eaaa` docs(dispatch): write the phase-4 batch instruction for W4, W5, W6
- `6dddeb70` build!: require pandas 3
- `5447dc8e` build!: retire the lockfiles; install everything from pyproject.toml
- `a66de393` build(conda): remove the in-repo recipe copy; floor test reads what is tested
- `9f31b51c` docs(changelog): record the Python 3.12 and pandas 3 floors and the single dependency source
- `80785f1d` docs(dispatch): align the phase-4 instruction with the single dependency source
- `1acc42d0` fix(fitfunctions): make the residuals doctest independent of numpy's bool repr
- `754e6327` docs(tdd): append empirical findings to dispatch-solarwindpy-modernization-phases-2026-09-28 dispatch
- `8de8587b` docs(tdd): purge completed dispatch-solarwindpy-modernization-phases-2026-09-28 unit (git retains the bytes)
- `3d0f83fd` ci: run black and flake8 at the versions pinned in pre-commit
- `ec080c75` style: reformat solarwindpy/ with black 26.5.1
- `26347482` chore: skip the black 26.5.1 reformat in git blame
- `41d26ec1` docs(dispatch): repoint two phase-4 line cites moved by the black reformat

## Spent-Mark: executed, findings recorded
