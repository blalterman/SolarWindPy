#!/usr/bin/env python3
"""SolarWindPy Test Generator Interactive test scaffolding for domain-specific
scientific testing."""

import sys
from pathlib import Path
from textwrap import dedent


def get_function_info():
    """Get function information from user."""

    print("🧪 SolarWindPy Test Generator")
    print("=" * 40)

    function_name = input("Function name to test: ").strip()
    if not function_name:
        print("❌ Function name required")
        sys.exit(1)

    module_path = input("Module path (e.g., solarwindpy.core.plasma): ").strip()
    if not module_path:
        print("❌ Module path required")
        sys.exit(1)

    return function_name, module_path


def select_test_types():
    """Let user select which types of tests to generate."""

    test_types = {
        "1": ("Physics Validation", "physics"),
        "2": ("Numerical Stability", "numerical"),
        "3": ("Unit Consistency", "units"),
        "4": ("DataFrame Structure", "dataframe"),
        "5": ("Performance", "performance"),
        "6": ("Integration", "integration"),
        "7": ("Conservation Laws", "conservation"),
        "8": ("Missing Data Handling", "missing_data"),
    }

    print("\nSelect test types (comma-separated numbers):")
    for key, (name, _) in test_types.items():
        print(f"  {key}. {name}")

    selection = input("\nYour selection (e.g., 1,2,4): ").strip()

    if not selection:
        return ["physics", "numerical"]  # Default

    selected = []
    for num in selection.split(","):
        num = num.strip()
        if num in test_types:
            selected.append(test_types[num][1])

    return selected if selected else ["physics", "numerical"]


def get_physics_details(function_name):
    """Get physics-specific details for the function."""

    print(f"\nPhysics details for {function_name}:")

    # Detect common physics functions
    physics_type = None
    if "thermal" in function_name.lower() or "temperature" in function_name.lower():
        physics_type = "thermal"
    elif "alfven" in function_name.lower() or "magnetic" in function_name.lower():
        physics_type = "alfven"
    elif "coulomb" in function_name.lower():
        physics_type = "coulomb"
    elif "beta" in function_name.lower():
        physics_type = "beta"

    if physics_type:
        print(f"Detected physics type: {physics_type}")
        use_detection = input("Use detected physics type? (y/n): ").strip().lower()
        if use_detection == "y":
            return physics_type

    # Manual selection
    physics_options = {
        "1": "thermal",
        "2": "alfven",
        "3": "coulomb",
        "4": "beta",
        "5": "instability",
        "6": "general",
    }

    print("\nPhysics type:")
    for key, value in physics_options.items():
        print(f"  {key}. {value}")

    choice = input("Select physics type: ").strip()
    return physics_options.get(choice, "general")


