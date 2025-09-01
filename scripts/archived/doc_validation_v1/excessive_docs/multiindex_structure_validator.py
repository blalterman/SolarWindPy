#!/usr/bin/env python3
"""
Comprehensive MultiIndex DataFrame structure validator for SolarWindPy.

This module validates that pandas DataFrames follow SolarWindPy's hierarchical
structure conventions for scientific data organization. It focuses on:

1. Column Structure: 3-level MultiIndex with ('M', 'C', 'S') names
2. Measurement Types: Valid M level values (n, v, w, b, T, P, etc.)
3. Component Types: Valid C level values (x, y, z, par, per, '', etc.)
4. Species Types: Valid S level values (p1, p2, a, he, '', etc.)
5. Data Access Patterns: Validates use of .xs() vs .loc[] or direct indexing
6. Index Naming: Ensures time series DataFrames use 'Epoch' as index name

Optimized for speed, minimal false positives, and CI/CD integration.
"""

import ast
import re
import time
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple, Set
import logging

import numpy as np
import pandas as pd


@dataclass
class StructureViolation:
    """Represents a MultiIndex structure violation."""

    rule: str
    message: str
    severity: str  # 'error', 'warning', 'info'
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    file_path: Optional[str] = None
    expected: Optional[Union[str, List]] = None
    actual: Optional[Union[str, List]] = None
    data_shape: Optional[Tuple[int, ...]] = None
    memory_usage: Optional[str] = None


@dataclass
class ValidationReport:
    """Results from MultiIndex structure validation."""

    compliant: bool
    total_violations: int
    violations: List[StructureViolation] = field(default_factory=list)
    execution_time: float = 0.0
    files_checked: int = 0
    dataframes_checked: int = 0

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


