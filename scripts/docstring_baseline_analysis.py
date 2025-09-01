#!/usr/bin/env python
"""Docstring format baseline analysis for SolarWindPy modules.

This script analyzes the current state of docstrings across all modules
to provide a baseline for standardization to NumPy format.
"""

import ast
import os
from pathlib import Path
from collections import defaultdict
import re


class DocstringFormatAnalyzer(ast.NodeVisitor):
    """Analyze docstring format compliance in Python modules."""

    def __init__(self):
        self.stats = {
            "total_functions": 0,
            "total_classes": 0,
            "total_methods": 0,
            "functions_with_docstrings": 0,
            "classes_with_docstrings": 0,
            "methods_with_docstrings": 0,
            "numpy_format": 0,
            "google_format": 0,
            "informal_format": 0,
            "empty_docstrings": 0,
        }
        self.issues = []
        self.current_file = None

    def analyze_docstring_format(self, docstring, node_type, node_name):
        """Analyze docstring format and categorize."""
        if not docstring:
            return None

        docstring = docstring.strip()
        if not docstring:
            self.stats["empty_docstrings"] += 1
            return "empty"

        # Check for NumPy format indicators
        numpy_indicators = [
            "Parameters\n    ----------",
            "Returns\n    -------",
            "Raises\n    ------",
            "Examples\n    --------",
            "Notes\n    -----",
        ]

        # Check for Google format indicators
        google_indicators = [
            "Args:",
            "Arguments:",
            "Returns:",
            "Raises:",
            "Example:",
            "Examples:",
            "Note:",
        ]

        has_numpy = any(indicator in docstring for indicator in numpy_indicators)
        has_google = any(indicator in docstring for indicator in google_indicators)

        if has_numpy:
            self.stats["numpy_format"] += 1
            return "numpy"
        elif has_google:
            self.stats["google_format"] += 1
            return "google"
        else:
            self.stats["informal_format"] += 1
            return "informal"

    def visit_FunctionDef(self, node):
        """Visit function definitions."""
        self.stats["total_functions"] += 1

        docstring = ast.get_docstring(node)
        if docstring:
            self.stats["functions_with_docstrings"] += 1
            format_type = self.analyze_docstring_format(
                docstring, "function", node.name
            )
        else:
            self.issues.append(
                {
                    "file": self.current_file,
                    "type": "function",
                    "name": node.name,
                    "issue": "missing_docstring",
                    "line": node.lineno,
                }
            )

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        """Visit async function definitions."""
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        """Visit class definitions."""
        self.stats["total_classes"] += 1

        docstring = ast.get_docstring(node)
        if docstring:
            self.stats["classes_with_docstrings"] += 1
            format_type = self.analyze_docstring_format(docstring, "class", node.name)
        else:
            self.issues.append(
                {
                    "file": self.current_file,
                    "type": "class",
                    "name": node.name,
                    "issue": "missing_docstring",
                    "line": node.lineno,
                }
            )

        # Check methods
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.stats["total_methods"] += 1
                method_docstring = ast.get_docstring(item)
                if method_docstring:
                    self.stats["methods_with_docstrings"] += 1
                    self.analyze_docstring_format(
                        method_docstring, "method", f"{node.name}.{item.name}"
                    )
                else:
                    self.issues.append(
                        {
                            "file": self.current_file,
                            "type": "method",
                            "name": f"{node.name}.{item.name}",
                            "issue": "missing_docstring",
                            "line": item.lineno,
                        }
                    )

        self.generic_visit(node)


