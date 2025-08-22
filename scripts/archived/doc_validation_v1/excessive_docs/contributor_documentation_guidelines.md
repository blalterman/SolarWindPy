# Documentation Example Guidelines for SolarWindPy Contributors

## Overview
This guide ensures all code examples in SolarWindPy documentation are executable, scientifically accurate, and follow established conventions. Following these standards prevents common issues and maintains consistency across the project.

## Example Writing Standards

### 1. Code Structure Requirements

#### Import Statements
```python
# ✅ REQUIRED: Use standardized import alias
import solarwindpy as swp
import numpy as np
import pandas as pd

# ❌ AVOID: Inconsistent aliases
import solarwindpy as sw  # Don't use this
import solarwindpy  # Use the alias instead
```

#### Data Setup
```python
# ✅ REQUIRED: Use fixture functions for complex data
epoch = pd.date_range('2023-01-01', periods=10, freq='1min', name='Epoch')
data = swp.create_example_plasma_data(epoch)
plasma = swp.Plasma(data)

# ❌ AVOID: Undefined variables
plasma = swp.Plasma(data)  # Where does 'data' come from?
```

### 2. Physics Compliance Rules

#### Thermal Speed Convention
```python
# ✅ REQUIRED: Follow mw² = 2kT convention
thermal_speed = plasma.p1.thermal_speed()  # Uses correct convention

# ❌ AVOID: Incorrect thermal speed calculations
thermal_speed = np.sqrt(temperature / mass)  # Wrong convention
thermal_speed = 50.0  # Hardcoded values

# Physics validation will automatically check this
```

#### Units Consistency
```python
# ✅ REQUIRED: Use SI internally, display units for user interface
# Internal calculations use SI (m/s, kg, etc.)
# Display uses conventional units (km/s, cm^-3, nT)
velocity_si = plasma.p1.v_si  # m/s for calculations
velocity_display = plasma.p1.v  # km/s for display

# ❌ AVOID: Mixed unit systems
velocity = 400 * 1000  # m/s - convert in calculations, not display
```

#### Missing Data Handling
```python
# ✅ REQUIRED: Use NaN for missing data
data_with_gaps = data.dropna()  # Proper missing data handling
valid_indices = ~np.isnan(data)

# ❌ AVOID: Using 0 or -999 for missing values
data[data == -999] = 0  # Don't do this
data.fillna(0)  # Don't fill with zeros
```

### 3. MultiIndex Structure Requirements

#### Column Structure
```python
# ✅ REQUIRED: Use (M, C, S) level naming
columns = pd.MultiIndex.from_tuples([
    ('n', '', 'p1'),    # Measurement, Component, Species
    ('v', 'x', 'p1'),   # Vector components: x, y, z
    ('v', 'y', 'p1'),
    ('v', 'z', 'p1'),
], names=['M', 'C', 'S'])  # Required level names

# ❌ AVOID: Inconsistent level naming
columns = pd.MultiIndex.from_tuples([
    ('density', '', 'proton'),  # Use standard abbreviations
    ('velocity', 'X', 'proton')  # Use lowercase for components
], names=['Measurement', 'Component', 'Species'])  # Use M, C, S
```

#### Data Access Patterns
```python
# ✅ REQUIRED: Use .xs() for MultiIndex access
proton_density = plasma.data.xs('n', level='M').xs('p1', level='S')
velocity_x = plasma.data.xs('v', level='M').xs('x', level='C').xs('p1', level='S')

# Alternative: Single operation
proton_density = plasma.data.xs(('n', '', 'p1'), axis=1)
velocity_x = plasma.data.xs(('v', 'x', 'p1'), axis=1)

# ❌ AVOID: Direct indexing or .loc[] for MultiIndex
proton_density = plasma.data[('n', '', 'p1')]  # Fragile
velocity_x = plasma.data.loc[:, ('v', 'x', 'p1')]  # Less efficient
```

#### Index Naming
```python
# ✅ REQUIRED: Time series indices must be named 'Epoch'
epoch = pd.date_range('2023-01-01', periods=10, freq='1min', name='Epoch')
data = pd.DataFrame(values, index=epoch)

# ❌ AVOID: Generic or missing index names
epoch = pd.date_range('2023-01-01', periods=10, freq='1min')  # No name
epoch = pd.date_range('2023-01-01', periods=10, freq='1min', name='Time')  # Wrong name
```

### 4. Example Testing

