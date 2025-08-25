# Example Templates for SolarWindPy Documentation

## Phase 4 Deliverable: Reusable Code Example Patterns

This document provides standardized templates for creating reliable, executable examples in SolarWindPy documentation.

## Template 1: Basic Plasma Object Creation

### Use Case: 
Creating a Plasma object with proper MultiIndex DataFrame structure

### Template:
```python
import solarwindpy as swp
import pandas as pd
import numpy as np

# Create sample data
epoch = pd.date_range('2023-01-01', periods=100, freq='1min')

# Ion moment data
n_p = np.random.normal(5.0, 1.0, 100)     # cm^-3 (density)
v_p = np.random.normal(400, 50, (100, 3)) # km/s (velocity)
w_thermal = np.random.normal(50, 10, 100) # km/s (thermal speed)

# Magnetic field data (required)
b_field = np.random.normal([5, -2, 3], [1, 1, 1], (100, 3))  # nT

# Create MultiIndex DataFrame structure
columns = pd.MultiIndex.from_tuples([
    ('n', '', 'p1'),    # Proton density
    ('v', 'x', 'p1'),   # Proton velocity components
    ('v', 'y', 'p1'),   
    ('v', 'z', 'p1'),   
    ('w', 'par', 'p1'), # Thermal speeds
    ('w', 'per', 'p1'), 
    ('b', 'x', ''),     # Magnetic field (required)
    ('b', 'y', ''),     
    ('b', 'z', ''),     
], names=['M', 'C', 'S'])

data = pd.DataFrame({
    ('n', '', 'p1'): n_p,
    ('v', 'x', 'p1'): v_p[:, 0],
    ('v', 'y', 'p1'): v_p[:, 1],
    ('v', 'z', 'p1'): v_p[:, 2],
    ('w', 'par', 'p1'): w_thermal,
    ('w', 'per', 'p1'): w_thermal,
    ('b', 'x', ''): b_field[:, 0],
    ('b', 'y', ''): b_field[:, 1],
    ('b', 'z', ''): b_field[:, 2],
}, index=epoch, columns=columns)

# Create plasma object
plasma = swp.Plasma(data, 'p1')
```

### Key Requirements:
- ✅ Must include magnetic field data ('b', 'x/y/z', '')
- ✅ Use proper MultiIndex column structure ('M', 'C', 'S')
- ✅ Include ion species in constructor: `Plasma(data, 'p1')`
- ✅ Never use deprecated `epoch=` parameter

## Template 2: Ion Property Access

### Use Case:
Accessing ion moments and derived quantities

### Template:
```python
# Access ion properties (assuming plasma object exists)
proton_density = plasma.p1.n      # Number density [cm^-3]
proton_velocity = plasma.p1.v     # Velocity vector [km/s]
thermal_speed = plasma.p1.thermal_speed()  # Thermal speed tensor

# Plasma physics calculations
beta = plasma.beta('p1')          # Plasma beta for protons

# Data access via MultiIndex
density_data = plasma.data.xs('n', level='M').xs('p1', level='S')
velocity_x = plasma.data.xs('v', level='M').xs('x', level='C').xs('p1', level='S')
```

### Key Requirements:
- ✅ Use `.p1` attribute access for ions (not `get_ion('p1')`)
- ✅ Use `plasma.beta('species')` method (not ion-level beta)
- ✅ Use `.xs()` for MultiIndex data access

## Template 3: Plotting with Matplotlib

### Use Case:
Creating scientific visualizations

### Template:
```python
import matplotlib.pyplot as plt
import solarwindpy.plotting.labels as labels

# Time series plot (assuming plasma object exists)
fig, ax = plt.subplots()
proton_density = plasma.data.xs('n', level='M').xs('p1', level='S')
ax.plot(proton_density.index, proton_density.values)
ax.set_ylabel(labels.density('p1'))
ax.set_title('Proton Density Time Series')
plt.show()

# Scatter plot
fig, ax = plt.subplots()
vx = plasma.data.xs('v', level='M').xs('x', level='C').xs('p1', level='S')
temp = plasma.data.xs('w', level='M').xs('par', level='S').xs('p1', level='S')
ax.scatter(vx, temp)
ax.set_xlabel(labels.velocity_x('p1'))
ax.set_ylabel(labels.thermal_speed_par('p1'))
plt.show()
```

### Key Requirements:
- ✅ Use standard `matplotlib.pyplot` (not non-existent solarwindpy plotting functions)
- ✅ Use `solarwindpy.plotting.labels` for scientific labels
- ✅ Access data via `.xs()` method with proper level specification

## Template 4: Fit Functions

### Use Case:
Statistical analysis and curve fitting

