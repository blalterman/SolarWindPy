# SolarWindPy Testing Templates

**Scope:** Test patterns for physics calculations and data structures
**See also:** calculation-patterns.md for what to test, dataframe-patterns.md for test data, physics-constants.md for validation

## Test Organization

### Directory Structure

```
tests/
├── conftest.py          # Shared fixtures
├── data/                # Centralized test data (CSV with MultiIndex columns)
│   ├── plasma.csv       # Standard plasma data (M|C|S pipe-delimited format)
│   ├── epoch.csv        # Timestamp index
│   └── spacecraft.csv   # Spacecraft data
├── core/                # Ion/Plasma physics tests
├── fitfunctions/        # Curve fitting and optimization tests
├── plotting/            # Visualization tests
└── solar_activity/      # Solar activity data and plotting tests
```

**Convention:** `tests/` mirrors `solarwindpy/` module structure.

**Discovery:** For current structure with subdirectories, use:
```bash
find tests -type d -maxdepth 2 ! -name "__pycache__" | sort
```

### File Naming

- **Test files:** `test_<module>.py`
- **Test classes:** `Test<ClassName>` or `<Class>TestBase`
- **Test methods:** `test_<what_is_tested>`

### Imports Pattern

```python
#!/usr/bin/env python
"""Tests for <module/class>."""
import numpy as np
import pandas as pd
import pandas.testing as pdt
from scipy.constants import physical_constants

from solarwindpy import ions  # External imports (not relative)
from solarwindpy import plasma
```

**Note:** Use external imports (`import solarwindpy`), not relative imports.

## Fixture Patterns

SolarWindPy uses **two fixture patterns** depending on test type:

### Pattern 1: Classmethod Fixtures (Core Tests)

Used in tests/core/ for Ion and Plasma tests:

```python
from abc import ABC, abstractproperty

class IonTestBase(ABC):
    @classmethod
    def set_object_testing(cls):
        """Create test object as class attribute."""
        data = cls.data.xs(cls().species, axis=1, level="S")
        ion = ions.Ion(data, cls().species)
        cls.object_testing = ion

    @abstractproperty
    def species(self):
        pass

    def test_temperature(self):
        # Access via cls.object_testing
        T = self.object_testing.temperature
        assert (T > 0).all().all()
```

### Pattern 2: Pytest Fixtures (Fitfunctions Tests)

Used in tests/fitfunctions/ for curve fitting tests:

```python
import pytest

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    x = np.linspace(0, 10, 100)
    y = 2 * x + 1 + np.random.normal(0, 0.1, 100)
    return pd.DataFrame({'x': x, 'y': y})

def test_line_fit(sample_data):
    # Fixture injected via parameter
    result = fit_line(sample_data)
    assert result.slope > 0
```

**When to use which:**
- **Classmethod:** Physics objects (Ion, Plasma) requiring complex setup
- **Pytest fixtures:** Reusable test data, simpler objects, parametrized inputs

### Pattern 3: Test Data Base Classes (Core Tests)

Core tests inherit from `test_base.SWEData` which loads standard test data from `tests/data/`:

```python
from . import test_base as base

# Inherit from SWEData to get cls.data automatically loaded
class TestIonP1(base.P1Test, IonTestBase, base.SWEData):
    pass
```

**Provides:**
- `cls.data` - Standard plasma DataFrame from tests/data/plasma.csv
- `cls.set_object_testing()` - Abstract method to create test objects
- Species mixins: `base.P1Test`, `base.AlphaTest`, etc. (provide `.species` property)

**When to use:** All Ion/Plasma physics tests (tests/core/)

## Physics Validation Patterns

### Constraint Checking Template

```python
def test_density_positive(self):
    """Density must be positive."""
    ion = ions.Ion(self.data, species='p')
    n = ion.n
    assert (n > 0).all(), "Density must be positive"

def test_temperature_positive(self):
    """Temperature must be positive."""
    ion = ions.Ion(self.data, species='p')
    T = ion.temperature
    assert (T > 0).all().all(), "Temperature must be positive"
```

**Key constraints to test:**
- Density: `n > 0`
- Temperature: `T > 0`
- Thermal speed: `w > 0`
- Thermal pressure: `pth > 0`

### Units Consistency Validation

```python
def test_temperature_units(self):
    """Temperature calculation uses correct units."""
    # Expected: T = 0.5 * m * w^2 / k_B (in SI)
    m = physical_constants["proton mass"][0]
    k_B = physical_constants["Boltzmann constant"][0]

    w = self.data.w * 1e3  # km/s → m/s
    T_expected = (0.5 * m / k_B) * w.pow(2) / 1e5  # → 10^5 K

    pdt.assert_frame_equal(T_expected, self.object_testing.temperature)
```

**Pattern:** Calculate expected value with explicit unit conversions, compare to result.

