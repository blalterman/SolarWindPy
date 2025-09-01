#!/usr/bin/env python
"""
Custom docstring validation framework for SolarWindPy.

This script provides advanced validation for scientific computing requirements
beyond standard pydocstyle checks, including physics-specific validation.
"""

import ast
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import argparse


class SolarWindPyDocstringValidator:
    """Custom docstring validation for scientific computing requirements."""

    # Required sections for different component types
    REQUIRED_SECTIONS = {
        "functions": ["Parameters", "Returns"],
        "methods": ["Parameters", "Returns"],
        "classes": ["Parameters", "Attributes"],
        "properties": ["Returns"],
    }

    # Scientific documentation requirements
    SCIENTIFIC_REQUIREMENTS = {
        "units_documentation": True,
        "latex_equations": True,
        "literature_references": True,
        "example_code": True,
    }

    # Common physics units patterns
    PHYSICS_UNITS = {
        r"\bm/s\b",
        r"\bkm/s\b",
        r"\bm\^2/s\b",
        r"\bkg\b",
        r"\bK\b",
        r"\bnT\b",
        r"\bmT\b",
        r"\bT\b",
        r"\bcm\^-3\b",
        r"\b1/cc\b",
        r"\beV\b",
        r"\bkeV\b",
        r"\bJ\b",
        r"\bPa\b",
        r"\bN/m\^2\b",
        r"\brad\b",
        r"\bdeg\b",
        r"\bs\b",
        r"\bmin\b",
        r"\bh\b",
        r"\bAU\b",
        r"\bkm\b",
        r"\bm\b",
        r"\bcm\b",
        r"\bmm\b",
    }

    # LaTeX equation patterns
    LATEX_PATTERNS = {
        r"\$[^$]+\$",  # Inline math: $equation$
        r"\$\$[^$]+\$\$",  # Display math: $$equation$$
        r"\\[a-zA-Z]+{[^}]*}",  # LaTeX commands: \command{content}
        r"\\[a-zA-Z]+",  # LaTeX commands: \command
        r"\^{[^}]+}",  # Superscripts: ^{content}
        r"_{[^}]+}",  # Subscripts: _{content}
    }

    def __init__(self):
        """Initialize the validator."""
        self.validation_results = []
        self.current_file = None

    def validate_docstring_structure(
        self, docstring: str, component_type: str, name: str, line: int
    ) -> List[Dict]:
        """Validate the structure of a docstring against NumPy conventions.

        Parameters
        ----------
        docstring : str
            The docstring to validate.
        component_type : str
            Type of component ('function', 'method', 'class', 'property').
        name : str
            Name of the component.
        line : int
            Line number where the component is defined.

        Returns
        -------
        list of dict
            List of validation issues found.
        """
        issues = []

        if not docstring:
            issues.append(
                {
                    "type": "missing_docstring",
                    "component": component_type,
                    "name": name,
                    "line": line,
                    "message": f"Missing docstring for {component_type} '{name}'",
                }
            )
            return issues

        # Check required sections
        required_sections = self.REQUIRED_SECTIONS.get(component_type, [])
        for section in required_sections:
            if not self._has_section(docstring, section):
                issues.append(
                    {
                        "type": "missing_section",
                        "component": component_type,
                        "name": name,
                        "line": line,
                        "message": f"Missing required '{section}' section in {component_type} '{name}'",
                    }
                )

        # Validate scientific requirements
        issues.extend(
            self._validate_scientific_requirements(
                docstring, component_type, name, line
            )
        )

        return issues

    def _has_section(self, docstring: str, section: str) -> bool:
        """Check if docstring contains a specific section.

        Parameters
        ----------
        docstring : str
            The docstring text.
        section : str
            The section name to look for.

        Returns
        -------
        bool
            True if section is found.
        """
        # Look for section headers like "Parameters\n----------"
        pattern = rf"{section}\s*\n\s*-+\s*\n"
        return bool(re.search(pattern, docstring, re.MULTILINE))

    def _validate_scientific_requirements(
        self, docstring: str, component_type: str, name: str, line: int
    ) -> List[Dict]:
        """Validate scientific computing specific requirements.

        Parameters
        ----------
        docstring : str
            The docstring text.
        component_type : str
            Type of component.
        name : str
            Component name.
        line : int
            Line number.

        Returns
        -------
        list of dict
            List of scientific validation issues.
        """
        issues = []

        # Skip validation for simple utility functions
        if component_type in ["function", "method"] and len(docstring.split("\n")) < 5:
            return issues

        # Check for physics units documentation
        if self._likely_physics_function(name, docstring):
            if not self._has_units_documentation(docstring):
                issues.append(
                    {
                        "type": "missing_units",
                        "component": component_type,
                        "name": name,
                        "line": line,
                        "message": f"Physics function '{name}' missing units documentation",
                    }
                )

        # Check for LaTeX equations in mathematical functions
        if self._likely_mathematical_function(name, docstring):
            if not self._has_latex_equations(docstring):
                issues.append(
                    {
                        "type": "missing_latex",
                        "component": component_type,
                        "name": name,
                        "line": line,
                        "message": f"Mathematical function '{name}' missing LaTeX equation formatting",
                    }
                )

        # Check for examples in complex functions
        if self._needs_examples(name, docstring, component_type):
            if not self._has_examples_section(docstring):
                issues.append(
                    {
                        "type": "missing_examples",
                        "component": component_type,
                        "name": name,
                        "line": line,
                        "message": f"Complex {component_type} '{name}' should include usage examples",
                    }
                )

        return issues

    def _likely_physics_function(self, name: str, docstring: str) -> bool:
        """Determine if function likely involves physics calculations."""
        physics_keywords = [
            "temperature",
            "velocity",
            "magnetic",
            "plasma",
            "thermal",
            "energy",
            "pressure",
            "density",
            "speed",
            "mass",
            "charge",
        ]
        text = (name + " " + docstring).lower()
        return any(keyword in text for keyword in physics_keywords)

    def _likely_mathematical_function(self, name: str, docstring: str) -> bool:
        """Determine if function involves mathematical calculations."""
        math_keywords = [
            "calculate",
            "compute",
            "sqrt",
            "log",
            "exp",
            "integrate",
            "derivative",
            "equation",
            "formula",
            "algorithm",
        ]
        text = (name + " " + docstring).lower()
        return any(keyword in text for keyword in math_keywords)

    def _has_units_documentation(self, docstring: str) -> bool:
        """Check if docstring contains physics units."""
        for pattern in self.PHYSICS_UNITS:
            if re.search(pattern, docstring):
                return True
        return False

    def _has_latex_equations(self, docstring: str) -> bool:
        """Check if docstring contains LaTeX formatted equations."""
        for pattern in self.LATEX_PATTERNS:
            if re.search(pattern, docstring):
                return True
        return False

    def _has_examples_section(self, docstring: str) -> bool:
        """Check if docstring contains an Examples section."""
        return self._has_section(docstring, "Examples")

    def _needs_examples(self, name: str, docstring: str, component_type: str) -> bool:
        """Determine if component should have examples."""
        # Classes and complex functions should have examples
        if component_type == "class":
            return True

        # Functions with many parameters likely need examples
        param_section = re.search(
            r"Parameters\s*\n\s*-+\s*\n(.*?)(?=\n\s*[A-Z][a-z]+\s*\n\s*-+|\Z)",
            docstring,
            re.DOTALL | re.MULTILINE,
        )
        if param_section:
            param_count = len(
                re.findall(r"^\s*\w+\s*:", param_section.group(1), re.MULTILINE)
            )
            if param_count > 3:
                return True

        # Long docstrings likely need examples
        if len(docstring.split("\n")) > 15:
            return True

        return False


