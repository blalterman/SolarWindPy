---
name: 'Combined Plan and Checklist: LISIRD Sub-package'
about: Test plan and checklist for the solar_activity LISIRD sub-package.
labels: [sweep, SolarActivity, LISIRD]
---

<!--
This file was extracted from combined_test_plan_with_checklist_solar_activity.md.
Source lines: 1-45, 141-179, 239-263
-->

<!-- markdownlint-disable MD024 -->

# Combined Test Plan and Checklist for `solar_activity` Submodule (update-2025 branch)

## Overview

This document describes a comprehensive test suite for the
**solar_activity** submodule of SolarWindPy. The goals are to verify
behavior, mock external interactions, and isolate side effects.

### Checklist

- [ ] Use `pytest` and `unittest.mock` to verify classes, methods, and properties
- [ ] Mock external I/O such as HTTP downloads and file reads
- [ ] Use fixtures (`tmp_path`, `monkeypatch`) to isolate side effects

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

## 4. LISIRD Sub-package

### 4.1 `class LISIRD_ID`

#### Checklist

- [ ] Valid keys build URLs
- [ ] Invalid keys raise error

### 4.2 `class LISIRDLoader`

#### Checklist

- [ ] For `"Lalpha"`, unequal missing values in `convert_nans` raise `NotImplementedError`
- [ ] For other keys, `convert_nans` is a no-op
- [ ] DataFrame with duplicated `milliseconds` dropped in `verify_monotonic_epoch`
- [ ] Manual timestamps dropped for `"f107-penticton"` in `verify_monotonic_epoch`
- [ ] Mock `urllib.request.urlopen` to return JSON; assert CSV & JSON outputs in
  `download_data`
- [ ] Fake CSV & JSON in `data_path/today.*`, assert `loader.data` & `loader.meta`
  in `load_data`

### 4.3 `class LISIRD`

#### Checklist

- [ ] Monkeypatch loader to return dummy data
- [ ] Assert `normalized` behavior
- [ ] Assert `run_normalization` behavior
- [ ] Assert `interpolate_data()` behavior

### 4.4 `class LISIRDExtrema`

#### Checklist

- [ ] Monkeypatch `ExtremaCalculator` to return known `formatted_extrema`

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
