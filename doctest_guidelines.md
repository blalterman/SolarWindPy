# Doctest Guidelines for SolarWindPy

## Overview

This guide provides comprehensive best practices for writing maintainable, physics-compliant doctests in SolarWindPy. Following these guidelines ensures scientific accuracy, consistent documentation, and reliable automated testing.

## Table of Contents

1. [Basic Doctest Structure](#basic-doctest-structure)
2. [Physics Compliance Rules](#physics-compliance-rules)
3. [MultiIndex DataFrame Patterns](#multiindex-dataframe-patterns)
4. [Example Data Generation](#example-data-generation)
5. [Common Patterns](#common-patterns)
6. [Testing Guidelines](#testing-guidelines)
7. [CI/CD Integration](#cicd-integration)

## Basic Doctest Structure

### Standard Format

```python
def calculate_thermal_speed(temperature, mass=1.67262192e-27):
    """Calculate thermal speed from temperature using mw² = 2kT convention
    
    Parameters
    ----------
    temperature : float or array_like
        Particle temperature [K]
    mass : float, optional
        Particle mass [kg] (default: proton mass)
    
    Returns
    -------
    float or array_like
        Thermal speed [km/s]
    
    Examples
    --------
    >>> import numpy as np
    >>> T_p = 1e5  # 100,000 K
    >>> w_thermal = calculate_thermal_speed(T_p)
    >>> 40 < w_thermal < 50  # Typical range for protons
    True
    
    >>> # Array input
    >>> temperatures = np.array([5e4, 1e5, 2e5])
    >>> speeds = calculate_thermal_speed(temperatures)
    >>> len(speeds)
    3
    >>> (speeds > 0).all()
    True
    """
    k_B = 1.380649e-23  # Boltzmann constant [J/K]
    return np.sqrt(2 * k_B * temperature / mass) / 1000  # Convert to km/s
```

### Key Elements

- **Clear description**: Explain what the function does and why
- **Parameter documentation**: Include units and physical meaning
- **Physics examples**: Use realistic values and ranges
- **Verification tests**: Check results make physical sense
- **Error handling**: Show expected behavior for edge cases

## Physics Compliance Rules

### 1. Thermal Speed Convention

**✅ CORRECT**: Calculate from temperature using mw² = 2kT
```python
>>> from doctest_fixtures import create_example_plasma_data
>>> data = create_example_plasma_data()
>>> T_p = data.xs(('T', '', 'p1'), axis=1).iloc[0]
>>> k_B, m_p = 1.380649e-23, 1.67262192e-27
>>> w_expected = np.sqrt(2 * k_B * T_p / m_p) / 1000
>>> w_actual = data.xs(('w', 'par', 'p1'), axis=1).iloc[0]
>>> abs(w_actual - w_expected) / w_expected < 0.01
True
```

**❌ INCORRECT**: Hardcoded values
```python
>>> # Don't do this!
>>> w_thermal = 50.0  # km/s - arbitrary value
```

### 2. SI Units Convention

**✅ CORRECT**: Use SI internally, convert for display
```python
>>> # Internal calculation in SI units
>>> density_si = 5.0 * 1e6  # Convert cm^-3 to m^-3
>>> B_si = 5.0 * 1e-9      # Convert nT to T
>>> mu_0 = 4 * np.pi * 1e-7
>>> V_A_si = B_si / np.sqrt(mu_0 * density_si * 1.67262192e-27)
>>> V_A_display = V_A_si / 1000  # Convert to km/s for display
>>> 10 < V_A_display < 100  # Typical Alfvén speed range
True
```

### 3. Missing Data Handling

**✅ CORRECT**: Use NaN for missing data
```python
>>> import numpy as np
>>> data = np.array([1.0, 2.0, np.nan, 4.0])
>>> valid_data = data[~np.isnan(data)]
>>> len(valid_data)
3
```

**❌ INCORRECT**: Fill values
```python
>>> # Don't use -999, 0, or other fill values
>>> data[invalid_indices] = -999  # Wrong!
```

### 4. Alfvén Speed Calculations

**✅ CORRECT**: Include μ₀ and proper ion composition
```python
>>> # Complete Alfvén speed calculation
>>> B_magnitude = 5.0  # nT
>>> n_p = 5.0  # cm^-3
>>> mu_0 = 4 * np.pi * 1e-7  # H/m
>>> m_p = 1.67262192e-27  # kg
>>> 
>>> # Convert to SI units
>>> B_si = B_magnitude * 1e-9  # T
>>> rho_si = n_p * 1e6 * m_p   # kg/m^3
>>> 
>>> V_A = B_si / np.sqrt(mu_0 * rho_si) / 1000  # km/s
>>> 20 < V_A < 80  # Typical range
True
```

## MultiIndex DataFrame Patterns

### 1. Proper Column Structure

**✅ CORRECT**: 3-level MultiIndex with names
```python
>>> from doctest_fixtures import create_example_plasma_data
>>> data = create_example_plasma_data()
>>> data.columns.names
['M', 'C', 'S']
>>> len(data.columns.levels)
3
```

### 2. Efficient Data Access

**✅ CORRECT**: Use .xs() with level specification
```python
>>> # Access proton density efficiently
>>> proton_density = data.xs('n', level='M').xs('p1', level='S')
>>> len(proton_density)
10

>>> # Access all velocity components
>>> velocity_data = data.xs('v', level='M').xs('p1', level='S')
>>> list(velocity_data.columns)
['x', 'y', 'z']

>>> # Single operation for specific column
>>> v_x = data.xs(('v', 'x', 'p1'), axis=1, level=['M', 'C', 'S'])
>>> len(v_x)
10
```

### 3. Index Naming

**✅ CORRECT**: Time series must use 'Epoch'
```python
>>> data.index.name
'Epoch'
>>> isinstance(data.index, pd.DatetimeIndex)
True
```

## Example Data Generation

### Use Standard Fixtures

Always use provided fixtures for consistent examples:

```python
>>> from doctest_fixtures import create_example_plasma_data, create_example_ion_data
>>> 
>>> # Full plasma data
>>> plasma_data = create_example_plasma_data(n_points=5)
>>> plasma_data.shape
(5, 8)
>>> 
>>> # Single species data
>>> proton_data = create_example_ion_data('p1', n_points=5)
>>> proton_data.shape
(5, 5)
>>> 
>>> # Custom epoch
>>> import pandas as pd
>>> epoch = pd.date_range('2023-06-01', periods=3, freq='1H', name='Epoch')
>>> custom_data = create_example_plasma_data(epoch=epoch)
>>> len(custom_data)
3
```

### Reproducible Random Data

When generating custom data, always set seed:

```python
>>> import numpy as np
>>> np.random.seed(42)  # For reproducible results
>>> test_values = np.random.normal(100, 10, 5)
>>> len(test_values)
5
>>> 95 < test_values[0] < 105  # First value should be consistent
True
```

## Common Patterns

### 1. Plasma Object Creation

```python
>>> from doctest_fixtures import create_test_plasma_object
>>> plasma = create_test_plasma_object(n_points=5)
>>> hasattr(plasma, 'p1')
True
>>> plasma.p1.n.iloc[0] > 0
True
>>> len(plasma.p1.v)
5
```

### 2. Unit Conversions

```python
>>> # Density: cm^-3 to m^-3
>>> n_cm3 = 5.0
>>> n_si = n_cm3 * 1e6
>>> n_si
5000000.0

>>> # Magnetic field: nT to T
>>> B_nT = 10.0
>>> B_si = B_nT * 1e-9
>>> B_si
1e-08

>>> # Velocity: km/s (already SI-compatible)
>>> v_kms = 400.0  # km/s
>>> v_ms = v_kms * 1000  # m/s for SI calculations
>>> v_ms
400000.0
```

### 3. Physics Calculations

```python
>>> # Thermal pressure calculation
>>> k_B = 1.380649e-23
>>> n_si = 5e6  # m^-3
>>> T = 1e5     # K
>>> P_thermal = n_si * k_B * T  # Pa
>>> P_thermal > 0
True

>>> # Magnetic pressure
>>> B_si = 5e-9  # T
>>> mu_0 = 4 * np.pi * 1e-7
>>> P_mag = B_si**2 / (2 * mu_0)  # Pa
>>> P_mag > 0
True
```

### 4. Data Validation

```python
>>> from doctest_fixtures import validate_physics_relationships
>>> data = create_example_plasma_data()
>>> validation = validate_physics_relationships(data)
>>> validation['thermal_speed_consistency']
True
>>> validation['positive_quantities']  
True
```

## Testing Guidelines

### 1. Test Realistic Ranges

```python
>>> # Solar wind ranges
>>> velocity = create_example_plasma_data().xs(('v', 'x', 'p1'), axis=1)
>>> (200 <= velocity).all() and (velocity <= 800).all()
True

>>> density = create_example_plasma_data().xs(('n', '', 'p1'), axis=1) 
>>> (0.1 <= density).all() and (density <= 50).all()
True
```

### 2. Test Edge Cases

```python
>>> # Test with minimal data
>>> minimal_data = create_example_plasma_data(n_points=1)
>>> len(minimal_data)
1

>>> # Test with different species
>>> try:
...     alpha_data = create_example_ion_data('a')
...     success = False  # Should fail without include_alphas
>>> except ValueError:
...     success = True
>>> success
True
```

### 3. Test Error Conditions

```python
>>> # Test invalid inputs
>>> try:
...     invalid_data = create_example_ion_data('invalid_species')
...     error_raised = False
>>> except ValueError:
...     error_raised = True
>>> error_raised
True
```

## Best Practices

### Do's ✅

1. **Use fixtures**: Always use `create_example_plasma_data()` and related functions
2. **Set random seeds**: Use `np.random.seed(42)` for reproducible results
3. **Check physical ranges**: Verify results are in realistic ranges
4. **Include units**: Always specify units in comments and documentation
5. **Test positive quantities**: Ensure densities, temperatures > 0
6. **Use .xs() for MultiIndex**: More efficient than .loc for MultiIndex access
7. **Specify levels**: Always use `level=` parameter in .xs() calls
8. **Name time indices**: Use `'Epoch'` for time series index names

### Don'ts ❌

1. **Don't hardcode physics values**: Calculate from first principles
2. **Don't use fill values**: Use `np.nan` for missing data
3. **Don't mix units**: Keep SI internally, convert only for display
4. **Don't create large datasets**: Use small examples (≤10 points) in doctests
5. **Don't ignore physics**: All examples should be scientifically realistic
6. **Don't use .loc for MultiIndex**: Use .xs() for better performance
7. **Don't omit level specification**: Be explicit about which level you're accessing

### Example Structure Template

```python
def your_function(parameter):
    """Brief description with physics context
    
    Longer description explaining the physics principles and
    conventions used in this function.
    
    Parameters
    ----------
    parameter : type
        Description with units [unit]
    
    Returns
    -------
    type
        Description with units [unit]
    
    Examples
    --------
    >>> # Basic usage with realistic values
    >>> from doctest_fixtures import create_example_plasma_data
    >>> data = create_example_plasma_data(n_points=3)
    >>> result = your_function(data)
    >>> len(result)
    3
    
    >>> # Test physics compliance
    >>> # Include checks that verify physical correctness
    >>> (result > 0).all()  # For positive quantities
    True
    
    >>> # Test edge cases
    >>> # Show behavior with minimal or boundary inputs
    >>> edge_result = your_function(minimal_input)
    >>> isinstance(edge_result, expected_type)
    True
    """
    # Implementation here
    pass
```

## CI/CD Integration

### Running Doctest Validation

```bash
# Run all doctests with physics validation
python doctest_physics_validator.py solarwindpy/

# Quick check for pre-commit hooks
python doctest_physics_validator.py solarwindpy/ --quick-check

# Generate detailed report
python doctest_physics_validator.py solarwindpy/ \
  --output-report doctest_results.json \
  --text-report doctest_report.txt
```

### Pre-commit Hook Integration

Add to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: doctest-physics-validation
      name: Validate doctests with physics rules
      entry: python doctest_physics_validator.py
      language: system
      files: \.py$
      args: [--quick-check]
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all required imports are included in examples
2. **Random Seed Issues**: Always set `np.random.seed(42)` for reproducible results
3. **Physics Violations**: Use physics-compliant calculations, not hardcoded values
4. **MultiIndex Errors**: Verify column structure with `data.columns.names`
5. **Unit Inconsistencies**: Keep SI units internal, convert only for display

### Debugging Tips

1. **Test incrementally**: Start with simple examples, add complexity gradually
2. **Check intermediate results**: Verify physics at each calculation step
3. **Use validation functions**: Call `validate_physics_relationships()` to check compliance
4. **Review error messages**: Physics validator provides specific guidance
5. **Compare with fixtures**: Use standard fixtures as reference implementations

---

Following these guidelines ensures that all SolarWindPy doctests maintain scientific accuracy while providing clear, maintainable documentation for users and contributors.