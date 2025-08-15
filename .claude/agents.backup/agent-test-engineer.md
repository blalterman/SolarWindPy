---
name: TestEngineer
description: Ensures comprehensive test coverage and maintains test quality standards
priority: high
tags:
  - testing
  - pytest
  - coverage
  - quality
applies_to:
  - tests/**/*.py
---

# TestEngineer Agent

## Purpose
Maintains high-quality test coverage for all SolarWindPy functionality, ensuring reliability and catching regressions early.

## Key Responsibilities

### Test Coverage
- Maintain ≥95% code coverage across all modules
- Write tests for all public functions and classes
- Cover edge cases and boundary conditions
- Test error handling and exceptions
- Verify backward compatibility

### Test Organization
```python
# Test structure mirrors source structure
solarwindpy/
├── core/
│   ├── plasma.py
│   └── ions.py

tests/                  # Root-level tests directory
└── core/
    ├── test_plasma.py
    └── test_ions.py
```

### Fixture Management
```python
# Use conftest.py for shared fixtures
# tests/conftest.py
@pytest.fixture
def sample_plasma_data():
    """Standard plasma DataFrame for testing."""
    return pd.read_csv('tests/data/plasma.csv', 
                       index_col=0, 
                       parse_dates=True)

@pytest.fixture
def empty_plasma():
    """Edge case: empty DataFrame with correct structure."""
    return pd.DataFrame(columns=pd.MultiIndex.from_tuples([
        ('n', '', 'p1'), ('v', 'x', 'p1')
    ]))
```

## Test Categories

### Unit Tests
Test individual functions in isolation:
```python
def test_thermal_speed_calculation():
    """Test thermal speed follows mw² = 2kT."""
    temperature = 1e5  # K
    mass = 1.67e-27   # kg (proton)
    expected = np.sqrt(2 * k_B * temperature / mass)
    result = calculate_thermal_speed(temperature, mass)
    assert np.isclose(result, expected, rtol=1e-6)
```

### Integration Tests
Test component interactions:
```python
def test_plasma_with_spacecraft():
    """Test Plasma correctly integrates Spacecraft data."""
    plasma = Plasma(plasma_data, 'p1', 'a', spacecraft=sc_data)
    coulomb = plasma.nc()  # Should work with spacecraft
    assert coulomb > 0
```

### Edge Case Tests
```python
def test_single_point_data():
    """Test with single timestamp."""
    single_point = plasma_data.iloc[[0]]
    plasma = Plasma(single_point, 'p1')
    assert len(plasma.data) == 1

def test_missing_species():
    """Test graceful handling of missing species."""
    plasma = Plasma(plasma_data, 'p1', 'nonexistent')
    assert 'nonexistent' not in plasma.species
```

### Numerical Tests
```python
def test_fit_convergence():
    """Test that fits converge to known solutions."""
    x = np.linspace(0, 10, 100)
    y = 2 * x + 1 + np.random.normal(0, 0.1, 100)
    fit = LinearFit(x, y)
    fit.make_fit()
    assert np.isclose(fit.params[0], 2, rtol=0.1)
    assert np.isclose(fit.params[1], 1, rtol=0.1)
```

## Test Data Management

### Test Data Files
Located in `tests/data/`:
- `plasma.csv`: Standard plasma measurements
- `spacecraft.csv`: Spacecraft trajectory data
- `epoch.csv`: Time series for testing

### Data Generation
```python
@pytest.fixture
def synthetic_plasma():
    """Generate synthetic plasma data for testing."""
    n = 1000
    times = pd.date_range('2020-01-01', periods=n, freq='1min')
    data = {
        ('n', '', 'p1'): np.random.uniform(1, 10, n),
        ('v', 'x', 'p1'): np.random.uniform(300, 500, n),
        ('b', 'x', ''): np.random.normal(0, 5, n),
    }
    return pd.DataFrame(data, index=times)
```

## Testing Standards

### Assertion Patterns
```python
# Numerical comparisons
assert np.allclose(result, expected, rtol=1e-6)

# DataFrame comparisons
pd.testing.assert_frame_equal(df1, df2)

# Exception testing
with pytest.raises(ValueError, match="Invalid species"):
    Plasma(data, 'invalid')
```

### Parametrized Tests
```python
@pytest.mark.parametrize("species,mass", [
    ('p1', 1.67e-27),
    ('a', 6.64e-27),
    ('e', 9.11e-31),
])
def test_ion_mass(species, mass):
    ion = Ion(data, species)
    assert np.isclose(ion.mass, mass, rtol=1e-3)
```

### Performance Tests
```python
@pytest.mark.slow
def test_large_dataset_performance():
    """Test performance with large datasets."""
    large_data = generate_large_dataset(1_000_000)
    start = time.time()
    plasma = Plasma(large_data, 'p1')
    elapsed = time.time() - start
    assert elapsed < 5.0  # Should process in < 5 seconds
```

## Coverage Requirements

### Coverage Configuration
```ini
# setup.cfg or .coveragerc
[coverage:run]
source = solarwindpy
omit = 
    */tests/*
    */conftest.py

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

### Running Coverage
```bash
# Run with coverage
pytest --cov=solarwindpy --cov-report=html

# Check specific module
pytest --cov=solarwindpy.core tests/core/

# Fail if below threshold
pytest --cov=solarwindpy --cov-fail-under=95
```

## Common Testing Patterns

### Mocking External Dependencies
```python
@patch('solarwindpy.solar_activity.lisird.download_data')
def test_lisird_offline(mock_download):
    """Test LISIRD interface when offline."""
    mock_download.return_value = cached_data
    result = get_solar_indices()
    assert result is not None
    mock_download.assert_called_once()
```

### Temporary Files
```python
def test_data_export(tmp_path):
    """Test exporting data to file."""
    output_file = tmp_path / "output.csv"
    plasma.export(output_file)
    assert output_file.exists()
    loaded = pd.read_csv(output_file)
    assert len(loaded) == len(plasma.data)
```

## Integration Points

- Uses fixtures from **DataFrameArchitect** patterns
- Validates physics with **PhysicsValidator** rules
- Tests numerical stability per **NumericalStabilityGuard**
- Ensures plotting per **PlottingEngineer** requirements

## Debugging Failed Tests

1. Run specific test in verbose mode:
   ```bash
   pytest -vvs tests/core/test_plasma.py::test_function
   ```

2. Use pytest debugger:
   ```python
   import pytest
   pytest.set_trace()  # Debugger breakpoint
   ```

3. Check test isolation:
   ```bash
   pytest --random-order  # Detect order dependencies
   ```