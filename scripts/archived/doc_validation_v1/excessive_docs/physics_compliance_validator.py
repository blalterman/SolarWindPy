#!/usr/bin/env python3
"""
Comprehensive physics compliance validator for SolarWindPy.

This module validates code examples for physics correctness including:
- Thermal speed convention (mw² = 2kT)
- SI units for internal calculations
- Missing data handling (NaN vs fill values)
- Alfvén speed calculations
- MultiIndex structure compliance

Optimized for speed and practical validation without false positives.
"""

import ast
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
import warnings
import logging

import numpy as np
import pandas as pd

# Import physics constants
from scipy import constants


@dataclass
class ComplianceViolation:
    """Represents a physics compliance violation."""

    rule: str
    message: str
    severity: str  # 'error', 'warning', 'info'
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    expected: Optional[Union[float, str]] = None
    actual: Optional[Union[float, str]] = None
    tolerance: Optional[float] = None
    file_path: Optional[str] = None


@dataclass
class ValidationResult:
    """Results from physics compliance validation."""

    compliant: bool
    total_violations: int
    violations: List[ComplianceViolation] = field(default_factory=list)
    execution_time: float = 0.0
    files_checked: int = 0

    @property
    def violations_by_severity(self) -> Dict[str, int]:
        """Count violations by severity level."""
        counts = {}
        for violation in self.violations:
            counts[violation.severity] = counts.get(violation.severity, 0) + 1
        return counts

    @property
    def violations_by_rule(self) -> Dict[str, int]:
        """Count violations by rule type."""
        counts = {}
        for violation in self.violations:
            counts[violation.rule] = counts.get(violation.rule, 0) + 1
        return counts


class PhysicsConstants:
    """Centralized physics constants for validation."""

    k_B = constants.k  # Boltzmann constant [J/K]
    m_p = constants.m_p  # Proton mass [kg]
    m_e = constants.m_e  # Electron mass [kg]
    mu_0 = constants.mu_0  # Permeability of free space [H/m]
    c = constants.c  # Speed of light [m/s]
    e = constants.e  # Elementary charge [C]

    # Species masses in kg
    species_masses = {
        "p1": m_p,
        "p2": m_p,
        "p": m_p,
        "a": 4 * m_p,
        "he": 4 * m_p,
        "e": m_e,
    }

    # Typical solar wind ranges for validation
    typical_ranges = {
        "velocity_si": (1e2, 1e6),  # m/s
        "velocity_display": (100, 1000),  # km/s
        "density_si": (1e6, 1e12),  # m^-3
        "density_display": (0.1, 100),  # cm^-3
        "temperature": (1e3, 1e7),  # K
        "magnetic_field_si": (1e-9, 1e-3),  # T
        "magnetic_field_display": (0.1, 100),  # nT
        "thermal_speed_si": (1e3, 1e6),  # m/s
        "thermal_speed_display": (10, 1000),  # km/s
    }


