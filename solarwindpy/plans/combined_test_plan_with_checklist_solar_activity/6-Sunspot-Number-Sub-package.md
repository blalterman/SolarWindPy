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

#### 6.1 `class SIDC_ID`

##### Checklist

#### 6.2 `class SIDCLoader`

##### Checklist

#### 6.3 `class SIDC`

##### Checklist

#### 6.4 `class SSNExtrema`

##### Checklist

______________________________________________________________________

### Test File Structure

```
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

## 🔧 Framework & Dependencies

- pytest

## 📂 Affected Files and Paths

None

## 📊 Figures, Diagrams, or Artifacts (Optional)

None

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
- [ ] Mirror the test file structure as described above
- [ ] Add this plan as `solar_activity_TEST_PLAN.md` at the root of the `solar_activity` module

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

None
