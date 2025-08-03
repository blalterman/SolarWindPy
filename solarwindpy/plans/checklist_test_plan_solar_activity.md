# Test Plan for `solar_activity` Submodule (update-2025 branch)

______________________________________________________________________

## Overview

- Use `pytest` and `unittest.mock` to verify classes, methods, and properties
- Mock external I/O (HTTP downloads, file reads)
- Use fixtures (`tmp_path`, `monkeypatch`) to isolate side effects

## Test Framework & Dependencies

- `pytest`
- `unittest.mock` for HTTP and filesystem mocking
- `pytest-monkeypatch` for the `monkeypatch` fixture
- `pytest-tmp_path` for temporary directories

## Fixtures

| Fixture | Purpose |
| --- | --- |
| `tmp_path` | Simulate `data_path` directories & files |
| `monkeypatch` | Patch network calls (e.g., `urllib.request`) |
| custom DataFrames | Provide synthetic time series inputs |

______________________________________________________________________

## 1. Package Entry Point: `__init__.py`

### 1.1 `get_all_indices()`

- [ ] Create dummy classes `DummyLISIRD`, `DummySIDC` with `.data` attributes (#PR)
- [ ] Monkeypatch `lisird.lisird.LISIRD` and `sunspot_number.sidc.SIDC` to return dummies (#PR)
- [ ] Call `get_all_indices()` and assert columns are `["CaK", "Lalpha", "MgII", "ssn"]` (#PR)
- [ ] Call `get_all_indices()` and assert index type is `pd.DatetimeIndex` (#PR)

______________________________________________________________________

## 2. Core Base Classes (`base.py`)

### 2.1 `class Base`

- [ ] Instantiate a trivial subclass of `Base` and call `_init_logger()` (#PR)
- [ ] Assert `instance.logger` is a `logging.Logger` named correctly (#PR)
- [ ] Assert `str(instance) == ClassName` (#PR)

### 2.2 `class ID`

- [ ] Create a dummy subclass defining `_url_base` and `_trans_url` (#PR)
- [ ] Call `set_key(valid_key)`, assert `instance.key` and `instance.url` match expected (#PR)
- [ ] Call `set_key(invalid_key)`, assert `NotImplementedError` is raised (#PR)

### 2.3 `class DataLoader`

- [ ] Use `tmp_path` to create fake date-named CSV directories for `get_data_ctime` (#PR)
- [ ] Assert `ctime` is parsed correctly or defaults to epoch when none exist (#PR)
- [ ] After setting `_ctime`, call and assert `age` = `(today – ctime)` for `get_data_age` (#PR)
- [ ] Patch `download_data` and monkeypatch “today” to simulate stale data for `maybe_update_stale_data` (#PR)
- [ ] Assert `download_data` called with correct paths in `maybe_update_stale_data` (#PR)
- [ ] Create a fake CSV in `data_path/today.csv`, write sample CSV for `load_data` (#PR)
- [ ] Call `load_data()` and assert `instance.data` matches DataFrame (#PR)

### 2.4 `class ActivityIndicator`

- [ ] Use a dummy subclass implementing abstract methods to test setting and retrieving `id` and `loader` (#PR)
- [ ] Access `data`, raising on `norm_by` if not set (#PR)
- [ ] Test basic interpolation on simple time series (e.g., linear) (#PR)

### 2.5 `class IndicatorExtrema`

- [ ] Feed synthetic extrema DataFrame (two cycles) into a dummy subclass (#PR)
- [ ] Assert `cycle_intervals` yields correct intervals (#PR)
- [ ] Test `cut_spec_by_interval()` with valid/invalid `kind` (#PR)
- [ ] Test `calculate_extrema_bands()` for single & pair durations (#PR)
- [ ] Test `cut_about_extrema_bands()` verifying intervals and labels (#PR)

______________________________________________________________________

## 3. Plotting Helpers (`plots.py`)

### 3.1 `class IndicatorPlot`

- [ ] Create a dummy `ActivityIndicator` with known `data` (#PR)
- [ ] Instantiate `IndicatorPlot(dummy, "col", plasma_index)`, assert `.plot_data` slicing (#PR)
- [ ] Patch a matplotlib `Axes` object; call `make_plot(ax)` and assert `ax.plot` called with numeric X, correct Y (#PR)
- [ ] Patch a matplotlib `Axes` object; assert `_format_axis` settings are applied (#PR)

### 3.2 `class SSNPlot`

- [ ] Assert `ykey == "ssn"` (#PR)
- [ ] After plotting, verify `ax.set_ylim(0, 200)` was called (#PR)

______________________________________________________________________

## 4. LISIRD Sub-package

### 4.1 `class LISIRD_ID`

- [ ] Valid keys build URLs (#PR)
- [ ] Invalid keys raise error (#PR)

### 4.2 `class LISIRDLoader`

- [ ] For `"Lalpha"`: unequal missing values in `convert_nans` → `NotImplementedError` (#PR)
- [ ] For other keys: `convert_nans` is no-op (#PR)
- [ ] DataFrame with duplicated `milliseconds` dropped in `verify_monotonic_epoch` (#PR)
- [ ] Manual timestamps dropped for `"f107-penticton"` in `verify_monotonic_epoch` (#PR)
- [ ] Mock `urllib.request.urlopen` to return JSON; assert CSV & JSON outputs in `download_data` (#PR)
- [ ] Fake CSV & JSON in `data_path/today.*`, assert `loader.data` & `loader.meta` in `load_data` (#PR)

### 4.3 `class LISIRD`

- [ ] Monkeypatch loader to return dummy data (#PR)
- [ ] Assert `normalized` behavior (#PR)
- [ ] Assert `run_normalization` behavior (#PR)
- [ ] Assert `interpolate_data()` behavior (#PR)

### 4.4 `class LISIRDExtrema`

- [ ] Monkeypatch `ExtremaCalculator` to return known `formatted_extrema` (#PR)

______________________________________________________________________

## 5. Extrema Calculator

### 5.1 `class ExtremaCalculator`

- [ ] `set_name`: invalid names → `ValueError` (#PR)
- [ ] `set_data`: window handling & data shift (#PR)
- [ ] `set_threshold`: callable vs scalar (#PR)
- [ ] `find_threshold_crossings`: correct crossing indices (#PR)
- [ ] `cut_data_into_extrema_finding_intervals`: correct binning (#PR)
- [ ] `_find_extrema` logic (#PR)
- [ ] `_validate_extrema` logic (#PR)
- [ ] `format_extrema` logic (#PR)
- [ ] `find_extrema` logic (#PR)
- [ ] `make_plot`: conditional plotting (#PR)

______________________________________________________________________

## 6. Sunspot Number Sub-package

### 6.1 `class SIDC_ID`

- [ ] Valid keys build URLs (#PR)
- [ ] Invalid keys raise error (#PR)

### 6.2 `class SIDCLoader`

- [ ] `convert_nans`: replace `-1` with `np.nan` (#PR)
- [ ] `download_data`: mock `pd.read_csv`; assert CSV is created (#PR)
- [ ] `load_data`: verify `cycle` column is produced (#PR)

### 6.3 `class SIDC`

- [ ] Init with dummy loader & `SSNExtrema` (#PR)
- [ ] Test `calculate_extrema_kind` (#PR)
- [ ] Test `calculate_edge` (#PR)
- [ ] Test `normalized` (#PR)
- [ ] Test `run_normalization` (#PR)
- [ ] Test `cut_spec_by_ssn_band` (#PR)
- [ ] Test `interpolate_data` (#PR)
- [ ] Test `plot_on_colorbar` (#PR)

### 6.4 `class SSNExtrema`

- [ ] Temporary `ssn_extrema.csv`, assert parsed `data` (#PR)
- [ ] Passing args/kwargs raises `ValueError` (#PR)

______________________________________________________________________

## Test File Structure

- [ ] Mirror the test file structure as described in the plan (#PR)

______________________________________________________________________
