# Spent-When: PERMANENT(solarwindpy.solar_activity.cache is removed)
# Supersedes: none
"""The shared download cache in ``solarwindpy.solar_activity.cache``.

``fetch(url, max_age)`` returns a local copy of ``url``: the cached one while
it is younger than ``max_age``, a fresh download once it is older, and the
cached one again, with a warning naming its age, when that download fails.

The network is the external boundary. Every "remote" file here is a real file
under ``tmp_path`` served through a ``file://`` URL, so astropy's real download
and cache code runs without opening a socket; deleting the served file makes
the next download fail exactly as an unreachable server does. The cache itself
lives under ``tmp_path`` through the autouse ``isolated_cache`` fixture, and an
entry is aged by moving its file's modification time back, the clock the
cache reads.
"""

import os
import time
import warnings

import pandas as pd
import pytest

from astropy.config.paths import get_cache_dir_path

ONE_DAY = 86400.0


def serve(tmp_path, text):
    """Write ``text`` as a "remote" file; return its path and ``file://`` URL."""
    remote = tmp_path / "remote"
    remote.mkdir(exist_ok=True)
    source = remote / "series.csv"
    source.write_text(text)
    return source, source.as_uri()


def backdate(path, days):
    """Move ``path``'s modification time ``days`` into the past."""
    then = time.time() - days * ONE_DAY
    os.utime(path, (then, then))


def test_the_isolated_cache_lies_under_tmp_path(isolated_cache):
    """The cache astropy resolves for SolarWindPy is the fixture's directory.

    ON FAILURE: the fixture no longer keeps the download cache out of the
    user's home directory; fix the fixture.
    """
    resolved = get_cache_dir_path("solarwindpy", ensure_exists=False)
    assert resolved == isolated_cache / "solarwindpy"


def test_a_fresh_entry_is_returned_without_downloading(tmp_path):
    """Within its freshness window the cached copy is returned as is.

    Chosen input: after the first fetch the served file is deleted, so any
    download would fail and warn; turning warnings into errors makes such a
    download visible.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.solar_activity import cache

    source, url = serve(tmp_path, "first\n")
    cache.fetch(url, max_age=pd.Timedelta(days=1))
    source.unlink()

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        path = cache.fetch(url, max_age=pd.Timedelta(days=1))

    assert path.read_text() == "first\n"


def test_a_stale_entry_is_downloaded_again(tmp_path):
    """Past its freshness window the entry is replaced by a new download.

    Chosen input: the served file changes after the first fetch and the
    cached copy is two days old against a one-day window, so only a new
    download returns the second text.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.solar_activity import cache

    source, url = serve(tmp_path, "first\n")
    backdate(cache.fetch(url, max_age=pd.Timedelta(days=1)), 2)
    source.write_text("second\n")

    path = cache.fetch(url, max_age=pd.Timedelta(days=1))

    assert path.read_text() == "second\n"


def test_a_failed_refresh_returns_the_cached_copy_and_warns_its_age(tmp_path):
    """A stale entry whose download fails is returned, with a warning of its age.

    Chosen input: the cached copy is three days old and the served file is
    gone, so the refresh fails and the warning names "3.0 days".

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.solar_activity import cache

    source, url = serve(tmp_path, "first\n")
    backdate(cache.fetch(url, max_age=pd.Timedelta(days=1)), 3)
    source.unlink()

    with pytest.warns(cache.StaleCacheWarning, match=r"3\.0 days old"):
        path = cache.fetch(url, max_age=pd.Timedelta(days=1))

    assert path.read_text() == "first\n"


def test_a_failed_download_with_nothing_cached_raises(tmp_path):
    """With no cached copy to fall back on, a failed download raises.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.solar_activity import cache

    url = (tmp_path / "never-served.csv").as_uri()

    with pytest.raises(cache.DownloadError, match="no cached copy"):
        cache.fetch(url, max_age=pd.Timedelta(days=1))


def test_cache_contents_lists_each_url_with_its_path_and_age(tmp_path):
    """The listing maps each cached URL to its local file and that file's age.

    Chosen input: one entry, backdated five days, so its age is five days
    plus the few seconds the test takes.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.solar_activity import cache

    _, url = serve(tmp_path, "first\n")
    path = cache.fetch(url, max_age=pd.Timedelta(days=1))
    backdate(path, 5)

    listing = cache.cache_contents()

    assert listing.index.tolist() == [url]
    assert listing.loc[url, "path"] == path
    age = listing.loc[url, "age"]
    assert pd.Timedelta(days=5) <= age < pd.Timedelta(days=5, minutes=1)


def test_cache_contents_of_an_empty_cache_is_an_empty_listing():
    """Before anything is downloaded the listing is empty but keeps its columns.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.solar_activity import cache

    listing = cache.cache_contents()

    assert listing.empty
    assert listing.columns.tolist() == ["path", "age"]


def test_a_local_path_is_read_in_place_and_not_cached(tmp_path):
    """A plain file path is returned as is, and nothing enters the cache.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.solar_activity import cache

    local = tmp_path / "local.csv"
    local.write_text("first\n")

    assert cache.fetch(str(local), max_age=pd.Timedelta(days=1)) == local
    assert cache.cache_contents().empty
