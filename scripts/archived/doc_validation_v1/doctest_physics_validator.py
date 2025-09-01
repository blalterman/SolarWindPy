"""
Enhanced doctest execution with integrated physics rule validation.

This module provides a custom doctest runner that validates physics
calculations and data structure compliance during doctest execution,
ensuring all examples maintain scientific accuracy.
"""

import doctest
import sys
import ast
import re
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from io import StringIO
from pathlib import Path
import importlib.util
import warnings
from contextlib import redirect_stdout, redirect_stderr


class PhysicsDocTestRunner(doctest.DocTestRunner):
    """Enhanced doctest runner with physics validation

    This runner extends the standard doctest functionality to include
    physics rule validation, ensuring all docstring examples follow
    SolarWindPy conventions for scientific accuracy and data structure.
    """

    def __init__(self, checker=None, verbose=None, optionflags=0):
        super().__init__(checker, verbose, optionflags)
        self.physics_violations = []
        self.validation_stats = {
            "tests_run": 0,
            "examples_checked": 0,
            "physics_validations": 0,
            "violations_found": 0,
        }

    def run(self, test, compileflags=None, out=None, clear_globs=True):
        """Run doctest with physics validation"""
        if out is None:
            out = StringIO()

        # Standard doctest execution
        result = super().run(test, compileflags, out, clear_globs)

        # Update statistics
        self.validation_stats["tests_run"] += 1
        self.validation_stats["examples_checked"] += len(test.examples)

        # Additional physics validation
        self._validate_physics_in_test(test)

        return result

    def _validate_physics_in_test(self, test):
        """Apply physics rules to test outputs and source code"""
        for example in test.examples:
            self.validation_stats["physics_validations"] += 1

            # Validate source code patterns
            self._validate_source_patterns(example)

            # Validate expected outputs if available
            self._validate_expected_outputs(example)

    def _validate_source_patterns(self, example):
        """Validate physics patterns in source code"""
        source = example.source.strip()

        # Check for thermal speed calculations
        if any(
            term in source for term in ["w_thermal", "thermal_speed", "w_par", "w_per"]
        ):
            self._check_thermal_speed_source(source, example)

        # Check for Alfvén speed calculations
        if any(term in source for term in ["V_A", "alfven", "v_alfven"]):
            self._check_alfven_speed_source(source, example)

        # Check for MultiIndex access patterns
        if "xs(" in source or ".loc[" in source:
            self._check_multiindex_access(source, example)

        # Check for missing data handling
        if any(term in source for term in ["nan", "NaN", "np.nan", "isnan"]):
            self._check_missing_data_patterns(source, example)

    def _check_thermal_speed_source(self, source: str, example):
        """Validate thermal speed calculations in source code"""
        # Look for hardcoded thermal speed values (violation)
        hardcoded_pattern = (
            r"w_thermal\s*=\s*(?:np\.random\.normal\()?([0-9]+\.?[0-9]*)"
        )
        if re.search(hardcoded_pattern, source):
            self.physics_violations.append(
                {
                    "type": "thermal_speed_hardcoded",
                    "message": "Thermal speed should be calculated from temperature using mw² = 2kT",
                    "source": source,
                    "line": getattr(example, "lineno", "unknown"),
                }
            )
            self.validation_stats["violations_found"] += 1

        # Check for proper thermal speed formula
        formula_indicators = ["sqrt(2", "k_B", "m_p", "/ m_p"]
        if any(indicator in source for indicator in formula_indicators):
            # Good - using proper physics formula
            pass
        elif "w_thermal" in source or "thermal_speed" in source:
            # Potential issue - thermal speed without proper calculation
            if not any(calc in source for calc in ["sqrt", "temperature", "T_p"]):
                self.physics_violations.append(
                    {
                        "type": "thermal_speed_missing_calculation",
                        "message": "Thermal speed should be calculated from temperature",
                        "source": source,
                        "line": getattr(example, "lineno", "unknown"),
                    }
                )
                self.validation_stats["violations_found"] += 1

    def _check_alfven_speed_source(self, source: str, example):
        """Validate Alfvén speed calculations"""
        # Check for missing μ₀ (permeability)
        if "V_A" in source or "alfven" in source:
            if "mu_0" not in source and "4 * np.pi * 1e-7" not in source:
                self.physics_violations.append(
                    {
                        "type": "alfven_missing_permeability",
                        "message": "Alfvén speed calculation missing μ₀ permeability term",
                        "source": source,
                        "line": getattr(example, "lineno", "unknown"),
                    }
                )
                self.validation_stats["violations_found"] += 1

    def _check_multiindex_access(self, source: str, example):
        """Validate MultiIndex access patterns"""
        # Check for inefficient .loc usage
        if ".loc[" in source and "xs(" not in source:
            # Suggest .xs() for better performance
            self.physics_violations.append(
                {
                    "type": "multiindex_inefficient_access",
                    "message": "Consider using .xs() for more efficient MultiIndex access",
                    "source": source,
                    "line": getattr(example, "lineno", "unknown"),
                    "severity": "info",
                }
            )

        # Check for level specification in .xs()
        xs_pattern = r"\.xs\([^)]+\)"
        xs_matches = re.findall(xs_pattern, source)
        for match in xs_matches:
            if "level=" not in match:
                self.physics_violations.append(
                    {
                        "type": "multiindex_missing_level",
                        "message": "Specify level parameter in .xs() for clarity",
                        "source": source,
                        "line": getattr(example, "lineno", "unknown"),
                        "severity": "info",
                    }
                )

    def _check_missing_data_patterns(self, source: str, example):
        """Validate missing data handling patterns"""
        # Check for bad fill values
        bad_fills = ["-999", "9999", "-9999", "999999"]
        for fill in bad_fills:
            if fill in source:
                self.physics_violations.append(
                    {
                        "type": "missing_data_bad_fill",
                        "message": f"Use np.nan instead of {fill} for missing data",
                        "source": source,
                        "line": getattr(example, "lineno", "unknown"),
                    }
                )
                self.validation_stats["violations_found"] += 1

    def _validate_expected_outputs(self, example):
        """Validate expected outputs for physics compliance"""
        want = example.want.strip()

        if not want:
            return

        # Check for DataFrame structure indicators
        if "DataFrame" in want or "MultiIndex" in want:
            self._validate_dataframe_output(want, example)

        # Check for numerical values that should follow physics rules
        if any(term in want for term in ["thermal_speed", "w_par", "w_per"]):
            self._validate_thermal_speed_output(want, example)

    def _validate_dataframe_output(self, output: str, example):
        """Validate DataFrame output structure"""
        # Check for proper MultiIndex naming
        if "names=['M', 'C', 'S']" not in output and "MultiIndex" in output:
            self.physics_violations.append(
                {
                    "type": "multiindex_missing_names",
                    "message": "MultiIndex should have names=['M', 'C', 'S']",
                    "source": example.source,
                    "output": output,
                    "line": getattr(example, "lineno", "unknown"),
                    "severity": "warning",
                }
            )

    def _validate_thermal_speed_output(self, output: str, example):
        """Validate thermal speed values in output"""
        # Extract numerical values from output
        number_pattern = r"[-+]?(?:\d*\.)?\d+(?:[eE][-+]?\d+)?"
        numbers = re.findall(number_pattern, output)

        # Check if thermal speeds are in realistic ranges
        for num_str in numbers:
            try:
                value = float(num_str)
                # Thermal speeds typically 10-100 km/s for solar wind protons
                if "thermal" in output.lower() and (value < 5 or value > 200):
                    self.physics_violations.append(
                        {
                            "type": "thermal_speed_unrealistic",
                            "message": f"Thermal speed {value} km/s outside typical range (10-100 km/s)",
                            "source": example.source,
                            "output": output,
                            "line": getattr(example, "lineno", "unknown"),
                            "severity": "warning",
                        }
                    )
            except ValueError:
                continue


