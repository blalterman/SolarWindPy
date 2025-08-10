# Test Plan for `solar_activity` Submodule (update-2025 branch)

## Overview
This document describes a comprehensive test suite for the **solar_activity** submodule of SolarWindPy.  
We will use **pytest** and **unittest.mock** to:
- Verify all public and non–public classes, methods, and properties.
- Mock external I/O (HTTP downloads, file reads).
- Use fixtures (`tmp_path`, `monkeypatch`) to isolate side effects.

---

## Test Framework & Dependencies

- **pytest**  
- **unittest.mock** (for HTTP and filesystem mocking)  
- **pytest-monkeypatch** (monkeypatch fixture)  
- **pytest-tmp_path** (temporary directories for caching)  

---

## Fixtures

| Fixture     | Purpose                                    |
| ----------- | ------------------------------------------ |
| `tmp_path`    | Simulate `data_path` directories & files   |
| `monkeypatch` | Patch network calls (e.g., `urllib.request`) |
| custom DataFrames | Provide synthetic time series inputs  |

---

## 1. Package Entry Point: `__init__.py`

### 1.1 `get_all_indices()`
- **Purpose**: ensure it aggregates daily Lα, CaK, SSN, MgII into one DataFrame.  
- **Approach**:  
  1. Create dummy classes `DummyLISIRD`, `DummySIDC` with `.data` attributes.  
  2. Monkeypatch `lisird.lisird.LISIRD` and `sunspot_number.sidc.SIDC` to return dummies.  
  3. Call `get_all_indices()` and assert:
     - Columns = `["CaK", "Lalpha", "MgII", "ssn"]`  
     - Index type = `pd.DatetimeIndex`  
- **Justification**: validates package‐level convenience function.

---

## 2. Core Base Classes (`base.py`)

### 2.1 `class Base`
- **Tests**:
  - Instantiate a trivial subclass of `Base` and call `_init_logger()`.  
  - Assert `instance.logger` is a `logging.Logger` named correctly.  
  - Assert `str(instance) == ClassName`.

### 2.2 `class ID`
- **Tests**:
  - Create a dummy subclass defining `_url_base` and `_trans_url`.  
  - Call `set_key(valid_key)`, assert `instance.key` and `instance.url` match expected.  
  - Call `set_key(invalid_key)`, assert `NotImplementedError` is raised.

### 2.3 `class DataLoader`
- **Tests**:
  - **`get_data_ctime`**:
    - Use `tmp_path` to create fake date‐named CSV directories.  
    - Assert `ctime` is parsed correctly or defaults to epoch when none exist.
  - **`get_data_age`**:
    - After setting `_ctime`, call and assert `age` = `(today – ctime)`.
  - **`maybe_update_stale_data`**:
    - Patch `download_data` and monkeypatch “today” to simulate stale data.  
    - Assert `download_data` called with correct paths.
  - **`load_data`**:
    - Create a fake CSV in `data_path/today.csv`, write sample CSV.  
    - Call `load_data()` and assert `instance.data` matches DataFrame.

### 2.4 `class ActivityIndicator`
- **Tests**:
  - Use a dummy subclass implementing abstract methods to test:
    - Setting and retrieving `id` and `loader`.
    - Accessing `data`, raising on `norm_by` if not set.
    - Basic interpolation on simple time series (e.g., linear).

### 2.5 `class IndicatorExtrema`
- **Tests**:
  - Feed synthetic extrema DataFrame (two cycles) into a dummy subclass.  
  - Assert `cycle_intervals` yields correct intervals.  
  - Test `cut_spec_by_interval()` with valid/invalid `kind`.  
  - Test `calculate_extrema_bands()` for single & pair durations.  
  - Test `cut_about_extrema_bands()` verifying intervals and labels.

---

## 3. Plotting Helpers (`plots.py`)

### 3.1 `class IndicatorPlot`
- **Tests**:
  - Dummy `ActivityIndicator` with known `data`.  
  - Instantiate `IndicatorPlot(dummy, "col", plasma_index)`, assert `.plot_data` slicing.  
  - Patch a matplotlib `Axes` object; call `make_plot(ax)` and assert:
    - `ax.plot` called with numeric X, correct Y.
    - `_format_axis` settings.

### 3.2 `class SSNPlot`
- **Tests**:
  - Assert `ykey == "ssn"`.  
  - After plotting, verify `ax.set_ylim(0, 200)` was called.

---

## 4. LISIRD Sub-package

### 4.1 `class LISIRD_ID`
- **Tests**:
  - Valid keys build URLs; invalid raise.

### 4.2 `class LISIRDLoader`
- **Tests**:
  - **`convert_nans`**:
    - For `"Lalpha"`: unequal missing values → `NotImplementedError`.
    - Others: no-op.
  - **`verify_monotonic_epoch`**:
    - DataFrame with duplicated `milliseconds` dropped.
    - Manual timestamps dropped for `"f107-penticton"`.
  - **`download_data`**:
    - Mock `urllib.request.urlopen` to return JSON; assert CSV & JSON outputs.
  - **`load_data`**:
    - Fake CSV & JSON in `data_path/today.*`, assert `loader.data` & `loader.meta`.

### 4.3 `class LISIRD`
- **Tests**:
  - Monkeypatch loader to return dummy data.
  - Assert `normalized`, `run_normalization`, `interpolate_data()` behaviours.

### 4.4 `class LISIRDExtrema`
- **Tests**:
  - Monkeypatch `ExtremaCalculator` to return known `formatted_extrema`.

---

## 5. Extrema Calculator

### 5.1 `class ExtremaCalculator`
- **Tests**:
  - `set_name`: invalid names → `ValueError`.
  - `set_data`: window handling & data shift.
  - `set_threshold`: callable vs scalar.
  - `find_threshold_crossings`: correct crossing indices.
  - `cut_data_into_extrema_finding_intervals`: correct binning.
  - `_find_extrema`, `_validate_extrema`, `format_extrema`, `find_extrema`.
  - `make_plot`: conditional plotting.

---

## 6. Sunspot Number Sub-package

### 6.1 `class SIDC_ID`
- **Tests**:
  - Valid keys → URLs; invalid → raise.

### 6.2 `class SIDCLoader`
- **Tests**:
  - `convert_nans`: replace `-1` with `np.nan`.
  - `download_data`: mock `pd.read_csv`; assert CSV.
  - `load_data`: verify `cycle` column.

### 6.3 `class SIDC`
- **Tests**:
  - Init with dummy loader & `SSNExtrema`.
  - `calculate_extrema_kind`, `calculate_edge`.
  - `normalized`, `run_normalization`, `cut_spec_by_ssn_band`.
  - `interpolate_data`, `plot_on_colorbar`.

### 6.4 `class SSNExtrema`
- **Tests**:
  - Temporary `ssn_extrema.csv`, assert parsed `data`.
  - Passing args/kwargs raises `ValueError`.

---

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

Add this file as **solar_activity_TEST_PLAN.md** at the root of the `solar_activity` module for easy reference.