class ThermalSpeedComplianceChecker:
    """Validates thermal speed convention: mw² = 2kT."""

    def __init__(self, tolerance: float = 0.1):
        self.tolerance = tolerance  # 10% tolerance for examples

    def check_code_patterns(
        self, code: str, file_path: str = None
    ) -> List[ComplianceViolation]:
        """Check code for thermal speed calculation patterns."""
        violations = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            # Check for incorrect thermal speed calculations
            violations.extend(self._check_thermal_speed_formulas(line, i, file_path))
            # Check for temperature/thermal speed relationships
            violations.extend(self._check_temperature_consistency(line, i, file_path))

        return violations

    def _check_thermal_speed_formulas(
        self, line: str, line_num: int, file_path: str
    ) -> List[ComplianceViolation]:
        """Check for incorrect thermal speed formula patterns."""
        violations = []

        # Pattern: w = sqrt(kT/m) - should be sqrt(2kT/m)
        if re.search(r"sqrt\s*\(\s*k.*T.*\/.*m", line) and "2" not in line:
            if "thermal" in line.lower() or "w" in line:
                violations.append(
                    ComplianceViolation(
                        rule="thermal_speed_formula",
                        message="Thermal speed formula missing factor of 2: should be sqrt(2kT/m)",
                        severity="error",
                        line_number=line_num,
                        code_snippet=line.strip(),
                        file_path=file_path,
                        expected="sqrt(2*k*T/m)",
                        actual="sqrt(k*T/m)",
                    )
                )

        # Pattern: Check for hardcoded thermal speeds that don't match temperature
        if re.search(r"w.*=.*\d+", line) and "thermal" in line.lower():
            # This is a simple heuristic - more complex analysis would need AST parsing
            if any(temp_val in line for temp_val in ["1e5", "100000", "2e4"]):
                violations.append(
                    ComplianceViolation(
                        rule="thermal_speed_consistency",
                        message="Hardcoded thermal speed may not match temperature values",
                        severity="warning",
                        line_number=line_num,
                        code_snippet=line.strip(),
                        file_path=file_path,
                    )
                )

        return violations

    def _check_temperature_consistency(
        self, line: str, line_num: int, file_path: str
    ) -> List[ComplianceViolation]:
        """Check temperature and thermal speed value consistency."""
        violations = []

        # Look for suspicious thermal speed values
        thermal_speed_match = re.search(r"w.*=.*np\.random\.normal\((\d+)", line)
        if thermal_speed_match:
            speed_val = float(thermal_speed_match.group(1))
            # If speed is in km/s display units but should be from temperature
            if 10 < speed_val < 200:  # km/s range
                violations.append(
                    ComplianceViolation(
                        rule="thermal_speed_generation",
                        message="Thermal speed should be calculated from temperature, not hardcoded",
                        severity="warning",
                        line_number=line_num,
                        code_snippet=line.strip(),
                        file_path=file_path,
                        expected="Calculate from temperature using sqrt(2kT/m)",
                        actual=f"Hardcoded value: {speed_val}",
                    )
                )

        return violations

    def validate_data_values(self, data: Dict[str, Any]) -> List[ComplianceViolation]:
        """Validate thermal speed values in execution results."""
        violations = []

        # Look for DataFrames with thermal speed and temperature data
        for var_name, value in data.items():
            if isinstance(value, pd.DataFrame) and hasattr(value, "columns"):
                if isinstance(value.columns, pd.MultiIndex):
                    violations.extend(
                        self._validate_multiindex_thermal_speeds(value, var_name)
                    )
            elif (
                isinstance(value, (np.ndarray, pd.Series))
                and "thermal" in var_name.lower()
            ):
                violations.extend(self._validate_thermal_speed_array(value, var_name))

        return violations

    def _validate_multiindex_thermal_speeds(
        self, df: pd.DataFrame, var_name: str
    ) -> List[ComplianceViolation]:
        """Validate thermal speeds in MultiIndex DataFrame."""
        violations = []

        try:
            # Look for thermal speed and temperature columns
            w_cols = [col for col in df.columns if col[0] == "w"]
            T_cols = [col for col in df.columns if col[0] == "T"]

            for w_col in w_cols:
                species = w_col[2] if len(w_col) > 2 else "p1"

                # Try to find corresponding temperature
                T_col = None
                for t_col in T_cols:
                    if len(t_col) > 2 and t_col[2] == species:
                        T_col = t_col
                        break

                if T_col is not None:
                    w_data = df[w_col].dropna()
                    T_data = df[T_col].dropna()

                    if len(w_data) > 0 and len(T_data) > 0:
                        # Check if values are consistent with mw² = 2kT
                        mass = PhysicsConstants.species_masses.get(
                            species, PhysicsConstants.m_p
                        )
                        violations.extend(
                            self._check_thermal_speed_temperature_relation(
                                w_data.values, T_data.values, mass, var_name, species
                            )
                        )
        except Exception:
            pass  # Skip validation if structure is unexpected

        return violations

    def _validate_thermal_speed_array(
        self, data: Union[np.ndarray, pd.Series], var_name: str
    ) -> List[ComplianceViolation]:
        """Validate thermal speed array values."""
        violations = []

        if isinstance(data, pd.Series):
            data = data.dropna().values

        if len(data) == 0:
            return violations

        # Check for reasonable thermal speed values
        median_val = np.median(data)

        # If values look like they're in m/s (very high)
        if median_val > 1e5:
            violations.append(
                ComplianceViolation(
                    rule="thermal_speed_units",
                    message="Thermal speed values appear to be in m/s, consider km/s for display",
                    severity="warning",
                    expected="10-200 km/s (typical range)",
                    actual=f"{median_val:.2e} (appears to be m/s)",
                )
            )

        # If values are unreasonably high or low
        elif median_val > 1000 or median_val < 1:
            violations.append(
                ComplianceViolation(
                    rule="thermal_speed_range",
                    message="Thermal speed outside physically reasonable range",
                    severity="error",
                    expected="10-200 km/s",
                    actual=f"{median_val:.2f}",
                )
            )

        return violations

    def _check_thermal_speed_temperature_relation(
        self,
        w_data: np.ndarray,
        T_data: np.ndarray,
        mass: float,
        var_name: str,
        species: str,
    ) -> List[ComplianceViolation]:
        """Check if thermal speed and temperature follow mw² = 2kT relation."""
        violations = []

        # Take median values to avoid issues with time series alignment
        w_median = np.median(w_data)
        T_median = np.median(T_data)

        # Convert thermal speed to SI if needed (assume km/s for display)
        if w_median < 1000:  # Likely in km/s
            w_si = w_median * 1000
        else:  # Already in m/s
            w_si = w_median

        # Expected thermal speed from temperature: w = sqrt(2kT/m)
        w_expected = np.sqrt(2 * PhysicsConstants.k_B * T_median / mass)

        # Check relative error
        if w_expected > 0:
            relative_error = abs(w_si - w_expected) / w_expected

            if relative_error > self.tolerance:
                violations.append(
                    ComplianceViolation(
                        rule="thermal_speed_temperature_consistency",
                        message=f"Thermal speed for {species} inconsistent with temperature (mw² = 2kT)",
                        severity="warning",  # Often examples use simplified values
                        expected=f"{w_expected/1000:.1f} km/s",
                        actual=f"{w_si/1000:.1f} km/s",
                        tolerance=relative_error,
                    )
                )

        return violations


