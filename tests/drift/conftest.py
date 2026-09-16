# Spent-When: PERMANENT(the tests/drift/ suite is retired)
# Supersedes: none
"""Fixtures shared by tests/drift/."""

import urllib.error
import urllib.request
from pathlib import Path

import pytest

from solarwindpy.solar_activity.icme.icmecat import ICMECAT_URL, _DATETIME_COLUMNS


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Repository root, three levels up from this file."""
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def head_status():
    """Return a callable ``head_status(url) -> dict`` performing an HTTP HEAD.

    Uses stdlib ``urllib.request`` rather than ``requests``, which is not a
    declared dependency.

    Returns
    -------
    dict
        ``{"status": int, "content_type": str or None,
        "content_length": int or None}``. A network/URL error yields
        ``status=None``.
    """

    def _head_status(url: str) -> dict:
        req = urllib.request.Request(url, method="HEAD")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                headers = resp.headers
                content_length = headers.get("Content-Length")
                return {
                    "status": resp.status,
                    "content_type": headers.get("Content-Type"),
                    "content_length": (
                        int(content_length) if content_length is not None else None
                    ),
                }
        except urllib.error.HTTPError as exc:
            return {
                "status": exc.code,
                "content_type": None,
                "content_length": None,
            }
        except urllib.error.URLError:
            return {"status": None, "content_type": None, "content_length": None}

    return _head_status


@pytest.fixture(scope="session")
def live_catalog():
    """Download the pinned ICMECAT catalog once per session."""
    import pandas as pd

    return pd.read_csv(ICMECAT_URL, parse_dates=_DATETIME_COLUMNS)
