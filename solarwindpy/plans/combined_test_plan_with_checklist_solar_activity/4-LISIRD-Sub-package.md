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

#### 4.1 `class LISIRD_ID`

##### Checklist

#### 4.2 `class LISIRDLoader`

##### Checklist

#### 4.3 `class LISIRD`

##### Checklist

#### 4.4 `class LISIRDExtrema`

##### Checklist

______________________________________________________________________

## 🔧 Framework & Dependencies

- pytest

## 📂 Affected Files and Paths

None

## 📊 Figures, Diagrams, or Artifacts (Optional)

None

## ✅ Acceptance Criteria

- [ ] Valid keys build URLs
- [ ] Invalid keys raise error
- [ ] For `"Lalpha"`, unequal missing values in `convert_nans` raise `NotImplementedError`
- [ ] For other keys, `convert_nans` is a no-op
- [ ] DataFrame with duplicated `milliseconds` dropped in `verify_monotonic_epoch`
- [ ] Manual timestamps dropped for `"f107-penticton"` in `verify_monotonic_epoch`
- [ ] Mock `urllib.request.urlopen` to return JSON; assert CSV & JSON outputs in `download_data`
- [ ] Fake CSV & JSON in `data_path/today.*`, assert `loader.data` & `loader.meta` in `load_data`
- [ ] Monkeypatch loader to return dummy data
- [ ] Assert `normalized` behavior
- [ ] Assert `run_normalization` behavior
- [ ] Assert `interpolate_data()` behavior
- [ ] Monkeypatch `ExtremaCalculator` to return known `formatted_extrema`

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

None