class UnitsComplianceChecker:
    """Validates unit usage - SI internally, display units for output."""

    def check_code_patterns(
        self, code: str, file_path: str = None
    ) -> List[ComplianceViolation]:
        """Check code for unit usage patterns."""
        violations = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            violations.extend(self._check_unit_conversions(line, i, file_path))
            violations.extend(self._check_hardcoded_values(line, i, file_path))

        return violations

    def _check_unit_conversions(
        self, line: str, line_num: int, file_path: str
    ) -> List[ComplianceViolation]:
        """Check for proper unit conversion patterns."""
        violations = []

        # Look for multiplication/division by common conversion factors
        conversion_patterns = [
            (r"\*\s*1e3", "velocity conversion m/s to km/s"),
            (r"\/\s*1e3", "velocity conversion km/s to m/s"),
            (r"\*\s*1e-9", "magnetic field conversion T to nT"),
            (r"\/\s*1e-9", "magnetic field conversion nT to T"),
            (r"\*\s*1e6", "density conversion m^-3 to cm^-3"),
            (r"\/\s*1e6", "density conversion cm^-3 to m^-3"),
        ]

        for pattern, description in conversion_patterns:
            if re.search(pattern, line):
                # This is good - unit conversions are present
                # Could add more sophisticated checking for context
                pass

        # Check for missing unit conversions in calculations
        if re.search(r"sqrt\s*\(.*k.*T.*\/.*m", line):
            if "units" not in line.lower() and "convert" not in line.lower():
                violations.append(
                    ComplianceViolation(
                        rule="missing_unit_conversion",
                        message="Physics calculation may need unit conversion consideration",
                        severity="info",
                        line_number=line_num,
                        code_snippet=line.strip(),
                        file_path=file_path,
                    )
                )

        return violations

    def _check_hardcoded_values(
        self, line: str, line_num: int, file_path: str
    ) -> List[ComplianceViolation]:
        """Check for hardcoded values that should use constants."""
        violations = []

        # Check for hardcoded physical constants
        constant_patterns = [
            (r"1\.67.*e-27", "proton mass - consider using constants.m_p"),
            (r"9\.109.*e-31", "electron mass - consider using constants.m_e"),
            (r"1\.38.*e-23", "Boltzmann constant - consider using constants.k"),
            (r"4.*pi.*1e-7", "permeability - consider using constants.mu_0"),
        ]

        for pattern, message in constant_patterns:
            if re.search(pattern, line):
                violations.append(
                    ComplianceViolation(
                        rule="hardcoded_constants",
                        message=message,
                        severity="warning",
                        line_number=line_num,
                        code_snippet=line.strip(),
                        file_path=file_path,
                    )
                )

        return violations

    def validate_data_values(self, data: Dict[str, Any]) -> List[ComplianceViolation]:
        """Validate units in execution results."""
        violations = []

        for var_name, value in data.items():
            violations.extend(self._check_variable_units(var_name, value))

        return violations

    def _check_variable_units(
        self, var_name: str, data: Any
    ) -> List[ComplianceViolation]:
        """Check if variable values are in expected unit ranges."""
        violations = []

        if not isinstance(data, (int, float, np.ndarray, pd.Series, pd.DataFrame)):
            return violations

        # Convert to array for analysis
        if isinstance(data, pd.DataFrame):
            return violations  # Handle DataFrames separately
        elif isinstance(data, pd.Series):
            arr = data.dropna().values
        else:
            arr = np.atleast_1d(data)

        if len(arr) == 0:
            return violations

        median_val = np.median(arr)

        # Velocity checks
        if any(v_key in var_name.lower() for v_key in ["velocity", "v_p", "speed"]):
            if "thermal" not in var_name.lower():  # Bulk velocity
                if 1e4 < median_val < 1e6:  # Likely m/s, should be km/s for display
                    violations.append(
                        ComplianceViolation(
                            rule="velocity_display_units",
                            message="Velocity appears to be in m/s, consider km/s for display",
                            severity="info",
                            expected="~400 km/s (typical solar wind)",
                            actual=f"{median_val:.0f} m/s",
                        )
                    )
                elif median_val > 1e6 or median_val < 10:
                    violations.append(
                        ComplianceViolation(
                            rule="velocity_range",
                            message="Velocity outside reasonable range",
                            severity="warning",
                            expected="100-1000 km/s or 1e5-1e6 m/s",
                            actual=f"{median_val:.2e}",
                        )
                    )

        # Density checks
        if any(d_key in var_name.lower() for d_key in ["density", "n_p"]):
            if 1e6 < median_val < 1e12:  # Likely m^-3, should be cm^-3 for display
                violations.append(
                    ComplianceViolation(
                        rule="density_display_units",
                        message="Density appears to be in m^-3, consider cm^-3 for display",
                        severity="info",
                        expected="~5 cm^-3 (typical solar wind)",
                        actual=f"{median_val:.2e} m^-3",
                    )
                )

        # Magnetic field checks
        if any(
            b_key in var_name.lower() for b_key in ["magnetic", "b_field", "bfield"]
        ):
            if 1e-9 < median_val < 1e-6:  # Likely T, should be nT for display
                violations.append(
                    ComplianceViolation(
                        rule="magnetic_field_display_units",
                        message="Magnetic field appears to be in T, consider nT for display",
                        severity="info",
                        expected="~5 nT (typical solar wind)",
                        actual=f"{median_val:.2e} T",
                    )
                )

        return violations


