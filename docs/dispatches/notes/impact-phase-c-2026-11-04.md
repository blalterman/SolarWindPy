<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# Phase C impact analysis

## Method and provenance

- Coverage contexts: `conda run -n solarwindpy pytest -q --cov=solarwindpy --cov-context=test` (6239 passed, 12 skipped). For each target symbol I took its body's line range from the AST and collected `CoverageData.contexts_by_lineno`, with parametrize ids stripped. The run started while the entropy removal sat uncommitted in the tree, and it was committed as 64379c6f two minutes later. Line ranges were taken from 64379c6f and match the run (e.g. Plasma.anisotropy 1258-1274).
- git grep: per-item symbol patterns over tests/, with each hit mapped to its enclosing test function. The two sets are unioned. Grep-only hits that exercise nothing the item changes are listed as excluded, not classified.
- Coverage context caveat: a class- or module-scoped fixture's work is attributed to the first test that triggers it, so a coverage-derived set is a lower bound.
- Doctests (`pytest --doctest-modules solarwindpy`, the separate CI doctest workflow) were not run per trial. B3's doctest is the only doctest mapped. D1 removes the doctests of the deleted classes along with them.
- Guard labels were checked empirically where behaviour changes. I extracted HEAD into the scratchpad with `git archive`, applied a minimal patch per item, and ran the impacted test directories with PYTHONPATH on the copy (solarwindpy.__file__ confirmed inside it). Verified this way: D1, B2, B4, B5, B6, B7, B9, B11, M1. Inferred (docstring-only, or widening what is accepted): B3, B8, B10, P1.
- Pins: pins.tsv is at the session scratchpad (`/private/tmp/claude-501/-Users-blalterman-observatories-code-SolarWindPy/a04e7fdc-c916-4938-acad-74b79ff7234b/scratchpad/pins.tsv`), not tmp/coherence-review/. It carries file and commit only, no line or test. I reconstructed the lines: asserts containing a literal with two or more decimals after removing rel=/abs=/rtol=/atol=/decimal= values, blamed, and matched per (file, commit). At HEAD 64379c6f, 22 of the 28 (file, commit) groups match exactly. test_ions (2) and test_plasma (1) lost pins to the entropy removal. Four groups over-count by 1 to 9, because the original rule is not recorded. The test_tolerance_rule group differs most (10 lines found against 1 listed). Roughly 52 of the 55 pins survive.
- Counts, summed per item: {'delete': 118, 'guard': 344, 'fragile': 3, 'update': 21}. Deduplicated across items (a test counted once, at its strongest class, ordered delete > update > fragile > guard): 450 tests, {'delete': 118, 'guard': 308, 'fragile': 3, 'update': 21}.

## Execution order

1. Group 1, deletions: D1, D2, D3, D4. They can run in parallel; serialize the CHANGELOG.md edits.
2. Groups 2 to 8 in parallel. Within a group, run in the order listed:
   - Group 2: B9 then B2. fitfunctions plotter. B9 edits plots.py's imports, B2 edits FFPlot.residuals and its constructor in the same file.
   - Group 3: B10. fitfunctions/gaussians.py docstring only; independent.
   - Group 4: B3 then B4. Same module and test file.
   - Group 5: B7 then B11 then B6. All three edit sidc.py; B6 also edits solar_activity/plots.py and tests/solar_activity/test_plots.py, and B11 also edits solar_activity/base.py and tests/solar_activity/test_base.py.
   - Group 6: B1. core/vector.py, core/tensor.py, tests/core/test_quantities.py; independent.
   - Group 7: B8 then M1. B8 adds the supported-frame table that distance2sun reads; M1 edits distance2sun's reduction in the same method. M1 also edits plasma.py, alfvenic_turbulence.py, missing_data.rst, and their test files.
   - Group 8: B5. tools/__init__.py, tests/tools/test_tools.py; independent.
3. Group 9, P1, last. It changes the declared environment.

CHANGELOG.md is touched by nearly every item and will conflict across parallel groups. Either serialize the commits that touch it, or let each group's commit carry its own entry and rebase in order.

`order` in the JSON is the wave: 1 = deletions, 2 to 4 = position within a parallel group, 5 = P1.

## Items flagged for the author's eyes on the diff

- B2: the residual sign. Simple flips to observed minus fitted. Robust `fit_result.fun` is model minus observed, so it must be negated or kind='both' overlays opposite signs. Also the delegation mechanism.
- B5: a dead assert becomes live on user data.
- M1: NaN replaces finite values at masked rows, including downstream Plasma.nc and the raffaella bfield.
- B8: whether spacecraft names are unrestricted or a core-level list.
- D1: scope confirmation. GaussianPlusHeavySide is included, so composite.py is removed whole.
- Not flagged, but visible to users: B6 changes SSN plot ranges; B7 renames data columns (a same-day cache keeps the old names).

## Author-file pins

None of the 11 surviving pins in the author's files (tests/core/test_plasma.py: 9, tests/core/test_units_constants.py: 2) sits in a test any Phase C item impacts, so none is touched. This is a lower bound, per the fixture-attribution caveat. M1's test_plasma.py impact is the eight test_anisotropy methods (one per species-combination class) plus six nc tests that reach distance2sun, and none carries a pin.

## D1 (F88, F96, F97)

Group 1, wave 1, author review: yes.

**Targets**

- solarwindpy/fitfunctions/heaviside.py (whole module: HeavySide)
- solarwindpy/fitfunctions/composite.py (whole module: GaussianPlusHeavySide, GaussianTimesHeavySide, GaussianTimesHeavySidePlusHeavySide)
- solarwindpy/fitfunctions/exponentials.py:ExponentialCDF (and its __all__ entry)
- solarwindpy/fitfunctions/__init__.py:__all__ ('composite', 'heaviside'), the two `from . import` lines, and the module docstring's GaussianTimesHeavySide guess_x0 example (line 26)
- solarwindpy/fitfunctions/CONTRIBUTING.md lines 183, 405 (and 404: test_composite.py cited as the parameterization example)
- tests/fitfunctions/test_every_fit_function.py: REQUIRED_KWARGS and SETUP entries for the deleted classes
- CHANGELOG.md

Scope is an interpretation. No class in composite.py imports heaviside.py's HeavySide; all three use np.heaviside inline. I read "every fit function built on HeavySide" as the Heaviside-step family, which takes GaussianPlusHeavySide too and empties composite.py, so the whole module goes. Two premises support this: the brief names GaussianTimesHeavySide and GaussianTimesHeavySidePlusHeavySide only as examples ("e.g."), and tests/test_source_fitfunctions_defects.py carries `Spent-When: PERMANENT(solarwindpy.fitfunctions drops GaussianPlusHeavySide)`, the event this deletion triggers. Flagged for the author to confirm.

Verified in a HEAD snapshot (git archive, run with PYTHONPATH on the copy; solarwindpy.__file__ resolved into it): after deleting the modules, the only failure among the surviving fitfunctions files is test_every_fit_function.py::test_every_class_has_a_case (`len(CLASSES) >= 20`, 16 remain). test_exponentials.py and test_p0_contract.py fail at collection because they import the removed names. Their per-test labels come from reading the parametrize lists.

The fragile test must change in the D1 commit itself, or the suite goes red.

docs/source/ has no hand-written reference to these classes (autosummary generates the API pages), so the docs edit is CONTRIBUTING.md and the package docstring only.

**Impacted tests**: 111 (93 delete, 1 fragile, 8 guard, 9 update)

*delete* (93)

