# Contributing to fitfunctions

This document defines the standards, conventions, and quality requirements for contributing
to the `solarwindpy.fitfunctions` module. It is standalone and will be integrated into
unified project documentation once all submodules have contribution standards.

## 1. Overview

The `fitfunctions` module provides a framework for fitting mathematical models to data
using `scipy.optimize.curve_fit`. Each fit function is a class that inherits from
`FitFunction` and implements three required abstract properties.

**Key files:**
- `core.py` - Base `FitFunction` class and exceptions
- `hinge.py`, `lines.py`, `gaussians.py`, etc. - Concrete implementations
- `tests/fitfunctions/` - Test suite

## 2. Development Workflow (TDD)

Follow Test-Driven Development with separate commits for tests and implementation:

```
1. Requirements   →  What does this function model? What are the parameters?
2. Test Writing   →  Commit: test(fitfunctions): add tests for <ClassName>
3. Implementation →  Commit: feat(fitfunctions): add <ClassName>
4. Verification   →  All tests pass, including existing tests
```

**Commit order matters:** Tests are committed before implementation. This documents the
expected behavior and ensures tests are not written to pass existing code.

## 3. FitFunction Class Requirements

### 3.1 Required Abstract Properties

Every `FitFunction` subclass MUST implement these three properties:

| Property | Returns | Purpose |
|----------|---------|---------|
| `function` | callable | The mathematical function `f(x, *params)` to fit |
| `p0` | list | Initial parameter guesses (data-driven) |
| `TeX_function` | str | LaTeX representation for plotting |

**Minimal implementation:**

```python
from .core import FitFunction

class MyFunction(FitFunction):
    r"""One-line description.

    Extended description with math:

    .. math::

        f(x) = m \cdot x + b

    Parameters
    ----------
    xobs : array-like
        Independent variable observations.
    yobs : array-like
        Dependent variable observations.
    **kwargs
        Additional arguments passed to :class:`FitFunction`.
    """

    @property
    def function(self):
        def my_func(x, m, b):
            return m * x + b
        return my_func

    @property
    def p0(self) -> list:
        assert self.sufficient_data
        x = self.observations.used.x
        y = self.observations.used.y
        # Data-driven estimation (see §3.2)
        m = (y[-1] - y[0]) / (x[-1] - x[0])
        b = y[0] - m * x[0]
        return [m, b]

    @property
    def TeX_function(self) -> str:
        return r"f(x) = m \cdot x + b"
```

### 3.2 p0 Estimation (Data-Driven)

Initial parameter guesses MUST be data-driven. Hardcoded domain values are prohibited.

**REQUIRED pattern:**

```python
@property
def p0(self) -> list:
    assert self.sufficient_data
    x = self.observations.used.x
    y = self.observations.used.y

    # Data-driven estimation examples:
    x0 = (x.max() + x.min()) / 2       # Midpoint for transitions
    y0 = np.median(y[x > x0])          # Baseline from data
    m = np.polyfit(x[:10], y[:10], 1)[0]  # Slope from segment
    A = y.max() - y.min()              # Amplitude from range

    return [x0, y0, m, A]
```

**PROHIBITED (hardcoded values):**

```python
# BAD: Domain-specific hardcoded values
x0 = 425  # Solar wind speed
m1 = 0.0163  # Kasper 2007 value
```

**Why data-driven?**
- Works on arbitrary datasets, not just solar wind
- Enables reuse across scientific domains
- Reduces "magic number" bugs

### 3.3 Optional Overrides

**Custom `__init__` with guess parameters:**

```python
def __init__(
    self,
    xobs,
    yobs,
    guess_x0: float | None = None,  # Optional user hint
    **kwargs,
):
    self._guess_x0 = guess_x0
    super().__init__(xobs, yobs, **kwargs)
```

**Derived properties:**

```python
@property
def xs(self) -> float:
    """Saturation x-coordinate (derived from fitted params)."""
    return self.popt["x1"] + self.popt["yh"] / self.popt["m1"]
```

### 3.4 Code Conventions

| Convention | Standard | Example |
|------------|----------|---------|
| Class names | PascalCase | `HingeSaturation`, `GaussianPlusHeavySide` |
| Method names | snake_case | `make_fit()`, `build_plotter()` |
| Property names | snake_case | `popt`, `TeX_function` |
| Docstrings | NumPy style with `r"""` | See example above |
| Type hints | Selective (params with defaults) | `guess_x0: float = None` |
| Imports | Relative, future annotations | `from .core import FitFunction` |
| LaTeX | Raw strings | `r"$\chi^2_\nu$"` |

