"""Consolidated test configuration for SolarWindPy.

This file provides shared test configuration for all tests in the consolidated /tests/
directory structure. It enables external package imports for migrated tests from
solarwindpy/tests/.
"""

import os

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
    parser.addoption(
        "--run-drift",
        action="store_true",
        default=False,
        help=(
            "Run tests marked drift, integration, or slow. Also honoured via "
            "the SWP_RUN_DRIFT=1 environment variable."
        ),
    )


def pytest_collection_modifyitems(config, items):
    """Skip drift/integration/slow tests unless explicitly opted into.

    The gate lives here (rather than in an ``addopts`` marker expression) so
    it holds under any pytest invocation, including one supplying its own
    ``-m``. Tests are skipped rather than deselected, so a default run still
    reports how many exist.
    """
    run_drift = (
        config.getoption("--run-drift") or os.environ.get("SWP_RUN_DRIFT") == "1"
    )
    if run_drift:
        return

    gated = {"drift", "integration", "slow"}
    skip_marker = pytest.mark.skip(
        reason="drift/integration/slow tests are opt-in: pass --run-drift or "
        "set SWP_RUN_DRIFT=1"
    )
    for item in items:
        if gated.intersection(mark.name for mark in item.iter_markers()):
            item.add_marker(skip_marker)


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
