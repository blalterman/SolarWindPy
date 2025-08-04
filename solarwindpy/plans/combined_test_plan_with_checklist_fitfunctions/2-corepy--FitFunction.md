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

#### 2.1 Initialization & observation filtering

- `_clean_raw_obs`
  - Mismatched shapes → `ValueError`.
  - Valid inputs → arrays returned.
- `_build_one_obs_mask`
  - Test with `xmin`, `xmax`, `None` → masks correct.
- `_build_outside_mask`
  - `outside=None` → all `True`.
  - Valid tuple → only outside points `True`.
- `set_fit_obs`
  - Combined masks apply correctly for `x`, `y`, `wmin`, `wmax`, and `logy`.

##### Checklist

#### 2.2 Argument introspection

- `_set_argnames`
  - On subclass with known signature → `argnames` matches function arguments.

##### Checklist

#### 2.3 Fitting workflow

- `_run_least_squares`
  - Monkey-patch `scipy.optimize.least_squares` to return dummy `OptimizeResult`.
  - Test default kwargs (`loss`, `method`, etc.).
  - Passing invalid `args` kwarg → `ValueError`.
- `_calc_popt_pcov_psigma_chisq`
  - Feed dummy `res` with known `fun`, `jac`, produce known `popt`, `pcov`, `psigma`, `chisq`.
- `make_fit`
  - **Success:** returns `None`, sets `_popt`, `_psigma`, `_pcov`, `_chisq_dof`, `_fit_result`, builds `TeX_info` and `plotter`.
  - **Insufficient data:** returns `ValueError` if `return_exception=True`.
  - **Optimization failure:** raises `RuntimeError` or returns exception.

##### Checklist

#### 2.4 Public properties

- `__str__` → `"<ClassName> (<TeX_function>)"`.
- `__call__` → returns `function(x, *popt)` array.
- **Properties:**
  - `argnames`, `fit_bounds`, `chisq_dof`, `dof`, `fit_result`,
  - `initial_guess_info`, `nobs`, `observations`, `plotter`,
  - `popt`, `psigma`, `psigma_relative`, `combined_popt_psigma`, `pcov`, `rsq`,
  - `sufficient_data`, `TeX_info`.
- **Test:** after a dummy fit, each property yields expected dtype, shape, or value.

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

- [ ] Test `_clean_raw_obs` for mismatched shapes (`ValueError`)
- [ ] Test `_clean_raw_obs` for valid inputs (arrays returned)
- [ ] Test `_build_one_obs_mask` with `xmin`, `xmax`, `None` (masks correct)
- [ ] Test `_build_outside_mask` with `outside=None` (all `True`)
- [ ] Test `_build_outside_mask` with valid tuple (only outside points `True`)
- [ ] Test `set_fit_obs` for combined masks (`x`, `y`, `wmin`, `wmax`, `logy`)
- [ ] Test `_set_argnames` on subclass with known signature (`argnames` matches function arguments)
- [ ] Test `_run_least_squares` with monkey-patched optimizer (dummy `OptimizeResult`)
- [ ] Test `_run_least_squares` for default kwargs (`loss`, `method`, etc.)
- [ ] Test `_run_least_squares` for invalid `args` kwarg (`ValueError`)
- [ ] Test `_calc_popt_pcov_psigma_chisq` with dummy `res`, known `fun`, `jac` (check outputs)
- [ ] Test `make_fit` success path (sets internals and helpers)
- [ ] Test `make_fit` with insufficient data (`ValueError` if `return_exception=True`)
- [ ] Test `make_fit` on optimization failure (`RuntimeError` or exception)
- [ ] Test `__str__` returns `"<ClassName> (<TeX_function>)"`
- [ ] Test `__call__` returns `function(x, *popt)` array
- [ ] Test `argnames` property after dummy fit
- [ ] Test `fit_bounds` property after dummy fit
- [ ] Test `chisq_dof` property after dummy fit
- [ ] Test `dof` property after dummy fit
- [ ] Test `fit_result` property after dummy fit
- [ ] Test `initial_guess_info` property after dummy fit
- [ ] Test `nobs` property after dummy fit
- [ ] Test `observations` property after dummy fit
- [ ] Test `plotter` property after dummy fit
- [ ] Test `popt` property after dummy fit
- [ ] Test `psigma` property after dummy fit
- [ ] Test `psigma_relative` property after dummy fit
- [ ] Test `combined_popt_psigma` property after dummy fit
- [ ] Test `pcov` property after dummy fit
- [ ] Test `rsq` property after dummy fit
- [ ] Test `sufficient_data` property after dummy fit
- [ ] Test `TeX_info` property after dummy fit

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

None
