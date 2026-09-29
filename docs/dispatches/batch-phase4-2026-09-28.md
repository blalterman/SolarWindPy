<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# Phase-4 batch instruction: W4 tests, W5 documentation, W6 retirement

author_signoff: none

The author pastes everything below the line after `/batch`. Each unit reads only the shared
sections and its own unit block.

**Before launch.** `git -C /Users/balterma/observatories/code/SolarWindPy rev-list --count origin/master..master`
must print `0`. Batch worktrees branch from `origin/master`; a stale origin sent three pilot
units to a base 25 commits old.

---

## Shared brief (every unit reads this)

### Program

Governing principle: **every claim this repository makes is warranted or bounded.** Warranted
means it points outside itself to something independently checkable (a physical identity, a
published constant, a cited paper, a canonical source file, a re-runnable measurement). Bounded
means it names the observable event after which it stops being the best available claim.

When a claim cannot be warranted there are five routes: cite a source; assert a property rather
than a value; record present behavior in a bounded recording file as part of a named migration;
declare an honest gap; or, for a defect you can warrant in code outside your owned paths, write
the correct test marked `@pytest.mark.xfail(strict=True, reason=...)` naming what retires it. A
unit that can take none of these reports what it found instead of writing around it.

Governing property: a check seen only to pass is indistinguishable from one that cannot fail.
Every check you add or rely on is shown failing against a known-bad input, and you report the
command and its output.

The test standard is `/Users/balterma/observatories/code/SolarWindPy/.claude/docs/TEST_PATTERNS.md`.
Read it before writing a test. Every new or rebuilt test's docstring ends with one `ON FAILURE:`
line, and `grep -c "ON FAILURE"` over a rebuilt file equals its `def test_` count.

### Workstream governance

**W4, tests.** *Purpose:* the evidence both the author and the assistant reason from; a test
that cannot fail silently licenses whatever is built on it. *Intent:* a test that passes means
the behavior is right. *Seam:* a unit decides test structure, fixtures, parametrization, and
what to assert about behavior. The author decides whether a physics assertion is correct. A unit
that cannot determine an expected physical value reports that rather than asserting whatever
the code currently returns. The governing question for every test: reimplement the module
correctly from scratch; does the test still pass, and does it fail on a broken one?

**W5, documentation.** *Purpose:* the face a researcher meets the library through; a wrong
example costs them a debugging session before they reach the science. *Intent:* every
documented call runs. *Seam:* a unit fixes what does not run and regenerates what is derived
from source. The author decides what the library is described as doing. A unit that finds
documentation describing a capability the code lacks reports the discrepancy rather than
choosing which side is right. The author distrusts the existing docs build and `usage.rst`
(early generative-model output), so rewriting is preferred to patching where they conflict.

**W6, retirement.** *Purpose:* the working tree is the surface every session reads; a finished
or dead artifact competes with live ones. *Intent:* what remains in the tree has a stated
reason to exist. *Seam:* a unit proposes a removal, shows the path is recoverable from history
(`git log --oneline -1 -- <path>`), and shows the suite passes without it. The author approves
every removal by merging or declining the pull request. A unit that cannot name what ends an
artifact reports it as undecided rather than removing it.

### Seam for library defects

A unit that finds a library defect inside its own owned paths fixes it, with a test that fails
before the fix and passes after. A defect outside its owned paths becomes a strict xfail naming
what retires it. Physics values that cannot be derived or cited, and the exact wording of plot
labels, go back to the author.

### Reserved: do not touch

- The `29.9` constant in `Plasma.lnlambda` (parked until the author supplies its citation).
- `.claude/scripts/gh-plan-create.sh` and the `.claude/hooks/plan-*.py` scripts it calls: not
  deleted by any unit. `CLAUDE.md` documents them as the planning workflow; retiring them is the
  author's decision. (Unit `tooling-lint` may reformat them; it removes nothing.)
- Anything outside your `OWNS:` line. Partition rule: units own disjoint file sets.

### End-to-end verification (every unit)