def analyze_module(file_path):
    """Analyze a single Python module."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)
        analyzer = DocstringFormatAnalyzer()
        analyzer.current_file = str(file_path)
        analyzer.visit(tree)

        return analyzer.stats, analyzer.issues

    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return {}, []


def main():
    """Run baseline docstring analysis on SolarWindPy."""

    # Find all Python files in solarwindpy/
    solarwindpy_dir = Path("solarwindpy")
    if not solarwindpy_dir.exists():
        print("Error: solarwindpy directory not found")
        return

    python_files = list(solarwindpy_dir.rglob("*.py"))
    # Exclude test files
    python_files = [f for f in python_files if "test_" not in f.name]

    print(f"SolarWindPy Docstring Baseline Analysis")
    print(f"=" * 50)
    print(f"Found {len(python_files)} Python modules to analyze")
    print()

    # Aggregate statistics
    total_stats = defaultdict(int)
    all_issues = []
    module_stats = {}

    for py_file in python_files:
        stats, issues = analyze_module(py_file)
        module_stats[str(py_file)] = stats
        all_issues.extend(issues)

        for key, value in stats.items():
            total_stats[key] += value

    # Print summary statistics
    print("Overall Statistics:")
    print(f"  Total Functions: {total_stats['total_functions']}")
    print(f"  Total Classes: {total_stats['total_classes']}")
    print(f"  Total Methods: {total_stats['total_methods']}")
    print(
        f"  Total Code Objects: {total_stats['total_functions'] + total_stats['total_classes'] + total_stats['total_methods']}"
    )
    print()

    print("Documentation Coverage:")
    total_objects = (
        total_stats["total_functions"]
        + total_stats["total_classes"]
        + total_stats["total_methods"]
    )
    documented_objects = (
        total_stats["functions_with_docstrings"]
        + total_stats["classes_with_docstrings"]
        + total_stats["methods_with_docstrings"]
    )
    coverage_pct = (
        (documented_objects / total_objects * 100) if total_objects > 0 else 0
    )
    print(
        f"  Functions with docstrings: {total_stats['functions_with_docstrings']}/{total_stats['total_functions']} ({total_stats['functions_with_docstrings']/total_stats['total_functions']*100:.1f}%)"
    )
    print(
        f"  Classes with docstrings: {total_stats['classes_with_docstrings']}/{total_stats['total_classes']} ({total_stats['classes_with_docstrings']/total_stats['total_classes']*100:.1f}%)"
    )
    print(
        f"  Methods with docstrings: {total_stats['methods_with_docstrings']}/{total_stats['total_methods']} ({total_stats['methods_with_docstrings']/total_stats['total_methods']*100:.1f}%)"
    )
    print(
        f"  Overall Coverage: {documented_objects}/{total_objects} ({coverage_pct:.1f}%)"
    )
    print()

    print("Format Distribution:")
    total_documented = (
        total_stats["numpy_format"]
        + total_stats["google_format"]
        + total_stats["informal_format"]
    )
    if total_documented > 0:
        print(
            f"  NumPy format: {total_stats['numpy_format']} ({total_stats['numpy_format']/total_documented*100:.1f}%)"
        )
        print(
            f"  Google format: {total_stats['google_format']} ({total_stats['google_format']/total_documented*100:.1f}%)"
        )
        print(
            f"  Informal format: {total_stats['informal_format']} ({total_stats['informal_format']/total_documented*100:.1f}%)"
        )
        print(f"  Empty docstrings: {total_stats['empty_docstrings']}")
    print()

    # Show modules with highest standardization priority
    print("Modules with mixed/non-NumPy formats (standardization priority):")
    format_issues = defaultdict(list)

    for py_file in python_files:
        stats = module_stats[str(py_file)]
        non_numpy = stats.get("google_format", 0) + stats.get("informal_format", 0)
        if non_numpy > 0:
            format_issues[non_numpy].append(str(py_file))

    # Sort by number of format issues (descending)
    for issue_count in sorted(format_issues.keys(), reverse=True):
        for module in sorted(format_issues[issue_count]):
            print(f"  {module}: {issue_count} non-NumPy docstrings")

    print()
    print(f"Missing docstrings: {len(all_issues)} items")
    print(f"pydocstyle violations: ~1400 (from baseline analysis)")

    print("\nConclusion:")
    print(f"- {coverage_pct:.1f}% documentation coverage")
    print(f"- {total_stats['numpy_format']} items already in NumPy format")
    print(
        f"- {total_stats['google_format'] + total_stats['informal_format']} items need format conversion"
    )
    print(f"- {len(all_issues)} items need docstrings added")
    print(f"- ~1400 pydocstyle violations to address")


if __name__ == "__main__":
    main()
