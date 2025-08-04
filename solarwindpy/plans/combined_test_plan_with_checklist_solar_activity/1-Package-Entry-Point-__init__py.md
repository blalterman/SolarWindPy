---
name: SweepAI Task Template
about: Use this template to request a code update, refactor, or documentation change via SweepAI.
labels: [sweep]
---

> Extracted from solarwindpy/plans/combined_test_plan_with_checklist_solar_activity.md

## 🧠 Context

Combined Test Plan and Checklist for `solar_activity` Submodule (update-2025 branch)

Overview

This document describes a comprehensive test suite for the **solar_activity** submodule of
SolarWindPy. The goals are to verify behavior, mock external interactions, and isolate side effects.

Checklist

- [ ] Use `pytest` and `unittest.mock` to verify classes, methods, and properties
- [ ] Mock external I/O such as HTTP downloads and file reads
- [ ] Use fixtures (`tmp_path`, `monkeypatch`) to isolate side effects

______________________________________________________________________

Test Framework & Dependencies

- `pytest`
- `unittest.mock` (for HTTP and filesystem mocking)
- `pytest-monkeypatch` (monkeypatch fixture)
- `tmp_path` fixture (built into `pytest` for temporary directories)

Checklist

- [ ] Ensure `pytest` is available
- [ ] Ensure `unittest.mock` is available for HTTP and filesystem mocking
- [ ] Ensure `pytest-monkeypatch` plugin is available
- [ ] Ensure `tmp_path` fixture from core `pytest` is available

______________________________________________________________________

Fixtures

| Fixture | Purpose |
| ----------------- | -------------------------------------------- |
| `tmp_path` | Simulate `data_path` directories & files |
| `monkeypatch` | Patch network calls (e.g., `urllib.request`) |
| custom DataFrames | Provide synthetic time series inputs |

Checklist

- [ ] Use `tmp_path` to simulate `data_path` directories & files
- [ ] Use `monkeypatch` to patch network calls such as `urllib.request`
- [ ] Use custom DataFrames for synthetic time series inputs

______________________________________________________________________

## 🎯 Overview of the Task

#### 1.1 `get_all_indices()`

**Purpose:** Ensure it aggregates daily Lα, CaK, SSN, MgII into one DataFrame.

##### Checklist

______________________________________________________________________

## 🔧 Framework & Dependencies

- pytest

## 📂 Affected Files and Paths

None

## 📊 Figures, Diagrams, or Artifacts (Optional)

None

## ✅ Acceptance Criteria

- [ ] Create dummy classes `DummyLISIRD`, `DummySIDC` with `.data` attributes
- [ ] Monkeypatch `lisird.lisird.LISIRD` and `sunspot_number.sidc.SIDC` to return dummies
- [ ] Call `get_all_indices()` and assert columns are `["CaK", "Lalpha", "MgII", "ssn"]`
- [ ] Call `get_all_indices()` and assert index type is `pd.DatetimeIndex`

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

None