```bash
conda run -n solarwindpy pytest -q
conda run -n imap-loaders-20260225 pytest -q --no-header \
  --ignore=tests/plotting/test_performance.py --ignore=tests/test_issue_titles.py
```

Both report `0 failed` at launch (pandas 3.0.6 / py3.13 and pandas 3.0.5 / py3.12). A unit is
done when both stay at `0 failed`. Run pytest as the bare binary inside the env, never
`python -m pytest`. Also run your own positive control and report its command and output,
including a unit that changed nothing.

### Commit route

1. Run `code-review` on your diff and fix what it surfaces.
2. Stage explicit paths only (`git add <path> ...`). Never `git add -A`, `git add .`, or
   `git commit -a`. On `index.lock`, wait and retry; never delete it.
3. Commit with `conda run -n solarwindpy git commit` (a bare shell resolves an older pytest
   that blocks the hook on correct work). Never `--no-verify`. Conventional subject; body ends
   with the attribution lines the session supplies.
4. Push your branch and open a pull request. Do not merge. End your report with `PR: <url>`.

### Report (every unit)

What changed; each baseline below re-measured before and after with its command; the positive
control's command and output; every seam you hit and whether you settled it or handed it back;
defects found, with the strict xfail or fix for each.

---

## Units expected to run long

Identified before launch. The pilot's hardest unit (`hist2d`) ran about ten times the median.

- `plotting-orbits`: `orbits.py` at 24.3% across 206 statements, 30 introspection-only asserts.
- `plotting-spiral`: `spiral.py` at 66.9% across 517 statements, 32 introspection-only asserts.
- `instabilities`: first tests for 192 statements at 32.8%, thresholds fitted in published papers.
- `source-core`: 32 nitpicky warnings from `solarwindpy/core` docstrings plus the 355-line
  commented-out class.

Coverage figures come from
`conda run -n solarwindpy pytest -q --cov=solarwindpy --cov-report=json:/tmp/cov.json` read per
file (`files[<path>].summary.percent_covered`); total 85.30% at launch.

---

## Units

### W4, tests

#### core-repair (keep, repair surgically)

OWNS: tests/core/__init__.py, tests/core/test_abundances.py, tests/core/test_alfvenic_turbulence.py, tests/core/test_base.py, tests/core/test_base_head_tail.py, tests/core/test_base_mi_tuples.py, tests/core/test_core_verify_datetimeindex.py, tests/core/test_ions.py, tests/core/test_plasma.py, tests/core/test_plasma_io.py, tests/core/test_quantities.py, tests/core/test_spacecraft.py

Keep the physics assertions; repairs only. Rename `TestData` in `test_base.py` so pytest stops
collecting it as a test class (every subclass in these files moves with it). Run or delete
`TestIonSpecificsOptions` (`test_ions.py:221`), which never executes. Fix the D205 docstring
warning at `test_ions.py:223`. Remove commented-out code, keep prose comments. Resolve the
permanently skipped tests. Fix flake8 in owned files. `test_plasma.py` was repaired by PR #435;
its `constants.`-derived coefficients must survive.

Baselines:
- `TestData` classes: 1 — `grep -rn "class TestData\b" tests/core | wc -l`
- skip sites in core and fitfunctions: 7 — `grep -rnE "@pytest.mark.skip\b|pytest.skip\(" tests/core tests/fitfunctions | wc -l` (split with `fitfunctions-repair`)
- comment lines in tests/core: 464 — `grep -rhcE "^\s*#" tests/core | paste -sd+ - | bc`
- live derivation sites: `grep -c "constants\." tests/core/test_plasma.py` must not fall
- flake8: `conda run -n solarwindpy flake8 tests/core/` (11 at launch across test_plasma.py and test_ions.py)

#### core-units-constants (rebuild)

OWNS: tests/core/test_units_constants.py

Rebuild so each constant's value is compared to CODATA through `scipy.constants` or
`scipy.constants.physical_constants`, and each `Units` conversion is checked by a round trip or
a dimensional identity. Positive control: perturb one constant in a scratch copy of
`solarwindpy/core/units_constants.py`, confirm the test fails, revert.

