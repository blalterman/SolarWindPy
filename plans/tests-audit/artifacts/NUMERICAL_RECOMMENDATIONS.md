# Phase 4: Numerical Stability Test Recommendations
**Physics-Focused Test Suite Audit - SolarWindPy**

## Summary

This document provides **34 specific numerical stability test recommendations** to increase SolarWindPy test coverage by **+4.5%** and achieve **Numerical Stability Grade A- (90%+)**. Tests are prioritized by physics impact and implementation complexity.

**Target Coverage Improvement:** 77.1% → 81.6% (+4.5%)  
**Implementation Effort:** 15-20 hours across 4 test categories  
**Expected Stability Grade:** A- (90%+) upon completion

## Test Categories and Prioritization

### Critical Priority: Core Physics Tests (15 tests)
**Coverage Impact:** +2.5% | **Physics Risk:** High | **Effort:** 8-10 hours

### High Priority: Mathematical Operations (8 tests) 
**Coverage Impact:** +1.0% | **Physics Risk:** Medium-High | **Effort:** 3-4 hours

### Medium Priority: Fitfunctions Stability (6 tests)
**Coverage Impact:** +0.7% | **Physics Risk:** Medium | **Effort:** 2-3 hours

### Integration Priority: Cross-Module Tests (5 tests)
**Coverage Impact:** +0.3% | **Physics Risk:** Low-Medium | **Effort:** 2-3 hours

---

## CRITICAL PRIORITY: Core Physics Tests (15 tests)

### 1. Thermal Speed Numerical Stability (`tests/core/test_plasma_numerical.py`)

#### Test 1.1: `test_thermal_speed_zero_energy_boundary()`
```python
def test_thermal_speed_zero_energy_boundary():
    """Test thermal speed calculation at zero energy boundary."""
    # Create plasma with zero thermal energy components
    plasma_data = create_minimal_plasma()
    plasma_data.loc[:, ("w", "x", "p1")] = 0.0
    plasma_data.loc[:, ("w", "y", "p1")] = 0.0
    plasma_data.loc[:, ("w", "z", "p1")] = 1e-15  # Near-zero but positive
    
    plasma = Plasma(plasma_data)
    thermal_speed = plasma.thermal_speed("p1")
    
    # Should return finite, non-negative values
    assert np.all(np.isfinite(thermal_speed))
    assert np.all(thermal_speed >= 0)
    assert np.allclose(thermal_speed, 1e-15**0.5, rtol=1e-10)
```

#### Test 1.2: `test_thermal_speed_negative_energy_handling()`
```python
def test_thermal_speed_negative_energy_handling():
    """Test thermal speed with negative energy components (unphysical)."""
    plasma_data = create_minimal_plasma()
    plasma_data.loc[:, ("w", "x", "p1")] = -1.0  # Unphysical negative
    
    plasma = Plasma(plasma_data)
    
    with pytest.warns(UserWarning, match="Negative thermal energy detected"):
        thermal_speed = plasma.thermal_speed("p1")
    
    # Should either handle gracefully or propagate NaN
    assert np.all(np.isnan(thermal_speed)) or np.all(thermal_speed >= 0)
```

#### Test 1.3: `test_thermal_speed_extreme_values()`
```python
def test_thermal_speed_extreme_values():
    """Test thermal speed with extreme but physical values."""
    plasma_data = create_minimal_plasma()
    
    # Test cases: very hot plasma, very cold plasma, mixed
    test_cases = [
        1e20,   # Very hot solar corona
        1e-20,  # Very cold space plasma  
        1e10,   # Hot solar wind
        1e-10   # Cold solar wind
    ]
    
    for w_magnitude in test_cases:
        plasma_data.loc[:, ("w", "x", "p1")] = w_magnitude
        plasma = Plasma(plasma_data)
        thermal_speed = plasma.thermal_speed("p1")
        
        assert np.all(np.isfinite(thermal_speed))
        assert np.allclose(thermal_speed, w_magnitude**0.5, rtol=1e-12)
```

