"""Behaviour of the solar-activity base classes in ``solar_activity.base``.

The classes under test are abstract, so each is exercised through the
smallest concrete subclass that fills in its abstract hooks: those subclasses
are real implementations, not stand-ins. The only external boundary is the
cache directory a ``DataLoader`` reads and writes, which lives under
``tmp_path``. Expected values are chosen inputs or hand-computed dates.
"""

import logging
import re

import numpy as np
import pandas as pd
import pytest

from solarwindpy.solar_activity.base import (
    ID,
    ActivityIndicator,
    DataLoader,
    IndicatorExtrema,
)
from tests.tolerances import exact

# ---------------------------------------------------------------------------
# Concrete subclasses
# ---------------------------------------------------------------------------


class Catalog(ID):
    """An identifier whose URLs are chosen so the joins are known by hand."""

    _url_base = "https://example.org/archive/"
    _trans_url = {"daily": "daily/latest.csv", "monthly": "monthly.csv"}


class CacheLoader(DataLoader):
    """A loader whose cache is a chosen directory and whose download is local.

    ``download_data`` writes ``DOWNLOADED`` into the new slot and removes the
    old one, which is what the package's real loaders do with the bytes they
    fetch.
    """

    DOWNLOADED = pd.DataFrame(
        {"value": [7.0, 8.0, 9.0]},
        index=pd.DatetimeIndex(["2021-03-01", "2021-03-02", "2021-03-03"]),
    )

    def __init__(self, key, url, root, allow_download=True):
        self._root = root
        self._allow_download = allow_download
        super().__init__(key, url)

    @property
    def data_path(self):
        return self._root

    @staticmethod
    def convert_nans(data):
        return data.replace(-1, np.nan)

    def download_data(self, new_data_path, old_data_path):
        if not self._allow_download:
            raise AssertionError("download attempted although the cache is current")
        self.DOWNLOADED.to_csv(new_data_path.with_suffix(".csv"))
        old_data_path.with_suffix(".csv").unlink(missing_ok=True)

    def load_data(self):
        super().load_data()


class Indicator(ActivityIndicator):
    """An indicator that fills in the abstract hooks and nothing else."""

    def __init__(self, loader=None):
        self._init_logger()
        self._loader = loader

    def interpolate_data(self, source_data, target_index):
        return super().interpolate_data(source_data, target_index)

    @property
    def normalized(self):
        return None

    def set_extrema(self):
        pass

    def run_normalization(self):
        pass


class Extrema(IndicatorExtrema):
    """Extrema read from a table the test hands in."""

    def load_or_set_data(self, table):
        self._data = table


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TODAY_STR_FORMAT = "%Y%m%d"


def today():
    """Today's date at midnight, as the package computes it."""
    return pd.Timestamp.today().normalize()


@pytest.fixture
def cache_root(tmp_path):
    """An empty cache directory whose path holds no 8-digit run.

    ``DataLoader.get_data_ctime`` reads the cache date from the first
    8-digit run anywhere in each CSV's absolute path, so a ``tmp_path`` that
    already contains one would be misread as a date.
    """
    if re.search(r"\d{8}", str(tmp_path)):
        pytest.skip(f"tmp_path contains an 8-digit run: {tmp_path}")
    root = tmp_path / "cache"
    root.mkdir()
    return root


def extrema_table(max3="2015-01-01"):
    """Three cycles, extrema three years apart, on round dates."""
    table = pd.DataFrame(
        {
            "Min": pd.to_datetime(["2000-01-01", "2006-01-01", "2012-01-01"]),
            "Max": pd.to_datetime(["2003-01-01", "2009-01-01", max3]),
        },
        index=pd.Index([1, 2, 3], name="Number"),
    )
    table.columns.name = "kind"
    return table


@pytest.fixture
def extrema():
    return Extrema(extrema_table())


def iv(left, right):
    """Right-closed interval between two dates, as ``pd.cut`` produces."""
    return pd.Interval(pd.Timestamp(left), pd.Timestamp(right))


EPOCHS = pd.DatetimeIndex(["2001-06-01", "2004-06-01", "2007-06-01", "2013-06-01"])


# ---------------------------------------------------------------------------
# Base and ID
# ---------------------------------------------------------------------------