- `tests/fitfunctions/test_composite.py`: `TestGaussianPlusHeavySide::test_callable_interface`, `TestGaussianPlusHeavySide::test_fit_recovers_gaussian_parameters_for_various_combinations`, `TestGaussianPlusHeavySide::test_fit_recovers_gaussian_parameters_from_clean_data`, `TestGaussianPlusHeavySide::test_fit_uncertainty_scales_with_noise`, `TestGaussianPlusHeavySide::test_fit_with_noise_recovers_gaussian_parameters_within_2sigma`, `TestGaussianPlusHeavySide::test_func_evaluates_above_x0_correctly`, `TestGaussianPlusHeavySide::test_func_evaluates_at_gaussian_peak`, `TestGaussianPlusHeavySide::test_func_evaluates_at_x0_correctly`, `TestGaussianPlusHeavySide::test_func_evaluates_below_x0_correctly`, `TestGaussianPlusHeavySide::test_function_signature`, `TestGaussianPlusHeavySide::test_insufficient_data_raises_error`, `TestGaussianPlusHeavySide::test_p0_enables_successful_convergence`, `TestGaussianPlusHeavySide::test_p0_returns_list_with_correct_length`, `TestGaussianPlusHeavySide::test_popt_has_correct_keys`, `TestGaussianPlusHeavySide::test_psigma_has_same_keys_as_popt`, `TestGaussianPlusHeavySide::test_psigma_values_are_nonnegative`, `TestGaussianTimesHeavySide::test_callable_interface`, `TestGaussianTimesHeavySide::test_fit_recovers_exact_parameters_from_clean_data`, `TestGaussianTimesHeavySide::test_fit_recovers_various_parameter_combinations`, `TestGaussianTimesHeavySide::test_fit_uncertainty_scales_with_noise`, `TestGaussianTimesHeavySide::test_fit_with_noise_recovers_gaussian_parameters_within_2sigma`, `TestGaussianTimesHeavySide::test_func_evaluates_above_x0_as_gaussian`, `TestGaussianTimesHeavySide::test_func_evaluates_at_gaussian_peak`, `TestGaussianTimesHeavySide::test_func_evaluates_at_x0_correctly`, `TestGaussianTimesHeavySide::test_func_evaluates_below_x0_as_zero`, `TestGaussianTimesHeavySide::test_function_signature`, `TestGaussianTimesHeavySide::test_guess_x0_is_required`, `TestGaussianTimesHeavySide::test_insufficient_data_raises_error`, `TestGaussianTimesHeavySide::test_p0_enables_successful_convergence`, `TestGaussianTimesHeavySide::test_p0_returns_list_with_correct_length`, `TestGaussianTimesHeavySide::test_popt_has_correct_keys`, `TestGaussianTimesHeavySide::test_psigma_values_are_nonnegative`, `TestGaussianTimesHeavySidePlusHeavySide::test_callable_interface`, `TestGaussianTimesHeavySidePlusHeavySide::test_fit_recovers_exact_parameters_from_clean_data`, `TestGaussianTimesHeavySidePlusHeavySide::test_fit_recovers_various_parameter_combinations`, `TestGaussianTimesHeavySidePlusHeavySide::test_fit_uncertainty_scales_with_noise`, `TestGaussianTimesHeavySidePlusHeavySide::test_fit_with_noise_recovers_gaussian_parameters_within_2sigma`, `TestGaussianTimesHeavySidePlusHeavySide::test_func_evaluates_above_x0_as_gaussian`, `TestGaussianTimesHeavySidePlusHeavySide::test_func_evaluates_at_gaussian_peak`, `TestGaussianTimesHeavySidePlusHeavySide::test_func_evaluates_at_x0_correctly`, `TestGaussianTimesHeavySidePlusHeavySide::test_func_evaluates_below_x0_as_constant`, `TestGaussianTimesHeavySidePlusHeavySide::test_function_signature`, `TestGaussianTimesHeavySidePlusHeavySide::test_guess_x0_is_required`, `TestGaussianTimesHeavySidePlusHeavySide::test_insufficient_data_raises_error`, `TestGaussianTimesHeavySidePlusHeavySide::test_p0_enables_successful_convergence`, `TestGaussianTimesHeavySidePlusHeavySide::test_p0_returns_list_with_correct_length`, `TestGaussianTimesHeavySidePlusHeavySide::test_plateau_region_is_constant`, `TestGaussianTimesHeavySidePlusHeavySide::test_popt_has_correct_keys`, `TestGaussianTimesHeavySidePlusHeavySide::test_psigma_values_are_nonnegative`, `TestGaussianTimesHeavySidePlusHeavySide::test_transition_continuity`
- `tests/fitfunctions/test_exponentials.py`: `test_cdf_tex_info_reports_the_fixed_amplitude_after_the_rate`, `test_exponential_cdf_fits_one_point`, `test_exponential_cdf_monotonicity`, `test_exponential_cdf_p0_estimation`, `test_make_fit_success_cdf`, `test_str_and_call_methods_cdf`
- `tests/fitfunctions/test_heaviside.py`: `test_callable_interface`, `test_fit_recovers_exact_parameters_from_clean_data`, `test_fit_recovers_negative_step_parameters`, `test_fit_recovers_various_parameter_combinations`, `test_fit_recovers_zero_baseline_parameters`, `test_fit_uncertainty_scales_with_noise`, `test_fit_with_noise_recovers_parameters_within_tolerance`, `test_func_evaluates_above_step_correctly`, `test_func_evaluates_at_step_transition`, `test_func_evaluates_below_step_correctly`, `test_func_with_negative_step_height`, `test_func_with_zero_baseline`, `test_function_signature`, `test_insufficient_data_raises_error`, `test_p0_provides_reasonable_initial_guesses`, `test_p0_returns_list_with_correct_length`, `test_popt_has_correct_keys`, `test_psigma_has_same_keys_as_popt`, `test_psigma_values_are_nonnegative`, `test_step_discontinuity_magnitude`, `test_tex_function_property`
- `tests/fitfunctions/test_p0_contract.py`: `test_heavyside_uses_both_level_guesses_when_given`, `test_malformed_bounds_with_no_guess_are_returned_by_the_x0_scan`
- `tests/test_source_fitfunctions_defects.py`: `test_gaussian_plus_heavyside_accepts_absolute_sigma_false`, `test_gaussian_plus_heavyside_finds_a_step_in_the_first_gap`, `test_gaussian_plus_heavyside_fits_x0_between_bracketing_samples`, `test_gaussian_plus_heavyside_fits_x0_between_bracketing_samples_with_noise`, `test_gaussian_plus_heavyside_replaces_the_x0_of_a_caller_p0`, `test_gaussian_plus_heavyside_returns_a_failed_final_fit`, `test_gaussian_plus_heavyside_returns_insufficient_data_error`, `test_gaussian_plus_heavyside_scan_respects_caller_x0_bounds`, `test_gaussian_plus_heavyside_with_a_single_x_starts_from_the_default`, `test_gaussian_plus_heavyside_with_no_guess_starts_inside_caller_bounds`, `test_line_fits_exact_data_when_repeated_x_defeats_the_initial_guess`, `test_line_p0_is_slope_and_intercept_of_exact_line`, `test_line_x_intercept_p0_is_slope_and_x_intercept_of_exact_line`, `test_trend_fit_popt1d_keys_survive_pickle_round_trip`

*update* (9)

- `tests/fitfunctions/test_exponentials.py`: `TestExponentialTeXPhase6::test_all_tex_functions_valid`, `test_TeX_function_strings`, `test_extreme_decay_rates_reach_their_limits`, `test_function_signature_and_output`, `test_p0_zero_size_input`, `test_property_access_before_fit`
- `tests/fitfunctions/test_p0_contract.py`: `test_impossible_estimate_gives_none_and_fits_from_the_feasible_default`, `test_insufficient_data_still_raises_from_p0`, `test_normal_input_estimate_matches_hand_calculation`

*fragile* (1)

- `tests/fitfunctions/test_every_fit_function.py`: `test_every_class_has_a_case`

*guard* (8)

- `tests/fitfunctions/test_every_fit_function.py`: `test_base_class_keywords_reach_the_observation_selection`, `test_explicit_p0_none_fits_from_the_generic_start`
- `tests/test_available.py`: `test_available_ignores_subclasses_defined_elsewhere`, `test_available_lists_exactly_the_fit_functions_defined_in_the_package`, `test_columns_are_aligned_under_dashes_as_wide_as_each_column`, `test_each_row_names_the_module_the_class_is_imported_from`, `test_each_row_shows_that_class_s_own_formula`, `test_every_fit_function_formula_reads_without_data`

**Pins in impacted tests**

- None.

**Target tests, written first as `pytest.mark.xfail(strict=True)`**

- The removed modules are gone: importlib.util.find_spec('solarwindpy.fitfunctions.heaviside') and ('...composite') are None, and 'ExponentialCDF' is not an attribute of solarwindpy.fitfunctions.exponentials.
- Guard, not xfail (it passes on HEAD too): fitfunctions.__all__ names only importable submodules, i.e. importlib.import_module(f'solarwindpy.fitfunctions.{n}') succeeds for every n. This protects the __all__ edit.
- Rewrite of the fragile test_every_class_has_a_case: the CLASSES discovered by test_every_fit_function equal the set found by test_available's module scan (a relation between two discoveries, replacing the unsourced `>= 20`). This one is a guard rewrite, not an xfail: it passes before and after.

## D2 (F168, F192)

Group 1, wave 1, author review: no.

**Targets**

- solarwindpy/solar_activity/sunspot_number/ssn_extrema.csv.silso (delete; nothing reads it, MANIFEST.in ships only ssn_extrema.csv)
- tests/test_contracts_dataframe.py (delete; references solarwindpy zero times)
- CHANGELOG.md

tests/test_contracts_dataframe.py: all 23 tests deleted. The coverage run cannot see it (it imports no solarwindpy), so the set comes from the file's AST.

ssn_extrema.csv.silso: no test or code reads it. The `silso` grep hits are SILSO-download tests, which are unrelated and not counted.

**Impacted tests**: 23 (23 delete)

*delete* (23)