def generate_physics_test(function_name, physics_type):
    """Generate physics-specific test."""

    if physics_type == "thermal":
        return dedent(
            f'''
        def test_{function_name}_thermal_speed_convention():
            """Test {function_name} follows mw² = 2kT convention."""
            from solarwindpy.tools import units_constants as uc

            # Arrange
            temperature = 1e5  # K
            mass = uc.proton_mass  # kg
            expected = np.sqrt(2 * uc.k_B * temperature / mass)

            # Act
            result = {function_name}(temperature, mass)

            # Assert
            assert np.isclose(result, expected, rtol=1e-6), \\
                f"Thermal speed convention violated: expected={{expected}}, got={{result}}"
            assert result > 0, "Thermal speed must be positive"
            assert result < uc.c, "Thermal speed cannot exceed speed of light"
        '''
        ).strip()

    elif physics_type == "alfven":
        return dedent(
            f'''
        def test_{function_name}_alfven_speed_formula():
            """Test {function_name} follows V_A = B/√(μ₀ρ) formula."""
            from solarwindpy.tools import units_constants as uc

            # Arrange
            B = 5e-9  # Tesla (typical solar wind)
            density = 5e6  # m^-3
            mass = uc.proton_mass  # kg
            rho = density * mass
            expected = B / np.sqrt(uc.mu_0 * rho)

            # Act
            result = {function_name}(B, density, mass)

            # Assert
            assert np.isclose(result, expected, rtol=1e-6), \\
                f"Alfvén speed formula violated: expected={{expected}}, got={{result}}"
            assert result > 0, "Alfvén speed must be positive"
            assert result < uc.c, "Alfvén speed cannot exceed speed of light"
        '''
        ).strip()

    elif physics_type == "beta":
        return dedent(
            f'''
        def test_{function_name}_plasma_beta_calculation():
            """Test {function_name} plasma beta calculation β = 2μ₀nkT/B²."""
            from solarwindpy.tools import units_constants as uc

            # Arrange
            density = 5e6  # m^-3
            temperature = 1e5  # K
            B = 5e-9  # Tesla
            expected = (2 * uc.mu_0 * density * uc.k_B * temperature) / (B**2)

            # Act
            result = {function_name}(density, temperature, B)

            # Assert
            assert np.isclose(result, expected, rtol=1e-6), \\
                f"Plasma beta formula violated: expected={{expected}}, got={{result}}"
            assert result > 0, "Plasma beta must be positive"
        '''
        ).strip()

    else:
        return dedent(
            f'''
        def test_{function_name}_physics_constraints():
            """Test {function_name} respects physical constraints."""
            # TODO: Add physics-specific tests for {function_name}
            # Consider: conservation laws, physical bounds, unit consistency

            # Arrange
            # Add realistic input parameters

            # Act
            result = {function_name}(input_params)

            # Assert
            assert result is not None, "Function must return a result"
            assert np.isfinite(result).all(), "Result must be finite"
            # Add physics-specific assertions
        '''
        ).strip()


def generate_numerical_test(function_name):
    """Generate numerical stability test."""

    return dedent(
        f'''
    def test_{function_name}_numerical_stability():
        """Test {function_name} numerical stability at boundaries."""
        # Test very small values (approach zero)
        small_input = 1e-15
        small_result = {function_name}(small_input)
        assert np.isfinite(small_result), "Function unstable at small values"

        # Test very large values
        large_input = 1e15
        large_result = {function_name}(large_input)
        assert np.isfinite(large_result), "Function unstable at large values"

        # Test edge case: exactly zero (if applicable)
        try:
            zero_result = {function_name}(0.0)
            assert np.isfinite(zero_result) or np.isnan(zero_result), \\
                "Function should handle zero gracefully"
        except (ZeroDivisionError, ValueError):
            pass  # Expected for some functions
    '''
    ).strip()


def generate_dataframe_test(function_name):
    """Generate DataFrame structure test."""

    return dedent(
        f'''
    def test_{function_name}_dataframe_structure():
        """Test {function_name} maintains proper MultiIndex DataFrame structure."""
        # Arrange
        test_data = create_test_plasma_dataframe()

        # Act
        result = {function_name}(test_data)

        # Assert DataFrame structure
        assert isinstance(result, pd.DataFrame), "Result must be DataFrame"
        assert isinstance(result.columns, pd.MultiIndex), "Must maintain MultiIndex columns"
        assert result.columns.nlevels == 3, "Must have 3-level MultiIndex (M, C, S)"
        assert list(result.columns.names) == ['M', 'C', 'S'], \\
            "Column level names must be ['M', 'C', 'S']"

        # Assert index properties
        assert isinstance(result.index, pd.DatetimeIndex), "Index must be DatetimeIndex"
        assert result.index.name == 'Epoch', "Index must be named 'Epoch'"

        # Assert no data corruption
        assert len(result) > 0, "Result cannot be empty"
        assert not result.isna().all().all(), "Result cannot be all NaN"
    '''
    ).strip()


