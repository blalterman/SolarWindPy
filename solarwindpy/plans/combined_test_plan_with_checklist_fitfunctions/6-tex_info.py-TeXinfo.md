---
name: 'Combined Plan and Checklist: TeXinfo'
about: Presents test plan and checklist for TeXinfo formatting utilities.
labels: [sweep, FitFunction, plotting, LaTeX]
---

> Extracted from solarwindpy/plans/combined_test_plan_with_checklist_fitfunctions.md

## 🧠 Context

Verify correctness, robustness, and coverage of the `solarwindpy.fitfunctions` submodule. This task targets the `TeXinfo` class in `tex_info.py`.

## 🎯 Overview of the Task

### 6.1 Construction & storage

- Valid inputs; invalid types → `TypeError` or `ValueError` in setters.

### 6.2 Properties & formatting

- `info` / `__str__` with various flag combinations.
- Properties: `initial_guess_info`, `chisq_dof`, `npts`, `popt`, `psigma`, `rsq`,
  `TeX_argnames`, `TeX_function`, `TeX_popt`, `TeX_relative_error`.

### 6.3 Static/private helpers

- `_check_and_add_math_escapes`: odd `$` → `ValueError`.
- `_calc_precision`, `_simplify_for_paper`, `_add_additional_info`, `_build_fit_parameter_info`,
  `annotate_info`, `build_info`, setters, `val_uncert_2_string`.

## 🔧 Framework & Dependencies

- `pytest`
- `numpy`

## 📂 Affected Files and Paths

- `solarwindpy/fitfunctions/tex_info.py`
- `tests/fitfunctions/test_tex_info.py`

## 📊 Figures, Diagrams, or Artifacts (Optional)

None.

## ✅ Acceptance Criteria

- [ ] Test valid construction and invalid types in setters (`TypeError`/`ValueError`).
- [ ] Test `info` / `__str__` with flag combinations.
- [ ] Test `initial_guess_info` property.
- [ ] Test `chisq_dof` property.
- [ ] Test `npts` property.
- [ ] Test `popt` property.
- [ ] Test `psigma` property.
- [ ] Test `rsq` property.
- [ ] Test `TeX_argnames` property.
- [ ] Test `TeX_function` property.
- [ ] Test `TeX_popt` property.
- [ ] Test `TeX_relative_error` property.
- [ ] Test `_check_and_add_math_escapes` with odd `$` (`ValueError`).
- [ ] Test `_calc_precision` (exponent from scientific notation).
- [ ] Test `_simplify_for_paper` (strips zeros/decimals).
- [ ] Test `_add_additional_info` with `str`, iterable, invalid type.
- [ ] Test `_build_fit_parameter_info` (flag combos, unused kwargs `ValueError`).
- [ ] Test `annotate_info` with stub axis (`ax.text` calls).
- [ ] Test `build_info` (same as `info` with explicit kwargs).
- [ ] Test all setters for type/key-consistency errors.
- [ ] Test `val_uncert_2_string` with value/uncertainty pairs (e.g., `3.1415± 0.01`).

## 🧩 Decomposition Instructions (Optional)

None.

## 🤖 Sweep Agent Instructions (Optional)

None.

## 💬 Additional Notes

Follow repository style guidelines and run tests with `pytest -q`.