**Import template:**

```python
r"""Module docstring."""

from __future__ import annotations

import numpy as np

from .core import FitFunction
```

## 4. Test Requirements

### 4.1 Test Categories (E1-E7)

Every FitFunction MUST have tests in categories E1-E5. E6-E7 are recommended where applicable.

| Category | Purpose | Tolerance | Required? |
|----------|---------|-----------|-----------|
| E1. Function Evaluation | Verify exact f(x) values | `rtol=1e-10` | YES |
| E2. Parameter Recovery (Clean) | Fit recovers known params | `rel_error < 2%` | YES |
| E3. Parameter Recovery (Noisy) | Statistical precision | `deviation < 2σ` | YES |
| E4. Initial Parameter (p0) | p0 enables convergence | `isfinite(popt)` | YES |
| E5. Edge Cases | Error handling | `raises Exception` | YES |
| E6. Derived Properties | Internal consistency | `rtol=1e-6` | If applicable |
| E7. Behavioral | Continuity, transitions | `rtol=0.1` | If applicable |

### 4.2 Fixture Pattern

All fixtures MUST return `(x, y, w, true_params)`:

```python
@pytest.fixture
def clean_gaussian_data():
    """Clean Gaussian data with known parameters."""
    true_params = {"mu": 5.0, "sigma": 1.0, "A": 10.0}
    x = np.linspace(0, 10, 200)
    y = gaussian(x, **true_params)
    w = np.ones_like(x)
    return x, y, w, true_params


@pytest.fixture
def noisy_gaussian_data():
    """Noisy Gaussian data with known parameters."""
    rng = np.random.default_rng(42)  # Deterministic seed
    true_params = {"mu": 5.0, "sigma": 1.0, "A": 10.0}
    noise_std = 0.5  # 5% of amplitude

    x = np.linspace(0, 10, 200)
    y_true = gaussian(x, **true_params)
    y = y_true + rng.normal(0, noise_std, len(x))
    w = np.ones_like(x) / noise_std

    return x, y, w, true_params
```

**Conventions:**
- Random seed: `np.random.default_rng(42)` for reproducibility
- Noise level: 3-5% of signal amplitude
- Weights: `w = np.ones_like(x) / noise_std` for noisy data

### 4.3 Assertion Patterns

**REQUIRED: Use `np.testing.assert_allclose` with `err_msg`:**

```python
np.testing.assert_allclose(
    result, expected, rtol=0.02,
    err_msg=f"param: fitted={result:.4f}, expected={expected:.4f}"
)
```

**Tolerance Reference:**

| Test Type | Tolerance | Justification |
|-----------|-----------|---------------|
| Exact math (E1) | `rtol=1e-10` | Floating point precision |
| Clean fitting (E2) | `rel_error < 0.02` | curve_fit convergence |
| Noisy fitting (E3) | `deviation < 2*sigma` | 95% confidence interval |
| Derived quantities (E6) | `rtol=1e-6` | Computed from fitted params |
| Behavioral (E7) | `rtol=0.1` | Approximate behavior |

### 4.4 Test Parameterization (REQUIRED for multi-case tests)

Use `@pytest.mark.parametrize` to avoid code duplication:

**Pattern 1: Multiple parameter sets**

```python
@pytest.mark.parametrize(
    "true_params",
    [
        {"mu": 5.0, "sigma": 1.0, "A": 10.0},   # Standard case
        {"mu": 0.0, "sigma": 0.5, "A": 5.0},    # Edge: mu at origin
        {"mu": 10.0, "sigma": 2.0, "A": 1.0},   # Edge: small amplitude
    ],
    ids=["standard", "mu_at_origin", "small_amplitude"],
)
def test_gaussian_recovers_parameters(true_params):
    """Test parameter recovery across configurations."""
    # Single test logic, multiple cases
```

**Pattern 2: Multiple classes**

```python
@pytest.mark.parametrize("cls", [Line, LineXintercept])
def test_make_fit_success(cls, simple_linear_data):
    """All line classes should fit successfully."""
    x, y, w, _ = simple_linear_data
    fit = cls(x, y)
    fit.make_fit()
    assert np.isfinite(fit.popt['m'])
```

**Best practices:**
- Use `ids=` for readable test names
- Use dict for multiple parameters
- Document each case with comments
- Include edge cases

## 5. Test Patterns (DO THIS)