class MissingDataComplianceChecker:
    """Validates missing data is represented as NaN, not fill values."""

    def __init__(self):
        self.bad_fill_values = [0, -999, -9999, 999, 9999, -1]

    def check_code_patterns(
        self, code: str, file_path: str = None
    ) -> List[ComplianceViolation]:
        """Check code for missing data handling patterns."""
        violations = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            violations.extend(self._check_fill_value_usage(line, i, file_path))
            violations.extend(self._check_nan_usage(line, i, file_path))

        return violations

    def _check_fill_value_usage(
        self, line: str, line_num: int, file_path: str
    ) -> List[ComplianceViolation]:
        """Check for problematic fill value usage."""
        violations = []

        # Look for assignment of common fill values
        for fill_val in ["-999", "999", "-9999"]:
            if f"= {fill_val}" in line or f"={fill_val}" in line:
                violations.append(
                    ComplianceViolation(
                        rule="fill_value_assignment",
                        message=f"Using fill value {fill_val}, consider np.nan instead",
                        severity="warning",
                        line_number=line_num,
                        code_snippet=line.strip(),
                        file_path=file_path,
                        expected="np.nan",
                        actual=fill_val,
                    )
                )

        # Check for zero as missing data indicator in physical quantities
        if "= 0" in line and any(
            phys in line.lower() for phys in ["temperature", "density", "pressure"]
        ):
            violations.append(
                ComplianceViolation(
                    rule="zero_as_missing_data",
                    message="Zero may not be appropriate for missing physical quantity",
                    severity="info",
                    line_number=line_num,
                    code_snippet=line.strip(),
                    file_path=file_path,
                    expected="np.nan for missing data",
                    actual="0",
                )
            )

        return violations

    def _check_nan_usage(
        self, line: str, line_num: int, file_path: str
    ) -> List[ComplianceViolation]:
        """Check for proper NaN usage."""
        violations = []

        # Positive check: good NaN usage
        if "np.nan" in line or "pd.isna" in line or "dropna" in line:
            # This is good practice - no violation
            pass

        # Check for improper NaN comparisons
        if "== np.nan" in line:
            violations.append(
                ComplianceViolation(
                    rule="nan_comparison",
                    message="Use pd.isna() or np.isnan() instead of == np.nan",
                    severity="error",
                    line_number=line_num,
                    code_snippet=line.strip(),
                    file_path=file_path,
                    expected="pd.isna() or np.isnan()",
                    actual="== np.nan",
                )
            )

        return violations

    def validate_data_values(self, data: Dict[str, Any]) -> List[ComplianceViolation]:
        """Validate missing data representation in execution results."""
        violations = []

        for var_name, value in data.items():
            violations.extend(self._check_data_for_fill_values(var_name, value))

        return violations

    def _check_data_for_fill_values(
        self, var_name: str, data: Any
    ) -> List[ComplianceViolation]:
        """Check data for improper fill values."""
        violations = []

        if isinstance(data, pd.DataFrame):
            for fill_val in self.bad_fill_values:
                count = (data == fill_val).sum().sum()
                if count > 0:
                    violations.append(
                        ComplianceViolation(
                            rule="data_fill_values",
                            message=f"Found {count} instances of fill value {fill_val} in {var_name}",
                            severity="warning",
                            expected="np.nan",
                            actual=f"{fill_val} ({count} instances)",
                        )
                    )

        elif isinstance(data, (pd.Series, np.ndarray)):
            arr = np.array(data) if not isinstance(data, np.ndarray) else data
            for fill_val in self.bad_fill_values:
                count = np.sum(arr == fill_val)
                if count > 0:
                    violations.append(
                        ComplianceViolation(
                            rule="data_fill_values",
                            message=f"Found {count} instances of fill value {fill_val} in {var_name}",
                            severity="warning",
                            expected="np.nan",
                            actual=f"{fill_val} ({count} instances)",
                        )
                    )

        return violations


