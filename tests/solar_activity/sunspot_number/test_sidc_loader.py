#!/usr/bin/env python
"""Test SIDCLoader against real files it parses itself.

``SIDCLoader.download_data`` reads whatever :func:`pandas.read_csv` is pointed
at. The genuine external boundary is the network, so these tests redirect the
loader at a local file in SILSO's published wire format and at a local cache
directory (via ``Path.home``) and then let the real parsing, the real
arithmetic, and the real filesystem writes run. Nothing patches
:func:`pandas.read_csv`, and nothing asserts that a method was called.

The SILSO format is documented at <https://www.sidc.be/SILSO/infosnmtot> for
the monthly series and <https://www.sidc.be/SILSO/infosndtot> for the daily
series: semicolon-separated, no header, with ``-1`` as the missing-value
sentinel for the standard deviation and observation count.
"""

import re

import numpy as np
import pandas as pd
import pytest

from pathlib import Path

from solarwindpy.solar_activity.base import DataLoader
from solarwindpy.solar_activity.sunspot_number.sidc import (
    SIDCLoader,
    SIDC_ID,
    SSNExtrema,
)

# SILSO's missing-value sentinel.
MISSING = -1

# DataLoader.get_data_ctime recovers the cache date by matching eight
# consecutive digits anywhere in the absolute path, and asserts it finds
# exactly one.
EIGHT_DIGITS = re.compile(r"\d{8}")


def test_the_temporary_directory_can_serve_as_a_cache_root(tmp_path):
    """pytest's tmp_path does not itself contain an eight-digit run.

    This is the canary for the ``fake_home`` fixture below, which skips when
    it does. $TMPDIR is stable per machine, so without this check a host whose
    temp path happened to contain eight consecutive digits would skip every
    cache-backed test in this module and in test_sidc.py, permanently and
    silently, while the suite still reported green.

    ON FAILURE: nothing is wrong with the package. The test environment's
    temporary directory collides with DataLoader's date-matching, so point
    $TMPDIR somewhere without an eight-digit run before trusting this module.
    """
    assert not EIGHT_DIGITS.search(str(tmp_path)), (
        f"tmp_path {tmp_path} contains an 8-digit run, so the cache-backed "
        "tests in this module and in test_sidc.py will all skip"
    )


# ---------------------------------------------------------------------------
# A local stand-in for the SIDC cache root and the SIDC download URL.
# ---------------------------------------------------------------------------
@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Redirect ``Path.home`` so the loader caches under ``tmp_path``.

    Skips if tmp_path carries its own eight-digit run, which would break
    ``get_data_ctime`` for reasons unrelated to the code under test. The
    canary above fails loudly when that happens, so the skip cannot go
    unnoticed.
    """
    if EIGHT_DIGITS.search(str(tmp_path)):
        pytest.skip(f"tmp_path contains an 8-digit run: {tmp_path}")

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    return home


@pytest.fixture
def no_download(monkeypatch):
    """Refuse any attempt to download, so no test can reach the network.

    ``maybe_update_stale_data`` recomputes "today" at load time, so a run that
    straddles local midnight between seeding the cache and loading it would
    consider the cache stale and call ``download_data``. This is a guard on
    the external boundary, not a stand-in that lets a test pass: it turns a
    silent network call into a named failure.
    """

    def refuse(self, new_data_path, old_data_path):
        raise AssertionError(
            "download_data was called; the seeded cache was judged stale, "
            "most likely because this run straddled local midnight"
        )

    monkeypatch.setattr(SIDCLoader, "download_data", refuse)


@pytest.fixture
def make_loader(fake_home):
    """Build a real :class:`SIDCLoader` pointed at a local cache."""

    def _make(key, url="http://example.invalid/unused"):
        return SIDCLoader(key, str(url))

    return _make


def write_silso(path, rows):
    """Write ``rows`` in SILSO's semicolon-separated, headerless wire format."""
    path.write_text("\n".join(";".join(str(field) for field in row) for row in rows))
    return path


def read_written(path):
    """Read back the CSV ``download_data`` wrote."""
    written = pd.read_csv(path.with_suffix(".csv"), index_col=0)
    written.index = pd.DatetimeIndex(written.index)
    return written


