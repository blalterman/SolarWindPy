#!/usr/bin/env python3
"""
Physics constraint validation for code examples.

This module validates that code examples follow established physics rules:
- Thermal speed convention: mw² = 2kT
- SI units for internal calculations  
- NaN for missing data (not 0 or -999)
- Physically reasonable outputs
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import warnings


@dataclass
class PhysicsViolation:
    """Represents a violation of physics rules."""

    rule: str
    message: str
    severity: str  # 'error', 'warning', 'info'
    expected: Optional[Union[float, str]] = None
    actual: Optional[Union[float, str]] = None
    tolerance: Optional[float] = None


class PhysicsConstants:
    """Physics constants for validation."""

    k_B = 1.380649e-23  # Boltzmann constant [J/K]
    m_p = 1.67262192e-27  # Proton mass [kg]
    m_e = 9.1093837015e-31  # Electron mass [kg]
    mu_0 = 4 * np.pi * 1e-7  # Permeability of free space [H/m]

    # Species masses (in kg)
    species_masses = {
        "p1": m_p,  # Protons
        "p2": m_p,  # Secondary protons
        "a": 4 * m_p,  # Alpha particles (He++)
        "he": 4 * m_p,  # Helium
        "e": m_e,  # Electrons
    }


class ThermalSpeedValidator:
    """Validate thermal speed calculations follow mw² = 2kT convention."""

    def __init__(self, tolerance: float = 0.05):
        self.tolerance = tolerance  # 5% tolerance

    def validate_thermal_speed(
        self,
        thermal_speed: Union[float, np.ndarray],
        temperature: Union[float, np.ndarray],
        mass: float = PhysicsConstants.m_p,
    ) -> List[PhysicsViolation]:
        """
        Validate thermal speed follows mw² = 2kT convention.

        Parameters
        ----------
        thermal_speed : float or array
            Thermal speed in m/s (SI units)
        temperature : float or array
            Temperature in K
        mass : float
            Particle mass in kg

        Returns
        -------
        List[PhysicsViolation]
            List of violations found
        """
        violations = []

        # Convert to numpy arrays for consistent handling
        w = np.atleast_1d(thermal_speed)
        T = np.atleast_1d(temperature)

        # Expected thermal speed: w = sqrt(2kT/m)
        w_expected = np.sqrt(2 * PhysicsConstants.k_B * T / mass)

        # Check relative error
        with warnings.catch_warnings():
            warnings.simplefilter(
                "ignore", RuntimeWarning
            )  # Ignore div by zero warnings
            relative_error = np.abs(w - w_expected) / w_expected

            # Find violations
            violation_mask = relative_error > self.tolerance

            if np.any(violation_mask):
                max_error = np.max(relative_error[violation_mask])
                violations.append(
                    PhysicsViolation(
                        rule="thermal_speed_convention",
                        message=f"Thermal speed violates mw² = 2kT convention",
                        severity="error",
                        expected=f"sqrt(2kT/m) = {np.mean(w_expected):.2e} m/s",
                        actual=f"{np.mean(w):.2e} m/s",
                        tolerance=max_error,
                    )
                )

        return violations

    def validate_from_plasma_data(self, data: pd.DataFrame) -> List[PhysicsViolation]:
        """Validate thermal speed in plasma DataFrame."""
        violations = []

        if not isinstance(data.columns, pd.MultiIndex):
            return violations

        try:
            # Look for thermal speed and temperature columns
            if ("w", "", "p1") in data.columns and ("T", "", "p1") in data.columns:
                thermal_speed = data[("w", "", "p1")].dropna()
                temperature = data[("T", "", "p1")].dropna()

                if len(thermal_speed) > 0 and len(temperature) > 0:
                    violations.extend(
                        self.validate_thermal_speed(
                            thermal_speed.values,
                            temperature.values,
                            PhysicsConstants.m_p,
                        )
                    )
        except KeyError:
            pass  # Thermal speed or temperature not found

        return violations


class UnitsValidator:
    """Validate unit consistency and proper SI usage."""

    def __init__(self):
        self.expected_ranges = {
            # Internal SI units (what calculations should use)
            "velocity_si": (1e2, 1e6),  # m/s (100 m/s to 1000 km/s)
            "density_si": (1e6, 1e12),  # m^-3 (converted from cm^-3)
            "temperature": (1e3, 1e7),  # K
            "magnetic_field_si": (1e-9, 1e-3),  # T (converted from nT)
            "pressure_si": (1e-12, 1e-9),  # Pa
            # Display units (what users see)
            "velocity_display": (100, 1000),  # km/s
            "density_display": (0.1, 100),  # cm^-3
            "magnetic_field_display": (0.1, 100),  # nT
        }

    def validate_units(self, data: Dict[str, Any]) -> List[PhysicsViolation]:
        """Validate that data uses appropriate units."""
        violations = []

        for var_name, value in data.items():
            if not isinstance(value, (int, float, np.ndarray, pd.Series)):
                continue

            # Convert to numpy array for consistent handling
            arr = np.atleast_1d(value)
            if len(arr) == 0:
                continue

            # Check for common unit issues
            violations.extend(self._check_velocity_units(var_name, arr))
            violations.extend(self._check_density_units(var_name, arr))
            violations.extend(self._check_magnetic_field_units(var_name, arr))

        return violations

    def _check_velocity_units(
        self, var_name: str, data: np.ndarray
    ) -> List[PhysicsViolation]:
        """Check velocity units are appropriate."""
        violations = []

        if "velocity" in var_name.lower() or "v" in var_name.lower():
            data_clean = data[~np.isnan(data)]
            if len(data_clean) == 0:
                return violations

            typical_value = np.median(data_clean)

            # If values are in m/s range but should be km/s for display
            if 1e4 < typical_value < 1e6:
                violations.append(
                    PhysicsViolation(
                        rule="velocity_units",
                        message="Velocity appears to be in m/s, consider km/s for display",
                        severity="warning",
                        expected="~400 km/s (typical solar wind)",
                        actual=f"{typical_value:.0f} m/s",
                    )
                )

            # If values are unreasonably high or low
            elif typical_value > 1e6 or typical_value < 10:
                violations.append(
                    PhysicsViolation(
                        rule="velocity_range",
                        message="Velocity outside physically reasonable range",
                        severity="error",
                        expected="100-1000 km/s",
                        actual=f"{typical_value:.2e}",
                    )
                )

        return violations

    def _check_density_units(
        self, var_name: str, data: np.ndarray
    ) -> List[PhysicsViolation]:
        """Check density units are appropriate."""
        violations = []

        if "density" in var_name.lower() or var_name.lower() == "n":
            data_clean = data[~np.isnan(data)]
            if len(data_clean) == 0:
                return violations

            typical_value = np.median(data_clean)

            # If values are in m^-3 range but should be cm^-3 for display
            if 1e6 < typical_value < 1e12:
                violations.append(
                    PhysicsViolation(
                        rule="density_units",
                        message="Density appears to be in m^-3, consider cm^-3 for display",
                        severity="warning",
                        expected="~5 cm^-3 (typical solar wind)",
                        actual=f"{typical_value:.2e} m^-3",
                    )
                )

        return violations

    def _check_magnetic_field_units(
        self, var_name: str, data: np.ndarray
    ) -> List[PhysicsViolation]:
        """Check magnetic field units are appropriate."""
        violations = []

        if "magnetic" in var_name.lower() or "b" in var_name.lower():
            data_clean = data[~np.isnan(data)]
            if len(data_clean) == 0:
                return violations

            typical_value = np.median(data_clean)

            # If values are in T range but should be nT for display
            if 1e-9 < typical_value < 1e-6:
                violations.append(
                    PhysicsViolation(
                        rule="magnetic_field_units",
                        message="Magnetic field appears to be in T, consider nT for display",
                        severity="warning",
                        expected="~5 nT (typical solar wind)",
                        actual=f"{typical_value:.2e} T",
                    )
                )

        return violations


class MissingDataValidator:
    """Validate missing data handling uses NaN appropriately."""

    def __init__(self):
        self.bad_fill_values = [0, -999, -9999, 999, 9999]

    def validate_missing_data(self, data: Dict[str, Any]) -> List[PhysicsViolation]:
        """Check that NaN is used for missing data, not fill values."""
        violations = []

        for var_name, value in data.items():
            if isinstance(value, (pd.Series, pd.DataFrame)):
                violations.extend(self._check_pandas_missing_data(var_name, value))
            elif isinstance(value, np.ndarray):
                violations.extend(self._check_numpy_missing_data(var_name, value))

        return violations

    def _check_pandas_missing_data(
        self, var_name: str, data: Union[pd.Series, pd.DataFrame]
    ) -> List[PhysicsViolation]:
        """Check pandas data for improper missing value handling."""
        violations = []

        # Check for common fill values that should be NaN
        for fill_value in self.bad_fill_values:
            if isinstance(data, pd.DataFrame):
                count = (data == fill_value).sum().sum()
            else:
                count = (data == fill_value).sum()

            if count > 0:
                violations.append(
                    PhysicsViolation(
                        rule="missing_data_handling",
                        message=f"Found {count} instances of fill value {fill_value}, should use NaN",
                        severity="warning",
                        expected="NaN",
                        actual=f"{fill_value} ({count} instances)",
                    )
                )

        return violations

    def _check_numpy_missing_data(
        self, var_name: str, data: np.ndarray
    ) -> List[PhysicsViolation]:
        """Check numpy data for improper missing value handling."""
        violations = []

        for fill_value in self.bad_fill_values:
            count = np.sum(data == fill_value)
            if count > 0:
                violations.append(
                    PhysicsViolation(
                        rule="missing_data_handling",
                        message=f"Found {count} instances of fill value {fill_value}, should use NaN",
                        severity="warning",
                        expected="NaN",
                        actual=f"{fill_value} ({count} instances)",
                    )
                )

        return violations


class MultiIndexValidator:
    """Validate MultiIndex DataFrame structure compliance."""

    def __init__(self):
        self.required_levels = ["M", "C", "S"]
        self.valid_measurements = ["n", "v", "w", "b", "T", "P"]
        self.valid_components = ["x", "y", "z", ""]
        self.valid_species = ["p1", "p2", "a", "he", "e", ""]

    def validate_multiindex_structure(
        self, data: Dict[str, Any]
    ) -> List[PhysicsViolation]:
        """Validate MultiIndex DataFrame structure."""
        violations = []

        for var_name, value in data.items():
            if isinstance(value, pd.DataFrame) and isinstance(
                value.columns, pd.MultiIndex
            ):
                violations.extend(self._check_multiindex_levels(var_name, value))
                violations.extend(self._check_multiindex_values(var_name, value))

        return violations

    def _check_multiindex_levels(
        self, var_name: str, df: pd.DataFrame
    ) -> List[PhysicsViolation]:
        """Check MultiIndex level names."""
        violations = []

        if list(df.columns.names) != self.required_levels:
            violations.append(
                PhysicsViolation(
                    rule="multiindex_levels",
                    message="MultiIndex levels must be ['M', 'C', 'S']",
                    severity="error",
                    expected="['M', 'C', 'S']",
                    actual=str(list(df.columns.names)),
                )
            )

        return violations

    def _check_multiindex_values(
        self, var_name: str, df: pd.DataFrame
    ) -> List[PhysicsViolation]:
        """Check MultiIndex level values."""
        violations = []

        if "M" in df.columns.names:
            measurements = df.columns.get_level_values("M").unique()
            invalid_measurements = set(measurements) - set(self.valid_measurements)
            if invalid_measurements:
                violations.append(
                    PhysicsViolation(
                        rule="measurement_types",
                        message=f"Invalid measurement types: {invalid_measurements}",
                        severity="warning",
                        expected=str(self.valid_measurements),
                        actual=str(list(measurements)),
                    )
                )

        return violations


class PhysicsValidator:
    """Main physics validation orchestrator."""

    def __init__(self, tolerance: float = 0.05):
        self.thermal_speed_validator = ThermalSpeedValidator(tolerance)
        self.units_validator = UnitsValidator()
        self.missing_data_validator = MissingDataValidator()
        self.multiindex_validator = MultiIndexValidator()

    def validate_outputs(self, outputs: Dict[str, Any]) -> List[PhysicsViolation]:
        """Comprehensive physics validation of example outputs."""
        violations = []

        # Thermal speed validation
        violations.extend(self.thermal_speed_validator.validate_thermal_speed)

        # Units validation
        violations.extend(self.units_validator.validate_units(outputs))

        # Missing data validation
        violations.extend(self.missing_data_validator.validate_missing_data(outputs))

        # MultiIndex structure validation
        violations.extend(
            self.multiindex_validator.validate_multiindex_structure(outputs)
        )

        # Look for plasma DataFrames for specialized validation
        for var_name, value in outputs.items():
            if isinstance(value, pd.DataFrame) and isinstance(
                value.columns, pd.MultiIndex
            ):
                violations.extend(
                    self.thermal_speed_validator.validate_from_plasma_data(value)
                )

        return violations

    def generate_report(self, violations: List[PhysicsViolation]) -> Dict[str, Any]:
        """Generate physics validation report."""
        if not violations:
            return {
                "physics_compliant": True,
                "total_violations": 0,
                "violations_by_severity": {},
                "violations_by_rule": {},
            }

        violations_by_severity = {}
        violations_by_rule = {}

        for violation in violations:
            # Count by severity
            severity = violation.severity
            violations_by_severity[severity] = (
                violations_by_severity.get(severity, 0) + 1
            )

            # Count by rule
            rule = violation.rule
            violations_by_rule[rule] = violations_by_rule.get(rule, 0) + 1

        return {
            "physics_compliant": len([v for v in violations if v.severity == "error"])
            == 0,
            "total_violations": len(violations),
            "violations_by_severity": violations_by_severity,
            "violations_by_rule": violations_by_rule,
            "violation_details": [
                {
                    "rule": v.rule,
                    "message": v.message,
                    "severity": v.severity,
                    "expected": v.expected,
                    "actual": v.actual,
                }
                for v in violations
            ],
        }


if __name__ == "__main__":
    # Test physics validation
    validator = PhysicsValidator()

    # Test thermal speed validation
    test_outputs = {
        "thermal_speed": np.array([50000, 60000]),  # m/s
        "temperature": np.array([100000, 120000]),  # K
        "velocity": np.array([400000, 500000]),  # m/s (should suggest km/s)
        "bad_fill_data": pd.Series([1, 2, -999, 4, 5]),  # Contains fill value
    }

    violations = validator.validate_outputs(test_outputs)
    report = validator.generate_report(violations)

    print("Physics Validation Test:")
    print(f"Compliant: {report['physics_compliant']}")
    print(f"Total violations: {report['total_violations']}")

    for violation in violations:
        print(f"- {violation.severity.upper()}: {violation.message}")
        if violation.expected:
            print(f"  Expected: {violation.expected}")
            print(f"  Actual: {violation.actual}")
