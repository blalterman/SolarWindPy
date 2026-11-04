<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# Plan: coherence cleanup of SolarWindPy

author_signoff: none

owner: /Users/blalterman/observatories/code/SolarWindPy

Findings: `docs/dispatches/findings-coherence-and-tooling-review-2026-11-04.md`. Every `F<n>` below
is a finding there. This plan proposes; nothing in it runs until the author approves the
sequence and rules on the items in "Changes for author confirmation".

## How to read this plan

Stages are ordered by dependency, in six phases: environment and test infrastructure,
root-cause bugs, one home per idea, API alignment, the test tree, and the agent tooling. A stage
names the findings it closes. It takes an `[AUTHOR]` finding only after the author has ruled on
it. Until then that finding stays listed under "Changes for author confirmation".

Rules every stage follows:

- Run checks inside the env: `conda run -n solarwindpy pytest -q`, `conda run -n solarwindpy lint-imports`,
  and `black --check` and `flake8` through pre-commit. The suite baseline is 1 failed, 6254
  passed, 12 skipped. The one failure is `tests/test_import_aliases.py`, which reads the author's
  untracked `solarwindpy/tests/` (F194). Stage S2 removes it; until then "green" means no new
  failure.
- A behavior-preserving stage passes its guarding tests unchanged, before and after. A stage that
  changes a result writes its new test first, sees it fail, then makes it pass. It changes an
  existing assertion only where the author approved that change.
- One logical change per commit, with a conventional subject.
- Never touch `solarwindpy/plans/` or `solarwindpy/tests/`; they are the author's untracked work.

Test-quality program: every unit of `b01647bf:docs/dispatches/dispatch-continue-test-quality-fixes-2026-10-05.md`
§ Scope is merged (`gh pr list --state merged --limit 60`; `gh pr list --state open` is empty),
with two exceptions. Step 6, the parked `hingemax-point` (`solarwindpy/fitfunctions/hinge.py:1070`
still raises `NotImplementedError`), is open, and stage S29 depends on it. Step 4, "read the
warnings", has no closing commit the review could identify; `tq-fix/warning-fixes` (#499)
suggests it ran. Stage S3 treats it as unverified-open.

## Phase 1: environment and test infrastructure

### Stage S1: the environment spec matches pyproject.toml
**Target files:** `solarwindpy.yml`, `pyproject.toml` § `[tool.pip-tools]` and `[tool.setuptools.package-data]`, `MANIFEST.in`, `README.rst:96`, `CONTRIBUTING.md:20`, `docs/source/installation.rst:68`, `.claude/docs/DEVELOPMENT.md:40`
**Findings:** F196, F197, F198, F199, F200, F201, F205, F169, F206. The dependency changes F202, F203, F204 wait for the author.
**Principle:** P1 (one dependency declaration), P9 (every header line true).
**Mirrors:** `.github/workflows/ci-master.yml:36` (`pip install -e ".[dev]"`) for the install step; `pyproject.toml:57` `requires-python` for the Python pin; `pyproject.toml` § `[tool.setuptools.package-data]` as the one home for package data.
**Done when:** a fresh `conda env create -f solarwindpy.yml` env runs `pytest -q`, `lint-imports`, `black --check`, and `flake8` with no further install; `command grep -c -E '^- python' solarwindpy.yml` is 1; `git grep -n -E 'pip install -e \.( |$)' -- solarwindpy.yml README.rst CONTRIBUTING.md docs/source/installation.rst` prints nothing; `command grep -c LICESNSE MANIFEST.in` is 0; `command grep -c csv MANIFEST.in` is 0.
**Density:** judgment: the yml stops restating pyproject's list, so each remaining line states something only conda needs to know.
**Guarding tests:** `tests/test_declared_versions.py` and the full suite, run in the new env.
**Depends on:** none.

