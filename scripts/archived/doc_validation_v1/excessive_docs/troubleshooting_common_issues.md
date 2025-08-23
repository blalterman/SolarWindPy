# Troubleshooting Common Documentation Issues

## Overview
This guide provides solutions to the most frequently encountered issues when writing and validating documentation examples in SolarWindPy. Use this as a quick reference for resolving common problems.

## Import and Module Issues

### Issue: ModuleNotFoundError
```python
# ❌ Problem
from solarwindpy.plotting import time_series
# ModuleNotFoundError: No module named 'solarwindpy.plotting'

# ✅ Solution: Check correct import paths
import solarwindpy as swp
# Use swp.plotting if available, or check actual module structure

# ✅ Alternative: Use available imports
import solarwindpy.plotting as swpp  # If this module exists
```

**Debugging Steps:**
```bash
# Check what's actually available
python -c "import solarwindpy; print(dir(solarwindpy))"
python -c "import solarwindpy; print(solarwindpy.__file__)"

# Check module structure
find solarwindpy/ -name "*.py" | head -10
```

### Issue: ImportError for Dependencies
```python
# ❌ Problem
import matplotlib.pyplot as plt
# ImportError: No module named 'matplotlib'

# ✅ Solution: Use conda environment
conda activate solarwindpy-20250403
# or
pip install matplotlib numpy pandas
```

**Environment Check:**
```bash
# Verify environment setup
conda info --envs
conda activate solarwindpy-20250403
python -c "import numpy, pandas, matplotlib; print('All dependencies OK')"
```

### Issue: Relative Import Errors
```python
# ❌ Problem
from .core import Plasma
# attempted relative import with no known parent package

# ✅ Solution: Use absolute imports in examples
import solarwindpy as swp
plasma = swp.Plasma(data)

# ✅ Alternative: For doctest modules
from solarwindpy.core.plasma import Plasma
```

## Variable Definition Issues

### Issue: NameError - Undefined Variables
```python
# ❌ Problem
plasma = swp.Plasma(data)
# NameError: name 'data' is not defined

# ✅ Solution: Define variables explicitly
import pandas as pd
epoch = pd.date_range('2023-01-01', periods=10, freq='1min', name='Epoch')
data = swp.create_example_plasma_data(epoch)
plasma = swp.Plasma(data)

# ✅ Alternative: Use fixture functions
from doctest_fixtures import create_example_plasma_data
data = create_example_plasma_data()
plasma = swp.Plasma(data)
```

### Issue: Undefined Constants
```python
# ❌ Problem
thermal_speed = np.sqrt(2 * k_B * temperature / m_p)
# NameError: name 'k_B' is not defined

# ✅ Solution: Define constants explicitly
k_B = 1.380649e-23  # Boltzmann constant [J/K]
m_p = 1.67262192e-27  # Proton mass [kg]
thermal_speed = np.sqrt(2 * k_B * temperature / m_p) / 1000  # km/s

# ✅ Alternative: Import from constants module
try:
    from solarwindpy.core.units_constants import Constants
    const = Constants()
    k_B = const.kb
    m_p = const.m['p1']
except ImportError:
    k_B = 1.380649e-23
    m_p = 1.67262192e-27
```

## Physics Rule Violations

### Issue: Thermal Speed Convention Violation
```python
# ❌ Problem: Incorrect thermal speed calculation
thermal_speed = np.sqrt(temperature / mass)  # Wrong convention
thermal_speed = 45.0  # Hardcoded value

# ✅ Solution: Use mw² = 2kT convention
k_B = 1.380649e-23  # J/K
m_p = 1.67262192e-27  # kg
T = 1e5  # K
thermal_speed = np.sqrt(2 * k_B * T / m_p) / 1000  # km/s

# ✅ Alternative: Use class methods
thermal_speed = plasma.p1.thermal_speed()  # Uses correct convention
```

**Physics Validation Check:**
```bash
# Check thermal speed calculations specifically
python doctest_physics_validator.py your_file.py --rule thermal_speed
```

### Issue: Unit Inconsistency
```python
# ❌ Problem: Mixed units in calculations
B = 5.0  # nT
n = 10.0  # cm^-3
alfven_speed = B / np.sqrt(n)  # Wrong! Mixed units

# ✅ Solution: Convert to SI for calculations
B_nT = 5.0  # nT
n_cm3 = 10.0  # cm^-3

# Convert to SI
B_si = B_nT * 1e-9  # T
n_si = n_cm3 * 1e6  # m^-3
mu_0 = 4 * np.pi * 1e-7  # H/m
m_p = 1.67262192e-27  # kg

# Calculate in SI
rho_si = n_si * m_p  # kg/m^3
alfven_speed_si = B_si / np.sqrt(mu_0 * rho_si)  # m/s
alfven_speed = alfven_speed_si / 1000  # km/s for display
```