class PhysicsDocTestFinder(doctest.DocTestFinder):
    """Enhanced doctest finder with physics context"""

    def __init__(self, verbose=False, parser=None, recurse=True, exclude_empty=True):
        super().__init__(verbose, parser, recurse, exclude_empty)

    def find(self, obj, name=None, module=None, globs=None, extraglobs=None):
        """Find doctests with physics context annotation"""
        tests = super().find(obj, name, module, globs, extraglobs)

        # Annotate tests with physics context
        for test in tests:
            test.physics_context = self._extract_physics_context(test)

        return tests

    def _extract_physics_context(self, test) -> Dict[str, Any]:
        """Extract physics-relevant context from test"""
        context = {
            "has_thermal_calculations": False,
            "has_multiindex_operations": False,
            "has_unit_conversions": False,
            "has_physics_constants": False,
        }

        for example in test.examples:
            source = example.source

            # Check for thermal calculations
            if any(term in source for term in ["thermal", "w_par", "w_per", "sqrt(2"]):
                context["has_thermal_calculations"] = True

            # Check for MultiIndex operations
            if any(term in source for term in ["xs(", "MultiIndex", "level="]):
                context["has_multiindex_operations"] = True

            # Check for unit conversions
            if any(term in source for term in ["* 1e", "/ 1000", "convert"]):
                context["has_unit_conversions"] = True

            # Check for physics constants
            if any(term in source for term in ["k_B", "m_p", "mu_0", "Constants"]):
                context["has_physics_constants"] = True

        return context


