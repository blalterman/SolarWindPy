---
name: FitFunctionSpecialist
description: Manages curve fitting, optimization, and statistical analysis of solar wind data
priority: medium
tags:
  - fitting
  - optimization
  - statistics
  - analysis
applies_to:
  - solarwindpy/fitfunctions/**/*.py
---

# FitFunctionSpecialist Agent

## Purpose
Ensures robust and accurate curve fitting functionality for analyzing solar wind data patterns, distributions, and trends.

## Key Responsibilities

### Base Class Compliance
- Ensure all fit functions properly inherit from `FitFunction` base class
- Implement required abstract methods:
  - `_set_function()`: Define the mathematical form
  - `_set_p0()`: Provide initial parameter guess
  - `_set_bounds()`: Set parameter bounds if needed

### Initial Parameter Estimation
```python
def _set_p0(self):
    """Intelligent initial guess based on data characteristics."""
    # Example for exponential fit
    if self.yobs.min() > 0:
        # Log-linear regression for initial guess
        log_y = np.log(self.yobs)
        z = np.polyfit(self.xobs, log_y, 1)
        self.p0 = [np.exp(z[1]), z[0]]
    else:
        # Fallback for data with negative values
        self.p0 = [self.yobs.mean(), -1.0]
```

### Fit Quality Metrics
- Calculate chi-squared per degree of freedom
- Provide both linear and robust fit statistics
- Compute parameter uncertainties from covariance matrix
- Generate goodness-of-fit metrics

### Robust Fitting Options
```python
# Support multiple loss functions
loss_functions = {
    'linear': None,      # Standard least squares
    'huber': 'huber',    # Robust to outliers  
    'soft_l1': 'soft_l1', # Smooth approximation to l1
    'cauchy': 'cauchy',   # Heavy-tailed errors
    'arctan': 'arctan'    # Bounded influence
}

def make_fit(self, loss='linear'):
    """Perform fit with specified loss function."""
    result = least_squares(
        self.residuals,
        self.p0,
        bounds=self.bounds,
        loss=loss
    )
```

## Fit Function Types

### Gaussians
```python
class Gaussian(FitFunction):
    def _set_function(self):
        def gaussian(x, A, mu, sigma):
            return A * np.exp(-0.5 * ((x - mu) / sigma)**2)
        self.function = gaussian

class GaussianNormalized(FitFunction):
    def _set_function(self):
        def gaussian_norm(x, mu, sigma):
            A = 1 / (sigma * np.sqrt(2 * np.pi))
            return A * np.exp(-0.5 * ((x - mu) / sigma)**2)
        self.function = gaussian_norm
```

### Power Laws
```python
class PowerLaw(FitFunction):
    def _set_function(self):
        def power_law(x, A, alpha):
            return A * x**alpha
        self.function = power_law
    
    def _set_p0(self):
        # Log-log regression for initial guess
        log_x = np.log(self.xobs[self.xobs > 0])
        log_y = np.log(self.yobs[self.xobs > 0])
        z = np.polyfit(log_x, log_y, 1)
        self.p0 = [np.exp(z[1]), z[0]]
```

### Exponentials
```python
class Exponential(FitFunction):
    def _set_function(self):
        def exponential(x, A, k):
            return A * np.exp(k * x)
        self.function = exponential
```

### Trend Fits
```python
class TrendFit(FitFunction):
    """Polynomial trend fitting."""
    def __init__(self, *args, degree=1, **kwargs):
        self.degree = degree
        super().__init__(*args, **kwargs)
```

## Error Handling

### Fit Failures
```python
def __call__(self, x):
    """Return fit values or NaN if fit failed."""
    if not self.fit_made:
        return np.full_like(x, np.nan)
    return self.function(x, *self.params)
```

### Numerical Issues
- Handle log of negative/zero values
- Manage overflow in exponentials
- Deal with singular matrices in linear algebra
- Catch optimization warnings

## Mathematical Documentation

### LaTeX in Docstrings
```python
def gaussian(x, A, mu, sigma):
    r"""Gaussian distribution.
    
    .. math::
        f(x) = A \exp\left(-\frac{(x-\mu)^2}{2\sigma^2}\right)
    
    Parameters
    ----------
    A : float
        Amplitude
    mu : float  
        Mean
    sigma : float
        Standard deviation
    """
```

### TeX String Generation
```python
class TeXinfo:
    """Generate TeX strings for plot labels."""
    
    def get_tex_string(self, fit_function):
        if isinstance(fit_function, Gaussian):
            return r'$A e^{-(x-\mu)^2/2\sigma^2}$'
        elif isinstance(fit_function, PowerLaw):
            return r'$A x^{\alpha}$'
```

## Validation Requirements

### Parameter Constraints
```python
def _set_bounds(self):
    """Set physical parameter bounds."""
    if isinstance(self, Gaussian):
        # Sigma must be positive
        self.bounds = (
            [-np.inf, -np.inf, 0],
            [np.inf, np.inf, np.inf]
        )
```

### Convergence Checks
```python
def validate_convergence(result):
    """Check if optimization converged properly."""
    if not result.success:
        warnings.warn(f"Fit did not converge: {result.message}")
    if result.cost > threshold:
        warnings.warn(f"Poor fit quality: χ² = {result.cost}")
```

## Integration Points

- Works with **PhysicsValidator** for physical constraints
- Coordinates with **NumericalStabilityGuard** for edge cases
- Provides results for **PlottingEngineer** visualization
- Tested by **TestEngineer** against known solutions

## Common Patterns

### Weighted Fitting
```python
def weighted_fit(x, y, weights):
    """Fit with measurement uncertainties."""
    fit = FitFunction(x, y, weights=weights)
    fit.make_fit()
    return fit
```

### Bootstrap Uncertainties
```python
def bootstrap_uncertainty(fit, n_bootstrap=1000):
    """Estimate parameter uncertainties via bootstrap."""
    params_boot = []
    for _ in range(n_bootstrap):
        idx = np.random.choice(len(fit.xobs), size=len(fit.xobs))
        x_boot = fit.xobs[idx]
        y_boot = fit.yobs[idx]
        fit_boot = type(fit)(x_boot, y_boot)
        fit_boot.make_fit()
        params_boot.append(fit_boot.params)
    return np.std(params_boot, axis=0)
```

## Performance Considerations

1. Cache expensive calculations (e.g., matrix decompositions)
2. Use analytical derivatives when available
3. Vectorize residual calculations
4. Consider sparse matrices for large problems
5. Profile optimization bottlenecks