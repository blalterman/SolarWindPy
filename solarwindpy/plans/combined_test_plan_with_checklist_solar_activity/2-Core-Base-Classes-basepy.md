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

#### 2.1 `class Base`

##### Checklist

#### 2.2 `class ID`

##### Checklist

#### 2.3 `class DataLoader`

##### Checklist

`maybe_update_stale_data`

#### 2.4 `class ActivityIndicator`

##### Checklist

`loader`

#### 2.5 `class IndicatorExtrema`

##### Checklist

______________________________________________________________________

## 🔧 Framework & Dependencies

- pytest

## 📂 Affected Files and Paths

None

## 📊 Figures, Diagrams, or Artifacts (Optional)

None

## ✅ Acceptance Criteria

- [ ] Instantiate a trivial subclass of `Base` and call `_init_logger()`
- [ ] Assert `instance.logger` is a `logging.Logger` named correctly
- [ ] Assert `str(instance) == ClassName`
- [ ] Create a dummy subclass defining `_url_base` and `_trans_url`
- [ ] Call `set_key(valid_key)`, assert `instance.key` and `instance.url` match expected
- [ ] Call `set_key(invalid_key)`, assert `NotImplementedError` is raised
- [ ] Use `tmp_path` to create fake date-named CSV directories for `get_data_ctime`
- [ ] Assert `ctime` is parsed correctly or defaults to epoch when none exist
- [ ] After setting `_ctime`, call and assert `age` = `(today – ctime)` for `get_data_age`
- [ ] Patch `download_data` and monkeypatch “today” to simulate stale data for
- [ ] Assert `download_data` called with correct paths in `maybe_update_stale_data`
- [ ] Create a fake CSV in `data_path/today.csv`, write sample CSV for `load_data`
- [ ] Call `load_data()` and assert `instance.data` matches DataFrame
- [ ] Use a dummy subclass implementing abstract methods to test setting and retrieving `id` and
- [ ] Access `data`, raising on `norm_by` if not set
- [ ] Test basic interpolation on simple time series (e.g., linear)
- [ ] Feed synthetic extrema DataFrame (two cycles) into a dummy subclass
- [ ] Assert `cycle_intervals` yields correct intervals
- [ ] Test `cut_spec_by_interval()` with valid/invalid `kind`
- [ ] Test `calculate_extrema_bands()` for single & pair durations
- [ ] Test `cut_about_extrema_bands()` verifying intervals and labels

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

None