# ---------------------------------------------------------------------------
# convert_nans: the SILSO missing-value sentinel.
# ---------------------------------------------------------------------------
def test_convert_nans_replaces_the_sentinel_and_nothing_else(make_loader):
    """NaN appears exactly where the input held SILSO's -1 sentinel.

    Property over the whole frame rather than a handful of cells: the mask of
    NaNs afterwards equals the mask of sentinels beforehand, and every
    surviving value is the one that went in.

    ON FAILURE: either real measurements are being discarded or missing values
    are being kept as -1 and will be averaged into results. The code is wrong.
    """
    loader = make_loader("m")
    data = pd.DataFrame(
        {
            "ssn": [10.5, MISSING, 25.3, MISSING, 8.7],
            "std": [2.1, 3.4, MISSING, 5.6, MISSING],
            "n_obs": [12.0, 15.0, MISSING, 18.0, 20.0],
        }
    )
    sentinel_mask = data == MISSING
    original = data.copy()

    loader.convert_nans(data)

    pd.testing.assert_frame_equal(data.isna(), sentinel_mask)
    kept = ~sentinel_mask
    pd.testing.assert_frame_equal(data[kept], original[kept])


def test_convert_nans_leaves_a_frame_without_sentinels_untouched(make_loader):
    """A frame with no -1 is returned unchanged.

    ON FAILURE: convert_nans is corrupting values it should not touch. The
    code is wrong.
    """
    loader = make_loader("m")
    data = pd.DataFrame({"ssn": [10.5, 20.3, 25.3], "std": [2.1, 3.4, 4.2]})
    original = data.copy()

    loader.convert_nans(data)

    pd.testing.assert_frame_equal(data, original)


def test_convert_nans_mutates_in_place(make_loader):
    """convert_nans edits its argument and returns nothing.

    download_data relies on this: it calls ``self.convert_nans(csv)`` and then
    writes ``csv``, so a version that returned a new frame would silently
    write the unconverted one.

    ON FAILURE: download_data will write -1 sentinels to the cache. The code
    is wrong.
    """
    loader = make_loader("m")
    data = pd.DataFrame({"ssn": [MISSING, 1.0]})

    assert loader.convert_nans(data) is None
    assert data.loc[0, "ssn"] != MISSING
    assert pd.isna(data.loc[0, "ssn"])


def test_convert_nans_leaves_booleans_alone(make_loader):
    """The definitive flag is boolean, so the -1 sentinel cannot apply to it.

    ON FAILURE: the provisional/definitive flag is being destroyed. The code
    is wrong.
    """
    loader = make_loader("m")
    data = pd.DataFrame(
        {"ssn": [10.5, MISSING], "definitive": [True, False]},
    )

    loader.convert_nans(data)

    assert list(data.loc[:, "definitive"]) == [True, False]


# ---------------------------------------------------------------------------
# Where the cache lives.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("key", ["d", "m", "m13", "y", "hd", "hm", "hm13"])
def test_data_path_is_the_cache_root_keyed_by_series(make_loader, fake_home, key):
    """Each series caches under ``<cache root>/sidc/<key>``.

    Identity, composed from the parts: DataLoader supplies
    ``~/solarwindpy/data`` and SIDCLoader appends ``sidc`` and the key, so two
    series never share a cache directory.

    ON FAILURE: two SSN series would overwrite each other's cache. The code is
    wrong.
    """
    loader = make_loader(key)
    assert loader.data_path == fake_home / "solarwindpy" / "data" / "sidc" / key


def test_data_path_does_not_create_the_directory(make_loader):
    """Reading the path is a pure computation with no filesystem side effect.

    ON FAILURE: merely inspecting a loader litters the user's home directory.
    The code is wrong.
    """
    loader = make_loader("m")
    assert not loader.data_path.exists()


def test_loader_carries_the_key_and_url_it_was_given(fake_home):
    """A loader built from a SIDC_ID keeps that identifier's key and URL.

    ON FAILURE: the loader would download one series and cache it as another.
    The code is wrong.
    """
    sidc_id = SIDC_ID("m")
    loader = SIDCLoader(sidc_id.key, sidc_id.url)

    assert isinstance(loader, DataLoader)
    assert loader.key == sidc_id.key
    assert loader.url == sidc_id.url


def test_ctime_is_the_epoch_when_no_cache_exists(make_loader):
    """With an empty cache the loader reports 1970, forcing a fresh download.

    ON FAILURE: a first-run loader would believe it already has current data
    and never download. The code is wrong.
    """
    loader = make_loader("m")
    assert loader.ctime == pd.to_datetime(0)