### Issue: Missing Data Handling
```python
# ❌ Problem: Using fill values for missing data
data[data < 0] = -999  # Don't use fill values
data = data.fillna(0)  # Don't fill with zeros

# ✅ Solution: Use NaN for missing data
import numpy as np
data_clean = data.dropna()  # Remove missing values
valid_mask = ~np.isnan(data)  # Identify valid data
data_valid = data[valid_mask]  # Select valid data only
```

## MultiIndex DataFrame Issues

### Issue: Incorrect Column Structure
```python
# ❌ Problem: Wrong level naming
columns = pd.MultiIndex.from_tuples([
    ('density', '', 'proton'),
    ('velocity', 'X', 'proton')
], names=['Measurement', 'Component', 'Species'])

# ✅ Solution: Use standard (M, C, S) naming
columns = pd.MultiIndex.from_tuples([
    ('n', '', 'p1'),      # density → n, proton → p1
    ('v', 'x', 'p1')      # velocity → v, X → x
], names=['M', 'C', 'S'])  # Standard level names
```

### Issue: Inefficient MultiIndex Access
```python
# ❌ Problem: Using .loc[] for MultiIndex
proton_density = data.loc[:, ('n', '', 'p1')]  # Less efficient
velocity_x = data[('v', 'x', 'p1')]  # Direct indexing is fragile

# ✅ Solution: Use .xs() for efficient access
proton_density = data.xs(('n', '', 'p1'), axis=1)
velocity_x = data.xs(('v', 'x', 'p1'), axis=1)

# ✅ Alternative: Level-specific access
proton_density = data.xs('n', level='M').xs('p1', level='S')
velocity_data = data.xs('v', level='M').xs('p1', level='S')
```

### Issue: Missing Index Names
```python
# ❌ Problem: Generic or missing index names
epoch = pd.date_range('2023-01-01', periods=10)  # No name
data = pd.DataFrame(values, index=epoch)

# ✅ Solution: Use 'Epoch' for time series
epoch = pd.date_range('2023-01-01', periods=10, freq='1min', name='Epoch')
data = pd.DataFrame(values, index=epoch)

# Verify index name
assert data.index.name == 'Epoch', "Time series index must be named 'Epoch'"
```

## Execution and Runtime Issues

### Issue: Fixture Function Not Found
```python
# ❌ Problem
data = create_example_plasma_data()
# NameError: name 'create_example_plasma_data' is not defined

# ✅ Solution: Import fixture or define data explicitly
# Option 1: Import fixture
from doctest_fixtures import create_example_plasma_data
data = create_example_plasma_data()

# Option 2: Create data explicitly  
import pandas as pd
epoch = pd.date_range('2023-01-01', periods=10, freq='1min', name='Epoch')
# Define data structure manually or use available methods
```

### Issue: Random Results in Examples
```python
# ❌ Problem: Non-reproducible random data
data = np.random.normal(100, 10, 10)  # Different results each run

# ✅ Solution: Set random seed for reproducible results
np.random.seed(42)  # Ensures consistent results
data = np.random.normal(100, 10, 10)

# Verify reproducibility
expected_first_value = 149.7  # From seed 42
assert abs(data[0] - expected_first_value) < 0.1, "Random seed not working"
```

### Issue: Large Dataset Performance
```python
# ❌ Problem: Creating large datasets in examples
data = create_example_plasma_data(n_points=10000)  # Too large for doctest

# ✅ Solution: Use small datasets for examples
data = create_example_plasma_data(n_points=5)  # Small and fast
# or
epoch = pd.date_range('2023-01-01', periods=3, freq='1min', name='Epoch')
data = create_example_plasma_data(epoch)  # Explicit small size
```

## Doctest-Specific Issues

### Issue: Output Format Mismatches
```python
# ❌ Problem: Exact output matching required
>>> plasma.p1.n.mean()
5.234567890123456

# ✅ Solution: Use ellipsis or round for consistent output
>>> plasma.p1.n.mean()  # doctest: +ELLIPSIS
5.234...

# ✅ Alternative: Round to reasonable precision
>>> round(plasma.p1.n.mean(), 2)
5.23

# ✅ Alternative: Use boolean checks
>>> plasma.p1.n.mean() > 0
True
```

### Issue: Platform-Specific Output
```python
# ❌ Problem: Different output on different platforms
>>> data.dtypes
# Windows vs Linux differences

# ✅ Solution: Test behavior, not exact output
>>> len(data.dtypes)
8
>>> all(isinstance(dtype, np.dtype) for dtype in data.dtypes)
True
```

### Issue: Exception Testing
```python
# ❌ Problem: Exact exception message matching
>>> plasma = swp.Plasma(invalid_data)
Traceback (most recent call last):
    ...
ValueError: Invalid data format for plasma initialization

# ✅ Solution: Test exception type, not exact message
>>> plasma = swp.Plasma(invalid_data)  # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
ValueError: ...
```

