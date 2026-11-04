"""Download cache shared by the solar activity data sources.

Every downloaded file is kept in astropy's download cache under the package
name ``solarwindpy``, by default ``~/.cache/solarwindpy`` (``XDG_CACHE_HOME``
is honoured when that directory exists). :func:`fetch` returns the cached copy
while it is younger than the source's freshness window and downloads again
once it is older. If that download fails, the cached copy is returned with a
:class:`StaleCacheWarning` naming its age, because a stale copy is better than
none; only a source never downloaded raises :class:`DownloadError`.

astropy names each cached file by a hash of its URL, so :func:`cache_contents`
lists which URL each file holds and how old it is. To remove entries, use
``astropy.utils.data.clear_download_cache(url, pkgname="solarwindpy")``.
"""

__all__ = [
    "PKGNAME",
    "DownloadError",
    "StaleCacheWarning",
    "fetch",
    "cached_age",
    "cache_contents",
]

import http.client
import logging
import time
import warnings

from pathlib import Path

import pandas as pd

from astropy.utils import data as _astropy_data

#: Package name under which astropy keeps SolarWindPy's downloads.
PKGNAME = "solarwindpy"

_logger = logging.getLogger(__name__)

# Network and HTTP failures. urllib raises URLError and HTTPError, both
# OSError subclasses, as are timeouts and dropped connections;
# http.client.HTTPException covers a malformed or truncated response.
_DOWNLOAD_ERRORS = (OSError, http.client.HTTPException)


class DownloadError(RuntimeError):
    """Raised when a download fails and there is no cached copy to fall back on."""


class StaleCacheWarning(UserWarning):
    """Warns that a download failed and an older cached copy is being used."""


def _download_file(url, cache):
    """Download ``url`` into the cache; the single point where SolarWindPy downloads.

    Tests that guard the network patch this function.
    """
    return _astropy_data.download_file(
        url, cache=cache, show_progress=False, pkgname=PKGNAME
    )


def _cached_urls():
    """Map each cached URL to its local file, as astropy records them."""
    with warnings.catch_warnings():
        # A cache that does not exist yet is simply empty.
        warnings.simplefilter("ignore", _astropy_data.CacheMissingWarning)
        contents = _astropy_data.cache_contents(pkgname=PKGNAME)
    return {url: Path(path) for url, path in contents.items()}


def _age(path):
    """Time since ``path`` was written, i.e. since its URL was downloaded."""
    return pd.Timedelta(seconds=time.time() - path.stat().st_mtime)


def cached_age(url):
    """Age of the cached copy of ``url``.

    Parameters
    ----------
    url : str
        URL as passed to :func:`fetch`.

    Returns
    -------
    pandas.Timedelta or None
        Time since the cached copy was downloaded, or None if ``url`` is not
        cached.
    """
    path = _cached_urls().get(url)
    return None if path is None else _age(path)


def fetch(url, max_age):
    """Return a local copy of ``url``, downloading it if the cached one is stale.

    Parameters
    ----------
    url : str
        Remote URL (``http``, ``https``, ``ftp`` or ``file``). A plain local
        path is returned as is and never cached.
    max_age : pandas.Timedelta or str
        Freshness window: a cached copy younger than this is returned without
        downloading. Anything :class:`pandas.Timedelta` accepts.

    Returns
    -------
    pathlib.Path
        Path to the local copy.

    Raises
    ------
    DownloadError
        If the download fails and no copy is cached, or a local path does not
        exist.

    Warns
    -----
    StaleCacheWarning
        If the download fails and an older cached copy is returned instead.
    """
    if not _astropy_data.is_url(url):
        path = Path(url)
        if not path.exists():
            raise DownloadError(f"Local file {path} does not exist.")
        return path

    max_age = pd.Timedelta(max_age)
    cached = _cached_urls().get(url)
    if cached is not None:
        age = _age(cached)
        if age <= max_age:
            _logger.info("Using cached %s (%s old): %s", url, age, cached)
            return cached

    _logger.info("Downloading %s", url)
    try:
        return Path(_download_file(url, cache="update"))
    except _DOWNLOAD_ERRORS as exc:
        if cached is None:
            raise DownloadError(
                f"Could not download {url} and there is no cached copy to fall "
                f"back on. Underlying error: {exc!r}"
            ) from exc
        days = _age(cached) / pd.Timedelta(days=1)
        message = (
            f"Could not download {url} ({exc!r}); using the cached copy that "
            f"is {days:.1f} days old: {cached}"
        )
        warnings.warn(message, StaleCacheWarning, stacklevel=2)
        _logger.warning(message)
        return cached


def cache_contents():
    """List SolarWindPy's cached downloads.

    Returns
    -------
    pandas.DataFrame
        One row per cached URL, indexed by ``url``, with columns ``path``
        (:class:`pathlib.Path` of the local copy) and ``age``
        (:class:`pandas.Timedelta` since it was downloaded).
    """
    rows = [
        {"url": url, "path": path, "age": _age(path)}
        for url, path in sorted(_cached_urls().items())
    ]
    listing = pd.DataFrame(rows, columns=["url", "path", "age"])
    return listing.set_index("url")