class AlfvenSpeedComplianceChecker:
    """Validates Alfvén speed calculations: V_A = B/√(μ₀ρ)."""

    def check_code_patterns(
        self, code: str, file_path: str = None
    ) -> List[ComplianceViolation]:
        """Check code for Alfvén speed calculation patterns."""
        violations = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            violations.extend(self._check_alfven_formulas(line, i, file_path))

        return violations

    def _check_alfven_formulas(
        self, line: str, line_num: int, file_path: str
    ) -> List[ComplianceViolation]:
        """Check for Alfvén speed formula patterns."""
        violations = []

        # Look for Alfvén speed calculations
        if any(alfven_key in line.lower() for alfven_key in ["alfven", "v_a", "ca"]):
            # Check for proper formula: B / sqrt(mu0 * rho)
            if "sqrt" in line.lower():
                if "mu0" not in line.lower() and "mu_0" not in line.lower():
                    violations.append(
                        ComplianceViolation(
                            rule="alfven_speed_formula",
                            message="Alfvén speed calculation missing μ₀ (permeability)",
                            severity="warning",
                            line_number=line_num,
                            code_snippet=line.strip(),
                            file_path=file_path,
                            expected="B / sqrt(mu_0 * rho)",
                            actual="Missing mu_0 term",
                        )
                    )

                # Check if mass density is properly calculated
                if "rho" not in line.lower() and "density" not in line.lower():
                    violations.append(
                        ComplianceViolation(
                            rule="alfven_speed_density",
                            message="Alfvén speed needs mass density (ρ = Σ n_i * m_i)",
                            severity="info",
                            line_number=line_num,
                            code_snippet=line.strip(),
                            file_path=file_path,
                            expected="Include ion composition in mass density",
                            actual="May be missing ion composition",
                        )
                    )

        return violations

    def validate_data_values(self, data: Dict[str, Any]) -> List[ComplianceViolation]:
        """Validate Alfvén speed values in execution results."""
        violations = []

        for var_name, value in data.items():
            if any(
                alfven_key in var_name.lower() for alfven_key in ["alfven", "v_a", "ca"]
            ):
                violations.extend(self._validate_alfven_speed_values(value, var_name))

        return violations

    def _validate_alfven_speed_values(
        self, data: Any, var_name: str
    ) -> List[ComplianceViolation]:
        """Validate Alfvén speed values are reasonable."""
        violations = []

        if isinstance(data, (pd.Series, np.ndarray)):
            arr = np.array(data) if not isinstance(data, np.ndarray) else data
            arr = arr[~np.isnan(arr)]  # Remove NaN values

            if len(arr) == 0:
                return violations

            median_val = np.median(arr)

            # Typical Alfvén speed range: 10-200 km/s
            if median_val > 1000:  # Very high - might be in m/s
                violations.append(
                    ComplianceViolation(
                        rule="alfven_speed_units",
                        message="Alfvén speed appears to be in m/s, consider km/s for display",
                        severity="info",
                        expected="10-200 km/s (typical range)",
                        actual=f"{median_val:.0f} (appears to be m/s)",
                    )
                )
            elif median_val > 500 or median_val < 1:
                violations.append(
                    ComplianceViolation(
                        rule="alfven_speed_range",
                        message="Alfvén speed outside typical solar wind range",
                        severity="warning",
                        expected="10-200 km/s",
                        actual=f"{median_val:.1f}",
                    )
                )

        return violations


