---
name: 'Combined Plan and Checklist: Core Base Classes'
about: Test plan and checklist for base classes in the solar_activity module.
labels: [sweep, SolarActivity]
---

<!--
This file was extracted from combined_test_plan_with_checklist_solar_activity.md.
Source lines: 1-45, 65-117, 239-263
-->

<!-- markdownlint-disable MD024 -->

# Combined Test Plan and Checklist for `solar_activity` Submodule (update-2025 branch)

## Overview

This document describes a comprehensive test suite for the **solar_activity**
submodule of SolarWindPy. The goals are to verify behavior, mock external
interactions, and isolate side effects.

### Checklist

- [ ] Use `pytest` and `unittest.mock` to verify classes, methods, and properties
- [ ] Mock external I/O such as HTTP downloads and file reads
- [ ] Use fixtures (`tmp_path`, `monkeypatch`) to isolate side effects

______________________________________________________________________

## Test Framework & Dependencies

- `pytest`
- `unittest.mock` (for HTTP and filesystem mocking)
- `pytest-monkeypatch` (monkeypatch fixture)
- `tmp_path` fixture (built into `pytest` for temporary directories)

### Checklist

- [ ] Ensure `pytest` is available
- [ ] Ensure `unittest.mock` is available for HTTP and filesystem mocking
- [ ] Ensure `pytest-monkeypatch` plugin is available
- [ ] Ensure `tmp_path` fixture from core `pytest` is available

______________________________________________________________________

## Fixtures

| Fixture | Purpose |
| ----------------- | -------------------------------------------- |
| `tmp_path` | Simulate `data_path` directories & files |
| `monkeypatch` | Patch network calls (e.g., `urllib.request`) |
| custom DataFrames | Provide synthetic time series inputs |

### Checklist

- [ ] Use `tmp_path` to simulate `data_path` directories & files
- [ ] Use `monkeypatch` to patch network calls such as `urllib.request`
- [ ] Use custom DataFrames for synthetic time series inputs

## 2. Core Base Classes (`base.py`)

### 2.1 `class Base`

#### Checklist

- [ ] Instantiate a trivial subclass of `Base` and call `_init_logger()`
- [ ] Assert `instance.logger` is a `logging.Logger` named correctly
- [ ] Assert `str(instance) == ClassName`

### 2.2 `class ID`

#### Checklist

- [ ] Create a dummy subclass defining `_url_base` and `_trans_url`
- [ ] Call `set_key(valid_key)`, assert `instance.key` and `instance.url` match expected
- [ ] Call `set_key(invalid_key)`, assert `NotImplementedError` is raised

### 2.3 `class DataLoader`

#### Checklist

- [ ] Use `tmp_path` to create fake date-named CSV directories for `get_data_ctime`

- [ ] Assert `ctime` is parsed correctly or defaults to epoch when none exist

- [ ] After setting `_ctime`, call and assert `age` = `(today – ctime)` for `get_data_age`

- [ ] Patch `download_data` and monkeypatch “today” to simulate stale data for
  `maybe_update_stale_data`

- [ ] Assert `download_data` called with correct paths in `maybe_update_stale_data`

- [ ] Create a fake CSV in `data_path/today.csv`, write sample CSV for `load_data`

- [ ] Call `load_data()` and assert `instance.data` matches DataFrame

### 2.4 `class ActivityIndicator`

#### Checklist

- [ ] Use a dummy subclass implementing abstract methods to test setting and
  retrieving `id` and `loader`
- [ ] Access `data`, raising on `norm_by` if not set
- [ ] Test basic interpolation on simple time series (e.g., linear)

### 2.5 `class IndicatorExtrema`

#### Checklist

- [ ] Feed synthetic extrema DataFrame (two cycles) into a dummy subclass
- [ ] Assert `cycle_intervals` yields correct intervals
- [ ] Test `cut_spec_by_interval()` with valid/invalid `kind`
- [ ] Test `calculate_extrema_bands()` for single & pair durations
- [ ] Test `cut_about_extrema_bands()` verifying intervals and labels

______________________________________________________________________

## Test File Structure

```text
tests/
  solar_activity/
    test_init.py
    test_base.py
    test_plots.py
    lisird/
      test_lisird_id.py
      test_lisird_loader.py
      test_lisird.py
      test_extrema_calculator.py
    sunspot_number/
      test_sidc_id.py
      test_sidc_loader.py
      test_sidc.py
      test_ssnextrema.py
```

### Checklist

- [ ] Mirror the test file structure as described above
- [ ] Add this plan as `solar_activity_TEST_PLAN.md` at the root of the
  `solar_activity` module
