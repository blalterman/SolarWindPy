#!/usr/bin/env python
"""
Docstring coverage analysis for SolarWindPy modules.

This script analyzes the current state of docstring coverage across all
SolarWindPy Python modules and generates comprehensive reports for
enhancement prioritization.
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
import argparse


class DocstringCoverageAnalyzer(ast.NodeVisitor):
    """Analyze docstring coverage in Python modules."""

    def __init__(self, module_path: str):
        """Initialize the analyzer for a specific module.

        Parameters
        ----------
        module_path : str
            Path to the Python module to analyze.
        """
        self.module_path = module_path
        self.stats = {
            "modules": 0,
            "classes": 0,
            "functions": 0,
            "methods": 0,
            "properties": 0,
            "documented_modules": 0,
            "documented_classes": 0,
            "documented_functions": 0,
            "documented_methods": 0,
            "documented_properties": 0,
        }
        self.missing_docs = []
        self.current_class = None

    def visit_Module(self, node):
        """Visit module node and check for module-level docstring."""
        self.stats["modules"] += 1
        if ast.get_docstring(node):
            self.stats["documented_modules"] += 1
        else:
            self.missing_docs.append(
                {"type": "module", "name": self.module_path, "line": 1}
            )
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Visit class definition and check for class docstring."""
        self.stats["classes"] += 1
        if ast.get_docstring(node):
            self.stats["documented_classes"] += 1
        else:
            self.missing_docs.append(
                {
                    "type": "class",
                    "name": node.name,
                    "line": node.lineno,
                    "class": node.name,
                }
            )

        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node):
        """Visit function definition and check for function/method docstring."""
        if self.current_class:
            # This is a method
            self.stats["methods"] += 1
            if ast.get_docstring(node):
                self.stats["documented_methods"] += 1
            else:
                # Skip private methods and special methods (except __init__)
                if not node.name.startswith("_") or node.name == "__init__":
                    self.missing_docs.append(
                        {
                            "type": "method",
                            "name": f"{self.current_class}.{node.name}",
                            "line": node.lineno,
                            "class": self.current_class,
                        }
                    )
        else:
            # This is a function
            self.stats["functions"] += 1
            if ast.get_docstring(node):
                self.stats["documented_functions"] += 1
            else:
                # Skip private functions
                if not node.name.startswith("_"):
                    self.missing_docs.append(
                        {"type": "function", "name": node.name, "line": node.lineno}
                    )

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        """Visit async function definition (treat same as regular function)."""
        self.visit_FunctionDef(node)

    def analyze_properties(self, tree):
        """Analyze property definitions in the AST."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and self.current_class:
                # Check for property decorators
                for decorator in node.decorator_list:
                    if (
                        isinstance(decorator, ast.Name) and decorator.id == "property"
                    ) or (
                        isinstance(decorator, ast.Attribute)
                        and decorator.attr == "property"
                    ):
                        self.stats["properties"] += 1
                        if ast.get_docstring(node):
                            self.stats["documented_properties"] += 1
                        else:
                            self.missing_docs.append(
                                {
                                    "type": "property",
                                    "name": f"{self.current_class}.{node.name}",
                                    "line": node.lineno,
                                    "class": self.current_class,
                                }
                            )


def analyze_module(module_path: Path) -> Tuple[Dict[str, Any], List[Dict]]:
    """Analyze a single Python module for docstring coverage.

    Parameters
    ----------
    module_path : Path
        Path to the Python module file.

    Returns
    -------
    tuple
        Statistics dictionary and list of missing documentation items.
    """
    try:
        with open(module_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(module_path))

        analyzer = DocstringCoverageAnalyzer(str(module_path))
        analyzer.visit(tree)
        analyzer.analyze_properties(tree)

        return analyzer.stats, analyzer.missing_docs
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"Error analyzing {module_path}: {e}")
        return {}, []


def generate_coverage_report(solarwindpy_path: Path) -> None:
    """Generate comprehensive docstring coverage report.

    Parameters
    ----------
    solarwindpy_path : Path
        Path to the solarwindpy package directory.
    """
    print("SolarWindPy Docstring Coverage Analysis")
    print("=" * 50)

    total_stats = {
        "modules": 0,
        "classes": 0,
        "functions": 0,
        "methods": 0,
        "properties": 0,
        "documented_modules": 0,
        "documented_classes": 0,
        "documented_functions": 0,
        "documented_methods": 0,
        "documented_properties": 0,
    }

    all_missing = []
    module_reports = {}

    # Find all Python files
    python_files = list(solarwindpy_path.rglob("*.py"))
    python_files = [f for f in python_files if not f.name.startswith("test_")]

    print(f"Analyzing {len(python_files)} Python modules...\n")

    for py_file in sorted(python_files):
        relative_path = py_file.relative_to(solarwindpy_path.parent)
        stats, missing = analyze_module(py_file)

        if stats:
            # Add to totals
            for key in total_stats:
                total_stats[key] += stats[key]

            # Calculate module coverage
            total_items = (
                stats["modules"]
                + stats["classes"]
                + stats["functions"]
                + stats["methods"]
                + stats["properties"]
            )
            documented_items = (
                stats["documented_modules"]
                + stats["documented_classes"]
                + stats["documented_functions"]
                + stats["documented_methods"]
                + stats["documented_properties"]
            )

            coverage = (
                (documented_items / total_items * 100) if total_items > 0 else 100
            )

            module_reports[str(relative_path)] = {
                "coverage": coverage,
                "stats": stats,
                "missing": missing,
            }

            all_missing.extend(missing)

    # Print summary statistics
    print("Summary Statistics:")
    print("-" * 30)
    total_items = sum(
        total_stats[k]
        for k in ["modules", "classes", "functions", "methods", "properties"]
    )
    total_documented = sum(
        total_stats[k]
        for k in [
            "documented_modules",
            "documented_classes",
            "documented_functions",
            "documented_methods",
            "documented_properties",
        ]
    )

    overall_coverage = (
        (total_documented / total_items * 100) if total_items > 0 else 100
    )

    print(f"Overall Coverage: {overall_coverage:.1f}%")
    print(f"Total Items: {total_items}")
    print(f"Documented Items: {total_documented}")
    print(f"Missing Documentation: {total_items - total_documented}")
    print()

    # Print detailed statistics by type
    for item_type in ["modules", "classes", "functions", "methods", "properties"]:
        total = total_stats[item_type]
        documented = total_stats[f"documented_{item_type}"]
        if total > 0:
            coverage = documented / total * 100
            print(f"{item_type.capitalize()}: {coverage:.1f}% ({documented}/{total})")

    print("\n" + "=" * 50)
    print("Module-by-Module Coverage Report:")
    print("=" * 50)

    # Sort modules by coverage (lowest first)
    sorted_modules = sorted(module_reports.items(), key=lambda x: x[1]["coverage"])

    for module_path, report in sorted_modules:
        coverage = report["coverage"]
        stats = report["stats"]
        missing = report["missing"]

        print(f"\n{module_path}: {coverage:.1f}%")
        if coverage < 100:
            print(f"  Missing documentation:")
            for item in missing:
                print(f"    - {item['type']}: {item['name']} (line {item['line']})")

    # Priority recommendations
    print("\n" + "=" * 50)
    print("Enhancement Priority Recommendations:")
    print("=" * 50)

    high_priority = [m for m, r in module_reports.items() if r["coverage"] < 50]
    medium_priority = [m for m, r in module_reports.items() if 50 <= r["coverage"] < 80]
    low_priority = [m for m, r in module_reports.items() if 80 <= r["coverage"] < 100]

    print(f"\nHIGH PRIORITY (<50% coverage): {len(high_priority)} modules")
    for module in high_priority[:5]:  # Show top 5
        print(f"  - {module}: {module_reports[module]['coverage']:.1f}%")

    print(f"\nMEDIUM PRIORITY (50-80% coverage): {len(medium_priority)} modules")
    for module in medium_priority[:5]:  # Show top 5
        print(f"  - {module}: {module_reports[module]['coverage']:.1f}%")

    print(f"\nLOW PRIORITY (80-100% coverage): {len(low_priority)} modules")


def main():
    """Main entry point for docstring coverage analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze docstring coverage in SolarWindPy"
    )
    parser.add_argument(
        "--path",
        type=str,
        default="solarwindpy",
        help="Path to solarwindpy package (default: solarwindpy)",
    )

    args = parser.parse_args()

    solarwindpy_path = Path(args.path)
    if not solarwindpy_path.exists():
        print(f"Error: Path {solarwindpy_path} does not exist")
        sys.exit(1)

    generate_coverage_report(solarwindpy_path)


if __name__ == "__main__":
    main()
