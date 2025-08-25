# Physics Examples Guide - SolarWindPy Best Practices

## Overview

This guide provides comprehensive best practices for creating physics-compliant examples in SolarWindPy. Following these guidelines ensures scientific accuracy, consistency, and maintainability across all documentation and code examples.

## Table of Contents

1. [Physics Rules and Conventions](#physics-rules-and-conventions)
2. [MultiIndex DataFrame Patterns](#multiindex-dataframe-patterns)
3. [Example Templates](#example-templates)
4. [Common Mistakes and Fixes](#common-mistakes-and-fixes)
5. [Validation and Testing](#validation-and-testing)
6. [CI/CD Integration](#cicd-integration)

## Physics Rules and Conventions

### 1. Thermal Speed Convention

**Rule**: Always use the `mw² = 2kT` convention for thermal speed calculations.

```python
# ✅ CORRECT: Calculate thermal speed from temperature
from solarwindpy.core.units_constants import Constants
const = Constants()

# For protons
k_B = const.kb  # Boltzmann constant [J/K]
m_p = const.m['p1']  # Proton mass [kg]
T_p = 1e5  # Temperature [K]

# Thermal speed: w = sqrt(2kT/m)
w_thermal = np.sqrt(2 * k_B * T_p / m_p) / 1000  # Convert to km/s

# ❌ INCORRECT: Hardcoded thermal speed values
w_thermal = 50.0  # km/s - Don't do this!
```

### 2. SI Units Convention

**Rule**: Use SI units internally for all calculations, convert to conventional units only for display.

```python
# ✅ CORRECT: SI units for calculations
density_si = 5.0 * 1e6  # Convert cm^-3 to m^-3 for calculation
magnetic_field_si = 5.0 * 1e-9  # Convert nT to T for calculation

# Calculate Alfvén speed in SI
mu_0 = 4 * np.pi * 1e-7  # Permeability [H/m]
V_A_si = B_si / np.sqrt(mu_0 * rho_si)  # [m/s]

# Convert to conventional units for display
V_A_display = V_A_si / 1000  # Convert to km/s

# ❌ INCORRECT: Mixing units in calculations
V_A = B_nT / np.sqrt(density_cm3)  # Wrong units!
```

### 3. Missing Data Handling

**Rule**: Always use `NaN` for missing data, never `0`, `-999`, or other fill values.

```python
# ✅ CORRECT: Use NaN for missing data
import numpy as np

# Mark invalid data points as NaN
velocity[invalid_indices] = np.nan
temperature[temperature < 0] = np.nan

# Handle missing data in calculations
valid_temp = temperature[~np.isnan(temperature)]

# ❌ INCORRECT: Using fill values
velocity[invalid_indices] = -999  # Don't do this!
temperature[temperature < 0] = 0   # Don't do this!
```

### 4. Alfvén Speed Calculations

**Rule**: Use the complete formula `V_A = B / √(μ₀ρ)` with proper ion composition.

```python
# ✅ CORRECT: Complete Alfvén speed calculation
def calculate_alfven_speed(B, ion_data):
    """Calculate Alfvén speed with proper ion composition."""
    mu_0 = 4 * np.pi * 1e-7  # Permeability [H/m]
    
    # Calculate mass density from ion composition
    rho = 0  # Total mass density [kg/m³]
    for species in ['p1', 'p2', 'a']:  # Include all ion species
        if species in ion_data:
            n_i = ion_data[species]['density'] * 1e6  # Convert to m^-3
            m_i = const.m[species]  # Mass [kg]
            rho += n_i * m_i
    
    # Alfvén speed [m/s]
    V_A = B / np.sqrt(mu_0 * rho)
    return V_A / 1000  # Convert to km/s

# ❌ INCORRECT: Missing μ₀ or incomplete ion composition
V_A = B / np.sqrt(rho)  # Missing μ₀
V_A = B / np.sqrt(mu_0 * n_p * m_p)  # Only protons, missing alphas
```

## MultiIndex DataFrame Patterns

### 1. Column Structure

**Rule**: Always use 3-level MultiIndex with `('M', 'C', 'S')` naming convention.

```python
# ✅ CORRECT: Proper MultiIndex structure
columns = pd.MultiIndex.from_tuples([
    ('n', '', 'p1'),        # Measurement, Component, Species
    ('v', 'x', 'p1'),       # Vector quantity needs x, y, z
    ('v', 'y', 'p1'),
    ('v', 'z', 'p1'),
    ('w', 'par', 'p1'),     # Thermal speeds: parallel/perpendicular
    ('w', 'per', 'p1'),
    ('T', '', 'p1'),        # Scalar quantity: empty component
    ('b', 'x', ''),         # Magnetic field: empty species
    ('b', 'y', ''),
    ('b', 'z', ''),
], names=['M', 'C', 'S'])  # Always specify names!

# ❌ INCORRECT: Missing names or wrong structure
columns = pd.MultiIndex.from_tuples([...])  # No names
columns = pd.MultiIndex.from_tuples([('n', 'p1')])  # Only 2 levels
```

### 2. Data Access Patterns

**Rule**: Use `.xs()` for efficient MultiIndex access, specify level names for clarity.

```python
# ✅ CORRECT: Efficient MultiIndex access
proton_density = df.xs('n', level='M').xs('p1', level='S')
velocity_components = df.xs('v', level='M').xs('p1', level='S')
magnetic_field = df.xs('b', level='M')

# Alternative: Single .xs() with tuple (faster for specific columns)
proton_density = df.xs(('n', '', 'p1'), axis=1, level=['M', 'C', 'S'])

# ❌ INCORRECT: Inefficient or unclear access
proton_density = df.loc[:, ('n', '', 'p1')].copy()  # Creates copy, slow
velocity_x = df[('v', 'x', 'p1')]  # Direct access, fragile
data = df.xs(('n', '', 'p1'), axis=1)  # No level specification
```

### 3. Index Naming

**Rule**: Time series DataFrames must use `'Epoch'` as index name.

```python
# ✅ CORRECT: Proper index naming
epoch = pd.date_range('2023-01-01', periods=100, freq='1min', name='Epoch')
df = pd.DataFrame(data, index=epoch, columns=columns)

# Alternative: Set name after creation
df.index.name = 'Epoch'

# ❌ INCORRECT: Missing or wrong index name
df = pd.DataFrame(data, index=timestamps, columns=columns)  # No name
df.index.name = 'Time'  # Wrong name
```

## Example Templates

### 1. Basic Plasma Creation

```python
import solarwindpy as swp
import numpy as np
import pandas as pd
from solarwindpy.core.units_constants import Constants

# Initialize constants
const = Constants()

# Create time series
epoch = pd.date_range('2023-01-01', periods=100, freq='1min', name='Epoch')

# Generate physical data
n_p = np.random.normal(5.0, 1.0, 100)  # Proton density [cm^-3]
v_p = np.random.normal([400, 0, 0], [50, 20, 20], (100, 3))  # Velocity [km/s]
T_p = np.random.normal(1e5, 2e4, 100)  # Temperature [K]

# Calculate thermal speed using physics convention
k_B = const.kb
m_p = const.m['p1']
w_par = np.sqrt(2 * k_B * T_p / m_p) / 1000  # Parallel thermal speed [km/s]
w_per = w_par * np.random.normal(1.0, 0.1, 100)  # Add anisotropy

# Magnetic field data
b_field = np.random.normal([5, -2, 3], [1, 1, 1], (100, 3))  # [nT]

# Create MultiIndex DataFrame
columns = pd.MultiIndex.from_tuples([
    ('n', '', 'p1'), ('v', 'x', 'p1'), ('v', 'y', 'p1'), ('v', 'z', 'p1'),
    ('w', 'par', 'p1'), ('w', 'per', 'p1'), ('T', '', 'p1'),
    ('b', 'x', ''), ('b', 'y', ''), ('b', 'z', ''),
], names=['M', 'C', 'S'])

data = pd.DataFrame({
    ('n', '', 'p1'): n_p,
    ('v', 'x', 'p1'): v_p[:, 0], ('v', 'y', 'p1'): v_p[:, 1], ('v', 'z', 'p1'): v_p[:, 2],
    ('w', 'par', 'p1'): w_par, ('w', 'per', 'p1'): w_per, ('T', '', 'p1'): T_p,
    ('b', 'x', ''): b_field[:, 0], ('b', 'y', ''): b_field[:, 1], ('b', 'z', ''): b_field[:, 2],
}, index=epoch, columns=columns)

# Create plasma object
plasma = swp.Plasma(data, 'p1')
```

### 2. MultiIndex Data Analysis

```python
# Access proton properties
proton_data = plasma.data.xs('p1', level='S')
proton_velocity = proton_data.xs('v', level='M')
proton_thermal = proton_data.xs('w', level='M')

# Calculate derived quantities
speed = np.sqrt(proton_velocity.sum(axis=1))  # Total speed
thermal_pressure = plasma.p1.thermal_pressure()  # Use built-in methods
```

### 3. Physics Calculations

```python
# Calculate Alfvén speed properly
magnetic_field = plasma.data.xs('b', level='M')  # Get B field
B_magnitude = np.sqrt((magnetic_field**2).sum(axis=1))  # |B| [nT]
B_si = B_magnitude * 1e-9  # Convert to Tesla

# Mass density including ion composition
rho_si = 0
for species in plasma.species:
    ion = getattr(plasma, species)
    n_si = ion.n.values * 1e6  # Convert cm^-3 to m^-3
    m_si = const.m[species]    # Mass [kg]
    rho_si += n_si * m_si

# Alfvén speed
mu_0 = 4 * np.pi * 1e-7
V_A = (B_si / np.sqrt(mu_0 * rho_si)) / 1000  # Convert to km/s
```

## Common Mistakes and Fixes

### 1. Physics Mistakes

| Mistake | Fix | Example |
|---------|-----|---------|
| Hardcoded thermal speeds | Calculate from temperature | `w = sqrt(2*k*T/m)` |
| Missing μ₀ in Alfvén speed | Include permeability | `V_A = B/sqrt(μ₀*ρ)` |
| Wrong thermal speed convention | Use `mw² = 2kT` | Check factor of 2 |
| Mixing units in calculations | Use SI throughout | Convert only for display |
| Using 0/-999 for missing data | Use `np.nan` | `data[invalid] = np.nan` |

### 2. MultiIndex Mistakes

| Mistake | Fix | Example |
|---------|-----|---------|
| Missing column names | Add `names=['M','C','S']` | Always specify names |
| Wrong level count | Use 3 levels always | `('M', 'C', 'S')` structure |
| Inefficient access | Use `.xs()` method | `df.xs('n', level='M')` |
| Missing level specification | Add `level=` parameter | More explicit and clear |
| Wrong index name | Use `'Epoch'` for time | `index.name = 'Epoch'` |

### 3. Performance Mistakes

| Mistake | Fix | Example |
|---------|-----|---------|
| Creating copies with `.loc` | Use `.xs()` for views | Faster and memory efficient |
| Not specifying levels | Add level names | Clearer and more maintainable |
| Inefficient data access | Batch operations | Reduce MultiIndex overhead |
| Memory waste | Use appropriate dtypes | `float32` vs `float64` |

## Validation and Testing

### 1. Physics Validation

```python
# Run physics compliance validation
python physics_compliance_validator.py your_file.py --fast

# Check specific physics rules
python physics_compliance_validator.py docs/source/usage.rst --rules thermal_speed,units
```

### 2. MultiIndex Validation

```python
# Run MultiIndex structure validation
python multiindex_structure_validator.py your_file.py --verbose

# Strict mode (warnings become errors)
python multiindex_structure_validator.py your_file.py --strict
```

### 3. Integration Testing

```python
# Run both validators together
python physics_compliance_validator.py your_file.py && \
python multiindex_structure_validator.py your_file.py
```

## CI/CD Integration

### 1. Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running physics compliance validation..."
python physics_compliance_validator.py "solarwindpy/**/*.py" --fast --ci
if [ $? -ne 0 ]; then
    echo "Physics compliance validation failed!"
    exit 1
fi

echo "Running MultiIndex structure validation..."
python multiindex_structure_validator.py "solarwindpy/**/*.py" --ci --strict
if [ $? -ne 0 ]; then
    echo "MultiIndex structure validation failed!"
    exit 1
fi

echo "All validations passed!"
```

### 2. GitHub Actions

```yaml
name: Physics Compliance Check
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -e .
        
    - name: Run physics validation
      run: |
        python physics_compliance_validator.py "solarwindpy/**/*.py" --ci --fast
        
    - name: Run MultiIndex validation  
      run: |
        python multiindex_structure_validator.py "solarwindpy/**/*.py" --ci
```

### 3. Documentation Generation

```bash
# Validate examples before building docs
python physics_compliance_validator.py docs/source/*.rst --fast
python multiindex_structure_validator.py docs/source/*.rst

# Generate compliance report
python physics_compliance_validator.py docs/source/*.rst --output compliance_report.json
```

## Best Practices Summary

### Do's ✅
- Calculate thermal speeds from temperature using `mw² = 2kT`
- Use SI units for all internal calculations
- Use `np.nan` for missing data
- Include μ₀ in Alfvén speed calculations
- Use 3-level MultiIndex with `('M', 'C', 'S')` names
- Access data efficiently with `.xs()` method
- Name time series index as `'Epoch'`
- Validate examples with automated tools
- Document physics assumptions clearly

### Don'ts ❌
- Never hardcode physical constants or derived quantities
- Don't mix units within calculations
- Don't use 0, -999, or other fill values for missing data
- Don't omit permeability or ion composition in calculations
- Don't create MultiIndex without proper names
- Don't use inefficient `.loc` or direct indexing
- Don't leave time series indices unnamed
- Don't skip validation steps
- Don't assume values without physical basis

---

This guide serves as the authoritative reference for creating physics-compliant examples in SolarWindPy. Following these patterns ensures scientific accuracy, performance, and maintainability across the entire codebase.