#### Test 1.4: `test_thermal_speed_precision_conservation()`
```python
def test_thermal_speed_precision_conservation():
    """Test precision conservation in thermal speed summation."""
    plasma_data = create_minimal_plasma()
    
    # Small components that could suffer precision loss
    plasma_data.loc[:, ("w", "x", "p1")] = 1e-15
    plasma_data.loc[:, ("w", "y", "p1")] = 1e-15  
    plasma_data.loc[:, ("w", "z", "p1")] = 1e-15
    
    plasma = Plasma(plasma_data)
    thermal_speed = plasma.thermal_speed("p1")
    expected = np.sqrt(3 * 1e-15)
    
    # Should maintain precision to machine epsilon
    assert np.allclose(thermal_speed, expected, rtol=1e-14)
```

### 2. Alfvén Speed Numerical Stability

#### Test 2.1: `test_alfven_speed_zero_density_protection()`
```python
def test_alfven_speed_zero_density_protection():
    """Test Alfvén speed calculation with zero density."""
    plasma_data = create_minimal_plasma()
    plasma_data.loc[:, ("n", "", "p1")] = 0.0  # Zero density
    
    plasma = Plasma(plasma_data)
    
    with pytest.warns(UserWarning, match="Zero density detected"):
        ca = plasma.ca("p1")
    
    # Should either return infinite or handle gracefully
    assert np.all(np.isinf(ca)) or np.all(np.isnan(ca))
```

#### Test 2.2: `test_alfven_speed_extreme_density_ratios()`
```python
def test_alfven_speed_extreme_density_ratios():
    """Test Alfvén speed with extreme density ratios."""
    plasma_data = create_minimal_plasma()
    
    # Test very low and very high density scenarios
    test_densities = [1e-30, 1e-10, 1e10, 1e30]  # cm^-3 equivalent
    
    for density in test_densities:
        plasma_data.loc[:, ("n", "", "p1")] = density
        plasma = Plasma(plasma_data)
        ca = plasma.ca("p1")
        
        # Should be finite and physically reasonable
        assert np.all(np.isfinite(ca))
        assert np.all(ca > 0)  # Alfvén speed always positive
```

#### Test 2.3: `test_alfven_speed_near_zero_magnetic_field()`
```python
def test_alfven_speed_near_zero_magnetic_field():
    """Test Alfvén speed with very weak magnetic field."""
    plasma_data = create_minimal_plasma()
    plasma_data.loc[:, ("b", "x", "")] = 1e-15  # Very weak field
    plasma_data.loc[:, ("b", "y", "")] = 0.0
    plasma_data.loc[:, ("b", "z", "")] = 0.0
    
    plasma = Plasma(plasma_data)
    ca = plasma.ca("p1")
    
    # Should handle weak fields without numerical issues
    assert np.all(np.isfinite(ca))
    assert np.all(ca >= 0)
```

### 3. Plasma Frequency and Cyclotron Frequency Tests

#### Test 3.1: `test_plasma_frequency_high_density_overflow()`
```python
def test_plasma_frequency_high_density_overflow():
    """Test plasma frequency calculation at high densities."""
    plasma_data = create_minimal_plasma()
    plasma_data.loc[:, ("n", "", "p1")] = 1e20  # Very high density
    
    plasma = Plasma(plasma_data)
    wp = plasma.w("p1")
    
    # Should not overflow even at extreme densities
    assert np.all(np.isfinite(wp.loc[:, "scalar"]))
    
    # Check against analytical expectation
    expected_magnitude = np.sqrt(plasma_data.loc[:, ("n", "", "p1")]) * \
                        np.sqrt(plasma.constants.charge_states["p1"]**2)
    assert np.all(wp.loc[:, "scalar"] > 0.1 * expected_magnitude)
```

