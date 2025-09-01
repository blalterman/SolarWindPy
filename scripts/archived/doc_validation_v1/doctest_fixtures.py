"""
Reusable fixtures and utilities for SolarWindPy doctest examples.

This module provides standardized data generation functions and validation
utilities to ensure consistent, physics-compliant doctest examples across
the entire codebase.
"""

import numpy as np
import pandas as pd
import warnings
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta


def create_example_plasma_data(
    epoch: Optional[pd.DatetimeIndex] = None,
    n_points: int = 10,
    seed: int = 42,
    include_alphas: bool = False,
) -> pd.DataFrame:
    """Create standardized plasma data for doctest examples

    This function provides consistent, physics-compliant data for all doctest
    examples, ensuring reproducible results and proper MultiIndex structure.
    All data follows SolarWindPy conventions:
    - SI units for calculations, conventional units for display
    - mw² = 2kT thermal speed convention
    - MultiIndex columns with ('M', 'C', 'S') levels
    - 'Epoch' index name for time series

    Parameters
    ----------
    epoch : pd.DatetimeIndex, optional
        Time index for data. If None, creates default 10-minute series.
    n_points : int, optional
        Number of data points to generate (default: 10).
    seed : int, optional
        Random seed for reproducible results (default: 42).
    include_alphas : bool, optional
        Whether to include alpha particle data (default: False).

    Returns
    -------
    pd.DataFrame
        MultiIndex DataFrame with (M, C, S) structure containing
        proton (and optionally alpha) density, velocity, thermal speeds,
        temperature, and magnetic field data.

    Examples
    --------
    >>> data = create_example_plasma_data()
    >>> data.shape
    (10, 8)
    >>> list(data.columns.names)
    ['M', 'C', 'S']
    >>> 'p1' in data.columns.get_level_values('S')
    True
    >>> data.index.name
    'Epoch'

    >>> # Test physics compliance
    >>> T_p = data.xs(('T', '', 'p1'), axis=1).iloc[0]
    >>> w_par = data.xs(('w', 'par', 'p1'), axis=1).iloc[0]
    >>> k_B, m_p = 1.380649e-23, 1.67262192e-27
    >>> expected_w = np.sqrt(2 * k_B * T_p / m_p) / 1000
    >>> abs(w_par - expected_w) / expected_w < 0.01
    True
    """
    if epoch is None:
        epoch = pd.date_range("2023-01-01", periods=n_points, freq="1min", name="Epoch")

    n_points = len(epoch)
    np.random.seed(seed)

    # Suppress performance warnings for cleaner doctest output
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

        # Physics constants
        k_B = 1.380649e-23  # Boltzmann constant [J/K]
        m_p = 1.67262192e-27  # Proton mass [kg]
        m_a = 6.64465775e-27  # Alpha mass [kg]

        # Generate physics-compliant synthetic data

        # Proton data
        n_p = np.maximum(np.random.normal(5.0, 1.0, n_points), 0.1)  # [cm^-3]
        v_p = np.random.normal([400, 0, 0], [50, 20, 20], (n_points, 3))  # [km/s]
        T_p = np.maximum(np.random.normal(1e5, 2e4, n_points), 1e4)  # [K]

        # Calculate thermal speeds using mw² = 2kT convention
        w_par_p = np.sqrt(2 * k_B * T_p / m_p) / 1000  # [km/s]
        w_per_p = w_par_p * np.random.normal(1.0, 0.05, n_points)  # Slight anisotropy

        # Magnetic field data
        b_field = np.random.normal([5, -2, 3], [1, 0.5, 0.5], (n_points, 3))  # [nT]

        # Base column structure for protons
        columns_list = [
            ("n", "", "p1"),  # Proton density
            ("v", "x", "p1"),  # Proton velocity components
            ("v", "y", "p1"),
            ("v", "z", "p1"),
            ("w", "par", "p1"),  # Proton thermal speeds
            ("w", "per", "p1"),
            ("T", "", "p1"),  # Proton temperature
            ("b", "x", ""),  # Magnetic field components
            ("b", "y", ""),
            ("b", "z", ""),
        ]

        data_dict = {
            ("n", "", "p1"): n_p,
            ("v", "x", "p1"): v_p[:, 0],
            ("v", "y", "p1"): v_p[:, 1],
            ("v", "z", "p1"): v_p[:, 2],
            ("w", "par", "p1"): w_par_p,
            ("w", "per", "p1"): w_per_p,
            ("T", "", "p1"): T_p,
            ("b", "x", ""): b_field[:, 0],
            ("b", "y", ""): b_field[:, 1],
            ("b", "z", ""): b_field[:, 2],
        }

        # Add alpha particle data if requested
        if include_alphas:
            n_a = np.maximum(np.random.normal(0.2, 0.05, n_points), 0.01)  # [cm^-3]
            v_a = v_p + np.random.normal([0, 0, 0], [10, 5, 5], (n_points, 3))  # [km/s]
            T_a = np.maximum(
                np.random.normal(4 * T_p, T_p, n_points), 1e4
            )  # [K] - typically hotter

            # Alpha thermal speeds
            w_par_a = np.sqrt(2 * k_B * T_a / m_a) / 1000  # [km/s]
            w_per_a = w_par_a * np.random.normal(1.0, 0.05, n_points)

            # Add alpha columns
            alpha_columns = [
                ("n", "", "a"),
                ("v", "x", "a"),
                ("v", "y", "a"),
                ("v", "z", "a"),
                ("w", "par", "a"),
                ("w", "per", "a"),
                ("T", "", "a"),
            ]
            columns_list.extend(alpha_columns)

            alpha_data = {
                ("n", "", "a"): n_a,
                ("v", "x", "a"): v_a[:, 0],
                ("v", "y", "a"): v_a[:, 1],
                ("v", "z", "a"): v_a[:, 2],
                ("w", "par", "a"): w_par_a,
                ("w", "per", "a"): w_per_a,
                ("T", "", "a"): T_a,
            }
            data_dict.update(alpha_data)

        # Create MultiIndex columns
        columns = pd.MultiIndex.from_tuples(columns_list, names=["M", "C", "S"])

        # Create DataFrame
        data = pd.DataFrame(data_dict, index=epoch, columns=columns)

        return data