- `tests/test_contracts_dataframe.py`: `TestColumnDuplicationPrevention::test_duplicated_filters_duplicates`, `TestColumnDuplicationPrevention::test_isin_detects_duplicates`, `TestCrossSectionPatterns::test_xs_extracts_measurement_type`, `TestCrossSectionPatterns::test_xs_extracts_single_species`, `TestCrossSectionPatterns::test_xs_preserves_index`, `TestCrossSectionPatterns::test_xs_with_tuple_full_path`, `TestGroupbyTransposePattern::test_groupby_transpose_preserves_row_index`, `TestGroupbyTransposePattern::test_groupby_transpose_sum_by_component`, `TestGroupbyTransposePattern::test_groupby_transpose_sum_by_species`, `TestIonDataStructure::test_ion_extraction_from_mcs_data`, `TestIonDataStructure::test_ion_mc_column_names`, `TestIonDataStructure::test_required_columns_present`, `TestLevelSpecificOperations::test_drop_with_level`, `TestLevelSpecificOperations::test_multiply_with_level_broadcasts`, `TestMultiIndexStructure::test_bfield_empty_species`, `TestMultiIndexStructure::test_datetime_index`, `TestMultiIndexStructure::test_density_empty_component`, `TestMultiIndexStructure::test_monotonic_increasing_index`, `TestMultiIndexStructure::test_multiindex_level_count`, `TestMultiIndexStructure::test_multiindex_level_names`, `TestMultiIndexStructure::test_no_duplicate_columns`, `TestReorderLevelsBehavior::test_reorder_levels_restores_canonical_order`, `TestReorderLevelsBehavior::test_sort_index_after_reorder`

**Pins in impacted tests**

- None.

**Target tests, written first as `pytest.mark.xfail(strict=True)`**

- None. The csv is read by no code (git grep 'csv.silso' over solarwindpy/ and tests/ is empty) and the test file guards no package code, so no behaviour changes and there is nothing for a target test to pin.

## D3 (F194)

Group 1, wave 1, author review: no.

**Targets**

- tests/test_import_aliases.py (delete)
- CHANGELOG.md (only if the author wants test-suite changes logged)

Both tests deleted. The plan's fallback (scope the scan to git ls-files, mirroring tests/test_public_imports.py:40) is moot under the decision.

**Impacted tests**: 2 (2 delete)

*delete* (2)

- `tests/test_import_aliases.py`: `test_only_np_pd_plt_mpl_mdates_aliases_are_used`, `test_the_scan_reads_the_package_and_finds_allowed_aliases`

**Pins in impacted tests**

- None.

**Target tests, written first as `pytest.mark.xfail(strict=True)`**

- None. Removes a test only. Note it currently fails on the untracked solarwindpy/plans/ (the working tree has it), which is F194's own point.

## D4 (F54)

Group 1, wave 1, author review: no.

**Targets**

- solarwindpy/examples/__init__.py lines 1-2 (Spent-When, Supersedes)
- solarwindpy/plotting/binned.py lines 1-2

No test reads either header. Neither Spent-When gate blocks stripping a header: the write gate binds new files only, and the commit gate binds additions only (spent_gate.py, spent_commit_gate.py docstrings). After D4 the two modules carry no declaration, like the other 49 package modules. /session:close's audit may list them, as it would those 49.

**Impacted tests**: 0 ()

**Pins in impacted tests**

- None.

**Target tests, written first as `pytest.mark.xfail(strict=True)`**

- No tracked solarwindpy/**/*.py module begins with a 'Spent-When:' line (git ls-files 'solarwindpy/*.py', read each first two lines). Fails today on the two modules.

## B1 (F78)

Group 6, wave 2, author review: no.

**Targets**

- solarwindpy/core/vector.py:Vector.__call__
- solarwindpy/core/tensor.py:Tensor.__call__

Untested today: zero coverage contexts reach Vector.__call__ or Tensor.__call__, and git grep finds no call form in tests. Vector and Tensor define no x/y/z or par/per attributes, so the fix is `self.data.xs(component, axis=1)` (or .loc) and not getattr. Keep .xs: CLAUDE.md forbids a deep copy in this path.

**Impacted tests**: 0 ()

**Pins in impacted tests**

- None.

**Target tests, written first as `pytest.mark.xfail(strict=True)`**

- For the example plasma's field, plasma.b(c) equals plasma.b.data.xs(c, axis=1) for c in x, y, z (pdt.assert_series_equal); same for velocity.
- For a species' thermal speed tensor, w(c) equals w.data.xs(c, axis=1) for c in par, per, scalar (the F78 call form `tensor('par')`).
- An unknown component raises KeyError whose message names the component.
- The returned Series shares memory with the source frame (np.shares_memory), per CLAUDE.md's .xs() view rule; this guards against a .copy() in the fix.

## B2 (F86)

Group 2, wave 3, author review: yes.

**Targets**

- solarwindpy/fitfunctions/core.py:FitFunction.residuals (governs: observed minus fitted)
- solarwindpy/fitfunctions/plots.py:FFPlot.residuals (delegates)
- solarwindpy/fitfunctions/plots.py:FFPlot.plot_residuals (draws the result)
- solarwindpy/fitfunctions/core.py:FitFunction.plotter / FFPlot.__init__ (the delegation mechanism)

Verified sign: on the F86 repro, fit.residuals()[3] = +0.873, fit.plotter.residuals()[3] = -0.873, and fit.plotter.residuals(robust=True)[3] = -0.873. least_squares minimizes `func(x) - ydata` (scipy _wrap_func), so `fit_result.fun` is model minus observed.

Author decision needed. If FitFunction.residuals governs, simple residuals flip sign. Robust residuals (`fun`) stay model minus observed unless they are also negated, and kind='both' would then overlay opposite signs. The trial below ran both ways.

Mechanism: FFPlot is built from (observations, y_fit, TeX_info, fit_result) and holds no handle on its FitFunction, and fitfunctions/core.py imports plots.py, so plots.py cannot import core.py (the acyclic_siblings contract). Options: pass FitFunction.residuals into FFPlot as a callable, or move the arithmetic into one function that both call, defined in plots.py or a new leaf module. Either one changes the tests' make_ffplot helper, which builds FFPlot directly.

Verified in the snapshot: flipping only the simple sign fails 8 test ids across 6 test functions (every update below except test_robust_residuals_are_the_fit_results_residual_vector). Negating robust as well adds test_residuals_return_an_ndarray_on_every_path[False-True] and test_robust_residuals_are_the_fit_results_residual_vector, which is therefore an update only if the author negates robust residuals (conditional). test_both_draws_simple_then_robust_residuals and test_residual_axes_carry_labels_scales_and_grid change on their robust lines too in that case.

The FitFunction.residuals tests in test_core.py and test_trend_fits_advanced.py are guards (verified): the governing side does not change.

**Impacted tests**: 40 (33 guard, 7 update)

*update* (7)

- `tests/fitfunctions/test_plots.py`: `test_both_draws_simple_then_robust_residuals`, `test_percent_residuals_are_nan_where_the_model_is_zero`, `test_residual_axes_carry_labels_scales_and_grid`, `test_residuals_return_an_ndarray_on_every_path`, `test_robust_residuals_are_the_fit_results_residual_vector`, `test_simple_residuals_are_model_minus_observation`, `test_stacked_plot_passes_keywords_through`

*guard* (33)

- `tests/fitfunctions/test_core.py`: `TestResidualsAllOptions::test_residuals_pct_handles_zero_fitted`, `TestResidualsAllOptions::test_residuals_pct_true`, `TestResidualsAllOptions::test_residuals_use_all_and_pct_together`, `TestResidualsAllOptions::test_residuals_use_all_true`
- `tests/fitfunctions/test_plots.py`: `test_an_ffplot_figure_renders_to_png`, `test_an_unknown_residual_kind_is_refused`, `test_both_lets_other_attribute_errors_through`, `test_both_skips_robust_residuals_when_the_fit_holds_none`, `test_caller_keywords_override_the_default_style_by_alias`, `test_each_plot_draws_its_pinned_default_style`, `test_plot_residuals_makes_its_figure_from_subplots_kwargs`, `test_residual_labels_keep_the_callers_label_whole`, `test_residuals_mark_every_tenth_of_the_used_points_decade`, `test_robust_residuals_in_percent_are_refused`, `test_stacked_plot_hides_the_fit_axes_x_ticks_on_free_axes`, `test_stacked_plot_is_a_3_to_1_fit_over_residual_layout`
- `tests/fitfunctions/test_trend_fits.py`: `test_plot_all_ffuncs`, `test_plot_all_ffuncs_titles_tell_in_trend_bins_from_the_others`, `test_plot_trend_and_resid_on_ffuncs_overlays_1d_fits`, `test_plot_trend_and_resid_on_ffuncs_passes_options_and_places_the_legend`, `test_plot_trend_fit_resid_defaults`, `test_plot_trend_fit_resid_draws_the_1d_centroids`, `test_plot_trend_fit_resid_options_and_unknown_keywords`, `test_trend_logx_fits_and_plots_against_ten_to_the_x`
- `tests/fitfunctions/test_trend_fits_advanced.py`: `TestPhase4Integration::test_complete_workflow`, `TestResidualsEnhancement::test_backward_compatibility`, `TestResidualsEnhancement::test_division_by_zero_handling`, `TestResidualsEnhancement::test_percentage_residuals`, `TestResidualsEnhancement::test_percentage_residuals_use_all`, `TestResidualsEnhancement::test_use_all_parameter_basic`, `TestResidualsEnhancement::test_use_all_parameter_no_constraints`, `TestTrendLogxPaths::test_plot_trend_and_resid_on_ffuncs_trend_logx`, `TestTrendLogxPaths::test_plot_trend_fit_resid_trend_logx`

**Pins in impacted tests**

- None.

**Target tests, written first as `pytest.mark.xfail(strict=True)`**

