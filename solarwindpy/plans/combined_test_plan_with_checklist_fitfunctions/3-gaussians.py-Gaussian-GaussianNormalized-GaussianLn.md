---
name: 'Combined Plan and Checklist: Gaussian Classes'
about: Lists tests and checklist for FitFunction subclass Gaussian in gaussians.py.
labels: [sweep, FitFunction]
---

> Extracted from solarwindpy/plans/combined_test_plan_with_checklist_fitfunctions.md

## 🧠 Context

Verify correctness, robustness, and coverage of the `solarwindpy.fitfunctions` submodule. This task targets `Gaussian`, `GaussianNormalized`, and `GaussianLn` in `gaussians.py`.

## 🎯 Overview of the Task

For each class:

### 3.1 Signature & `function` property

- Call `.function`, inspect returned callable’s signature and behavior on sample `x`.

### 3.2 `p0` initial guesses

- With synthetic Gaussian data → `p0` ≈ true `[μ, σ, A]` (tolerance).
- Empty data → triggers the zero-size-array `ValueError`.

### 3.3 `TeX_function`

- Matches expected LaTeX string literal.

### 3.4 `make_fit` override

- On success → calls base `make_fit`, sets `TeX_argnames` in `TeX_info`.
- On forced failure (monkey-patched optimizer) → no exception in `make_fit`, leaves `TeX_argnames` unset.

## 🔧 Framework & Dependencies

- `pytest`
- `numpy`
- `scipy`

## 📂 Affected Files and Paths

- `solarwindpy/fitfunctions/gaussians.py`
- `tests/fitfunctions/test_gaussians.py`

## 📊 Figures, Diagrams, or Artifacts (Optional)

None.

## ✅ Acceptance Criteria

- [ ] Test `.function` signature and behavior on sample `x`.
- [ ] Test `p0` with synthetic Gaussian data (matches true `[μ, σ, A]` within tolerance).
- [ ] Test `p0` with empty data (triggers zero-size-array `ValueError`).
- [ ] Test `.TeX_function` matches expected LaTeX string literal.
- [ ] Test success path: calls base `make_fit`, sets `TeX_argnames` in `TeX_info`.
- [ ] Test forced failure: no exception in `make_fit`, leaves `TeX_argnames` unset.

## 🧩 Decomposition Instructions (Optional)

None.

## 🤖 Sweep Agent Instructions (Optional)

None.

## 💬 Additional Notes

Follow repository style guidelines and run tests with `pytest -q`.
