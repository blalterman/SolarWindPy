<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# PR review synthesis: phase-4 PRs #446-#469

The `claude-review` action left one comment on each of the 24 phase-4 PRs, and this file
splits those comments into 115 points and gives each point one disposition. No reviewer
marked anything as blocking, and about 20 points turned out to be wrong when checked against
the branches. The author's rulings in the review doc give 16 edits before merge on 10
branches plus one review pass; everything else is a follow-on, a rejection with its reason,
or one of two questions still open.

author_approved: yes

**How to approve.** Change the line above to `author_approved: yes`. To change an outcome
first, edit the `disposition:` value on that point, then flip the line. Only the points
marked `fix-before-merge` are applied before merge.

## AC 4 bound

The `Documentation / build` check (the strict nitpicky Sphinx build) fails on every one of
the 24 PRs, and on every `master` push since 0742fd6a. Each PR clears only its own area's
warnings, so only the combined tree builds clean. The author ruled that AC 4 counts CI
failures other than `Documentation / build`. AC 5, the combined check, carries the docs
build.

## Fix before merge

None of these edits touches a strict-xfail defect held on another branch, and none adds a
file that another PR touches.

| PR | Point | Edit |
|---|---|---|
| #446 | P446.2 | each xfail reason carries a grep slug (`swp-defect:<slug>`) plus the function name, with no `orbits.py` line numbers; #450's docstrings shift every cited line |
| #448 | P448.1 | `set_threshold` docstring describes what the code does now: only a plain function is called. The `callable()` fix is row 8, with `test_extrema_calculator.py` |
| #448 | P448.5 | delete `solarwindpy/reproducibility.py`, its import and `__all__` entry in `solarwindpy/__init__.py`, and its section in `docs/source/api_reference.rst` |
| #450 | P450.5 | the Spent-When header of `tests/test_source_plotting_defects.py` names an event that fits every test in the file |
| #450 | P458.7 | delete the `ab`, `carr` and `cos_theta` entries from `_trans_measurement` in `plotting/labels/base.py`; the `_templates` copies stay (#450 owns the file) |
| #452 | P452.1 | `test_gse` also asserts inequality against a perturbed Vector, so it can fail |
| #453 | P453.4 | the test pre-sets a log scale and asserts it survives; if it does not, narrow the docstring instead and report (no new xfail without the author) |
| #456 | P456.2 | parametrize the `set_log` test over x and y |
| #456 | P456.7 | review pass on `tests/plotting/test_base.py` against TEST_PATTERNS; findings go to the author and none are applied without the author |
| #460 | P460.5 | `CLAUDE.md` lists `lint-imports` in its Commands block, and the CI sentence names it |
| #448 | P460.1 | delete `solarwindpy/scripts/` (an empty package nothing imports; the phase-4 OWNS line gives it to #448); no layer comment on #460 is needed once it and `reproducibility` are gone |
| #466 | P466.3 | reword the "which governs" sentence in `.claude/commands/swp/test/audit.md:12` |
| #466 | P466.1, P466.2 | retire ast-grep rules swp-test-001, 002, 005, 006 and 007 in `tools/dev/ast_grep/test-patterns.yml` |
| #466 | P466.6 | `.claude/docs/TEST_PATTERNS.md` says plain `git commit` and names `.claude/hooks/project-env.sh` as the reason the env no longer matters |
| #468 | P468.1, P468.2 | drop the `$(SOURCEDIR)/api` removal in `docs/Makefile` and `docs/make.bat`; add the trailing newline to `docs/README.md` |
| #469 | P469.1 | `README.rst:55` links `pyproject.toml` on GitHub master, because the README also renders on PyPI |
| #469 | P469.4 | `CITATION.rst` gets the reference "Alterman, B. L. SolarWindPy. Zenodo. doi:10.5281/zenodo.17042839" and a BibTeX block |

Skipped under the author's rule 1 (code that is only a maintenance burden with no effect is
not added): P455.1.

## Author decisions

The author answered these in the review doc. Two are still open.