- For any fitted Line, fit.plotter.residuals(pct=p) equals fit.residuals(pct=p) for p in (False, True): identity, the one home.
- fit.plotter.residuals() equals observations.used.y minus fit(observations.used.x): observed minus fitted (fails today, because FFPlot gives the negative). The same relation for fit.residuals() already holds, so it is a guard, not an xfail.
- Percent residuals: fit.residuals(pct=True) equals 100 * fit.residuals() / fit(x_used), NaN where fit(x_used) == 0, for both callers.
- If the author negates robust residuals too: fit.plotter.residuals(robust=True) equals -fit_result.fun, so for linear loss and unit weights it equals the simple residuals (relation); with kind='both' the two drawn lines share a sign at every point.

## B3 (F105)

Group 4, wave 2, author review: no.

**Targets**

- solarwindpy/instabilities/verscharen2016.py:beta_ani_inst (docstring Examples: a=0.367, b=-0.408, c=0.011 and its printed output)

Docstring-only. The 23 coverage hits are the Eq. (5) tests in test_verscharen2016.py, all guards. The one impacted test is the doctest, which runs only in the CI doctest workflow. The correct row is AIC at -4: a=0.367, b=0.364, c=0.011 (insta_params, verified by printing it).

**Impacted tests**: 24 (23 guard, 1 update)

*update* (1)

- `solarwindpy/instabilities/verscharen2016.py`: `solarwindpy.instabilities.verscharen2016.beta_ani_inst (doctest, CI doctest workflow only)`

*guard* (23)

- `tests/instabilities/test_verscharen2016.py`: `test_beta_ani_inst_is_equation_5`, `test_color_norm_centres_each_stability_bin`, `test_colorbar_has_one_colour_and_one_labelled_tick_per_stability_bin`, `test_contours_are_equation_5_for_every_growth_rate`, `test_isotropic_plasma_below_the_fmw_fit_domain_is_stable`, `test_missing_beta_or_anisotropy_counts_as_stable`, `test_plot_contours_default_styles`, `test_plot_contours_draws_every_published_threshold_on_log_axes`, `test_plot_contours_fix_scale_false_keeps_caller_scales`, `test_plot_contours_style_kwargs_override_every_default`, `test_plot_gamma_draws_only_that_growth_rate`, `test_stability_condition_classifies_by_published_thresholds`, `test_stability_condition_thresholds_are_equation_5`, `test_stability_contours_figure_renders_to_png`, `test_stability_results_align_with_the_measurement_index`, `test_table_legend_rows_and_columns_describe_their_curves`, `test_threshold_at_unit_offset_is_one_plus_a`, `test_threshold_is_undefined_below_the_fit_offset`, `test_tk_kind_rejects_non_string_entries`, `test_tk_kind_rejects_unknown_instability`, `test_tk_kind_selects_instabilities_case_insensitively`, `test_undefined_threshold_is_stable_while_others_hold`, `test_user_visible_names_are_instability_growth_rate_and_stability`

**Pins in impacted tests**

- None.

**Target tests, written first as `pytest.mark.xfail(strict=True)`**

- The (a, b, c) triple in beta_ani_inst's doctest is a row of insta_params (parse the call from beta_ani_inst.__doc__, compare with insta_params rows): a cited reference value, Verscharen et al. (2016), :cite:`Verscharen2016a`, doi:10.3847/0004-637x/831/2/128 (from docs/source/solarwindpy.bib).
- The doctest's printed array equals beta_ani_inst(beta, **that row) (relation between docstring and code). The doctest itself runs only in .github/workflows/doctest_validation.yml (pytest --doctest-modules solarwindpy), not in the default suite.

## B4 (F109)

Group 4, wave 3, author review: no.

**Targets**

- solarwindpy/instabilities/verscharen2016.py:StabilityCondition.fill (-9999.0 to -9999)
- solarwindpy/instabilities/verscharen2016.py:StabilityCondition._calc_stability_bin (dtype)

Verified in the snapshot: with fill = -9999, stability_bin is int64 (with a NaN input row too), and all 113 tests under tests/instabilities pass, so every label is guard.

Excluded as grep false positives: 9 plotting tests where 9999 is a clip value, unrelated to stability_bin.

**Impacted tests**: 10 (10 guard)

*guard* (10)

- `tests/instabilities/test_verscharen2016.py`: `test_color_norm_centres_each_stability_bin`, `test_colorbar_has_one_colour_and_one_labelled_tick_per_stability_bin`, `test_isotropic_plasma_below_the_fmw_fit_domain_is_stable`, `test_missing_beta_or_anisotropy_counts_as_stable`, `test_stability_condition_classifies_by_published_thresholds`, `test_stability_condition_thresholds_are_equation_5`, `test_stability_results_align_with_the_measurement_index`, `test_threshold_at_unit_offset_is_one_plus_a`, `test_undefined_threshold_is_stable_while_others_hold`, `test_user_visible_names_are_instability_growth_rate_and_stability`

*Excluded grep false positives* (9): `tests/plotting/test_agg_plot.py::TestCut::test_clip_data_moves_an_outlier_to_the_bin_of_its_clipped_value`, `tests/plotting/test_agg_plot.py::TestNbinsAndEdges::test_out_of_memory_count_follows_clip_data`, `tests/plotting/test_binned_data.py::TestClipAxes::test_spiral_clips_only_the_axes_it_names`, `tests/plotting/test_binned_data.py::TestCodes::test_clip_bins_an_outlier_at_its_quantile`, `tests/plotting/test_data_path_defects.py::test_an_infinite_value_no_longer_makes_the_upper_quantile_nan`, `tests/plotting/test_data_path_defects.py::test_clip_quantiles_ignore_infinities_and_clip_them_to_the_finite_quantiles`, `tests/plotting/test_data_path_defects.py::test_one_tail_clip_leaves_the_other_infinity`, `tests/plotting/test_spiral.py::TestCountsAndBinNumbers::test_bin_number_is_the_index_of_the_containing_cell`, `tests/plotting/test_spiral.py::TestMeshEqualsBruteForce::test_bin_id_is_the_row_of_the_leaf_holding_each_point`

**Pins in impacted tests**

- None.

**Target tests, written first as `pytest.mark.xfail(strict=True)`**

- pd.api.types.is_integer_dtype(sc.stability_bin) for an input with stable, unstable and NaN rows.
- sc.fill is an int, equals the author-decided placeholder -9999 (cite the Phase C decision), and is not a key of stability_map (so the placeholder never collides with a real bin).

## B5 (F136)

Group 8, wave 2, author review: yes.

**Targets**

- solarwindpy/tools/__init__.py:swap_protons (post-swap check, lines 103-106: n_p2 / n_p2 becomes n_p2 / n_p1)

Verified in the snapshot: with the check corrected to n_p2 / n_p1, all 19 tests/tools tests pass. The check cannot fire on frames swap_protons builds, because the swap enforces the invariant. So the behaviour change shows only if the swap logic regresses. Flagged anyway because it turns a dead assert into a live one on user data. Rows where n_p1 is 0 and n_p2 is 0 give NaN, which dropna removes.

**Impacted tests**: 7 (7 guard)

*guard* (7)

- `tests/tools/test_tools.py`: `TestSwapProtons::test_beam_is_never_denser_than_core_afterwards`, `TestSwapProtons::test_default_logger_does_not_accumulate_handlers`, `TestSwapProtons::test_given_logger_receives_one_info_record_with_the_count`, `TestSwapProtons::test_input_frame_is_not_modified`, `TestSwapProtons::test_mask_and_flag_column_mark_exactly_the_swapped_rows`, `TestSwapProtons::test_output_keeps_mcs_level_names_so_it_can_be_swapped_again`, `TestSwapProtons::test_swaps_every_p1_p2_quantity_where_n_p2_exceeds_n_p1`

**Pins in impacted tests**

- None.

**Target tests, written first as `pytest.mark.xfail(strict=True)`**

- The fixed check cannot fire on any frame swap_protons itself produces, so it needs a seam: extract the post-condition into one helper (e.g. _check_core_dominates(new_data)) and test that it raises on a frame where n_p2 > n_p1 at one row, and passes where n_p2 == n_p1 and where either density is NaN.
- Existing guard kept as is: test_beam_is_never_denser_than_core_afterwards already asserts the same invariant from outside.

## B6 (F161)

Group 5, wave 4, author review: no.

**Targets**

- solarwindpy/solar_activity/plots.py:SSNPlot._format_axis (set_ylim(0, 200))
- solarwindpy/solar_activity/sunspot_number/sidc.py:SIDC.plot_on_colorbar (line 537, the round-up rule to share)

Relabelled guard, not update: test_ssn_axis_spans_zero_to_two_hundred passes unchanged under the round-up rule, because its fixture peaks at 169 and rounds up to 200. Its name, docstring and ON FAILURE line describe the old fixed range and should be reworded in the B6 commit. Verified in the snapshot: with the rule applied, all tests/solar_activity tests pass. So the xfail targets need a peak above 200 and a peak below 100.

CLAUDE.md requires one shared helper at the second copy. The rule lives in sidc.py:537 today. SSNPlot is in solar_activity/plots.py, which already receives a SIDC. The helper belongs in sunspot_number/sidc.py, and plots.py should call it through the indicator it holds (e.g. a SIDC method), not through a new import. Check `lint-imports` (acyclic_siblings) before choosing a module-level import.