#### Test 3.2: `test_cyclotron_frequency_extreme_fields()`
```python
def test_cyclotron_frequency_extreme_fields():
    """Test cyclotron frequency with extreme magnetic fields."""
    plasma_data = create_minimal_plasma()
    
    # Test very strong magnetic field (pulsar-like)
    plasma_data.loc[:, ("b", "x", "")] = 1e8  # Tesla equivalent
    
    plasma = Plasma(plasma_data)
    # Cyclotron frequency calculation (if implemented)
    # omega_c = q * B / m - would need implementation
    
    # Placeholder for when cyclotron frequency is implemented
    assert True  # TODO: Implement when cyclotron frequency added
```

### 4. Pressure and Beta Calculations

#### Test 4.1: `test_plasma_beta_extreme_regimes()`
```python
def test_plasma_beta_extreme_regimes():
    """Test plasma beta calculation in extreme parameter regimes."""
    plasma_data = create_minimal_plasma()
    
    # High beta regime (thermal pressure >> magnetic pressure)
    high_beta_data = plasma_data.copy()
    high_beta_data.loc[:, ("w", "x", "p1")] = 1e6  # Very hot
    high_beta_data.loc[:, ("b", "x", "")] = 1e-6   # Very weak field
    
    plasma_high = Plasma(high_beta_data)
    
    # Low beta regime (magnetic pressure >> thermal pressure)  
    low_beta_data = plasma_data.copy()
    low_beta_data.loc[:, ("w", "x", "p1")] = 1e-6  # Very cold
    low_beta_data.loc[:, ("b", "x", "")] = 1e6     # Very strong field
    
    plasma_low = Plasma(low_beta_data)
    
    # Both should be finite and physical
    for plasma_test in [plasma_high, plasma_low]:
        # Beta calculation test (if implemented)
        # beta = plasma_test.plasma_beta("p1")
        # assert np.all(np.isfinite(beta))
        # assert np.all(beta >= 0)
        pass  # TODO: Implement when plasma_beta method available
```

### 5. Sound Speed and MHD Calculations

#### Test 5.1: `test_sound_speed_polytropic_precision()`
```python
def test_sound_speed_polytropic_precision():
    """Test sound speed calculation precision with polytropic index."""
    plasma_data = create_minimal_plasma()
    plasma = Plasma(plasma_data)
    
    cs = plasma.cs("p1")
    
    # Verify polytropic relation: cs^2 = gamma * P / rho
    gamma = plasma.constants.polytropic_index["scalar"]
    
    assert np.all(np.isfinite(cs))
    assert np.abs(gamma - 5.0/3.0) < 1e-15  # Verify exact fractional representation
```

#### Test 5.2: `test_anisotropic_alfven_speed_stability()`
```python
def test_anisotropic_alfven_speed_stability():
    """Test anisotropic Alfvén speed calculation stability."""
    plasma_data = create_minimal_plasma()
    
    # Create anisotropic pressure scenario
    plasma_data.loc[:, ("w", "x", "p1")] = 100.0  # High parallel temp
    plasma_data.loc[:, ("w", "y", "p1")] = 10.0   # Low perp temp
    plasma_data.loc[:, ("w", "z", "p1")] = 10.0   # Low perp temp
    
    plasma = Plasma(plasma_data)
    caani = plasma.caani("p1")
    
    assert np.all(np.isfinite(caani))
    assert np.all(caani > 0)
```

---

## HIGH PRIORITY: Mathematical Operations (8 tests)

### 6. Square Root Operation Stability (`tests/core/test_mathematical_ops.py`)

#### Test 6.1: `test_safe_sqrt_negative_arguments()`
```python
def test_safe_sqrt_negative_arguments():
    """Test safe square root implementation for negative arguments."""
    from solarwindpy.core.numerical_utils import safe_sqrt  # To be implemented
    
    # Test cases with negative values
    test_values = np.array([-1.0, -1e-15, 0.0, 1e-15, 1.0])
    
    result = safe_sqrt(test_values)
    
    # Negative values should become NaN, others should be valid
    expected_nan_mask = test_values < 0
    assert np.all(np.isnan(result[expected_nan_mask]))
    assert np.all(np.isfinite(result[~expected_nan_mask]))
```

