# Spent-When: PERMANENT(SolarWindPy stops collecting doctests with pytest)
# Supersedes: none
"""Repository-root pytest configuration for doctest collection.

``pytest --doctest-modules solarwindpy`` collects docstring examples as
``DoctestItem`` objects, which accept no decorators. Examples that document
correct behavior the library does not yet deliver are marked strict xfail
here, so the suite reports the day the library catches up.
"""

import pytest

# Doctest node id -> reason. Each entry names the defect that retires it.
DOCTEST_XFAIL = {
    "solarwindpy/fitfunctions/composite.py::"
    "solarwindpy.fitfunctions.composite.GaussianPlusHeavySide": (
        "x0 is never fitted: the Heaviside term has zero gradient in x0, so "
        "curve_fit returns p0's x0 (3.05) instead of the true step at 2.0. "
        "Retired by a fit that can move x0."
    ),
}


def pytest_collection_modifyitems(config, items):
    for item in items:
        reason = DOCTEST_XFAIL.get(item.nodeid)
        if reason is not None:
            item.add_marker(pytest.mark.xfail(strict=True, reason=reason))
