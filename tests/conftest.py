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
            "Run tests marked drift or slow. Also honoured via the "
            "SWP_RUN_DRIFT=1 environment variable."
        ),
    )


def pytest_collection_modifyitems(config, items):
    """Skip drift and slow tests unless explicitly opted into.

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

    gated = {"drift", "slow"}
    skip_marker = pytest.mark.skip(
        reason="drift/slow tests are opt-in: pass --run-drift or set SWP_RUN_DRIFT=1"
    )
    for item in items:
        if gated.intersection(mark.name for mark in item.iter_markers()):
            item.add_marker(skip_marker)


@pytest.fixture
def isolated_cache(tmp_path, monkeypatch):
    """Point the download cache at an empty directory under ``tmp_path``.

    The cache is a filesystem boundary under the user's home directory; astropy
    resolves it on every call from ``XDG_CACHE_HOME``, so a test using this
    fixture neither reads nor writes the user's ``~/.cache/solarwindpy``.
    Returns the directory that plays the role of ``~/.cache``. astropy ignores
    an ``XDG_CACHE_HOME`` that does not exist, and releases before 8 honour it
    only when ``<XDG_CACHE_HOME>/solarwindpy`` exists too, so both are created.
    """
    root = tmp_path / "xdg-cache"
    (root / "solarwindpy").mkdir(parents=True)
    monkeypatch.setenv("XDG_CACHE_HOME", str(root))
    return root
