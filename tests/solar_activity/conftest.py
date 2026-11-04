# Spent-When: PERMANENT(the solar-activity tests stop sharing a download-cache fixture)
# Supersedes: none
"""Shared fixtures for the solar-activity tests.

The download cache is a filesystem boundary under the user's home directory.
astropy resolves it on every call from ``XDG_CACHE_HOME`` when that directory
exists, so pointing the variable at a directory under ``tmp_path`` keeps every
test's cache private and leaves the user's ``~/.cache/solarwindpy`` untouched.
"""

import pytest


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Point the download cache at an empty directory under ``tmp_path``.

    Returns the directory that plays the role of ``~/.cache``; SolarWindPy's
    cache is its ``solarwindpy`` subdirectory. astropy ignores an
    ``XDG_CACHE_HOME`` that does not exist, so the directory is created.
    """
    root = tmp_path / "xdg-cache"
    root.mkdir()
    monkeypatch.setenv("XDG_CACHE_HOME", str(root))
    return root
