# Test Plan for `solarwindpy.fitfunctions` (update-2025 branch)

> **Goal:** Verify correctness, robustness, and full coverage (public & non‐public APIs) of the `fitfunctions` submodule.\
> **Framework:** `pytest` + fixtures; follow AGENTS.md guidelines (`pytest -q`, no skipping, style with `flake8` & `black`).

---

## 1. Common fixtures

```python
import numpy as np
import pandas as pd
import pytest
from scipy.optimize import OptimizeResult

from solarwindpy.fitfunctions import core, gaussians, trend_fits, plots, tex_info
```

- ``: 1D arrays `x = np.linspace(0,1,20)`, `y = 2*x + 1 + noise`, `w = np.ones_like(x)`.
- ``: sample `x`, generate `y = A·exp(−0.5((x−μ)/σ)²)` + small noise.
- ``: too few points to trigger `sufficient_data → ValueError`.

---

## 2. core.py → `FitFunction`

### 2.1 Initialization & observation filtering

- ``
  - Mismatched shapes → `ValueError`.
  - Valid inputs → arrays returned.
- ``
  - Test with `xmin`, `xmax`, `None` → masks correct.
- ``
  - `outside=None` → all `True`.
  - Valid tuple → only outside points `True`.
- ``
  - Combined masks apply correctly for `x`, `y`, `wmin`, `wmax` and `logy`.

### 2.2 Argument introspection

- ``
  - On subclass with known signature → `argnames` matches function arguments.

### 2.3 Fitting workflow

- ``
  - Monkey-patch `scipy.optimize.least_squares` to return dummy `OptimizeResult`.
  - Test default kwargs (`loss`, `method`, etc.).
  - Passing invalid `args` kwarg → `ValueError`.
- ``
  - Feed dummy `res` with known `fun`, `jac`, produce known `popt`, `pcov`, `psigma`, `chisq`.
- ``
  - **Success:** returns `None`, sets `_popt`, `_psigma`, `_pcov`, `_chisq_dof`, `_fit_result`, builds `TeX_info` & `plotter`.
  - **Insufficient data:** returns `ValueError` if `return_exception=True`.
  - **Optimization failure:** raised `RuntimeError` or returned exception.

### 2.4 Public properties

- `` → `"<ClassName> (<TeX_function>)"`.
- `` → returns `function(x,*popt)` array.
- **Properties:**
  - `argnames`, `fit_bounds`, `chisq_dof`, `dof`, `fit_result`,
  - `initial_guess_info`, `nobs`, `observations`, `plotter`,
  - `popt`, `psigma`, `psigma_relative`, `combined_popt_psigma`, `pcov`, `rsq`,
  - `sufficient_data`, `TeX_info`.
- **Test:** after a dummy fit, each property yields expected dtype/shape/value.

---

## 3. gaussians.py → `Gaussian`, `GaussianNormalized`, `GaussianLn`

For each class:

### 3.1 Signature & `function` property

- Call `.function`, inspect returned callable’s signature and behavior on sample `x`.

### 3.2 `p0` initial guesses

- With synthetic Gaussian data → `p0` ≈ true `[μ,σ,A]` (tolerance).
- Empty data → triggers the zero-size‐array `ValueError`.

### 3.3 `TeX_function`

- Matches expected LaTeX string literal.

### 3.4 `make_fit` override

- On success → calls base `make_fit`, sets `TeX_argnames` in `TeX_info`.
- On forced failure (monkey-patch optimizer) → no exception in `make_fit`, leaves TeX\_argnames unset.

---

## 4. trend\_fits.py → `TrendFit`

### 4.1 Initialization & type enforcement

- Valid `agged: pd.DataFrame`, `trendfunc: FitFunction` subclass → no error.
- Invalid `ffunc1d` or `trendfunc` → raises `TypeError`.

### 4.2 Properties

- `__str__`, `agged`, `ffunc1d_class`, `trendfunc_class`, `ffuncs` (after `make_ffunc1ds`),\
  `popt_1d`, `psigma_1d`, `trend_func`, `bad_fits`, `popt1d_keys`, `trend_logx`, `labels`.

### 4.3 1D‐fit pipeline

- ``: builds `Series` of `FitFunction` instances.
- ``: mark bad fits (return value ≠ `None`), remove them from `ffuncs` → `bad_fits` populated.

### 4.4 Trend fitting

- ``: with valid `popt_1d`, builds `trend_func`; insufficient fits → `ValueError`.

### 4.5 Plot helpers

- `plot_all_ffuncs`, `plot_all_popt_1d`, `plot_trend_fit_resid`, `plot_trend_and_resid_on_ffuncs`, `plot_1d_popt_and_trend`
  - Stub out plotting (monkey-patch `.plotter` methods to record calls), ensure axes returned.

### 4.6 Label sharing

- `set_agged` type check; `set_fitfunctions` logic; `set_shared_labels` updates label objects.

---

## 5. plots.py → `FFPlot`

### 5.1 Initialization & basic attributes

- `__init__` with dummy `Observations`, `y_fit`, `TeXinfo`, dummy `OptimizeResult`, `fitfunction_name` → no errors.
- `__str__`, `labels`, `log` default `(False,False)`, `observations`, `fitfunction_name`, `fit_result`, `y_fit`.

### 5.2 Path generation

- Vary `labels.x`, `labels.y`, optional `labels.z` → `path` property concatenates correctly.

### 5.3 State mutators

- `set_fitfunction_name`, `set_fit_result`, `set_observations` (shape assertions).

### 5.4 Internal helpers

- `` with small & huge `observations.used.x.size`.
- ``, ``: stub axes → grid/scale calls, ensure correct axes methods invoked.

### 5.5 Plot methods

- ``, ``, ``, ``, ``, ``
  - Provide dummy axes (monkey-patch `plt.subplots`) and assert returned axes and legend/text behavior.
  - For `pct=True/False`, robust branch, missing `fit_result.fun` → skip second curve.

### 5.6 Label & style setters

- `` updates `labels` namedtuple, unexpected key → `KeyError`.
- `` toggles `log` flags.
- `` stores `TeXinfo`.

---

## 6. tex\_info.py → `TeXinfo`

### 6.1 Construction & storage

- Valid inputs; invalid types → `TypeError`/`ValueError` in setters.

### 6.2 Properties & formatting

- ``** / **`` with flags combinations.
- ``**, **``**, **``**, **``**, **``**, **``**, **``**, **``**, **``**, **``.

### 6.3 Static/private helpers

- ``: odd `$` → `ValueError`.
- ``, ``, ``, ``, ``, ``, **setters**, ``.

---

## 7. Justification

1. **Safety & regression**: non‐public helpers guard data integrity.
2. **Numerical correctness**: fitting and parameter extraction must remain accurate.
3. **API contracts**: string formats (`TeX`), plotting behaviors, and property outputs must be stable.
4. **Edge cases**: zero‐size data, insufficient observations, bad weights, solver failures—ensures graceful degradation.

*Aligns with AGENTS.md:* run with `pytest -q`, enforce no skipped tests, maintain code style with `flake8` & `black`.