### Template:
```python
from solarwindpy.fitfunctions import Gaussian

# Prepare data for fitting (assuming plasma object exists)
w_par = plasma.data.xs('w', level='M').xs('par', level='C').xs('p1', level='S')
x_data = w_par.index.astype('int64') // 10**9  # Convert to seconds
y_data = w_par.values

# Create and execute fit
fit = Gaussian(x_data, y_data)
fit.fit()

# Access results
fit_params = fit.best_fit_parameters
```

### Key Requirements:
- ✅ Provide both `xobs` and `yobs` parameters to Gaussian constructor
- ✅ Prepare data appropriately (convert timestamps, extract values)
- ✅ Call `.fit()` method after construction

## Template 5: Instability Analysis

### Use Case:
Plasma instability calculations

### Template:
```python
from solarwindpy.instabilities.verscharen2016 import beta_ani_inst

# Calculate plasma betas (assuming plasma object exists)
beta_par = plasma.beta('p1').par
beta_per = plasma.beta('p1').per

# Check instability threshold
instability_threshold = beta_ani_inst(beta_par)
```

### Key Requirements:
- ✅ Use full import path: `solarwindpy.instabilities.verscharen2016`
- ✅ Access beta components: `plasma.beta('species').par/per`
- ✅ Function name is `beta_ani_inst` (not `beta_ani_instability`)

## Template 6: Docstring Examples

### Use Case:
Self-contained examples in function/class docstrings

### Template:
```python
"""
Example function with proper doctest.

Examples
--------
>>> import pandas as pd
>>> import numpy as np
>>> columns = pd.MultiIndex.from_tuples([
...     ('n', '', 'p1'), ('v', 'x', 'p1')
... ], names=['M', 'C', 'S'])
>>> df = pd.DataFrame([[1, 400], [2, 450]], columns=columns)
>>> result = example_function(df)
>>> len(result)  # Verifiable output
2
"""
```

### Key Requirements:
- ✅ Include all necessary imports within the doctest
- ✅ Create complete, minimal data structures
- ✅ Use verifiable outputs (lengths, types, simple values)
- ✅ Follow proper doctest syntax with `>>>` and `...`

## Template 7: Physics Validation

### Use Case:
Checking physical constraints and data quality

### Template:
```python
# Manual physics validation (assuming plasma object exists)
# Check positive densities
assert (plasma.p1.n > 0).all(), "Density must be positive"

# Check positive thermal speeds  
thermal_data = plasma.data.xs('w', level='M')
assert (thermal_data > 0).all().all(), "Thermal speeds must be positive"

# Check for missing data (NaN handling)
data_with_gaps = plasma.data.dropna()
missing_fraction = (len(plasma.data) - len(data_with_gaps)) / len(plasma.data)
print(f"Missing data: {missing_fraction:.1%}")
```

### Key Requirements:
- ✅ Use manual assertions instead of non-existent `validate_physics()` method
- ✅ Check realistic physics constraints (positive values, reasonable ranges)
- ✅ Handle missing data as NaN (never 0 or -999 fill values)

## Anti-Patterns to Avoid

### ❌ Deprecated/Non-existent APIs
```python
# WRONG - These don't exist:
plasma = swp.Plasma(epoch=epoch)           # No epoch parameter
plasma.add_ion_species(...)                # Method doesn't exist
plasma.validate_physics()                  # Method doesn't exist
plasma.alfven_speed()                      # Method doesn't exist
plasma.get_ion('p1')                       # Use plasma.p1 instead
swpp.time_series(...)                      # Function doesn't exist
```

### ❌ Incomplete Data Setup
```python
# WRONG - Missing required magnetic field:
data = pd.DataFrame({('n', '', 'p1'): density})  # Plasma needs 'b' field

# WRONG - Undefined variables in examples:
proton_density = plasma.p1.n  # Where did 'plasma' come from?
```

### ❌ Incorrect Import Paths
```python
# WRONG:
from solarwindpy.instabilities import beta_ani_inst    # Wrong module
from solarwindpy.tools.units_constants import constants # Wrong structure
```

## Success Validation Checklist

For any new example, verify:

- [ ] **Imports**: All necessary imports included and paths correct
- [ ] **Data Structure**: Proper MultiIndex with ('M', 'C', 'S') levels
- [ ] **Magnetic Field**: Includes required ('b', 'x/y/z', '') columns
- [ ] **Constructor**: Uses `Plasma(data, *species)` format
- [ ] **Method Calls**: All methods exist and use correct signatures
- [ ] **Variables**: All variables defined before use
- [ ] **Output**: Produces verifiable, meaningful results
- [ ] **Physics**: Follows established physics conventions (units, NaN handling)

## Template Usage Guidelines

1. **Copy and Adapt**: Start with appropriate template and modify for specific use case
2. **Validate Early**: Test examples immediately after creation
3. **Keep Simple**: Avoid complex calculations that might fail
4. **Document Assumptions**: Note what data/objects must exist
5. **Verify Imports**: Double-check all import paths work correctly

These templates ensure consistent, working examples throughout SolarWindPy documentation while following established API patterns and physics conventions.