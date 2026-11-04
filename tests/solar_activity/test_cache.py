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

import http.server
import os
import threading
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


def test_a_refresh_leaves_exactly_one_entry_for_its_url(tmp_path, isolated_cache):
    """A stale entry's refresh replaces it rather than adding a second copy.

    Chosen input: the entry is refreshed twice, each time after being
    backdated past its window, and the served text changes each time, so a
    refresh that kept the old copy would leave two or three files on disk.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.solar_activity import cache

    source, url = serve(tmp_path, "first\n")
    path = cache.fetch(url, max_age=pd.Timedelta(days=1))
    for text in ("second\n", "third\n"):
        backdate(path, 2)
        source.write_text(text)
        path = cache.fetch(url, max_age=pd.Timedelta(days=1))

    assert cache.cache_contents().index.tolist() == [url]
    entries = list((isolated_cache / "solarwindpy").rglob("contents"))
    assert entries == [path]
    assert path.read_text() == "third\n"


class DownloadAttempted(AssertionError):
    """Raised when a test that must not download calls ``_download_file``."""


@pytest.mark.parametrize("seeded", [False, True], ids=["empty", "seeded"])
@pytest.mark.parametrize("accessor", ["age", "ctime"])
def test_reading_a_loaders_age_writes_nothing(
    accessor, seeded, isolated_cache, seed_cache, monkeypatch
):
    """Reading ``DataLoader.age`` or ``ctime`` neither downloads nor writes the cache.

    ``ctime`` and ``age`` are the loaders' read-only accessors (``ICMECAT``
    has none). Chosen input: an empty cache, and one holding the loader's
    own URL; the cache tree is snapshotted, names and modification times,
    before and after the read, and any download raises.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.solar_activity import cache
    from solarwindpy.solar_activity.sunspot_number.sidc import SIDC_ID, SIDCLoader

    sidc_id = SIDC_ID("m13")
    if seeded:
        seed_cache(sidc_id.url, "2020;01;2020.042;2.2;0.8;795;1\n", age_days=3)

    def refuse(url, cache):
        raise DownloadAttempted(f"reading {accessor} tried to download {url}")

    monkeypatch.setattr(cache, "_download_file", refuse)

    def snapshot():
        return {
            path.relative_to(isolated_cache): path.stat().st_mtime_ns
            for path in isolated_cache.rglob("*")
        }

    before = snapshot()
    getattr(SIDCLoader(sidc_id.key, sidc_id.url), accessor)
    assert snapshot() == before


def test_a_first_run_on_a_clean_home_creates_the_cache(tmp_path, monkeypatch):
    """With no cache folder yet, the first fetch creates ``~/.cache/solarwindpy``.

    Chosen input: HOME is an empty directory under ``tmp_path`` and
    ``XDG_CACHE_HOME`` is unset, so astropy (8 or later) resolves the
    default location and must create every level of it.

    ON FAILURE: the code is wrong, unless astropy changed its default cache
    location; then external fact drifted; update the cache module docstring.
    """
    import astropy

    from packaging.version import Version

    if Version(astropy.__version__) < Version("8"):
        pytest.skip("astropy before 8 does not create ~/.cache/<package>")

    from solarwindpy.solar_activity import cache

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    expected = home / ".cache" / "solarwindpy"
    assert get_cache_dir_path("solarwindpy", ensure_exists=False) == expected
    assert not expected.exists()

    _, url = serve(tmp_path, "first\n")
    path = cache.fetch(url, max_age=pd.Timedelta(days=1))

    assert expected.is_dir()
    assert path.is_relative_to(expected)
    assert cache.cache_contents().index.tolist() == [url]


@pytest.fixture
def http_server():
    """A loopback HTTP server: ``/<code>.csv`` answers ``<code>``, ``/ok.csv`` 200.

    Returns the server's base URL. It stands in for a remote host so the
    status astropy's real download raises can be read; it binds 127.0.0.1
    only and never leaves the machine.
    """

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            name = self.path.strip("/").split(".")[0]
            code = 200 if name == "ok" else int(name)
            self.send_response(code)
            self.end_headers()
            if code == 200:
                self.wfile.write(b"served\n")

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}/"
    server.shutdown()
    server.server_close()


_STATUS_XFAIL = pytest.mark.xfail(
    strict=True,
    reason="cache.DownloadError has no status and fetch has no fallback "
    "switch; remove this marker when both land",
)


@_STATUS_XFAIL
@pytest.mark.parametrize("code", [404, 500])
def test_a_failed_http_download_reports_its_status(http_server, code):
    """``DownloadError.status`` is the HTTP status the server answered.

    Chosen input: a loopback server answering 404 and 500, through
    astropy's real download.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.solar_activity import cache

    with pytest.raises(cache.DownloadError) as info:
        cache.fetch(f"{http_server}{code}.csv", max_age=pd.Timedelta(days=1))

    assert info.value.status == code


@_STATUS_XFAIL
def test_a_failure_without_an_http_answer_has_no_status(tmp_path):
    """A download that never got an HTTP answer has ``status`` None.

    Chosen input: a missing ``file://`` source, which fails the way an
    unreachable host does, with no HTTP status.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.solar_activity import cache

    with pytest.raises(cache.DownloadError) as info:
        cache.fetch((tmp_path / "gone.csv").as_uri(), max_age=pd.Timedelta(days=1))

    assert info.value.status is None


@_STATUS_XFAIL
def test_without_fallback_a_failed_refresh_raises_despite_a_cached_copy(
    http_server, seed_cache
):
    """``fallback=False`` raises with the status instead of using the cache.

    Chosen input: a three-day-old cached copy of a URL that now answers 404.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.solar_activity import cache

    url = f"{http_server}404.csv"
    seed_cache(url, "old\n", age_days=3)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(cache.DownloadError) as info:
            cache.fetch(url, max_age=pd.Timedelta(days=1), fallback=False)

    assert info.value.status == 404


@_STATUS_XFAIL
def test_fall_back_returns_the_cached_copy_and_warns_its_age(seed_cache):
    """``fall_back`` returns a cached copy with a warning naming its age.

    Chosen input: a copy seeded three days old and a stand-in download
    error, so the warning names "3.0 days".

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.solar_activity import cache

    url = "https://example.invalid/series.csv"
    seed_cache(url, "old\n", age_days=3)

    with pytest.warns(cache.StaleCacheWarning, match=r"3\.0 days old"):
        path = cache.fall_back(url, OSError("unreachable"))

    assert path.read_text() == "old\n"


@_STATUS_XFAIL
def test_fall_back_with_nothing_cached_raises_with_the_status(http_server):
    """``fall_back`` raises ``DownloadError`` carrying the error's status.

    Chosen input: the HTTPError a 404 download raised, and an empty cache.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.solar_activity import cache

    url = f"{http_server}404.csv"
    with pytest.raises(cache.DownloadError) as raised:
        cache.fetch(url, max_age=pd.Timedelta(days=1))
    error = raised.value.__cause__

    with pytest.raises(cache.DownloadError, match="no cached copy") as info:
        cache.fall_back(url, error)

    assert info.value.status == 404