@pytest.mark.xfail(
    raises=AttributeError,
    strict=True,
    reason=(
        "DataLoader.get_data_age stores the age on self._data_age "
        "(base.py:210) but DataLoader.age reads self._age (base.py:155), "
        "which nothing ever sets, so the property always raises. Reported to "
        "the author rather than fixed: base.py is outside this unit's scope, "
        "and whether `age` or `get_data_age` is the one to change is the "
        "author's call. The message is \"'SIDCLoader' object has no attribute "
        "'_age'\"; pytest.mark.xfail cannot assert on it because the marker "
        "has no match= (it narrows by exception type alone), and the raising "
        "line is in production code so the test cannot choose a narrower "
        "type. raises=AttributeError is therefore the available granularity. "
        "Delete the marker once the property is fixed."
    ),
)
def test_age_is_the_time_since_the_cache_was_written(make_loader):
    """``age`` reports how stale the cache is.

    Identity: age = now - ctime. With an empty cache ctime is the epoch, so
    the age is decades and certainly positive.

    ON FAILURE (that is, if this unexpectedly passes): the property was fixed
    and this xfail should be removed.
    """
    loader = make_loader("m")
    assert loader.age > pd.Timedelta(0)


# ---------------------------------------------------------------------------
# download_data: real parsing of the real wire format.
# ---------------------------------------------------------------------------
def test_download_data_monthly_round_trip(make_loader, tmp_path):
    """A monthly SILSO file survives parse, derivation and write unchanged.

    Every expectation is computed from the input, not captured from a run:
    the index is the month start built from the year and month fields, the
    sunspot numbers are the ones supplied, and the standard error is
    std / sqrt(n_obs) -- the standard error of the mean of n_obs observations.

    ON FAILURE: the download path is corrupting the SILSO series. The code is
    wrong.
    """
    rows = [
        (1996, 1, 1996.042, 17.5, 8.0, 14, 1),
        (1996, 2, 1996.125, 21.5, 9.0, 9, 1),
        (1996, 3, 1996.208, 9.0, 4.0, 16, 0),
    ]
    source = write_silso(tmp_path / "silso_m.csv", rows)
    loader = make_loader("m", url=source)

    target = tmp_path / "20240101"
    loader.download_data(target, tmp_path / "19700101")
    written = read_written(target)

    expected_index = pd.DatetimeIndex(
        [pd.Timestamp(year=row[0], month=row[1], day=1) for row in rows]
    )
    pd.testing.assert_index_equal(written.index, expected_index, check_names=False)

    ssn = np.array([row[3] for row in rows])
    std = np.array([row[4] for row in rows])
    n_obs = np.array([row[5] for row in rows], dtype=float)

    np.testing.assert_allclose(written.loc[:, "ssn"].values, ssn)
    np.testing.assert_allclose(written.loc[:, "std"].values, std)
    np.testing.assert_allclose(written.loc[:, "n_obs"].values, n_obs)
    np.testing.assert_allclose(written.loc[:, "std_error"].values, std / np.sqrt(n_obs))
    assert list(written.loc[:, "definitive"]) == [True, True, False]


def test_download_data_propagates_the_missing_sentinel_to_nan(make_loader, tmp_path):
    """A month SILSO marks as missing arrives as NaN, not as -1.

    ON FAILURE: -1 would be averaged into sunspot statistics as if it were a
    measurement. The code is wrong.
    """
    rows = [
        (1996, 1, 1996.042, 17.5, 8.0, 14, 1),
        (1996, 2, 1996.125, MISSING, MISSING, MISSING, 0),
    ]
    source = write_silso(tmp_path / "silso_m.csv", rows)
    loader = make_loader("m", url=source)

    target = tmp_path / "20240101"
    loader.download_data(target, tmp_path / "19700101")
    written = read_written(target)

    assert written.loc[:, ["ssn", "std", "n_obs"]].iloc[1].isna().all()
    assert not written.loc[:, ["ssn", "std", "n_obs"]].iloc[0].isna().any()