Excluded as grep false positives: 6 tests (fitfunctions and plotting) that call get_ylim on unrelated axes.

**Impacted tests**: 12 (12 guard)

*guard* (12)

- `tests/solar_activity/sunspot_number/test_sidc.py`: `test_plot_on_colorbar_draws_the_requested_span`, `test_plot_on_colorbar_handles_a_low_activity_window`, `test_plot_on_colorbar_rounds_a_peak_of_140_up_to_200`
- `tests/solar_activity/test_plots.py`: `test_auto_path_is_built_from_class_labels_and_scales`, `test_axes_are_labelled_with_time_and_the_indicator`, `test_date_ticks_are_labelled_by_year`, `test_explicit_path_is_used_with_or_without_scales`, `test_make_plot_without_axes_draws_on_a_new_figure`, `test_plasma_index_after_the_series_leaves_nothing_to_plot`, `test_plasma_index_trims_to_data_from_its_earliest_time`, `test_ssn_axis_spans_zero_to_two_hundred`, `test_ssn_plot_shows_the_whole_ssn_series`

*Excluded grep false positives* (6): `tests/fitfunctions/test_plots.py::test_residual_axes_carry_labels_scales_and_grid`, `tests/plotting/test_hist2d_plotting.py::TestJointPlot::test_marginal_panels_share_the_central_axes`, `tests/plotting/test_scatter.py::test_axis_limits_hug_the_plotted_points`, `tests/plotting/test_spiral.py::TestMakePlotOptions::test_axes_limits_span_the_mesh`, `tests/plotting/test_tools.py::TestBuildAxArrayWithCommonColorbar::test_defaults_are_one_panel_with_shared_axes`, `tests/plotting/test_tools.py::TestBuildAxArrayWithCommonColorbar::test_sharex_and_sharey_link_limits_only_when_requested`

**Pins in impacted tests**

- None.

**Target tests, written first as `pytest.mark.xfail(strict=True)`**

- For an SSN series peaking above 200, SSNPlot's y upper limit equals the shared round-up of the peak, and is >= the peak (fails today: fixed 200 clips it).
- For a quiet series peaking below 100, the upper limit is 100, the rule's floor (fails today: 200).
- Within the two series above (peak above 200, peak below 100), SSNPlot's upper limit equals the scale plot_on_colorbar uses for the same series. Any peak between 100 and 200, including the existing 169 fixture, would XPASS, so it must not be used.

## B7 (F154)

Group 5, wave 2, author review: no.

**Targets**

- solarwindpy/solar_activity/sunspot_number/sidc.py:SIDCLoader.download_data (line 266: + 'std_error' becomes + '_std_error')

Verified in the snapshot: renaming to `_std_error` passes all tests/solar_activity tests, so all 21 are guards. The hemispheric test matches by startswith/endswith (F154). Downstream: the loader caches one CSV per day (DataLoader.load_data reads <data_path>/<today>.csv), so a cached file written before the change keeps the old names until the next download. A same-day cache will therefore show the old column names.

**Impacted tests**: 21 (21 guard)

*guard* (21)

- `tests/solar_activity/sunspot_number/test_sidc.py`: `test_stale_cache_downloads_the_silso_series_and_loads_it`
- `tests/solar_activity/sunspot_number/test_sidc_loader.py`: `test_download_data_daily_round_trip`, `test_download_data_hemispheric_standard_errors`, `test_download_data_monthly_round_trip`, `test_download_data_propagates_the_missing_sentinel_to_nan`, `test_download_data_removes_the_superseded_cache_file`, `test_download_data_tolerates_a_missing_previous_cache`, `test_download_data_yearly_round_trip`
- `tests/solar_activity/test_plots.py`: `test_an_absent_column_is_reported_by_name`, `test_auto_path_is_built_from_class_labels_and_scales`, `test_axes_are_labelled_with_time_and_the_indicator`, `test_date_ticks_are_labelled_by_year`, `test_explicit_path_is_used_with_or_without_scales`, `test_log_flags_set_the_matching_axis_scale`, `test_make_plot_draws_the_series_against_date_numbers`, `test_make_plot_without_axes_draws_on_a_new_figure`, `test_plasma_index_after_the_series_leaves_nothing_to_plot`, `test_plasma_index_trims_to_data_from_its_earliest_time`, `test_ssn_axis_spans_zero_to_two_hundred`, `test_ssn_plot_shows_the_whole_ssn_series`, `test_the_fixture_series_is_the_one_chosen`

**Pins in impacted tests**

- None.

**Target tests, written first as `pytest.mark.xfail(strict=True)`**

- For a hemispheric download, the written frame has a column f'{h}_std_error' for each h in total, north, south, and each equals f'{h}_std' / sqrt(n_{h}) (relation; the existing startswith/endswith test cannot see the name).

## B8 (F80)

Group 7, wave 2, author review: yes.

**Targets**

- solarwindpy/core/spacecraft.py:Spacecraft.set_frame_name
- solarwindpy/core/spacecraft.py:Spacecraft.distance2sun (frame branches GSE, HCI)
- solarwindpy/core/spacecraft.py: one module-level table of supported frames that both methods read (new)

Definition of "supports", from the code: frames are the ones distance2sun converts (GSE, HCI, spacecraft.py:160 and :173), which are also the frames the plotting labels know (plotting/labels/base.py:122, :240). Keep them in one module-level table that set_frame_name and distance2sun both read. Spacecraft name: nothing in the package branches on it (git grep finds it only in docstrings and examples). ICMECAT's SPACECRAFT_NAMES cannot be the source, because core sits below solar_activity in the layers contract. So the author picks: (a) any non-empty name, which is my recommendation because the name is identification only; or (b) a core-level list.

Coverage: 62 tests reach set_frame_name because every Spacecraft construction calls it. All use PSP or WIND with HCI or GSE, so all are guards (inferred: B8 only widens what is accepted, and no test asserts a rejection).

**Impacted tests**: 62 (62 guard)

*guard* (62)

- `tests/core/test_alfvenic_turbulence.py`: `test_raffaella_version_converts_gse_to_rtn_with_hand_computed_values`, `test_raffaella_version_without_a_spacecraft_raises_value_error`
- `tests/core/test_base.py`: `test_a_child_whose_times_differ_from_its_parents_is_checked`, `test_a_plasma_species_joined_by_plus_raises_value_error_naming_it`, `test_a_standalone_object_refuses_missing_times`, `test_a_standalone_vector_or_tensor_out_of_order_warns_then_sorts`, `test_a_vector_built_directly_on_a_non_datetime_index_warns`, `test_a_vector_on_an_index_that_cannot_be_ordered_warns_and_is_kept`, `test_an_ion_a_plasma_built_still_checks_new_data`, `test_an_unrelated_type_error_while_sorting_is_not_swallowed`, `test_objects_with_differently_labelled_data_are_unequal`, `test_one_non_datetime_index_logs_one_warning_across_a_plasma_build`, `test_one_out_of_order_problem_logs_exactly_one_warning`
- `tests/core/test_plasma.py`: `TestPlasmaAlpha::test_spacecraft_in_plasma`, `TestPlasmaAlphaP1::test_nc_with_spacecraft`, `TestPlasmaAlphaP1::test_spacecraft_in_plasma`, `TestPlasmaAlphaP1P2::test_nc_with_spacecraft`, `TestPlasmaAlphaP1P2::test_spacecraft_in_plasma`, `TestPlasmaAlphaP2::test_nc_with_spacecraft`, `TestPlasmaAlphaP2::test_spacecraft_in_plasma`, `TestPlasmaP1::test_spacecraft_in_plasma`, `TestPlasmaP1P2::test_nc_with_spacecraft`, `TestPlasmaP1P2::test_spacecraft_in_plasma`, `TestPlasmaP2::test_spacecraft_in_plasma`, `test_auxiliary_data_levels_out_of_order_raise_value_error`, `test_auxiliary_data_with_wrong_level_names_raises_value_error`, `test_auxiliary_index_differing_at_one_row_raises_value_error_naming_it`, `test_data_that_is_not_a_dataframe_raise_type_error_naming_the_type`, `test_drop_species_keeps_shared_and_remaining_species_auxiliary_columns`, `test_drop_species_keeps_the_spacecraft`, `test_missing_attribute_raises_attribute_error_naming_it`, `test_nc_defaults_to_both_species`, `test_plasma_data_column_levels_may_come_in_any_order`, `test_plasma_data_with_wrong_level_names_raises_value_error`, `test_plasma_spacecraft_and_auxiliary_data_stay_aligned`, `test_set_auxiliary_data_refuses_missing_timestamps`, `test_set_auxiliary_data_reorders_the_plasma_times_given_in_another_order`, `test_set_data_refuses_missing_timestamps`, `test_set_data_refuses_out_of_order_data_while_frames_are_attached`, `test_set_data_sorts_out_of_order_data_with_one_warning`, `test_setters_refuse_a_mismatched_index_with_value_error`, `test_setters_refuse_a_one_row_frame_naming_both_lengths`, `test_spacecraft_and_auxiliary_data_are_sorted_with_the_plasma`, `test_spacecraft_with_wrong_level_names_raises_value_error`, `test_species_string_with_whitespace_is_unavailable`
- `tests/core/test_plasma_io.py`: `test_load_from_file_keeps_only_rows_between_start_and_stop`, `test_load_from_file_loads_only_the_species_passed`, `test_load_from_file_needs_spacecraft_name_and_frame`, `test_load_from_file_passes_extra_keywords_to_plasma`, `test_save_applies_each_modifier_function_before_writing`, `test_save_rejects_a_modifier_that_is_not_a_function`, `test_save_then_load_round_trips_data_spacecraft_and_auxiliary_data`, `test_save_writes_data_spacecraft_and_aux_at_the_default_keys`
- `tests/core/test_spacecraft.py`: `TestPSP::test_data`, `TestWind::test_position`, `test_an_unknown_frame_or_name_raises_naming_it`, `test_data_that_is_not_a_dataframe_raise_type_error_naming_the_type`, `test_out_of_order_spacecraft_data_warn_once_then_sort`, `test_spacecraft_refuses_missing_timestamps`
- `tests/test_examples.py`: `test_load_plasma_holds_the_example_species_rows_and_spacecraft`, `test_plasma_logs_each_optional_input_not_passed`, `test_plasma_no_longer_accepts_log_plasma_stats`