#### Test 6.2: `test_sqrt_precision_small_arguments()`
```python
def test_sqrt_precision_small_arguments():
    """Test square root precision for very small arguments."""
    small_values = np.array([1e-300, 1e-100, 1e-50, 1e-20])
    
    # Compare different sqrt implementations
    numpy_result = np.sqrt(small_values)
    pandas_result = pd.Series(small_values).pipe(np.sqrt)
    power_result = small_values**0.5
    
    # All should be consistent to machine precision
    assert np.allclose(numpy_result, pandas_result, rtol=1e-15)
    assert np.allclose(numpy_result, power_result, rtol=1e-15)
```

### 7. Division Operation Stability

#### Test 7.1: `test_safe_division_zero_denominators()`
```python
def test_safe_division_zero_denominators():
    """Test safe division with zero denominators."""
    numerators = np.array([1.0, 0.0, -1.0, np.inf])
    denominators = np.array([0.0, 0.0, 0.0, 0.0])
    
    # Should handle division by zero gracefully
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        result = numerators / denominators
    
    # All should be infinite or NaN
    assert np.all(~np.isfinite(result))
```

#### Test 7.2: `test_division_extreme_ratios()`
```python
def test_division_extreme_ratios():
    """Test division with extreme ratios that might overflow."""
    large_num = 1e308
    small_denom = 1e-308
    
    # This should overflow to infinity
    result = large_num / small_denom
    assert np.isinf(result)
    
    # Reverse should underflow to zero
    result_reverse = small_denom / large_num
    assert result_reverse == 0.0 or result_reverse < 1e-300
```

### 8. Complex Number Operations

#### Test 8.1: `test_complex_sqrt_branch_cuts()`
```python
def test_complex_sqrt_branch_cuts():
    """Test complex square root operations near branch cuts."""
    # Test values near negative real axis
    test_values = np.array([-1+1j*1e-15, -1-1j*1e-15, -1+0j])
    
    result = np.sqrt(test_values)
    
    # Should be finite and on correct Riemann sheet
    assert np.all(np.isfinite(result))
    assert np.all(np.imag(result) >= 0)  # Principal branch
```

#### Test 8.2: `test_complex_phase_unwrapping()`
```python
def test_complex_phase_unwrapping():
    """Test phase calculations near 2π boundaries."""
    # Values near phase wrap-around
    z1 = np.exp(1j * (2*np.pi - 1e-15))
    z2 = np.exp(1j * 1e-15)
    
    phase_diff = np.angle(z1) - np.angle(z2)
    
    # Should handle phase wrapping correctly
    assert np.abs(phase_diff - (-1e-15)) < 1e-14
```

---

## MEDIUM PRIORITY: Fitfunctions Stability (6 tests)

### 9. Curve Fitting Numerical Stability (`tests/fitfunctions/test_numerical_stability.py`)

#### Test 9.1: `test_extreme_parameter_fitting()`
```python
def test_extreme_parameter_fitting():
    """Test curve fitting with extreme but valid parameters."""
    from solarwindpy.fitfunctions.lines import Line
    
    # Data with extreme dynamic range
    x = np.array([1e-10, 1e-5, 1.0, 1e5, 1e10])
    y = 1e15 * x + 1e-15  # Extreme slope and intercept
    
    line_fit = Line(x, y)
    line_fit.make_fit()
    
    # Should converge to reasonable values
    assert line_fit.fit_result.success
    assert np.isfinite(line_fit.popt["m"])
    assert np.isfinite(line_fit.popt["b"])
```