#### Local Validation
```bash
# Test your examples before submitting
python -m doctest your_module.py -v
python doctest_physics_validator.py --file solarwindpy/your_module.py

# For documentation files
python validate_examples.py --file docs/your_file.rst
```

#### Physics Validation
```python
# Examples automatically checked for:
# - Thermal speed convention compliance (mw² = 2kT)
# - SI unit consistency
# - Proper missing data handling (NaN usage)
# - MultiIndex structure compliance ((M, C, S) naming)
# - Positive physical quantities (density, temperature)
# - Realistic value ranges for solar wind parameters
```

### 5. Documentation Patterns

#### RST Code Blocks
```rst
.. code-block:: python
   
   # Always include necessary imports at the top
   import solarwindpy as swp
   import numpy as np
   import pandas as pd
   
   # Use fixture functions for complex setup
   epoch = pd.date_range('2023-01-01', periods=10, freq='1min', name='Epoch')
   data = swp.create_example_plasma_data(epoch)
   plasma = swp.Plasma(data)
   
   # Show realistic usage patterns
   proton_density = plasma.p1.n
   print(f"Average density: {proton_density.mean():.1f} cm^-3")
   
   # Include physics validation
   assert proton_density.min() > 0, "Density must be positive"
```

#### Docstring Examples
```python
def thermal_speed(self):
    """Calculate thermal speed using mw² = 2kT convention.
    
    Returns
    -------
    pd.Series
        Thermal speed in km/s
    
    Examples
    --------
    >>> import solarwindpy as swp
    >>> epoch = pd.date_range('2023-01-01', periods=5, freq='1min', name='Epoch')
    >>> data = swp.create_example_plasma_data(epoch)
    >>> plasma = swp.Plasma(data)
    >>> thermal_speed = plasma.p1.thermal_speed()
    >>> thermal_speed.iloc[0] > 0  # Physics check
    True
    >>> len(thermal_speed)  # Shape check
    5
    """
```

## Validation Workflow

### Automated Checks
The validation framework automatically verifies:

1. **Syntax Validation**: All code blocks must be valid Python
2. **Import Resolution**: All imports must resolve correctly
3. **Execution Testing**: Examples must run without errors
4. **Physics Validation**: Outputs must follow physics rules
5. **Structure Compliance**: MultiIndex patterns must be correct

### Manual Review
Contributors should also verify:

1. **Scientific Accuracy**: Physics content should be domain-expert reviewed
2. **User Experience**: Examples should be clear and educational
3. **Consistency**: Patterns should match existing documentation
4. **Completeness**: Examples should be self-contained

## Common Issues and Solutions

### Issue: Import Errors
```python
# ❌ Problem: Module not found
from solarwindpy.plotting import time_series  # Doesn't exist

# ✅ Solution: Use correct import
import solarwindpy.plotting as swpp
fig = swpp.plot_time_series(data)

# ✅ Alternative: Check available modules
import solarwindpy as swp
# Use swp.plotting.plot_time_series() if available
```

### Issue: Undefined Variables
```python
# ❌ Problem: Variable used without definition
plasma = swp.Plasma(data)  # What is 'data'?

# ✅ Solution: Use fixture or define explicitly
epoch = pd.date_range('2023-01-01', periods=10, freq='1min', name='Epoch')
data = swp.create_example_plasma_data(epoch)
plasma = swp.Plasma(data)

# ✅ Alternative: Import fixture functions
from doctest_fixtures import create_example_plasma_data
data = create_example_plasma_data()
plasma = swp.Plasma(data)
```

### Issue: Physics Violations
```python
# ❌ Problem: Incorrect thermal speed calculation
thermal_speed = np.sqrt(temperature / mass)  # Wrong convention
thermal_speed = 45.0  # Hardcoded value

# ✅ Solution: Use established methods or correct formula
thermal_speed = plasma.p1.thermal_speed()  # Uses mw² = 2kT

# ✅ Alternative: Correct manual calculation
k_B = 1.380649e-23  # Boltzmann constant [J/K]
m_p = 1.67262192e-27  # Proton mass [kg]
T_p = 1e5  # Temperature [K]
thermal_speed = np.sqrt(2 * k_B * T_p / m_p) / 1000  # [km/s]
```

### Issue: MultiIndex Access Errors
```python
# ❌ Problem: Inefficient or incorrect MultiIndex access
density = data[('n', '', 'p1')]  # Direct indexing
velocity = data.loc[:, ('v', 'x', 'p1')]  # .loc[] usage

# ✅ Solution: Use .xs() for efficient access
density = data.xs(('n', '', 'p1'), axis=1)
velocity = data.xs(('v', 'x', 'p1'), axis=1)

# ✅ Alternative: Level-specific access
density = data.xs('n', level='M').xs('p1', level='S')
velocity_x = data.xs('v', level='M').xs('x', level='C').xs('p1', level='S')
```