def test_download_data_daily_round_trip(make_loader, tmp_path):
    """A daily SILSO file is indexed by its own year, month and day fields.

    Unlike the monthly series the day is read from the file rather than fixed
    at 1, so this covers the other branch of the datetime construction.

    ON FAILURE: daily measurements are being stamped with the wrong date. The
    code is wrong.
    """
    rows = [
        (1996, 1, 5, 1996.011, 17.5, 8.0, 14, 1),
        (1996, 2, 29, 1996.163, 21.5, 9.0, 9, 1),
    ]
    source = write_silso(tmp_path / "silso_d.csv", rows)
    loader = make_loader("d", url=source)

    target = tmp_path / "20240101"
    loader.download_data(target, tmp_path / "19700101")
    written = read_written(target)

    expected_index = pd.DatetimeIndex(
        [pd.Timestamp(year=row[0], month=row[1], day=row[2]) for row in rows]
    )
    pd.testing.assert_index_equal(written.index, expected_index, check_names=False)

    std = np.array([row[5] for row in rows])
    n_obs = np.array([row[6] for row in rows], dtype=float)
    np.testing.assert_allclose(written.loc[:, "std_error"].values, std / np.sqrt(n_obs))


def test_download_data_yearly_round_trip(make_loader, tmp_path):
    """The yearly series is indexed by its decimal year.

    The yearly SILSO file dates each row by a decimal year rather than by
    year/month fields, so download_data converts it through
    ``astropy.time.Time(..., format="decimalyear")``. The expectation here is
    the definition of a decimal year -- the fraction of the way through the
    calendar year -- recomputed from the resulting timestamp, not read back
    from astropy. Tolerance is one day, the resolution the series carries.

    ON FAILURE: yearly sunspot numbers are stamped with the wrong epoch, or an
    astropy API change broke the conversion. The code is wrong.
    """
    decimal_years = [1996.5, 1997.0, 1998.25]
    rows = [
        (decimal_years[0], 17.5, 8.0, 14, 1),
        (decimal_years[1], 21.5, 9.0, 9, 1),
        (decimal_years[2], 9.0, 4.0, 16, 0),
    ]
    source = write_silso(tmp_path / "silso_y.csv", rows)
    loader = make_loader("y", url=source)

    target = tmp_path / "20240101"
    loader.download_data(target, tmp_path / "19700101")
    written = read_written(target)

    assert len(written) == len(rows)
    assert written.index.is_monotonic_increasing

    for timestamp, decimal_year in zip(written.index, decimal_years):
        year = int(decimal_year)
        start = pd.Timestamp(year=year, month=1, day=1)
        end = pd.Timestamp(year=year + 1, month=1, day=1)
        recovered = year + (timestamp - start) / (end - start)
        assert abs(recovered - decimal_year) < 1.0 / 365.0

    std = np.array([row[2] for row in rows])
    n_obs = np.array([row[3] for row in rows], dtype=float)
    np.testing.assert_allclose(written.loc[:, "std_error"].values, std / np.sqrt(n_obs))


def test_download_data_hemispheric_standard_errors(make_loader, tmp_path):
    """Each hemisphere's standard error is its own std over its own sqrt(count).

    Identity per hemisphere: the total, northern and southern standard errors
    are formed from the matching standard deviation and observation count, so
    a mis-paired column would show up as a wrong value here rather than as a
    renamed column.

    ON FAILURE: hemispheric uncertainties are paired with the wrong counts.
    The code is wrong.
    """
    rows = [
        (2015, 1, 2015.042, 67.0, 40.0, 27.0, 9.0, 6.0, 4.0, 900, 400, 500, 1),
        (2015, 2, 2015.125, 44.8, 20.0, 24.8, 8.0, 5.0, 3.0, 400, 100, 900, 1),
    ]
    source = write_silso(tmp_path / "silso_hm.csv", rows)
    loader = make_loader("hm", url=source)

    target = tmp_path / "20240101"
    loader.download_data(target, tmp_path / "19700101")
    written = read_written(target)

    for hemisphere, std_column, count_column in (
        ("total", "total_std", "n_total"),
        ("north", "north_std", "n_north"),
        ("south", "south_std", "n_south"),
    ):
        derived = [
            column for column in written.columns if column.startswith(hemisphere)
        ]
        error_column = [column for column in derived if column.endswith("std_error")]
        assert len(error_column) == 1, f"no unique std_error column for {hemisphere}"

        expected = written.loc[:, std_column] / np.sqrt(written.loc[:, count_column])
        np.testing.assert_allclose(
            written.loc[:, error_column[0]].values, expected.values
        )