Baselines:
- tests: 5 — `grep -c "def test_" tests/core/test_units_constants.py`
- introspection-only asserts: 4 — `grep -cE "assert hasattr|assert callable" tests/core/test_units_constants.py`

#### fitfunctions-repair (keep, repair surgically)

OWNS: tests/fitfunctions/

Keep the parameter-recovery tests. Move mock targets to external boundaries in `test_core.py`,
`test_plots.py`, `test_trend_fits.py`; resolve skipped tests; fix flake8 (`test_hinge.py`,
`test_composite.py`, `test_heaviside.py`).

Baselines:
- mock sites: 29 — `grep -rcE "@patch|MagicMock|Mock\(|monkeypatch" tests/fitfunctions | awk -F: '{s+=$2} END {print s}'`
- flake8: `conda run -n solarwindpy flake8 tests/fitfunctions/` (16 at launch)

#### plotting-orbits (rebuild; long)

OWNS: tests/plotting/test_orbits.py

Baselines:
- introspection-only asserts: 30 — `grep -cE "assert hasattr|assert callable" tests/plotting/test_orbits.py`
- `solarwindpy/plotting/orbits.py` coverage: 24.3% (command above)
- flake8: 13 — `conda run -n solarwindpy flake8 tests/plotting/test_orbits.py | wc -l`

#### plotting-spiral (rebuild; long)

OWNS: tests/plotting/test_spiral.py

Baselines:
- introspection-only asserts: 32 — `grep -cE "assert hasattr|assert callable" tests/plotting/test_spiral.py`
- `solarwindpy/plotting/spiral.py` coverage: 66.9%
- flake8: 9 — `conda run -n solarwindpy flake8 tests/plotting/test_spiral.py | wc -l`

#### plotting-base-scatter (rebuild)

OWNS: tests/plotting/test_base.py, tests/plotting/test_scatter.py

Baselines:
- mock sites: 78 — `grep -cE "@patch|MagicMock|Mock\(|monkeypatch" tests/plotting/test_base.py tests/plotting/test_scatter.py | awk -F: '{s+=$2} END {print s}'`
- flake8: `conda run -n solarwindpy flake8 tests/plotting/test_base.py tests/plotting/test_scatter.py | wc -l` (16 at launch)

#### plotting-agg-tools (rebuild)

OWNS: tests/plotting/test_agg_plot.py, tests/plotting/test_tools.py, tests/plotting/test_nan_gaussian_filter.py

Baselines:
- introspection-only asserts: 21 — `grep -cE "assert hasattr|assert callable" tests/plotting/test_agg_plot.py tests/plotting/test_tools.py | awk -F: '{s+=$2} END {print s}'`
- `solarwindpy/tools/__init__.py` coverage: 12.8%

#### plotting-hist1d (new tests)

OWNS: tests/plotting/test_hist1d.py

`hist1d.py` is at 62.2% across 164 statements. `tests/plotting/test_histograms.py` was rebuilt
by PR #437 and is not yours; write the Hist1D contract tests in the new file, with binned
counts derived from `numpy.histogram` on the same input.

#### plotting-misc (rebuild)

OWNS: tests/plotting/__init__.py, tests/plotting/test_fixtures_utilities.py, tests/plotting/test_integration.py, tests/plotting/test_performance.py, tests/plotting/test_visual_validation.py

Baselines:
- tests: `grep -c "def test_" tests/plotting/test_fixtures_utilities.py tests/plotting/test_integration.py tests/plotting/test_performance.py tests/plotting/test_visual_validation.py` (14, 11, 16, 17)
- flake8: `conda run -n solarwindpy flake8 tests/plotting/test_fixtures_utilities.py tests/plotting/test_integration.py tests/plotting/test_performance.py | wc -l`

#### solar-activity-root (rebuild)

OWNS: tests/solar_activity/__init__.py, tests/solar_activity/test_base.py, tests/solar_activity/test_init.py, tests/solar_activity/test_plots.py