class DocstringASTVisitor(ast.NodeVisitor):
    """AST visitor for collecting docstring validation information."""

    def __init__(self, filepath: str, validator: SolarWindPyDocstringValidator):
        """Initialize visitor.

        Parameters
        ----------
        filepath : str
            Path to the file being analyzed.
        validator : SolarWindPyDocstringValidator
            The validator instance to use.
        """
        self.filepath = filepath
        self.validator = validator
        self.current_class = None

    def visit_Module(self, node):
        """Visit module and validate module-level docstring."""
        docstring = ast.get_docstring(node)
        issues = self.validator.validate_docstring_structure(
            docstring or "", "module", self.filepath, 1
        )
        self.validator.validation_results.extend(issues)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Visit class definition and validate class docstring."""
        docstring = ast.get_docstring(node)
        issues = self.validator.validate_docstring_structure(
            docstring or "", "class", node.name, node.lineno
        )
        self.validator.validation_results.extend(issues)

        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node):
        """Visit function/method definition and validate docstring."""
        docstring = ast.get_docstring(node)

        # Skip private methods/functions (except __init__)
        if node.name.startswith("_") and node.name != "__init__":
            self.generic_visit(node)
            return

        component_type = "method" if self.current_class else "function"
        name = f"{self.current_class}.{node.name}" if self.current_class else node.name

        issues = self.validator.validate_docstring_structure(
            docstring or "", component_type, name, node.lineno
        )
        self.validator.validation_results.extend(issues)

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        """Visit async function (treat same as regular function)."""
        self.visit_FunctionDef(node)


def validate_file(filepath: Path) -> List[Dict]:
    """Validate docstrings in a single Python file.

    Parameters
    ----------
    filepath : Path
        Path to Python file to validate.

    Returns
    -------
    list of dict
        List of validation issues found.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(filepath))

        validator = SolarWindPyDocstringValidator()
        visitor = DocstringASTVisitor(str(filepath), validator)
        visitor.visit(tree)

        return validator.validation_results
    except (SyntaxError, UnicodeDecodeError) as e:
        return [
            {
                "type": "parse_error",
                "component": "file",
                "name": str(filepath),
                "line": 0,
                "message": f"Error parsing file: {e}",
            }
        ]


