"""
Enhanced pytest configuration for doctest execution with physics validation.

This module provides comprehensive doctest setup including automated fixture
injection, physics rule validation, and standardized test data generation.
"""

import pytest
import numpy as np
import pandas as pd
import solarwindpy as swp
from typing import Dict, Any, Optional
import warnings


@pytest.fixture(autouse=True)
def doctest_namespace(doctest_namespace):
    """Automatically inject common imports and fixtures into doctest namespace

    This fixture ensures all doctests have access to:
    - Standard libraries (numpy, pandas)
    - SolarWindPy package and utilities
    - Physics-compliant example data generators
    - Common constants and validation functions

    Parameters
    ----------
    doctest_namespace : dict
        Pytest doctest namespace to populate

    Returns
    -------
    dict
        Enhanced namespace with all required imports and data
    """
    # Standard imports available in all doctests
    doctest_namespace["np"] = np
    doctest_namespace["pd"] = pd
    doctest_namespace["swp"] = swp

    # Suppress pandas warnings for cleaner doctest output
    warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

    # Example data generators
    doctest_namespace["create_example_plasma_data"] = create_example_plasma_data
    doctest_namespace["create_example_ion_data"] = create_example_ion_data
    doctest_namespace["validate_doctest_output"] = validate_doctest_output

    # Common test data - reproducible for consistent doctests
    np.random.seed(42)
    epoch = pd.date_range("2023-01-01", periods=10, freq="1min", name="Epoch")
    doctest_namespace["epoch"] = epoch
    doctest_namespace["data"] = create_example_plasma_data(epoch)

    # Physics constants from solarwindpy.core.units_constants
    try:
        from solarwindpy.core.units_constants import Constants

        const = Constants()
        doctest_namespace["k_B"] = const.kb  # Boltzmann constant [J/K]
        doctest_namespace["m_p"] = const.m["p1"]  # Proton mass [kg]
        doctest_namespace["m_a"] = const.m.get("a", 6.64465775e-27)  # Alpha mass [kg]
        doctest_namespace["mu_0"] = 4 * np.pi * 1e-7  # Permeability [H/m]
    except ImportError:
        # Fallback constants if imports fail
        doctest_namespace["k_B"] = 1.380649e-23
        doctest_namespace["m_p"] = 1.67262192e-27
        doctest_namespace["m_a"] = 6.64465775e-27
        doctest_namespace["mu_0"] = 4 * np.pi * 1e-7

    return doctest_namespace