1. P447.1, Moyal form: remove Moyal from the package, as the first commit after merge.
2. P454.4, energy flux value: the author has no preference, so 267.6 stays.
3. P455.3, `scan_x0` switch: left to Claude; no switch, because the scan is what fits x0.
4. P459.2, base-10 lognormal: support both bases through a `base=` argument (row 8).
5. P463.2, beta wording: no change; `usage.rst` already defines the m w² = 2kT convention.
6. P450.4, scatter clipping: clipping stays, as the code and docstring already say.
7. P450.3, `set_axnorm("t")`: accept it (row 8).
8. P450.6, `str` `other_label`: raise `TypeError` at creation (row 8).
9. P458.7, duplicate labels: keep `_templates`, delete the `_trans_measurement` entries (before merge on #450).
10. P460.2, sibling imports: keep them independent; the rule stays.
11. P466.1 and P466.2, ast-grep rules: retire the five rules (before merge on #466).
12. P466.6, commit instruction: plain `git commit` (before merge on #466).
13. P454.5, scipy floor: remove the looser tier after the scipy floor push (row 6).
14. P469.2, Python floor: state none; keep pointing at `pyproject.toml`.
15. P469.4, citation: "Alterman, B. L." with BibTeX on #469; `CITATION.cff` with ORCID as a follow-on. ORCID iD 0000-0001-6673-3432.
16. P451.3, spiral hang and top edge: deferred to row 14; #470 tracks the hang, and the top-edge formula gets no GitHub issue (author); it is recorded under row 14.
17. P456.7, second review of `test_base.py`: yes, before merge on #456.
18. P457.6, GitHub issues per xfail: no. The defects are resolved inside this work plan (row 8).

Also from the review doc: delete `solarwindpy/reproducibility` and `solarwindpy/scripts`
(the author's reply on P460.1), and skip code that only adds maintenance with no effect
(the author's rule 1).

## Per-PR points

Tracker rows refer to the Next actions table in the phase-4 work plan artifact. "New row:
test-quality" is a row to add there for test-only nits that change no library code.

### PR #446
test(plotting): rebuild orbits tests on a hand-built orbit

Strict xfails (5): `OrbitHist1D.agg` MultiIndex TypeError; `OrbitHist2D.agg` normalises
twice; `make_one_plot("")` IndexError; `_put_agg_on_ax` passes `ax` positionally;
`OrbitHist2D.project_1d` KeyError 'z'.

- P446.1 [minor] test_orbits.py: notes the narrow `raises=LegNormalizationMismatch`. disposition: reject (no change asked).
- P446.2 [minor] test_orbits.py: cite something sturdier than line numbers in xfail reasons. disposition: fix-before-merge (PR #446). Author changed it to a grep slug plus the function name; the matching library comments and a slug-coverage test go to row 8.
- P446.3 [minor] test_orbits.py: wrap the kind in `re.escape` inside `match=`. disposition: reject (author rule 1: code that is only a maintenance burden with no effect). The kinds are fixed literals.
- P446.4 [minor] test_orbits.py: `test_both_leg_is_disabled` pins private behaviour. disposition: reject (false: the test goes through the public call and asserts the public error).
- P446.5 [minor] test_orbits.py: tests depend on internals `cut`, `edges`, `orbit`. disposition: reject (false: these names carry no underscore and are public under TEST_PATTERNS).

### PR #447
test(fitfunctions): real boundaries, resolved skips, flake8 clean

Strict xfails (4): `make_fit` re-raises AssertionError; `Gaussian` and `GaussianNormalized`
drop `super().make_fit()`'s return; `Moyal.function` not proportional to the Moyal pdf;
failed Gaussian fits missing from `bad_fits`.

- P447.1 [suggestion] test_moyal.py:145: the Moyal xfail rests on an unconfirmed defect. disposition: follow-on (first commit after merge). The author removes Moyal: delete `moyal.py`, its export, `test_moyal.py` with this marker, and doc mentions. Not pre-merge, because #447 edits `test_moyal.py` and #455 edits `moyal.py`, so deleting either on the other's branch is a modify/delete conflict.
- P447.2 [minor] test_moyal.py:173: the pdf ratio may underflow if the range widens. disposition: reject (no change asked; the range is safe today).
- P447.3 [minor] test_moyal.py:138: `rel=1e-6` may flicker. disposition: reject (TEST_PATTERNS sets `rel=1e-6` for noise-free fits, reason on the line).
- P447.4 [minor] general: confirm fixed seeds. disposition: follow-on (new row: test-quality). The untouched `test_trend_fits_advanced.py:64` uses unseeded `np.random.normal`.
- P447.5 [suggestion] general: fix `make_fit` and the Gaussian returns. disposition: follow-on (row 8). The strict markers on this branch record them.

### PR #448
docs(source-misc): resolve Verscharen2016a, document solar_activity, drop commented-out code

Strict xfails (3, one shared marker): `set_threshold` calls only a `FunctionType`, so
`np.nanmedian` and `functools.partial` are stored uncalled.

- P448.1 [suggestion] extrema_calculator.py: the docstring claims callables are called, which the code does not do. disposition: fix-before-merge (PR #448). Docstring half only; the `callable()` fix goes to row 8 with `test_extrema_calculator.py`.
- P448.2 [suggestion] extrema_calculator.py, sidc.py: lines over 88 columns. disposition: reject (false: `setup.cfg` ignores E501 and black passes).
- P448.3 [suggestion] tests/test_source_misc_defects.py: move the SIDC docstring test to `tests/solar_activity/`. disposition: follow-on (new row: test-quality).
- P448.4 [minor] tests/test_source_misc_defects.py: turn import-time constants into a fixture. disposition: reject (the constants are immutable; TEST_PATTERNS requires function scope only for mutating fixtures).
- P448.5 [author] solarwindpy/reproducibility.py: delete the module, which the author does not want to maintain. disposition: fix-before-merge (PR #448), confirmed by the author. #448 owns `solarwindpy/__init__.py`, which imports it; `api_reference.rst` is in no PR and no test on any branch uses the module.

### PR #449
fix(core): clear core nitpicky docs warnings and commented-out code

Strict xfails: 0.

- P449.1 [minor] plasma.py `velocity`: single backticks around `pd.Series`. disposition: reject (author rule 1: code that is only a maintenance burden with no effect). No `default_role` is set, so the docs render the same.
- P449.2 [minor] alfvenic_turbulence.py: note why the References list is flush left. disposition: reject (author rule 1: code that is only a maintenance burden with no effect).
- P449.3 [minor] plasma.py:1272, 1333: fix the `pydnamic` typo. disposition: follow-on (new row: test-quality).
- P449.4 [minor] plans/sphinx-warnings-analysis.md:72: update a reference to a deleted class. disposition: reject (historical plan note).

### PR #450
fix(plotting): clear nitpicky docs warnings, document plotting, fix four defects

Strict xfails: 0; four defects fixed in place.

- P450.1 [suggestion] agg_plot.py: `clip_data` still calls the removed `clip_lower`/`clip_upper`. disposition: follow-on (row 8). #459 holds strict markers on it; the docstring half is already done.
- P450.2 [suggestion] spiral.py: land the `build_cat` fix. disposition: follow-on (row 8). #451 holds a strict marker on it; fixing it here fails #451 as XPASS(strict).
- P450.3 [suggestion] hist1d.py:115: should `set_axnorm` accept `"t"`. disposition: follow-on (row 8). The author answered yes.
- P450.4 [suggestion] scatter.py: clipping at 0.0001/0.9999 versus removal. disposition: reject (author: clipping stays; the code and #450's docstring already agree).
- P450.5 [minor] tests/test_source_plotting_defects.py:1: the Spent-When header does not fit the file. disposition: fix-before-merge (PR #450).
- P450.6 [suggestion] labels/special.py: raise `TypeError` for a `str` `other_label`. disposition: follow-on (row 8). The author answered yes, at creation.
- P450.7 [suggestion] labels: check `__ge__` and remove or rename `__geq__`/`__leq__`. disposition: follow-on (new row: test-quality).

### PR #451
test(plotting): rebuild spiral mesh tests on a hand-worked mesh

Strict xfails (3): `build_cat` `inplace=True` TypeError; `cell_filter` passes the -9999 fill
to `np.bincount`; `calc_initial_bins` writes into the caller's int array.

- P451.1 [minor] test_spiral.py:1004: fixing `build_cat` may reroute the `cell_filter` xfail. disposition: reject (false: `cell_filter` never calls `build_cat`).
- P451.2 [minor] test_spiral.py:1002-1030: lines too long. disposition: reject (false: E501 is ignored and black passes).
- P451.3 [suggestion] spiral.py: file issues for the `generate_mesh` hang and the top-edge formula. disposition: follow-on (row 14). The author defers both and does not need them fixed; #470 tracks the hang, and the top-edge formula gets no GitHub issue (author); it is recorded under row 14.
- P451.4 [n/a] general: praises dropping call-count checks. disposition: reject (no change asked).

### PR #452
test(core): repair core tests (TestData rename, revive skipped and uncollected tests, flake8)

Strict xfails: 0.

- P452.1 [minor] test_quantities.py:383-391: `test_gse` compares a Vector with itself. disposition: fix-before-merge (PR #452). A perturbed copy gives the test the power to fail.
- P452.2 [consider] test_ions.py: compare Ions built from different frames. disposition: follow-on (new row: test-quality).
- P452.3 [minor] test_quantities.py:81: stray blank line. disposition: reject (author rule 1: code that is only a maintenance burden with no effect).
- P452.4 [minor] general: the ON FAILURE convention is correct. disposition: reject (no change asked).
- P452.5 [minor] general: unused imports are fine. disposition: reject (no change asked).

### PR #453
test(instabilities): first tests for verscharen2016 and beta_ani

Strict xfails (3): `_calc_is_unstable` masks a bool frame with NaN; `cmap` uses
`plt.cm.get_cmap` (matplotlib 3.11 and later); `_add_table_legend` puts handles in the wrong
rows.

- P453.1 [suggestion] test_verscharen2016.py: parametrize the legend test per row so OFI stays a regression guard. disposition: follow-on (new row: test-quality).
- P453.2 [suggestion] test_verscharen2016.py: gate the NaN xfail on pandas 3. disposition: reject (pyproject already pins `pandas>=3,<4`).
- P453.3 [suggestion] test_verscharen2016.py:486, 511: `legend_handles` needs matplotlib 3.7 while pyproject allows 3.5. disposition: reject (moot once tracker step 3 pushes b570a1c5, which raises the floor to 3.10; the "private API" half is false).
- P453.4 [suggestion] test_verscharen2016.py:390: the docstring promises scales survive but only checks linear. disposition: fix-before-merge (PR #453).
- P453.5 [nit] test_beta_ani.py:38: filter `ax.collections` for `QuadMesh`. disposition: follow-on (new row: test-quality).
- P453.6 [nit] test_verscharen2016.py:163: run black. disposition: reject (false: black passes).

### PR #454
test(core): rebuild units_constants tests against CODATA, SI, and IAU

Strict xfails: 0.

- P454.1 [minor] test_units_constants.py: comment that building `Constants()` at import turns a broken constructor into a collection error. disposition: reject (author rule 1: code that is only a maintenance burden with no effect).
- P454.2 [minor] test_units_constants.py: `particle()` maps species by first letter. disposition: reject (false: the example `"he"` raises KeyError; failure is already loud).
- P454.3 [minor] test_units_constants.py: add a separate electron charge test. disposition: reject (the parametrized test already covers it).
- P454.4 [minor] test_units_constants.py: use unrounded 267.63 with a tighter tolerance. disposition: reject (the author has no preference; 267.6 is the TEST_PATTERNS example and stays).
- P454.5 [minor] general: raise the floor to `scipy>=1.15`. disposition: follow-on (row 6). Local commit b570a1c5 already sets scipy 1.16; the author confirmed removing the `CODATA_TRUNCATED` tier after it is pushed.

### PR #455
fix+docs(fitfunctions): GaussianPlusHeavySide fits x0; zero nitpicky warnings; own-path defects

Strict xfails: 0; retires the `GaussianPlusHeavySide` doctest xfail.

- P455.1 [suggestion] composite.py:149: the fine-scan result is not guarded against `None`. disposition: reject (author rule 1: the fine range includes the coarse winner, which already succeeded, so the guard can never run).
- P455.2 [suggestion] composite.py:122: `list(self.p0)` does not handle `None`. disposition: reject (false: `p0` never returns `None`).
- P455.3 [suggestion] composite.py: add a `scan_x0` opt-out for the extra fits. disposition: reject (the author left it to Claude: the scan is what fits x0, and nothing calls this model inside `TrendFit` today).
- P455.4 [suggestion] composite.py: a gap midpoint outside the caller's x0 bounds could make the refit raise. disposition: follow-on (new row: test-quality).
- P455.5 [suggestion] tests/test_source_fitfunctions_defects.py: add single-x, user `p0` and noisy-step cases. disposition: follow-on (new row: test-quality).
- P455.6 [minor] general: check nothing links the deleted architecture doc. disposition: reject (checked: only historical plan and dispatch text mentions it).

### PR #456
test(plotting): rebuild base and scatter tests on real Agg objects

Strict xfails (1): `Scatter.make_plot` writes `cbar_kwargs['ax']` into the caller's dict.

- P456.1 [suggestion] test_scatter.py, test_base.py: drop the boilerplate ON FAILURE lines. disposition: reject (contradicts TEST_PATTERNS, which requires one ON FAILURE line per test and approves `the code is wrong.`).
- P456.2 [suggestion] test_scatter.py:184: `set_log` is tested only with x. disposition: fix-before-merge (PR #456).
- P456.3 [suggestion] test_scatter.py:195: add a NaN to the list-input test. disposition: follow-on (new row: test-quality).
- P456.4 [suggestion] test_scatter.py:180-181: replace exact limits with a bound. disposition: reject (contradicts TEST_PATTERNS: weakens an assertion).
- P456.5 [minor] test_scatter.py:128: create the figure inside the `try`. disposition: reject (nothing can fail in between, and the test needs a separate figure).
- P456.6 [suggestion] test_scatter.py: keep the cbar test after the fix. disposition: reject (no change asked; the xfail protocol already does this).
- P456.7 [general] test_base.py: the reviewer did not read it. disposition: fix-before-merge (PR #456). The author wants a review pass before merge; findings go to the author and none are applied without the author.

### PR #457
test(plotting): add Hist1D contract tests against numpy.histogram

Strict xfails (5): integer `nbins` drops extreme samples; logx density normalised over
neither axis; smoothed counts truncated to integers; `plot_window` with `transpose_axes`
TypeError; `construct_cdf` KeyError on the unnamed index.

- P457.1 [minor] test_hist1d.py:143: write `3` instead of `1 + 1 + 1`. disposition: reject (the sum shows the hand count, as TEST_PATTERNS wants).
- P457.2 [minor] test_hist1d.py:584: move the module-level test into a class. disposition: reject (author rule 1: code that is only a maintenance burden with no effect).
- P457.3 [minor] fixture seed: no change asked. disposition: reject (no change asked).
- P457.4 [minor] test_hist1d.py:546: loosen `rtol` if it flakes. disposition: reject (contradicts TEST_PATTERNS: speculative loosening of a reasoned tolerance).
- P457.5 [minor] test_hist1d.py:34-44: comment the AssertionError subclasses. disposition: reject (each already has a docstring).
- P457.6 [unstated] general: open tracking issues for the 5 xfails. disposition: reject (author: no issues; the defects are resolved inside this work plan, row 8 retires the markers directly).

### PR #458
test(plotting): rebuild plotting-misc on the label/mathtext contract

Strict xfails: 0.

- P458.1 [worth fixing] test_integration.py:106-129: an empty parser result raises KeyError at collection. disposition: follow-on (new row: test-quality). The failure is loud either way.
- P458.2 [minor] test_integration.py: coverage is per axis, not the cross product. disposition: follow-on (new row: test-quality).
- P458.3 [minor] test_integration.py:64: `_unescaped_dollar_count` miscounts `\\$`. disposition: follow-on (new row: test-quality).
- P458.4 [minor] test_integration.py: completeness matches class names only. disposition: reject (the ON FAILURE text covers it).
- P458.5 [minor] test_integration.py: move `import contextlib, io` to the top. disposition: reject (author rule 1: code that is only a maintenance burden with no effect).
- P458.6 [minor] test_integration.py: the regex depends on the `available()` layout. disposition: follow-on (new row: test-quality). Needs a library accessor.
- P458.7 [unstated] labels: duplicate `ab`, `carr`, `cos_theta` entries. disposition: fix-before-merge (PR #450). The author keeps the `_templates` copies and deletes the `_trans_measurement` entries; #450 owns `labels/base.py`, and #458's tests name none of the three keys.
- P458.8 [unstated] pyproject.toml, solarwindpy.yml, tests/fitfunctions/conftest.py:14: drop `psutil` and fix a stale cite. disposition: follow-on (row 6).

### PR #459
test(plotting): rebuild agg_plot, tools and nan_gaussian_filter tests on behaviour

Strict xfails (13): marginal 2-D mask (2); 1-D unnamed index KeyError (2); `clip_lower`/
`clip_upper` removed from pandas (5); list raises AttributeError; int array UFuncTypeError in
`nan_gaussian_filter`; `swap_protons` loses M/C/S names; `swap_protons` adds a handler per
call.

- P459.1 [suggestion] general: file issues and fix `clip_lower` and the Hist1D KeyError. disposition: follow-on (row 8). Defects recorded by strict markers on this branch and #457.
- P459.2 [suggestion] tools: `normal_parameters` docstring mismatch and a `swap_protons` check that never fires. disposition: follow-on (row 8). The author wants both bases: `base=np.e`, scaling m and s by ln(base), both formulas in the docstring, and a sampled test per base.
- P459.3 [suggestion] general: confirm xfail reasons are specific. disposition: reject (already done: typed `raises=` and a retiring clause on each).
- P459.4 [suggestion] general: confirm CI. disposition: reject (no change asked; CI is read after fixes under the AC 4 bound).
- P459.5 [suggestion] tests/plotting/test_tools.py: split out the `solarwindpy.tools` tests. disposition: follow-on (new row: test-quality).

### PR #460
test: replace circular-import tests with an import-linter contract

Strict xfails: 0.

- P460.1 [minor] pyproject.toml: `reproducibility` and `scripts` are not in `layers`. disposition: fix-before-merge (PR #448). The author deletes both instead of commenting. Both go on #448, whose phase-4 OWNS line covers `solarwindpy/scripts/` and `reproducibility.py` (P448.5).
- P460.2 [worth a look] pyproject.toml: confirm the lateral import bans. disposition: reject (author: keep the siblings independent; the rule stays).
- P460.3 [worth a look] general: add a subprocess import test per submodule. disposition: follow-on (new row: test-quality). Tracker row 12 covers the public import test.
- P460.4 [unstated] pyproject.toml: set `exclude_type_checking_imports`. disposition: reject (moot: no `TYPE_CHECKING` in the package).
- P460.5 [unstated] CLAUDE.md:49: the CI line omits `lint-imports`. disposition: fix-before-merge (PR #460). It goes into the Commands block and the CI sentence; a wider `/doctor prompt-audit` review of `CLAUDE.md` is a new follow-on row.
- P460.6 [unstated] workflow: whitespace-only change. disposition: reject (harmless).

### PR #461
test(drift): retire the Read the Docs drift test superseded by declared versions

Strict xfails: 0.

- P461.1 [minor] tests/drift/test_drift_controls.py: note that `_write_declaring_repo` must mirror every file the module reads. disposition: follow-on (new row: test-quality).
- P461.2 [minor] general: check `from tests import test_declared_versions` under bare pytest. disposition: reject (moot: `tests/__init__.py` exists).
- P461.3 [minor] general: the match regex is tied to the message format. disposition: reject (the reviewer calls it intended).

### PR #462
test(solar_activity): rebuild root tests on real objects

Strict xfails (3, marking 13 tests): `DataLoader.age` reads `_age` but `get_data_age` writes
`_data_age`; `lisird.py` imports `urllib` without `urllib.request`; `IndicatorPlot` uses
`labels.special.DateTime`.

- P462.1 [main follow-up] solar_activity/plots.py: land the DateTime fix and drop the 11 plotter xfails. disposition: follow-on (row 8). This PR is tests only; the fix removes its markers.
- P462.2 [unstated] test_plots.py, test_init.py: use `raises=` on the xfails. disposition: reject (already done).
- P462.3 [unstated] test_init.py: check the `sys.modules` fixture under xdist. disposition: reject (the repo uses no xdist or random order).
- P462.4 [unstated] test_init.py, test_plots.py: prefer `monkeypatch.setattr` on the URL base. disposition: reject (already done).
- P462.5 [unstated] general: commit attribution lines. disposition: reject (already present).
- P462.6 [verdict] general: fix all three library defects. disposition: follow-on (row 8).

### PR #463
docs(usage): rewrite usage.rst as a first session that runs

Strict xfails: 0; removes the whole-page xfail in `docs/source/conftest.py`.

- P463.1 [suggestion] usage.rst:63: `Freq: h` depends on the pandas version. disposition: reject (pandas is pinned `>=3,<4`).
- P463.2 [suggestion] usage.rst:74-78: state the thermal speed and `mw²=2kT` convention. disposition: reject (already satisfied: the beta sentence defines the m w² = 2kT convention, which the author says is all that is needed).
- P463.3 [suggestion] usage.rst:100-101: the ellipsis check is weak. disposition: follow-on (new row: test-quality).
- P463.4 [suggestion] usage.rst:113: note `matplotlib.use("Agg")` must come first. disposition: follow-on (new row: test-quality).
- P463.5 [info] README: the species comment is wrong. disposition: reject (no change asked here; #469 fixes it).

### PR #464
style(hooks): clear flake8 findings in the plan and compaction scripts

Strict xfails: 0.

- P464.1 [nit] .claude/hooks/create-compaction.py: a long f-string line. disposition: reject (flake8 and black accept it).
- P464.2 [nit] .claude/hooks/create-compaction.py: `ZeroDivisionError` when the token estimate is 0. disposition: follow-on (new row: test-quality).

### PR #465
chore(paper): retire the abandoned JOSS paper directory

Strict xfails: 0.

- P465.1 [note] general: files can be restored from history. disposition: reject (no change asked).

### PR #466
docs(tests): repoint TEST_PATTERNS citations; make ast-grep test rules loadable

Strict xfails: 0.

- P466.1 [minor] tools/dev/ast_grep/test-patterns.yml: rules 002 and 005 recommend `wraps=`, against the header. disposition: fix-before-merge (PR #466). The author retires the rules.
- P466.2 [minor] tools/dev/ast_grep/test-patterns.yml: rules 001, 006, 007 recommend `isinstance`. disposition: fix-before-merge (PR #466). Retired with P466.1.
- P466.3 [minor] .claude/commands/swp/test/audit.md:12: reword the "which governs" sentence. disposition: fix-before-merge (PR #466).
- P466.4 [minor] tools/dev/ast_grep/test-patterns.yml: `--filter` may do nothing with `--rule`. disposition: reject (no change asked; unverified).
- P466.5 [minor] .claude/docs/DEVELOPMENT.md: watch the branch wording. disposition: reject (the kept text is not shown false).
- P466.6 [follow-up] .claude/docs/TEST_PATTERNS.md: fix the stale `conda run ... git commit` advice. disposition: fix-before-merge (PR #466). Plain `git commit`, naming `project-env.sh`; no other PR touches the file.

### PR #467
chore(scripts): retire six one-off scripts whose use is over

Strict xfails: 0.

- P467.1 [note] general: make sure CI is green. disposition: reject (no change asked; the merge gate covers it).
- P467.2 [note] scripts/archived/: kept while a doc cites it. disposition: follow-on (row 7). #468 deletes that doc, so retire it once both merge.

### PR #468
chore: retire one-time reports and dead scaffolding

Strict xfails: 0.

- P468.1 [minor] docs/Makefile:17-20, docs/make.bat:31-32: drop the `$(SOURCEDIR)/api` removal. disposition: fix-before-merge (PR #468). The Makefile comment says to drop it once the ignore entry goes, which this PR does.
- P468.2 [minor] docs/README.md: add the trailing newline. disposition: fix-before-merge (PR #468).
- P468.3 [minor] .gitignore:10: `.DS_store` should be `.DS_Store`. disposition: follow-on (new row: test-quality).

### PR #469
docs: point install docs at pyproject.toml and fill CITATION

Strict xfails: 0.

- P469.1 [suggestion] README.rst:55: link `pyproject.toml` on GitHub. disposition: fix-before-merge (PR #469). The README renders on PyPI.
- P469.2 [suggestion] installation.rst: state a minimum Python version. disposition: reject (author: state none; keep pointing at `pyproject.toml`).
- P469.3 [note] installation.rst:86: the `Requirements`_ reference works. disposition: reject (no change asked).
- P469.4 [note] CITATION.rst: no BibTeX entry, creator name unsettled. disposition: fix-before-merge (PR #469). Reference and BibTeX as "Alterman, B. L."; a `CITATION.cff` with ORCID iD 0000-0001-6673-3432 is a new follow-on row.

## Cross-PR

- **Hist1D unnamed index (#457 and #459).** Strict markers in both PRs record the same
  `_agg_reindexer` / `Hist1D.agg` defect. One fix XPASSes both files, so it removes both
  marker sets in one commit.
- **`calc_bins_intervals` binning (#457 and `test_hist2d_plotting.py`).** The retiring fixes
  are worded differently (rounded outward, closed on both ends, both must change). A
  rounding-only fix XPASSes one hist2d marker and not #457's, so the row 8 unit fixes both
  aspects together.
- **Integer smoothing truncation (#457 and #459).** `Hist1D.make_plot` and
  `nan_gaussian_filter` are separate sites with separate markers; one float-cast policy
  covers both.
- **`SpiralMesh.build_cat` (#450 and #451).** #450's reviewer asks for the fix; #451 holds
  the strict marker. The fix lands after #451 merges and drops the marker in the same change.
- **`orbits.py` line numbers (#446 and #450).** #450's docstrings shift every line #446's
  reasons cite; P446.2 switches them to grep slugs plus function names. The matching library
  comments land in row 8, because `orbits.py` belongs to #450.
- **Moyal removal (#447 and #455).** #447 edits `test_moyal.py` and #455 edits `moyal.py`,
  so the removal waits for both to merge and lands as the first commit after.
- **`reproducibility` and `scripts` deletion (#448).** The phase-4 OWNS line gives #448
  `solarwindpy/__init__.py`, `reproducibility.py` and `scripts/`, so both deletions go there,
  with the `docs/source/api_reference.rst` entry (in no PR) removed in the same commit so the
  strict docs build stays green.
- **`verscharen2016.py` (#448 and #453).** #448 edits the file and fixes none of #453's three
  defects. Whoever fixes them drops #453's markers in the same change; `get_cmap` is row 6.
- **`set_threshold` (#448).** The library fix is blocked by `test_extrema_calculator.py`,
  which asserts the stored callable. Row 8 fixes both files and removes #448's marker.
- **`pyproject.toml` has one owner (#460).** #454's scipy floor and #458's `psutil` drop
  land after #460 merges.
- **`scripts/archived/` (#467 and #468).** Once both merge, nothing outside plans and
  dispatches cites it, so row 7 retires it.
- **False "line too long" points (#448, #451, #453).** `setup.cfg` ignores E501 and black
  passes on every file named.
- **Points that contradict TEST_PATTERNS.** P456.1 (drop ON FAILURE lines), P456.4 (weaken
  exact limits), P457.4 (speculative tolerance loosening) and P447.3 (question the
  noise-free tolerance) are rejected under the standard.