## Validation Framework Issues

### Issue: Validation Script Fails
```bash
# ❌ Problem
python doctest_physics_validator.py solarwindpy/
# ImportError: No module named 'doctest_physics_validator'

# ✅ Solution: Check working directory and environment
pwd  # Should be in SolarWindPy root directory
conda activate solarwindpy-20250403
ls doctest_physics_validator.py  # Should exist

# ✅ Alternative: Use full path
python /full/path/to/doctest_physics_validator.py solarwindpy/
```

### Issue: Slow Validation Performance
```bash
# ❌ Problem: Validation takes too long
python doctest_physics_validator.py solarwindpy/  # >5 minutes

# ✅ Solution: Use quick check during development
python doctest_physics_validator.py solarwindpy/ --quick-check

# ✅ Alternative: Validate specific files only
python doctest_physics_validator.py solarwindpy/core/plasma.py

# ✅ Alternative: Use parallel processing
python doctest_physics_validator.py solarwindpy/ --parallel
```

### Issue: False Positive Physics Violations
```bash
# ❌ Problem: Incorrect physics violation reported
# Physics validator flags correct thermal speed calculation

# ✅ Solution: Check calculation manually
python -c "
import numpy as np
k_B = 1.380649e-23
m_p = 1.67262192e-27  
T = 1e5
expected = np.sqrt(2 * k_B * T / m_p) / 1000
print(f'Expected thermal speed: {expected:.2f} km/s')
"

# ✅ Alternative: Adjust validation tolerance
python doctest_physics_validator.py --tolerance 0.05 file.py

# ✅ Report false positive
# Create GitHub issue with specific example
```

## Best Practices for Avoiding Issues

### Preventive Measures

#### 1. Always Test Locally
```bash
# Before committing
python -m doctest your_module.py -v
python doctest_physics_validator.py your_module.py --quick-check
```

#### 2. Use Standard Patterns
```python
# Standard example template
import solarwindpy as swp
import numpy as np
import pandas as pd

# Set random seed for reproducibility
np.random.seed(42)

# Use standard epoch naming
epoch = pd.date_range('2023-01-01', periods=5, freq='1min', name='Epoch')

# Use fixture functions
data = swp.create_example_plasma_data(epoch)
plasma = swp.Plasma(data)

# Test with realistic checks
assert len(plasma.p1.n) == 5
assert (plasma.p1.n > 0).all()
```

#### 3. Include Physics Validation
```python
# Always verify physics makes sense
thermal_speed = plasma.p1.thermal_speed()
assert thermal_speed.min() > 0, "Thermal speed must be positive"
assert thermal_speed.max() < 1000, "Thermal speed seems unreasonably high"
```

#### 4. Document Units Clearly
```python
# Always specify units in comments
B_nT = 5.0  # Magnetic field [nT]
n_cm3 = 10.0  # Number density [cm^-3]
v_kms = 400.0  # Velocity [km/s]
T_K = 1e5  # Temperature [K]
```

### Quick Diagnostic Commands

#### Environment Check
```bash
# Verify setup
conda info --envs
which python
python -c "import solarwindpy; print(solarwindpy.__version__)"
```

#### Module Structure Check
```bash
# See what's available
python -c "
import solarwindpy as swp
print('SolarWindPy modules:')
for attr in dir(swp):
    if not attr.startswith('_'):
        print(f'  swp.{attr}')
"
```

#### Physics Constants Check
```bash
# Verify constants
python -c "
try:
    from solarwindpy.core.units_constants import Constants
    const = Constants()
    print(f'k_B: {const.kb}')
    print(f'm_p: {const.m[\"p1\"]}')
except ImportError:
    print('Using fallback constants')
    print('k_B: 1.380649e-23')
    print('m_p: 1.67262192e-27')
"
```

#### Validation Framework Check
```bash
# Test validation framework
python doctest_physics_validator.py --help
python doctest_physics_validator.py --version
ls -la doctest_*.py  # Check all validator files exist
```

## Getting Additional Help

### Resources
1. **GitHub Issues**: Report bugs in validation framework
2. **Discussion Forums**: Ask questions about physics conventions
3. **Code Review**: Request review for complex examples
4. **Documentation**: Check `doctest_guidelines.md` for detailed patterns

### Support Workflow
1. **Check this troubleshooting guide** for common issues
2. **Test locally** with validation framework
3. **Create minimal example** that demonstrates the issue
4. **Report issue** with complete error messages and context
5. **Follow up** on resolution and update documentation

### Contributing Improvements
If you solve a problem not covered here:
1. Document the solution
2. Add it to this troubleshooting guide
3. Submit a pull request with the update
4. Help other contributors avoid the same issue

---

This troubleshooting guide covers the most common issues encountered when working with SolarWindPy documentation examples. Keep this reference handy during development to quickly resolve problems and maintain productivity.