<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# Batch: test-quality fixes

author_signoff: none

owner: /Users/balterma/observatories/code/SolarWindPy

The instruction the author pastes after `/batch`. Findings and evidence:
`docs/dispatches/findings-test-quality-review-2026-10-02.md`. Test standard:
`.claude/docs/TEST_PATTERNS.md`.

## Governance

**Governing Property.** Every passing test in SolarWindPy means a behavior the package owes
its users holds; every behavior the package owes has a test that would fail if it broke; and
no test fails when the package changes correctly.

**Seam.** A unit decides test structure, fixtures, and how a finding is fixed inside its own
files. Physics correctness stays with the author: a unit that cannot derive or cite an
expected value reports that instead of asserting what the code returns. A defect found
outside a unit's files becomes a strict xfail naming what retires it.

**Approved by the author:** the listed test removals, the dev-extra tool removals, the
`CLAUDE.md` coverage figure, and the `Vector.latitude`/`colatitude` swap.

## Every unit

- Runs its positive control and reports the command and output: each new or repaired test is
  shown failing on a deliberately broken input, then passing.
- Every test it writes or touches carries an `ON FAILURE` line.
- Keeps both suites green: `conda run -n solarwindpy pytest -q` → 0 failed.
- Builds the docs as CI does (warnings are errors) whenever it edits a docstring, and shows
  0 warnings: CI's documentation build failed on PR #491 when no unit ran it.
- Commits from its worktree with plain `git commit -F <msgfile> -- <paths written out individually>`
  (the pre-commit hooks enter the solarwindpy env themselves), explicit-path staging, never `--no-verify`, a conventional subject, and the line
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; pushes its branch, opens a pull
  request, and does not merge.
- Pushes only with an explicit refspec, `git push -u origin HEAD:refs/heads/tq-fix/<unit>`.
  The author's git sets `push.default=upstream`, so a branch created from `origin/master`
  tracks master and a plain push lands on master unreviewed.

Baselines in brackets are collected test counts from
`conda run -n solarwindpy pytest --collect-only -q <files>`; per-file pass counts are in
`tmp/test-quality-review/per_file_baseline.txt`.

## Units

### hook-and-alias-tests

OWNS: tests/test_hook_integration.py, tests/test_import_aliases.py, .claude/hooks/tests/

Delete the 5 cannot-fail tests, the 5 shell-script substring checks, the 3 file-exists checks,
and the `CLAUDE.md`-coupled `test_coverage_requirement_in_pre_commit`. Move the 6 hook-behaviour
tests to `.claude/hooks/tests/`. Replace `tests/test_import_aliases.py` with ruff `ICN` rules
only if the rule set reproduces the check; otherwise keep it and report. [20 + 2]

### plasma-physics-cases

OWNS: tests/core/test_plasma.py

Add a low dv/w hand case for `Plasma.nuc`, expected values computed in the test from
Hernández & Marsch (1985), Eqs. 18 and 23 (cited in the `nuc` docstring). Add cases for
`sound_speed`/`cs` from cs = sqrt(gamma p / rho), `heat_flux` from its docstring formula, and
the multi-species ordering in `specific_entropy` and `estimate_electrons`. `Wk` is defined, not
derived: W_K,s = ½ ρ_s v_s³ per species, with v_s the species speed; no citation is needed.
Add hand cases for one species and for a species sum.

Author decisions:

- A species sum (`"a+p1"`) is a partial sum: a NaN row in one species leaves the other
  species' contribution, it does not make the sum NaN.
- Since `Vector.project` returns NaN on rows missing from either vector, add a hand case
  where a missing `b` row gives NaN in `heat_flux` and `vdf_ratio`.

Control: the coefficient change 2.0 → 3.0 in `nuc` now fails a test. [245]

### quantities-and-vector

OWNS: tests/core/test_quantities.py, solarwindpy/core/vector.py, solarwindpy/core/tensor.py, solarwindpy/plotting/labels/base.py, tests/plotting/labels/test_labels_base.py, CHANGELOG.md

Swap `Vector.latitude` and `colatitude` in `solarwindpy/core/vector.py` so latitude is
`arctan2(z, rho)` and colatitude is `arctan2(rho, z)`; record the fix in `CHANGELOG.md`. Add hand cases: (0, 0, 1) has latitude 90 and
colatitude 0, (1, 0, 0) has latitude 0 and colatitude 90; `Tensor.magnitude`; the
`project`/`cos_theta` survivors. Control: the unswapped code fails the new cases. [83]

