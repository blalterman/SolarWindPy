# Contributing to SolarWindPy

Thank you for considering contributing to SolarWindPy. This guide ensures that contributions maintain the high standards of scientific accuracy and numerical stability required for plasma physics research.

## Development Workflow

### 1. Environment Setup

Create a virtual environment and install dependencies:

```bash
# Create conda environment
conda env create -f solarwindpy-20250403.yml
conda activate solarwindpy-20250403
pip install -e .

# Or generate environment from requirements
python scripts/requirements_to_conda_env.py --name solarwindpy-dev
conda env create -f solarwindpy-dev.yml
conda activate solarwindpy-dev
pip install -e .
```

### 2. Physics Validation Requirements (MANDATORY)

All contributions involving physics calculations must meet rigorous validation standards:

#### 2.1 Parameter Validation Standards
Every physics function MUST validate inputs for:

```python
# REQUIRED: Input validation pattern
def your_physics_function(temperature, density, magnetic_field):
    """Your physics calculation with required validation."""
    
    # 1. Check for positive physical quantities
    if np.any(temperature <= 0):
        raise ValueError("Temperature must be positive")
    
    if np.any(density <= 0):
        raise ValueError("Density must be positive")
    
    # 2. Check for reasonable physical ranges
    if np.any(temperature > 1e8):  # K
        warnings.warn("Temperature exceeds typical solar wind range")
    
    if np.any(density < 1e-25):  # kg/m³
        warnings.warn("Density below numerical precision threshold")
    
    # 3. Perform calculation with error handling
    try:
        result = your_calculation(temperature, density, magnetic_field)
    except (OverflowError, ZeroDivisionError) as e:
        raise RuntimeError(f"Numerical error in calculation: {e}")
    
    # 4. Validate results are physical
    if np.any(~np.isfinite(result)):
        raise RuntimeError("Calculation produced non-finite results")
    
    return result
```

#### 2.2 Critical Physics Error Prevention

Based on comprehensive numerical stability analysis, the following patterns are **PROHIBITED**:

```python
# ❌ PROHIBITED: Zero density vulnerability (causes infinite Alfvén speeds)
alfven_speed = rho.pow(-0.5) * magnetic_field_coefficient

# ✅ REQUIRED: Protected calculation
def safe_alfven_speed(density, magnetic_field):
    min_density = 1e-23  # kg/m³
    if np.any(density <= min_density):
        raise ValueError(f"Density must be > {min_density} kg/m³ for reliable Alfvén speed")
    
    return magnetic_field / np.sqrt(mu0 * density)

# ❌ PROHIBITED: Negative energy vulnerability (causes NaN thermal speeds)  
thermal_speed = thermal_energy.pow(0.5)

# ✅ REQUIRED: Protected calculation
def safe_thermal_speed(thermal_energy):
    if np.any(thermal_energy <= 0):
        raise ValueError("Thermal energy must be positive")
    
    return np.sqrt(thermal_energy)
```

#### 2.3 Numerical Stability Testing (MANDATORY)

Every physics function requires numerical stability tests:

```python
# tests/test_your_module.py
import pytest
import numpy as np
from solarwindpy.your_module import your_physics_function

class TestNumericalStability:
    """Mandatory numerical stability tests for physics calculations."""
    
    def test_zero_density_protection(self):
        """Test protection against zero density singularities."""
        with pytest.raises(ValueError, match="Density must be positive"):
            your_physics_function(temperature=1e5, density=0.0, magnetic_field=5e-9)
    
    def test_negative_temperature_protection(self):
        """Test protection against negative temperatures."""
        with pytest.raises(ValueError, match="Temperature must be positive"):
            your_physics_function(temperature=-1000, density=1e-21, magnetic_field=5e-9)
    
    def test_extreme_parameter_handling(self):
        """Test behavior at parameter boundaries."""
        # Test very small values
        result_small = your_physics_function(
            temperature=1e3, density=1e-24, magnetic_field=0.1e-9
        )
        assert np.all(np.isfinite(result_small))
        
        # Test very large values
        result_large = your_physics_function(
            temperature=1e8, density=1e-15, magnetic_field=100e-9
        )
        assert np.all(np.isfinite(result_large))
    
    def test_precision_preservation(self):
        """Test numerical precision is maintained."""
        # Use high-precision reference values
        temp, density, b_field = 1e6, 1e-20, 5e-9
        result = your_physics_function(temp, density, b_field)
        
        # Verify precision (adapt expected_value to your calculation)
        expected_value = calculate_reference_value(temp, density, b_field)
        relative_error = np.abs((result - expected_value) / expected_value)
        assert np.all(relative_error < 1e-12), "Precision loss detected"
    
    def test_vector_operations_stability(self):
        """Test vector operations don't lose precision."""
        # Test with nearly parallel vectors (catastrophic cancellation risk)
        large_component = 1e6
        small_components = [1e-3, 1e-3]
        
        # Your vector calculation should handle this robustly
        result = your_vector_function(large_component, small_components)
        assert np.all(np.isfinite(result))
```