**Universal application:** This pattern works for ALL physics calculations:
- B-field independent: temperature, density, thermal_pressure
- B-field dependent: beta, alfven_speed, gyrofrequency
- Multi-species: mass-weighted velocity, total pressure

The template is always: (1) calculate expected from physics formula with explicit SI conversions, (2) compare to actual property/method result using `pdt.assert_frame_equal()`, (3) verify physical constraints.

### NaN Handling Tests

```python
def test_nan_propagation(self):
    """NaN values propagate through calculations."""
    data = self.data.copy()
    data.iloc[5, data.columns.get_loc(('T', 'par', 'p'))] = np.nan

    ion = ions.Ion(data, species='p')
    result = ion.thermal_pressure

    # Check NaN propagated
    assert result.iloc[5].isna().any(), "NaN should propagate"

def test_nan_preserved(self):
    """Calculations preserve NaN, don't raise errors."""
    data = self.data.copy()
    data.loc[:, ('n', '', 'p')] = np.nan

    # Should not raise - NaN is valid
    ion = ions.Ion(data, species='p')
    pth = ion.thermal_pressure  # Should contain NaN, not error
    assert pth.isna().all().all()
```

**Philosophy:** NaN represents missing/invalid data, not errors. Calculations should propagate NaN.

## Parametrization Patterns

### Species Combinations

```python
import itertools
from itertools import combinations, chain

@property
def species_combinations(self):
    """Generate all species combinations for testing."""
    stuple = ('p', 'a', 'e')
    ncombinations = range(1, len(stuple) + 1)
    return chain(*[combinations(stuple, n) for n in ncombinations])

def test_temperature_all_species(self):
    """Test temperature method for all species combinations."""
    for combo in self.species_combinations:
        temp = self.object_testing.temperature(*combo)
        assert isinstance(temp, (pd.DataFrame, pd.Series))
        assert not temp.empty
```

### Component Combinations

```python
import pytest

@pytest.mark.parametrize("component", ["par", "per", "scalar"])
def test_temperature_components(self, component):
    """Test temperature has all expected components."""
    ion = ions.Ion(self.data, species='p')
    T = ion.temperature
    assert component in T.columns, f"Missing component: {component}"

@pytest.mark.parametrize("component", ["x", "y", "z"])
def test_velocity_components(self, component):
    """Test velocity has Cartesian components."""
    ion = ions.Ion(self.data, species='p')
    v = ion.velocity
    # May have x/y/z or R/T/N depending on data
    # Check structure matches dataframe-patterns.md conventions
```

**Usage:** Parametrize is common in fitfunctions tests (29+ instances), less common in core physics tests which use species_combinations property.

### Edge Cases

```python
@pytest.mark.parametrize("edge_case,expected_error", [
    ("", ValueError),  # Empty species
    ("invalid", ValueError),  # Invalid species
    ("p,a", ValueError),  # Comma syntax forbidden
])
def test_species_edge_cases(self, edge_case, expected_error):
    """Test species parameter edge cases."""
    plasma_obj = plasma.Plasma(self.data, 'p', 'a')
    with pytest.raises(expected_error):
        plasma_obj.temperature(edge_case)
```

## Test Data Patterns

### Loading from Centralized Test Data (Core Tests - PREFERRED)

Physics tests load standard test data from `tests/data/` CSV files:

```python
from pathlib import Path
from unittest import TestCase
import pandas as pd
import numpy as np

DATA_PATH = Path(__file__).parent.parent / "data"

class TestData:
    """Load standard test data from tests/data/ directory."""

    @property
    def plasma_data(self):
        """Load plasma.csv with MultiIndex columns."""
        path = DATA_PATH / "plasma.csv"
        test_plasma = pd.read_csv(path)

        # Parse MultiIndex from "M|C|S" column naming
        test_plasma.columns = pd.MultiIndex.from_tuples(
            [tuple(c.split("|")) for c in test_plasma.columns]
        )
        test_plasma.columns.names = ["M", "C", "S"]
        test_plasma.index = self.epoch  # DatetimeIndex
        return test_plasma

class SWEData(TestCase):
    """Base class providing standard plasma test data."""

    @classmethod
    def setUpClass(cls):
        data = TestData()
        cls.data = data.plasma_data.sort_index(axis=1)
        cls.set_object_testing()  # Subclass implements this

# Usage in test classes
class TestIonP1(base.P1Test, IonTestBase, base.SWEData):
    pass  # cls.data loaded automatically from plasma.csv
```

**Test data files:**
- `tests/data/plasma.csv` - Standard plasma measurements (n, v, w, T for multiple species)
- `tests/data/epoch.csv` - Timestamp index
- `tests/data/spacecraft.csv` - Spacecraft data

**Column format:** CSV uses pipe-delimited MultiIndex: `M|C|S` (e.g., `n||p`, `v|x|p1`, `T|par|a`)