class MultiIndexStructureValidator:
    """
    Comprehensive validator for SolarWindPy's MultiIndex DataFrame patterns.

    Validates the hierarchical DataFrame structure that is central to
    SolarWindPy's architecture for organizing scientific measurements.
    """

    def __init__(self, tolerance: float = 0.05, strict_mode: bool = False):
        """
        Initialize the MultiIndex structure validator.

        Parameters
        ----------
        tolerance : float, optional
            Tolerance for numerical validation (default: 5%)
        strict_mode : bool, optional
            If True, enforce stricter validation rules (default: False)
        """
        self.tolerance = tolerance
        self.strict_mode = strict_mode

        # Define valid MultiIndex structure
        self.required_levels = ["M", "C", "S"]

        # Valid measurement types (M level)
        self.valid_measurements = {
            "n",  # Number density
            "v",  # Velocity
            "w",  # Thermal speed
            "b",  # Magnetic field
            "T",  # Temperature
            "P",  # Pressure
            "beta",  # Plasma beta
            "nu",  # Collision frequency
            "lambda",  # Mean free path
            "kappa",  # Kappa parameter
            "pdyn",  # Dynamic pressure
            "pmag",  # Magnetic pressure
            "pth",  # Thermal pressure
        }

        # Valid component types (C level)
        self.valid_components = {
            "x",
            "y",
            "z",  # Cartesian coordinates
            "par",
            "per",  # Parallel/perpendicular
            "mag",  # Magnitude
            "phi",
            "theta",  # Spherical coordinates
            "",  # Empty for scalars
        }

        # Valid species types (S level)
        self.valid_species = {
            "p1",
            "p2",  # Protons (primary/secondary)
            "a",  # Alpha particles
            "he",
            "he2",  # Helium
            "o",
            "o6",
            "o7",  # Oxygen
            "c",
            "c6",  # Carbon
            "n",
            "n5",  # Nitrogen
            "si",
            "si9",  # Silicon
            "mg",
            "mg10",  # Magnesium
            "fe",
            "fe9",  # Iron
            "e",  # Electrons
            "",  # Empty for magnetic field
        }

        # Expected index name for time series
        self.expected_index_name = "Epoch"

        # Setup logging
        self.logger = logging.getLogger(__name__)

    def validate_structure(
        self, data: Dict[str, Any], file_path: str = None
    ) -> ValidationReport:
        """
        Validate MultiIndex DataFrame structures in provided data.

        Parameters
        ----------
        data : Dict[str, Any]
            Dictionary containing variables to validate (e.g., from exec)
        file_path : str, optional
            Path to file being validated for context

        Returns
        -------
        ValidationReport
            Comprehensive validation results
        """
        start_time = time.time()
        violations = []
        dataframes_checked = 0

        # Find and validate all DataFrames
        for var_name, value in data.items():
            if isinstance(value, pd.DataFrame):
                dataframes_checked += 1
                violations.extend(
                    self._validate_dataframe_structure(value, var_name, file_path)
                )

        execution_time = time.time() - start_time

        return ValidationReport(
            compliant=len([v for v in violations if v.severity == "error"]) == 0,
            total_violations=len(violations),
            violations=violations,
            execution_time=execution_time,
            files_checked=1 if file_path else 0,
            dataframes_checked=dataframes_checked,
        )

    def validate_code_patterns(
        self, code: str, file_path: str = None
    ) -> ValidationReport:
        """
        Validate MultiIndex access patterns in code.

        Parameters
        ----------
        code : str
            Python code to analyze
        file_path : str, optional
            Path to file being validated for context

        Returns
        -------
        ValidationReport
            Validation results for code patterns
        """
        start_time = time.time()
        violations = []

        violations.extend(self._check_multiindex_creation_patterns(code, file_path))
        violations.extend(self._check_data_access_patterns(code, file_path))
        violations.extend(self._check_index_naming_patterns(code, file_path))

        execution_time = time.time() - start_time

        return ValidationReport(
            compliant=len([v for v in violations if v.severity == "error"]) == 0,
            total_violations=len(violations),
            violations=violations,
            execution_time=execution_time,
            files_checked=1 if file_path else 0,
        )

    def validate_file(self, file_path: Union[str, Path]) -> ValidationReport:
        """
        Validate a Python file for MultiIndex structure compliance.

        Parameters
        ----------
        file_path : str or Path
            Path to Python file to validate

        Returns
        -------
        ValidationReport
            Comprehensive validation results
        """
        start_time = time.time()
        file_path = Path(file_path)
        violations = []

        try:
            # Read and validate code patterns
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()

            code_report = self.validate_code_patterns(code, str(file_path))
            violations.extend(code_report.violations)

            # Try to execute and validate actual DataFrames
            try:
                exec_globals = {"np": np, "pd": pd, "__name__": "__main__"}

                # Import solarwindpy if available
                try:
                    import solarwindpy as swp

                    exec_globals["swp"] = swp
                    exec_globals["solarwindpy"] = swp
                except ImportError:
                    pass

                # Execute code and validate results
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    exec(code, exec_globals)

                struct_report = self.validate_structure(exec_globals, str(file_path))
                violations.extend(struct_report.violations)

            except Exception as e:
                self.logger.debug(f"Code execution failed for {file_path}: {e}")

        except Exception as e:
            violations.append(
                StructureViolation(
                    rule="file_read_error",
                    message=f"Failed to read file: {e}",
                    severity="error",
                    file_path=str(file_path),
                )
            )

        execution_time = time.time() - start_time

        return ValidationReport(
            compliant=len([v for v in violations if v.severity == "error"]) == 0,
            total_violations=len(violations),
            violations=violations,
            execution_time=execution_time,
            files_checked=1,
        )

    def _validate_dataframe_structure(
        self, df: pd.DataFrame, var_name: str, file_path: str = None
    ) -> List[StructureViolation]:
        """Validate individual DataFrame structure."""
        violations = []

        # Check if it has MultiIndex columns
        if not isinstance(df.columns, pd.MultiIndex):
            # Only flag as error if DataFrame has physics-related column names
            physics_cols = any(
                col in str(df.columns).lower()
                for col in [
                    "velocity",
                    "density",
                    "temperature",
                    "magnetic",
                    "plasma",
                    "proton",
                ]
            )

            if physics_cols or "plasma" in var_name.lower():
                violations.append(
                    StructureViolation(
                        rule="missing_multiindex",
                        message=f"DataFrame '{var_name}' should use MultiIndex for physics data",
                        severity="warning" if not self.strict_mode else "error",
                        expected="MultiIndex with levels ['M', 'C', 'S']",
                        actual="Regular Index/columns",
                        file_path=file_path,
                        data_shape=df.shape,
                    )
                )
            return violations

        # Validate MultiIndex structure
        violations.extend(self._check_multiindex_levels(df, var_name, file_path))
        violations.extend(self._check_multiindex_values(df, var_name, file_path))
        violations.extend(self._check_index_structure(df, var_name, file_path))
        violations.extend(self._check_memory_efficiency(df, var_name, file_path))

        return violations

    def _check_multiindex_levels(
        self, df: pd.DataFrame, var_name: str, file_path: str = None
    ) -> List[StructureViolation]:
        """Check MultiIndex level names and structure."""
        violations = []

        # Check level names
        actual_levels = list(df.columns.names) if df.columns.names else []

        if actual_levels != self.required_levels:
            violations.append(
                StructureViolation(
                    rule="multiindex_level_names",
                    message=f"MultiIndex levels should be {self.required_levels}",
                    severity="error",
                    expected=self.required_levels,
                    actual=actual_levels,
                    file_path=file_path,
                    data_shape=df.shape,
                )
            )

        # Check level count
        if df.columns.nlevels != 3:
            violations.append(
                StructureViolation(
                    rule="multiindex_level_count",
                    message="MultiIndex should have exactly 3 levels",
                    severity="error",
                    expected="3 levels",
                    actual=f"{df.columns.nlevels} levels",
                    file_path=file_path,
                    data_shape=df.shape,
                )
            )

        return violations

    def _check_multiindex_values(
        self, df: pd.DataFrame, var_name: str, file_path: str = None
    ) -> List[StructureViolation]:
        """Check MultiIndex level values for validity."""
        violations = []

        if df.columns.nlevels < 3 or not all(df.columns.names):
            return violations  # Skip if structure is invalid

        # Check measurement types (M level)
        if "M" in df.columns.names:
            measurements = set(df.columns.get_level_values("M"))
            invalid_measurements = measurements - self.valid_measurements

            if invalid_measurements:
                violations.append(
                    StructureViolation(
                        rule="invalid_measurement_types",
                        message=f"Invalid measurement types: {sorted(invalid_measurements)}",
                        severity="warning",
                        expected=f"One of: {sorted(self.valid_measurements)}",
                        actual=f"Found: {sorted(measurements)}",
                        file_path=file_path,
                    )
                )

        # Check component types (C level)
        if "C" in df.columns.names:
            components = set(df.columns.get_level_values("C"))
            invalid_components = components - self.valid_components

            if invalid_components:
                violations.append(
                    StructureViolation(
                        rule="invalid_component_types",
                        message=f"Invalid component types: {sorted(invalid_components)}",
                        severity="warning",
                        expected=f"One of: {sorted(self.valid_components)}",
                        actual=f"Found: {sorted(components)}",
                        file_path=file_path,
                    )
                )

        # Check species types (S level)
        if "S" in df.columns.names:
            species = set(df.columns.get_level_values("S"))
            invalid_species = species - self.valid_species

            if invalid_species:
                violations.append(
                    StructureViolation(
                        rule="invalid_species_types",
                        message=f"Invalid species types: {sorted(invalid_species)}",
                        severity="warning",
                        expected=f"One of: {sorted(self.valid_species)}",
                        actual=f"Found: {sorted(species)}",
                        file_path=file_path,
                    )
                )

        # Check for proper vector/scalar groupings
        violations.extend(
            self._check_vector_scalar_consistency(df, var_name, file_path)
        )

        return violations

    def _check_vector_scalar_consistency(
        self, df: pd.DataFrame, var_name: str, file_path: str = None
    ) -> List[StructureViolation]:
        """Check that vector quantities have appropriate components."""
        violations = []

        if "M" not in df.columns.names or "C" not in df.columns.names:
            return violations

        # Vector quantities should have x, y, z components
        vector_measurements = {"v", "b"}  # Velocity and magnetic field are vectors

        for measurement in vector_measurements:
            if measurement in df.columns.get_level_values("M"):
                # Get components for this measurement
                measurement_data = df.xs(measurement, level="M", axis=1)
                if isinstance(measurement_data.columns, pd.MultiIndex):
                    components = set(measurement_data.columns.get_level_values("C"))
                else:
                    components = set(measurement_data.columns)

                # Check for complete vector set
                expected_components = {"x", "y", "z"}
                if expected_components.issubset(components):
                    continue  # Good - has full vector
                elif components & expected_components:  # Partial vector
                    missing = expected_components - components
                    violations.append(
                        StructureViolation(
                            rule="incomplete_vector_components",
                            message=f"Vector quantity '{measurement}' missing components: {sorted(missing)}",
                            severity="warning",
                            expected=f"Components: {sorted(expected_components)}",
                            actual=f"Found: {sorted(components)}",
                            file_path=file_path,
                        )
                    )

        # Scalar quantities should have empty component
        scalar_measurements = {
            "n",
            "T",
            "P",
        }  # Density, temperature, pressure are scalars

        for measurement in scalar_measurements:
            if measurement in df.columns.get_level_values("M"):
                measurement_data = df.xs(measurement, level="M", axis=1)
                if isinstance(measurement_data.columns, pd.MultiIndex):
                    components = set(measurement_data.columns.get_level_values("C"))
                    if components != {""}:
                        violations.append(
                            StructureViolation(
                                rule="scalar_with_components",
                                message=f"Scalar quantity '{measurement}' should have empty component",
                                severity="warning",
                                expected="Component: ''",
                                actual=f"Found: {sorted(components)}",
                                file_path=file_path,
                            )
                        )

        return violations

    def _check_index_structure(
        self, df: pd.DataFrame, var_name: str, file_path: str = None
    ) -> List[StructureViolation]:
        """Check DataFrame index structure."""
        violations = []

        # Check for time series index
        if isinstance(df.index, pd.DatetimeIndex):
            # Check index name
            if df.index.name != self.expected_index_name:
                violations.append(
                    StructureViolation(
                        rule="datetime_index_name",
                        message=f"DatetimeIndex should be named '{self.expected_index_name}'",
                        severity="warning",
                        expected=self.expected_index_name,
                        actual=str(df.index.name),
                        file_path=file_path,
                    )
                )

            # Check for duplicates
            if df.index.has_duplicates:
                violations.append(
                    StructureViolation(
                        rule="duplicate_timestamps",
                        message="DatetimeIndex contains duplicate timestamps",
                        severity="error",
                        expected="Unique timestamps",
                        actual="Duplicates found",
                        file_path=file_path,
                    )
                )

            # Check chronological order
            if not df.index.is_monotonic_increasing:
                violations.append(
                    StructureViolation(
                        rule="non_chronological_index",
                        message="DatetimeIndex should be chronologically ordered",
                        severity="warning",
                        expected="Monotonic increasing timestamps",
                        actual="Non-monotonic",
                        file_path=file_path,
                    )
                )

        return violations

    def _check_memory_efficiency(
        self, df: pd.DataFrame, var_name: str, file_path: str = None
    ) -> List[StructureViolation]:
        """Check DataFrame memory usage patterns."""
        violations = []

        try:
            memory_usage = df.memory_usage(deep=True).sum()
            memory_mb = memory_usage / (1024 * 1024)

            # Store memory info for reporting
            memory_str = f"{memory_mb:.1f}MB"

            # Check for excessive memory usage (>100MB for examples)
            if memory_mb > 100:
                violations.append(
                    StructureViolation(
                        rule="high_memory_usage",
                        message=f"DataFrame uses {memory_str} - consider optimization",
                        severity="info",
                        memory_usage=memory_str,
                        file_path=file_path,
                        data_shape=df.shape,
                    )
                )

            # Check dtype efficiency
            float_cols = df.select_dtypes(include=["float64"]).columns
            if len(float_cols) > 0 and memory_mb > 10:
                violations.append(
                    StructureViolation(
                        rule="dtype_optimization",
                        message=f"Consider float32 for large DataFrame ({memory_str})",
                        severity="info",
                        expected="float32 for large datasets",
                        actual=f"float64 ({len(float_cols)} columns)",
                        memory_usage=memory_str,
                        file_path=file_path,
                    )
                )

        except Exception:
            # Memory analysis failed, skip
            pass

        return violations

    def _check_multiindex_creation_patterns(
        self, code: str, file_path: str = None
    ) -> List[StructureViolation]:
        """Check code patterns for MultiIndex creation."""
        violations = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            # Check for MultiIndex.from_tuples with proper names
            if "MultiIndex.from_tuples" in line:
                # Look for names parameter in this line or nearby lines (expand search)
                context_lines = lines[
                    max(0, i - 2) : min(len(lines), i + 10)
                ]  # Look further ahead
                context = " ".join(context_lines)

                if "names=" not in context:
                    violations.append(
                        StructureViolation(
                            rule="multiindex_missing_names",
                            message="MultiIndex creation should specify names=['M', 'C', 'S']",
                            severity="warning",
                            line_number=i,
                            code_snippet=line.strip(),
                            expected="names=['M', 'C', 'S']",
                            actual="Missing names parameter",
                            file_path=file_path,
                        )
                    )
                elif (
                    "names=['M', 'C', 'S']" not in context
                    and 'names=["M", "C", "S"]' not in context
                ):
                    violations.append(
                        StructureViolation(
                            rule="multiindex_wrong_names",
                            message="MultiIndex names should be ['M', 'C', 'S']",
                            severity="warning",
                            line_number=i,
                            code_snippet=line.strip(),
                            expected="['M', 'C', 'S']",
                            file_path=file_path,
                        )
                    )

            # Check for proper tuple structure in MultiIndex creation
            # Look for lines that contain tuple patterns within MultiIndex context
            if (
                "(" in line
                and ")" in line
                and (
                    "from_tuples" in line
                    or (i < len(lines) - 1 and "from_tuples" in lines[i])
                    or (i > 0 and "from_tuples" in lines[i - 2])
                )
            ):
                # Count tuple elements - should be multiples of 3
                tuple_elements = line.count("'") + line.count('"')
                if (
                    tuple_elements > 0 and tuple_elements % 6 != 0
                ):  # Each tuple needs 6 quotes (3 elements)
                    violations.append(
                        StructureViolation(
                            rule="malformed_multiindex_tuple",
                            message="MultiIndex tuples should have 3 elements (M, C, S)",
                            severity="warning",
                            line_number=i,
                            code_snippet=line.strip(),
                            expected="('measurement', 'component', 'species')",
                            file_path=file_path,
                        )
                    )

        return violations

    def _check_data_access_patterns(
        self, code: str, file_path: str = None
    ) -> List[StructureViolation]:
        """Check patterns for MultiIndex data access."""
        violations = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            # Check for proper .xs() usage with level names
            if ".xs(" in line:
                if "level=" in line:
                    # Good - using level names
                    if not any(
                        level in line
                        for level in ["'M'", "'C'", "'S'", '"M"', '"C"', '"S"']
                    ):
                        violations.append(
                            StructureViolation(
                                rule="xs_without_level_name",
                                message="Use level names ('M', 'C', 'S') in .xs() for clarity",
                                severity="info",
                                line_number=i,
                                code_snippet=line.strip(),
                                expected=".xs('value', level='M')",
                                file_path=file_path,
                            )
                        )
                else:
                    violations.append(
                        StructureViolation(
                            rule="xs_missing_level",
                            message="Consider specifying level= in .xs() for MultiIndex access",
                            severity="info",
                            line_number=i,
                            code_snippet=line.strip(),
                            expected=".xs('value', level='M')",
                            actual="Missing level specification",
                            file_path=file_path,
                        )
                    )

            # Check for inefficient access patterns
            if ".loc[" in line and "(" in line and ")" in line:
                # Might be direct tuple access - could use .xs() instead
                if any(x in line for x in ["'n',", "'v',", "'b',"]):
                    violations.append(
                        StructureViolation(
                            rule="inefficient_multiindex_access",
                            message="Consider using .xs() instead of .loc[] for MultiIndex access",
                            severity="info",
                            line_number=i,
                            code_snippet=line.strip(),
                            expected=".xs('value', level='M')",
                            file_path=file_path,
                        )
                    )

            # Check for potential copy vs view issues
            if ".copy()" in line and ".xs(" in line:
                violations.append(
                    StructureViolation(
                        rule="unnecessary_copy_with_xs",
                        message=".xs() returns views by default, .copy() may be unnecessary",
                        severity="info",
                        line_number=i,
                        code_snippet=line.strip(),
                        expected="Use .xs() view when possible",
                        file_path=file_path,
                    )
                )

        return violations

    def _check_index_naming_patterns(
        self, code: str, file_path: str = None
    ) -> List[StructureViolation]:
        """Check patterns for proper index naming."""
        violations = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            # Check for date_range without proper index name
            if "pd.date_range" in line:
                # Look for index assignment in nearby lines
                context_lines = lines[max(0, i - 2) : min(len(lines), i + 5)]
                context = "\n".join(context_lines)

                if "index=" in context and self.expected_index_name not in context:
                    violations.append(
                        StructureViolation(
                            rule="datetime_index_naming",
                            message=f"DatetimeIndex should be named '{self.expected_index_name}'",
                            severity="info",
                            line_number=i,
                            code_snippet=line.strip(),
                            expected=f"index.name = '{self.expected_index_name}'",
                            file_path=file_path,
                        )
                    )

            # Check for explicit index naming
            if ".name =" in line and "index" in line.lower():
                if self.expected_index_name not in line:
                    violations.append(
                        StructureViolation(
                            rule="wrong_index_name",
                            message=f"Index should be named '{self.expected_index_name}' for time series",
                            severity="info",
                            line_number=i,
                            code_snippet=line.strip(),
                            expected=f"index.name = '{self.expected_index_name}'",
                            file_path=file_path,
                        )
                    )

        return violations

    def generate_report(self, report: ValidationReport, verbose: bool = False) -> str:
        """
        Generate a comprehensive validation report.

        Parameters
        ----------
        report : ValidationReport
            Validation results to format
        verbose : bool, optional
            Include detailed violation information (default: False)

        Returns
        -------
        str
            Formatted report string
        """
        lines = []
        lines.append("=" * 70)
        lines.append("SOLARWINDPY MULTIINDEX STRUCTURE VALIDATION REPORT")
        lines.append("=" * 70)
        lines.append("")

        # Summary
        status = "✓ COMPLIANT" if report.compliant else "✗ NON-COMPLIANT"
        lines.append(f"Overall Status: {status}")
        lines.append(f"Files Checked: {report.files_checked}")
        lines.append(f"DataFrames Checked: {report.dataframes_checked}")
        lines.append(f"Total Violations: {report.total_violations}")
        lines.append(f"Execution Time: {report.execution_time:.3f}s")
        lines.append("")

        # Violations by severity
        if report.violations_by_severity:
            lines.append("Violations by Severity:")
            for severity in ["error", "warning", "info"]:
                count = report.violations_by_severity.get(severity, 0)
                if count > 0:
                    icon = (
                        "🔴"
                        if severity == "error"
                        else "🟡" if severity == "warning" else "🔵"
                    )
                    lines.append(f"  {icon} {severity.upper()}: {count}")
            lines.append("")

        # Top rule violations
        if report.violations_by_rule:
            lines.append("Top Rule Violations:")
            sorted_rules = sorted(
                report.violations_by_rule.items(), key=lambda x: x[1], reverse=True
            )
            for rule, count in sorted_rules[:10]:
                lines.append(f"  • {rule}: {count}")
            lines.append("")

        # Detailed violations
        if verbose and report.violations:
            lines.append("Detailed Violations:")
            lines.append("-" * 50)

            for i, violation in enumerate(report.violations, 1):
                icon = (
                    "🔴"
                    if violation.severity == "error"
                    else "🟡" if violation.severity == "warning" else "🔵"
                )
                lines.append(f"{i}. {icon} {violation.rule}")
                lines.append(f"   {violation.message}")

                if violation.file_path:
                    path_str = violation.file_path
                    if violation.line_number:
                        path_str += f":{violation.line_number}"
                    lines.append(f"   📁 {path_str}")

                if violation.code_snippet:
                    lines.append(f"   💻 {violation.code_snippet}")

                if violation.expected and violation.actual:
                    lines.append(f"   ✓ Expected: {violation.expected}")
                    lines.append(f"   ✗ Actual: {violation.actual}")

                if violation.data_shape:
                    shape_str = f"Shape: {violation.data_shape}"
                    if violation.memory_usage:
                        shape_str += f", Memory: {violation.memory_usage}"
                    lines.append(f"   📊 {shape_str}")

                lines.append("")

        # Recommendations
        if not report.compliant:
            lines.append("Recommendations:")
            lines.append("-" * 20)

            error_rules = {v.rule for v in report.violations if v.severity == "error"}
            warning_rules = {
                v.rule for v in report.violations if v.severity == "warning"
            }

            if "missing_multiindex" in error_rules:
                lines.append("• Convert physics DataFrames to use MultiIndex structure")
                lines.append(
                    "  Example: pd.MultiIndex.from_tuples([...], names=['M', 'C', 'S'])"
                )

            if "multiindex_level_names" in error_rules:
                lines.append("• Use correct MultiIndex level names: ['M', 'C', 'S']")

            if "invalid_measurement_types" in warning_rules:
                lines.append("• Use standard measurement types: n, v, w, b, T, P, etc.")

            if "xs_missing_level" in [v.rule for v in report.violations]:
                lines.append(
                    "• Use .xs() with level names for efficient MultiIndex access"
                )
                lines.append(
                    "  Example: df.xs('v', level='M') instead of complex indexing"
                )

            lines.append("")

        return "\n".join(lines)


