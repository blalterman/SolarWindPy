<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# Findings: holistic test-quality review of SolarWindPy

author_signoff: none

owner: /Users/balterma/observatories/code/SolarWindPy

Produced by `docs/dispatches/dispatch-test-quality-review-2026-10-02.md`. Every number below
names the command or artifact that reproduces it. Artifacts live under the git-ignored
`tmp/test-quality-review/`; run commands from the repository root in the `solarwindpy` conda
env (`conda run -n solarwindpy ...`). The fix program is
`docs/dispatches/batch-test-quality-fixes-2026-10-02.md`.

## Author decisions recorded

- `Vector.latitude` and `Vector.colatitude` are swapped in `solarwindpy/core/vector.py`;
  the fix program corrects the source and adds hand-worked cases.
- Test removals, the dev-extra tool removals, and the `CLAUDE.md` coverage figure are approved.
- `Plasma.nuc` expectations derive from Hernández & Marsch (1985), Eqs. 18 and 23, already
  cited in its docstring. `sound_speed` derives from cs = sqrt(gamma p / rho). `heat_flux`
  derives from its docstring formula. `Wk` has no formula or citation in its docstring; its
  definition and source come from the author before its test is written.

## Baseline

- Suite: 2849 passed, 12 skipped, about 35 s (`tmp/test-quality-review/baseline_run.txt`).
  Three random-order seeds and a network-blocked run give the same result
  (`tmp/test-quality-review/suite_properties.sh`); the 12 skips are the opt-in network tests.
- Collected tests: 2861 (`pytest --collect-only -q`; under `conda run` the count is on the
  last non-blank line).
- Line coverage: 94% (7120 statements, 418 missed; `tmp/test-quality-review/coverage.json`).
  `CLAUDE.md` still states about 82%.
- Coverage contexts on Python 3.14 need `COVERAGE_CORE=ctrace`: the default `sysmon` core
  records 535 contexts for 2861 tests, `ctrace` records 2804
  (`tmp/test-quality-review/coverage_contexts.sqlite`).
- `ON FAILURE` lines: a plain recursive grep returns 889 because it reads 253 stale `.pyc`
  files; over `*.py` it is 636 occurrences. 1612 of 2861 tests carry one
  (`tmp/test-quality-review/tests.csv`). The remaining 1249 sit mostly in files not yet
  rebuilt: `test_abundances` (168), `test_alfvenic_turbulence` (156), `test_hinge` (90),
  `test_quantities` (79), the label tests (241), `test_composite` (56), the ICME tests (67),
  the contract tests (58).

## Tool trial

| Tool | Outcome | Reason |
|---|---|---|
| griffe | kept | public-API inventory (`contract_inventory.py`) |
| coverage contexts | kept | test-to-line map; needs `COVERAGE_CORE=ctrace` on 3.14 |
| mutmut | kept | sampled mutation testing; needs an isolated copy, a shim removing the editable-install finder, `--ignore=tests/test_import_aliases.py`, and the whole-file recheck |
| Sybil | kept | runs rst `code-block` examples the doctest glob ignores |
| pytest-randomly | kept | random test order |
| vulture | kept | at 100% confidence only |
| ruff PT/B | kept | 232 unittest-style asserts, 9 B018 useless expressions in tests, 33 B findings in the package |
| pytest --durations | kept | run-time profile |
| numpydoc validation | kept | flags docstrings that misstate signatures |
| Sphinx linkcheck | kept | long-running, needs network |
| ast-grep | dropped | pattern `mock.patch($$$)` matched 0 of 51 patch calls; stdlib `ast` scripts cover it |
| grimp | dropped | duplicates `lint-imports` |
| pydeps | dropped | a third import graph |
| pyreverse | dropped | class diagrams answer no test-quality question; trial installed `pylint`, which remains in the env undeclared |
| radon | dropped | no complexity number changed a disposition |
| wily | dropped | checks out old revisions in the target repo; safe only on a clone |
| deptry | dropped | 0 package findings |
| pytest-deadfixtures | dropped | INTERNALERROR on numpy parametrize values |
| interrogate | dropped | duplicates numpydoc |