| Pattern | Purpose | Example |
|---------|---------|---------|
| Analytic expected values | Verify math is correct | `expected = m * x + b` |
| Known parameter recovery | Verify fitting works | Generate data, fit, compare |
| Statistical bounds | Handle noise properly | `assert deviation < 2 * sigma` |
| Boundary conditions | Verify edge behavior | Test at x=x0 for step functions |
| Derived property consistency | Verify internal math | `assert m2 == (y2-y1)/(x2-x1)` |
| Documented tolerances | Explain precision | `rtol=0.02  # curve_fit convergence` |
| Error messages with context | Enable debugging | `err_msg=f"fitted={x:.3f}"` |
| Deterministic random seeds | Reproducibility | `rng = np.random.default_rng(42)` |

## 6. Test Anti-Patterns (DO NOT DO THIS)

| Anti-Pattern | Why It's Bad | Good Alternative |
|--------------|--------------|------------------|
| `assert fit.popt is not None` | Proves nothing about correctness | `assert_allclose(fit.popt['m'], 2.0, rtol=0.02)` |
| `assert isinstance(fit.popt, dict)` | Verifies structure, not behavior | Verify actual parameter values |
| `assert len(fit.popt) == 3` | Trivial, no math validation | Verify each parameter value |
| `rtol=0.1  # works` | Unexplained, arbitrary | `rtol=0.02  # curve_fit convergence` |
| `assert a == b` (no message) | Hard to debug failures | `assert a == b, f"got {a}, expected {b}"` |
| `rtol=1e-15` for noisy data | Flaky tests | `rtol=0.02` for fitting |
| Only test clean data | Misses real-world behavior | Include noisy data with 2σ bounds |
| `np.random.normal(...)` | Non-reproducible failures | `rng.normal(...)` with fixed seed |

## 7. Non-Trivial Test Criteria

**Definition:** A test is **non-trivial** if it would FAIL on a plausible incorrect implementation.

Every test MUST satisfy ALL of these criteria:

| Criterion | Requirement | Anti-Example |
|-----------|-------------|--------------|
| Numeric assertion | Uses `assert_allclose` with explicit tolerance | `assert popt is not None` |
| Known expected value | Expected value is analytically computed | `assert result` (truthy) |
| Justified tolerance | rtol/atol documented with reasoning | `rtol=0.1  # seems to work` |
| Failure diagnostic | Error message shows actual vs expected | Bare `AssertionError` |
| Mathematical meaning | Tests a model property, not structure | `assert len(popt) == 4` |
| Would fail if broken | A plausible bug would cause failure | Test that always passes |

**Example non-trivial test:**

```python
def test_line_evaluates_correctly():
    """Line: f(x) = m*x + b should give exact values.

    Non-trivial because:
    - Tests specific numeric values, not just "runs"
    - Would fail if formula were m*x - b (sign error)
    - Tolerance is 1e-10 (floating point, not fitting)
    """
    m, b = 2.0, 1.0
    x = np.array([0.0, 1.0, 2.0])
    expected = np.array([1.0, 3.0, 5.0])  # Analytically computed

    fit = Line(x, expected)
    result = fit.function(x, m, b)

    np.testing.assert_allclose(
        result, expected, rtol=1e-10,
        err_msg=f"Line(x, m={m}, b={b}) should equal m*x + b"
    )
```

## 8. Quality Checklist

Before submitting a PR, verify:

- [ ] All 3 abstract properties implemented (`function`, `p0`, `TeX_function`)
- [ ] p0 is data-driven (no hardcoded domain values)
- [ ] Tests cover categories E1-E5 minimum
- [ ] All tests are non-trivial (pass criteria in §7)
- [ ] Docstrings complete with `.. math::` blocks
- [ ] `make_fit()` converges on clean data
- [ ] `make_fit()` within 2σ on noisy data
- [ ] Class exported in `__init__.py`
- [ ] No regressions (all existing tests pass)

## 9. Complete Examples

For complete implementation examples, see:

- **Implementation:** `hinge.py:HingeSaturation` (lines 20-180)
- **Tests:** `tests/fitfunctions/test_hinge.py:TestHingeSaturation`

For test organization patterns:

- **Parameterization:** `tests/fitfunctions/test_composite.py` (lines 359-365)
- **Fixtures:** `tests/fitfunctions/test_hinge.py` (fixture definitions)
- **Categories E1-E7:** `tests/fitfunctions/test_heaviside.py` (section headers)