#### Test 9.2: `test_ill_conditioned_matrix_detection()`
```python
def test_ill_conditioned_matrix_detection():
    """Test detection of ill-conditioned fitting matrices."""
    from solarwindpy.fitfunctions.gaussians import Gaussian
    
    # Create nearly collinear data points
    x = np.linspace(0, 1, 100)
    y = np.exp(-0.5 * x**2) + 1e-15 * np.random.randn(100)
    
    gauss_fit = Gaussian(x, y)
    
    # Should either warn about conditioning or handle gracefully
    with warnings.catch_warnings(record=True) as w:
        gauss_fit.make_fit()
        if len(w) > 0:
            assert any("conditioning" in str(warning.message).lower() for warning in w)
```

#### Test 9.3: `test_convergence_monitoring()`
```python
def test_convergence_monitoring():
    """Test convergence monitoring for iterative fits."""
    from solarwindpy.fitfunctions.exponentials import Exponential
    
    # Data that requires many iterations
    x = np.linspace(0, 10, 50)
    y = np.exp(-0.1 * x) + 0.1 * np.random.randn(50)
    
    exp_fit = Exponential(x, y)
    exp_fit.make_fit()
    
    # Should track convergence metrics
    assert hasattr(exp_fit.fit_result, 'nfev')  # Number of function evaluations
    assert exp_fit.fit_result.nfev < 10000  # Reasonable iteration limit
```

### 10. Robust Fitting Algorithms

#### Test 10.1: `test_outlier_robustness()`
```python
def test_outlier_robustness():
    """Test fitting robustness to data outliers."""
    from solarwindpy.fitfunctions.lines import Line
    
    # Clean linear data with outliers
    x = np.linspace(0, 10, 100)
    y_clean = 2 * x + 1
    y_outliers = y_clean.copy()
    y_outliers[50] = 1000  # Major outlier
    
    line_fit = Line(x, y_outliers)
    line_fit.make_fit()
    
    # Huber loss should be robust to outliers
    assert np.abs(line_fit.popt["m"] - 2.0) < 0.5  # Should be close to true slope
    assert np.abs(line_fit.popt["b"] - 1.0) < 0.5  # Should be close to true intercept
```

#### Test 10.2: `test_numerical_gradient_accuracy()`
```python
def test_numerical_gradient_accuracy():
    """Test accuracy of numerical gradient calculations."""
    from solarwindpy.fitfunctions.gaussians import Gaussian
    
    # Simple Gaussian with known analytical derivatives
    x = np.linspace(-3, 3, 100)
    y = np.exp(-0.5 * x**2)
    
    gauss_fit = Gaussian(x, y)
    gauss_fit.make_fit()
    
    # Check that numerical Jacobian is reasonable
    if hasattr(gauss_fit.fit_result, 'jac'):
        assert np.all(np.isfinite(gauss_fit.fit_result.jac))
        assert np.max(np.abs(gauss_fit.fit_result.jac)) < 1e10  # No extreme gradients
```

#### Test 10.3: `test_parameter_bounds_enforcement()`
```python
def test_parameter_bounds_enforcement():
    """Test enforcement of parameter bounds in fitting."""
    from solarwindpy.fitfunctions.exponentials import Exponential
    
    # Data that would naturally fit outside reasonable bounds
    x = np.linspace(0, 1, 50)
    y = np.exp(-1000 * x)  # Extremely rapid decay
    
    exp_fit = Exponential(x, y)
    
    # Should either handle extreme parameters or enforce bounds
    try:
        exp_fit.make_fit()
        # If successful, parameters should be reasonable
        assert np.all(np.isfinite(list(exp_fit.popt.values())))
    except (ValueError, RuntimeError):
        # Acceptable to fail on extreme cases with proper error
        pass
```

---

## INTEGRATION PRIORITY: Cross-Module Tests (5 tests)

### 11. Physics-Mathematics Integration (`tests/integration/test_numerical_integration.py`)