### Issue: Unit Inconsistencies
```python
# ❌ Problem: Mixed unit systems in calculations
B_nT = 5.0  # nT
n_cm3 = 10.0  # cm^-3
# Direct calculation with mixed units
alfven_speed = B_nT / np.sqrt(n_cm3)  # Wrong!

# ✅ Solution: Convert to SI for calculations
B_si = B_nT * 1e-9  # Convert nT to T
n_si = n_cm3 * 1e6  # Convert cm^-3 to m^-3
mu_0 = 4 * np.pi * 1e-7  # H/m
m_p = 1.67262192e-27  # kg
rho_si = n_si * m_p  # kg/m^3
alfven_speed_si = B_si / np.sqrt(mu_0 * rho_si)  # m/s
alfven_speed = alfven_speed_si / 1000  # Convert to km/s for display
```

## Best Practices Summary

### Do's ✅

1. **Use fixtures**: Always use `create_example_plasma_data()` and related functions
2. **Set random seeds**: Use `np.random.seed(42)` for reproducible results
3. **Check physical ranges**: Verify results are in realistic ranges
4. **Include units**: Always specify units in comments and documentation
5. **Test positive quantities**: Ensure densities, temperatures > 0
6. **Use .xs() for MultiIndex**: More efficient than .loc for MultiIndex access
7. **Specify levels**: Always use `level=` parameter in .xs() calls
8. **Name time indices**: Use `'Epoch'` for time series index names
9. **Import consistently**: Use `swp` alias for solarwindpy
10. **Validate locally**: Test examples before submitting

### Don'ts ❌

1. **Don't hardcode physics values**: Calculate from first principles
2. **Don't use fill values**: Use `np.nan` for missing data
3. **Don't mix units**: Keep SI internally, convert only for display
4. **Don't create large datasets**: Use small examples (≤10 points) in doctests
5. **Don't ignore physics**: All examples should be scientifically realistic
6. **Don't use .loc for MultiIndex**: Use .xs() for better performance
7. **Don't omit level specification**: Be explicit about which level you're accessing
8. **Don't assume imports**: Include all necessary imports in examples
9. **Don't use deprecated APIs**: Update to current API patterns
10. **Don't skip validation**: Always run local tests before submitting

## Template for New Examples

```python
def example_function(parameter):
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
    >>> import solarwindpy as swp
    >>> import numpy as np
    >>> import pandas as pd
    >>> epoch = pd.date_range('2023-01-01', periods=3, freq='1min', name='Epoch')
    >>> data = swp.create_example_plasma_data(epoch)
    >>> plasma = swp.Plasma(data)
    >>> result = example_function(plasma.p1.n)
    >>> len(result)
    3
    
    >>> # Test physics compliance
    >>> # Include checks that verify physical correctness
    >>> (result > 0).all()  # For positive quantities
    True
    
    >>> # Test edge cases
    >>> # Show behavior with minimal or boundary inputs
    >>> minimal_data = swp.create_example_plasma_data(
    ...     pd.date_range('2023-01-01', periods=1, freq='1min', name='Epoch')
    ... )
    >>> edge_result = example_function(minimal_data.xs(('n', '', 'p1'), axis=1))
    >>> isinstance(edge_result, pd.Series)
    True
    """
    # Implementation here
    pass
```

## Getting Help

### Resources
- **Validation Tools**: Use `doctest_physics_validator.py` for comprehensive checking
- **Fixtures**: Import from `doctest_fixtures.py` for standard data patterns
- **Guidelines**: This document and `doctest_guidelines.md` for detailed patterns
- **CI/CD**: GitHub Actions provide automated validation feedback

### Support
- **Issues**: Create GitHub issues for validation framework problems
- **Questions**: Use project discussion forums for documentation questions
- **Contributions**: Follow PR process for guideline improvements

### Continuous Learning
- **Review Examples**: Study existing compliant examples in the codebase
- **Physics Documentation**: Consult domain-specific physics documentation
- **Framework Updates**: Stay informed about validation framework enhancements

---

Following these guidelines ensures that your documentation contributions maintain SolarWindPy's high standards for scientific accuracy, usability, and maintainability. The automated validation framework will help catch common issues, but understanding these principles will help you write better examples from the start.