def test_str_and_logger_name_the_concrete_class():
    """``str`` and the logger both name the concrete class.

    ON FAILURE: the code is wrong.
    """
    catalog = Catalog("daily")
    assert str(catalog) == "Catalog"
    assert isinstance(catalog.logger, logging.Logger)
    assert catalog.logger.name.split(".")[-1] == "Catalog"


def test_id_url_joins_the_key_path_onto_the_base_url():
    """The URL is the key's path resolved against the base URL.

    Hand-joined: a relative path against a base ending in ``/`` appends.

    ON FAILURE: the code is wrong.
    """
    catalog = Catalog("daily")
    assert catalog.key == "daily"
    assert catalog.url == "https://example.org/archive/daily/latest.csv"


def test_id_set_key_replaces_key_and_url_together():
    """``set_key`` moves both the key and the URL to the new product.

    ON FAILURE: the code is wrong.
    """
    catalog = Catalog("daily")
    catalog.set_key("monthly")
    assert catalog.key == "monthly"
    assert catalog.url == "https://example.org/archive/monthly.csv"


def test_id_rejects_an_unknown_key():
    """An unmapped key raises rather than building a URL.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(NotImplementedError, match="yearly key unavailable"):
        Catalog("yearly")


def test_id_without_a_url_table_cannot_be_instantiated():
    """A subclass that omits an abstract URL property is refused.

    ON FAILURE: the code is wrong.
    """

    class NoTable(ID):
        _url_base = "https://example.org/"

    with pytest.raises(TypeError, match="abstract"):
        NoTable("daily")


@pytest.mark.parametrize("cls", [DataLoader, ActivityIndicator, IndicatorExtrema])
def test_abstract_bases_cannot_be_instantiated_directly(cls):
    """Each abstract base is refused until a subclass fills in its hooks.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(TypeError, match="abstract"):
        cls()


# ---------------------------------------------------------------------------
# DataLoader
# ---------------------------------------------------------------------------


def test_loader_keeps_key_and_url(cache_root):
    """The loader reports the key and URL it was built with.

    ON FAILURE: the code is wrong.
    """
    loader = CacheLoader("daily", "https://example.org/daily.csv", cache_root)
    assert loader.key == "daily"
    assert loader.url == "https://example.org/daily.csv"


def test_ctime_is_the_date_in_the_cached_file_name(cache_root):
    """The cache's creation time is the date written in its file name.

    Chosen input: a file named ``20230315.csv`` means 2023-03-15.

    ON FAILURE: the code is wrong.
    """
    (cache_root / "20230315.csv").write_text("t,value\n")
    loader = CacheLoader("daily", "unused", cache_root)
    assert loader.ctime == pd.Timestamp("2023-03-15")


def test_ctime_of_an_empty_cache_is_the_unix_epoch(cache_root):
    """With nothing cached, the creation time is 1970-01-01, i.e. stale.

    ON FAILURE: the code is wrong.
    """
    loader = CacheLoader("daily", "unused", cache_root)
    assert loader.ctime == pd.Timestamp("1970-01-01")


def test_age_is_the_time_since_the_cache_was_written(cache_root):
    """``age`` = now - ctime, for a cache written five days ago.

    Identity: ctime is midnight five days back, so the age is at least five
    days and less than six.

    ON FAILURE: the code is wrong.
    """
    written = today() - pd.Timedelta(days=5)
    (cache_root / f"{written.strftime(TODAY_STR_FORMAT)}.csv").write_text("t\n")
    loader = CacheLoader("daily", "unused", cache_root)
    assert pd.Timedelta(days=5) <= loader.age < pd.Timedelta(days=6)


def test_load_data_downloads_into_todays_slot_when_the_cache_is_stale(cache_root):
    """A stale cache is replaced by today's download, which is then read.

    Chosen input: an old cache file dated 2020-01-01. The loader must pass
    ``download_data`` the old slot (so it is removed) and today's slot (so the
    read finds the new file).

    ON FAILURE: the code is wrong.
    """
    old = cache_root / "20200101.csv"
    old.write_text("t,value\n2020-01-01,1.0\n")
    loader = CacheLoader("daily", "unused", cache_root)
    loader.load_data()

    new = cache_root / f"{today().strftime(TODAY_STR_FORMAT)}.csv"
    assert new.exists()
    assert not old.exists()
    pd.testing.assert_frame_equal(
        loader.data, CacheLoader.DOWNLOADED, check_freq=False, check_names=False
    )


