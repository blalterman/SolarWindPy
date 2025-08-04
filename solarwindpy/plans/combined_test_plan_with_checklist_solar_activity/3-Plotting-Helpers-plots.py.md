---
name: 'Combined Plan and Checklist: Plotting Helpers'
about: Test plan and checklist for plotting helper functions in the solar_activity module.
labels: [sweep, SolarActivity, plotting]
---

# 3-Plotting-Helpers-plots.py

## 🧠 Context

> Extracted from plans/combined_test_plan_with_checklist_solar_activity.md

<!-- markdownlint-disable-next-line MD013 -->

### Combined Test Plan and Checklist for `solar_activity` Submodule (update-2025 branch)

## Overview

This document describes a comprehensive test suite for the
__solar_activity__ submodule of SolarWindPy. The goals are to verify
behavior, mock external interactions, and isolate side effects.

### Overview Checklist

- [ ] Use `pytest` and `unittest.mock` to verify classes, methods, and properties
- [ ] Mock external I/O such as HTTP downloads and file reads
- [ ] Use fixtures (`tmp_path`, `monkeypatch`) to isolate side effects

______________________________________________________________________

## 🎯 Overview of the Task

## 3. Plotting Helpers (`plots.py`)

### 3.1 `class IndicatorPlot`

### 3.2 `class SSNPlot`

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

- [ ] Create a dummy `ActivityIndicator` with known `data`
- [ ] Instantiate `IndicatorPlot(dummy, "col", plasma_index)`, assert
  `.plot_data` slicing
- [ ] Patch a matplotlib `Axes` object; call `make_plot(ax)` and assert
  `ax.plot` called with numeric X and correct Y
- [ ] Patch a matplotlib `Axes` object; assert `_format_axis` settings are
  applied
- [ ] Assert `ykey == "ssn"`
- [ ] After plotting, verify `ax.set_ylim(0, 200)` was called

## 🧩 Decomposition Instructions (Optional)

_None._

## 🤖 Sweep Agent Instructions (Optional)

_None._

## 💬 Additional Notes

_None._