def test_download_data_removes_the_superseded_cache_file(make_loader, tmp_path):
    """Writing today's cache deletes yesterday's.

    Round trip on the filesystem: the old file exists going in and is gone
    coming out, while the new one exists. DataLoader.get_data_ctime asserts
    it finds exactly one cache date, so a stale file left behind breaks the
    next load.

    ON FAILURE: the cache accumulates dated files and the next load raises.
    The code is wrong.
    """
    rows = [(1996, 1, 1996.042, 17.5, 8.0, 14, 1)]
    source = write_silso(tmp_path / "silso_m.csv", rows)
    loader = make_loader("m", url=source)

    old = tmp_path / "19960101"
    old.with_suffix(".csv").write_text("stale\n")
    new = tmp_path / "20240101"

    loader.download_data(new, old)

    assert not old.with_suffix(".csv").exists()
    assert new.with_suffix(".csv").exists()


def test_download_data_tolerates_a_missing_previous_cache(make_loader, tmp_path):
    """A first download, with nothing to delete, still writes its output.

    ON FAILURE: the very first download raises FileNotFoundError. The code is
    wrong.
    """
    rows = [(1996, 1, 1996.042, 17.5, 8.0, 14, 1)]
    source = write_silso(tmp_path / "silso_m.csv", rows)
    loader = make_loader("m", url=source)

    new = tmp_path / "20240101"
    loader.download_data(new, tmp_path / "never_existed")

    assert new.with_suffix(".csv").exists()


def test_download_data_refuses_a_series_with_no_column_layout(make_loader, tmp_path):
    """A key with no declared dtypes and columns is refused, not guessed at.

    sidc.py declares the column layout of each SILSO series explicitly. An
    unknown key has no layout, and parsing it positionally would mislabel
    every column, so the loader raises instead.

    ON FAILURE: an unrecognised series would be parsed with whatever columns
    happened to be lying around. The code is wrong.
    """
    loader = make_loader("not_a_series")

    with pytest.raises(NotImplementedError, match="You have not yet used the SSN"):
        loader.download_data(tmp_path / "new", tmp_path / "old")


# ---------------------------------------------------------------------------
# load_data: cycle assignment against the real extrema table.
# ---------------------------------------------------------------------------
def test_load_data_assigns_each_measurement_to_its_containing_cycle(
    make_loader, fake_home, no_download
):
    """Every measurement is labelled with the solar cycle whose interval contains it.

    The cache is seeded on disk and read back by the real loader, and the
    expected cycle for each timestamp is recomputed independently from a fresh
    SSNExtrema's Cycle intervals rather than taken from the loader's own
    answer.

    ON FAILURE: measurements are attributed to the wrong solar cycle, and
    every cycle-resolved result built on them is wrong. The code is wrong.
    """
    loader = make_loader("m13")
    cache = loader.data_path
    cache.mkdir(parents=True)

    index = pd.date_range("1990-01-01", "2018-01-01", freq="6MS")
    frame = pd.DataFrame(
        {"ssn": np.linspace(10.0, 120.0, len(index)), "std": 1.0, "n_obs": 10},
        index=index,
    )
    today = pd.to_datetime("today").strftime("%Y%m%d")
    frame.to_csv(cache / f"{today}.csv")

    loader.get_data_ctime()
    loader.load_data()

    cycles = SSNExtrema().cycle_intervals.loc[:, "Cycle"]
    expected = []
    for timestamp in index:
        containing = [
            number for number, interval in cycles.items() if timestamp in interval
        ]
        assert len(containing) == 1, f"{timestamp} is in {len(containing)} cycles"
        expected.append(containing[0])

    assert [int(value) for value in loader.data.loc[:, "cycle"]] == expected


def test_load_data_preserves_the_measurements_it_labels(
    make_loader, fake_home, no_download
):
    """Cycle assignment adds a column without disturbing the measurements.

    ON FAILURE: the concat that attaches the cycle label is reordering or
    dropping data. The code is wrong.
    """
    loader = make_loader("m13")
    cache = loader.data_path
    cache.mkdir(parents=True)

    index = pd.date_range("2005-01-01", "2015-01-01", freq="MS")
    frame = pd.DataFrame(
        {"ssn": np.linspace(10.0, 120.0, len(index)), "std": 1.0, "n_obs": 10},
        index=index,
    )
    today = pd.to_datetime("today").strftime("%Y%m%d")
    frame.to_csv(cache / f"{today}.csv")

    loader.get_data_ctime()
    loader.load_data()

    pd.testing.assert_index_equal(loader.data.index, index, check_names=False)
    np.testing.assert_allclose(
        loader.data.loc[:, "ssn"].values, frame.loc[:, "ssn"].values
    )
    assert "cycle" in loader.data.columns