## Contract inventory

942 public objects (`conda run -n solarwindpy python tmp/test-quality-review/contract_inventory.py`;
artifact `tmp/test-quality-review/contract_inventory.csv`, 51 rows naming `Plasma`).

## Test inventory

Every collected test classified by type, assertion, and expectation source:
`tmp/test-quality-review/tests.csv`, 2861 rows plus header, produced by
`tmp/test-quality-review/classify_tests.py`.

## Gaps: owed behavior no test catches

- `Plasma.nuc`: changing the Gaussian-term coefficient from 2.0 to 3.0 leaves all 28 nuc/nc
  tests passing. The fixture sets dv/w_ab between 8.6 and 11, where that term is effectively
  zero (`tmp/test-quality-review/nuc_regime.py`). A low-drift hand case is needed.
- Never executed by any test: `Plasma.sound_speed`/`cs`, `Plasma.Wk`, `Vector.lat`/`latitude`,
  `Tensor.magnitude` (coverage contexts).
- `Vector.latitude` and `colatitude` are swapped: `colatitude` computes
  `arctan2(z, rho)` (90 degrees for (0, 0, 1)), `latitude` computes `arctan2(rho, z)` (0).
  The only test re-derives the same formula.

### Mutation sample

Re-run with `bash tmp/test-quality-review/run_mutmut.sh <module>`; results in
`tmp/test-quality-review/mutmut/*/results.txt`, survivors in
`tmp/test-quality-review/mutants_survivors.csv`.

| Module | Killed | Survived | No tests | Score |
|---|---|---|---|---|
| plotting/hist2d.py | 896 | 488 | 0 | 0.65 |
| core/plasma.py | 1384 | 729 | 26 | 0.65 |
| core/ions.py | 62 | 10 | 0 | 0.86 |
| core/vector.py | 55 | 13 | 1 | 0.80 |
| fitfunctions/core.py | 397 | 131 | 0 | 0.75 |
| fitfunctions/lines.py | 9 | 1 | 0 | 0.90 |
| instabilities/beta_ani.py | 78 | 12 | 0 | 0.87 |
| sunspot_number/sidc.py | 496 | 186 | 0 | 0.73 |
| tools/__init__.py | 199 | 33 | 0 | 0.86 |

Survivor counts are upper bounds: mutmut credits code run in `setUpClass` only to the first
test of each class. Whole-file rechecks (`recheck_survivors.sh` →
`tmp/test-quality-review/mutants_recheck.csv`): every survivor held for ions, vector,
fitfunctions/core, lines, beta_ani, sidc, tools; for plasma, 499 of 729 rechecked and 11
flipped to killed (all in `Plasma.set_data` scalar thermal-speed coefficients). The remaining
plasma survivors and all of hist2d are not rechecked. Some survivors are unkillable by
construction: unit factors of 1.0 (lnlambda, nc, distance2sun) make `/` and `*` identical,
and in the fixture's high-drift regime `nuc` does not depend on `w_ab`.

Control: mutmut has no operator turning `x0 <= x` into `x0 > x` in
`solarwindpy/plotting/hist2d.py`; its `tk | (x0 <= x)` mutant was killed, and the boundary
mutant `x0 < x` survived (no test puts a limit exactly on a vertex). The hand flip
(`tmp/test-quality-review/manual_flip.sh`) is killed by
`tests/plotting/test_hist2d_plotting.py::TestPlotEdges::test_limits_drop_vertices_outside_them`.

## Excess: tests checking nothing the package owes

- 5 tests cannot fail: they assert values written inside the test
  (`tmp/test-quality-review/tautology_scan.py`), all in `tests/test_hook_integration.py`.
- 8 tests can pass without asserting on some outcome, e.g. `test_line_vertical_like_data_fails`
  ends in `except: pass` (`tmp/test-quality-review/any_outcome_candidates.txt`).
