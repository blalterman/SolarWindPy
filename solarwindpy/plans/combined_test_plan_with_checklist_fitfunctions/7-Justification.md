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

1. **Safety and regression**: non‑public helpers guard data integrity.
1. **Numerical correctness**: fitting and parameter extraction must remain accurate.
1. **API contracts**: string formats (`TeX`), plotting behaviors, and property outputs must be stable.
1. **Edge cases**: zero‑size data, insufficient observations, bad weights, solver failures—ensures graceful degradation.

*Aligns with `AGENTS.md`: run with `pytest -q`, enforce no skipped tests, maintain code style with `flake8` and `black`.*

## 🔧 Framework & Dependencies

- pytest
- flake8
- black

## 📂 Affected Files and Paths

None

## 📊 Figures, Diagrams, or Artifacts (Optional)

None

## ✅ Acceptance Criteria

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

None
