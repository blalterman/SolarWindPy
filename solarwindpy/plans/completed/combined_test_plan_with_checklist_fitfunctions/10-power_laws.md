---
name: 'Combined Plan and Checklist: Power-Law Classes'
about: Lists tests and checklist for FitFunction subclasses PowerLaw, PowerLawPlusC, and PowerLawOffCenter in power_laws.py.
labels: [sweep, FitFunction]
---

> Extracted from solarwindpy/plans/combined_test_plan_with_checklist_fitfunctions.md

## 🧠 Context

Verify correctness, robustness, and coverage of the `solarwindpy.fitfunctions`
submodule. This task targets `PowerLaw`, `PowerLawPlusC`, and
`PowerLawOffCenter` in `power_laws.py`.

## 🎯 Overview of the Task

For each class:

### 11.1 Signature & `function` property

- Call `.function`, inspect returned callable’s signature and behavior on sample `x`.
- Example: `power_law(x=[1,2,4], A=2, b=0.5)` → `y=[2, 2.828..., 4]`.

### 11.2 `p0` initial guesses

- Synthetic power-law data → `p0` ≈ true parameters (tolerance).
- Empty data → fails `assert self.sufficient_data`.

### 11.3 `TeX_function`

- Matches expected LaTeX string literal.

## 🔧 Framework & Dependencies

- `pytest`
- `numpy`

## 📂 Affected Files and Paths

- `solarwindpy/fitfunctions/power_laws.py`
- `tests/fitfunctions/test_power_laws.py`

## ✅ Acceptance Criteria

- [ ] Test `.function` signature and behavior on sample `x`.
- [ ] Test `p0` with synthetic power-law data (matches true parameters).
- [ ] Test `p0` assertion on empty data.
- [ ] Test `.TeX_function` matches expected LaTeX string literal.
- [ ] Verify numerical stability for large exponents and `x`.
- [ ] Validate broadcasting with array inputs.
- [ ] Confirm dtype handling for float32 and float64.
- [ ] Ensure vectorization over `x`.

## 💬 Additional Notes

Follow repository style guidelines and run tests with `pytest -q`.