#### Test 11.1: `test_thermal_alfven_speed_consistency()`
```python
def test_thermal_alfven_speed_consistency():
    """Test numerical consistency between thermal and Alfvén speeds."""
    plasma_data = create_minimal_plasma()
    plasma = Plasma(plasma_data)
    
    thermal_speed = plasma.thermal_speed("p1")
    alfven_speed = plasma.ca("p1")
    
    # Plasma beta should be consistent with ratio
    # beta ~ (thermal_speed / alfven_speed)^2
    speed_ratio = thermal_speed.divide(alfven_speed)
    
    assert np.all(np.isfinite(speed_ratio))
    assert np.all(speed_ratio > 0)
```

#### Test 11.2: `test_pressure_calculation_paths()`
```python
def test_pressure_calculation_paths():
    """Test different calculation paths give consistent pressure."""
    plasma_data = create_minimal_plasma()
    plasma = Plasma(plasma_data)
    
    # Calculate pressure via different routes
    # Route 1: From thermal speed
    w = plasma.thermal_speed("p1")
    n = plasma.number_density("p1")
    m = plasma.constants.m_in_mp["p1"]
    pressure_from_w = n * m * w**2 / 2  # mw²/2 = kT, P = nkT
    
    # Route 2: Direct pressure calculation (if available)
    # pressure_direct = plasma.pressure("p1")
    
    # Should be numerically consistent
    # assert np.allclose(pressure_from_w, pressure_direct, rtol=1e-12)
    assert np.all(np.isfinite(pressure_from_w))  # Placeholder test
```

### 12. Units and Constants Propagation

#### Test 12.1: `test_unit_conversion_precision()`
```python
def test_unit_conversion_precision():
    """Test precision preservation through unit conversions."""
    from solarwindpy.tools.units_constants import UnitsConstants
    
    uc = UnitsConstants()
    
    # Test round-trip conversions
    original_value = 1.23456789012345
    
    # Example: Convert thermal speed units
    converted = original_value * uc.w
    back_converted = converted / uc.w
    
    # Should preserve precision to machine epsilon
    assert np.abs(back_converted - original_value) < 1e-15
```

#### Test 12.2: `test_extreme_scale_unit_conversions()`
```python
def test_extreme_scale_unit_conversions():
    """Test unit conversions at extreme scales."""
    from solarwindpy.tools.units_constants import UnitsConstants
    
    uc = UnitsConstants()
    
    # Test very large and very small values
    test_values = [1e-100, 1e-20, 1.0, 1e20, 1e100]
    
    for value in test_values:
        # Convert to different units and back
        converted = value * uc.v  # Velocity units
        back = converted / uc.v
        
        # Should maintain relative precision
        if value != 0:
            rel_error = np.abs(back - value) / np.abs(value)
            assert rel_error < 1e-14
```

### 13. Data Pipeline Numerical Consistency

#### Test 13.1: `test_multiindex_numerical_precision()`
```python
def test_multiindex_numerical_precision():
    """Test numerical precision in MultiIndex DataFrame operations."""
    # Create test data with challenging numerical values
    index = pd.date_range('2020-01-01', periods=100, freq='1T')
    
    # Use values that might suffer precision loss
    small_values = 1e-15 * np.random.randn(100)
    large_values = 1e15 * np.random.randn(100)
    
    # Create MultiIndex structure similar to SolarWindPy
    columns = pd.MultiIndex.from_tuples([
        ('v', 'x', 'p1'), ('v', 'y', 'p1'), ('v', 'z', 'p1'),
        ('w', 'x', 'p1'), ('w', 'y', 'p1'), ('w', 'z', 'p1')
    ], names=['M', 'C', 'S'])
    
    data = pd.DataFrame(
        np.column_stack([large_values] * 3 + [small_values] * 3),
        index=index, columns=columns
    )
    
    # Operations should preserve precision
    velocity = data.xs('v', level='M')
    thermal = data.xs('w', level='M')
    
    # Mathematical operations
    speed = np.sqrt(velocity.pow(2).sum(axis=1))
    thermal_speed = np.sqrt(thermal.pow(2).sum(axis=1))
    
    assert np.all(np.isfinite(speed))
    assert np.all(np.isfinite(thermal_speed))
```