def test_load_data_reads_a_current_cache_without_downloading(cache_root):
    """A cache written today is read as-is, with a datetime index.

    Chosen input: two rows written to today's slot; ``download_data`` refuses
    to run, so reaching it fails the test.

    ON FAILURE: the code is wrong.
    """
    cached = pd.DataFrame(
        {"value": [4.0, 5.0]},
        index=pd.DatetimeIndex(["2024-07-01", "2024-07-02"]),
    )
    cached.to_csv(cache_root / f"{today().strftime(TODAY_STR_FORMAT)}.csv")
    loader = CacheLoader("daily", "unused", cache_root, allow_download=False)
    loader.load_data()

    assert isinstance(loader.data.index, pd.DatetimeIndex)
    pd.testing.assert_frame_equal(
        loader.data, cached, check_freq=False, check_names=False
    )


# ---------------------------------------------------------------------------
# ActivityIndicator
# ---------------------------------------------------------------------------


def test_indicator_data_is_the_loaders_data(cache_root):
    """``ActivityIndicator.data`` is a shortcut to its loader's data.

    ON FAILURE: the code is wrong.
    """
    loader = CacheLoader("daily", "unused", cache_root)
    loader.load_data()
    assert Indicator(loader).data is loader.data


def test_indicator_id_round_trips_through_set_id():
    """``set_id`` stores the identifier that ``id`` returns.

    ON FAILURE: the code is wrong.
    """
    indicator = Indicator()
    catalog = Catalog("monthly")
    indicator.set_id(catalog)
    assert indicator.id is catalog


def test_set_id_refuses_something_that_is_not_an_id():
    """A bare key string is not an identifier and is refused.

    Either refusal type is accepted: today's check is an ``assert``, and a
    rewrite raising ``TypeError`` keeps the same promise.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises((AssertionError, TypeError)):
        Indicator().set_id("monthly")


def test_norm_by_before_normalizing_asks_for_normalization():
    """Reading ``norm_by`` before normalizing names the missing step.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(AttributeError, match="Please calculate normalized quantity"):
        Indicator().norm_by


LINEAR_SOURCE = pd.Series(
    [0.0, 10.0, 20.0, 30.0, 40.0],
    index=pd.date_range("2020-01-01", periods=5, freq="D"),
    name="flux",
)


def test_interpolation_reproduces_a_straight_line():
    """Interpolating a straight line in time returns points on that line.

    Hand-computed: the source rises 10 per day from 0 at 2020-01-01, so
    2020-01-02 12:00 is 15 and 2020-01-04 06:00 is 32.5. Any interpolant
    through a straight line reproduces it.

    ON FAILURE: the code is wrong.
    """
    target = pd.DatetimeIndex(["2020-01-02 12:00", "2020-01-04 06:00"])
    out = Indicator().interpolate_data(LINEAR_SOURCE, target)

    assert list(out.columns) == ["flux"]
    assert out.index.equals(target)
    assert out["flux"].to_numpy() == exact([15.0, 32.5])


def test_interpolation_blanks_targets_outside_the_source_span():
    """Targets before the first or after the last source time are NaN.

    ON FAILURE: the code is wrong.
    """
    target = pd.DatetimeIndex(["2019-12-31", "2020-01-03", "2020-01-06"])
    out = Indicator().interpolate_data(LINEAR_SOURCE, target)["flux"]

    assert np.isnan(out.iloc[0])
    assert out.iloc[1] == exact(20.0)
    assert np.isnan(out.iloc[2])


def test_interpolation_handles_each_column_and_keeps_the_result():
    """Each column is interpolated independently; ``interpolated`` keeps it.

    Hand-computed: ``double`` is twice ``flux``, so at 2020-01-02 12:00 it
    is 30.

    ON FAILURE: the code is wrong.
    """
    source = pd.DataFrame({"flux": LINEAR_SOURCE, "double": 2 * LINEAR_SOURCE})
    target = pd.DatetimeIndex(["2020-01-02 12:00"])
    indicator = Indicator()
    out = indicator.interpolate_data(source, target)

    assert out.loc[target[0], "flux"] == exact(15.0)
    assert out.loc[target[0], "double"] == exact(30.0)
    assert indicator.interpolated is out