Author decisions after the pilot's first report:

- `Tensor.magnitude` is the scalar magnitude of a thermal speed, which combines through the
  temperatures: sqrt((par² + 2 per²) / 3). Fix `tensor.py` (it raises on every Tensor the
  package builds) and replace the trace-form xfail with a passing hand case.
- `project` and `cos_theta` return NaN for a row present in only one of the two vectors.
- In `_trans_component` (`plotting/labels/base.py`), `lat` maps to λ and `colat` to θ.

### icme-tests

OWNS: tests/solar_activity/icme/test_icmecat.py, tests/solar_activity/icme/conftest.py, tests/solar_activity/icme/test_icmecat_smoke.py, tests/solar_activity/icme/test_icmecat_integration.py

Replace the process-wide `pandas.read_csv` patch with a URL constant pointed at a local file;
switch to `default_rng`; fix the vacuous tests; remove the docstring-text tests.
[42 + 17 + 8; the 8 integration tests are skipped opt-in]

### sidc-docstring

OWNS: tests/solar_activity/sunspot_number/test_sidc.py

Make the module docstring state the `no_download` fixture's `SIDCLoader.download_data` guard, or
move the guard to the network boundary. [33]

### fitfunction-small-files

OWNS: tests/fitfunctions/test_lines.py, tests/fitfunctions/test_exponentials.py, tests/fitfunctions/test_power_laws.py

Fix the vacuous tests (including `test_line_vertical_like_data_fails`), add `ON FAILURE` lines,
switch to `default_rng`. [27 + 31 + 35]

### abundances-tests

OWNS: tests/core/test_abundances.py

Replace the 40 existence-only tests with value assertions or remove them; fix the vacuous
float64 test. [169]

### hist2d-tests

OWNS: tests/plotting/test_hist2d_pandas_compat.py, tests/plotting/test_hist2d_plotting.py

Fix the vacuous column-normalize test and the existence-only tests; pin xlim/ylim inclusivity
with a limit placed exactly on a vertex (kills the surviving `x0 < x` mutant). [25 + 126]

### docstring-examples

OWNS: solarwindpy/core/plasma.py, solarwindpy/tools/__init__.py, solarwindpy/fitfunctions/core.py, solarwindpy/core/abundances.py, solarwindpy/instabilities/beta_ani.py, solarwindpy/solar_activity/icme/__init__.py, solarwindpy/solar_activity/icme/icmecat.py

Docstrings and their examples only: correct the `Plasma` docstring (`beta` returns a DataFrame;
species order), the `swap_protons` example, seed the inherited `FitFunction.__init__` example,
keep ICMECAT examples off the network, replace the dead Google Drive link, and drop `+SKIP`
wherever the example can run. Control: `pytest --doctest-modules solarwindpy -q` skip count
falls from 36. [doctests: 24 passed, 36 skipped]

Review follow-up (author decision): the four `plasma.py` examples that repeat the same
`Plasma` setup (`epoch`, `set_log_plasma_stats`, `set_spacecraft`, `set_auxiliary_data`) use a
shared `plasma` from `doctest_namespace`, provided by the root `conftest.py` that
`documented-examples` adds. This unit makes that switch after `documented-examples` merges,
and each of the four docstrings says where `plasma` comes from.

### documented-examples

OWNS: README.rst, docs/source/tutorial/quickstart.rst, docs/source/installation.rst, conftest.py, .github/workflows/doctest_validation.yml

Run the rst examples under Sybil in CI and give each an asserted expected output. Control: an
example with a wrong expected output fails the run. [31 Sybil examples pass, none assert]

### abundances-2021-only

OWNS: solarwindpy/core/abundances.py, solarwindpy/core/data/asplund2009.csv, solarwindpy/core/data/asplund2021.csv, tests/core/test_abundances.py, CHANGELOG.md

Runs after `docstring-examples` and `abundances-tests` merge. Author decisions: delete
`asplund2009.csv`; remove the `year` parameter and the `.year` property so
`ReferenceAbundances()` always loads Asplund et al. (2021), Table 2
(doi:10.1051/0004-6361/202140445); restore the CI_chondrites Ab values the CSV leaves blank,
Ne −1.12, Ar −0.50, Kr −2.27, Xe −1.95 (each ± 0.18, as printed in Table 2). Every other row
of the 2021 CSV already matches Table 2. Drop the 2009 tests, retire the noble-gas strict
xfails, record the removal and the fix in `CHANGELOG.md`. Add a test asserting that the 15
Photosphere cells Table 2 leaves blank (unavailable) stay NaN: As, Se, Br, Cd, Sb, Te, I, Cs,
Ta, Re, Ir, Pt, Hg, Bi, U. Controls: blanking any one of the four restored cells fails a test,
and filling any one of the 15 blank cells fails a test. Also make `get_element("Fe")` and
`get_element(26)` return Series with the same name, retiring the name-quirk xfail.