def generate_validation_report(
    solarwindpy_path: Path, output_format: str = "detailed"
) -> None:
    """Generate comprehensive validation report.

    Parameters
    ----------
    solarwindpy_path : Path
        Path to solarwindpy package.
    output_format : str
        Report format ('detailed' or 'summary').
    """
    print("SolarWindPy Docstring Validation Report")
    print("=" * 50)

    python_files = list(solarwindpy_path.rglob("*.py"))
    python_files = [f for f in python_files if not f.name.startswith("test_")]

    all_issues = []
    issue_counts = {}

    print(f"Validating {len(python_files)} Python modules...\n")

    for py_file in sorted(python_files):
        relative_path = py_file.relative_to(solarwindpy_path.parent)
        issues = validate_file(py_file)

        if issues:
            all_issues.extend(issues)

            # Count issue types
            for issue in issues:
                issue_type = issue["type"]
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1

            if output_format == "detailed":
                print(f"{relative_path}:")
                for issue in issues:
                    print(f"  {issue['line']:3d}: {issue['message']}")
                print()

    # Summary statistics
    print("Validation Summary:")
    print("-" * 30)
    print(f"Total Issues: {len(all_issues)}")
    print(
        f"Files with Issues: {len(set(issue.get('name', '').split('.')[0] for issue in all_issues))}"
    )
    print()

    print("Issue Type Breakdown:")
    for issue_type, count in sorted(issue_counts.items()):
        print(f"  {issue_type}: {count}")

    if len(all_issues) == 0:
        print("\n✅ No validation issues found! All docstrings meet requirements.")
    else:
        print(f"\n⚠️  Found {len(all_issues)} validation issues requiring attention.")


def main():
    """Main entry point for docstring validation."""
    parser = argparse.ArgumentParser(description="Validate SolarWindPy docstrings")
    parser.add_argument(
        "--path",
        type=str,
        default="solarwindpy",
        help="Path to solarwindpy package (default: solarwindpy)",
    )
    parser.add_argument(
        "--format",
        choices=["detailed", "summary"],
        default="detailed",
        help="Output format (default: detailed)",
    )

    args = parser.parse_args()

    solarwindpy_path = Path(args.path)
    if not solarwindpy_path.exists():
        print(f"Error: Path {solarwindpy_path} does not exist")
        sys.exit(1)

    generate_validation_report(solarwindpy_path, args.format)


if __name__ == "__main__":
    main()
