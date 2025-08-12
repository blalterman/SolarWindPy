---
name: 'Combined Plan and Checklist: Exponential Classes'
about: Lists tests and checklist for FitFunction subclasses Exponential, ExponentialPlusC, and ExponentialCDF in exponentials.py.
labels: [sweep, FitFunction]
---

> Extracted from solarwindpy/plans/combined_test_plan_with_checklist_fitfunctions.md

## 🧠 Context

Verify correctness, robustness, and coverage of the `solarwindpy.fitfunctions`
submodule. This task targets `Exponential`, `ExponentialPlusC`, and
`ExponentialCDF` in `exponentials.py`.

## 🎯 Overview of the Task

For each class:

### 8.1 Signature & `function` property

- Call `.function`, inspect returned callable’s signature and behavior on sample `x`.
- Example: `exp(x=[0,1,2], c=0.5, A=2)` → `y=[2, 1.213..., 0.736...]`.

### 8.2 `p0` initial guesses

- Synthetic exponential data → `p0` ≈ true `[c, A]` (tolerance).
- Empty data → triggers zero-size-array `ValueError`.

### 8.3 `TeX_function`

- Matches expected LaTeX string literal.

### 8.4 Amplitude helpers (`ExponentialCDF`)

- `set_y0` with numeric input → updates `y0`, rejects non-numbers.
- `set_TeX_info` → includes `$A = …$` in `TeXinfo`.

## 🔧 Framework & Dependencies

- `pytest`
- `numpy`
- `scipy`

## 📂 Affected Files and Paths

- `solarwindpy/fitfunctions/exponentials.py`
- `tests/fitfunctions/test_exponentials.py`

## ✅ Acceptance Criteria

- [ ] Test `.function` signature and behavior on sample `x`.
- [ ] Test `p0` with synthetic exponential data (matches true `[c, A]` within tolerance).
- [ ] Test `p0` with empty data (raises zero-size-array `ValueError`).
- [ ] Test `.TeX_function` matches expected LaTeX string literal.
- [ ] Test `set_y0` validation and update.
- [ ] Test `set_TeX_info` adds amplitude info.
- [ ] Verify numerical stability for large `c` or `x`.
- [ ] Validate broadcasting with array inputs.
- [ ] Confirm dtype handling for float32 and float64.
- [ ] Ensure vectorization over `x`.

## 💬 Additional Notes

Follow repository style guidelines and run tests with `pytest -q`.