Known defects (verified by the pilot): `solar_activity/base.py:210` sets `_data_age` while the
`age` property at `:154` reads `_age`; `plot_on_colorbar` divides by `np.round(ssn.max(), -2)`,
0 for a window peaking at or below SSN 50. Both are outside your paths: strict xfail.

Baselines:
- mock sites: 21 — `grep -cE "@patch|MagicMock|Mock\(|monkeypatch" tests/solar_activity/test_base.py tests/solar_activity/test_init.py tests/solar_activity/test_plots.py | awk -F: '{s+=$2} END {print s}'`
- `solarwindpy/solar_activity/plots.py` coverage: 76.6%

#### instabilities (first tests; long)

OWNS: tests/instabilities/

`solarwindpy/instabilities/` (`beta_ani.py`, `verscharen2016.py`) is named in no test file.
Thresholds are fitted in published papers: cite each with its DOI in the test. What you cannot
cite goes to the author.

Baselines:
- test files naming the package: 0 — `git grep -l "instabilities" -- tests | wc -l`
- `solarwindpy/instabilities/verscharen2016.py` coverage: 32.8%

#### import-contract (replace)

OWNS: tests/test_circular_imports.py, .importlinter, pyproject.toml, .github/workflows/continuous-integration.yml

Replace `tests/test_circular_imports.py` with an `import-linter` contract in `.importlinter`,
add `import-linter` to the `dev` extra, and run `lint-imports` in CI. Positive control: introduce
a forbidden import in a scratch edit, confirm `lint-imports` fails, revert. You are the only unit
that edits `pyproject.toml`; do not change any version range in it.

Baselines:
- tests replaced: 11 — `grep -c "def test_" tests/test_circular_imports.py`
- flake8: 6 — `conda run -n solarwindpy flake8 tests/test_circular_imports.py | wc -l`

#### drift-shrink

OWNS: tests/drift/

Shrink to the checks that need the network or an outside source.
`tests/drift/test_drift_readthedocs.py` is superseded by the fast, default-suite
`tests/test_declared_versions.py`; retire it and move the one control in
`test_drift_controls.py` that imports from it.

Baselines:
- tracked files: 6 — `git ls-files tests/drift | wc -l`

#### tooling-lint

OWNS: .claude/hooks/plan-value-generator.py, .claude/hooks/plan-completion-manager.py, .claude/hooks/create-compaction.py, .claude/hooks/plan-value-validator.py, .claude/scripts/generate-test.py

flake8 only; behavior unchanged; delete nothing (see Reserved).

Baselines:
- flake8: `conda run -n solarwindpy flake8 <the five paths> | wc -l` (28 at launch)

### W5, documentation

#### usage

OWNS: docs/source/usage.rst, docs/source/conftest.py

Rewrite `usage.rst` modeled on `README.rst:19-49`, the one correct example in the repository.
It is collected by `pytest --doctest-glob='*.rst' docs/source` and marked strict xfail from
`docs/source/conftest.py`; when your rewrite runs, the xfail flips red. Remove the entry (and
the conftest file if it is then empty).

Baselines:
- doctest lines: 13 — `grep -c ">>>" docs/source/usage.rst`
- `conda run -n solarwindpy pytest --doctest-glob='*.rst' docs/source -q` → 1 xfailed

#### install-citation

OWNS: docs/source/installation.rst, CITATION.rst, README.rst

Rewrite `installation.rst` against `pyproject.toml` (Python >=3.12, pandas >=3,<4); drop the
outage note about a version three releases back. `README.rst:54` and `:65` still say Python 3.11.
Fill `CITATION.rst` from the published DOI already in the repository; wording of how the
author wants to be cited goes back to the author.

Baselines:
- `grep -c TODO CITATION.rst` → 1
- `grep -n "3\.11" README.rst docs/source/installation.rst`

#### test-patterns-refs

OWNS: .claude/commands/swp/test/audit.md, tools/dev/ast_grep/test-patterns.yml, .claude/docs/DEVELOPMENT.md

Repoint citations to sections the current `.claude/docs/TEST_PATTERNS.md` has (`grep -n '^## '
.claude/docs/TEST_PATTERNS.md`).

