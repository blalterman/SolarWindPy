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

For each class:

#### 3.1 Signature & `function` property

- Call `.function`, inspect returned callable’s signature and behavior on sample `x`.

##### Checklist

#### 3.2 `p0` initial guesses

- With synthetic Gaussian data → `p0` ≈ true `[μ, σ, A]` (tolerance).
- Empty data → triggers the zero-size-array `ValueError`.

##### Checklist

#### 3.3 `TeX_function`

- Matches expected LaTeX string literal.

##### Checklist

#### 3.4 `make_fit` override

- On success → calls base `make_fit`, sets `TeX_argnames` in `TeX_info`.
- On forced failure (monkey-patched optimizer) → no exception in `make_fit`, leaves `TeX_argnames` unset.

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

- [ ] Test `.function` signature and behavior on sample `x`
- [ ] Test `p0` with synthetic Gaussian data (matches true `[μ, σ, A]` within tolerance)
- [ ] Test `p0` with empty data (triggers zero-size-array `ValueError`)
- [ ] Test `.TeX_function` matches expected LaTeX string literal
- [ ] Test success path: calls base `make_fit`, sets `TeX_argnames` in `TeX_info`
- [ ] Test forced failure: no exception in `make_fit`, leaves `TeX_argnames` unset

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

None
