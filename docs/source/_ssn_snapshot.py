"""Serve SILSO's 13-month smoothed sunspot number to the docs from a snapshot.

A plot block in the Usage guide calls ``SIDC("m13")``, which downloads the
series from SILSO, as a reader's session does. The docs build (``conf.py``)
and ``tests/test_docs_plot_blocks.py`` instead call :func:`seed_ssn_snapshot`,
which points SolarWindPy's download cache at a private directory and stores the
committed snapshot there under the URL the loader fetches. ``fetch`` finds a
copy younger than the loader's freshness window and returns it without a
download. The user's own cache, which may hold the full series under the same
URL, is never touched.
"""

from pathlib import Path

from astropy.utils.data import import_file_to_cache

from solarwindpy.solar_activity.cache import PKGNAME
from solarwindpy.solar_activity.sunspot_number.sidc import SIDC_ID

#: The committed snapshot; its ``#`` lines name the source and download date.
SNAPSHOT = Path(__file__).resolve().parent / "_data" / "SN_ms_tot_1994-2026.csv"

#: The URL ``SIDC("m13")`` downloads, the cache key the snapshot is stored under.
URL = SIDC_ID("m13").url


def seed_ssn_snapshot(root, setenv):
    """Make ``root`` SolarWindPy's download cache, holding the snapshot as ``URL``.

    Parameters
    ----------
    root : str or pathlib.Path
        Directory that plays the role of ``~/.cache``; it is created if absent.
    setenv : callable
        Called as ``setenv("XDG_CACHE_HOME", str(root))``, e.g.
        ``os.environ.__setitem__`` or pytest's ``monkeypatch.setenv``.

    Returns
    -------
    pathlib.Path
        The cached copy: the snapshot without its ``#`` lines, which the
        loader would not parse, written now, so it is fresh.
    """
    root = Path(root)
    (root / PKGNAME).mkdir(parents=True, exist_ok=True)
    setenv("XDG_CACHE_HOME", str(root))
    lines = SNAPSHOT.read_text().splitlines(keepends=True)
    data = root / "snmstotcsv.csv"
    data.write_text("".join(line for line in lines if not line.startswith("#")))
    return Path(import_file_to_cache(URL, str(data), pkgname=PKGNAME))