### dev-extras-and-coverage-figure

OWNS: pyproject.toml, CLAUDE.md, .claude/docs/ATTRIBUTION.md, .pre-commit-config.yaml, .claude/docs/DEVELOPMENT.md, .claude/docs/MAINTENANCE.md, .github/PULL_REQUEST_TEMPLATE.md, .gitmessage

Runs after `hook-and-alias-tests` merges. Remove grimp, pydeps, radon, wily, deptry,
pytest-deadfixtures, and interrogate from the `dev` extra; set the coverage figure in
`CLAUDE.md` from a fresh measurement without restating the hook's threshold number.

Author decision: retire `.claude/docs/ATTRIBUTION.md`. The `Co-Authored-By` trailer is the
attribution for AI-written commits; there is no "Generated with Claude Code" commit line.
Delete the file and the echo-only `attribution-reminder` hook in `.pre-commit-config.yaml`.
`CLAUDE.md` keeps the rule in its Conventions list, rewritten: AI-written commits carry the
`Co-Authored-By` trailer; external code records URL, license, and modifications in a comment;
when provenance is unclear, reimplement. Drop `ATTRIBUTION.md` from the "Further
documentation" list, and repoint or remove the references in `DEVELOPMENT.md`,
`MAINTENANCE.md`, the PR template, and `.gitmessage`. Control: `git grep -n ATTRIBUTION.md`
outside `docs/dispatches/` returns nothing.

## Follow-up units

Both run after every unit above has merged; their files are disjoint. `plasma-code-fixes`
also waits for `examples-and-logging-cleanup`, since both change `plasma.py`. Each retires the strict
xfails its fixes resolve, with the three-run demonstration from TEST_PATTERNS.md.

### examples-and-logging-cleanup

OWNS: solarwindpy/examples.py (new), solarwindpy/__init__.py, solarwindpy/core/data/ (new example CSVs only), tests/data/, tests/core/test_base.py, tests/test_examples.py (new), conftest.py, solarwindpy/core/plasma.py, CHANGELOG.md

Replaces the re-apply of 6ed14f84 (the conftest-fixture approach). Author decisions:

- Docstring examples get their Plasma from one public loader, `swp.examples.load_plasma()`,
  which builds a full Plasma from the suite's three-row test data: plasma, epoch, and
  spacecraft, plus auxiliary data if a CSV holds it (none does today). Move
  `tests/data/{epoch,plasma,spacecraft}.csv` into `solarwindpy/core/data/` (already packaged)
  as `example_*.csv` with `git mv`, keeping their bytes. The loader holds the one copy of the
  `a|b|c` → `(M, C, S)` column parsing; `tests/core/test_base.py` uses the loader instead of
  its own. The examples in `Plasma.epoch`, `set_spacecraft` and `set_auxiliary_data` start
  with `>>> plasma = swp.examples.load_plasma()` and show this data's real values. Remove the
  root `conftest.py` doctest fixture (`_doctest_plasma`, `_small_plasma`), which then has no
  users.
- Remove the unused plasma-statistics logging to simplify the code: the `log_plasma_stats`
  argument, `log_plasma_at_init`, `set_log_plasma_stats`, the pass-throughs at the class
  constructor and the species-subset method, and the statistics in `_log_object_at_load`
  (this also removes the pandas-3 `applymap` crash). Keep the INFO message "No %s data passed
  to %s" when an optional input is None. Record the removal in `CHANGELOG.md`.

Controls: an installed-style check that the loader finds its CSVs through the package (not a
path into `tests/`); a test that `load_plasma()` returns the documented species, row count and
spacecraft columns, failing on a broken CSV; `Plasma(..., log_plasma_stats=True)` raises
`TypeError`; the "No … data passed" message is still logged (caplog).

### plasma-code-fixes

OWNS: solarwindpy/core/plasma.py, tests/core/test_plasma.py

Author decisions:

