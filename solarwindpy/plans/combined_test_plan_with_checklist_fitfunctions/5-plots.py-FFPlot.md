---
name: 'Combined Plan and Checklist: FFPlot'
about: Describes plotting tests and checklist for the FFPlot class in plots.py.
labels: [sweep, FitFunctions, plotting]
---

> Extracted from solarwindpy/plans/combined_test_plan_with_checklist_fitfunctions.md

## 🧠 Context

Verify correctness, robustness, and coverage of the `solarwindpy.fitfunctions` submodule. This task targets the `FFPlot` class in `plots.py`.

## 🎯 Overview of the Task

### 5.1 Initialization & basic attributes

- `__init__` with dummy `Observations`, `y_fit`, `TeXinfo`, dummy `OptimizeResult`, `fitfunction_name` → no errors.
- `__str__`, `labels`, `log` default `(False, False)`, `observations`, `fitfunction_name`, `fit_result`, `y_fit`.

### 5.2 Path generation

- Vary `labels.x`, `labels.y`, optional `labels.z` → `path` property concatenates correctly.

### 5.3 State mutators

- `set_fitfunction_name`, `set_fit_result`, `set_observations` (shape assertions).

### 5.4 Internal helpers

- `_estimate_markevery` with small and huge `observations.used.x.size`.
- `_format_hax`, `_format_rax`: stub axes → grid/scale calls, ensure correct axes methods invoked.

### 5.5 Plot methods

- `plot_raw`, `plot_used`, `plot_fit`, `plot_raw_used_fit`, `plot_residuals`, `plot_raw_used_fit_resid`
  - Provide dummy axes (monkey-patch `plt.subplots`) and assert returned axes and legend/text behavior.
  - For `pct=True/False`, robust branch, missing `fit_result.fun` → skip second curve.

### 5.6 Label & style setters

- `set_labels` updates `labels` namedtuple, unexpected key → `KeyError`.
- `set_log` toggles `log` flags.
- `set_TeX_info` stores `TeXinfo`.

## 🔧 Framework & Dependencies

- `pytest`
- `matplotlib`

## 📂 Affected Files and Paths

- `solarwindpy/fitfunctions/plots.py`
- `tests/fitfunctions/test_plots.py`

## 📊 Figures, Diagrams, or Artifacts (Optional)

None.

## ✅ Acceptance Criteria

- [ ] Test `__init__` with dummy inputs (no errors).
- [ ] Test `__str__` method.
- [ ] Test `labels` property.
- [ ] Test default `log` equals `(False, False)`.
- [ ] Test `observations` property.
- [ ] Test `fitfunction_name` property.
- [ ] Test `fit_result` property.
- [ ] Test `y_fit` property.
- [ ] Test `path` concatenation for different label combinations.
- [ ] Test `set_fitfunction_name`.
- [ ] Test `set_fit_result`.
- [ ] Test `set_observations` with shape assertions.
- [ ] Test `_estimate_markevery` for small and large datasets.
- [ ] Test `_format_hax` with stub axes.
- [ ] Test `_format_rax` with stub axes.
- [ ] Test `plot_raw` method.
- [ ] Test `plot_used` method.
- [ ] Test `plot_fit` method.
- [ ] Test `plot_raw_used_fit` method.
- [ ] Test `plot_residuals` for kinds `'simple'`, `'robust'`, `'both'`.
- [ ] Test `plot_raw_used_fit_resid` method.
- [ ] Provide dummy axes and monkey-patch `plt.subplots`, verify axes and legend/text behavior.
- [ ] Test `pct=True/False`, robust branch, missing `fit_result.fun` (skip second curve).
- [ ] Test `set_labels` updates `labels` and raises `KeyError` on unknown key.
- [ ] Test `set_log` toggles `log` flags.
- [ ] Test `set_TeX_info` stores `TeXinfo`.

## 🧩 Decomposition Instructions (Optional)

None.

## 🤖 Sweep Agent Instructions (Optional)

None.

## 💬 Additional Notes

Follow repository style guidelines and run tests with `pytest -q`.