### Stage S2: the alias test goes, and the other scans read tracked files only
**Target files:** `tests/test_import_aliases.py`, `tests/plotting/test_no_data_files.py`, `tests/test_tolerance_rule.py`
**Findings:** F194, F195.
**Principle:** P1 (one definition of "the package"), P9; for the alias test, P6, since the check costs more than the drift it has caught.
**Mirrors:** deleting the alias test mirrors no form. For the two scans that stay, and for the alias test if the author keeps it, `tests/test_public_imports.py:40` (`pkgutil.walk_packages`) for package roots and `git ls-files` for the `tests/` root.
**Done when:** `git ls-files tests/test_import_aliases.py` prints nothing (or, under the fallback, `conda run -n solarwindpy pytest -q tests/test_import_aliases.py` passes with the author's untracked `solarwindpy/tests/` present), and `git grep -n rglob -- tests` prints nothing.
**Density:** judgment: one custom check that has caught nothing goes, and two improvised file-set definitions become the one the suite already uses.
**Guarding tests:** the full suite before and after, minus `tests/test_import_aliases.py`; for the two scans that stay, their own vacuity guards. Under the fallback, a positive control on a scratch branch, where a tracked aliased import makes the alias test fail.
**Depends on:** the author's approval of the deletion, or the choice of the fallback (Changes for author confirmation).

### Stage S3: tests stop setting an option pandas 3 ignores
**Target files:** the six `tests/core` files that call `pd.set_option("mode.chained_assignment", "raise")`
**Findings:** F172.
**Principle:** P1.
**Mirrors:** the package-side removal, commit "chore: remove the inert pandas chained_assignment settings".
**Done when:** `git grep -n chained_assignment -- tests` prints nothing, and `conda run -n solarwindpy pytest tests/core -q -W error::pandas.errors.Pandas4Warning` passes.
**Density:** judgment: six dead lines go, and the warning count of `tests/core` falls from 6 to 0.
**Guarding tests:** `conda run -n solarwindpy pytest tests/core tests/test_examples.py -q` (894 passed before and after).
**Depends on:** test-quality step 4 ("read the warnings"), unverified-open; if it has reported, none.

## Phase 2: root-cause bugs

### Stage S4: runtime checks that can fail
**Target files:** `solarwindpy/tools/__init__.py`, `solarwindpy/solar_activity/base.py`
**Findings:** F136 (author), F145.
**Principle:** P9 (a check that can show its failure).
**Mirrors:** `solarwindpy/core/base.py:Core._require_dataframe`, which raises a named error with a message.
**Done when:** the `swap_protons` check is the one the author's ruling names (the proposal divides by `n p1`), a test makes it fire on a hand-built frame, and `command grep -n 'assert dates.size' solarwindpy/solar_activity/base.py` prints nothing.
**Density:** judgment: unchanged line count; two inert checks become live ones.
**Guarding tests:** `tests/tools/test_tools.py` and `tests/solar_activity/test_base.py` pass before and after; the new `swap_protons` test and a test with two dated cache directories are written red first.
**Depends on:** the author's ruling on F136.

### Stage S5: one missing-data rule for core magnitudes
**Target files:** `solarwindpy/core/plasma.py`, `solarwindpy/core/spacecraft.py`
**Findings:** F59, F63 (both author). F66 stays a suspicion until the author rules.
**Principle:** P1, P8.
**Mirrors:** `solarwindpy/core/ions.py:Ion.anisotropy` and `solarwindpy/core/vector.py:Vector.mag` (`skipna=False`).
**Done when:** the F59 and F63 repros print the values the author's recorded ruling names (`nan nan` for each, if the proposed rule is accepted).
**Density:** judgment: `Plasma.anisotropy` gathers `Ion.anisotropy` instead of recomputing it, so one formula has one home.
**Guarding tests:** `tests/core/test_plasma.py`, `tests/core/test_spacecraft.py`, `tests/core/test_ions.py` pass before and after; one masked-time test per finding is written red first.
**Depends on:** the author's ruling on F59 and F63.

### Stage S6: Vector and Tensor calls work or go
**Target files:** `solarwindpy/core/vector.py`, `solarwindpy/core/tensor.py`, `tests/core/test_quantities.py`
**Findings:** F78 (author), the untested half of F171.
**Principle:** P2, P9.
**Mirrors:** `solarwindpy/core/vector.py:Vector.x` style component properties, which `__call__` would delegate to by `getattr(self, component)`.
**Done when:** `plasma.b("x")` returns the `x` component, or `__call__` is removed with a CHANGELOG entry, per the author; a test covers whichever exists.
**Density:** judgment: a documented call that always raises either works or stops being documented.
**Guarding tests:** `tests/core/test_quantities.py` passes before and after; the `__call__` test is written red first.
**Depends on:** the author's ruling on F78.

### Stage S7: the save path is derived, not stored
**Target files:** `solarwindpy/plotting/base.py`, `solarwindpy/plotting/hist1d.py`, `solarwindpy/plotting/scatter.py`
**Findings:** F121, F122, F123 (author), F124 (author).
**Principle:** P1, P3.
**Mirrors:** `solarwindpy/plotting/base.py:Base.data`, a property rebuilt from state on each access; `solarwindpy/plotting/labels/special.py:_path_part` for the one path-part helper.
**Done when:** the F123 and F122 repros print the paths the author's ruling names (`logX-logY` and a y scale, under the proposal), and `git grep -c 'replace(" ", "-")' -- solarwindpy/plotting/base.py` is 1.
**Density:** judgment: four path builders become one, and the "Bug:" comment goes with the bug.
**Guarding tests:** `tests/plotting/test_base.py`, `test_scatter.py`, `test_hist1d.py`; a new test pinning every class's default path passes before and after for unchanged cases, and is red first for the cases the author approves changing.
**Depends on:** the author's ruling on F123 and F124.

### Stage S8: label species come from one table
**Target files:** `solarwindpy/plotting/labels/base.py`, `solarwindpy/plotting/labels/composition.py`
**Findings:** F128 (author for the new TeX), F129.
**Principle:** P1.
**Mirrors:** `solarwindpy/plotting/labels/elemental_abundance.py:known_species`, which derives its tuple instead of retyping it.
**Done when:** the F128 repro prints `[]` and a subscript with no `bim`; `known_species` in `composition.py` is derived.
**Density:** judgment: two species lists become one plus a test that ties it to `core`'s roster.
**Guarding tests:** `tests/plotting/labels/test_labels_base.py`, `tests/plotting/labels/test_composition.py`; a test iterating `core/units_constants.py:_m_in_mp` is written red first.
**Depends on:** the author's TeX for `a_bimax` and `pm`.

### Stage S9: one residual
**Target files:** `solarwindpy/fitfunctions/core.py`, `solarwindpy/fitfunctions/plots.py`
**Findings:** F86 (author picks the sign), F95.
**Principle:** P2, P1.
**Mirrors:** `solarwindpy/fitfunctions/core.py:FitFunction.build_plotter`, which already hands its state to `FFPlot`; the simple residual delegates to one implementation.
**Done when:** the F86 repro prints two equal numbers, `git grep -c "100.0 \* (r /" solarwindpy/fitfunctions` totals 1, and the provenance Notes at `core.py:757` are gone.
**Density:** judgment: two residual implementations with opposite signs become one.
**Guarding tests:** `tests/fitfunctions/test_core.py`, `tests/fitfunctions/test_plots.py`; the side whose sign flips changes its assertions with the author's approval.
**Depends on:** the author's ruling on F86.

## Phase 3: one home per idea

### Stage S10: one Gaussian kernel and one Gaussian LaTeX string
**Target files:** `solarwindpy/fitfunctions/gaussians.py`, `solarwindpy/fitfunctions/composite.py`
**Findings:** F87, F89, F90.
**Principle:** P1.
**Mirrors:** `solarwindpy/fitfunctions/gaussians.py:_weighted_moments`, a private module helper the composites already import.
**Done when:** `git grep -c "arg = -0.5 \* (((x - mu)" solarwindpy/fitfunctions` totals 1, and each composite's `function.__name__` differs.
**Density:** judgment: five kernel copies become one, and the drifted bracket form goes.
**Guarding tests:** `conda run -n solarwindpy pytest tests/fitfunctions/test_composite.py tests/fitfunctions/test_gaussians.py tests/test_source_fitfunctions_defects.py tests/test_available.py -q`, before and after.
**Depends on:** none.

### Stage S11: one Heaviside step value
**Target files:** `solarwindpy/fitfunctions/heaviside.py`, `solarwindpy/fitfunctions/composite.py`, `tests/fitfunctions/test_heaviside.py`
**Findings:** F88 (author).
**Principle:** P1, P8.
**Mirrors:** a `_step` helper beside S10's `_gaussian`, in the form of `solarwindpy/fitfunctions/gaussians.py:_weighted_moments`.
**Done when:** every step model evaluates to the author's chosen value at `x == x0` (the F88 repro prints the same middle value for both classes), and `git grep -n "np.heaviside(" solarwindpy/fitfunctions | command grep -v ">>>"` shows one line.
**Density:** judgment: three disagreeing step rules become one.
**Guarding tests:** `tests/fitfunctions/test_heaviside.py` and `tests/fitfunctions/test_composite.py`; `test_heaviside.py:170` changes by design, with the author's sign-off.
**Depends on:** S10; the author's ruling on F88.

### Stage S12: core validators and level names have one home
**Target files:** `solarwindpy/core/base.py`, `ions.py`, `plasma.py`, `spacecraft.py`, `solarwindpy/examples/__init__.py`, `solarwindpy/tools/__init__.py`
**Findings:** F50, F55, F56, F57, F58.
**Principle:** P1, P5.
**Mirrors:** `solarwindpy/core/base.py:Core._require_dataframe` (move `_require_level_names` beside it); `solarwindpy/core/base.py:Base.mi_tuples` (its level names become one module constant); `solarwindpy/core/base.py:Base._clean_species_for_setting` as the only `+` rule.
**Done when:** the F50 repro prints one line; `git grep -n "assert " -- 'solarwindpy/core/*.py'` lists only the four internal invariants; `Ion.set_data` calls the shared level-name check.
**Density:** judgment: ten literal copies and ten input asserts collapse into one constant and one validator family.
**Guarding tests:** `tests/core/test_base*.py`, `tests/core/test_core_verify_datetimeindex.py`, `tests/core/test_ions.py`, `tests/core/test_spacecraft.py`, `tests/core/test_plasma.py`; a test that a wrong spacecraft type raises `TypeError` under `python -O` is written red first.
**Depends on:** the author's confirmation of the exception types (Changes for author confirmation).

### Stage S13: fitfunctions and instabilities raise named errors
**Target files:** `solarwindpy/fitfunctions/core.py`, `exponentials.py`, `trend_fits.py`, `composite.py`, `solarwindpy/instabilities/verscharen2016.py`
**Findings:** F97 (author), F98, F104, F112.
**Principle:** P3, P5.
**Mirrors:** the existing `raise InvalidParameterError(...)` sites in `solarwindpy/fitfunctions/core.py`; in `verscharen2016.py`, the `TypeError` and `ValueError` raises of `StabilityContours.plot_contours`.
**Done when:** `git grep -n "^\s*assert " solarwindpy/fitfunctions/*.py solarwindpy/instabilities` lists only the five internal invariants, and the F97, F98, F104 repros show a named error with a message or a signature with no default.
**Density:** judgment: nine caller-input asserts become the package's own error type.
**Guarding tests:** `conda run -n solarwindpy pytest tests/fitfunctions tests/instabilities -q`; one new test per converted check is written red against the old `AssertionError`.
**Depends on:** the author's confirmation of the exception types and of F97.

### Stage S14: each core formula has one home
**Target files:** `solarwindpy/core/plasma.py`, `tensor.py`, `alfvenic_turbulence.py`, `units_constants.py`
**Findings:** F60, F61, F62, F64, F65, F67.
**Principle:** P1.
**Mirrors:** `solarwindpy/core/tensor.py:Tensor.magnitude` (scalar thermal speed); `solarwindpy/core/ions.py:Ion.cs` gathered as `solarwindpy/core/plasma.py:Plasma.pth` gathers `Ion.pth`; `solarwindpy/core/vector.py:Vector.rho`; `solarwindpy/core/units_constants.py:_misc_constants` (rotation rate).
**Done when:** `git grep -n "cs = pth.divide(rho, axis=0)" -- solarwindpy/core` prints one line; `git grep -n -E "units\.b / \(" -- solarwindpy/core` prints one line; `git grep -n "2.865e-6" -- solarwindpy` matches only `units_constants.py`.
**Density:** judgment: the same physics in fewer formula lines, each with one home.
**Guarding tests:** `tests/core/test_plasma.py`, `test_ions.py`, `test_quantities.py`, `test_alfvenic_turbulence.py` (including the hand-computed Raffaella test), `test_spacecraft.py`, unchanged before and after.
**Depends on:** S5 (both touch `Plasma` formula methods).

### Stage S15: one gather helper and no dead code in Plasma
**Target files:** `solarwindpy/core/plasma.py`, `solarwindpy/examples/__init__.py`, `solarwindpy/core/abundances.py`
**Findings:** F68, F69, F70, F71, F72.
**Principle:** P1.
**Mirrors:** `solarwindpy/core/plasma.py:Plasma._species_weighted_mean`, a private static helper every caller shares. No form fits the HDF key defaults; they become class attributes read by `save` and `load_from_file`.
**Done when:** `git grep -n -E "\{s: self\.ions\.loc\[s\]\." -- solarwindpy/core/plasma.py` matches only the helper; `git grep -c include_dynamic -- solarwindpy/core/plasma.py` is 0; `git grep -c "You passes" -- solarwindpy` is 0.
**Density:** judgment: six copied gather blocks become one helper, and three dead blocks go, with no method lost.
**Guarding tests:** `tests/core/test_plasma.py`, `tests/core/test_plasma_io.py`, unchanged before and after.
**Depends on:** S14.

### Stage S16: comments, docstrings, and dead text predict their content
**Target files:** the four `xs` comments, `solarwindpy/core/plasma.py` module and `save` docstrings, `solarwindpy/core/alfvenic_turbulence.py`, `solarwindpy/core/units_constants.py` docstring, `solarwindpy/fitfunctions/composite.py`, `solarwindpy/fitfunctions/trend_fits.py`, `solarwindpy/instabilities/verscharen2016.py`
**Findings:** F53, F77, F81, F82, F83, F84, F94, F103, F111.
**Principle:** P2, P1.
**Mirrors:** `solarwindpy/core/base.py:Base` class Notes for the no-deep-copy rule, stated once; `solarwindpy/fitfunctions/hinge.py:Hinge` Notes, which state behavior without TODOs. The `xs` comment is rewritten for pandas 3 copy-on-write, per the probe in the CLAUDE.md proposal.
**Done when:** `git grep -c "We rely on views via DataFrame.xs" -- solarwindpy` totals 1; `git grep -n -E "auto_reindex|Propoded|spacecraft_modifier_fcn|cos_colat|#XX|color_norm" -- solarwindpy` prints nothing; `trend_fits.py` has no `noqa: F401`.
**Density:** judgment: one rule stated once, and about 22 lines of history removed from a module docstring.
**Guarding tests:** `conda run -n solarwindpy pytest --doctest-modules solarwindpy -q` and the docs build, before and after.
**Depends on:** S12, S14 (the `cos_colat` local sits in code S14 moves).

### Stage S17: one logger helper
**Target files:** the seven `_init_logger` sites, `solarwindpy/tools/__init__.py`, `solarwindpy/plotting/labels/base.py`
**Findings:** F101, F133, F137.
**Principle:** P1, P5.
**Mirrors:** `solarwindpy/core/base.py:Core._init_logger` (logger `<module>.<class>`, no handler); the bottom layer can host it under the `[tool.importlinter]` contract.
**Done when:** `git grep -c "def _init_logger" -- solarwindpy` is 1, and `tools/__init__.py` attaches no `StreamHandler`.
**Density:** judgment: seven copies of one idea become one.
**Guarding tests:** the logger tests across `tests/` (`git grep -l logger -- tests`), the full suite, and `lint-imports`, before and after.
**Depends on:** none.

### Stage S18: stale pointers and dead copies in solar_activity
**Target files:** `solarwindpy/solar_activity/icme/icmecat.py`, `tests/drift/test_drift_icmecat.py`, `solarwindpy/solar_activity/base.py`, `solarwindpy/solar_activity/sunspot_number/sidc.py`
**Findings:** F146, F149, F153, F163, F166, F186, the unreachable branch of F152.
**Principle:** P1, P9.
**Mirrors:** the `p0-simplify` acceptance check that removed the stale `plasma.py:102` pointer: name the symbol, never the line.
**Done when:** `git grep -nE 'icmecat\.py:[0-9]' -- solarwindpy tests` prints nothing; `command grep -c 'dt = pd.to_timedelta(dt)' solarwindpy/solar_activity/base.py` is 1; `command grep -n 'raise ValueError$' solarwindpy/solar_activity/base.py` prints nothing; `git grep -il sidc -- tests/drift | wc -l` is at least 1.
**Density:** judgment: five copied line facts and two dead statements go.
**Guarding tests:** `conda run -n solarwindpy pytest -q tests/solar_activity tests/drift`, plus one run with `--run-drift` for the edited messages.
**Depends on:** none.

### Stage S19: one home per fact in sidc.py
**Target files:** `solarwindpy/solar_activity/sunspot_number/sidc.py`
**Findings:** F151, F152, F155, F156, F159, F160; F158 after the author rules.
**Principle:** P1.
**Mirrors:** `solarwindpy/solar_activity/sunspot_number/sidc.py:SIDC_ID._trans_url` as the single key table; `solarwindpy/solar_activity/base.py:ActivityIndicator._run_normalization` for the per-cycle helper.
**Done when:** in `sidc.py`, `command grep -c '_dtypes_columns = '` is 5, `command grep -c 'SSNExtrema()'` is 1, `command grep -c 'groupby("cycle")'` is 1, `command grep -c '(7, 3, 2, 3, 2, 3, 2, 3)'` is 1; `command grep -c 'def plot_on_colorbar'` is 0, the method now living in `solarwindpy/solar_activity/plots.py`.
**Density:** judgment: seven tables hold five facts and will hold five; two loops and two branches become one each.
**Guarding tests:** `conda run -n solarwindpy pytest -q tests/solar_activity/sunspot_number tests/solar_activity/test_plots.py`, notably `test_sidc_loader.py:402`, `test_sidc.py:367`, `test_sidc.py:385`.
**Depends on:** S18.

### Stage S20: verscharen2016 tables keyed once
**Target files:** `solarwindpy/instabilities/verscharen2016.py`
**Findings:** F106, F107, F108, F109 (author for the dtype).
**Principle:** P1.
**Mirrors:** `solarwindpy/instabilities/verscharen2016.py:_inst_type_idx`, the one-index form.
**Done when:** the growth-rate values are typed once outside `insta_params`, `"Between"` appears only in display labels, and the F109 repro prints an integer dtype or the docstring says float, per the author.
**Density:** judgment: style rows come from two short indexes instead of twelve hand-typed rows.
**Guarding tests:** `tests/instabilities/test_verscharen2016.py`, including `test_table_legend_rows_and_columns_describe_their_curves` and the PNG render, before and after.
**Depends on:** S13 (same module).

### Stage S21: plotting style path and clim have one owner
**Target files:** `solarwindpy/plotting/tools.py`, `solarwindpy/plotting/agg_plot.py`, `solarwindpy/plotting/spiral.py`, `solarwindpy/plotting/binned.py`
**Findings:** F115, F119 (author for the type), F120, F118 (author for the percentile).
**Principle:** P1.
**Mirrors:** `solarwindpy/plotting/__init__.py:_STYLE_PATH`; `solarwindpy/plotting/base.py:PlotWithZdata._apply_alim` for a shared `_apply_clim`; `solarwindpy/plotting/binned.py:_clip_to_quantiles`, given a percentile argument.
**Done when:** `git grep -c '_STYLE_PATH =' -- solarwindpy` totals 1; `git grep -c 'c0, c1 = self.clim' -- solarwindpy` totals 1; the F119 repro prints one type name twice; `git grep -n -E 'quantile\(\[' -- solarwindpy/plotting` prints only `binned.py`.
**Density:** judgment: one style path, one clim filter, one clipping rule.
**Guarding tests:** `tests/plotting/test_tools.py`, `test_integration.py`, `test_agg_plot.py`, `test_spiral.py`, `test_plot_invariants.py`; a test that forces the `MemoryError` branch is written first and passes before and after while the percentile is unchanged.
**Depends on:** the author's rulings on F119 and F118.

### Stage S22: one label-with-units formatter
**Target files:** `solarwindpy/plotting/labels/base.py`, `special.py`, `datetime.py`
**Findings:** F130 (author for the bracket form), F131, F132.
**Principle:** P1.
**Mirrors:** `solarwindpy/plotting/labels/base.py:Base.with_units` with `_format_with_description`; `solarwindpy/plotting/labels/special.py:ArbitraryLabel` as the shared parent of `CountOther` and `Probability`.
**Done when:** the F130 `git grep` prints one line and `special.py:162` calls the formatter; the F131 repro prints only `_inU` lines.
**Density:** judgment: fourteen restatements of one format and four copies of `set_new_line_for_units` become one each.
**Guarding tests:** `tests/plotting/labels/test_special.py`, `test_datetime.py`, `tests/plotting/test_integration.py`.
**Depends on:** S8 (same tables); the author's bracket form.

### Stage S23: units stated once
**Target files:** `solarwindpy/core/units_constants.py`, `solarwindpy/plotting/labels/base.py`
**Findings:** F51 (author).
**Principle:** P1.
**Mirrors:** no form holds a factor and its TeX unit together. The nearest is `solarwindpy/core/units_constants.py:Constants`'s `pd.Series` fields: `Units` gains a `tex` mapping that `_trans_units` reads.
**Done when:** the `nuc` TODO is gone, and a test asserts every `Units` field has a `_trans_units` entry with the same unit.
**Density:** judgment: two unit homes become one, with a test tying them.
**Guarding tests:** `tests/core/test_units_constants.py`, `tests/plotting/labels/test_labels_base.py`; the cross-check test is written red first.
**Depends on:** S22; the author's ruling on the key names.

### Stage S24: log-normal moments have one home
**Target files:** `solarwindpy/fitfunctions/gaussians.py`
**Findings:** F134. The rename in F135 waits for the author.
**Principle:** P1.
**Mirrors:** `solarwindpy/tools/__init__.py:normal_parameters`.
**Done when:** `GaussianLn.normal_parameters` calls `tools.normal_parameters`, and `git grep -c 'np.exp(s\*\*2.0) - 1.0' -- solarwindpy` totals 1.
**Density:** judgment: two copies of a cited formula become one.
**Guarding tests:** `tests/fitfunctions/test_gaussians.py::TestGaussianLn::test_normal_parameters_calculation`, `tests/tools/test_tools.py`.
**Depends on:** S10 (same module).

## Phase 4: API alignment

### Stage S25: solar_activity base contracts predict their subclasses
**Target files:** `solarwindpy/solar_activity/base.py`, `solarwindpy/solar_activity/sunspot_number/sidc.py`
**Findings:** F141, F142, F144, F147, F150; F143 and F148 after the author rules.
**Principle:** P3, P5.
**Mirrors:** `@property` over `@abstractmethod` for abstract properties; `solarwindpy/fitfunctions/core.py:FitFunctionMeta` for docstring inheritance.
**Done when:** `git grep -nE '@abstract(property|staticmethod)' solarwindpy/solar_activity` prints nothing; `command grep -c '__doc__ =' solarwindpy/solar_activity/sunspot_number/sidc.py` is 0; `download_data` and `convert_nans` show matching parameter lists in base and subclass.
**Density:** judgment: the abstract signatures become a contract the subclass satisfies, with no growth.
**Guarding tests:** `conda run -n solarwindpy pytest -q tests/solar_activity`, notably `tests/solar_activity/test_base.py:216`.
**Depends on:** S18, S19; the author's confirmation of the signature changes.

### Stage S26: ICMECAT joins the subpackage's base layer
**Target files:** `solarwindpy/solar_activity/icme/icmecat.py`, `solarwindpy/solar_activity/icme/__init__.py`
**Findings:** F139, F162, F164, F165, F167; F140 after the author rules on the cache.
**Principle:** P1, P3, P5.
**Mirrors:** `solarwindpy/solar_activity/base.py:Base` for the logger; `solarwindpy/solar_activity/icme/icmecat.py:ICMECAT._filter_by_spacecraft` as the one name lookup.
**Done when:** `command grep -c 'def _init_logger' solarwindpy/solar_activity/icme/icmecat.py` is 0; `command grep -c 'name_map = ' solarwindpy/solar_activity/icme/icmecat.py` is 1; `command grep -c 'icmecat.ICMECAT_URL = str(local)' solarwindpy/solar_activity/icme/__init__.py` is 0; `RULES_OF_THE_ROAD` is in `icmecat.__all__`.
**Density:** judgment: one logger, one lookup, one doctest where there were two of each.
**Guarding tests:** `conda run -n solarwindpy pytest -q tests/solar_activity/icme`, `conda run -n solarwindpy pytest --doctest-modules solarwindpy/solar_activity -q`, `tests/test_public_imports.py`.
**Depends on:** S17, S25.

### Stage S27: plot constructors and contour parameters agree
**Target files:** `solarwindpy/plotting/hist1d.py`, `scatter.py`, `spiral.py`, `hist2d.py`
**Findings:** F125 (author), F126 (author), F127.
**Principle:** P3.
**Mirrors:** `solarwindpy/plotting/hist2d.py:Hist2D.__init__` for parameter order; `solarwindpy/plotting/spiral.py:SpiralPlot2D.plot_contours` for the direct `nan_gaussian_filter` call.
**Done when:** the F125 and F126 repros print matching parameter lists, and `git grep -c _nan_gaussian_filter -- solarwindpy` is 0.
**Density:** judgment: one wrapper concept fewer; the same positional call binds the same parameter in every class.
**Guarding tests:** `tests/plotting/test_hist2d_plotting.py`, `test_spiral.py`, `test_hist1d.py`, `test_scatter.py`.
**Depends on:** S7, S21; the author's rulings on F125 and F126.

### Stage S28: the fit plotter shares plotting's vocabulary
**Target files:** `solarwindpy/fitfunctions/plots.py`, `solarwindpy/instabilities/beta_ani.py`
**Findings:** F99 (author), F100, F113.
**Principle:** P1, P3.
**Mirrors:** `solarwindpy/fitfunctions/trend_fits.py:19` (`from ..plotting.tools import subplots`); `solarwindpy/plotting/base.py:Base.set_log` for the `set_log` signature.
**Done when:** `git grep -n "AxesLabels = namedtuple" solarwindpy` shows one line, and `beta_ani.py` contains no `_bimax`.
**Density:** judgment: two namedtuple definitions and one re-implemented setter go.
**Guarding tests:** `tests/fitfunctions/test_plots.py`, `tests/instabilities/test_beta_ani.py`, `tests/test_public_imports.py`.
**Depends on:** S9 (same module); the author's ruling on F99.

### Stage S29: one hinge guess vocabulary
**Target files:** `solarwindpy/fitfunctions/hinge.py`, `solarwindpy/fitfunctions/CONTRIBUTING.md`, `tests/fitfunctions/test_hinge.py`, `tests/fitfunctions/test_p0_contract.py`
**Findings:** F91 (author), F92 (author), F93.
**Principle:** P2, P3, P5.
**Mirrors:** `solarwindpy/fitfunctions/hinge.py:Hinge._XH`, the single home for the reference hinge.
**Done when:** the F91 repro prints one keyword name across all six classes; `command grep -c "self\._guess_\w* = \|self\._saturation_guess = " solarwindpy/fitfunctions/hinge.py` is 1; `CONTRIBUTING.md` agrees with the shipped default.
**Density:** judgment: three names and three defaults for one concept become one.
**Guarding tests:** `tests/fitfunctions/test_hinge.py`, `test_p0_contract.py`, `test_docstring_inheritance.py`.
**Depends on:** the open test-quality step 6, `hingemax-point` (`hinge.py:1070`); run after it or fold it in, with the author.

### Stage S30: examples is its own layer
**Target files:** `pyproject.toml` § `[tool.importlinter]` and `[tool.setuptools.package-data]`, `solarwindpy/examples/`, `solarwindpy/core/data/example_*.csv`
**Findings:** F48, F49, F85.
**Principle:** P4, P3, P2.
**Mirrors:** `solarwindpy/core/abundances.py:ReferenceAbundances._load_data` (data beside its owner via `resources.files(__package__)`); the existing `layers` contract with `examples` above `core`.
**Done when:** `lint-imports` lists `examples` in a layer; the example CSVs live under `solarwindpy/examples/data/` with `Spacecraft`'s labels; `tests/test_examples.py::test_load_plasma_finds_its_data_through_the_package` passes.
**Density:** judgment: the three-entry translation table in the loader disappears.
**Guarding tests:** `tests/test_examples.py` and `conda run -n solarwindpy pytest --doctest-modules solarwindpy -q`.
**Depends on:** S1 (package data), S12 (the shared level-name constant).

### Stage S31: public names the author has ruled on
**Target files:** per ruling; see "Changes for author confirmation", public API.
**Findings:** F52, F73, F74, F75, F76, F79, F80, F173, F96, F102, F105, F110, F114, F116, F117, F135, F138, F154.
**Principle:** P2, P4, P8.
**Mirrors:** per item, the sibling the finding names (`solarwindpy/core/vector.py:Vector.r` for `r`, `solarwindpy/core/ions.py:Ion.velocity` returning a `Vector` for `thermal_speed`); for deprecation, `solarwindpy/__init__.py:pp`.
**Done when:** each item carries the author's ruling; each accepted rename ships with a deprecation alias and a CHANGELOG entry; each declined item is recorded as decided in the CHANGELOG or the findings file.
**Density:** judgment: a name stops meaning two things; nothing is measured.
**Guarding tests:** per accepted change, a test that the old name warns and the new one returns the sibling's type, written red first; the full suite before and after.
**Depends on:** the author's rulings; S6 and S12 for the core items.

## Phase 5: the test tree mirrors the code tree

### Stage S32: tests/core and examples mirror their modules
**Target files:** `tests/core/test_base.py`, `test_base_head_tail.py`, `test_base_mi_tuples.py`, `test_core_verify_datetimeindex.py`, `test_quantities.py`, `tests/test_examples.py`, `tests/test_contracts_class.py`
**Findings:** F170, F171, F174, F187, F189, F191; F173 after the author rules.
**Principle:** P3.
**Mirrors:** `tests/plotting/_cases.py` for the shared fixture module; `tests/tools/test_tools.py` for a one-module subpackage.
**Done when:** every `core` module has a `tests/core/test_<module>.py` (including `vector`, `tensor`, `base`); `git grep -n "import test_base" -- tests` prints nothing; `tests/examples/` holds the loader test.
**Density:** judgment: same tests, one placement rule.
**Guarding tests:** `conda run -n solarwindpy pytest tests/core tests/test_examples.py tests/test_contracts_class.py --collect-only -q | tail -1` equal before and after, and the suite passes; moves use `git mv`.
**Depends on:** S3, S5, S6, S12, S14, S15, so moved tests carry their new assertions.

### Stage S33: fitfunctions tests mirror their modules
**Target files:** `tests/test_source_fitfunctions_defects.py`, `tests/test_fitfunctions_public_names.py`, `tests/test_available.py`, `tests/fitfunctions/test_trend_fit_properties.py`, `tests/fitfunctions/__init__.py` (new)
**Findings:** F175, F176, F177, F178, F179, F190.
**Principle:** P3, P1.
**Mirrors:** `tests/instabilities/`, one test file per module with an `__init__.py`.
**Done when:** each fitfunctions test lives in `tests/fitfunctions/test_<module>.py` or a named cross-class contract file (or the author keeps the `test_source_*_defects.py` form and its header names every module it guards); `tests/fitfunctions/__init__.py` exists; the redundant re-export test is gone.
**Density:** judgment: three test files for one module become two, and one test that restates another goes.
**Guarding tests:** collected test ids before and after differ only by path and the removed duplicate (`conda run -n solarwindpy pytest --collect-only -q tests/fitfunctions tests/test_fitfunctions_public_names.py tests/test_source_fitfunctions_defects.py tests/test_available.py | tail -1`).
**Depends on:** S9, S10, S11, S13, S24, S28, S29.

### Stage S34: plotting tests named for what they test
**Target files:** `tests/plotting/`, `tests/test_source_plotting_defects.py`, `tests/plotting/labels/test_labels_base.py`
**Findings:** F180, F181, F182, F188.
**Principle:** P3, P2.
**Mirrors:** `tests/plotting/labels/`, one file per module.
**Done when:** every `tests/plotting/test_*.py` names a module in `solarwindpy/plotting/` or a cross-class invariant (`test_plot_invariants.py`, `test_plot_budget.py`, `test_integration.py`, `test_no_data_files.py`); `tests/test_source_plotting_defects.py` lives under `tests/plotting/`.
**Density:** judgment: provenance names give way to subject names; about 21 files become about 12.
**Guarding tests:** `conda run -n solarwindpy pytest --collect-only -q tests/plotting tests/test_source_plotting_defects.py | tail -1` equal before and after; `Spent-When` headers move with their tests.
**Depends on:** S7, S8, S21, S22, S27.

### Stage S35: solar_activity and root tests follow one placement rule
**Target files:** `tests/solar_activity/icme/test_icmecat_smoke.py`, `tests/solar_activity/sunspot_number/test_init.py`, `tests/conftest.py`
**Findings:** F183, F184, F193; F185 and F192 after the author rules.
**Principle:** P3, P5.
**Mirrors:** `tests/solar_activity/test_init.py:test_every_exported_name_resolves` for the init contract; the split-by-class rule of the `sidc.py` tests.
**Done when:** each tracked `tests/test_*.py` imports more than one subpackage or no package code; `tests/solar_activity/sunspot_number/test_init.py` uses the parent's form; the `tests/conftest.py` docstring describes what the file holds.
**Density:** judgment: two split rules become one, and a 155-line init test becomes the parent's 14-line form.
**Guarding tests:** `conda run -n solarwindpy pytest -q --collect-only 2>&1 | tail -1` before and after, with only the agreed duplicates removed, and the full suite.
**Depends on:** S18, S19, S25, S26, S32, S33, S34.

## Phase 6: agent tooling, per Pass 1

The tooling stages touch no package code. They are last by the dependency order the review was
asked for, but S36 to S39 could run at any point, and an earlier run would give every later
cleanup session accurate instructions. The author decides.

### Stage S36: retire the tooling nothing uses
**Target files:** `.claude/README.md`, `.claude/WORKFLOW_TEMPLATE.md`, `.claude/branch-preservation.log`, `.claude/compacted_state.md`, `.claude/docs/HOOKS.md`, `.claude/ecosystem-documentation.md`, `.claude/emergency-rollback.json`, `.claude/hooks/coverage-monitor.py`, `.claude/hooks/create-compaction.py`, `.claude/hooks/input-validation.sh`, `.claude/hooks/validate-tags.sh`, `.claude/logs/phase0-time-tracking.md`, `.claude/scripts/cleanup-compaction-tags.py`, `.claude/scripts/generate-test.py`, `.claude/templates/test-patterns.py`, `.claude/validation-monitoring.json`, the `.claude/templates` exclude in `.pre-commit-config.yaml`, the Stop and PreCompact registrations and the allow rules for retired scripts in `.claude/settings.json`, the coverage-monitor sentence at `CLAUDE.md:58`, `tests/test_hooks.py`
**Findings:** F12, F13, F21, F31, F32, F34, F35, F37, F38, F39, F40, F41, F42, F43, F44, F45, F46.
**Principle:** P1, P9.
**Mirrors:** `https://code.claude.com/docs/en/claude-directory.md`, the documented roles for a committed `.claude/`; nothing outside those roles stays.
**Done when:** `git ls-files .claude | wc -l` is 9 (the three kept and six rebuilt files of Pass 1's verdicts); `git grep -n -E 'coverage-monitor|create-compaction|compacted_state' -- .claude tests CLAUDE.md ':!.claude/docs/MAINTENANCE.md'` prints nothing (MAINTENANCE.md goes in S39); `conda run -n solarwindpy pytest -q tests/test_hooks.py` passes.
**Density:** judgment: sixteen files that restate, misstate, or do nothing go.
**Guarding tests:** `tests/test_hooks.py` (its PreCompact tests at lines 122-143 and 184-192 go with the hook, with the author's approval); the full suite before and after.
**Depends on:** the author's approval of the retirements.

### Stage S37: settings.json uses documented keys only
**Target files:** `.claude/settings.json`, `tests/test_hooks.py`
**Findings:** F1, F2, F3, F4, F5, F6, F7, F8 (author), F9, F10, F11, F14, F15, F16.
**Principle:** P9, P1.
**Mirrors:** `https://code.claude.com/docs/en/settings-reference.md` and `https://code.claude.com/docs/en/permissions.md`; the existing deny list is kept as is.
**Done when:** `python3 -c 'import json; print(sorted(json.load(open(".claude/settings.json"))))'` prints only documented keys, including `$schema`; `command grep -c -E 'systemPrompt|planningMode|"ai"|"tools"|MultiEdit|domain:!' .claude/settings.json` is 0; push rules sit under `ask`; `Read(//etc/**)` replaces `Read(/etc/**)`; hook commands use `${CLAUDE_PROJECT_DIR}`.
**Density:** judgment: four undocumented keys and the dead or subsumed allow rules go.
**Guarding tests:** `tests/test_hooks.py`, updated for the new registrations, passes; Claude Code starts with no Settings Error.
**Depends on:** S36; the author's ruling on F8.

### Stage S38: the hooks that gate, gate
**Target files:** `.claude/hooks/pre-commit-tests.sh`, `.claude/hooks/test-runner.sh`, `.claude/settings.json` hooks, `.github/PULL_REQUEST_TEMPLATE.md:18`, `tests/test_hooks.py`
**Findings:** F17, F18, F19, F22, F23, F24, F25, F33.
**Principle:** P9, P1.
**Mirrors:** the Stop-hook shape in `https://code.claude.com/docs/en/hooks-guide.md` (exit 2 with failures on stderr, a `stop_hook_active` guard), run through `.claude/hooks/project-env.sh`.
**Done when:** `pre-commit-tests.sh` holds the staged-file guard and the one coverage gate and nothing after it; the floor number appears only there; either `test-runner.sh` is retired with its PR-template line, or a Stop hook built on it fails a turn with a red test and `tests/test_hooks.py` has a test that sees that failure.
**Density:** judgment: a hook either gates or goes; the coverage floor gets one home.
**Guarding tests:** `tests/test_hooks.py` passes before and after; the new test that a failing test reaches Claude is written red first, if the per-turn gate is kept.
**Depends on:** S37; the author's ruling on the per-turn test gate and on raising the floor.

### Stage S39: procedures move into a skill, rules into one place
**Target files:** `.claude/docs/RELEASING.md`, `.claude/docs/MAINTENANCE.md`, `.claude/docs/DEVELOPMENT.md`, `.claude/scripts/monitor-conda-release.sh`, `.claude/skills/release/SKILL.md` (new), `.claude/docs/TEST_PATTERNS.md`
**Findings:** F22, F34, F36, F47, F200 (the DEVELOPMENT.md copy).
**Principle:** P1, P4.
**Mirrors:** the skill layout in `https://code.claude.com/docs/en/skills.md` (SKILL.md under 500 lines, details in supporting files).
**Done when:** `.claude/skills/release/SKILL.md` exists and names `RELEASING.md` and `monitor-conda-release.sh` as supporting files; `.claude/docs/DEVELOPMENT.md` and `MAINTENANCE.md` are gone with their keepable lines moved; the citations of `TEST_PATTERNS.md` in `pyproject.toml:24` and `tests/plotting/test_no_data_files.py:134` still resolve.
**Density:** judgment: a 591-line procedure loads only when used, and each rule it carried lives in one place.
**Guarding tests:** `tests/plotting/test_no_data_files.py` and the full suite before and after.
**Depends on:** S36; the author's approval of the skill.

### Stage S40: CLAUDE.md holds only what the code cannot say
**Target files:** `CLAUDE.md`, `.claude/settings.json` (deny rules for the author's untracked directories, if chosen)
**Findings:** F20, F26, F27, F28, F29, F30.
**Principle:** P1, P4, P9.
**Mirrors:** the proposed file in the findings file, § "CLAUDE.md proposal".
**Done when:** `CLAUDE.md` matches the approved proposal; every command in it runs as written in a fresh shell; `command grep -c -E 'test-runner|coverage-monitor|units_constants.py:[0-9]' CLAUDE.md` is 0; it names the `xs` rule by symbol, which `git grep` finds; it is under 200 lines; the branch line is filled in by the author.
**Density:** judgment: layout lines `ls` can show give way to the commands, gotchas, and decisions a session cannot infer.
**Guarding tests:** a fresh session reads the file with no Settings Error; the full suite, unchanged, before and after.
**Depends on:** S1, S36, S37, S38, S39; the author's approval of the rewrite.

## Changes for author confirmation

Every item below needs the author's ruling before a stage takes it. Ids are findings in the
findings file; C-labels are control-arm items listed in its § "Control comparison".

### Public API changes

- Exception types become named errors instead of `AssertionError`, raised also under `python -O`:
  F57, F58 (core, to `TypeError` or `ValueError`), F98, F104, F112 (to
  `InvalidParameterError`, `TypeError`, `ValueError`); F97 (`guess_x0` loses its `None`
  default). Stages S12, S13.
- `solar_activity`: `ID.set_key` raises `ValueError` instead of `NotImplementedError` (F148,
  pinned by `tests/solar_activity/test_base.py:193`); `SIDC.interpolate_data` takes the base's
  parameter order (F143). Stage S25.
- `Vector.__call__` and `Tensor.__call__`: fix or remove (F78). Stage S6.
- `clim` type: `tuple` or `RangeLimits` for every aggregating plot (F119). Stage S21.
- Plot constructors: one parameter order, `logx`, `logy`, `axnorm` keyword-only (F125);
  `plot_contours` defaults (F126). Stage S27.
- `AxesLabels` and `LogAxes` leave `fitfunctions.plots.__all__` or change their defining module
  (F99). Stage S28.
- Hinge guess keyword: one name and one default for six classes (F91); `saturation_guess`
  follows (F92). Stage S29.
- `stability_bin` dtype: integer, or a docstring that says float (F109). Stage S20.
- Renames and return types, stage S31: `heat_flux`, `qpar`, and `q` (F52); `Spacecraft.r`
  (F73); `Vector.rho` (F74); `Ion.thermal_speed` and `Plasma.thermal_speed` types (F75);
  `AlfvenicTurbulence.velocity` and `.bfield` types (F76); `Ion.set_species` and the missing
  aliases (F79); the spacecraft and frame name list (F80); a public raw-frame loader for the
  test fixtures (F173); `ExponentialCDF.set_y0` to a constructor keyword and `y0` against `A`
  (F96); `TrendFit`'s per-bin names (F102); `growth_rate`, `plot_gamma`, `gamma` (F110);
  the `beta_ani` module name (F114); the four `Base` and two `Ion` classes (F116); the
  `labels.datetime` module (F117); `normal_parameters` (F135); the two `tools` modules
  (F138).
- `RULES_OF_THE_ROAD` joins `icmecat.__all__` (F165). Stage S26.
- The abstract signatures of the public `solar_activity` base classes change to match their subclass (`download_data`, `convert_nans`; F141, F142, F144). Stage S25.
- The `tools` fallback logger is renamed to `<module>.<class>` and loses its handler (F137). Stage S17.
- `get_data_ctime` raises `ValueError` where it asserted (F145). Stage S4.

### Data-column and declared-compatibility changes

- Hemispheric `totalstd_error`, `northstd_error`, `southstd_error` gain an underscore, which
  changes users' cached CSVs (F154).
- `astropy>=5.0` floor raised so it excludes 6.1.x with numpy 2.5 (F202).
- `h5py` replaced by `tables` as a runtime dependency (F203); `pyyaml`, `numexpr`,
  `bottleneck` kept or dropped (F204).
- Two cache policies in `solar_activity` unified, which changes user-visible caching (F140).

### Scientific-result and output changes

- `Plasma.anisotropy` becomes NaN at masked times (F59); `Spacecraft.distance2sun` becomes NaN
  at a missing component (F63). Stage S5.
- Which residual sign governs, `FitFunction.residuals` or `FFPlot.residuals` (F86). Stage S9.
- One Heaviside value at `x == x0` (F88). Stage S11.
- `swap_protons`'s check can now raise (F136). Stage S4.
- Saved-figure paths change: scale follows `set_log`, and `Scatter`'s default path gains its
  class name (F123, F124). Stage S7.
- TeX for `a_bimax` and `pm` (F128); one bracket form for every label (F130). Stages S8, S22.
- The memory-fallback clip percentile (F118). Stage S21.
- `Units` and `_trans_units` tied, with one key per quantity (F51). Stage S23.
- The `SSNPlot` y range of 0 to 200 (F161).
- `cut_spec_by_ssn_band` takes its bands from `self.data` but cuts `self.interpolated`; making the two agree changes which values are cut (F158). Stage S19.

### Physics suspicions

The review flags these and judges none of them.

- `alfvenic_turbulence` fluctuation energies sum components with `skipna=True` (F66).
- `HeavySide`'s value at `x0` mixes `y` squared into a `y`-valued model (F88).
- The `beta_ani_inst` doctest uses `b=-0.408`, the FMW `a`, with the AIC row (F105).
- The extrema docstring says cycle mean while the code uses half the cycle maximum (F157).
- A fixed 200 SSN range may clip cycle 19's smoothed maximum (F161).

### Deletions

- The 16 `.claude` files Pass 1 marks retire, and the `tests/test_hooks.py` tests that check
  them (stage S36).
- `ssn_extrema.csv.silso`, kept as provenance or retired (F168).
- The redundant re-export test (F179); the `test_contracts_dataframe.py` file, kept, pointed at
  package code, or retired (F192).
- The `Spent-When` headers in two shipped modules, kept or removed (F54).

### Test placement decisions

- `tests/test_import_aliases.py` (F194). Recommendation: delete it. Stage S2.
  - It has caught nothing in history since the alias cleanup. 1244828c (2026-09-30) removed the
    remaining aliases. In the 157 commits since then that touch `solarwindpy/`, no added line
    binds an alias other than `np`, `pd`, `plt`, `mpl`, or `mdates`. Check: run
    `git log --format=%h -G '^\s*(import|from) .* as [A-Za-z_]+' 1244828c..HEAD -- solarwindpy`,
    then filter each hit's added lines for other aliases; the filter prints nothing. Counted by
    date instead (`--since=2026-09-30`), the figure is 208 commits, and the one hit, c7c5d160,
    predates the cleanup that removed its aliases. A catch by a local pre-commit run would never
    reach history, so this shows only that no alias was committed.
  - Its costs: it fails on untracked files (today's one suite failure); the mutation runs must
    pass `--ignore=tests/test_import_aliases.py`; ruff `ICN` cannot replace it (PR #480), so it
    is custom code to maintain.
  - The positive form already holds: the package imports under real names, and sessions mirror
    the code around them. The likelier source of alias habits is guidance a session reads, such
    as the dead "Common Aliases" section in `.claude/docs/DEVELOPMENT.md` (F47, stage S39).
  - Alias choice is open-space composition, not an author seam. The deletion is listed here
    because removing a test is a deletion.
  - Fallback, if the author keeps it: scan git-tracked files only, by mirroring
    `tests/test_public_imports.py:40` (`pkgutil.walk_packages`) or using `git ls-files`.
  - Either way, the `rglob` scans in `tests/plotting/test_no_data_files.py` and
    `tests/test_tolerance_rule.py` move to tracked files (F195).
- Whether fixed-defect tests mirror the code tree or the fix history (F176). Stage S33.
- Which home is canonical for live-network ICMECAT checks, `integration` or `drift` (F185).
  Stage S35.

### CLAUDE.md rewrite

- Replace `CLAUDE.md` with the proposal in the findings file (F20, F26 to F30), including
  the branch policy line, which the author writes (F36).
- Whether the untracked-directory protection becomes a deny rule.

### Tooling rebuild and retirement

- Pass 1's 25 verdicts as a whole: keep 3, rebuild 6, retire 16 (stages S36 to S39).
- Pushes move from `allow` to `ask` (F8).
- Whether a per-turn test gate is wanted at all; if not, `test-runner.sh` retires with its PR
  template line (F17 to F19).
- Raise the coverage floor per the ratchet rule (F22; measured 98%).
- `.claude/docs/RELEASING.md` becomes `.claude/skills/release/` (stage S39).
- `.claude/hooks/project-env.sh` stays, or moves to `scripts/` as a git-hook helper.
- `.claude/docs/TEST_PATTERNS.md` stays a pointer, or loads as `.claude/rules/tests.md`.

### Control-arm items the principled arm missed

Verified or read by the assembler, held for the author because the principled arm did not
review them. Each would become a stage in phase 2.

- C1, verified: `cut_spec_by_interval(kind=None)`, the documented default, raises. Raise a clear
  error, or default to `"Cycle"`.
- C2, read: `std_error` is computed before `convert_nans` replaces the `-1` sentinel, so
  sentinel rows cache `-inf` or `-0.5`.
- C3, read: `get_data_ctime` matches the date on the full path, and three test fixtures work
  around it.
- C5, verified: loggers are named after `solar_activity.base`, not the subclass's module.
- C17, verified: `pytest --cov=solarwindpy.solar_activity` fails at collection with
  `ImportError: cannot load module more than once per process`; `--cov=solarwindpy` passes. Pass
  1 did not cover it. The author decides whether `CLAUDE.md` should name the working form for
  one subpackage's coverage.