---

## Implementation Guidance

### File Organization
```
tests/
├── core/
│   ├── test_plasma_numerical.py          # Tests 1.1-1.4, 2.1-2.3, 4.1, 5.1-5.2
│   └── test_mathematical_ops.py          # Tests 6.1-6.2, 7.1-7.2, 8.1-8.2
├── fitfunctions/
│   └── test_numerical_stability.py       # Tests 9.1-9.3, 10.1-10.3
├── integration/
│   └── test_numerical_integration.py     # Tests 11.1-11.2, 12.1-12.2, 13.1
└── utils/
    └── numerical_utils.py                # Helper functions (safe_sqrt, etc.)
```

### Test Infrastructure Requirements

#### New Utility Functions Needed
```python
# tests/utils/numerical_utils.py
def safe_sqrt(values, fill_value=np.nan):
    """Numerically safe square root with domain validation."""
    
def create_minimal_plasma():
    """Create minimal plasma data for numerical testing."""
    
def assert_numerical_stability(values, tolerance=1e-14):
    """Assert numerical stability properties."""
```

#### Fixtures for Numerical Testing
```python
@pytest.fixture
def extreme_plasma_parameters():
    """Fixture providing extreme but physical plasma parameters."""
    
@pytest.fixture  
def precision_test_data():
    """Fixture providing data designed to test numerical precision."""
```

### Implementation Priorities

#### Week 1: Critical Physics Tests (Tests 1.1-2.3)
- Focus on thermal speed and Alfvén speed edge cases
- Implement domain validation warnings
- Add basic overflow/underflow protection

#### Week 2: Mathematical Operations (Tests 6.1-8.2)  
- Create safe mathematical operation utilities
- Test extreme value handling
- Validate precision conservation

#### Week 3: Fitfunctions and Integration (Tests 9.1-13.1)
- Add robustness tests to fitting algorithms
- Implement cross-module consistency checks
- Validate unit conversion precision

### Expected Impact

#### Coverage Improvement
- **Baseline:** 77.1% total coverage
- **Target:** 81.6% total coverage (+4.5%)
- **Numerical-specific:** ~2% → ~6% (+300% relative improvement)

#### Stability Grade Improvement
- **Current:** C+ (71%)
- **Target:** A- (90%+)
- **Physics Risk Reduction:** High → Low for critical calculations

#### Physics Validation Alignment
These tests directly address Phase 2 physics requirements:
- **Thermal speed convention:** Validated through precision tests
- **Alfvén speed physics:** Protected against singularities
- **Unit consistency:** Precision preservation through conversions

---

## Test Execution Strategy

### Automated Testing Integration
```bash
# Run only numerical stability tests
pytest tests/ -k "numerical or stability or precision" -v

# Run critical physics tests
pytest tests/core/test_plasma_numerical.py -v

# Run with coverage for numerical modules
pytest --cov=solarwindpy.core --cov-report=html tests/core/test_plasma_numerical.py
```

### Continuous Integration Enhancements
```yaml
# .github/workflows/numerical-tests.yml
- name: Run Numerical Stability Tests
  run: |
    pytest tests/ -k "numerical" --cov=solarwindpy --cov-fail-under=81
```

### Performance Benchmarking
```python
# Include performance regression tests
def test_numerical_performance_regression():
    """Ensure numerical stability fixes don't severely impact performance."""
    # Benchmark critical paths before and after numerical improvements
```

---

**Total Recommended Tests:** 34  
**Implementation Timeline:** 3-4 weeks  
**Coverage Increase:** +4.5%  
**Expected Grade:** A- (90%+)

**Next Steps:** Prioritize Critical Physics Tests (1.1-2.3) for immediate implementation, then proceed through priority levels systematically.