Baselines:
- `grep -n "TEST_PATTERNS" .claude/commands/swp/test/audit.md tools/dev/ast_grep/test-patterns.yml .claude/docs/DEVELOPMENT.md`

#### source-core, source-fitfunctions, source-plotting, source-misc (W5 docstrings with W6 commented code)

Each owns one slice of `solarwindpy/` so docstring work (W5) and commented-code removal (W6)
never meet in the same file from two units. In each: raise docstring coverage on modules under
50%, fix docstring references that are broken in fact (not ones `conf.py` resolves), and remove
commented-out code (prose comments stay). A defect found in your own files is yours to fix
with a test that fails before and passes after; that test lives in a new file under
`tests/` named in your `OWNS:` line.

Baselines for all four:
- `conda run -n solarwindpy python scripts/docstring_coverage.py` → Overall Coverage 53.6%,
  1180 items.
- Nitpicky Sphinx warnings, 122 total, every one attributed to a docstring in one of the four
  slices; docs CI turns green only when all four reach 0. Build a clean export (the
  `_autosummary/` directory is gitignored and a stale copy aborts the build):
  `T=$(mktemp -d); git archive HEAD docs LICENSE CITATION.rst | tar -x -C $T; ln -s "$PWD/solarwindpy" $T/solarwindpy; (cd $T/docs && conda run -n solarwindpy env SPHINXOPTS='-W --keep-going -n' make html) > $T/log 2>&1`,
  then count each warning once, by the first subpackage it names (a line usually names two: the
  file path and the `docstring of` target; the `sed` folds the `solarwidpy` typo in):
  `grep -E "WARNING|ERROR|CRITICAL" $T/log | sed 's/solarwidpy/solarwindpy/' | perl -ne 'print "$1\n" if /solarwindpy[\/.](core|fitfunctions|plotting|instabilities|solar_activity|tools)/' | sort | uniq -c`.
  Measured in the Documentation CI run on PR #445: core 32, fitfunctions 31, plotting 36,
  instabilities 14, solar_activity 9, tools 0.

##### source-core

OWNS: solarwindpy/core/, tests/test_source_core_defects.py

Delete the commented-out `AlfvenicTurbulenceDAmicis` class at `alfvenic_turbulence.py:447-801`.
Do not touch `Plasma.lnlambda`'s `29.9`.

- commented lines in that range: 355 — `sed -n 450,804p solarwindpy/core/alfvenic_turbulence.py | grep -cE "^\s*#"`
- comment lines in core: 381 — `grep -rhcE "^\s*# " solarwindpy/core | paste -sd+ - | bc`

##### source-fitfunctions

OWNS: solarwindpy/fitfunctions/, conftest.py, docs/source/fitfunctions_architecture.md, tests/test_source_fitfunctions_defects.py

`docs/source/fitfunctions_architecture.md` is never built and names classes the code lacks
(`ExponentialPlusCSin`, `Parabola`, `MaxwellBoltzmann`); its line 132 calls the loss hardcoded
while `make_fit` passes `loss` through. The author's decision: move what is still true into the
`solarwindpy.fitfunctions` package docstring, where the nitpicky build checks it, then delete
the file. Report each claim you dropped as false, with the code that contradicts it.

