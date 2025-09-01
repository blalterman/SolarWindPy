"""SolarWindPy Test Pattern Templates Domain-specific test templates for scientific
computing and plasma physics."""

import numpy as np
import pandas as pd
import pytest


# Physics Test Templates
THERMAL_SPEED_TEST = '''
def test_{function_name}_thermal_speed_physics():
    """Test {function_name} follows thermal speed convention mw² = 2kT."""
    # Arrange
    temperature = 1e5  # K
    mass = 1.67e-27   # kg (proton mass)
    expected = np.sqrt(2 * {k_constant} * temperature / mass)
    
    # Act
    result = {function_name}(temperature, mass)
    
    # Assert
    assert np.isclose(result, expected, rtol=1e-6), \\
        f"Thermal speed convention violated: expected={{expected}}, got={{result}}"
    assert result > 0, "Thermal speed must be positive"
    assert not np.isnan(result), "Thermal speed cannot be NaN"
'''

ALFVEN_SPEED_TEST = '''
def test_{function_name}_alfven_speed_physics():
    """Test {function_name} follows Alfvén speed formula V_A = B/√(μ₀ρ)."""
    # Arrange
    B = 5e-9  # Tesla (typical solar wind)
    density = 5e6  # m^-3 
    mass = 1.67e-27  # kg (proton)
    mu_0 = 4 * np.pi * 1e-7  # H/m
    rho = density * mass
    expected = B / np.sqrt(mu_0 * rho)
    
    # Act
    result = {function_name}(B, density, mass)
    
    # Assert
    assert np.isclose(result, expected, rtol=1e-6), \\
        f"Alfvén speed formula violated: expected={{expected}}, got={{result}}"
    assert result > 0, "Alfvén speed must be positive"
    # Should be much less than speed of light
    assert result < 3e8, "Alfvén speed cannot exceed speed of light"
'''

CONSERVATION_TEST = '''
def test_{function_name}_conservation_laws():
    """Test {function_name} respects conservation laws."""
    # Test mass conservation
    initial_mass = calculate_total_mass(initial_state)
    final_mass = calculate_total_mass({function_name}(initial_state))
    assert np.isclose(initial_mass, final_mass, rtol=1e-10), \\
        "Mass conservation violated"
    
    # Test energy conservation (if applicable)
    initial_energy = calculate_total_energy(initial_state)
    final_energy = calculate_total_energy({function_name}(initial_state))
    assert np.isclose(initial_energy, final_energy, rtol=1e-8), \\
        "Energy conservation violated"
'''

UNIT_CONSISTENCY_TEST = '''
def test_{function_name}_unit_consistency():
    """Test {function_name} maintains unit consistency."""
    from solarwindpy.tools import units_constants as uc
    
    # Test with different unit inputs
    value_si = {function_name}({si_input})
    value_cgs = {function_name}({cgs_input})
    
    # Convert and compare (allowing for conversion factors)
    expected_ratio = {conversion_factor}
    actual_ratio = value_cgs / value_si
    assert np.isclose(actual_ratio, expected_ratio, rtol=1e-6), \\
        f"Unit conversion inconsistent: expected_ratio={{expected_ratio}}, got={{actual_ratio}}"
'''

# Numerical Stability Templates
NUMERICAL_STABILITY_TEST = '''
def test_{function_name}_numerical_stability():
    """Test {function_name} numerical stability at boundaries."""
    # Test very small values
    small_result = {function_name}({small_input})
    assert not np.isnan(small_result), "Function unstable at small values"
    assert np.isfinite(small_result), "Function produces infinite values"
    
    # Test very large values
    large_result = {function_name}({large_input})
    assert not np.isnan(large_result), "Function unstable at large values"
    assert np.isfinite(large_result), "Function produces infinite values"
    
    # Test edge cases
    zero_result = {function_name}({zero_input})
    assert np.isfinite(zero_result) or np.isnan(zero_result), \\
        "Function should handle zero gracefully"
'''

CONVERGENCE_TEST = '''
def test_{function_name}_convergence():
    """Test {function_name} convergence properties."""
    # Test with known analytical solution
    x_analytical = {analytical_input}
    expected = {analytical_solution}
    
    result = {function_name}(x_analytical)
    assert np.allclose(result, expected, rtol=1e-6), \\
        f"Failed to converge to analytical solution: expected={{expected}}, got={{result}}"
    
    # Test convergence rate
    tolerances = [1e-3, 1e-6, 1e-9]
    iterations = []
    for tol in tolerances:
        iter_count = {function_name}(x_analytical, tolerance=tol).iterations
        iterations.append(iter_count)
    
    # Should converge faster with looser tolerance
    assert iterations[0] <= iterations[1] <= iterations[2], \\
        "Convergence rate not monotonic with tolerance"
'''

# DataFrame and Data Structure Templates
DATAFRAME_STRUCTURE_TEST = '''
def test_{function_name}_dataframe_structure():
    """Test {function_name} maintains proper MultiIndex structure."""
    # Arrange
    input_df = create_test_dataframe()
    
    # Act
    result = {function_name}(input_df)
    
    # Assert DataFrame structure
    assert isinstance(result, pd.DataFrame), "Result must be DataFrame"
    assert isinstance(result.columns, pd.MultiIndex), "Must maintain MultiIndex columns"
    assert result.columns.nlevels == 3, "Must have 3-level MultiIndex (M, C, S)"
    assert list(result.columns.names) == ['M', 'C', 'S'], \\
        "Column level names must be ['M', 'C', 'S']"
    
    # Assert index properties
    assert isinstance(result.index, pd.DatetimeIndex), "Index must be DatetimeIndex"
    assert result.index.is_monotonic_increasing, "Index must be chronological"
    assert result.index.name == 'Epoch', "Index must be named 'Epoch'"
'''

