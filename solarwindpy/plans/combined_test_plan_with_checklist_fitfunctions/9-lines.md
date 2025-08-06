---
name: 'Combined Plan and Checklist: Line Class'
about: Lists tests and checklist for the Line FitFunction subclass in lines.py.
labels: [sweep, FitFunction]
---

> Extracted from solarwindpy/plans/combined_test_plan_with_checklist_fitfunctions.md

## 🧠 Context

Verify correctness, robustness, and coverage of the `solarwindpy.fitfunctions`
submodule. This task targets the `Line` class in `lines.py`.

## 🎯 Overview of the Task

### 9.1 Signature & `function` property

- Call `.function`, inspect returned callable’s signature and behavior on sample `x`.
- Example: `line(x=[0,1,2], m=2, b=1)` → `y=[1,3,5]`.

### 9.2 `p0` initial guesses

- Synthetic linear data → `p0` ≈ true `[m, b]` (tolerance).
- Non-finite or zero `dx` values → warn and return `None`.

### 9.3 `TeX_function`

- Matches expected LaTeX string literal.

### 9.4 `x_intercept` property

- With fitted `popt`, computes `-b/m` and handles divide-by-zero.

## 🔧 Framework & Dependencies

- `pytest`
- `numpy`

## 📂 Affected Files and Paths

- `solarwindpy/fitfunctions/lines.py`
- `tests/fitfunctions/test_lines.py`

## ✅ Acceptance Criteria

- [ ] Test `.function` signature and behavior on sample `x`.
- [ ] Test `p0` with synthetic linear data (matches true `[m, b]`).
- [ ] Test `p0` returns `None` when `dx` contains zeros or NaNs.
- [ ] Test `.TeX_function` matches expected LaTeX string literal.
- [ ] Test `x_intercept` computation and divide-by-zero handling.
- [ ] Verify numerical stability for large `x` and slopes.
- [ ] Validate broadcasting with array inputs.
- [ ] Confirm dtype handling for float32 and float64.
- [ ] Ensure vectorization over `x`.

## 💬 Additional Notes

Follow repository style guidelines and run tests with `pytest -q`.
