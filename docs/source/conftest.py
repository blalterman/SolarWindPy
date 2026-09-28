# Spent-When: PERMANENT(docs/source/ carries no rst file marked expected-to-fail)
# Supersedes: none
"""pytest configuration for ``pytest --doctest-glob='*.rst' docs/source``.

``usage.rst`` carries examples that do not run (undefined names, failing
imports). It stays collected and is marked strict xfail, so the rewrite that
makes it run turns this mark red and forces its removal.
"""

import pytest

RST_XFAIL = {
    "usage.rst": (
        "usage.rst examples do not run (NameError on TeXlabel, failing "
        "imports). Retired by the phase-4 usage.rst rewrite."
    ),
}


def pytest_collection_modifyitems(config, items):
    for item in items:
        reason = RST_XFAIL.get(item.path.name)
        if reason is not None and item.nodeid.endswith(f"::{item.path.name}"):
            item.add_marker(pytest.mark.xfail(strict=True, reason=reason))
