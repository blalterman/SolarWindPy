# Combined Test Plan and Checklist for `solar_activity` Submodule (update-2025 branch)

## Overview

This document describes a comprehensive test suite for the **solar_activity** submodule of
SolarWindPy. The goals are to verify behavior, mock external interactions, and isolate side
effects.

### Checklist

- [ ] Use `pytest` and `unittest.mock` to verify classes, methods, and properties (#PR_NUMBER)
- [ ] Mock external I/O such as HTTP downloads and file reads (#PR_NUMBER)
- [ ] Use fixtures (`tmp_path`, `monkeypatch`) to isolate side effects (#PR_NUMBER)

______________________________________________________________________

## Test Framework & Dependencies

- `pytest`
- `unittest.mock` (for HTTP and filesystem mocking)
- `pytest-monkeypatch` (monkeypatch fixture)
- `tmp_path` fixture (built into `pytest` for temporary directories)

### Checklist

- [ ] Ensure `pytest` is available (#PR_NUMBER)
- [ ] Ensure `unittest.mock` is available for HTTP and filesystem mocking (#PR_NUMBER)
- [ ] Ensure `pytest-monkeypatch` plugin is available (#PR_NUMBER)
- [ ] Ensure `tmp_path` fixture from core `pytest` is available (#PR_NUMBER)

______________________________________________________________________

## Fixtures

| Fixture           | Purpose                                      |
| ----------------- | -------------------------------------------- |
| `tmp_path`        | Simulate `data_path` directories & files     |
| `monkeypatch`     | Patch network calls (e.g., `urllib.request`) |
| custom DataFrames | Provide synthetic time series inputs         |

### Checklist

- [ ] Use `tmp_path` to simulate `data_path` directories & files (#PR_NUMBER)
- [ ] Use `monkeypatch` to patch network calls such as `urllib.request` (#PR_NUMBER)
- [ ] Use custom DataFrames for synthetic time series inputs (#PR_NUMBER)

______________________________________________________________________

## 1. Package Entry Point: `__init__.py`

### 1.1 `get_all_indices()`

**Purpose:** Ensure it aggregates daily Lα, CaK, SSN, MgII into one DataFrame.

#### Checklist

- [ ] Create dummy classes `DummyLISIRD`, `DummySIDC` with `.data` attributes (#PR_NUMBER)
- [ ] Monkeypatch `lisird.lisird.LISIRD` and `sunspot_number.sidc.SIDC` to return dummies (#PR_NUMBER)
- [ ] Call `get_all_indices()` and assert columns are `["CaK", "Lalpha", "MgII", "ssn"]` (#PR_NUMBER)
- [ ] Call `get_all_indices()` and assert index type is `pd.DatetimeIndex` (#PR_NUMBER)

______________________________________________________________________

## 2. Core Base Classes (`base.py`)

### 2.1 `class Base`

#### Checklist

- [ ] Instantiate a trivial subclass of `Base` and call `_init_logger()` (#PR_NUMBER)
- [ ] Assert `instance.logger` is a `logging.Logger` named correctly (#PR_NUMBER)
- [ ] Assert `str(instance) == ClassName` (#PR_NUMBER)

### 2.2 `class ID`

#### Checklist

- [ ] Create a dummy subclass defining `_url_base` and `_trans_url` (#PR_NUMBER)
- [ ] Call `set_key(valid_key)`, assert `instance.key` and `instance.url` match expected (#PR_NUMBER)
- [ ] Call `set_key(invalid_key)`, assert `NotImplementedError` is raised (#PR_NUMBER)

### 2.3 `class DataLoader`

#### Checklist

- [ ] Use `tmp_path` to create fake date-named CSV directories for `get_data_ctime` (#PR_NUMBER)
- [ ] Assert `ctime` is parsed correctly or defaults to epoch when none exist (#PR_NUMBER)
- [ ] After setting `_ctime`, call and assert `age` = `(today – ctime)` for `get_data_age` (#PR_NUMBER)
- [ ] Patch `download_data` and monkeypatch “today” to simulate stale data for `maybe_update_stale_data` (#PR_NUMBER)
- [ ] Assert `download_data` called with correct paths in `maybe_update_stale_data` (#PR_NUMBER)
- [ ] Create a fake CSV in `data_path/today.csv`, write sample CSV for `load_data` (#PR_NUMBER)
- [ ] Call `load_data()` and assert `instance.data` matches DataFrame (#PR_NUMBER)

### 2.4 `class ActivityIndicator`

#### Checklist

- [ ] Use a dummy subclass implementing abstract methods to test setting and retrieving `id` and `loader` (#PR_NUMBER)
- [ ] Access `data`, raising on `norm_by` if not set (#PR_NUMBER)
- [ ] Test basic interpolation on simple time series (e.g., linear) (#PR_NUMBER)

### 2.5 `class IndicatorExtrema`

#### Checklist

- [ ] Feed synthetic extrema DataFrame (two cycles) into a dummy subclass (#PR_NUMBER)
- [ ] Assert `cycle_intervals` yields correct intervals (#PR_NUMBER)
- [ ] Test `cut_spec_by_interval()` with valid/invalid `kind` (#PR_NUMBER)
- [ ] Test `calculate_extrema_bands()` for single & pair durations (#PR_NUMBER)
- [ ] Test `cut_about_extrema_bands()` verifying intervals and labels (#PR_NUMBER)

______________________________________________________________________

## 3. Plotting Helpers (`plots.py`)

### 3.1 `class IndicatorPlot`

#### Checklist

- [ ] Create a dummy `ActivityIndicator` with known `data` (#PR_NUMBER)
- [ ] Instantiate `IndicatorPlot(dummy, "col", plasma_index)`, assert `.plot_data` slicing (#PR_NUMBER)
- [ ] Patch a matplotlib `Axes` object; call `make_plot(ax)` and assert `ax.plot` called with numeric X and correct Y (#PR_NUMBER)
- [ ] Patch a matplotlib `Axes` object; assert `_format_axis` settings are applied (#PR_NUMBER)

### 3.2 `class SSNPlot`

#### Checklist

- [ ] Assert `ykey == "ssn"` (#PR_NUMBER)
- [ ] After plotting, verify `ax.set_ylim(0, 200)` was called (#PR_NUMBER)

______________________________________________________________________

## 4. LISIRD Sub-package

### 4.1 `class LISIRD_ID`

#### Checklist

- [ ] Valid keys build URLs (#PR_NUMBER)
- [ ] Invalid keys raise error (#PR_NUMBER)

### 4.2 `class LISIRDLoader`

#### Checklist

- [ ] For `"Lalpha"`, unequal missing values in `convert_nans` raise `NotImplementedError` (#PR_NUMBER)
- [ ] For other keys, `convert_nans` is a no-op (#PR_NUMBER)
- [ ] DataFrame with duplicated `milliseconds` dropped in `verify_monotonic_epoch` (#PR_NUMBER)
- [ ] Manual timestamps dropped for `"f107-penticton"` in `verify_monotonic_epoch` (#PR_NUMBER)
- [ ] Mock `urllib.request.urlopen` to return JSON; assert CSV & JSON outputs in `download_data` (#PR_NUMBER)
- [ ] Fake CSV & JSON in `data_path/today.*`, assert `loader.data` & `loader.meta` in `load_data` (#PR_NUMBER)

### 4.3 `class LISIRD`

#### Checklist

- [ ] Monkeypatch loader to return dummy data (#PR_NUMBER)
- [ ] Assert `normalized` behavior (#PR_NUMBER)
- [ ] Assert `run_normalization` behavior (#PR_NUMBER)
- [ ] Assert `interpolate_data()` behavior (#PR_NUMBER)

### 4.4 `class LISIRDExtrema`

#### Checklist

- [ ] Monkeypatch `ExtremaCalculator` to return known `formatted_extrema` (#PR_NUMBER)

______________________________________________________________________

## 5. Extrema Calculator

### 5.1 `class ExtremaCalculator`

#### Checklist

- [ ] `set_name`: invalid names raise `ValueError` (#PR_NUMBER)
- [ ] `set_data`: handle window and data shift (#PR_NUMBER)
- [ ] `set_threshold`: callable vs scalar (#PR_NUMBER)
- [ ] `find_threshold_crossings`: correct crossing indices (#PR_NUMBER)
- [ ] `cut_data_into_extrema_finding_intervals`: correct binning (#PR_NUMBER)
- [ ] `_find_extrema` logic (#PR_NUMBER)
- [ ] `_validate_extrema` logic (#PR_NUMBER)
- [ ] `format_extrema` logic (#PR_NUMBER)
- [ ] `find_extrema` logic (#PR_NUMBER)
- [ ] `make_plot`: conditional plotting (#PR_NUMBER)

______________________________________________________________________

## 6. Sunspot Number Sub-package

### 6.1 `class SIDC_ID`

#### Checklist

- [ ] Valid keys build URLs (#PR_NUMBER)
- [ ] Invalid keys raise error (#PR_NUMBER)

### 6.2 `class SIDCLoader`

#### Checklist

- [ ] `convert_nans`: replace `-1` with `np.nan` (#PR_NUMBER)
- [ ] `download_data`: mock `pd.read_csv`; assert CSV is created (#PR_NUMBER)
- [ ] `load_data`: verify `cycle` column is produced (#PR_NUMBER)

### 6.3 `class SIDC`

#### Checklist

- [ ] Init with dummy loader & `SSNExtrema` (#PR_NUMBER)
- [ ] Test `calculate_extrema_kind` (#PR_NUMBER)
- [ ] Test `calculate_edge` (#PR_NUMBER)
- [ ] Test `normalized` (#PR_NUMBER)
- [ ] Test `run_normalization` (#PR_NUMBER)
- [ ] Test `cut_spec_by_ssn_band` (#PR_NUMBER)
- [ ] Test `interpolate_data` (#PR_NUMBER)
- [ ] Test `plot_on_colorbar` (#PR_NUMBER)

### 6.4 `class SSNExtrema`

#### Checklist

- [ ] Temporary `ssn_extrema.csv`, assert parsed `data` (#PR_NUMBER)
- [ ] Passing args/kwargs raises `ValueError` (#PR_NUMBER)

______________________________________________________________________

## Test File Structure

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

### Checklist

- [ ] Mirror the test file structure as described above (#PR_NUMBER)
- [ ] Add this plan as `solar_activity_TEST_PLAN.md` at the root of the `solar_activity` module (#PR_NUMBER)