def run_enhanced_doctests(
    module_path: str, verbose: bool = False, physics_validation: bool = True
) -> Dict[str, Any]:
    """Run doctests with enhanced physics validation

    Parameters
    ----------
    module_path : str
        Path to Python module or directory to test
    verbose : bool, optional
        Enable verbose output (default: False)
    physics_validation : bool, optional
        Enable physics rule validation (default: True)

    Returns
    -------
    Dict[str, Any]
        Comprehensive test results including physics violations
    """
    path = Path(module_path)

    if path.is_dir():
        return run_doctests_on_directory(path, verbose, physics_validation)
    else:
        return run_doctests_on_file(path, verbose, physics_validation)


def run_doctests_on_file(
    file_path: Path, verbose: bool = False, physics_validation: bool = True
) -> Dict[str, Any]:
    """Run doctests on a single file"""
    finder = PhysicsDocTestFinder()
    runner = PhysicsDocTestRunner(verbose=verbose)

    results = {
        "file": str(file_path),
        "tests_attempted": 0,
        "tests_failed": 0,
        "examples_run": 0,
        "physics_violations": [],
        "validation_stats": {},
        "success": True,
        "errors": [],
    }

    try:
        # Import the module
        if file_path.suffix == ".py":
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            module = importlib.util.module_from_spec(spec)

            # Suppress warnings during import
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore")
                spec.loader.exec_module(module)

            # Find and run doctests
            tests = finder.find(module)

            for test in tests:
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore")
                    result = runner.run(test)

                results["tests_attempted"] += result.attempted
                results["tests_failed"] += result.failed
                results["examples_run"] += len(test.examples)

        # Collect physics violations
        if physics_validation:
            results["physics_violations"] = runner.physics_violations
            results["validation_stats"] = runner.validation_stats

        results["success"] = (
            results["tests_failed"] == 0 and len(results["physics_violations"]) == 0
        )

    except Exception as e:
        results["success"] = False
        results["errors"].append(str(e))

    return results


def run_doctests_on_directory(
    directory: Path, verbose: bool = False, physics_validation: bool = True
) -> Dict[str, Any]:
    """Run doctests on all Python files in a directory"""
    results = {
        "directory": str(directory),
        "files_processed": 0,
        "total_tests_attempted": 0,
        "total_tests_failed": 0,
        "total_examples_run": 0,
        "total_physics_violations": 0,
        "file_results": [],
        "overall_success": True,
        "summary": {},
    }

    # Find all Python files
    python_files = list(directory.rglob("*.py"))

    for py_file in python_files:
        # Skip __pycache__ and other system files
        if "__pycache__" in str(py_file) or py_file.name.startswith("."):
            continue

        file_results = run_doctests_on_file(py_file, verbose, physics_validation)
        results["file_results"].append(file_results)
        results["files_processed"] += 1

        # Accumulate statistics
        results["total_tests_attempted"] += file_results["tests_attempted"]
        results["total_tests_failed"] += file_results["tests_failed"]
        results["total_examples_run"] += file_results["examples_run"]
        results["total_physics_violations"] += len(file_results["physics_violations"])

        if not file_results["success"]:
            results["overall_success"] = False

    # Generate summary
    results["summary"] = {
        "success_rate": (
            (results["total_tests_attempted"] - results["total_tests_failed"])
            / max(results["total_tests_attempted"], 1)
            * 100
        ),
        "physics_compliance_rate": (
            (results["total_examples_run"] - results["total_physics_violations"])
            / max(results["total_examples_run"], 1)
            * 100
        ),
        "files_with_violations": sum(
            1 for fr in results["file_results"] if len(fr["physics_violations"]) > 0
        ),
    }

    return results


