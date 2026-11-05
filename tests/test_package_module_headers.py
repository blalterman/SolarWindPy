# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
"""Shipped package modules carry no purge-system header.

``Spent-When`` and ``Supersedes`` declarations belong to working files, not to
modules installed with the package. The scan reads tracked files only
(``git ls-files``), so untracked work in the tree cannot change the verdict.
"""

import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _tracked_package_modules():
    """Every tracked ``*.py`` file under ``solarwindpy/``."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "solarwindpy/*.py"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout")
    return [REPO / line for line in out.splitlines()]


def test_no_shipped_module_opens_with_a_purge_header():
    """No tracked package module's first two lines declare Spent-When or Supersedes.

    ON FAILURE: the code is wrong; remove the header from the listed modules.
    """
    modules = _tracked_package_modules()
    assert modules, "git ls-files found no package module"
    flagged = []
    for path in modules:
        with path.open(encoding="utf-8") as fh:
            head = [fh.readline() for _ in range(2)]
        if any(
            line.lstrip("# ").startswith(("Spent-When:", "Supersedes:"))
            for line in head
        ):
            flagged.append(str(path.relative_to(REPO)))
    assert not flagged, flagged
