# Test Plan for `solarwindpy.fitfunctions` (update-2025 branch)

> **Goal:** Verify correctness, robustness, and full coverage (public & non‐public APIs) of the `fitfunctions` submodule.  
> **Framework:** `pytest` + fixtures; follow AGENTS.md guidelines (`pytest -q`, no skipping, style with `flake8` & `black`).

---

## 1. Common fixtures

- [ ] Implement `simple_linear_data`: 1D arrays `x = np.linspace(0,1,20)`, `y = 2*x + 1 + noise`, `w = np.ones_like(x)` (#PR)
- [ ] Implement `gauss_data`: sample `x`, generate `y = A·exp(−0.5((x−μ)/σ)²)` + small noise (#PR)
- [ ] Implement `small_n`: too few points to trigger `sufficient_data → ValueError` (#PR)

---

## 2. core.py → `FitFunction`

### 2.1 Initialization & observation filtering

- [ ] Test `_clean_raw_obs` for mismatched shapes (`ValueError`) (#PR)
- [ ] Test `_clean_raw_obs` for valid inputs (arrays returned) (#PR)
- [ ] Test `_build_one_obs_mask` with `xmin`, `xmax`, `None` (masks correct) (#PR)
- [ ] Test `_build_outside_mask` with `outside=None` (all `True`) (#PR)
- [ ] Test `_build_outside_mask` with valid tuple (only outside points `True`) (#PR)
- [ ] Test `set_fit_obs` for combined masks (`x`, `y`, `wmin`, `wmax`, `logy`) (#PR)

### 2.2 Argument introspection

- [ ] Test `_set_argnames` on subclass with known signature (`argnames` matches function arguments) (#PR)

### 2.3 Fitting workflow

- [ ] Test `_run_least_squares` by monkey-patching `scipy.optimize.least_squares` (dummy `OptimizeResult`) (#PR)
- [ ] Test `_run_least_squares` for default kwargs (`loss`, `method`, etc.) (#PR)
- [ ] Test `_run_least_squares` for invalid `args` kwarg (`ValueError`) (#PR)
- [ ] Test `_calc_popt_pcov_psigma_chisq` with dummy `res`, known `fun`, `jac` (check outputs) (#PR)
- [ ] Test `make_fit` success: returns `None`, sets `_popt`, `_psigma`, `_pcov`, `_chisq_dof`, `_fit_result`, builds `TeX_info` & `plotter` (#PR)
- [ ] Test `make_fit` with insufficient data (`ValueError` if `return_exception=True`) (#PR)
- [ ] Test `make_fit` on optimization failure (`RuntimeError` or exception) (#PR)

### 2.4 Public properties

- [ ] Test `__str__` returns `"<ClassName> (<TeX_function>)"` (#PR)
- [ ] Test `__call__` returns `function(x,*popt)` array (#PR)
- [ ] Test all properties after dummy fit:  
    - [ ] `argnames` (#PR)
    - [ ] `fit_bounds` (#PR)
    - [ ] `chisq_dof` (#PR)
    - [ ] `dof` (#PR)
    - [ ] `fit_result` (#PR)
    - [ ] `initial_guess_info` (#PR)
    - [ ] `nobs` (#PR)
    - [ ] `observations` (#PR)
    - [ ] `plotter` (#PR)
    - [ ] `popt` (#PR)
    - [ ] `psigma` (#PR)
    - [ ] `psigma_relative` (#PR)
    - [ ] `combined_popt_psigma` (#PR)
    - [ ] `pcov` (#PR)
    - [ ] `rsq` (#PR)
    - [ ] `sufficient_data` (#PR)
    - [ ] `TeX_info` (#PR)

---

## 3. gaussians.py → `Gaussian`, `GaussianNormalized`, `GaussianLn`

_For each class:_

### 3.1 Signature & `function` property

- [ ] Test `.function` signature and behavior on sample `x` (#PR)

### 3.2 `p0` initial guesses

- [ ] Test `p0` with synthetic Gaussian data (matches true `[μ,σ,A]` within tolerance) (#PR)
- [ ] Test `p0` with empty data (triggers zero-size-array `ValueError`) (#PR)

### 3.3 `TeX_function`

- [ ] Test `.TeX_function` matches expected LaTeX string literal (#PR)

### 3.4 `make_fit` override

- [ ] Test success path: calls base `make_fit`, sets `TeX_argnames` in `TeX_info` (#PR)
- [ ] Test forced failure (monkey-patched optimizer): no exception in `make_fit`, leaves `TeX_argnames` unset (#PR)

---

## 4. trend_fits.py → `TrendFit`

### 4.1 Initialization & type enforcement

- [ ] Test valid `agged: pd.DataFrame`, `trendfunc: FitFunction` subclass (no error) (#PR)
- [ ] Test invalid `ffunc1d` or `trendfunc` (raises `TypeError`) (#PR)

### 4.2 Properties

- [ ] Test properties:  
    - [ ] `__str__` (#PR)
    - [ ] `agged` (#PR)
    - [ ] `ffunc1d_class` (#PR)
    - [ ] `trendfunc_class` (#PR)
    - [ ] `ffuncs` (after `make_ffunc1ds`) (#PR)
    - [ ] `popt_1d` (#PR)
    - [ ] `psigma_1d` (#PR)
    - [ ] `trend_func` (#PR)
    - [ ] `bad_fits` (#PR)
    - [ ] `popt1d_keys` (#PR)
    - [ ] `trend_logx` (#PR)
    - [ ] `labels` (#PR)

### 4.3 1D‐fit pipeline

- [ ] Test `make_ffunc1ds`: builds `Series` of `FitFunction` instances (#PR)
- [ ] Test `make_1dfits`: marks bad fits, removes from `ffuncs`, populates `bad_fits` (#PR)

### 4.4 Trend fitting

- [ ] Test `make_trend_func` with valid `popt_1d` (builds `trend_func`) (#PR)
- [ ] Test `make_trend_func` with insufficient fits (`ValueError`) (#PR)

### 4.5 Plot helpers

- [ ] Test plot helpers:  
    - [ ] `plot_all_ffuncs` (#PR)
    - [ ] `plot_all_popt_1d` (#PR)
    - [ ] `plot_trend_fit_resid` (#PR)
    - [ ] `plot_trend_and_resid_on_ffuncs` (#PR)
    - [ ] `plot_1d_popt_and_trend` (#PR)
  - [ ] Stub out plotting (monkey-patch `.plotter` methods), ensure axes returned (#PR)

### 4.6 Label sharing

- [ ] Test `set_agged` type check (#PR)
- [ ] Test `set_fitfunctions` logic (#PR)
- [ ] Test `set_shared_labels` updates label objects (#PR)

---

## 5. plots.py → `FFPlot`

### 5.1 Initialization & basic attributes

- [ ] Test `__init__` with dummy `Observations`, `y_fit`, `TeXinfo`, dummy `OptimizeResult`, `fitfunction_name` (no errors) (#PR)
- [ ] Test `__str__` (#PR)
- [ ] Test `labels` (#PR)
- [ ] Test `log` defaults `(False,False)` (#PR)
- [ ] Test `observations` (#PR)
- [ ] Test `fitfunction_name` (#PR)
- [ ] Test `fit_result` (#PR)
- [ ] Test `y_fit` (#PR)

### 5.2 Path generation

- [ ] Vary `labels.x`, `labels.y`, optional `labels.z` (`path` property concatenates correctly) (#PR)

### 5.3 State mutators

- [ ] Test `set_fitfunction_name` (#PR)
- [ ] Test `set_fit_result` (#PR)
- [ ] Test `set_observations` (shape assertions) (#PR)

### 5.4 Internal helpers

- [ ] Test `_estimate_markevery` with small & huge `observations.used.x.size` (#PR)
- [ ] Test `_format_hax`: stub axes, check grid/scale calls (#PR)
- [ ] Test `_format_rax`: stub axes, check grid/scale calls (#PR)

### 5.5 Plot methods

- [ ] Test `plot_raw` (#PR)
- [ ] Test `plot_used` (#PR)
- [ ] Test `plot_fit` (#PR)
- [ ] Test `plot_raw_used_fit` (#PR)
- [ ] Test `plot_residuals` (kinds `'simple'`, `'robust'`, `'both'`) (#PR)
- [ ] Test `plot_raw_used_fit_resid` (#PR)
  - [ ] Provide dummy axes, monkey-patch `plt.subplots`, assert returned axes and legend/text behavior (#PR)
  - [ ] Test `pct=True/False`, robust branch, missing `fit_result.fun` (skip second curve) (#PR)

### 5.6 Label & style setters

- [ ] Test `set_labels` updates `labels` namedtuple, unexpected key (`KeyError`) (#PR)
- [ ] Test `set_log` toggles `log` flags (#PR)
- [ ] Test `set_TeX_info` stores `TeXinfo` (#PR)

---

## 6. tex_info.py → `TeXinfo`

### 6.1 Construction & storage

- [ ] Test valid construction; invalid types in setters (`TypeError`/`ValueError`) (#PR)

### 6.2 Properties & formatting

- [ ] Test `info` / `__str__` with various flag combinations (#PR)
- [ ] Test property access:  
    - [ ] `initial_guess_info` (#PR)
    - [ ] `chisq_dof` (#PR)
    - [ ] `npts` (#PR)
    - [ ] `popt` (#PR)
    - [ ] `psigma` (#PR)
    - [ ] `rsq` (#PR)
    - [ ] `TeX_argnames` (#PR)
    - [ ] `TeX_function` (#PR)
    - [ ] `TeX_popt` (#PR)
    - [ ] `TeX_relative_error` (#PR)

### 6.3 Static/private helpers

- [ ] Test `_check_and_add_math_escapes`: odd `$` triggers `ValueError` (#PR)
- [ ] Test `_calc_precision` (exponent from scientific notation) (#PR)
- [ ] Test `_simplify_for_paper` (strips zeros/decimals) (#PR)
- [ ] Test `_add_additional_info` with `str`, iterable, invalid type (#PR)
- [ ] Test `_build_fit_parameter_info` (flag combos, unused kwargs trigger `ValueError`) (#PR)
- [ ] Test `annotate_info`: stub axis, check `ax.text` calls (#PR)
- [ ] Test `build_info` (same as `info` but with explicit kwargs) (#PR)
- [ ] Test all setters (`set_initial_guess_info`, `set_npts`, `set_popt_psigma`, `set_TeX_argnames`, `set_TeX_function`, `set_chisq_dof`, `set_rsq`) for type/key-consistency errors (#PR)
- [ ] Test `val_uncert_2_string` with value/uncertainty pairs (e.g., `3.1415±0.01`) (#PR)

---

## 7. Justification

- [ ] Safety & regression: non-public helpers guard data integrity (#PR)
- [ ] Numerical correctness: fitting and parameter extraction must remain accurate (#PR)
- [ ] API contracts: string formats (`TeX`), plotting behaviors, and property outputs must be stable (#PR)
- [ ] Edge cases: zero-size data, insufficient observations, bad weights, solver failures—ensures graceful degradation (#PR)