### Generating Simple Test Data (Non-Physics Tests)

Non-physics tests (e.g., plotting, data handling) may generate simple data:

```python
def test_plotting_function():
    """Simple generated data for visualization tests."""
    dates = pd.date_range('2020-01-01', periods=100, freq='1D')
    data = pd.DataFrame({
        "ssn": np.random.uniform(0, 200, 100),
        "std": np.random.uniform(5, 15, 100)
    }, index=dates)

    plot_sunspot_numbers(data)
```

**When to use:**
- ✅ Plotting tests (don't need realistic physics)
- ✅ Data transformation tests (structure matters, values don't)
- ❌ Physics calculations (use tests/data/ CSV files)

### Sample Data Guidelines

**Realistic solar wind values** (as provided in tests/data/plasma.csv):
- Density (n): 1-20 cm⁻³
- Velocity (v): 250-800 km/s
- Thermal speed (w): 10-100 km/s
- Temperature (T): 0.5-50 × 10⁵ K
- Magnetic field (B): 1-20 nT

## Assertion Patterns

### DataFrame/Series Comparison

```python
import pandas.testing as pdt

def test_property_equality(self):
    """Test property returns expected DataFrame."""
    ion = ions.Ion(self.data, species='p')

    # For DataFrames
    pdt.assert_frame_equal(expected_df, ion.temperature)

    # For Series
    pdt.assert_series_equal(expected_series, ion.n)

    # With tolerance
    pdt.assert_frame_equal(expected, result, rtol=1e-5, atol=1e-8)
```

### Property Access Tests

```python
def test_property_aliases(self):
    """Test property aliases return same data."""
    ion = ions.Ion(self.data, species='p')

    # Multiple names for same property
    pdt.assert_series_equal(ion.n, ion.number_density)
    pdt.assert_frame_equal(ion.w, ion.thermal_speed)
    pdt.assert_frame_equal(ion.T, ion.temperature)
```

### Method Call Tests

```python
def test_plasma_method_species_param(self):
    """Test Plasma methods require species parameter."""
    plasma_obj = plasma.Plasma(self.data, 'p', 'a')

    # Single species
    temp_p = plasma_obj.temperature('p')
    assert isinstance(temp_p, pd.DataFrame)
    assert temp_p.columns.tolist() == ['par', 'per', 'scalar']

    # Sum species
    temp_sum = plasma_obj.temperature('p+a')
    assert isinstance(temp_sum, pd.DataFrame)

    # Multiple species
    temp_multi = plasma_obj.temperature('p', 'a')
    assert isinstance(temp_multi, pd.DataFrame)
    assert temp_multi.columns.nlevels == 2  # C and S levels
```

### Error Handling Tests

```python
def test_missing_data_raises_keyerror(self):
    """Test accessing missing data raises KeyError."""
    data = self.data.copy()
    data = data.drop(('T', 'par', 'p'), axis=1)

    ion = ions.Ion(data, species='p')
    with pytest.raises(KeyError):
        _ = ion.temperature

def test_invalid_species_raises_valueerror(self):
    """Test invalid species raises ValueError."""
    with pytest.raises(ValueError, match="not found"):
        ion = ions.Ion(self.data, species='invalid')
```

## Coverage Requirements

**Requirement:** ≥95% test coverage for all modules

**Note:** Coverage requirement documented in project standards but NOT enforced via config files (no coverage settings in pyproject.toml, tox.ini, or setup.cfg). Coverage enforced via CLI flags and pre-commit hooks.

### What to Test

✅ **Required:**
- All public APIs (methods, properties)
- Edge cases (empty data, NaN, boundary values)
- Error conditions (missing data, invalid parameters)
- Physics constraints (n > 0, T > 0, etc.)
- Units consistency
- Return types

❌ **Not required:**
- Private methods (unless complex logic)
- Trivial getters/setters
- `__repr__`, `__str__` (unless complex)

### Coverage Commands

```bash
# Run tests with coverage
pytest --cov=solarwindpy --cov-report=html

# Run tests quietly with coverage
pytest -q --cov=solarwindpy --cov-report=term

# Check specific module coverage
pytest --cov=solarwindpy.core.ions --cov-report=term

# Generate coverage report
pytest --cov=solarwindpy --cov-report=html
# Open htmlcov/index.html
```

### Coverage Reporting

```bash
# Via test-runner hook
.claude/hooks/test-runner.sh --coverage

# View coverage summary
pytest --cov=solarwindpy --cov-report=term --tb=short
```

**CI Pattern:** GitHub Actions runs `pytest --tb=short --disable-warnings tests/`

## Integration Test Patterns

### Multi-Step Workflow Tests

```python
def test_dataframe_to_ion_to_calculation(self):
    """Test complete workflow: DataFrame → Ion → calculation."""
    # Step 1: Load/create DataFrame
    data = self.sample_data

    # Step 2: Create Ion
    proton = ions.Ion(data, species='p')

    # Step 3: Access properties
    T = proton.temperature
    n = proton.density

    # Step 4: Verify results
    assert T.shape == (100, 3)  # 100 times, 3 components
    assert n.shape == (100,)
    assert (T > 0).all().all()
    assert (n > 0).all()
```

### Plasma Multi-Species Workflow

```python
def test_plasma_multi_species_workflow(self):
    """Test Plasma workflow with multiple species."""
    # Create Plasma with species list
    plasma_obj = plasma.Plasma(self.data, 'p', 'a')
    print(plasma_obj.species)  # ['p', 'a']

    # Individual species calculations
    p_temp = plasma_obj.temperature('p')
    a_temp = plasma_obj.temperature('a')

    # Aggregate calculation
    total_temp = plasma_obj.temperature('p+a')

    # Multi-species return
    both_temps = plasma_obj.temperature('p', 'a')

    # Verify structure (see dataframe-patterns.md)
    assert both_temps.columns.nlevels == 2  # C and S levels
    assert 'p' in both_temps.columns.get_level_values('S')
    assert 'a' in both_temps.columns.get_level_values('S')
```

## Best Practices

### Test Naming

```python
# Good - describes what is tested
def test_temperature_returns_dataframe_with_three_components(self):
    pass

# Good - describes expected behavior
def test_nan_propagates_through_thermal_pressure_calculation(self):
    pass

# Bad - too vague
def test_temperature(self):
    pass
```

### Assertion Messages

```python
# Good - informative failure message
assert (n > 0).all(), f"Density must be positive, got min={n.min()}"

# Good - context for debugging
pdt.assert_frame_equal(
    expected, result,
    "Temperature calculation mismatch for species 'p'"
)
```

### Test Isolation

```python
# Good - each test independent
def test_feature_a(self):
    data = self.sample_data.copy()  # Copy to avoid mutation
    ion = ions.Ion(data, species='p')
    # ...

# Bad - tests depend on order
def test_feature_a(self):
    self.shared_ion.calculate_something()  # Mutates state

def test_feature_b(self):
    # Depends on test_feature_a running first
    result = self.shared_ion.get_result()
```

### Fast Tests

✅ **Do:**
- Use small sample data (100-1000 points)
- Mock expensive operations
- Parametrize to avoid duplication

❌ **Don't:**
- Load large files (use fixtures with small data)
- Make network requests
- Perform I/O operations (unless testing I/O specifically)

### Deterministic Tests

```python
# Good - deterministic
np.random.seed(42)
data = np.random.uniform(5, 15, 100)

# Good - no randomness
data = np.linspace(5, 15, 100)

# Bad - flaky test
data = np.random.uniform(5, 15, 100)  # No seed
```

## Test Discovery

### Finding Existing Tests

```bash
# List all tests without running
pytest --collect-only

# List tests in specific module
pytest --collect-only tests/core/test_ions.py

# Find tests matching pattern
pytest --collect-only -k "temperature"
```

### Using Existing Tests as Templates

Explore `tests/` subdirectories (see "Directory Structure" section above) for live examples:
- **Physics validation patterns:** tests/core/ (Ion/Plasma calculate-expected-then-compare)
- **Parametrize & pytest fixtures:** tests/fitfunctions/
- **Module-specific patterns:** tests/plotting/, tests/data/, tests/solar_activity/

**Discovery command:**
```bash
pytest --collect-only tests/
```

## Common Patterns Summary

1. **Three fixture patterns** - Classmethod for core, pytest fixtures for fitfunctions, test_base inheritance for data loading
2. **Use pandas.testing** for DataFrame/Series assertions
3. **Test physics constraints** (n > 0, T > 0, etc.)
4. **Verify units consistency** with explicit conversions
5. **Test NaN propagation** - NaN is valid, not an error
6. **Load test data from tests/data/** for physics tests (core pattern)
7. **Parametrize** species and component combinations (common in fitfunctions)
8. **Species combinations property** for exhaustive testing (core tests)
9. **Test edge cases** - empty, invalid, boundary values
10. **Verify return types** - DataFrame vs Series structure
11. **Check MultiIndex structure** matches dataframe-patterns.md
12. **Use descriptive test names** and assertion messages
13. **Keep tests fast** - small data, no I/O
14. **Maintain ≥95% coverage** via CLI flags and hooks

## See Also

- **calculation-patterns.md** - What to test (Ion/Plasma APIs)
- **dataframe-patterns.md** - Test data structure (MultiIndex)
- **physics-constants.md** - Units, constraints, NaN philosophy
- **Existing tests:** tests/core/test_ions.py, test_plasma.py for core patterns; tests/fitfunctions/ for parametrize patterns