**Pins in impacted tests**

- None.

**Target tests, written first as `pytest.mark.xfail(strict=True)`**

- Every frame in the supported-frame table is accepted by set_frame_name and gives a finite distance2sun on the example position (relation between the two methods: they cannot drift apart).
- A frame outside the table raises NotImplementedError whose message lists the supported frames.
- Name: depends on the author's ruling. If names are unrestricted, Spacecraft(data, 'ACE', 'GSE') constructs and .name == 'ACE' (fails today). If a core-level list, every listed name constructs.

## B9 (F99)

Group 2, wave 2, author review: no.

**Targets**

- solarwindpy/fitfunctions/plots.py lines 23-24 (AxesLabels, LogAxes namedtuples) become `from ..plotting.base import AxesLabels, LogAxes`; names stay in plots.__all__

Verified in the snapshot: replacing the two namedtuples with the plotting.base import passes all 790 tests in tests/fitfunctions and tests/plotting/test_base.py. The definitions are field-for-field identical (plotting/base.py:30, :35). The names stay in fitfunctions.plots.__all__, so `from solarwindpy.fitfunctions.plots import AxesLabels` keeps working. Their __module__ becomes solarwindpy.plotting.base.

**Impacted tests**: 17 (17 guard)

*guard* (17)

- `tests/fitfunctions/test_plots.py`: `test_properties_return_what_was_set`, `test_set_labels_keeps_the_labels_it_is_not_given`, `test_set_log_changes_only_the_axes_it_is_given`
- `tests/fitfunctions/test_trend_fits.py`: `test_labels_instance_and_update`
- `tests/plotting/test_base.py`: `test_omitted_last_field_takes_its_neutral_default`, `test_set_labels_changes_only_the_labels_passed`, `test_set_labels_rejects_unknown_keywords_naming_each`, `test_set_log_coerces_to_bool_and_none_keeps_the_current_value`, `test_set_log_of_one_axis_keeps_the_other_logarithmic`
- `tests/plotting/test_binned_data.py`: `TestPassthrough::test_an_explicit_value_equal_to_the_binned_datas_is_accepted`, `TestPassthrough::test_log_is_inherited_per_column_by_name`, `TestPassthrough::test_without_a_binned_data_none_means_linear_and_unclipped`
- `tests/plotting/test_data_path_defects.py`: `test_set_log_cannot_change_a_binned_axis_of_a_built_hist2d`, `test_set_log_cannot_change_an_axis_of_a_built_spiral`, `test_set_log_cannot_change_x_of_a_built_hist1d_but_may_change_y`, `test_set_log_repeating_the_built_setting_is_allowed`
- `tests/plotting/test_scatter.py`: `test_new_scatter_has_linear_axes_and_default_labels`

**Pins in impacted tests**

- None.

**Target tests, written first as `pytest.mark.xfail(strict=True)`**

- solarwindpy.fitfunctions.plots.AxesLabels is solarwindpy.plotting.base.AxesLabels, and likewise LogAxes (identity; fails today, the two are distinct classes).

## B10 (F135)

Group 3, wave 2, author review: no.

**Targets**

- solarwindpy/fitfunctions/gaussians.py:GaussianLn.normal_parameters (docstring summary and math only)

Docstring-only; all guard. The impacted test test_tex_info_reports_normal_parameters_only_when_asked carries two AI-file pins (printed(1.7246), printed(0.5292)), so by the AI-file rule it is labelled fragile. B10 does not require touching it. GaussianLn.normal_parameters repeats tools.normal_parameters (F135), which CLAUDE.md's extract-at-second-copy rule covers. That is outside B10's decided scope.

**Impacted tests**: 10 (1 fragile, 9 guard)

*fragile* (1)

- `tests/fitfunctions/test_gaussians.py`: `TestGaussianLn::test_tex_info_reports_normal_parameters_only_when_asked`

*guard* (9)

- `tests/fitfunctions/test_gaussians.py`: `TestGaussianLn::test_flag_set_before_the_fit_reaches_the_annotation`, `TestGaussianLn::test_normal_parameters_calculation`
- `tests/tools/test_tools.py`: `TestNormalParameters::test_base_e_is_the_default`, `TestNormalParameters::test_invalid_base_raises_value_error`, `TestNormalParameters::test_matches_scipy_lognorm_mean_and_std`, `TestNormalParameters::test_other_base_matches_scipy_lognorm_scaled_by_ln_base`, `TestNormalParameters::test_sample_mean_of_base_b_lognormal_matches_mu`, `TestNormalParameters::test_scalar_inputs_unpack_as_mu_then_sigma`, `TestNormalParameters::test_zero_log_width_is_a_point_mass_at_e_to_the_m`

**Pins in impacted tests**

- `tests/fitfunctions/test_gaussians.py:270` (AI-file, line commit e3d69dbd): `assert mu == printed(1.7246, decimals=4)`
- `tests/fitfunctions/test_gaussians.py:271` (AI-file, line commit e3d69dbd): `assert sigma == printed(0.5292, decimals=4)`

**Target tests, written first as `pytest.mark.xfail(strict=True)`**

- None recommended: a docstring reword changes no behaviour, and a test on docstring wording would be the brittle kind. The values are guarded by test_normal_parameters_calculation. If the author wants one: the summary line names the mean and standard deviation of the log-normal variable.

## B11 (F143)

Group 5, wave 3, author review: no.

**Targets**

- solarwindpy/solar_activity/base.py:ActivityIndicator.interpolate_data (abstract, becomes interpolate_data(self, target_index))
- solarwindpy/solar_activity/base.py:ActivityIndicator._interpolate (new concrete engine, the current body)
- solarwindpy/solar_activity/sunspot_number/sidc.py:SIDC.interpolate_data (calls self._interpolate; keeps key='ssn')
- solarwindpy/solar_activity/sunspot_number/sidc.py line 494 (error message naming interpolate_data)

Verified in the snapshot: making the abstract interpolate_data(self, target_index) and moving the body to _interpolate fails exactly the four test_base.py interpolation tests. Their stub Indicator overrides interpolate_data(source_data, target_index) and calls super. They become calls to _interpolate. The 11 SIDC tests are guards.

test_narrow_normalized_bands_touch_without_overlapping is labelled fragile by the AI-file pin rule (exact(np.arange(10)/10 - 0.05), exact(0.95)). The values look derived from the band width, so the author may judge them sourced.

**Impacted tests**: 15 (1 fragile, 10 guard, 4 update)

*update* (4)

- `tests/solar_activity/test_base.py`: `test_interpolation_blanks_targets_outside_the_source_span`, `test_interpolation_handles_each_column_and_keeps_the_result`, `test_interpolation_refuses_a_source_with_nans`, `test_interpolation_reproduces_a_straight_line`

*fragile* (1)

- `tests/solar_activity/sunspot_number/test_sidc.py`: `test_narrow_normalized_bands_touch_without_overlapping`

*guard* (10)

- `tests/solar_activity/sunspot_number/test_sidc.py`: `test_interpolate_data_defaults_to_the_ssn_column`, `test_interpolate_data_does_not_extrapolate`, `test_interpolate_data_recovers_a_linear_ramp`, `test_interpolate_data_skips_a_missing_month`, `test_normalized_bands_accept_widths_below_one_only`, `test_run_normalization_also_normalizes_the_interpolated_series`, `test_ssn_bands_contain_the_values_they_label`, `test_ssn_bands_default_to_half_width_two_centred_on_zero`, `test_ssn_bands_for_a_column_never_interpolated_raise_key_error`, `test_ssn_bands_of_an_all_zero_series_are_empty`

**Pins in impacted tests**

- `tests/solar_activity/sunspot_number/test_sidc.py:912` (AI-file, line commit fd495d28): `assert intervals.left.to_numpy() == exact(np.arange(10) / 10 - 0.05)`
- `tests/solar_activity/sunspot_number/test_sidc.py:913` (AI-file, line commit fd495d28): `assert intervals.right[-1] == exact(0.95)`

**Target tests, written first as `pytest.mark.xfail(strict=True)`**