MISSING_DATA_TEST = '''
def test_{function_name}_missing_data_handling():
    """Test {function_name} properly handles missing data."""
    # Create data with NaN values
    data_with_nan = create_test_data_with_nan()
    
    result = {function_name}(data_with_nan)
    
    # Check NaN handling
    assert not (result == 0).any().any(), "Should not fill NaN with zeros"
    assert not (result == -999).any().any(), "Should not use -999 for missing data"
    
    # NaN should be preserved or handled gracefully
    nan_mask = pd.isna(data_with_nan)
    result_nan_mask = pd.isna(result)
    
    # Either preserve NaN or provide valid interpolation
    assert (nan_mask & result_nan_mask).sum().sum() >= 0, \\
        "Missing data handling must be consistent"
'''

# Performance and Integration Templates
PERFORMANCE_TEST = '''
@pytest.mark.slow
def test_{function_name}_performance():
    """Test {function_name} performance with large datasets."""
    import time
    
    # Create large test dataset
    large_data = generate_large_dataset(size=100000)
    
    # Measure execution time
    start_time = time.time()
    result = {function_name}(large_data)
    elapsed_time = time.time() - start_time
    
    # Performance assertions
    assert elapsed_time < {max_time_seconds}, \\
        f"Function too slow: {{elapsed_time:.2f}}s > {{max_time_seconds}}s"
    
    # Memory efficiency check
    import sys
    result_size = sys.getsizeof(result)
    input_size = sys.getsizeof(large_data)
    assert result_size < input_size * 2, \\
        "Result uses excessive memory compared to input"
'''

INTEGRATION_TEST = '''
def test_{function_name}_integration():
    """Test {function_name} integration with other SolarWindPy components."""
    # Create realistic plasma data
    plasma_data = create_realistic_plasma_data()
    
    # Test integration with Plasma class
    plasma = Plasma(plasma_data, 'p1', 'a')
    result = {function_name}(plasma)
    
    # Verify integration
    assert hasattr(result, 'data'), "Result should have data attribute"
    assert len(result.data) == len(plasma.data), \\
        "Result length should match input length"
    
    # Test with spacecraft data
    if hasattr(plasma, 'spacecraft'):
        spacecraft_result = {function_name}(plasma, use_spacecraft=True)
        assert spacecraft_result is not None, \\
            "Should handle spacecraft integration"
'''

# Fixture Templates
PLASMA_FIXTURE = '''
@pytest.fixture
def {fixture_name}():
    """Generate {description} plasma data for testing."""
    n_points = 1000
    times = pd.date_range('2020-01-01', periods=n_points, freq='1min')
    
    # Realistic solar wind parameters
    data = {{
        ('n', '', 'p1'): np.random.uniform(1, 10, n_points),      # cm^-3
        ('v', 'x', 'p1'): np.random.uniform(300, 800, n_points),  # km/s
        ('v', 'y', 'p1'): np.random.normal(0, 50, n_points),      # km/s  
        ('v', 'z', 'p1'): np.random.normal(0, 50, n_points),      # km/s
        ('w', '', 'p1'): np.random.uniform(10, 100, n_points),    # km/s
        ('b', 'x', ''): np.random.normal(0, 5, n_points),         # nT
        ('b', 'y', ''): np.random.normal(0, 5, n_points),         # nT
        ('b', 'z', ''): np.random.normal(0, 5, n_points),         # nT
    }}
    
    df = pd.DataFrame(data, index=times)
    df.index.name = 'Epoch'
    return df
'''

# Parametrized Test Templates
PARAMETRIZED_SPECIES_TEST = '''
@pytest.mark.parametrize("species,mass,charge", [
    ('p1', 1.67e-27, 1.602e-19),  # Proton
    ('a', 6.64e-27, 3.204e-19),   # Alpha particle  
    ('he2', 6.64e-27, 3.204e-19), # He2+
    ('o6', 2.66e-26, 9.612e-19),  # O6+
])
def test_{function_name}_multiple_species(species, mass, charge):
    """Test {function_name} with multiple ion species."""
    result = {function_name}(species, mass, charge)
    
    # Universal assertions for all species
    assert result > 0, f"Result must be positive for species {{species}}"
    assert not np.isnan(result), f"Result cannot be NaN for species {{species}}"
    
    # Species-specific checks
    if species == 'p1':
        assert 1e-28 < mass < 1e-26, "Proton mass out of range"
    elif species == 'a':
        assert mass > 6e-27, "Alpha particle mass too small"
'''


# Template Usage Guide
TEMPLATE_USAGE = '''
"""
How to Use These Templates:

1. Copy the relevant template
2. Replace placeholders with actual values:
   - {function_name}: Your function name
   - {si_input}, {cgs_input}: Input values in different units
   - {conversion_factor}: Expected unit conversion ratio
   - {analytical_solution}: Known analytical result
   - {max_time_seconds}: Performance threshold

3. Customize for your specific physics:
   - Add domain-specific assertions
   - Include relevant physical constants
   - Test edge cases specific to your calculation

4. Example usage:
   - For thermal speed: replace {k_constant} with k_B
   - For Alfvén speed: ensure B, density, mass parameters match
   - For conservation: define initial_state and conservation functions

5. Best practices:
   - Always test both normal and edge cases
   - Include physics-specific validation
   - Test numerical stability and convergence
   - Verify unit consistency across calculations
"""
'''
