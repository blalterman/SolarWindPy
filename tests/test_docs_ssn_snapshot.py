# Spent-When: PERMANENT(the documentation stops plotting SILSO's sunspot number)
# Supersedes: none
"""The docs serve SILSO's 13-month smoothed sunspot number from a snapshot.

``docs/source/_ssn_snapshot.py`` points SolarWindPy's download cache at a
private directory and seeds it with ``docs/source/_data``'s snapshot under the
URL ``SIDC("m13")`` fetches, so the docs build and the plot-block test load the
series without a download. Here any download attempt raises, and a stale-cache
fallback is an error, so a seed that ``fetch`` did not take as fresh fails.
"""

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from solarwindpy.solar_activity import cache
from solarwindpy.solar_activity.sunspot_number.sidc import SIDC, SIDC_ID, SIDCLoader

DOCS = Path(__file__).resolve().parents[1] / "docs" / "source"

if not DOCS.is_dir():
    pytest.skip(
        "docs/source is absent (e.g. testing from the sdist)",
        allow_module_level=True,
    )

pytestmark = pytest.mark.filterwarnings(
    "error::solarwindpy.solar_activity.cache.StaleCacheWarning"
)

_PENDING = pytest.mark.xfail(
    strict=True, reason="the docs have no sunspot-number snapshot yet"
)


def _helper():
    spec = importlib.util.spec_from_file_location(
        "_ssn_snapshot", DOCS / "_ssn_snapshot.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _no_download(url, cache):
    raise AssertionError(f"tried to download {url}")


@pytest.fixture
def seeded(tmp_path, monkeypatch):
    """Seed a private cache from the snapshot; any download raises."""
    monkeypatch.setattr(cache, "_download_file", _no_download)
    helper = _helper()
    path = helper.seed_ssn_snapshot(tmp_path / "cache", monkeypatch.setenv)
    return helper, path


@_PENDING
def test_snapshot_is_cached_fresh_under_the_m13_url(seeded):
    """The seed is the loader's URL, younger than its freshness window.

    ON FAILURE: the code is wrong.
    """
    helper, path = seeded
    url = SIDC_ID("m13").url
    assert helper.URL == url
    assert cache.cache_contents().index.tolist() == [url]
    assert cache.cached_age(url) < SIDCLoader("m13", url).max_age
    assert cache.fetch(url, SIDCLoader("m13", url).max_age) == path


@_PENDING
def test_snapshot_names_its_source_and_caches_only_the_data(seeded):
    """The committed file's header names the URL; the cached copy has no header.

    ON FAILURE: the code is wrong.
    """
    helper, path = seeded
    header = [
        line for line in helper.SNAPSHOT.read_text().splitlines() if line[:1] == "#"
    ]
    assert any(helper.URL in line for line in header)
    assert not [line for line in path.read_text().splitlines() if line[:1] == "#"]


@_PENDING
def test_snapshot_parses_through_sidc_and_covers_1994_to_2026(seeded):
    """``SIDC("m13")`` loads the seeded snapshot: months 1994-01 through 2026.

    The last months of a 13-month smoothed series are not yet defined, so the
    sunspot number is required only through 2025.
    ON FAILURE: the code is wrong.
    """
    ssn = SIDC("m13").data.loc[:, "ssn"]
    assert ssn.index.min() == pd.Timestamp("1994-01-01")
    assert ssn.index.max() >= pd.Timestamp("2026-01-01")
    assert ssn.loc["1994":"2025"].notna().all()