- `heat_flux` keeps its formula, ρ(v³ + 3/2 v w∥²): it is the along-field (parallel-parallel)
  part of the energy flux, not the total energy flux along the field. The docstring and its
  label say so precisely. The parallel-only thermal speed has been deliberate since 2019.
- A species sum with no species present is NaN, not 0, while a sum with some species present
  stays a partial sum: `heat_flux("a+p1")` and `kinetic_energy_flux("a+p1")` use
  `min_count=1`. Add the `Wk` all-missing row case beside the existing partial-sum case.
- `vdf_ratio` returns NaN where the projection is NaN (`skipna=False`).
- `estimate_electrons` sets T_e = T_p, as its docstring states: w_e² = (m_p/m_e) w_p², not
  the current (n_p/n_e)(m_p/m_e) w_p².
- (The pandas-3 `applymap` crash is removed with the logging in
  `examples-and-logging-cleanup`, which runs first.)

### small-code-fixes

OWNS: solarwindpy/solar_activity/icme/icmecat.py, tests/solar_activity/icme/test_icmecat.py, solarwindpy/plotting/hist2d.py, tests/plotting/test_hist2d_plotting.py, solarwindpy/fitfunctions/lines.py, solarwindpy/fitfunctions/core.py, tests/fitfunctions/test_lines.py, tests/fitfunctions/test_exponentials.py, solarwindpy/plotting/tools.py, .claude/docs/TEST_PATTERNS.md, .claude/README.md, .claude/WORKFLOW_TEMPLATE.md, .claude/docs/DEVELOPMENT.md, .claude/docs/MAINTENANCE.md, .github/PULL_REQUEST_TEMPLATE.md, .gitmessage

Author decisions:

- ICMECAT cache: save and read the cached copy as CSV (the format the catalog downloads in),
  not parquet, so caching needs no undeclared dependency; retire the two cache xfails.
- `plot_edges`: a vertex exactly on an `xlim`/`ylim` limit is kept. State it in the docstring
  and add the vertex-on-limit test that kills the `x0 < x` mutant.
- `Line.p0` checks for repeated x before dividing (no divide-by-zero warning);
  `LineXintercept.p0`'s docstring says it returns `[m, x0]`.
- `FitFunction.rsq` does not divide 0/0 on a single point or constant data; decide the
  returned value from its docstring, or report it if the docstring does not say.
- The `plotting/tools.py` `save` example writes into a temporary directory, not the current
  directory, and drops `+SKIP`.
- TEST_PATTERNS.md tolerance rule, replacing "values published to N significant digits":
  when the package stores a published value as printed, compare exactly; when it computes a
  value a source prints to d decimal places, allow half the last printed digit
  (`abs = 0.5 × 10^-d`, `rel = 0`). This holds on linear and logarithmic scales alike.
- Attribution leftovers after ATTRIBUTION.md's retirement (author-approved): remove the
  "Generated with Claude Code" commit instruction from `.claude/README.md` and
  `.claude/WORKFLOW_TEMPLATE.md` (including its "Commit with Attribution" step); where docs
  show the trailer, describe it as "a `Co-Authored-By: Claude …` trailer" rather than one exact
  string; remove the "Annual Attribution Audit" procedure in `MAINTENANCE.md` that writes to
  `docs/audits/attribution-audit-YYYY.md`. Control: `git grep -n "Generated with Claude Code"`
  outside `docs/dispatches/` returns nothing.
- The PR template and `.gitmessage` say "coverage ≥95%", which is neither the hook's floor
  nor a promise; say "coverage at or above the pre-commit hook's floor" instead.

### p0-contract

OWNS: solarwindpy/fitfunctions/ (all modules), tests/fitfunctions/