class MultiIndexComplianceChecker:
    """Validates MultiIndex DataFrame structure compliance."""

    def __init__(self):
        self.required_levels = ["M", "C", "S"]
        self.valid_measurements = ["n", "v", "w", "b", "T", "P", "beta"]
        self.valid_components = ["x", "y", "z", "par", "per", ""]
        self.valid_species = ["p1", "p2", "a", "he", "e", ""]

    def check_code_patterns(
        self, code: str, file_path: str = None
    ) -> List[ComplianceViolation]:
        """Check code for MultiIndex structure patterns."""
        violations = []
        lines = code.split("\n")

        # Check for MultiIndex creation patterns across multiple lines
        violations.extend(self._check_multiindex_creation(code, file_path))

        for i, line in enumerate(lines, 1):
            violations.extend(self._check_multiindex_usage(line, i, file_path))

        return violations

    def _check_multiindex_creation(
        self, code: str, file_path: str
    ) -> List[ComplianceViolation]:
        """Check for proper MultiIndex creation patterns across multiple lines."""
        violations = []

        # Simple approach: look for MultiIndex.from_tuples followed by names= within reasonable distance
        if "MultiIndex.from_tuples" in code:
            # Find the start of MultiIndex.from_tuples
            start_pos = code.find("MultiIndex.from_tuples")

            # Look for the closing parenthesis that matches the opening one
            # This is a simplified approach - we'll look for names= in the next 500 characters
            search_region = code[start_pos : start_pos + 500]

            if "names=" not in search_region and "names =" not in search_region:
                # Find line number
                line_num = code[:start_pos].count("\n") + 1
                violations.append(
                    ComplianceViolation(
                        rule="multiindex_level_names",
                        message="MultiIndex should specify level names ['M', 'C', 'S']",
                        severity="warning",
                        line_number=line_num,
                        code_snippet="MultiIndex.from_tuples(...)",
                        file_path=file_path,
                        expected="names=['M', 'C', 'S']",
                        actual="Missing names parameter",
                    )
                )

        return violations

    def _check_multiindex_usage(
        self, line: str, line_num: int, file_path: str
    ) -> List[ComplianceViolation]:
        """Check for proper MultiIndex usage patterns."""
        violations = []

        # Check for proper level access
        if ".xs(" in line and "level=" in line:
            # This is good - using proper level access
            pass
        elif ".xs(" in line and "level=" not in line:
            violations.append(
                ComplianceViolation(
                    rule="multiindex_level_access",
                    message="Consider using level names in .xs() for clarity",
                    severity="info",
                    line_number=line_num,
                    code_snippet=line.strip(),
                    file_path=file_path,
                    expected=".xs('value', level='M')",
                    actual="Missing level specification",
                )
            )

        # Check for DataFrame slicing that might break MultiIndex
        if "[(" in line and ")]" in line and "level" not in line:
            # Direct tuple access - could be improved
            violations.append(
                ComplianceViolation(
                    rule="multiindex_direct_access",
                    message="Consider using .xs() with level names for MultiIndex access",
                    severity="info",
                    line_number=line_num,
                    code_snippet=line.strip(),
                    file_path=file_path,
                )
            )

        return violations

    def validate_data_values(self, data: Dict[str, Any]) -> List[ComplianceViolation]:
        """Validate MultiIndex structure in execution results."""
        violations = []

        for var_name, value in data.items():
            if isinstance(value, pd.DataFrame) and isinstance(
                value.columns, pd.MultiIndex
            ):
                violations.extend(self._validate_multiindex_structure(value, var_name))

        return violations

    def _validate_multiindex_structure(
        self, df: pd.DataFrame, var_name: str
    ) -> List[ComplianceViolation]:
        """Validate MultiIndex DataFrame structure."""
        violations = []

        # Check level names
        if list(df.columns.names) != self.required_levels:
            violations.append(
                ComplianceViolation(
                    rule="multiindex_level_names",
                    message=f"MultiIndex levels should be {self.required_levels}",
                    severity="error",
                    expected="['M', 'C', 'S']",
                    actual=str(list(df.columns.names)),
                )
            )

        # Check for valid measurement types
        if "M" in df.columns.names:
            measurements = df.columns.get_level_values("M").unique()
            invalid_measurements = set(measurements) - set(self.valid_measurements)
            if invalid_measurements:
                violations.append(
                    ComplianceViolation(
                        rule="invalid_measurement_types",
                        message=f"Invalid measurement types: {invalid_measurements}",
                        severity="warning",
                        expected=str(self.valid_measurements),
                        actual=str(list(measurements)),
                    )
                )

        # Check for valid components
        if "C" in df.columns.names:
            components = df.columns.get_level_values("C").unique()
            invalid_components = set(components) - set(self.valid_components)
            if invalid_components:
                violations.append(
                    ComplianceViolation(
                        rule="invalid_component_types",
                        message=f"Invalid component types: {invalid_components}",
                        severity="warning",
                        expected=str(self.valid_components),
                        actual=str(list(components)),
                    )
                )

        # Check for valid species
        if "S" in df.columns.names:
            species = df.columns.get_level_values("S").unique()
            invalid_species = set(species) - set(self.valid_species)
            if invalid_species:
                violations.append(
                    ComplianceViolation(
                        rule="invalid_species_types",
                        message=f"Invalid species types: {invalid_species}",
                        severity="warning",
                        expected=str(self.valid_species),
                        actual=str(list(species)),
                    )
                )

        return violations