def test_interpolation_refuses_a_source_with_nans():
    """A NaN in the source is refused, not silently interpolated.

    ON FAILURE: the code is wrong.
    """
    source = LINEAR_SOURCE.copy()
    source.iloc[2] = np.nan
    with pytest.raises(NotImplementedError, match="drop NaNs"):
        Indicator().interpolate_data(source, LINEAR_SOURCE.index)


# ---------------------------------------------------------------------------
# IndicatorExtrema: cycle intervals
# ---------------------------------------------------------------------------


def test_cycle_intervals_run_min_to_max_to_next_min(extrema):
    """Rise is Min to Max, Fall is Max to next Min, Cycle is Min to next Min.

    Chosen input: the three-cycle table in ``extrema_table``. The last cycle
    has passed its maximum but not its next minimum, so it falls until
    today.

    ON FAILURE: the code is wrong.
    """
    got = extrema.cycle_intervals
    expected = {
        1: ("2000-01-01", "2003-01-01", "2006-01-01"),
        2: ("2006-01-01", "2009-01-01", "2012-01-01"),
        3: ("2012-01-01", "2015-01-01", today()),
    }
    for number, (t0, t1, t2) in expected.items():
        assert got.loc[number, "Rise"] == iv(t0, t1)
        assert got.loc[number, "Fall"] == iv(t1, t2)
        assert got.loc[number, "Cycle"] == iv(t0, t2)


def test_a_cycle_without_a_maximum_rises_until_today():
    """A cycle whose maximum is not yet known is rising until today.

    ON FAILURE: the code is wrong.
    """
    got = Extrema(extrema_table(max3=pd.NaT)).cycle_intervals
    assert got.loc[3, "Rise"] == iv("2012-01-01", today())


# ---------------------------------------------------------------------------
# IndicatorExtrema: cut_spec_by_interval
# ---------------------------------------------------------------------------


def test_cut_by_cycle_assigns_each_epoch_to_its_cycle(extrema):
    """Each epoch is labelled with the cycle interval containing it.

    ON FAILURE: the code is wrong.
    """
    cut = extrema.cut_spec_by_interval(EPOCHS, kind="Cycle")
    assert list(cut) == [
        iv("2000-01-01", "2006-01-01"),
        iv("2000-01-01", "2006-01-01"),
        iv("2006-01-01", "2012-01-01"),
        iv("2012-01-01", today()),
    ]


def test_cut_by_rise_leaves_falling_epochs_unassigned(extrema):
    """Cutting by rising edges alone leaves falling-edge epochs NaN.

    Chosen input: 2004-06-01 lies on cycle 1's falling edge.

    ON FAILURE: the code is wrong.
    """
    cut = extrema.cut_spec_by_interval(EPOCHS, kind="Rise")
    assert cut.iloc[0] == iv("2000-01-01", "2003-01-01")
    assert pd.isna(cut.iloc[1])


def test_cut_by_edges_uses_both_rise_and_fall(extrema):
    """``"Edges"`` cuts by rising and falling edges together.

    ON FAILURE: the code is wrong.
    """
    cut = extrema.cut_spec_by_interval(EPOCHS, kind="Edges")
    assert cut.iloc[0] == iv("2000-01-01", "2003-01-01")
    assert cut.iloc[1] == iv("2003-01-01", "2006-01-01")


def test_cut_by_a_list_of_kinds_uses_only_those(extrema):
    """A list of kinds restricts the cut to those kinds.

    ON FAILURE: the code is wrong.
    """
    cut = extrema.cut_spec_by_interval(EPOCHS, kind=["Fall"])
    assert pd.isna(cut.iloc[0])
    assert cut.iloc[1] == iv("2003-01-01", "2006-01-01")


def test_cut_restricted_to_chosen_cycles_ignores_the_others(extrema):
    """``tk_cycles`` limits the cut to the named cycles.

    ON FAILURE: the code is wrong.
    """
    cut = extrema.cut_spec_by_interval(EPOCHS, kind="Cycle", tk_cycles=[2])
    assert pd.isna(cut.iloc[0])
    assert cut.iloc[2] == iv("2006-01-01", "2012-01-01")
    assert pd.isna(cut.iloc[3])