def create_test_file(function_name, module_path, test_types, physics_type):
    """Create the complete test file."""

    # Extract module components
    module_parts = module_path.split(".")
    if len(module_parts) >= 2:
        submodule = module_parts[-1]  # e.g., 'plasma' from 'solarwindpy.core.plasma'
    else:
        submodule = "module"

    # Create test file path
    test_dir = Path("tests")
    if "core" in module_path:
        test_dir = test_dir / "core"
    elif "fitfunctions" in module_path:
        test_dir = test_dir / "fitfunctions"
    elif "plotting" in module_path:
        test_dir = test_dir / "plotting"
    elif "instabilities" in module_path:
        test_dir = test_dir / "instabilities"

    test_file = test_dir / f"test_{submodule}.py"

    # Generate imports
    imports = dedent(
        f'''
    """
    Tests for {module_path}.{function_name}
    Generated by SolarWindPy Test Generator
    """

    import numpy as np
    import pandas as pd
    import pytest
    from {module_path} import {function_name}


    '''
    ).strip()

    # Generate helper functions
    helpers = dedent(
        '''
    def create_test_plasma_dataframe():
        """Create test DataFrame with proper MultiIndex structure."""
        n_points = 100
        times = pd.date_range('2020-01-01', periods=n_points, freq='1min')

        data = {
            ('n', '', 'p1'): np.random.uniform(1, 10, n_points),
            ('v', 'x', 'p1'): np.random.uniform(300, 800, n_points),
            ('v', 'y', 'p1'): np.random.normal(0, 50, n_points),
            ('v', 'z', 'p1'): np.random.normal(0, 50, n_points),
            ('w', '', 'p1'): np.random.uniform(10, 100, n_points),
            ('b', 'x', ''): np.random.normal(0, 5, n_points),
            ('b', 'y', ''): np.random.normal(0, 5, n_points),
            ('b', 'z', ''): np.random.normal(0, 5, n_points),
        }

        df = pd.DataFrame(data, index=times)
        df.index.name = 'Epoch'
        return df


    '''
    ).strip()

    # Generate tests
    tests = []

    if "physics" in test_types:
        tests.append(generate_physics_test(function_name, physics_type))

    if "numerical" in test_types:
        tests.append(generate_numerical_test(function_name))

    if "dataframe" in test_types:
        tests.append(generate_dataframe_test(function_name))

    # Combine all parts
    test_content = f"{imports}\n\n{helpers}\n\n" + "\n\n".join(tests)

    return test_file, test_content


def main():
    """Main test generator function."""

    try:
        # Get user input
        function_name, module_path = get_function_info()
        test_types = select_test_types()

        physics_type = "general"
        if "physics" in test_types:
            physics_type = get_physics_details(function_name)

        # Generate test file
        test_file, test_content = create_test_file(
            function_name, module_path, test_types, physics_type
        )

        # Create directory if needed
        test_file.parent.mkdir(parents=True, exist_ok=True)

        # Write or append to test file
        if test_file.exists():
            print(f"\n📝 Test file exists: {test_file}")
            append = input("Append to existing file? (y/n): ").strip().lower()
            if append == "y":
                with open(test_file, "a") as f:
                    f.write(f"\n\n# Additional tests for {function_name}\n")
                    f.write(
                        test_content.split("\n\n", 2)[-1]
                    )  # Skip imports and helpers
            else:
                print("❌ Operation cancelled")
                sys.exit(1)
        else:
            with open(test_file, "w") as f:
                f.write(test_content)

        print(f"\n✅ Test file generated: {test_file}")
        print(f"📋 Test types: {', '.join(test_types)}")
        print(f"🔬 Physics type: {physics_type}")

        # Suggest next steps
        print("\n💡 Next steps:")
        print("   1. Review and customize the generated tests")
        print(f"   2. Run tests: pytest {test_file}")
        print("   3. Add to your test suite")

    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
