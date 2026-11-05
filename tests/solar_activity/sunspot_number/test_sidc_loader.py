#!/usr/bin/env python
"""Test SIDCLoader against real files it parses itself.

``SIDCLoader.read_data`` parses whatever file it is handed. The genuine
external boundaries are the network and the download cache, so these tests
hand the loader local files in SILSO's published wire format, seed the cache
(kept under ``tmp_path`` by the autouse ``isolated_cache`` fixture) with them,
and then let the real parsing and the real arithmetic run. Nothing patches
:func:`pandas.read_csv`, and nothing asserts that a method was called.

The SILSO format is documented at <https://www.sidc.be/SILSO/infosnmtot> for
the monthly series and <https://www.sidc.be/SILSO/infosndtot> for the daily
series: semicolon-separated, no header, with ``-1`` as the missing-value
sentinel for the standard deviation and observation count.
"""

import numpy as np
import pandas as pd
import pytest

from solarwindpy.solar_activity import cache as cache_module
from solarwindpy.solar_activity.base import DataLoader
from solarwindpy.solar_activity.sunspot_number.sidc import (
    SIDCLoader,
    SIDC_ID,
    SSNExtrema,
)

# SILSO's missing-value sentinel.
MISSING = -1


# ---------------------------------------------------------------------------
# A guard on the download and a real loader.
# ---------------------------------------------------------------------------
@pytest.fixture
def no_download(monkeypatch):
    """Refuse any attempt to download, so no test can reach the network.

    A seeded cache is fresh, so loading it must not download. This is a guard
    on the external boundary, ``cache._download_file``, the one call through
    which SolarWindPy downloads; it is not a stand-in that lets a test pass:
    it turns a silent network call into a named failure.
    """

    def refuse(url, cache):
        raise AssertionError(
            f"a download of {url} was attempted although the seeded cache is fresh"
        )

    monkeypatch.setattr(cache_module, "_download_file", refuse)


@pytest.fixture
def make_loader():
    """Build a real :class:`SIDCLoader`."""

    def _make(key, url="http://example.invalid/unused"):
        return SIDCLoader(key, str(url))

    return _make


def write_silso(path, rows):
    """Write ``rows`` in SILSO's semicolon-separated, headerless wire format."""
    path.write_text("\n".join(";".join(str(field) for field in row) for row in rows))
    return path


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

    read_data relies on this: it calls ``self.convert_nans(csv)`` and then
    returns ``csv``, so a version that returned a new frame would silently
    return the unconverted one.

    ON FAILURE: read_data will return -1 sentinels as data. The code
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
# The loader's identity and cache age.
# ---------------------------------------------------------------------------
def test_loader_carries_the_key_and_url_it_was_given():
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


def test_age_is_the_time_since_the_cache_was_written(make_loader):
    """``age`` reports how stale the cache is.

    Identity: age = now - ctime. With an empty cache ctime is the epoch, so
    the age is decades and certainly positive.

    ON FAILURE: the code is wrong.
    """
    loader = make_loader("m")
    assert loader.age > pd.Timedelta(0)


# ---------------------------------------------------------------------------
# read_data: real parsing of the real wire format.
# ---------------------------------------------------------------------------
def test_read_data_monthly_round_trip(make_loader, tmp_path):
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

    written = loader.read_data(source)

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


def test_read_data_propagates_the_missing_sentinel_to_nan(make_loader, tmp_path):
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

    written = loader.read_data(source)

    assert written.loc[:, ["ssn", "std", "n_obs"]].iloc[1].isna().all()
    assert not written.loc[:, ["ssn", "std", "n_obs"]].iloc[0].isna().any()


def test_read_data_daily_round_trip(make_loader, tmp_path):
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

    written = loader.read_data(source)

    expected_index = pd.DatetimeIndex(
        [pd.Timestamp(year=row[0], month=row[1], day=row[2]) for row in rows]
    )
    pd.testing.assert_index_equal(written.index, expected_index, check_names=False)

    std = np.array([row[5] for row in rows])
    n_obs = np.array([row[6] for row in rows], dtype=float)
    np.testing.assert_allclose(written.loc[:, "std_error"].values, std / np.sqrt(n_obs))


