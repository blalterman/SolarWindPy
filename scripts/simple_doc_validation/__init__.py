"""
Simplified Documentation Validation Framework for SolarWindPy

A right-sized validation framework appropriate for scientific packages
with moderate documentation complexity (~47 examples).

This framework replaces the over-engineered 3,751-line validation system
with a focused ~300-line implementation providing essential functionality:

- Core doctest execution with Python 3.9-3.11 compatibility
- Basic CI/CD integration for GitHub Actions
- Essential reporting and utilities
- Sustainable complexity for research team maintenance

Components:
- doctest_runner: Core doctest execution (~100 lines)
- ci_integration: GitHub Actions interface (~100 lines)  
- validation_utils: Reporting and helpers (~100 lines)
"""

from .doctest_runner import SimpleDocTestRunner
from .ci_integration import CIIntegration
from .validation_utils import (
    count_documentation_examples,
    validate_example_syntax,
    generate_validation_summary,
    create_minimal_report_files,
    get_framework_status,
)

__version__ = "1.0.0"
__all__ = [
    "SimpleDocTestRunner",
    "CIIntegration",
    "count_documentation_examples",
    "validate_example_syntax",
    "generate_validation_summary",
    "create_minimal_report_files",
    "get_framework_status",
]
