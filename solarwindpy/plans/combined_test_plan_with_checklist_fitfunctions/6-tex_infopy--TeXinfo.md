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

#### 6.1 Construction & storage

- Valid inputs; invalid types → `TypeError` or `ValueError` in setters.

##### Checklist

#### 6.2 Properties & formatting

- `info` / `__str__` with various flag combinations.
- Properties: `initial_guess_info`, `chisq_dof`, `npts`, `popt`, `psigma`, `rsq`,
  `TeX_argnames`, `TeX_function`, `TeX_popt`, `TeX_relative_error`.

##### Checklist

#### 6.3 Static/private helpers

- `_check_and_add_math_escapes`: odd `$` → `ValueError`.
- `_calc_precision`, `_simplify_for_paper`, `_add_additional_info`, `_build_fit_parameter_info`,
  `annotate_info`, `build_info`, setters, `val_uncert_2_string`.

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

- [ ] Test valid construction and invalid types in setters (`TypeError`/`ValueError`)
- [ ] Test `info` / `__str__` with flag combinations
- [ ] Test `initial_guess_info` property
- [ ] Test `chisq_dof` property
- [ ] Test `npts` property
- [ ] Test `popt` property
- [ ] Test `psigma` property
- [ ] Test `rsq` property
- [ ] Test `TeX_argnames` property
- [ ] Test `TeX_function` property
- [ ] Test `TeX_popt` property
- [ ] Test `TeX_relative_error` property
- [ ] Test `_check_and_add_math_escapes` with odd `$` (`ValueError`)
- [ ] Test `_calc_precision` (exponent from scientific notation)
- [ ] Test `_simplify_for_paper` (strips zeros/decimals)
- [ ] Test `_add_additional_info` with `str`, iterable, invalid type
- [ ] Test `_build_fit_parameter_info` (flag combos, unused kwargs `ValueError`)
- [ ] Test `annotate_info` with stub axis (`ax.text` calls)
- [ ] Test `build_info` (same as `info` with explicit kwargs)
- [ ] Test all setters for type/key-consistency errors
- [ ] Test `val_uncert_2_string` with value/uncertainty pairs (e.g., `3.1415± 0.01`)

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

None