def create_example_plasma_data(
    epoch: Optional[pd.DatetimeIndex] = None, n_points: int = 10, seed: int = 42
) -> pd.DataFrame:
    """Create standardized plasma data for doctest examples

    This function provides consistent, physics-compliant data for all doctest
    examples, ensuring reproducible results and proper MultiIndex structure.

    Parameters
    ----------
    epoch : pd.DatetimeIndex, optional
        Time index for data. If None, creates default 10-minute series.
    n_points : int, optional
        Number of data points to generate (default: 10).
    seed : int, optional
        Random seed for reproducible results (default: 42).

    Returns
    -------
    pd.DataFrame
        MultiIndex DataFrame with (M, C, S) structure containing
        proton density, velocity, thermal speeds, temperature, and magnetic field.

    Examples
    --------
    >>> data = create_example_plasma_data()
    >>> data.shape
    (10, 8)
    >>> list(data.columns.names)
    ['M', 'C', 'S']
    >>> 'p1' in data.columns.get_level_values('S')
    True
    """
    if epoch is None:
        epoch = pd.date_range("2023-01-01", periods=n_points, freq="1min", name="Epoch")

    n_points = len(epoch)
    np.random.seed(seed)

    # Physics-compliant synthetic data with realistic values
    n_p = np.random.normal(5.0, 1.0, n_points)  # Proton density [cm^-3]
    n_p = np.maximum(n_p, 0.1)  # Ensure positive density

    v_p = np.random.normal([400, 0, 0], [50, 20, 20], (n_points, 3))  # Velocity [km/s]

    T_p = np.random.normal(1e5, 2e4, n_points)  # Temperature [K]
    T_p = np.maximum(T_p, 1e4)  # Ensure positive temperature

    # Calculate thermal speeds from temperature using mw² = 2kT convention
    k_B = 1.380649e-23  # Boltzmann constant [J/K]
    m_p = 1.67262192e-27  # Proton mass [kg]

    # Thermal speeds [km/s]
    w_par = np.sqrt(2 * k_B * T_p / m_p) / 1000  # Parallel thermal speed
    w_per = w_par * np.random.normal(1.0, 0.05, n_points)  # Slight anisotropy

    # Magnetic field data [nT]
    b_field = np.random.normal([5, -2, 3], [1, 0.5, 0.5], (n_points, 3))

    # Create MultiIndex DataFrame with proper structure
    columns = pd.MultiIndex.from_tuples(
        [
            ("n", "", "p1"),  # Proton density
            ("v", "x", "p1"),  # Proton velocity x
            ("v", "y", "p1"),  # Proton velocity y
            ("v", "z", "p1"),  # Proton velocity z
            ("w", "par", "p1"),  # Parallel thermal speed
            ("w", "per", "p1"),  # Perpendicular thermal speed
            ("T", "", "p1"),  # Proton temperature
            ("b", "x", ""),  # Magnetic field x
            ("b", "y", ""),  # Magnetic field y
            ("b", "z", ""),  # Magnetic field z
        ],
        names=["M", "C", "S"],
    )

    data = pd.DataFrame(
        {
            ("n", "", "p1"): n_p,
            ("v", "x", "p1"): v_p[:, 0],
            ("v", "y", "p1"): v_p[:, 1],
            ("v", "z", "p1"): v_p[:, 2],
            ("w", "par", "p1"): w_par,
            ("w", "per", "p1"): w_per,
            ("T", "", "p1"): T_p,
            ("b", "x", ""): b_field[:, 0],
            ("b", "y", ""): b_field[:, 1],
            ("b", "z", ""): b_field[:, 2],
        },
        index=epoch,
        columns=columns,
    )

    return data


def create_example_ion_data(
    species: str = "p1", epoch: Optional[pd.DatetimeIndex] = None, n_points: int = 10
) -> pd.DataFrame:
    """Create standardized ion species data for doctest examples

    Parameters
    ----------
    species : str
        Ion species identifier ('p1', 'p2', 'a', etc.)
    epoch : pd.DatetimeIndex, optional
        Time index for data
    n_points : int, optional
        Number of data points

    Returns
    -------
    pd.DataFrame
        Single-species ion data with MultiIndex structure

    Examples
    --------
    >>> ion_data = create_example_ion_data('p1')
    >>> proton_density = ion_data.xs('n', level='M')
    >>> len(proton_density)
    10
    >>> proton_density.iloc[0] > 0
    True
    """
    if epoch is None:
        epoch = pd.date_range("2023-01-01", periods=n_points, freq="1min", name="Epoch")

    full_data = create_example_plasma_data(epoch, n_points)

    # Extract species-specific data
    species_data = full_data.xs(species, level="S", axis=1)

    return species_data