Runs after `small-code-fixes` merges. Author decision, after an evaluation in which a NaN
left in a guess failed every fit and a base-class NaN fill matched `None` exactly while
hiding estimator bugs: a fit function's `p0` returns `None` when it cannot make a guess, and
the fit starts from the feasible default (`core.py`'s existing `None` path). State that
contract once, in the base class's `p0` docstring. The base class rejects any guess holding
NaN or infinity with a `ValueError` naming the class and the parameter, instead of scipy's
"Initial guess is outside of provided bounds". Bring every subclass onto the contract:
`Heaviside`'s NaN substitutions, the unchecked estimates in `exponentials`, `power_laws`,
`gaussians` and `hinge`, and `composite`'s empty-data error; replace `assert
self.sufficient_data` (removed under `python -O`) with an explicit check. Controls: a guess
with NaN raises the new error; a subclass returning `None` still fits.

Author decisions after the first review:

- A zero-width Gaussian is one narrower than the data can resolve: when the estimated width
  is under half the smallest spacing between distinct x values, `p0` returns `None`.
- When a hinge class's `p0` is `None`, its fit starts from the author's point (vs, As, x1,
  m2) = (433, 4.12, 250, small), translated into each class's parameters, instead of the
  all-ones default; "small" is 1% of the rising slope m1 = 4.12 / (433 − 250). `HingeMax`
  has a different shape and will get its own point: until then its fallback raises
  `NotImplementedError`.
- `GaussianLn.p0` estimates in ln x: m and s are the y-weighted mean and standard deviation
  of ln x, and A is the peak y (A is not logged in the model).

### tolerance-helpers

OWNS: tests/ (all files), .claude/docs/TEST_PATTERNS.md

Runs after `plasma-code-fixes` and `p0-contract` merge, before `mutation-recheck`. Author
decision: one test helper module is the tolerance rule, a named function per comparison
kind (`exact`, `printed(x, decimals=d)`, `noise_free`, and the 4-error-bar check for noisy
fits), each with its reason in its docstring; `TEST_PATTERNS.md` points to the module instead
of restating numbers. Migrate the hand-written tolerances (304 `rel=`/`abs=`/`rtol=`/`atol=`
keywords across 33 test files), promoting `test_abundances.py`'s `exact()`. Add a test that
fails when a test file writes `rel=`, `abs=`, `rtol=` or `atol=` outside the helper module.
Line comments keep only the source of an expected value, never a restated rule. Controls: a
hand-written tolerance added to a test file fails the enforcing test; each helper fails on a
value shifted past its tolerance.

Also folded into `tolerance-helpers` (from PR #490's report): a test for
`estimate_electrons(inplace=True)`, and the one `tests/core/test_plasma.py` test missing its
`ON FAILURE` line.

Author decision (2026-10-05): the `heat_flux` plot label stays `q` (`Q` reads as charge); no label change.

### loader-examples

OWNS: solarwindpy/core/ions.py, solarwindpy/core/spacecraft.py, solarwindpy/core/plasma.py (the `Plasma` class docstring only)

Author decision: the `Plasma` class, `Ion` and `Spacecraft` docstring examples load their
data with `swp.examples.load_plasma()` (`plasma`, `plasma.p1`, `plasma.spacecraft`) instead of
building random or hand-typed frames, so the example CSVs are the single source. Docstrings
only. Runs alongside `tolerance-helpers` (disjoint files).

### scalar-w-nan

OWNS: solarwindpy/core/plasma.py, tests/core/test_plasma.py, CHANGELOG.md

Runs after `loader-examples` and `tolerance-helpers` merge (both touch these files). Author
decision: `Plasma.set_data` builds each species' scalar thermal speed from its parallel and
perpendicular parts with a NaN-skipping sum, so a time with both parts missing gets 0. It is
NaN instead, matching the empty-sum rule (`min_count=1` or `skipna=False` as fits the formula).
Control: a row with both parts missing gives NaN; the old code gives 0. CHANGELOG entry.

Author decisions after PR #494's review (the missing-data rule, two levels):

- Within one species, any missing component makes that species' value NaN: a time with
  only w∥ or only w⊥ has no scalar thermal speed (one component alone is unphysical).
- Across species, a total is the sum of the species present at that time and NaN only
  when none is: protons without alphas still give a valid total temperature or pressure.
  Thermal speeds do not add across species (`thermal_speed("a+p1")` already raises);
  only temperatures and pressures do.
- Apply the rule to every species or component sum in `plasma.py`: `thermal_speed`, `pth`
  and `temperature` for one species (a missing row is 0 today); `pdynamic`'s sum over
  components (within-species rule); `velocity`, `afsq` and `estimate_electrons` (across-species
  rule). A species with no velocity at a time also leaves the density weights in `velocity`
  and `estimate_electrons`.
- Document the rule once, with an ASCII diagram of the two levels for temperature and
  pressure, and point the `temperature` and `pth` docstrings to it.

Author decisions after the second #494 review:

- A species' moments stand or fall together: if any of its density, velocity components or
  thermal-speed components is missing at a time, every measurement of that species at that
  time is invalid. `Plasma` masks the species to NaN at that time when the data are set and
  logs how many times it masked. A density without a velocity cannot occur afterwards.
- A pair quantity needs both species: `nuc`'s combined thermal speed and mass-density ratio
  and `pdynamic`'s reduced mass are NaN when either species is missing (`skipna=False`).
- `number_density` and `mass_density` totals are NaN when no species is present (`min_count=1`).
- `afsq` and `caani` docstrings state how the pressure enters; `afsq` may return to
  `pth` since species masking makes the two forms equal.

### p0-simplify

OWNS: solarwindpy/fitfunctions/ (all modules, CONTRIBUTING.md), tests/fitfunctions/, CLAUDE.md, CHANGELOG.md

Runs after `tolerance-helpers` merges. Author decision: one concept, not two. A hinge class's
`p0` returns its documented reference start itself (logging that the data gave no estimate)
instead of returning None for an overridden `fallback_p0`; `HingeMax.p0` raises
`NotImplementedError` in that branch. `fallback_p0` becomes private `_fallback_p0`, used only
by the fitter for the generic in-bounds start when `p0` is None (no subclass overrides it).
Update the base `p0` contract, CONTRIBUTING.md and the CHANGELOG. Also fix the stale CLAUDE.md
pointer to a constructed example at `solarwindpy/core/plasma.py:102` (point to
`swp.examples.load_plasma()`). Controls: each hinge class's impossible-estimate input gives
the reference start from `p0` with the warning logged; `HingeMax` raises; a non-hinge class
returning None still fits from the generic start.

Author decision after PR #496's review: the six hinge classes (`HingeSaturation`, `TwoLine`,
`Saturation`, `HingeMin`, `HingeMax`, `HingeAtPoint`) inherit from one `Hinge(FitFunction)`
parent, not exported, that holds the reference hinge, the estimate-or-reference control flow
in `p0`, and the shared docstring text (through docstring inheritance). Each child writes
only its model, its estimate, and its parameter translation; `HingeMax` shares what it can
with `HingeMin`. The module-level `_author_start` and the five copied docstring paragraphs go.

Author decision after the second #496 review: fix the class docstrings of every `FitFunction`
subclass losing their Parameters section through docstring inheritance, in this PR.

Author decisions after the third #496 review:

- Remove `Hinge.__init_subclass__` and the per-class `p0` it builds. Each hinge class
  describes how its `p0` estimates in its class docstring (which docstring inheritance
  merges); `p0` is one inherited `Hinge` property with a generic docstring that points to
  the class description. No subclass defines `p0`.
- The reference-hinge numbers (433, 4.12, 250) are written once, in the `Hinge` class Notes,
  and a test fails if those numbers and the stored constants disagree.
- `HingeMax` with no estimate raises its `NotImplementedError` without logging the
  "data gave no estimate" warning first; the other hinge classes still warn, then return
  the reference start.

### warning-fixes

OWNS: solarwindpy/core/alfvenic_turbulence.py, solarwindpy/fitfunctions/power_laws.py, solarwindpy/fitfunctions/gaussians.py, solarwindpy/fitfunctions/hinge.py, solarwindpy/instabilities/verscharen2016.py, and their test files

Runs after `p0-simplify` merges. Author decisions: `logger.warn` becomes `logger.warning`;
`PowerLawOffCenter` bounds x0 below the smallest x (the model is defined only for x > x0);
`GaussianLn` raises `ValueError` when built with any x ≤ 0 (ln x is undefined; no absolute
value); the verscharen2016 table legend fills cells for unplotted instabilities with its
blank rectangle so the table keeps its layout (the table form is intentional); the hinge
`p0` estimates check before dividing (the divide-by-zero rule). Control for each: the warning
it removes is gone from `pytest -rw`, and a test fails on the old behavior.

Author decision after PR #499's review: fold these fixes into #499. Replace the private
`scipy.optimize._lsq` `prepare_bounds` import with public NumPy broadcasting of the bounds.
`PowerLawOffCenter` starts x0 below the smallest used x, and a caller bound that leaves x0 no
room below the data raises a clear `ValueError`. `GaussianLn` checks for used x ≤ 0 wherever
the used observations are set (construction and `set_fit_obs`), not only at construction.
`GaussianLn.TeX_function` returns the formula with its minus sign, with the dead first
assignment and the test asserting the wrong string fixed. `HingeSaturation._estimate`
treats a rising region with fewer than two distinct x as no estimate (the existing
repeated-x rule), so `p0` returns the reference start.

### hist2d-no-clabel

OWNS: solarwindpy/plotting/hist2d.py, tests/plotting/

Runs after `approx-default` (PR #495) merges, since both edit
`tests/plotting/test_hist2d_plotting.py`. Author decision: remove contour labeling. Drop `label_levels`, `clabel_kwargs` and
`skip_max_clbl` and the labels in the return values from both contour methods, with no
deprecation; this also removes matplotlib 3.11's filled-contour `clabel` deprecation warning.

## Long-running units

### mutation-recheck

OWNS: tmp/test-quality-review/mutmut/

Finish `tmp/test-quality-review/recheck_survivors.sh` for the remaining plasma survivors and all
of `hist2d.py`; re-baseline mutation scores after the other units land.

### linkcheck

OWNS: tmp/test-quality-review/linkcheck/

Re-run Sphinx linkcheck (network required) after the `docstring-examples` unit lands.

### plotting-and-docstring-cleanup

OWNS: solarwindpy/plotting/spiral.py, solarwindpy/plotting/hist2d.py, solarwindpy/fitfunctions/core.py, solarwindpy/fitfunctions/hinge.py, tests/plotting/test_spiral.py, tests/fitfunctions/, tests/test_tolerance_rule.py, solarwindpy/fitfunctions/power_laws.py, solarwindpy/fitfunctions/gaussians.py

Runs after PRs #498 and #499 merge (both touch these files). Author decisions: remove
contour labelling from `SpiralPlot2D` as #498 did for `Hist2D` (parameters, `clabel` code,
labels in return values, docstring examples), with no deprecation; replace the literal
`{self.plot_edges!s}` placeholder in the `hist2d.py` docstring with a working reference; in
merged fit-function class docstrings, put Attributes in numpydoc order, before See Also; give
`Hinge` a hinge example (or none) in place of the Gaussian example it inherits from
`FitFunction`. Also from PR #495's review: the bare-approx scanner in
`tests/test_tolerance_rule.py` follows aliased imports (`from pytest import approx as ap`,
`import pytest as pt`), and its docstring states that `approx(x, **tol)` is flagged
(fail-closed). Add `tests/test_tolerance_rule.py` to OWNS.
Also from PR #499's last review: `PowerLawOffCenter.make_fit` rejects a caller `p0` whose x0
is below the caller's lower bound with the same clear error it gives above the upper bound;
`initial_guess_info` reports the start the fit actually used after clipping; and
`GaussianLn.TeX_function` puts a space between `\cdot` and `\exp`.

`HingeMax` keeps raising `NotImplementedError` in its no-estimate branch: the author does not
yet have a good initial guess for it. The `hingemax-point` step stays parked, not blocking
the track's close.

## Survivor units

Author decision after the 2026-10-07 mutation re-measurement (findings, `### Mutation`): kill
the survivors that are real behaviour gaps with two test-only units, then close the track
with the rest named in the findings and a GitHub issue. Not targeted: survivors that cannot
be killed (behaviour-identical mutants such as dropped `sort=True` on sorted data, library
defaults, unit factors of 1.0), plotting appearance (figure size, line style, ticks), error
and log message wording, the two mutmut-excluded docstring functions, `hist2d` data paths and
the remaining `plasma.py` physics (these need a mutant-by-mutant look first). A defect a new
test exposes becomes a strict xfail naming what retires it; package code is not changed.
Survivor list: `tmp/test-quality-review/mutants_survivors.csv`, minus the rows
`tmp/test-quality-review/mutants_recheck.csv` marks killed.

### plasma-io-electrons

OWNS: tests/core/test_plasma_io.py, tests/core/test_plasma.py

Kill the behaviour survivors in `Plasma.save` and `Plasma.load_from_file` (a full save-then-load
round trip with spacecraft and auxiliary data, the default HDF5 keys, `start`/`stop` slicing,
the modifier-function checks) and in `Plasma.estimate_electrons` (the species guards: electrons
already present, `p` versus `p1`).

### fit-and-sidc-gaps

OWNS: tests/fitfunctions/test_core.py, tests/solar_activity/sunspot_number/test_sidc.py

Kill the behaviour survivors in `FitFunction._run_least_squares` (the correlated-sigma path:
the covariance-shape check and the Cholesky factor's orientation), `FitFunction.set_fit_obs`,
`FitFunction._calc_popt_pcov_psigma_chisq`, and in `SIDC.cut_spec_by_ssn_band`,
`SIDC.run_normalization` and `SIDC.interpolate_data`. `SIDCLoader.download_data` stays
offline (the existing `no_download` guard).

### survivor-defect-fixes

OWNS: solarwindpy/fitfunctions/core.py, solarwindpy/solar_activity/sunspot_number/sidc.py, tests/fitfunctions/test_core.py, tests/solar_activity/sunspot_number/test_sidc.py

Runs after PR #504 merges (it holds the two strict xfails). Author decisions: (1) a 2-d
covariance matrix passed as `weights` works as `FitFunction` documents (correlated errors:
`_clean_raw_obs` accepts it, `set_fit_obs` keeps its rows and columns, and the residuals are
whitened with its Cholesky factor), retiring the GLS xfail; (2) `SIDC.cut_spec_by_ssn_band`
re-raises a clear `KeyError` naming a column `interpolated` lacks, retiring that xfail, and its
dead band-overlap check is removed. `SIDC.run_normalization`'s column order stays unpromised.
CHANGELOG lines go in the PR body.

Author decision revised after PR #505 (2026-10-07): the author has never fit with correlated
errors, so `weights` is a 1-d array of 1-sigma uncertainties only. Revert #505's covariance
support; delete the unreachable covariance (Cholesky) branch in the fit; state in the
`weights` docstring that a 2-d array is refused; replace the GLS strict xfail with a test that
a 2-d `weights` raises `InvalidParameterError` with a clear message. Results for 1-d weights
and for no weights are unchanged. The `cut_spec_by_ssn_band` fixes stand.

Author decision (2026-10-07, from the survivor sort): `Plasma` keeps the caller's row order and
never sorts by time. Out-of-order timestamps flag a timestamp encoding error that the author's
upstream data cuts drop; sorting would hide it. Pin it with a test that out-of-order input keeps
its order (kills `Plasma.set_data` mutant 116).

### hist2d-projection-tests

OWNS: solarwindpy/plotting/hist2d.py, solarwindpy/plotting/hist1d.py, tests/plotting/test_hist2d_plotting.py, tests/plotting/test_hist1d.py

From the 2026-10-07 survivor sort (42 real gaps in `Hist2D.project_1d`,
`take_data_in_yrange_across_x` and `_prep_agg_for_plot`). Author decisions: label-only changes
to a projected histogram count as gaps; `_prep_agg_for_plot` defaults are tested only through
the public plotting path; `Hist1D` stores `clip` as a bool, as its base class does; a `z` with
exactly two distinct values is data, not counts (fix the stale comment); the log flag handed
to `take_data_in_yrange_across_x` callbacks is a strict bool; a zero-width range raises
`ValueError`, not `assert`.

### plasma-survivor-tests

OWNS: tests/core/test_plasma.py

Runs after the remaining `plasma.py` survivors are sorted. Known gaps: `nuc` refuses combined
species on either side (author confirmed; mutants 6, 8, 10, 11, 17); `nc` defaults to
`both_species=True` (mutant 1); `Plasma` keeps the input row order (`set_data` mutant 116).

Author decision revised (2026-10-07): when a `Plasma` is built from out-of-order timestamps it
logs a warning (how many rows, and where), then sorts the data by time; methods may assume
sorted data. This replaces the "never sort" decision above. `_species_weighted_mean` (added in
#494) stays, with a docstring line that it relies on species masking. Remove the dead comma
split in `Plasma._set_ions`; leave `build_alfvenic_turbulence`'s comma split unless shown dead.

Author correction (2026-10-07): `clip_data` clips the lower ("l") or upper ("u") tail on its own,
True clips both. Store `clip` as given in `Hist1D` and in the plotting base class (only None
becomes False); this reverses the earlier "store clip as a bool" decision and fixes Hist2D's
one-sided clipping, which the base class's `bool()` had broken.

Author decision (2026-10-07): duplicate timestamps also log a warning when a `Plasma` is built.

### projection-bin-edges

OWNS: solarwindpy/plotting/agg_plot.py, solarwindpy/plotting/hist2d.py, tests/plotting/test_hist2d_plotting.py, tests/plotting/test_agg_plot.py

Runs after PR #508 merges. Author decision: a 1-D projection of a 2-D histogram keeps the
parent's bins, including which edge each bin closes on, so a sample on a bin edge lands in the
same bin as in the parent and is never dropped. Retire #508's strict xfail
`test_integer_bin_projection_keeps_samples_on_bin_edges`.
Also from #508's review: reword `take_data_in_yrange_across_x`'s `Raises` docstring to say the
`ValueError` is for a `ranges_by_x` entry naming an x-bin the histogram does not have.
