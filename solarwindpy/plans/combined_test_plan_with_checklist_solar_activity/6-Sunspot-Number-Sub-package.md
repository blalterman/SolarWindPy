---
name: 'Combined Plan and Checklist: Sunspot Number Sub-package'
about: Test plan and checklist for the solar_activity sunspot number sub-package.
labels: [sweep, SolarActivity, SSN]
---


# 6-Sunspot-Number-Sub-package

## 🧠 Context

> Extracted from plans/combined_test_plan_with_checklist_solar_activity.md

<!-- markdownlint-disable-next-line MD013 -->

### Combined Test Plan and Checklist for `solar_activity` Submodule (update-2025 branch)

## Overview

This document describes a comprehensive test suite for the **solar_activity**
submodule of SolarWindPy. The goals are to verify behavior, mock external
interactions, and isolate side effects.

### Overview Checklist

- [ ] Use `pytest` and `unittest.mock` to verify classes, methods, and properties
- [ ] Mock external I/O such as HTTP downloads and file reads
- [ ] Use fixtures (`tmp_path`, `monkeypatch`) to isolate side effects

______________________________________________________________________

## 🎯 Overview of the Task

## 6. Sunspot Number Sub-package

### 6.1 `class SIDC_ID`

#### SIDC_ID Checklist

- [ ] Valid keys build URLs
- [ ] Invalid keys raise error

### 6.2 `class SIDCLoader`

#### SIDCLoader Checklist

- [ ] `convert_nans`: replace `-1` with `np.nan`
- [ ] `download_data`: mock `pd.read_csv`; assert CSV is created
- [ ] `load_data`: verify `cycle` column is produced

### 6.3 `class SIDC`

#### SIDC Checklist

- [ ] Init with dummy loader & `SSNExtrema`
- [ ] Test `calculate_extrema_kind`
- [ ] Test `calculate_edge`
- [ ] Test `normalized`
- [ ] Test `run_normalization`
- [ ] Test `cut_spec_by_ssn_band`
- [ ] Test `interpolate_data`
- [ ] Test `plot_on_colorbar`

### 6.4 `class SSNExtrema`

#### SSNExtrema Checklist

- [ ] Temporary `ssn_extrema.csv`, assert parsed `data`
- [ ] Passing args/kwargs raises `ValueError`

______________________________________________________________________

## 🔧 Framework & Dependencies

- `pytest`
- `unittest.mock` (for HTTP and filesystem mocking)
- `pytest-monkeypatch` (monkeypatch fixture)
- `tmp_path` fixture (built into `pytest` for temporary directories)

### Framework Checklist

- [ ] Ensure `pytest` is available
- [ ] Ensure `unittest.mock` is available for HTTP and filesystem mocking
- [ ] Ensure `pytest-monkeypatch` plugin is available
- [ ] Ensure `tmp_path` fixture from core `pytest` is available

______________________________________________________________________

## 📂 Affected Files and Paths

### Fixtures

| Fixture | Purpose |
| ----------------- | -------------------------------------------- |
| `tmp_path` | Simulate `data_path` directories & files |
| `monkeypatch` | Patch network calls (e.g., `urllib.request`) |
| custom DataFrames | Provide synthetic time series inputs |

### Fixtures Checklist

- [ ] Use `tmp_path` to simulate `data_path` directories & files
- [ ] Use `monkeypatch` to patch network calls such as `urllib.request`
- [ ] Use custom DataFrames for synthetic time series inputs

### Test File Structure

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

### Test File Structure Checklist

- [ ] Mirror the test file structure as described above
- [ ] Add this plan as `solar_activity_TEST_PLAN.md` at the root of the
  `solar_activity` module

## 📊 Figures, Diagrams, or Artifacts (Optional)

_None._

## ✅ Acceptance Criteria

- [ ] Valid keys build URLs
- [ ] Invalid keys raise error
- [ ] `convert_nans`: replace `-1` with `np.nan`
- [ ] `download_data`: mock `pd.read_csv`; assert CSV is created
- [ ] `load_data`: verify `cycle` column is produced
- [ ] Init with dummy loader & `SSNExtrema`
- [ ] Test `calculate_extrema_kind`
- [ ] Test `calculate_edge`
- [ ] Test `normalized`
- [ ] Test `run_normalization`
- [ ] Test `cut_spec_by_ssn_band`
- [ ] Test `interpolate_data`
- [ ] Test `plot_on_colorbar`
- [ ] Temporary `ssn_extrema.csv`, assert parsed `data`
- [ ] Passing args/kwargs raises `ValueError`

## 🧩 Decomposition Instructions (Optional)

_None._

## 🤖 Sweep Agent Instructions (Optional)

_None._

## 💬 Additional Notes

_None._