- 112 tests check only existence or type.
- 42 tests in `tests/solar_activity/icme/test_icmecat.py` patch `pandas.read_csv` for the whole
  process (`tmp/test-quality-review/patches.csv`).
- 5 tests assert docstring text.

## Fragility and harm

No captured literals, private-name assertions, or call-count mocks remain: all 12 heuristic
"captured value" hits were derived when read.

## Tooling tests

`tests/test_hook_integration.py` (20 tests): the `CLAUDE.md`-coupled
`test_coverage_requirement_in_pre_commit` (repo-state check), 5 cannot-fail tests, 5
shell-script substring checks, 3 file-exists checks; 6 test real hook behaviour.
`tests/test_import_aliases.py` (2) enforces an import-alias convention that ruff's `ICN`
rules cover.

## Documented code

- `+SKIP` docstring examples: 36 docstrings skipped whole; with the directive removed, 31 fail
  (`tmp/test-quality-review/run_skipped_doctests.sh`, `doctest_status.txt`).
- The `Plasma` docstring says `beta` returns a `Tensor` (it returns a DataFrame) and that
  species is `['p1', 'a']` (it is `('a', 'p1')`).
- The `swap_protons` example input contradicts its own comment, so its documented `True` is
  `False`.
- One unseeded `FitFunction.__init__` example is inherited by 21 subclasses.
- The ICMECAT examples reach the network.
- `README.rst`, `docs/source/tutorial/quickstart.rst`, and `docs/source/installation.rst`
  examples are not collected by the rst doctest run; under Sybil they run but assert nothing
  (`tmp/test-quality-review/run_sybil.sh`).
- Linkcheck: 5 broken links, 4 publisher 403s and 1 dead Google Drive link in the plasma module
  docstring (`tmp/test-quality-review/linkcheck.log`).

## Suite properties and other

- 7 test files use the legacy `np.random` API instead of `default_rng`.
- vulture: unreachable code at `solarwindpy/core/plasma.py:1028`.

## Positive control: known defects

| Known defect | Surfaced by |
|---|---|
| `CLAUDE.md`-coupled assertion in `tests/test_hook_integration.py` | per-test classifier (`classify_tests.py`) |
| text-matching hook tests in `tests/test_hook_integration.py` | per-test classifier; `tautology_scan.py` |
| `tests/solar_activity/sunspot_number/test_sidc.py:12` docstring | missed by the per-test classifier (the patch is in a fixture); caught by the fixture-aware `patch_inventory.py`: the docstring says nothing patches a `sidc.py` name while the `no_download` fixture patches `SIDCLoader.download_data` |
| `+SKIP` docstring examples | `run_skipped_doctests.sh` |
| `quickstart.rst` code blocks | rst doctest run finds none; Sybil runs them, asserting nothing |

The per-test method alone was too weak for fixture-level patches; the fixture-aware scan is
required.

## Re-measurement (2026-10-05)

Run after the fix program's units merged, as the long-running units of
`docs/dispatches/batch-test-quality-fixes-2026-10-02.md`.

### Linkcheck

`conda run -n solarwindpy sphinx-build -q -E -b linkcheck docs/source tmp/test-quality-review/linkcheck/out`
on master after PR #476 (results in `tmp/test-quality-review/linkcheck/out/output.json`; the
2026-10-02 baseline is kept in `tmp/test-quality-review/linkcheck-2026-10-02/`).

| | 2026-10-02 | 2026-10-05 |
|---|---|---|
| Broken | 5 | 4 |
| OK | 76 | 77 |
| Redirected | 7 | 7 |
| Unchecked (in-page anchors, one `mailto:`) | 170 | 170 |

The dead Google Drive link in the `plasma` module docstring is gone. The four remaining broken
links are DOIs whose publisher landing pages return 403 to the checker (Wiley/AGU
`10.1029/JA090iA11p11062`, A&A `10.1051/0004-6361/202140445`, Annual Reviews
`10.1146/annurev.astro.46.060407.145222`, OUP `10.1093/mnrasl/slw135`); reading them as
bot-blocks rather than dead links is an inference, not checked in a browser. No new broken link.

