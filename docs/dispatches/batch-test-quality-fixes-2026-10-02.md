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

Both run after every unit above has merged; their files are disjoint. Each retires the strict
xfails its fixes resolve, with the three-run demonstration from TEST_PATTERNS.md.

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
- Replace `DataFrame.applymap` (removed in pandas 3) in `_log_object_at_load`, with a test
  that `log_plasma_stats=True` no longer raises.

### small-code-fixes

OWNS: solarwindpy/solar_activity/icme/icmecat.py, tests/solar_activity/icme/test_icmecat.py, solarwindpy/plotting/hist2d.py, tests/plotting/test_hist2d_plotting.py, solarwindpy/fitfunctions/lines.py, solarwindpy/fitfunctions/core.py, tests/fitfunctions/test_lines.py, tests/fitfunctions/test_exponentials.py, solarwindpy/plotting/tools.py, .claude/docs/TEST_PATTERNS.md

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

## Long-running units

### mutation-recheck

OWNS: tmp/test-quality-review/mutmut/

Finish `tmp/test-quality-review/recheck_survivors.sh` for the remaining plasma survivors and all
of `hist2d.py`; re-baseline mutation scores after the other units land.

### linkcheck

OWNS: tmp/test-quality-review/linkcheck/

Re-run Sphinx linkcheck (network required) after the `docstring-examples` unit lands.
