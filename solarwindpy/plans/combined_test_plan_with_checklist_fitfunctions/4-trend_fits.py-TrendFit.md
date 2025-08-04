---
name: 'Combined Plan and Checklist: TrendFit'
about: Covers tests and checklist for the TrendFit class in trend_fits.py.
labels: [sweep, FitFunction]
---

> Extracted from solarwindpy/plans/combined_test_plan_with_checklist_fitfunctions.md

## 🧠 Context

Verify correctness, robustness, and coverage of the `solarwindpy.fitfunctions` submodule. This task targets the `TrendFit` class in `trend_fits.py`.

## 🎯 Overview of the Task

### 4.1 Initialization & type enforcement

- Valid `agged: pd.DataFrame`, `trendfunc: FitFunction` subclass → no error.
- Invalid `ffunc1d` or `trendfunc` → raises `TypeError`.

### 4.2 Properties

- `__str__`, `agged`, `ffunc1d_class`, `trendfunc_class`, `ffuncs` (after `make_ffunc1ds`),
  `popt_1d`, `psigma_1d`, `trend_func`, `bad_fits`, `popt1d_keys`, `trend_logx`, `labels`.

### 4.3 1D-fit pipeline

- `make_ffunc1ds`: builds `Series` of `FitFunction` instances.
- `make_1dfits`: mark bad fits (return value ≠ `None`), remove them from `ffuncs` → `bad_fits` populated.

### 4.4 Trend fitting

- `make_trend_func`: with valid `popt_1d`, builds `trend_func`; insufficient fits → `ValueError`.

### 4.5 Plot helpers

- `plot_all_ffuncs`, `plot_all_popt_1d`, `plot_trend_fit_resid`,
  `plot_trend_and_resid_on_ffuncs`, `plot_1d_popt_and_trend`
  - Stub out plotting (monkey-patch `.plotter` methods to record calls), ensure axes returned.

### 4.6 Label sharing

- `set_agged` type check; `set_fitfunctions` logic; `set_shared_labels` updates label objects.

## 🔧 Framework & Dependencies

- `pytest`
- `pandas`
- `numpy`

## 📂 Affected Files and Paths

- `solarwindpy/fitfunctions/trend_fits.py`
- `tests/fitfunctions/test_trend_fits.py`

## 📊 Figures, Diagrams, or Artifacts (Optional)

None.

## ✅ Acceptance Criteria

- [ ] Test valid `agged: pd.DataFrame` and `trendfunc: FitFunction` subclass (no error).
- [ ] Test invalid `ffunc1d` or `trendfunc` (raises `TypeError`).
- [ ] Test `__str__` property.
- [ ] Test `agged` property.
- [ ] Test `ffunc1d_class` property.
- [ ] Test `trendfunc_class` property.
- [ ] Test `ffuncs` after `make_ffunc1ds`.
- [ ] Test `popt_1d` property.
- [ ] Test `psigma_1d` property.
- [ ] Test `trend_func` property.
- [ ] Test `bad_fits` property.
- [ ] Test `popt1d_keys` property.
- [ ] Test `trend_logx` property.
- [ ] Test `labels` property.
- [ ] Test `make_ffunc1ds` builds `Series` of `FitFunction` instances.
- [ ] Test `make_1dfits` marks bad fits and populates `bad_fits`.
- [ ] Test `make_trend_func` with valid `popt_1d` (builds `trend_func`).
- [ ] Test `make_trend_func` with insufficient fits (`ValueError`).
- [ ] Test `plot_all_ffuncs` helper.
- [ ] Test `plot_all_popt_1d` helper.
- [ ] Test `plot_trend_fit_resid` helper.
- [ ] Test `plot_trend_and_resid_on_ffuncs` helper.
- [ ] Test `plot_1d_popt_and_trend` helper.
- [ ] Stub out plotting to record calls and verify axes returned.
- [ ] Test `set_agged` type check.
- [ ] Test `set_fitfunctions` logic.
- [ ] Test `set_shared_labels` updates label objects.

## 🧩 Decomposition Instructions (Optional)

None.

## 🤖 Sweep Agent Instructions (Optional)

None.

## 💬 Additional Notes

Follow repository style guidelines and run tests with `pytest -q`.