- The abstract interpolate_data's parameters (inspect.signature) are a prefix of SIDC.interpolate_data's: ['self', 'target_index'] (fails today: ['self', 'source_data', 'target_index']).
- SIDC(...).interpolate_data(t) equals ActivityIndicator._interpolate(sidc.data['ssn'].dropna(), t) (relation; _interpolate does not exist today).

## M1 (F59, F63, F66 (+ raffaella polarity, cross_helicity: new in phaseA-missing-data.md))

Group 7, wave 3, author review: yes.

**Targets**

- solarwindpy/core/plasma.py:Plasma.anisotropy lines 1269 (groupby prod) and 1271 (product): skipna=False on the par/per product
- solarwindpy/core/spacecraft.py:Spacecraft.distance2sun line 182: skipna=False
- solarwindpy/core/alfvenic_turbulence.py:AlfvenicTurbulence.e_plus (200), e_minus (211), kinetic_energy (222), magnetic_energy (235), cross_helicity (283): skipna=False
- solarwindpy/core/alfvenic_turbulence.py:AlfvenicTurbulence.set_data raffaella polarity (lines 408-413): skipna=False
- docs/source/missing_data.rst: one sentence extending P1 to objects without a species axis (phaseA decision D2)

Verified in the snapshot: skipna=False at all nine reduction sites passes all 876 tests under tests/core, so all 118 impacted tests are guards. The reason: the example plasma has no NaN (verified: 0 missing in data and in spacecraft), and the raffaella test asserts only rows 0 to 3, while the polarity change lands on row 4.

Downstream results change: Plasma.nc reads spacecraft.distance2sun (plasma.py:1832), so collisional age becomes NaN where a position component is missing. The raffaella bfield becomes NaN at rows where v_y or b_y is missing, because the polarity is NaN there. Anisotropy with no species present goes from 1.0 to NaN, and species-partial totals stay partial (phaseA-missing-data.md, verified table).

pandas 3.1.0 DataFrameGroupBy.prod accepts skipna (verified via inspect.signature), so the multi-species branch can use skipna=False. min_count=2 is the alternative that also works on older pandas.

Placement: Plasma.anisotropy's target tests belong beside test_anisotropy in tests/core/test_plasma.py, an author-created file. Ask before writing there, or put them in a new tests/core/test_missing_data.py.

Line numbers are as of 64379c6f; phaseA-missing-data.md's are as of 9ef459ed (plasma.py moved after the entropy removal).

**Impacted tests**: 118 (118 guard)

*guard* (118)

- `tests/core/test_alfvenic_turbulence.py`: `AlfvenicTrubulenceTestBase::test_cross_helicity`, `AlfvenicTrubulenceTestBase::test_e_minus`, `AlfvenicTrubulenceTestBase::test_e_plus`, `AlfvenicTrubulenceTestBase::test_magnetic_energy`, `AlfvenicTrubulenceTestBase::test_normalized_cross_helicity`, `TestAlfvenicTrubulenceAlphaP1::test_alfven_ratio`, `TestAlfvenicTrubulenceAlphaP1::test_cross_helicity`, `TestAlfvenicTrubulenceAlphaP1::test_e_minus`, `TestAlfvenicTrubulenceAlphaP1::test_e_plus`, `TestAlfvenicTrubulenceAlphaP1::test_elsasser_ratio`, `TestAlfvenicTrubulenceAlphaP1::test_kinetic_energy`, `TestAlfvenicTrubulenceAlphaP1::test_magnetic_energy`, `TestAlfvenicTrubulenceAlphaP1::test_normalized_cross_helicity`, `TestAlfvenicTrubulenceAlphaP1::test_normalized_residual_energy`, `TestAlfvenicTrubulenceAlphaP1::test_residual_energy`, `TestAlfvenicTrubulenceAlphaP1::test_sigma_r`, `TestAlfvenicTrubulenceAlphaP1::test_total_energy`, `TestAlfvenicTrubulenceAlphaP1P2::test_alfven_ratio`, `TestAlfvenicTrubulenceAlphaP1P2::test_cross_helicity`, `TestAlfvenicTrubulenceAlphaP1P2::test_e_minus`, `TestAlfvenicTrubulenceAlphaP1P2::test_e_plus`, `TestAlfvenicTrubulenceAlphaP1P2::test_elsasser_ratio`, `TestAlfvenicTrubulenceAlphaP1P2::test_kinetic_energy`, `TestAlfvenicTrubulenceAlphaP1P2::test_magnetic_energy`, `TestAlfvenicTrubulenceAlphaP1P2::test_normalized_cross_helicity`, `TestAlfvenicTrubulenceAlphaP1P2::test_normalized_residual_energy`, `TestAlfvenicTrubulenceAlphaP1P2::test_residual_energy`, `TestAlfvenicTrubulenceAlphaP1P2::test_sigma_r`, `TestAlfvenicTrubulenceAlphaP1P2::test_total_energy`, `TestAlfvenicTrubulenceAlphaP2::test_alfven_ratio`, `TestAlfvenicTrubulenceAlphaP2::test_cross_helicity`, `TestAlfvenicTrubulenceAlphaP2::test_e_minus`, `TestAlfvenicTrubulenceAlphaP2::test_e_plus`, `TestAlfvenicTrubulenceAlphaP2::test_elsasser_ratio`, `TestAlfvenicTrubulenceAlphaP2::test_kinetic_energy`, `TestAlfvenicTrubulenceAlphaP2::test_magnetic_energy`, `TestAlfvenicTrubulenceAlphaP2::test_normalized_cross_helicity`, `TestAlfvenicTrubulenceAlphaP2::test_normalized_residual_energy`, `TestAlfvenicTrubulenceAlphaP2::test_residual_energy`, `TestAlfvenicTrubulenceAlphaP2::test_sigma_r`, `TestAlfvenicTrubulenceAlphaP2::test_total_energy`, `TestAlfvenicTrubulenceP1::test_alfven_ratio`, `TestAlfvenicTrubulenceP1::test_cross_helicity`, `TestAlfvenicTrubulenceP1::test_e_minus`, `TestAlfvenicTrubulenceP1::test_e_plus`, `TestAlfvenicTrubulenceP1::test_elsasser_ratio`, `TestAlfvenicTrubulenceP1::test_kinetic_energy`, `TestAlfvenicTrubulenceP1::test_magnetic_energy`, `TestAlfvenicTrubulenceP1::test_normalized_cross_helicity`, `TestAlfvenicTrubulenceP1::test_normalized_residual_energy`, `TestAlfvenicTrubulenceP1::test_residual_energy`, `TestAlfvenicTrubulenceP1::test_sigma_r`, `TestAlfvenicTrubulenceP1::test_total_energy`, `TestAlfvenicTrubulenceP1P2::test_alfven_ratio`, `TestAlfvenicTrubulenceP1P2::test_cross_helicity`, `TestAlfvenicTrubulenceP1P2::test_e_minus`, `TestAlfvenicTrubulenceP1P2::test_e_plus`, `TestAlfvenicTrubulenceP1P2::test_elsasser_ratio`, `TestAlfvenicTrubulenceP1P2::test_kinetic_energy`, `TestAlfvenicTrubulenceP1P2::test_magnetic_energy`, `TestAlfvenicTrubulenceP1P2::test_normalized_cross_helicity`, `TestAlfvenicTrubulenceP1P2::test_normalized_residual_energy`, `TestAlfvenicTrubulenceP1P2::test_residual_energy`, `TestAlfvenicTrubulenceP1P2::test_sigma_r`, `TestAlfvenicTrubulenceP1P2::test_total_energy`, `TestAlfvenicTrubulenceP2::test_alfven_ratio`, `TestAlfvenicTrubulenceP2::test_cross_helicity`, `TestAlfvenicTrubulenceP2::test_e_minus`, `TestAlfvenicTrubulenceP2::test_e_plus`, `TestAlfvenicTrubulenceP2::test_elsasser_ratio`, `TestAlfvenicTrubulenceP2::test_kinetic_energy`, `TestAlfvenicTrubulenceP2::test_magnetic_energy`, `TestAlfvenicTrubulenceP2::test_normalized_cross_helicity`, `TestAlfvenicTrubulenceP2::test_normalized_residual_energy`, `TestAlfvenicTrubulenceP2::test_residual_energy`, `TestAlfvenicTrubulenceP2::test_sigma_r`, `TestAlfvenicTrubulenceP2::test_total_energy`, `TestPlasmaAlpha::test_alfven_ratio`, `TestPlasmaAlpha::test_cross_helicity`, `TestPlasmaAlpha::test_e_minus`, `TestPlasmaAlpha::test_e_plus`, `TestPlasmaAlpha::test_elsasser_ratio`, `TestPlasmaAlpha::test_kinetic_energy`, `TestPlasmaAlpha::test_magnetic_energy`, `TestPlasmaAlpha::test_normalized_cross_helicity`, `TestPlasmaAlpha::test_normalized_residual_energy`, `TestPlasmaAlpha::test_residual_energy`, `TestPlasmaAlpha::test_sigma_r`, `TestPlasmaAlpha::test_total_energy`, `test_raffaella_version_converts_gse_to_rtn_with_hand_computed_values`, `test_raffaella_version_without_a_spacecraft_raises_value_error`
- `tests/core/test_plasma.py`: `PlasmaTestBase::test_anisotropy`, `PlasmaTestBase::test_nc_with_spacecraft`, `TestPlasmaAlpha::test_anisotropy`, `TestPlasmaAlphaP1::test_anisotropy`, `TestPlasmaAlphaP1::test_nc_with_spacecraft`, `TestPlasmaAlphaP1P2::test_anisotropy`, `TestPlasmaAlphaP1P2::test_nc_with_spacecraft`, `TestPlasmaAlphaP2::test_anisotropy`, `TestPlasmaAlphaP2::test_nc_with_spacecraft`, `TestPlasmaP1::test_anisotropy`, `TestPlasmaP1P2::test_anisotropy`, `TestPlasmaP1P2::test_nc_with_spacecraft`, `TestPlasmaP2::test_anisotropy`, `test_nc_defaults_to_both_species`
- `tests/core/test_spacecraft.py`: `SpacecraftTestBase::test_distance2sun`, `TestPSP::test_distance2sun`, `TestWind::test_distance2sun`, `test_out_of_order_spacecraft_data_warn_once_then_sort`
- `tests/instabilities/test_verscharen2016.py`: `test_threshold_at_unit_offset_is_one_plus_a`
- `tests/plotting/labels/test_special.py`: `TestDistance2Sun::test_properties`, `test_distance2sun_unknown_units_error_names_them`
- `tests/plotting/test_binned_data.py`: `TestCodesEqualPandasCut::test_masked_rows_are_minus_one_and_kept_rows_match_pandas_cut`, `TestMask::test_rows_outside_the_mask_get_code_minus_one`
- `tests/plotting/test_data_path_defects.py`: `test_binned_data_codes_an_infinite_logged_value_minus_one_when_clipped`
- `tests/plotting/test_hist1d.py`: `TestMakePlot::test_errorbars_span_first_aggregate_plus_minus_second`, `test_transposed_window_edges_sit_at_value_minus_and_plus_error`
- `tests/plotting/test_spiral.py`: `test_top_edge_is_the_largest_value_plus_one_percent_of_its_size`