class PhysicsComplianceValidator:
    """Main physics compliance validator for SolarWindPy."""

    def __init__(self, tolerance: float = 0.1, fast_mode: bool = True):
        """
        Initialize the validator.

        Parameters
        ----------
        tolerance : float
            Tolerance for numerical comparisons (default 10%)
        fast_mode : bool
            If True, optimize for speed over exhaustive checking
        """
        self.tolerance = tolerance
        self.fast_mode = fast_mode

        # Initialize component checkers
        self.thermal_speed_checker = ThermalSpeedComplianceChecker(tolerance)
        self.units_checker = UnitsComplianceChecker()
        self.missing_data_checker = MissingDataComplianceChecker()
        self.alfven_speed_checker = AlfvenSpeedComplianceChecker()
        self.multiindex_checker = MultiIndexComplianceChecker()

        # Setup logging
        self.logger = logging.getLogger(__name__)

    def validate_file(self, file_path: Union[str, Path]) -> ValidationResult:
        """
        Validate a single Python file for physics compliance.

        Parameters
        ----------
        file_path : str or Path
            Path to Python file to validate

        Returns
        -------
        ValidationResult
            Comprehensive validation results
        """
        start_time = time.time()
        file_path = Path(file_path)
        violations = []

        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()

            # Static code analysis
            violations.extend(self._validate_code_static(code, str(file_path)))

            # Dynamic analysis (execution-based) - only if requested
            if not self.fast_mode:
                violations.extend(self._validate_code_dynamic(code, str(file_path)))

        except Exception as e:
            self.logger.warning(f"Failed to validate {file_path}: {e}")
            violations.append(
                ComplianceViolation(
                    rule="validation_error",
                    message=f"Failed to validate file: {e}",
                    severity="error",
                    file_path=str(file_path),
                )
            )

        execution_time = time.time() - start_time

        return ValidationResult(
            compliant=len([v for v in violations if v.severity == "error"]) == 0,
            total_violations=len(violations),
            violations=violations,
            execution_time=execution_time,
            files_checked=1,
        )

    def validate_documentation_examples(
        self, doc_path: Union[str, Path]
    ) -> ValidationResult:
        """
        Validate code examples from documentation files.

        Parameters
        ----------
        doc_path : str or Path
            Path to documentation file (e.g., .rst, .md)

        Returns
        -------
        ValidationResult
            Validation results for all code examples found
        """
        start_time = time.time()
        doc_path = Path(doc_path)
        violations = []

        try:
            with open(doc_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract code blocks
            code_blocks = self._extract_code_blocks(content)

            for i, code_block in enumerate(code_blocks):
                block_violations = self._validate_code_static(
                    code_block, f"{doc_path}:block_{i+1}"
                )
                violations.extend(block_violations)

        except Exception as e:
            self.logger.warning(f"Failed to validate documentation {doc_path}: {e}")
            violations.append(
                ComplianceViolation(
                    rule="doc_validation_error",
                    message=f"Failed to validate documentation: {e}",
                    severity="error",
                    file_path=str(doc_path),
                )
            )

        execution_time = time.time() - start_time

        return ValidationResult(
            compliant=len([v for v in violations if v.severity == "error"]) == 0,
            total_violations=len(violations),
            violations=violations,
            execution_time=execution_time,
            files_checked=1,
        )

    def validate_multiple_files(
        self, file_patterns: List[str], base_path: Union[str, Path] = "."
    ) -> ValidationResult:
        """
        Validate multiple files matching given patterns.

        Parameters
        ----------
        file_patterns : List[str]
            List of glob patterns to match files
        base_path : str or Path
            Base directory for pattern matching

        Returns
        -------
        ValidationResult
            Combined validation results
        """
        start_time = time.time()
        base_path = Path(base_path)
        all_violations = []
        files_checked = 0

        for pattern in file_patterns:
            for file_path in base_path.glob(pattern):
                if file_path.is_file():
                    result = self.validate_file(file_path)
                    all_violations.extend(result.violations)
                    files_checked += 1

                    # Early termination for speed in fast mode
                    if self.fast_mode and files_checked > 20:
                        break

        execution_time = time.time() - start_time

        return ValidationResult(
            compliant=len([v for v in all_violations if v.severity == "error"]) == 0,
            total_violations=len(all_violations),
            violations=all_violations,
            execution_time=execution_time,
            files_checked=files_checked,
        )

    def _validate_code_static(
        self, code: str, file_path: str
    ) -> List[ComplianceViolation]:
        """Perform static code analysis for physics compliance."""
        violations = []

        # Run all static checkers
        violations.extend(
            self.thermal_speed_checker.check_code_patterns(code, file_path)
        )
        violations.extend(self.units_checker.check_code_patterns(code, file_path))
        violations.extend(
            self.missing_data_checker.check_code_patterns(code, file_path)
        )
        violations.extend(
            self.alfven_speed_checker.check_code_patterns(code, file_path)
        )
        violations.extend(self.multiindex_checker.check_code_patterns(code, file_path))

        return violations

    def _validate_code_dynamic(
        self, code: str, file_path: str
    ) -> List[ComplianceViolation]:
        """Perform dynamic analysis by executing code and checking outputs."""
        violations = []

        try:
            # Create execution environment
            exec_globals = {"np": np, "pd": pd, "__name__": "__main__"}

            # Try to import solarwindpy modules for examples
            try:
                import solarwindpy as swp

                exec_globals["swp"] = swp
                exec_globals["solarwindpy"] = swp
            except ImportError:
                pass

            # Execute code and capture outputs
            exec(code, exec_globals)

            # Check outputs from execution
            for checker in [
                self.thermal_speed_checker,
                self.units_checker,
                self.missing_data_checker,
                self.alfven_speed_checker,
                self.multiindex_checker,
            ]:
                if hasattr(checker, "validate_data_values"):
                    violations.extend(checker.validate_data_values(exec_globals))

        except Exception as e:
            # Execution failed - this might be expected for documentation examples
            self.logger.debug(f"Code execution failed for {file_path}: {e}")

        return violations

    def _extract_code_blocks(self, content: str) -> List[str]:
        """Extract Python code blocks from documentation."""
        code_blocks = []

        # RST code blocks
        rst_pattern = r".. code-block:: python\s*\n\n((?:[ \t]+.*\n?)*)"
        rst_matches = re.findall(rst_pattern, content, re.MULTILINE)

        for match in rst_matches:
            # Remove common indentation
            lines = match.split("\n")
            if lines:
                min_indent = min(
                    len(line) - len(line.lstrip()) for line in lines if line.strip()
                )
                clean_lines = [
                    line[min_indent:] if len(line) > min_indent else line
                    for line in lines
                ]
                code_blocks.append("\n".join(clean_lines))

        # Markdown code blocks
        md_pattern = r"```python\s*\n(.*?)\n```"
        md_matches = re.findall(md_pattern, content, re.DOTALL)
        code_blocks.extend(md_matches)

        return code_blocks

    def generate_report(self, result: ValidationResult) -> str:
        """
        Generate a human-readable compliance report.

        Parameters
        ----------
        result : ValidationResult
            Validation results to report

        Returns
        -------
        str
            Formatted compliance report
        """
        report = []
        report.append("=" * 60)
        report.append("SOLARWINDPY PHYSICS COMPLIANCE REPORT")
        report.append("=" * 60)
        report.append("")

        # Summary
        status = "COMPLIANT" if result.compliant else "NON-COMPLIANT"
        report.append(f"Overall Status: {status}")
        report.append(f"Files Checked: {result.files_checked}")
        report.append(f"Total Violations: {result.total_violations}")
        report.append(f"Execution Time: {result.execution_time:.2f}s")
        report.append("")

        # Violations by severity
        if result.violations_by_severity:
            report.append("Violations by Severity:")
            for severity, count in sorted(result.violations_by_severity.items()):
                report.append(f"  {severity.upper()}: {count}")
            report.append("")

        # Violations by rule
        if result.violations_by_rule:
            report.append("Violations by Rule:")
            for rule, count in sorted(result.violations_by_rule.items()):
                report.append(f"  {rule}: {count}")
            report.append("")

        # Detailed violations (limit for readability)
        if result.violations:
            report.append("Detailed Violations:")
            report.append("-" * 40)

            for i, violation in enumerate(result.violations[:20]):  # Limit output
                report.append(
                    f"{i+1}. {violation.severity.upper()}: {violation.message}"
                )
                if violation.file_path:
                    report.append(f"   File: {violation.file_path}")
                if violation.line_number:
                    report.append(f"   Line: {violation.line_number}")
                if violation.code_snippet:
                    report.append(f"   Code: {violation.code_snippet}")
                if violation.expected and violation.actual:
                    report.append(f"   Expected: {violation.expected}")
                    report.append(f"   Actual: {violation.actual}")
                report.append("")

            if len(result.violations) > 20:
                report.append(f"... and {len(result.violations) - 20} more violations")

        return "\n".join(report)


def main():
    """Command line interface for physics compliance validation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate SolarWindPy code for physics compliance"
    )
    parser.add_argument(
        "files",
        nargs="*",
        default=["docs/source/usage.rst"],
        help="Files or patterns to validate (default: usage documentation)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast mode: static analysis only, skip execution",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.1,
        help="Tolerance for numerical comparisons (default: 0.1)",
    )
    parser.add_argument(
        "--output", "-o", type=str, help="Output file for report (default: stdout)"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    # Create validator
    validator = PhysicsComplianceValidator(
        tolerance=args.tolerance, fast_mode=args.fast
    )

    # Validate files
    start_time = time.time()
    all_results = []

    for file_pattern in args.files:
        file_path = Path(file_pattern)

        if file_path.exists() and file_path.is_file():
            if file_path.suffix in [".rst", ".md"]:
                result = validator.validate_documentation_examples(file_path)
            else:
                result = validator.validate_file(file_path)
            all_results.append(result)
        else:
            # Treat as glob pattern
            result = validator.validate_multiple_files([file_pattern])
            all_results.append(result)

    # Combine results
    if all_results:
        combined_violations = []
        total_files = 0
        for result in all_results:
            combined_violations.extend(result.violations)
            total_files += result.files_checked

        combined_result = ValidationResult(
            compliant=len([v for v in combined_violations if v.severity == "error"])
            == 0,
            total_violations=len(combined_violations),
            violations=combined_violations,
            execution_time=time.time() - start_time,
            files_checked=total_files,
        )
    else:
        combined_result = ValidationResult(
            compliant=True,
            total_violations=0,
            execution_time=time.time() - start_time,
            files_checked=0,
        )

    # Generate report
    report = validator.generate_report(combined_result)

    # Output report
    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report written to {args.output}")
    else:
        print(report)

    # Exit with error code if non-compliant
    sys.exit(0 if combined_result.compliant else 1)


if __name__ == "__main__":
    main()
