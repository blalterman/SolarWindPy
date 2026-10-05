"""Shared fixtures for ICMECAT tests.

The catalog download is the network boundary. Unit tests point the module's
``ICMECAT_URL`` constant at a CSV written under ``tmp_path``, so the real
``pandas.read_csv`` parses a real file exactly as it parses the HELIO4CAST one.
No library function is replaced.
"""

import pandas as pd
import pytest

from solarwindpy.solar_activity.icme import icmecat

T = pd.Timestamp
NaT = pd.NaT

# Hand-built six-event catalog. Spacecraft use the catalog's own spellings
# ("ULYSSES" is all caps in HELIO4CAST), so a caller's "Ulysses" exercises the
# case-insensitive match. Each interval_end source appears:
#
#   id  sc_insitu  icme_start        mo_start          mo_end      interval_end  source
#   U1  ULYSSES    2000-01-10        2000-01-11        2000-01-15  2000-01-15    mo_end
#   U2  ULYSSES    2000-02-15        2000-02-16        2000-02-20  2000-02-20    mo_end
#   U3  ULYSSES    2000-03-20        2000-03-21        NaT         2000-03-22    mo_start + 24 h
#   W1  Wind       2000-04-01        NaT               NaT         2000-04-02    icme_start + 24 h
#   W2  Wind       2000-05-01        2000-05-02        2000-05-04  2000-05-04    mo_end
#   S1  STEREO-A   2000-06-01        2000-06-01 12:00  2000-06-03  2000-06-03    mo_end
#
# mo_bmax is a catalog column that ICMECAT.intervals does not carry.
CATALOG = pd.DataFrame(
    {
        "icmecat_id": ["U1", "U2", "U3", "W1", "W2", "S1"],
        "sc_insitu": ["ULYSSES", "ULYSSES", "ULYSSES", "Wind", "Wind", "STEREO-A"],
        "icme_start_time": [
            T("2000-01-10"),
            T("2000-02-15"),
            T("2000-03-20"),
            T("2000-04-01"),
            T("2000-05-01"),
            T("2000-06-01"),
        ],
        "mo_start_time": [
            T("2000-01-11"),
            T("2000-02-16"),
            T("2000-03-21"),
            NaT,
            T("2000-05-02"),
            T("2000-06-01 12:00"),
        ],
        "mo_end_time": [
            T("2000-01-15"),
            T("2000-02-20"),
            NaT,
            NaT,
            T("2000-05-04"),
            T("2000-06-03"),
        ],
        "mo_sc_heliodistance": [1.5, 2.5, 3.5, 1.0, 1.0, 0.75],
        "mo_sc_lat_heeq": [10.0, -20.0, 30.0, 0.5, -0.5, 2.0],
        "mo_sc_long_heeq": [100.0, 200.0, 300.0, 5.0, 6.0, 7.0],
        "mo_bmax": [8.0, 9.0, 10.0, 11.0, 12.0, 13.0],
    }
)


@pytest.fixture(autouse=True)
def _no_network(request, tmp_path, monkeypatch):
    """Point ``ICMECAT_URL`` at a missing local file unless the test is ``integration``.

    A unit test that forgets ``serve_catalog`` then fails with
    ``ICMECATDownloadError`` instead of silently reaching helioforecast.space.
    """
    if request.node.get_closest_marker("integration") is None:
        monkeypatch.setattr(
            icmecat, "ICMECAT_URL", str(tmp_path / "no-network-in-unit-tests.csv")
        )


@pytest.fixture
def catalog():
    """A fresh copy of the hand-built ``CATALOG`` table."""
    return CATALOG.copy()


@pytest.fixture
def serve_catalog(tmp_path, monkeypatch):
    """Return ``serve(frame)``: write ``frame`` as CSV and point ``ICMECAT_URL`` at it.

    ``serve()`` with no argument serves ``CATALOG``. Returns the CSV path.
    """

    def _serve(frame=None):
        frame = CATALOG if frame is None else frame
        path = tmp_path / "icmecat.csv"
        frame.to_csv(path, index=False)
        monkeypatch.setattr(icmecat, "ICMECAT_URL", str(path))
        return path

    return _serve