**Pins in impacted tests**

- None.

**Target tests, written first as `pytest.mark.xfail(strict=True)`**

- Plasma.anisotropy('p1') is NaN where p1 is masked, and equals plasma.p1.anisotropy at every row (relation to Ion.anisotropy, which already has skipna=False).
- Plasma.anisotropy('a', 'p1') column s equals plasma.<s>.anisotropy for each s (same relation, multi-species branch).
- Plasma.anisotropy('a+p1') is NaN at a row where no species is present (P3; today 1.0, the empty product).
- Guard, separate test (it passes on HEAD): Plasma.anisotropy('a+p1') stays partial over species, so where p1 is masked it equals the alpha-only value (P2). Kept apart so it cannot hide inside the xfail.
- Spacecraft.distance2sun is NaN exactly where position.mag is NaN, and in HCI equals position.mag times Rs over units.distance2sun (relation to Vector.mag).
- Each AlfvenicTurbulence energy is NaN where any component of its vector is NaN, and equals 0.5 * that vector's squared magnitude with skipna=False elsewhere; cross_helicity is NaN where a component of v or b is NaN.
- A new strict-xfail test on the same _gse_inputs fixture: at row 4 (v_T already NaN) polarity and bfield are NaN. Verified in the snapshot: on HEAD polarity[4] is 0.0 and bfield[4] is finite; with skipna=False both are NaN. Do not extend the existing test, which must stay a passing guard.

## P1 (F202, F203, F204)

Group 9, wave 5, author review: no.

**Targets**

- pyproject.toml [project].dependencies: astropy>=5.0 to >=7; add tables>=3.9; drop h5py and pyyaml
- pyproject.toml [project.optional-dependencies] test and dev: add pyyaml>=6.0 (tests/test_declared_versions.py imports yaml; CI installs .[dev]); tables leaves dev (now runtime)
- solarwindpy.yml: drop h5py; keep pytables, pyyaml (test-time), astropy unpinned per the file's stated policy
- CHANGELOG.md

Impacted tests are inferred guards. test_declared_versions.py imports yaml, so pyyaml must reach [test] and [dev]: CI and tox install .[dev]. tests/core/test_plasma_io.py exercises the HDF path. tests/plotting/test_no_data_files.py names h5py only as a string. No test reads the dependency lists.

Excluded as grep false positives: 12 plotting TestSave tests (figure saves, not HDF).

Conda: solarwindpy.yml already has pytables and pyyaml. Only h5py leaves. astropy stays unpinned, per the file's header policy (pins live in pyproject). .github/workflows/docs.yml and security.yml install pytables separately; that becomes redundant but harmless.

**Impacted tests**: 14 (14 guard)

*guard* (14)

- `tests/core/test_plasma_io.py`: `test_load_from_file_keeps_only_rows_between_start_and_stop`, `test_load_from_file_loads_only_the_species_passed`, `test_load_from_file_needs_spacecraft_name_and_frame`, `test_load_from_file_passes_extra_keywords_to_plasma`, `test_save_and_load`, `test_save_applies_each_modifier_function_before_writing`, `test_save_rejects_a_modifier_that_is_not_a_function`, `test_save_then_load_round_trips_data_spacecraft_and_auxiliary_data`, `test_save_writes_data_spacecraft_and_aux_at_the_default_keys`
- `tests/plotting/test_no_data_files.py`: `test_scanner_passes_clean_plotting_code`
- `tests/test_declared_versions.py`: `test_declared_floors_equal_requires_python_floor`, `test_declared_versions_satisfy_requires_python`, `test_lowest_classifier_is_requires_python_floor`, `test_requires_python_sites_are_found`

*Excluded grep false positives* (12): `tests/plotting/test_tools.py::TestSave::test_axes_input_saves_its_figure_and_kwargs_reach_savefig`, `tests/plotting/test_tools.py::TestSave::test_kwargs_reach_the_pdf_save`, `tests/plotting/test_tools.py::TestSave::test_log_false_records_nothing`, `tests/plotting/test_tools.py::TestSave::test_log_true_records_the_path_and_each_suffix`, `tests/plotting/test_tools.py::TestSave::test_logs_by_default`, `tests/plotting/test_tools.py::TestSave::test_no_stamp_without_add_info_or_without_png`, `tests/plotting/test_tools.py::TestSave::test_pdf_is_cropped_to_the_drawn_content_by_default`, `tests/plotting/test_tools.py::TestSave::test_png_is_cropped_to_the_drawn_content_by_default`, `tests/plotting/test_tools.py::TestSave::test_png_is_stamped_with_the_save_time_at_info_xy`, `tests/plotting/test_tools.py::TestSave::test_rejects_a_non_path_or_a_non_figure`, `tests/plotting/test_tools.py::TestSave::test_stamp_defaults_to_the_bottom_left_corner`, `tests/plotting/test_tools.py::TestSave::test_writes_exactly_the_requested_formats`

**Pins in impacted tests**

- None.

**Target tests, written first as `pytest.mark.xfail(strict=True)`**

- Read pyproject.toml with tomllib (not importlib.metadata, which stays stale until a reinstall): every runtime dependency is imported somewhere under solarwindpy/ (git grep), or is in a named allowlist that carries each reason: {numexpr, bottleneck: pandas accelerators; tables: the pandas HDF backend behind Plasma.save}. Fails today on h5py and pyyaml. Verified: numpy, scipy, pandas, matplotlib, astropy, numba, tabulate and docstring_inheritance are each imported by at least one package module.
- Every optional pandas IO backend the package calls is a runtime dependency: Plasma.save / load_from_file use pandas HDF, so 'tables' is in [project].dependencies. Fails today.
- The astropy floor in [project].dependencies is >= 7, a cited reference value. Cite the author's Phase C decision P1 and F202 (verified by the caller: astropy 6.1.x calls numpy.in1d, which the numpy 2.5 admitted by numpy<3 removed).
- Guard, not xfail (it holds on HEAD): every pyproject runtime dependency's conda name appears in solarwindpy.yml, and every solarwindpy.yml package with a known PyPI name is declared somewhere in pyproject (runtime or an extra). The second clause catches a P1 diff that drops h5py from pyproject but leaves it in the yml. There is no xfail for the yml edit itself: the yml carries no relation that fails before it.

## File-conflict groups

| Group | Items, in order | Shared files |
|---|---|---|
| 1 | D1 then D2 then D3 then D4 | `CHANGELOG.md` |
| 2 | B9 then B2 | `solarwindpy/fitfunctions/plots.py`, `tests/fitfunctions/test_plots.py` |
| 3 | B10 | none |
| 4 | B3 then B4 | `solarwindpy/instabilities/verscharen2016.py`, `tests/instabilities/test_verscharen2016.py` |
| 5 | B7 then B11 then B6 | `solarwindpy/solar_activity/sunspot_number/sidc.py`, `tests/solar_activity/sunspot_number/test_sidc.py` |
| 6 | B1 | none |
| 7 | B8 then M1 | `solarwindpy/core/spacecraft.py`, `tests/core/test_spacecraft.py` |
| 8 | B5 | none |
| 9 | P1 | `pyproject.toml`, `solarwindpy.yml` |
