# Spent-When: PERMANENT(the solar-activity tests stop sharing a download-cache fixture)
# Supersedes: none
"""Shared fixtures for the solar-activity tests.

The download cache is a filesystem boundary under the user's home directory.
astropy resolves it on every call from ``XDG_CACHE_HOME`` when that directory
exists, so pointing the variable at a directory under ``tmp_path`` keeps every
test's cache private and leaves the user's ``~/.cache/solarwindpy`` untouched.
"""

import itertools
import os
import time

from pathlib import Path

import pytest

from astropy.utils.data import import_file_to_cache

ONE_DAY = 86400.0


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Point the download cache at an empty directory under ``tmp_path``.

    Returns the directory that plays the role of ``~/.cache``; SolarWindPy's
    cache is its ``solarwindpy`` subdirectory. astropy ignores an
    ``XDG_CACHE_HOME`` that does not exist, so the directory is created, and
    its ``solarwindpy`` subdirectory too, since astropy releases before 8 honour
    the variable only when ``<XDG_CACHE_HOME>/<package>`` already exists.
    """
    root = tmp_path / "xdg-cache"
    (root / "solarwindpy").mkdir(parents=True)
    monkeypatch.setenv("XDG_CACHE_HOME", str(root))
    return root


@pytest.fixture
def seed_cache(tmp_path, isolated_cache):
    """Return ``seed(url, text, age_days=0)``: cache ``text`` as ``url``'s download.

    The entry is registered with astropy's own ``import_file_to_cache``, so the
    cache holds exactly what a download of ``url`` would have left, and its
    file time is moved ``age_days`` into the past. Returns the cached path.
    """
    sources = tmp_path / "seeded"
    sources.mkdir()
    counter = itertools.count()

    def _seed(url, text, age_days=0.0):
        source = sources / f"{next(counter)}.txt"
        source.write_text(text)
        path = Path(import_file_to_cache(url, str(source), pkgname="solarwindpy"))
        if age_days:
            then = time.time() - age_days * ONE_DAY
            os.utime(path, (then, then))
        return path

    return _seed