def test_read_data_yearly_round_trip(make_loader, tmp_path):
    """The yearly series is indexed by its decimal year.

    The yearly SILSO file dates each row by a decimal year rather than by
    year/month fields, so read_data converts it through
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

    written = loader.read_data(source)

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


def test_read_data_hemispheric_standard_errors(make_loader, tmp_path):
    """Each hemisphere's standard error is ``<h>_std_error``, its std over sqrt(count).

    Identity per hemisphere: the total, northern and southern standard errors
    are formed from the matching standard deviation and observation count, so
    a mis-paired column would show up as a wrong value here. Each is named
    after its standard deviation column, ``<h>_std``, with ``_error``
    appended.

    ON FAILURE: hemispheric uncertainties are misnamed or paired with the
    wrong counts. The code is wrong.
    """
    rows = [
        (2015, 1, 2015.042, 67.0, 40.0, 27.0, 9.0, 6.0, 4.0, 900, 400, 500, 1),
        (2015, 2, 2015.125, 44.8, 20.0, 24.8, 8.0, 5.0, 3.0, 400, 100, 900, 1),
    ]
    source = write_silso(tmp_path / "silso_hm.csv", rows)
    loader = make_loader("hm", url=source)

    written = loader.read_data(source)

    for hemisphere, std_column, count_column in (
        ("total", "total_std", "n_total"),
        ("north", "north_std", "n_north"),
        ("south", "south_std", "n_south"),
    ):
        error_column = f"{std_column}_error"
        assert error_column in written.columns, f"no {error_column} column"

        expected = written.loc[:, std_column] / np.sqrt(written.loc[:, count_column])
        np.testing.assert_allclose(written.loc[:, error_column].values, expected.values)


def test_read_data_refuses_a_series_with_no_column_layout(make_loader, tmp_path):
    """A key with no declared dtypes and columns is refused, not guessed at.

    sidc.py declares the column layout of each SILSO series explicitly. An
    unknown key has no layout, and parsing it positionally would mislabel
    every column, so the loader raises instead.

    ON FAILURE: an unrecognised series would be parsed with whatever columns
    happened to be lying around. The code is wrong.
    """
    loader = make_loader("not_a_series")

    with pytest.raises(NotImplementedError, match="You have not yet used the SSN"):
        loader.read_data(tmp_path / "unread.csv")


# ---------------------------------------------------------------------------
# load_data: cycle assignment against the real extrema table.
# ---------------------------------------------------------------------------
def test_load_data_assigns_each_measurement_to_its_containing_cycle(
    make_loader, seed_m13, no_download
):
    """Every measurement is labelled with the solar cycle whose interval contains it.

    The cache is seeded with the series in SILSO's layout and read back by
    the real loader, and the
    expected cycle for each timestamp is recomputed independently from a fresh
    SSNExtrema's Cycle intervals rather than taken from the loader's own
    answer.

    ON FAILURE: measurements are attributed to the wrong solar cycle, and
    every cycle-resolved result built on them is wrong. The code is wrong.
    """
    loader = make_loader("m13")

    index = pd.date_range("1990-01-01", "2018-01-01", freq="6MS")
    frame = pd.DataFrame(
        {"ssn": np.linspace(10.0, 120.0, len(index)), "std": 1.0, "n_obs": 10},
        index=index,
    )
    seed_m13(frame, url=loader.url)

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
    make_loader, seed_m13, no_download
):
    """Cycle assignment adds a column without disturbing the measurements.

    ON FAILURE: the concat that attaches the cycle label is reordering or
    dropping data. The code is wrong.
    """
    loader = make_loader("m13")

    index = pd.date_range("2005-01-01", "2015-01-01", freq="MS")
    frame = pd.DataFrame(
        {"ssn": np.linspace(10.0, 120.0, len(index)), "std": 1.0, "n_obs": 10},
        index=index,
    )
    seed_m13(frame, url=loader.url)

    loader.load_data()

    pd.testing.assert_index_equal(loader.data.index, index, check_names=False)
    np.testing.assert_allclose(
        loader.data.loc[:, "ssn"].values, frame.loc[:, "ssn"].values
    )
    assert "cycle" in loader.data.columns