`GaussianPlusHeavySide` never fits `x0` (the Heaviside term has zero gradient, so `curve_fit`
returns `p0`'s `x0`); its doctest is strict xfail in the root `conftest.py`. A fix is in your
files; whether a different fitting method is acceptable is a methodology call to report.

##### source-plotting

OWNS: solarwindpy/plotting/, tests/test_source_plotting_defects.py

`labels.available()` and its deprecated alias `labels.available_labels()` are covered by
`tests/test_available.py`, which you do not own; keep both names working.

##### source-misc

OWNS: solarwindpy/instabilities/, solarwindpy/solar_activity/, solarwindpy/tools/, solarwindpy/scripts/, solarwindpy/__init__.py, solarwindpy/reproducibility.py, solarwindpy/README.md, docs/source/solarwindpy.bib, tests/test_source_misc_defects.py

`docs/source/solarwindpy.bib` is 0 bytes, so the `Verscharen2016a` citations in
`instabilities` docstrings cannot resolve; fill it from the DOIs the docstrings cite.
Untrack `solarwindpy/solar_activity/sunspot_number/.DS_Store`. Do not fix the two
pilot-found `solar_activity` defects (`base.py:210`, `plot_on_colorbar`): `solar-activity-root`
records them as strict xfails in this same run, and a concurrent fix would flip those red at
merge. They are follow-on work once both pull requests land.

### W6, retirement

#### retire-paper

OWNS: paper/

Remove `paper/` (4 tracked files: `git ls-files paper | wc -l`). The program plan also names
`draft-joss-paper.yml`; no tracked file by that name exists (`git ls-files | grep -i joss`).

#### retire-scripts

OWNS: scripts/analyze_imports.py, scripts/analyze_imports_fixed.py, scripts/analyze_imports_simple.py, scripts/archived/, scripts/docstring_baseline_analysis.py, scripts/test_dynamic_imports.py, scripts/update_pr_references.py, scripts/validate_docstrings.py, scripts/validate_physics_compliance.sh

Each has zero inbound references:
`git grep -l "<basename>" -- . ':!docs/dispatches' ':!plans'` returns only the file itself.
`scripts/docstring_coverage.py` also has none but is W5's measurement tool; it stays.

#### retire-reports

OWNS: docs/DEPLOYMENT_STATUS.md, docs/READTHEDOCS_SETUP.md, docs/BUILD_FAILURE_RESOLUTION.md, docs/VALIDATION_REPORT.md, docs/README.md, docs/transition-guide-doc-validation.md, coverage-monitor-fix.md, PYTHON-310-MIGRATION-NOTES.md, RELEASE_NOTES_PYTHON_310.md, baseline-coverage.json, pre-commit-config.yaml.old, fix_d205_docstrings.py, create_conda_env.sh, .gitignore

Candidates, not verdicts. Each has no inbound link by the same `git grep` rule. For each,
state what event it recorded and whether that event is over; remove only those that are, and
report the rest as undecided. `docs/transition-guide-doc-validation.md` documents the
standalone doctest runner removed in `93337e07`; `docs/READTHEDOCS_SETUP.md` describes a
`.readthedocs.yaml` (Python 3.11, requirements files) that no longer exists and links the
deleted `docs/TEMPLATE_SYSTEM.md`. `docs/VALIDATION_REPORT.md` and
`docs/BUILD_FAILURE_RESOLUTION.md` describe the sphinx-apidoc tree that PR #445 removed.
`docs/README.md:18,32-35` describes that tree and `add_no_index.py`; the file is otherwise a
live index, so remove only the dead passage, or report it undecided. In `.gitignore`, only the
`docs/source/api/` line is yours: nothing generates that directory now. Dropping it retires the
`api/` removal in `docs/Makefile`'s `clean` target, which is outside your paths; report that as a
follow-up. The program plan's "five one-time reports,
628 lines" matches no exact subset here; re-derive rather than aim at it.

---

## Not partitioned (no plan verdict; author decides)

`tests/solar_activity/lisird/` (15 introspection-only asserts, `lisird.py` at 33.3%),
`tests/solar_activity/icme/`, `tests/plotting/labels/` (keep, untouched, per the pilot),
`tests/plotting/test_hist2d_*.py` and `tests/plotting/test_histograms.py` (rebuilt by PR #437),
`tests/solar_activity/sunspot_number/` (rebuilt by PR #436), `tests/test_contracts_class.py`,
`tests/test_contracts_dataframe.py`, `tests/test_hook_integration.py`,
`tests/test_issue_titles.py`, `tests/test_declared_versions.py`.
The section prose of `docs/source/api_reference.rst` (omits hinge, heaviside, composite, ICME):
the author has chosen to drop it; the owner of that change is not yet assigned.

## Held outside phase 4

- The planning scripts named under Reserved.
