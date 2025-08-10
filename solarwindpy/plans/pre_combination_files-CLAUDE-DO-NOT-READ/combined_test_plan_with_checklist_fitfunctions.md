# Combined Test Plan and Checklist for `solarwindpy.fitfunctions` (update-2025 branch)

> **Goal:** Verify correctness, robustness, and full coverage (public and non‑public APIs) of the `fitfunctions` submodule.
> **Framework:** `pytest` with fixtures; follow `AGENTS.md` guidelines (`pytest -q`, no skipping, style with `flake8` and `black`).

## 1. Common fixtures

```python
import numpy as np
import pandas as pd
import pytest
from scipy.optimize import OptimizeResult

from solarwindpy.fitfunctions import core, gaussians, trend_fits, plots, tex_info
```

- `simple_linear_data`: 1D arrays `x = np.linspace(0, 1, 20)`, `y = 2 * x + 1 + noise`, `w = np.ones_like(x)`.
- `gauss_data`: sample `x`, generate `y = A · exp(-0.5((x - μ)/σ)²) + noise`.
- `small_n`: too few points to trigger `sufficient_data -> ValueError`.

### Checklist

- [ ] Implement `simple_linear_data` fixture (#PR_NUMBER)
- [ ] Implement `gauss_data` fixture (#PR_NUMBER)
- [ ] Implement `small_n` fixture (#PR_NUMBER)

## 2. core.py → `FitFunction`

### 2.1 Initialization & observation filtering

- `_clean_raw_obs`
  - Mismatched shapes → `ValueError`.
  - Valid inputs → arrays returned.
- `_build_one_obs_mask`
  - Test with `xmin`, `xmax`, `None` → masks correct.
- `_build_outside_mask`
  - `outside=None` → all `True`.
  - Valid tuple → only outside points `True`.
- `set_fit_obs`
  - Combined masks apply correctly for `x`, `y`, `wmin`, `wmax`, and `logy`.

#### Checklist

- [ ] Test `_clean_raw_obs` for mismatched shapes (`ValueError`) (#PR_NUMBER)
- [ ] Test `_clean_raw_obs` for valid inputs (arrays returned) (#PR_NUMBER)
- [ ] Test `_build_one_obs_mask` with `xmin`, `xmax`, `None` (masks correct) (#PR_NUMBER)
- [ ] Test `_build_outside_mask` with `outside=None` (all `True`) (#PR_NUMBER)
- [ ] Test `_build_outside_mask` with valid tuple (only outside points `True`) (#PR_NUMBER)
- [ ] Test `set_fit_obs` for combined masks (`x`, `y`, `wmin`, `wmax`, `logy`) (#PR_NUMBER)

### 2.2 Argument introspection

- `_set_argnames`
  - On subclass with known signature → `argnames` matches function arguments.

#### Checklist

- [ ] Test `_set_argnames` on subclass with known signature (`argnames` matches function arguments) (#PR_NUMBER)

### 2.3 Fitting workflow

- `_run_least_squares`
  - Monkey-patch `scipy.optimize.least_squares` to return dummy `OptimizeResult`.
  - Test default kwargs (`loss`, `method`, etc.).
  - Passing invalid `args` kwarg → `ValueError`.
- `_calc_popt_pcov_psigma_chisq`
  - Feed dummy `res` with known `fun`, `jac`, produce known `popt`, `pcov`, `psigma`, `chisq`.
- `make_fit`
  - **Success:** returns `None`, sets `_popt`, `_psigma`, `_pcov`, `_chisq_dof`, `_fit_result`, builds `TeX_info` and `plotter`.
  - **Insufficient data:** returns `ValueError` if `return_exception=True`.
  - **Optimization failure:** raises `RuntimeError` or returns exception.

#### Checklist

- [ ] Test `_run_least_squares` with monkey-patched optimizer (dummy `OptimizeResult`) (#PR_NUMBER)
- [ ] Test `_run_least_squares` for default kwargs (`loss`, `method`, etc.) (#PR_NUMBER)
- [ ] Test `_run_least_squares` for invalid `args` kwarg (`ValueError`) (#PR_NUMBER)
- [ ] Test `_calc_popt_pcov_psigma_chisq` with dummy `res`, known `fun`, `jac` (check outputs) (#PR_NUMBER)
- [ ] Test `make_fit` success path (sets internals and helpers) (#PR_NUMBER)
- [ ] Test `make_fit` with insufficient data (`ValueError` if `return_exception=True`) (#PR_NUMBER)
- [ ] Test `make_fit` on optimization failure (`RuntimeError` or exception) (#PR_NUMBER)

### 2.4 Public properties

- `__str__` → `"<ClassName> (<TeX_function>)"`.
- `__call__` → returns `function(x, *popt)` array.
- **Properties:**
  - `argnames`, `fit_bounds`, `chisq_dof`, `dof`, `fit_result`,
  - `initial_guess_info`, `nobs`, `observations`, `plotter`,
  - `popt`, `psigma`, `psigma_relative`, `combined_popt_psigma`, `pcov`, `rsq`,
  - `sufficient_data`, `TeX_info`.
- **Test:** after a dummy fit, each property yields expected dtype, shape, or value.

#### Checklist

- [ ] Test `__str__` returns `"<ClassName> (<TeX_function>)"` (#PR_NUMBER)
- [ ] Test `__call__` returns `function(x, *popt)` array (#PR_NUMBER)
- [ ] Test `argnames` property after dummy fit (#PR_NUMBER)
- [ ] Test `fit_bounds` property after dummy fit (#PR_NUMBER)
- [ ] Test `chisq_dof` property after dummy fit (#PR_NUMBER)
- [ ] Test `dof` property after dummy fit (#PR_NUMBER)
- [ ] Test `fit_result` property after dummy fit (#PR_NUMBER)
- [ ] Test `initial_guess_info` property after dummy fit (#PR_NUMBER)
- [ ] Test `nobs` property after dummy fit (#PR_NUMBER)
- [ ] Test `observations` property after dummy fit (#PR_NUMBER)
- [ ] Test `plotter` property after dummy fit (#PR_NUMBER)
- [ ] Test `popt` property after dummy fit (#PR_NUMBER)
- [ ] Test `psigma` property after dummy fit (#PR_NUMBER)
- [ ] Test `psigma_relative` property after dummy fit (#PR_NUMBER)
- [ ] Test `combined_popt_psigma` property after dummy fit (#PR_NUMBER)
- [ ] Test `pcov` property after dummy fit (#PR_NUMBER)
- [ ] Test `rsq` property after dummy fit (#PR_NUMBER)
- [ ] Test `sufficient_data` property after dummy fit (#PR_NUMBER)
- [ ] Test `TeX_info` property after dummy fit (#PR_NUMBER)

## 3. gaussians.py → `Gaussian`, `GaussianNormalized`, `GaussianLn`

For each class:

### 3.1 Signature & `function` property

- Call `.function`, inspect returned callable’s signature and behavior on sample `x`.

#### Checklist

- [ ] Test `.function` signature and behavior on sample `x` (#PR_NUMBER)

### 3.2 `p0` initial guesses

- With synthetic Gaussian data → `p0` ≈ true `[μ, σ, A]` (tolerance).
- Empty data → triggers the zero-size-array `ValueError`.

#### Checklist

- [ ] Test `p0` with synthetic Gaussian data (matches true `[μ, σ, A]` within tolerance) (#PR_NUMBER)
- [ ] Test `p0` with empty data (triggers zero-size-array `ValueError`) (#PR_NUMBER)

### 3.3 `TeX_function`

- Matches expected LaTeX string literal.

#### Checklist

- [ ] Test `.TeX_function` matches expected LaTeX string literal (#PR_NUMBER)

### 3.4 `make_fit` override

- On success → calls base `make_fit`, sets `TeX_argnames` in `TeX_info`.
- On forced failure (monkey-patched optimizer) → no exception in `make_fit`, leaves `TeX_argnames` unset.

#### Checklist

- [ ] Test success path: calls base `make_fit`, sets `TeX_argnames` in `TeX_info` (#PR_NUMBER)
- [ ] Test forced failure: no exception in `make_fit`, leaves `TeX_argnames` unset (#PR_NUMBER)

## 4. trend_fits.py → `TrendFit`

### 4.1 Initialization & type enforcement

- Valid `agged: pd.DataFrame`, `trendfunc: FitFunction` subclass → no error.
- Invalid `ffunc1d` or `trendfunc` → raises `TypeError`.

#### Checklist

- [ ] Test valid `agged: pd.DataFrame` and `trendfunc: FitFunction` subclass (no error) (#PR_NUMBER)
- [ ] Test invalid `ffunc1d` or `trendfunc` (raises `TypeError`) (#PR_NUMBER)

### 4.2 Properties

- `__str__`, `agged`, `ffunc1d_class`, `trendfunc_class`, `ffuncs` (after `make_ffunc1ds`),
  `popt_1d`, `psigma_1d`, `trend_func`, `bad_fits`, `popt1d_keys`, `trend_logx`, `labels`.

#### Checklist

- [ ] Test `__str__` property (#PR_NUMBER)
- [ ] Test `agged` property (#PR_NUMBER)
- [ ] Test `ffunc1d_class` property (#PR_NUMBER)
- [ ] Test `trendfunc_class` property (#PR_NUMBER)
- [ ] Test `ffuncs` after `make_ffunc1ds` (#PR_NUMBER)
- [ ] Test `popt_1d` property (#PR_NUMBER)
- [ ] Test `psigma_1d` property (#PR_NUMBER)
- [ ] Test `trend_func` property (#PR_NUMBER)
- [ ] Test `bad_fits` property (#PR_NUMBER)
- [ ] Test `popt1d_keys` property (#PR_NUMBER)
- [ ] Test `trend_logx` property (#PR_NUMBER)
- [ ] Test `labels` property (#PR_NUMBER)

### 4.3 1D-fit pipeline

- `make_ffunc1ds`: builds `Series` of `FitFunction` instances.
- `make_1dfits`: mark bad fits (return value ≠ `None`), remove them from `ffuncs` → `bad_fits` populated.

#### Checklist

- [ ] Test `make_ffunc1ds` builds `Series` of `FitFunction` instances (#PR_NUMBER)
- [ ] Test `make_1dfits` marks bad fits and populates `bad_fits` (#PR_NUMBER)

### 4.4 Trend fitting

- `make_trend_func`: with valid `popt_1d`, builds `trend_func`; insufficient fits → `ValueError`.

#### Checklist

- [ ] Test `make_trend_func` with valid `popt_1d` (builds `trend_func`) (#PR_NUMBER)
- [ ] Test `make_trend_func` with insufficient fits (`ValueError`) (#PR_NUMBER)

### 4.5 Plot helpers

- `plot_all_ffuncs`, `plot_all_popt_1d`, `plot_trend_fit_resid`,
  `plot_trend_and_resid_on_ffuncs`, `plot_1d_popt_and_trend`
  - Stub out plotting (monkey-patch `.plotter` methods to record calls), ensure axes returned.

#### Checklist

- [ ] Test `plot_all_ffuncs` helper (#PR_NUMBER)
- [ ] Test `plot_all_popt_1d` helper (#PR_NUMBER)
- [ ] Test `plot_trend_fit_resid` helper (#PR_NUMBER)
- [ ] Test `plot_trend_and_resid_on_ffuncs` helper (#PR_NUMBER)
- [ ] Test `plot_1d_popt_and_trend` helper (#PR_NUMBER)
- [ ] Stub out plotting to record calls and verify axes returned (#PR_NUMBER)

### 4.6 Label sharing

- `set_agged` type check; `set_fitfunctions` logic; `set_shared_labels` updates label objects.

#### Checklist

- [ ] Test `set_agged` type check (#PR_NUMBER)
- [ ] Test `set_fitfunctions` logic (#PR_NUMBER)
- [ ] Test `set_shared_labels` updates label objects (#PR_NUMBER)

## 5. plots.py → `FFPlot`

### 5.1 Initialization & basic attributes

- `__init__` with dummy `Observations`, `y_fit`, `TeXinfo`, dummy `OptimizeResult`, `fitfunction_name` → no errors.
- `__str__`, `labels`, `log` default `(False, False)`, `observations`, `fitfunction_name`, `fit_result`, `y_fit`.

#### Checklist

- [ ] Test `__init__` with dummy inputs (no errors) (#PR_NUMBER)
- [ ] Test `__str__` method (#PR_NUMBER)
- [ ] Test `labels` property (#PR_NUMBER)
- [ ] Test default `log` equals `(False, False)` (#PR_NUMBER)
- [ ] Test `observations` property (#PR_NUMBER)
- [ ] Test `fitfunction_name` property (#PR_NUMBER)
- [ ] Test `fit_result` property (#PR_NUMBER)
- [ ] Test `y_fit` property (#PR_NUMBER)

### 5.2 Path generation

- Vary `labels.x`, `labels.y`, optional `labels.z` → `path` property concatenates correctly.

#### Checklist

- [ ] Test `path` concatenation for different label combinations (#PR_NUMBER)

### 5.3 State mutators

- `set_fitfunction_name`, `set_fit_result`, `set_observations` (shape assertions).

#### Checklist

- [ ] Test `set_fitfunction_name` (#PR_NUMBER)
- [ ] Test `set_fit_result` (#PR_NUMBER)
- [ ] Test `set_observations` with shape assertions (#PR_NUMBER)

### 5.4 Internal helpers

- `_estimate_markevery` with small and huge `observations.used.x.size`.
- `_format_hax`, `_format_rax`: stub axes → grid/scale calls, ensure correct axes methods invoked.

#### Checklist

- [ ] Test `_estimate_markevery` for small and large datasets (#PR_NUMBER)
- [ ] Test `_format_hax` with stub axes (#PR_NUMBER)
- [ ] Test `_format_rax` with stub axes (#PR_NUMBER)

### 5.5 Plot methods

- `plot_raw`, `plot_used`, `plot_fit`, `plot_raw_used_fit`, `plot_residuals`, `plot_raw_used_fit_resid`
  - Provide dummy axes (monkey-patch `plt.subplots`) and assert returned axes and legend/text behavior.
  - For `pct=True/False`, robust branch, missing `fit_result.fun` → skip second curve.

#### Checklist

- [ ] Test `plot_raw` method (#PR_NUMBER)
- [ ] Test `plot_used` method (#PR_NUMBER)
- [ ] Test `plot_fit` method (#PR_NUMBER)
- [ ] Test `plot_raw_used_fit` method (#PR_NUMBER)
- [ ] Test `plot_residuals` for kinds `'simple'`, `'robust'`, `'both'` (#PR_NUMBER)
- [ ] Test `plot_raw_used_fit_resid` method (#PR_NUMBER)
- [ ] Provide dummy axes and monkey-patch `plt.subplots`, verify axes and legend/text behavior (#PR_NUMBER)
- [ ] Test `pct=True/False`, robust branch, missing `fit_result.fun` (skip second curve) (#PR_NUMBER)

### 5.6 Label & style setters

- `set_labels` updates `labels` namedtuple, unexpected key → `KeyError`.
- `set_log` toggles `log` flags.
- `set_TeX_info` stores `TeXinfo`.

#### Checklist

- [ ] Test `set_labels` updates `labels` and raises `KeyError` on unknown key (#PR_NUMBER)
- [ ] Test `set_log` toggles `log` flags (#PR_NUMBER)
- [ ] Test `set_TeX_info` stores `TeXinfo` (#PR_NUMBER)

## 6. tex_info.py → `TeXinfo`

### 6.1 Construction & storage

- Valid inputs; invalid types → `TypeError` or `ValueError` in setters.

#### Checklist

- [ ] Test valid construction and invalid types in setters (`TypeError`/`ValueError`) (#PR_NUMBER)

### 6.2 Properties & formatting

- `info` / `__str__` with various flag combinations.
- Properties: `initial_guess_info`, `chisq_dof`, `npts`, `popt`, `psigma`, `rsq`,
  `TeX_argnames`, `TeX_function`, `TeX_popt`, `TeX_relative_error`.

#### Checklist

- [ ] Test `info` / `__str__` with flag combinations (#PR_NUMBER)
- [ ] Test `initial_guess_info` property (#PR_NUMBER)
- [ ] Test `chisq_dof` property (#PR_NUMBER)
- [ ] Test `npts` property (#PR_NUMBER)
- [ ] Test `popt` property (#PR_NUMBER)
- [ ] Test `psigma` property (#PR_NUMBER)
- [ ] Test `rsq` property (#PR_NUMBER)
- [ ] Test `TeX_argnames` property (#PR_NUMBER)
- [ ] Test `TeX_function` property (#PR_NUMBER)
- [ ] Test `TeX_popt` property (#PR_NUMBER)
- [ ] Test `TeX_relative_error` property (#PR_NUMBER)

### 6.3 Static/private helpers

- `_check_and_add_math_escapes`: odd `$` → `ValueError`.
- `_calc_precision`, `_simplify_for_paper`, `_add_additional_info`, `_build_fit_parameter_info`,
  `annotate_info`, `build_info`, setters, `val_uncert_2_string`.

#### Checklist

- [ ] Test `_check_and_add_math_escapes` with odd `$` (`ValueError`) (#PR_NUMBER)
- [ ] Test `_calc_precision` (exponent from scientific notation) (#PR_NUMBER)
- [ ] Test `_simplify_for_paper` (strips zeros/decimals) (#PR_NUMBER)
- [ ] Test `_add_additional_info` with `str`, iterable, invalid type (#PR_NUMBER)
- [ ] Test `_build_fit_parameter_info` (flag combos, unused kwargs `ValueError`) (#PR_NUMBER)
- [ ] Test `annotate_info` with stub axis (`ax.text` calls) (#PR_NUMBER)
- [ ] Test `build_info` (same as `info` with explicit kwargs) (#PR_NUMBER)
- [ ] Test all setters for type/key-consistency errors (#PR_NUMBER)
- [ ] Test `val_uncert_2_string` with value/uncertainty pairs (e.g., `3.1415± 0.01`) (#PR_NUMBER)

## 7. Justification

1. **Safety and regression**: non‑public helpers guard data integrity.
1. **Numerical correctness**: fitting and parameter extraction must remain accurate.
1. **API contracts**: string formats (`TeX`), plotting behaviors, and property outputs must be stable.
1. **Edge cases**: zero‑size data, insufficient observations, bad weights, solver failures—ensures graceful degradation.

*Aligns with `AGENTS.md`: run with `pytest -q`, enforce no skipped tests, maintain code style with `flake8` and `black`.*