def test_cut_accepts_a_series_of_epochs_as_well_as_an_index(extrema):
    """A Series of epochs cuts to the same intervals as the bare index.

    ON FAILURE: the code is wrong.
    """
    from_index = extrema.cut_spec_by_interval(EPOCHS, kind="Cycle")
    from_series = extrema.cut_spec_by_interval(EPOCHS.to_series(), kind="Cycle")
    assert list(from_series) == list(from_index)


@pytest.mark.parametrize("kind", ["Peak", ["Rise", "Peak"], 5])
def test_cut_rejects_an_unknown_kind(extrema, kind):
    """An interval kind that does not exist is refused by name.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(ValueError, match="unavailable"):
        extrema.cut_spec_by_interval(EPOCHS, kind=kind)


# ---------------------------------------------------------------------------
# IndicatorExtrema: extrema bands
# ---------------------------------------------------------------------------


def test_extrema_bands_before_calculation_name_the_missing_call(extrema):
    """Reading the bands before computing them says which call is missing.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(AttributeError, match="calculate_extrema_bands"):
        extrema.extrema_bands


def test_default_band_is_a_year_either_side_of_each_extremum(extrema):
    """The default band spans 365 days either side of each extremum.

    Hand-computed: 2000 and 2008 are leap years, so 365 days from
    2000-01-01 is 2000-12-31 and 365 days before 2009-01-01 is 2008-01-02.

    ON FAILURE: the code is wrong.
    """
    bands = extrema.calculate_extrema_bands()
    assert bands.loc[1, "Min"] == iv("1999-01-01", "2000-12-31")
    assert bands.loc[2, "Max"] == iv("2008-01-02", "2010-01-01")
    assert extrema.extrema_bands is bands


def test_two_widths_set_the_left_and_right_half_widths(extrema):
    """A pair of widths sets the band's left and right half-widths.

    Hand-computed: 30 days before 2000-01-01 is 1999-12-02; 60 days after it
    is 2000-03-01 (31 January days, then 29 in leap February).

    ON FAILURE: the code is wrong.
    """
    bands = extrema.calculate_extrema_bands(dt=["30D", "60D"])
    assert bands.loc[1, "Min"] == iv("1999-12-02", "2000-03-01")


def test_more_than_two_widths_are_refused(extrema):
    """Three widths are refused.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(ValueError, match="1 or 2 dt"):
        extrema.calculate_extrema_bands(dt=["1D", "2D", "3D"])


BAND_EPOCHS = pd.DatetimeIndex(["2000-02-01", "2003-03-01", "2004-06-01"])


def test_cut_about_bands_labels_epochs_by_cycle_and_extremum(extrema):
    """Epochs in a band are labelled ``"<cycle>-<Min|Max>"``; others are NaN.

    Chosen input: 100-day bands. 2000-02-01 is 31 days after cycle 1's
    minimum, 2003-03-01 is 59 days after its maximum, and 2004-06-01 is more
    than a year from any extremum.

    ON FAILURE: the code is wrong.
    """
    extrema.calculate_extrema_bands(dt="100D")
    cut, mapped = extrema.cut_about_extrema_bands(BAND_EPOCHS)

    assert cut.iloc[0] == iv("1999-09-23", "2000-04-10")
    assert list(mapped.iloc[:2]) == ["1-Min", "1-Max"]
    assert pd.isna(mapped.iloc[2])


def test_cut_about_bands_honours_kind_and_cycle_selection(extrema):
    """``kind`` and ``tk_cycles`` drop the bands they exclude.

    ON FAILURE: the code is wrong.
    """
    extrema.calculate_extrema_bands(dt="100D")

    _, only_max = extrema.cut_about_extrema_bands(BAND_EPOCHS, kind="Max")
    assert pd.isna(only_max.iloc[0])
    assert only_max.iloc[1] == "1-Max"

    _, only_two = extrema.cut_about_extrema_bands(BAND_EPOCHS, tk_cycles=[2, 3])
    assert pd.isna(only_two).all()