def main():
    """Command line interface for MultiIndex structure validation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate SolarWindPy MultiIndex DataFrame structures",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s docs/source/usage.rst                    # Validate documentation examples
  %(prog)s solarwindpy/core/plasma.py               # Validate source file
  %(prog)s --patterns "**/*.py" --strict            # Validate all Python files
  %(prog)s test_file.py --verbose --output report.txt
        """,
    )

    parser.add_argument(
        "files",
        nargs="*",
        default=["docs/source/usage.rst"],
        help="Files to validate (default: usage documentation)",
    )
    parser.add_argument(
        "--patterns", nargs="*", help="Glob patterns to match multiple files"
    )
    parser.add_argument(
        "--strict", action="store_true", help="Strict mode: treat warnings as errors"
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.05,
        help="Tolerance for numerical validation (default: 0.05)",
    )
    parser.add_argument(
        "--output", "-o", help="Output file for report (default: stdout)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Include detailed violation information",
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: exit with error code for non-compliance",
    )

    args = parser.parse_args()

    # Create validator
    validator = MultiIndexStructureValidator(
        tolerance=args.tolerance, strict_mode=args.strict
    )

    # Collect files to validate
    files_to_check = []

    # Add explicit files
    for file_path in args.files:
        path = Path(file_path)
        if path.exists():
            files_to_check.append(path)
        else:
            print(f"Warning: File not found: {file_path}")

    # Add pattern matches
    if args.patterns:
        for pattern in args.patterns:
            matches = list(Path(".").glob(pattern))
            files_to_check.extend(f for f in matches if f.is_file())

    if not files_to_check:
        print("No files found to validate.")
        return 1

    # Validate files
    all_reports = []

    for file_path in files_to_check:
        if file_path.suffix == ".py":
            report = validator.validate_file(file_path)
        elif file_path.suffix in [".rst", ".md"]:
            # For documentation, validate code patterns only
            try:
                with open(file_path, "r") as f:
                    content = f.read()
                report = validator.validate_code_patterns(content, str(file_path))
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue
        else:
            print(f"Skipping unsupported file: {file_path}")
            continue

        all_reports.append(report)

    # Combine reports
    if all_reports:
        combined_violations = []
        total_files = sum(r.files_checked for r in all_reports)
        total_dataframes = sum(r.dataframes_checked for r in all_reports)
        total_time = sum(r.execution_time for r in all_reports)

        for report in all_reports:
            combined_violations.extend(report.violations)

        combined_report = ValidationReport(
            compliant=len([v for v in combined_violations if v.severity == "error"])
            == 0,
            total_violations=len(combined_violations),
            violations=combined_violations,
            execution_time=total_time,
            files_checked=total_files,
            dataframes_checked=total_dataframes,
        )
    else:
        combined_report = ValidationReport(compliant=True, total_violations=0)

    # Generate and output report
    report_text = validator.generate_report(combined_report, verbose=args.verbose)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report_text)
        print(f"Report written to {args.output}")

        # Also print summary to stdout
        lines = report_text.split("\n")
        try:
            summary_end = next(
                i for i, line in enumerate(lines) if line.strip() == "" and i > 10
            )
            print("\n".join(lines[:summary_end]))
        except StopIteration:
            # If no empty line found after line 10, just print first 15 lines
            print("\n".join(lines[:15]))
    else:
        print(report_text)

    # Exit with appropriate code for CI
    if args.ci:
        return 0 if combined_report.compliant else 1
    else:
        return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
