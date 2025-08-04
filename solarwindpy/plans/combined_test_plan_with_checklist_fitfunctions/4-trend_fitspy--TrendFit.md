---
name: SweepAI Task Template
about: Use this template to request a code update, refactor, or documentation change via SweepAI.
labels: [sweep]
---

> Extracted from solarwindpy/plans/combined_test_plan_with_checklist_fitfunctions.md

## 🧠 Context

Combined Test Plan and Checklist for `solarwindpy.fitfunctions` (update-2025 branch)

> **Goal:** Verify correctness, robustness, and full coverage (public and non‑public APIs) of the `fitfunctions` submodule.
> **Framework:** `pytest` with fixtures; follow `AGENTS.md` guidelines (`pytest -q`, no skipping, style with `flake8` and `black`).

## 🎯 Overview of the Task

#### 4.1 Initialization & type enforcement

- Valid `agged: pd.DataFrame`, `trendfunc: FitFunction` subclass → no error.
- Invalid `ffunc1d` or `trendfunc` → raises `TypeError`.

##### Checklist

#### 4.2 Properties

- `__str__`, `agged`, `ffunc1d_class`, `trendfunc_class`, `ffuncs` (after `make_ffunc1ds`),
  `popt_1d`, `psigma_1d`, `trend_func`, `bad_fits`, `popt1d_keys`, `trend_logx`, `labels`.

##### Checklist

#### 4.3 1D-fit pipeline

- `make_ffunc1ds`: builds `Series` of `FitFunction` instances.
- `make_1dfits`: mark bad fits (return value ≠ `None`), remove them from `ffuncs` → `bad_fits` populated.

##### Checklist

#### 4.4 Trend fitting

- `make_trend_func`: with valid `popt_1d`, builds `trend_func`; insufficient fits → `ValueError`.

##### Checklist

#### 4.5 Plot helpers

- `plot_all_ffuncs`, `plot_all_popt_1d`, `plot_trend_fit_resid`,
  `plot_trend_and_resid_on_ffuncs`, `plot_1d_popt_and_trend`
  - Stub out plotting (monkey-patch `.plotter` methods to record calls), ensure axes returned.

##### Checklist

#### 4.6 Label sharing

- `set_agged` type check; `set_fitfunctions` logic; `set_shared_labels` updates label objects.

##### Checklist

## 🔧 Framework & Dependencies

- pytest
- flake8
- black

## 📂 Affected Files and Paths

None

## 📊 Figures, Diagrams, or Artifacts (Optional)

None

## ✅ Acceptance Criteria

- [ ] Test valid `agged: pd.DataFrame` and `trendfunc: FitFunction` subclass (no error)
- [ ] Test invalid `ffunc1d` or `trendfunc` (raises `TypeError`)
- [ ] Test `__str__` property
- [ ] Test `agged` property
- [ ] Test `ffunc1d_class` property
- [ ] Test `trendfunc_class` property
- [ ] Test `ffuncs` after `make_ffunc1ds`
- [ ] Test `popt_1d` property
- [ ] Test `psigma_1d` property
- [ ] Test `trend_func` property
- [ ] Test `bad_fits` property
- [ ] Test `popt1d_keys` property
- [ ] Test `trend_logx` property
- [ ] Test `labels` property
- [ ] Test `make_ffunc1ds` builds `Series` of `FitFunction` instances
- [ ] Test `make_1dfits` marks bad fits and populates `bad_fits`
- [ ] Test `make_trend_func` with valid `popt_1d` (builds `trend_func`)
- [ ] Test `make_trend_func` with insufficient fits (`ValueError`)
- [ ] Test `plot_all_ffuncs` helper
- [ ] Test `plot_all_popt_1d` helper
- [ ] Test `plot_trend_fit_resid` helper
- [ ] Test `plot_trend_and_resid_on_ffuncs` helper
- [ ] Test `plot_1d_popt_and_trend` helper
- [ ] Stub out plotting to record calls and verify axes returned
- [ ] Test `set_agged` type check
- [ ] Test `set_fitfunctions` logic
- [ ] Test `set_shared_labels` updates label objects

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

None