class DoctestPhysicsValidator:
    """Validate physics rules in doctest outputs

    This class provides validation methods to ensure doctest outputs
    follow established physics conventions and data structure rules.
    """

    def __init__(self):
        self.violations = []

    def validate_thermal_speed(
        self,
        thermal_speed: float,
        temperature: float,
        mass: float = 1.67262192e-27,
        tolerance: float = 0.01,
    ) -> bool:
        """Validate thermal speed follows mw² = 2kT convention

        Parameters
        ----------
        thermal_speed : float
            Calculated thermal speed [km/s]
        temperature : float
            Temperature [K]
        mass : float
            Particle mass [kg] (default: proton mass)
        tolerance : float
            Relative tolerance for validation (default: 1%)

        Returns
        -------
        bool
            True if thermal speed is within tolerance
        """
        k_B = 1.380649e-23
        expected = np.sqrt(2 * k_B * temperature / mass) / 1000  # km/s

        relative_error = abs(thermal_speed - expected) / expected

        if relative_error > tolerance:
            self.violations.append(
                f"Thermal speed violation: expected {expected:.2f} km/s, "
                f"got {thermal_speed:.2f} km/s (error: {relative_error*100:.1f}%)"
            )
            return False

        return True

    def validate_multiindex_structure(self, dataframe: pd.DataFrame) -> bool:
        """Validate MultiIndex DataFrame structure

        Parameters
        ----------
        dataframe : pd.DataFrame
            DataFrame to validate

        Returns
        -------
        bool
            True if structure is compliant
        """
        if not isinstance(dataframe.columns, pd.MultiIndex):
            self.violations.append("DataFrame must have MultiIndex columns")
            return False

        if list(dataframe.columns.names) != ["M", "C", "S"]:
            self.violations.append(
                f"MultiIndex levels must be ['M', 'C', 'S'], "
                f"got {list(dataframe.columns.names)}"
            )
            return False

        if hasattr(dataframe.index, "name") and dataframe.index.name != "Epoch":
            self.violations.append(
                f"Time series index must be named 'Epoch', "
                f"got '{dataframe.index.name}'"
            )
            return False

        return True

    def validate_units(
        self, value: float, unit_type: str, expected_range: tuple = None
    ) -> bool:
        """Validate physical units and ranges

        Parameters
        ----------
        value : float
            Value to validate
        unit_type : str
            Type of unit ('density', 'velocity', 'temperature', 'magnetic_field')
        expected_range : tuple, optional
            (min, max) expected range for the value

        Returns
        -------
        bool
            True if value is within expected range
        """
        ranges = {
            "density": (0.01, 100),  # cm^-3
            "velocity": (200, 800),  # km/s
            "temperature": (1e4, 1e7),  # K
            "magnetic_field": (0.1, 50),  # nT
        }

        if unit_type in ranges:
            min_val, max_val = ranges[unit_type]
            if expected_range:
                min_val, max_val = expected_range

            if not (min_val <= value <= max_val):
                self.violations.append(
                    f"{unit_type} value {value} outside expected range "
                    f"[{min_val}, {max_val}]"
                )
                return False

        return True


def validate_doctest_output(
    output: Any,
    expected_type: type = None,
    physics_rules: bool = True,
    tolerance: float = 0.01,
) -> bool:
    """Validate doctest outputs against physics and structure rules

    Parameters
    ----------
    output : any
        Output from doctest execution
    expected_type : type, optional
        Expected type for output validation
    physics_rules : bool
        Whether to apply physics rule validation (default: True)
    tolerance : float
        Tolerance for numerical comparisons (default: 1%)

    Returns
    -------
    bool
        True if output passes all validation checks

    Examples
    --------
    >>> data = create_example_plasma_data()
    >>> validate_doctest_output(data, pd.DataFrame)
    True
    >>> validate_doctest_output(42, int)
    True
    """
    validator = DoctestPhysicsValidator()

    # Type validation
    if expected_type and not isinstance(output, expected_type):
        return False

    # Physics validation
    if physics_rules:
        if isinstance(output, pd.DataFrame) and hasattr(output, "columns"):
            validator.validate_multiindex_structure(output)

        # Add thermal speed validation if applicable
        if hasattr(output, "name") and "thermal_speed" in str(output.name):
            # Extract temperature context for validation
            pass  # Implementation depends on specific use case

    return len(validator.violations) == 0


# Configure pytest to use enhanced doctest features
def pytest_configure(config):
    """Configure pytest with enhanced doctest capabilities

    Parameters
    ----------
    config : pytest.Config
        Pytest configuration object
    """
    # Enable doctest modules and detailed reporting
    config.option.doctestmodules = True
    config.option.doctest_report_ndiff = True

    # Set doctest options for better error reporting
    import doctest

    config.option.doctest_optionflags = (
        doctest.ELLIPSIS
        | doctest.NORMALIZE_WHITESPACE
        | doctest.IGNORE_EXCEPTION_DETAIL
    )


# Pytest plugins configuration
pytest_plugins = ["doctest"]