def create_example_ion_data(
    species: str = "p1",
    epoch: Optional[pd.DatetimeIndex] = None,
    n_points: int = 10,
    seed: int = 42,
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
    seed : int, optional
        Random seed for reproducible results

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
    >>> ion_data.columns.names
    ['M', 'C']
    """
    if epoch is None:
        epoch = pd.date_range("2023-01-01", periods=n_points, freq="1min", name="Epoch")

    # Generate full plasma data including requested species
    include_alphas = species == "a"
    full_data = create_example_plasma_data(epoch, n_points, seed, include_alphas)

    # Extract species-specific data
    try:
        species_data = full_data.xs(species, level="S", axis=1)
        return species_data
    except KeyError:
        raise ValueError(
            f"Species '{species}' not found in generated data. "
            f"Available species: {list(full_data.columns.get_level_values('S').unique())}"
        )


def create_example_magnetic_field(
    epoch: Optional[pd.DatetimeIndex] = None,
    n_points: int = 10,
    seed: int = 42,
    field_type: str = "parker_spiral",
) -> pd.DataFrame:
    """Create example magnetic field data with realistic solar wind characteristics

    Parameters
    ----------
    epoch : pd.DatetimeIndex, optional
        Time index for data
    n_points : int, optional
        Number of data points
    seed : int, optional
        Random seed for reproducible results
    field_type : str, optional
        Type of magnetic field ('parker_spiral', 'random', 'constant')

    Returns
    -------
    pd.DataFrame
        Magnetic field data with MultiIndex structure

    Examples
    --------
    >>> b_data = create_example_magnetic_field()
    >>> b_data.shape
    (10, 3)
    >>> list(b_data.columns.get_level_values('M').unique())
    ['b']
    >>> b_magnitude = np.sqrt((b_data**2).sum(axis=1))
    >>> (b_magnitude > 0).all()
    True
    """
    if epoch is None:
        epoch = pd.date_range("2023-01-01", periods=n_points, freq="1min", name="Epoch")

    np.random.seed(seed)
    n_points = len(epoch)

    if field_type == "parker_spiral":
        # Realistic Parker spiral configuration
        # Approximate 45-degree spiral in ecliptic plane
        B_r = np.random.normal(2, 0.5, n_points)  # Radial component [nT]
        B_t = np.random.normal(-3, 1, n_points)  # Tangential component [nT]
        B_n = np.random.normal(0, 1, n_points)  # Normal component [nT]

        b_field = np.column_stack([B_r, B_t, B_n])

    elif field_type == "constant":
        # Constant field with small variations
        B_0 = np.array([3, -4, 1])  # Base field [nT]
        b_field = np.tile(B_0, (n_points, 1)) + np.random.normal(0, 0.2, (n_points, 3))

    else:  # random
        # Random field with realistic magnitudes
        b_field = np.random.normal([2, -2, 1], [2, 2, 1], (n_points, 3))

    # Create MultiIndex DataFrame
    columns = pd.MultiIndex.from_tuples(
        [
            ("b", "x", ""),
            ("b", "y", ""),
            ("b", "z", ""),
        ],
        names=["M", "C", "S"],
    )

    data = pd.DataFrame(
        {
            ("b", "x", ""): b_field[:, 0],
            ("b", "y", ""): b_field[:, 1],
            ("b", "z", ""): b_field[:, 2],
        },
        index=epoch,
        columns=columns,
    )

    return data


def create_test_plasma_object(
    epoch: Optional[pd.DatetimeIndex] = None,
    n_points: int = 10,
    seed: int = 42,
    include_alphas: bool = False,
):
    """Create example Plasma object for doctest examples

    Parameters
    ----------
    epoch : pd.DatetimeIndex, optional
        Time index for data
    n_points : int, optional
        Number of data points
    seed : int, optional
        Random seed for reproducible results
    include_alphas : bool, optional
        Whether to include alpha particles

    Returns
    -------
    swp.Plasma
        Plasma object with example data

    Examples
    --------
    >>> plasma = create_test_plasma_object()
    >>> hasattr(plasma, 'p1')
    True
    >>> plasma.p1.n.iloc[0] > 0
    True
    """
    try:
        import solarwindpy as swp

        data = create_example_plasma_data(epoch, n_points, seed, include_alphas)

        # Determine species list
        species = ["p1"]
        if include_alphas:
            species.append("a")

        plasma = swp.Plasma(data, species)
        return plasma

    except ImportError:
        raise ImportError("SolarWindPy not available for Plasma object creation")


def generate_physics_compliant_values(
    measurement_type: str, n_points: int = 10, seed: int = 42
) -> np.ndarray:
    """Generate physics-compliant values for specific measurement types

    Parameters
    ----------
    measurement_type : str
        Type of measurement ('density', 'velocity', 'temperature', 'thermal_speed', 'magnetic_field')
    n_points : int, optional
        Number of values to generate
    seed : int, optional
        Random seed for reproducibility

    Returns
    -------
    np.ndarray
        Array of physics-compliant values

    Examples
    --------
    >>> density = generate_physics_compliant_values('density', 5)
    >>> len(density)
    5
    >>> (density > 0).all()
    True
    >>> velocity = generate_physics_compliant_values('velocity', 3)
    >>> (200 <= velocity).all() and (velocity <= 800).all()
    True
    """
    np.random.seed(seed)

    if measurement_type == "density":
        # Typical solar wind proton density [cm^-3]
        values = np.maximum(np.random.normal(5.0, 2.0, n_points), 0.1)

    elif measurement_type == "velocity":
        # Solar wind bulk velocity [km/s]
        values = np.maximum(np.random.normal(400, 100, n_points), 200)

    elif measurement_type == "temperature":
        # Proton temperature [K]
        values = np.maximum(np.random.normal(1e5, 5e4, n_points), 1e4)

    elif measurement_type == "thermal_speed":
        # First generate temperature, then calculate thermal speed
        T_p = np.maximum(np.random.normal(1e5, 5e4, n_points), 1e4)
        k_B = 1.380649e-23  # [J/K]
        m_p = 1.67262192e-27  # [kg]
        values = np.sqrt(2 * k_B * T_p / m_p) / 1000  # [km/s]

    elif measurement_type == "magnetic_field":
        # Magnetic field magnitude [nT]
        values = np.maximum(np.random.normal(5.0, 2.0, n_points), 0.1)

    else:
        raise ValueError(f"Unknown measurement type: {measurement_type}")

    return values


def validate_physics_relationships(
    data: pd.DataFrame, tolerance: float = 0.05
) -> Dict[str, bool]:
    """Validate physics relationships in plasma data

    Parameters
    ----------
    data : pd.DataFrame
        Plasma data with MultiIndex structure
    tolerance : float, optional
        Relative tolerance for validation (default: 5%)

    Returns
    -------
    Dict[str, bool]
        Dictionary of validation results for different physics relationships

    Examples
    --------
    >>> data = create_example_plasma_data()
    >>> results = validate_physics_relationships(data)
    >>> results['thermal_speed_consistency']
    True
    >>> results['positive_quantities']
    True
    """
    results = {}

    try:
        # Check thermal speed consistency (mw² = 2kT)
        if ("T", "", "p1") in data.columns and ("w", "par", "p1") in data.columns:
            T_p = data.xs(("T", "", "p1"), axis=1)
            w_par = data.xs(("w", "par", "p1"), axis=1)

            k_B = 1.380649e-23
            m_p = 1.67262192e-27
            expected_w = np.sqrt(2 * k_B * T_p / m_p) / 1000

            relative_error = np.abs((w_par - expected_w) / expected_w)
            results["thermal_speed_consistency"] = (relative_error < tolerance).all()
        else:
            results["thermal_speed_consistency"] = True  # No data to validate

        # Check positive quantities
        positive_quantities = []
        for col in data.columns:
            if col[0] in ["n", "T"]:  # Density and temperature must be positive
                positive_quantities.append((data[col] > 0).all())

        results["positive_quantities"] = (
            all(positive_quantities) if positive_quantities else True
        )

        # Check velocity ranges (basic sanity check)
        velocity_reasonable = True
        for component in ["x", "y", "z"]:
            if ("v", component, "p1") in data.columns:
                v_comp = data.xs(("v", component, "p1"), axis=1)
                # Solar wind velocities typically 200-800 km/s for bulk flow
                if component == "x":  # Bulk flow component
                    velocity_reasonable &= (200 <= v_comp).all() and (
                        v_comp <= 800
                    ).all()
                else:  # Perpendicular components
                    velocity_reasonable &= (-200 <= v_comp).all() and (
                        v_comp <= 200
                    ).all()

        results["velocity_ranges"] = velocity_reasonable

    except Exception as e:
        # If validation fails, log the issue but don't crash
        results["validation_error"] = str(e)
        results["thermal_speed_consistency"] = False
        results["positive_quantities"] = False
        results["velocity_ranges"] = False

    return results


def create_doctest_summary_report() -> Dict[str, Any]:
    """Create summary report of available doctest fixtures and utilities

    Returns
    -------
    Dict[str, Any]
        Summary of available functions and their capabilities

    Examples
    --------
    >>> report = create_doctest_summary_report()
    >>> 'data_generators' in report
    True
    >>> len(report['data_generators']) >= 3
    True
    """
    return {
        "data_generators": [
            "create_example_plasma_data",
            "create_example_ion_data",
            "create_example_magnetic_field",
            "create_test_plasma_object",
            "generate_physics_compliant_values",
        ],
        "validation_functions": ["validate_physics_relationships"],
        "physics_constants": {
            "k_B": 1.380649e-23,  # Boltzmann constant [J/K]
            "m_p": 1.67262192e-27,  # Proton mass [kg]
            "m_a": 6.64465775e-27,  # Alpha mass [kg]
            "mu_0": 4 * np.pi * 1e-7,  # Permeability [H/m]
        },
        "conventions": [
            "mw² = 2kT thermal speed formula",
            "SI units for calculations",
            "MultiIndex (M, C, S) structure",
            "Epoch index name for time series",
            "NaN for missing data",
        ],
    }