### 3. Code Quality Standards

#### 3.1 Formatting and Linting
Format code with `black` and lint with `flake8`:

```bash
black solarwindpy/ tests/
flake8 solarwindpy/ tests/
```

#### 3.2 Documentation Requirements
Ensure all docstrings follow NumPy style with physics-specific additions:

```python
def physics_function(parameter1, parameter2):
    """
    Brief description of the physics calculation.
    
    Parameters
    ----------
    parameter1 : float or array-like
        Description including physical units and valid range
    parameter2 : float or array-like  
        Description including physical units and valid range
    
    Returns
    -------
    result : float or array-like
        Description with units and expected range
    
    Raises
    ------
    ValueError
        When input parameters are non-physical or outside valid ranges
    RuntimeError
        When calculation encounters numerical instabilities
    
    Notes
    -----
    Physics theory explanation and assumptions.
    
    .. warning::
       Description of numerical limitations and edge cases.
       
    Examples
    --------
    >>> # Example with parameter validation
    >>> import numpy as np
    >>> temp = np.array([1e5, 2e5, 1e6])  # K
    >>> result = physics_function(temp, other_params)
    """
```

### 4. Testing Requirements

#### 4.1 Comprehensive Test Coverage
Run the complete test suite:

```bash
pytest -q --cov=solarwindpy --cov-report=html
```

**Minimum coverage requirements:**
- Overall coverage: ≥95%  
- Physics modules: ≥98%
- Numerical stability tests: 100% for critical functions

#### 4.2 Physics Validation Tests
Every physics function requires:

1. **Domain validation tests** - verify input parameter ranges
2. **Edge case tests** - test behavior at calculation boundaries  
3. **Precision tests** - verify numerical accuracy preservation
4. **Cross-validation tests** - compare with analytical solutions where possible

#### 4.3 Integration Tests
Test interaction between modules:

```python
def test_multi_module_consistency():
    """Test consistency across physics modules."""
    plasma = create_test_plasma()
    
    # Calculate same quantity using different approaches
    thermal_speed_1 = plasma.thermal_speed()
    thermal_speed_2 = alternative_thermal_speed_calculation(plasma)
    
    # Verify consistency within numerical precision
    np.testing.assert_allclose(thermal_speed_1, thermal_speed_2, rtol=1e-12)
```

### 5. Documentation Standards

#### 5.1 Sphinx Documentation
Build documentation and ensure no warnings:

```bash
cd docs
make clean
make html SPHINXOPTS=-W
```

#### 5.2 Physics Documentation Requirements
New physics functions must include:

1. **Theoretical foundation** - mathematical derivation
2. **Valid parameter ranges** - explicit bounds for reliable calculation  
3. **Numerical considerations** - precision limitations and edge cases
4. **Example usage** - with proper parameter validation
5. **Literature references** - scientific validation sources

#### 5.3 User Safety Documentation
Critical functions must include user warnings:

```rst
.. danger::
   This calculation has known numerical instabilities.
   Always validate input parameters are within specified ranges.
```

### 6. Scientific Validation Checklist

Before submitting physics-related contributions:

- [ ] **Input validation implemented** for all parameters
- [ ] **Edge case protection** against singularities and mathematical errors
- [ ] **Numerical stability tests** covering boundary conditions
- [ ] **Results validation** against expected physical ranges
- [ ] **Cross-validation** with literature values or alternative methods
- [ ] **Documentation includes** physics theory and limitations
- [ ] **User warnings** documented for numerical limitations
- [ ] **Performance tested** with large-scale realistic datasets

### 7. Git Workflow Standards

#### 7.1 Branch Organization
- **Feature branches**: `feature/description-of-change`
- **Bug fixes**: `fix/issue-description`  
- **Physics enhancements**: `physics/calculation-improvement`

