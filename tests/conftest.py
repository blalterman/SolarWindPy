"""Test configuration shared by every test under ``tests/``.

``pythonpath = ["src"]`` in ``pyproject.toml`` puts this checkout's ``src/``
first on ``sys.path``, so ``import solarwindpy`` loads the package from this
checkout, not from whichever checkout the editable install points at.
"""

import os

import pytest


def pytest_addoption(parser):
    """Add custom command-line options for pytest."""
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