### Mutation

Re-run on 2026-10-07, after the fix program merged through PR #501:
`bash tmp/test-quality-review/mutmut/run_mutmut-2026-10-07-ff2.sh <module>` (results in
`tmp/test-quality-review/mutmut/<slug>/results.txt`), then a whole-file recheck of every
survivor with `tmp/test-quality-review/mutmut/recheck_survivors-2026-10-07.sh` (verdicts in
`tmp/test-quality-review/mutants_recheck.csv`). The 2026-10-02 inputs are kept beside them as
`*-2026-10-02.*`. `fitfunctions/core.py` was measured on master at 87f23f80 (#501 merged); the
other eight modules on master after #494 to #496 and, for `hist2d.py`, #498.

| Module | 2026-10-02 killed / survived | Score | 2026-10-07 killed / survived | Score | Recheck flips | Survivors after recheck |
|---|---|---|---|---|---|---|
| plotting/hist2d.py | 896 / 488 | 0.65 | 872 / 406 | 0.68 | 0 | 406 |
| core/plasma.py | 1384 / 729 | 0.65 | 1544 / 548 | 0.74 | 0 | 548 |
| core/ions.py | 62 / 10 | 0.86 | 62 / 10 | 0.86 | 0 | 10 |
| core/vector.py | 55 / 13 | 0.80 | 70 / 10 | 0.86 | 0 | 10 |
| fitfunctions/core.py | 397 / 131 | 0.75 | 470 / 184 | 0.72 | 13 | 171 |
| fitfunctions/lines.py | 9 / 1 | 0.90 | 19 / 2 | 0.90 | 0 | 2 |
| instabilities/beta_ani.py | 78 / 12 | 0.87 | 78 / 12 | 0.87 | 0 | 12 |
| sunspot_number/sidc.py | 496 / 186 | 0.73 | 497 / 185 | 0.73 | 0 | 185 |
| tools/__init__.py | 199 / 33 | 0.86 | 199 / 33 | 0.86 | 0 | 33 |

Scores are killed over all mutants, including "no tests" (26 for plasma on 2026-10-02, 1 for
vector on both dates). Mutant counts changed where the code changed: `plasma.py` gained the
species-validity masking, `fitfunctions/core.py` the shared bounds helper and the recorded
fit start, `hist2d.py` lost contour labelling.

What moved: `plasma.py` survivors fell from 729 to 548 and `vector.py` from 13 to 10, from the
missing-data and pair rules (#494) and the hand cases added through the program.
`fitfunctions/core.py` grew by 126 mutants and its score fell from 0.75 to 0.72: the new code
in #499 and #501 is less covered than the old. `sidc.py`, `tools`, `ions` and `beta_ani` are
unchanged; no unit owned them.

The whole-file recheck flipped 13 survivors, all in `fitfunctions/core.py`, against 11 in
`plasma.py` on 2026-10-02; reading the plasma difference as the rewritten tests no longer
relying on class-scoped setup is an inference, not checked mutant by mutant.

Two tests cannot run inside mutmut's instrumented copy and are excluded from both runs:
`tests/test_examples.py::test_load_plasma_finds_its_data_through_the_package` (it imports a
copy of the package from an empty directory, where mutmut's trampoline cannot find its
configuration), and the fit-function docstring tests (`-k "not docstring and not
describes_its_estimate and not notes_state"`; mutmut's rewrite replaces `FitFunction`'s class
docstring). Neither checks behaviour a code mutant changes. Controls: with no mutant active,
every module's recheck targets pass; a mutant mutmut killed (`Plasma.__init__` mutant 1)
reads killed in the recheck.

Remaining: 1,377 survivors after recheck, 1,139 of them in `plasma.py`, `hist2d.py` and
`sidc.py`. Some are unkillable by construction (unit factors of 1.0; `nuc` in the fixture's
high-drift regime, see Mutation sample). The rest are behaviours with no test that fails when
they break, the gap the review's Governing Property names.