#### 7.2 Commit Standards
Use conventional commit format with physics context:

```
feat(plasma): add robust Alfvén speed calculation with zero-density protection

- Implement minimum density threshold validation
- Add comprehensive numerical stability tests
- Include physics theory documentation  
- Prevent infinite speed calculation errors

Fixes critical numerical vulnerability in plasma.alfven_speed()
```

#### 7.3 Pre-commit Validation
Install pre-commit hooks for automatic validation:

```bash
pre-commit install
```

This runs automatic checks for:
- Code formatting (black)
- Linting (flake8)
- Basic test execution
- Documentation link validation

### 8. Physics-Specific Contribution Guidelines

#### 8.1 New Physics Calculations
When adding new plasma physics calculations:

1. **Literature review** - verify calculation method against established sources
2. **Mathematical validation** - confirm derivation and assumptions
3. **Parameter space analysis** - identify valid input ranges
4. **Edge case identification** - determine potential numerical issues
5. **Reference implementation** - compare with established codes when possible

#### 8.2 Existing Function Modifications
When modifying physics functions:

1. **Backward compatibility** - ensure existing valid usage continues to work
2. **Performance regression testing** - verify modifications don't degrade performance
3. **Scientific accuracy validation** - confirm modifications preserve physics correctness
4. **Cross-module impact assessment** - check effects on dependent calculations

#### 8.3 Numerical Algorithm Updates
When changing numerical approaches:

1. **Precision comparison** - benchmark new vs old algorithm accuracy
2. **Stability analysis** - test robustness across full parameter space  
3. **Performance analysis** - measure computational efficiency changes
4. **Scientific validation** - confirm physics results remain consistent

### 9. Review Process

#### 9.1 Physics Review Requirements
All physics-related contributions require:

- **Code review** by maintainer with plasma physics expertise
- **Numerical validation** of test coverage and stability
- **Documentation review** for scientific accuracy
- **Integration testing** with existing physics modules

#### 9.2 Quality Gates
Contributions must pass:

1. **Automated testing** - all tests passing with required coverage
2. **Physics validation** - numerical stability and accuracy verified
3. **Documentation build** - complete documentation without warnings
4. **Performance benchmarks** - no significant regression in calculation speed

### 10. Common Issues and Solutions

#### 10.1 Numerical Instability Debugging
If you encounter numerical issues:

```python
# Debug numerical problems systematically
import numpy as np

def debug_calculation(function, *args):
    """Debug helper for numerical issues."""
    
    # Check inputs
    for i, arg in enumerate(args):
        print(f"Arg {i}: min={np.min(arg)}, max={np.max(arg)}, "
              f"has_nan={np.any(np.isnan(arg))}, has_inf={np.any(np.isinf(arg))}")
    
    # Perform calculation
    try:
        result = function(*args)
        print(f"Result: min={np.min(result)}, max={np.max(result)}, "
              f"has_nan={np.any(np.isnan(result))}, has_inf={np.any(np.isinf(result))}")
        return result
    except Exception as e:
        print(f"Calculation failed: {e}")
        return None
```

#### 10.2 Performance vs. Precision Trade-offs
When optimizing calculations:

1. **Profile before optimizing** - identify actual bottlenecks
2. **Preserve numerical accuracy** - don't sacrifice precision for minor speed gains
3. **Test edge cases thoroughly** - optimization often affects stability
4. **Document trade-offs** - explain any precision limitations introduced

### 11. Getting Help

#### 11.1 Development Questions
- **Physics questions**: Consult plasma physics literature or domain experts
- **Numerical issues**: Review numerical stability guide and common patterns
- **Testing questions**: Examine existing test patterns in similar modules

#### 11.2 Community Resources  
- **GitHub Issues**: Report bugs or request features
- **Discussions**: Ask questions about contribution process
- **Documentation**: Comprehensive guides for common tasks

## Summary

Contributing to SolarWindPy requires attention to both software engineering best practices and scientific rigor. The physics validation requirements ensure that the library maintains its reliability for scientific research while the testing standards guarantee long-term maintainability.

**Key Principles:**
1. **Scientific accuracy first** - physics correctness takes priority over performance
2. **Systematic validation** - comprehensive testing prevents numerical errors
3. **Clear documentation** - users must understand limitations and proper usage  
4. **Defensive programming** - validate inputs and handle edge cases gracefully

Thank you for helping maintain SolarWindPy as a reliable tool for solar wind plasma physics research!