def generate_doctest_report(
    results: Dict[str, Any], output_file: Optional[str] = None
) -> str:
    """Generate human-readable report from doctest results

    Parameters
    ----------
    results : Dict[str, Any]
        Results from run_enhanced_doctests
    output_file : str, optional
        File to save the report to

    Returns
    -------
    str
        Formatted report text
    """
    report_lines = ["SolarWindPy Doctest Physics Validation Report", "=" * 45, ""]

    # Overall summary
    if "directory" in results:
        # Directory results
        report_lines.extend(
            [
                f"Directory: {results['directory']}",
                f"Files processed: {results['files_processed']}",
                f"Total tests: {results['total_tests_attempted']}",
                f"Failed tests: {results['total_tests_failed']}",
                f"Examples run: {results['total_examples_run']}",
                f"Physics violations: {results['total_physics_violations']}",
                f"Success rate: {results['summary']['success_rate']:.1f}%",
                f"Physics compliance: {results['summary']['physics_compliance_rate']:.1f}%",
                "",
            ]
        )

        # File-by-file breakdown
        if results["file_results"]:
            report_lines.append("File Results:")
            report_lines.append("-" * 20)

            for file_result in results["file_results"]:
                status = "✅ PASS" if file_result["success"] else "❌ FAIL"
                report_lines.append(
                    f"{status} {file_result['file']} "
                    f"({file_result['tests_attempted']} tests, "
                    f"{len(file_result['physics_violations'])} violations)"
                )
            report_lines.append("")

    else:
        # Single file results
        report_lines.extend(
            [
                f"File: {results['file']}",
                f"Tests attempted: {results['tests_attempted']}",
                f"Tests failed: {results['tests_failed']}",
                f"Examples run: {results['examples_run']}",
                f"Physics violations: {len(results['physics_violations'])}",
                "",
            ]
        )

    # Physics violations details
    all_violations = []
    if "file_results" in results:
        for file_result in results["file_results"]:
            all_violations.extend(file_result["physics_violations"])
    else:
        all_violations = results.get("physics_violations", [])

    if all_violations:
        report_lines.append("Physics Violations:")
        report_lines.append("-" * 20)

        for violation in all_violations:
            severity = violation.get("severity", "error").upper()
            report_lines.extend(
                [
                    f"[{severity}] {violation['type']}",
                    f"  Message: {violation['message']}",
                    f"  Source: {violation['source'][:100]}...",
                    "",
                ]
            )
    else:
        report_lines.append("✅ No physics violations found!")

    report_text = "\n".join(report_lines)

    if output_file:
        with open(output_file, "w") as f:
            f.write(report_text)

    return report_text


def main():
    """Command-line interface for doctest physics validation"""
    import argparse

    parser = argparse.ArgumentParser(description="Run doctests with physics validation")
    parser.add_argument("path", help="Path to Python file or directory to test")
    parser.add_argument("--output-report", help="Output file for JSON results")
    parser.add_argument("--text-report", help="Output file for text report")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "--no-physics", action="store_true", help="Disable physics validation"
    )
    parser.add_argument(
        "--quick-check",
        action="store_true",
        help="Quick validation for pre-commit hooks",
    )

    args = parser.parse_args()

    # Run doctests
    results = run_enhanced_doctests(
        args.path, verbose=args.verbose, physics_validation=not args.no_physics
    )

    # Save JSON results
    if args.output_report:
        with open(args.output_report, "w") as f:
            json.dump(results, f, indent=2)

    # Generate text report
    text_report = generate_doctest_report(results, args.text_report)

    if not args.quick_check:
        print(text_report)

    # Exit code for CI/CD
    if results.get("overall_success", results.get("success", False)):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
