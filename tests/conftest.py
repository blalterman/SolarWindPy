"""Consolidated test configuration for SolarWindPy.

This file provides shared test configuration for all tests in the consolidated /tests/
directory structure. It enables external package imports for migrated tests from
solarwindpy/tests/.
"""

import pytest

# Tests in the /tests/ directory should use external package imports
# (e.g., "import solarwindpy" instead of relative imports)
# No special module path configuration needed for external imports


def pytest_addoption(parser):
    """Add custom command-line options for pytest."""
    parser.addoption(
        "--debug-prints",
        action="store_true",
        default=False,
        help="Enable debug print statements in tests",
    )


@pytest.fixture
def debug_print(request):
    """Fixture that returns a conditional print function.

    Only prints when --debug-prints flag is passed to pytest.

    Usage
    -----
    def test_something(debug_print):
        debug_print(f"DataFrame shape: {df.shape}")

    Run with: pytest tests/ --debug-prints -s
    """
    enabled = request.config.getoption("--debug-prints")

    def _debug_print(*args, **kwargs):
        if enabled:
            print(*args, **kwargs)

    return _debug_print
