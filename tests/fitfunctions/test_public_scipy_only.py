# Spent-When: PERMANENT(fitfunctions stops depending on SciPy)
# Supersedes: none
"""The fitting modules use only SciPy's public API.

A private SciPy name (a module or attribute whose dotted path has a component
starting with an underscore) carries no compatibility promise and can vanish in
any release. Every ``src/solarwindpy/fitfunctions/*.py`` module is parsed and
its ``import`` and ``from ... import`` statements are checked. The scanner is
tested on snippets held in memory, so a scanner that flags nothing cannot pass
the module scan vacuously.
"""

import ast
from pathlib import Path

import pytest

import solarwindpy.fitfunctions

FITFUNCTIONS = Path(solarwindpy.fitfunctions.__file__).resolve().parent


class PrivateScipyImportError(AssertionError):
    """A fitfunctions module imports a private SciPy name."""


def _private_scipy_imports(source):
    """Return each private SciPy import in ``source`` as a dotted string."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            dotted = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            dotted = [f"{node.module}.{alias.name}" for alias in node.names]
        else:
            continue
        for name in dotted:
            parts = name.split(".")
            if parts[0] == "scipy" and any(p.startswith("_") for p in parts[1:]):
                found.append(name)
    return found


@pytest.mark.parametrize(
    "snippet, expected",
    [
        (
            "from scipy.optimize._minpack_py import _wrap_func",
            ["scipy.optimize._minpack_py._wrap_func"],
        ),
        ("from scipy.optimize import _minpack_py", ["scipy.optimize._minpack_py"]),
        (
            "from scipy.optimize.minpack import _initialize_feasible",
            ["scipy.optimize.minpack._initialize_feasible"],
        ),
        ("import scipy.optimize._lsq.common", ["scipy.optimize._lsq.common"]),
        ("from scipy.optimize import least_squares, OptimizeWarning", []),
        ("from scipy.linalg import svd", []),
        ("import scipy.optimize", []),
        ("from numpy._core import multiarray", []),
        ("from . import _least_squares", []),
    ],
)
def test_scanner_flags_exactly_the_private_scipy_imports(snippet, expected):
    """The scanner reports private SciPy imports and nothing else.

    ON FAILURE: the scanner no longer separates private from public SciPy imports; fix the scanner.
    """
    assert _private_scipy_imports(snippet) == expected


@pytest.mark.xfail(
    strict=True,
    raises=PrivateScipyImportError,
    reason=(
        "fitfunctions/core.py imports _wrap_func, _wrap_jac and "
        "_initialize_feasible from scipy.optimize._minpack_py (fallback "
        "scipy.optimize.minpack); expected message lists those names; remove "
        "this marker when the public-API fitting helpers land"
    ),
)
def test_fitfunctions_modules_import_no_private_scipy_name():
    """No fitfunctions module imports a SciPy name whose dotted path is private.

    ON FAILURE: the code is wrong; replace the listed imports with public SciPy API.
    """
    modules = sorted(FITFUNCTIONS.glob("*.py"))
    assert modules, f"no modules found in {FITFUNCTIONS}"
    flagged = {
        path.name: names
        for path in modules
        if (names := _private_scipy_imports(path.read_text(encoding="utf-8")))
    }
    if flagged:
        raise PrivateScipyImportError(flagged)
