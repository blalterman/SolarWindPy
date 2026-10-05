"""Unit tests for the ICMECAT class.

Every test reads a real CSV through the real ``pandas.read_csv``: the
``serve_catalog`` fixture (``conftest.py``) writes a hand-built catalog under
``tmp_path`` and points ``icmecat.ICMECAT_URL`` at it. Expected values are read
off the table in ``conftest.py``.
"""

import os
import time

import numpy as np
import pandas as pd
import pytest

from solarwindpy.solar_activity.icme import icmecat
from solarwindpy.solar_activity.icme.icmecat import ICMECAT, ICMECATDownloadError

T = pd.Timestamp

ALL_IDS = ["U1", "U2", "U3", "W1", "W2", "S1"]
ULYSSES_IDS = ["U1", "U2", "U3"]
STRICT_IDS = ["U1", "U2", "W2", "S1"]  # rows with mo_end_time present

# interval_end per row, from the conftest table: mo_end_time, else
# mo_start_time + 24 h (U3), else icme_start_time + 24 h (W1).
INTERVAL_END = [
    T("2000-01-15"),
    T("2000-02-20"),
    T("2000-03-22"),
    T("2000-04-02"),
    T("2000-05-04"),
    T("2000-06-03"),
]


class TestCatalogFixture:
    """The hand-built catalog separates the behaviors the tests rely on."""

    def test_catalog_fixture_covers_every_interval_end_source(self, catalog):
        """The catalog has a row for each interval_end source and mixed spellings.

        Needs: mo_end_time present; mo_end_time missing with mo_start_time
        present; both missing; more than one spacecraft; and a spacecraft
        spelled differently from the caller's "Ulysses".

        ON FAILURE: the fixture no longer separates the three interval_end
        sources (or exact from case-insensitive spacecraft matching); fix the
        fixture.
        """
        has_end = catalog["mo_end_time"].notna()
        has_start = catalog["mo_start_time"].notna()
        assert has_end.any()
        assert (~has_end & has_start).any()
        assert (~has_end & ~has_start).any()
        assert catalog["sc_insitu"].nunique() > 1
        assert "Ulysses" not in set(catalog["sc_insitu"])
        assert "ulysses" in set(catalog["sc_insitu"].str.lower())


class TestICMECATInitialization:
    """ICMECAT() loads the catalog and optionally filters it."""

    def test_init_loads_every_catalog_row(self, serve_catalog):
        """ICMECAT() loads every row of the catalog at ICMECAT_URL, in order.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        cat = ICMECAT()
        assert cat.data["icmecat_id"].tolist() == ALL_IDS

    def test_init_with_spacecraft_filters(self, serve_catalog):
        """ICMECAT(spacecraft="Ulysses") keeps exactly the ULYSSES rows.

        The catalog spells it "ULYSSES"; the match is case-insensitive and
        the caller's spelling is kept for display.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        cat = ICMECAT(spacecraft="Ulysses")
        assert cat.spacecraft == "Ulysses"
        assert cat.data["icmecat_id"].tolist() == ULYSSES_IDS
        assert cat.intervals["icmecat_id"].tolist() == ULYSSES_IDS

    def test_init_without_spacecraft_keeps_all(self, serve_catalog):
        """ICMECAT() without a spacecraft keeps every spacecraft.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        cat = ICMECAT()
        assert cat.spacecraft is None
        assert set(cat.data["sc_insitu"]) == {"ULYSSES", "Wind", "STEREO-A"}


class TestICMECATDataProperty:
    """ICMECAT.data is the catalog as read."""

    def test_data_values_match_catalog_file(self, serve_catalog, catalog):
        """data holds the catalog's values, row for row.

        Dtypes are not compared: CSV parsing picks string and datetime units.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        cat = ICMECAT()
        pd.testing.assert_frame_equal(
            cat.data.reset_index(drop=True), catalog, check_dtype=False
        )

    def test_data_has_catalog_columns(self, serve_catalog, catalog):
        """data keeps every catalog column, including ones intervals drops.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        cat = ICMECAT()
        assert cat.data.columns.tolist() == catalog.columns.tolist()

    def test_data_datetime_dtypes(self, serve_catalog):
        """The three time columns parse from CSV text to datetime64.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        cat = ICMECAT()
        for col in ["icme_start_time", "mo_start_time", "mo_end_time"]:
            assert pd.api.types.is_datetime64_any_dtype(
                cat.data[col]
            ), f"{col} should be datetime64, got {cat.data[col].dtype}"


class TestICMECATIntervalsProperty:
    """ICMECAT.intervals carries a computed interval_end."""

    def test_intervals_has_documented_columns(self, serve_catalog):
        """intervals carries the event id, the three times, and interval_end.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        cat = ICMECAT()
        required = {
            "icmecat_id",
            "icme_start_time",
            "mo_start_time",
            "mo_end_time",
            "interval_end",
        }
        assert required <= set(cat.intervals.columns)
        assert cat.intervals["icmecat_id"].tolist() == ALL_IDS

    def test_interval_end_matches_hand_computed_fallbacks(self, serve_catalog):
        """interval_end is mo_end, else mo_start + 24 h, else icme_start + 24 h.

        Expected values are hand-computed in the conftest table.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        cat = ICMECAT()
        assert cat.intervals["interval_end"].tolist() == INTERVAL_END

    def test_interval_end_dtype_datetime(self, serve_catalog):
        """interval_end is datetime64.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        cat = ICMECAT()
        assert pd.api.types.is_datetime64_any_dtype(cat.intervals["interval_end"])


class TestICMECATIntervalFallbacks:
    """Each interval_end source in isolation, one event per catalog."""

    def test_fallback_uses_mo_end_when_available(self, serve_catalog, catalog):
        """When mo_end_time exists, interval_end equals mo_end_time.

        ON FAILURE: the code is wrong.
        """
        serve_catalog(catalog.iloc[[0]])
        cat = ICMECAT()
        assert cat.intervals.iloc[0]["interval_end"] == T("2000-01-15")

    def test_fallback_mo_start_plus_24h(self, serve_catalog):
        """mo_end_time missing: interval_end = mo_start_time + 24 h.

        ON FAILURE: the code is wrong.
        """
        data = pd.DataFrame(
            {
                "icmecat_id": ["TEST"],
                "sc_insitu": ["ULYSSES"],
                "icme_start_time": [T("2000-01-01")],
                "mo_start_time": [T("2000-01-02")],
                "mo_end_time": [pd.NaT],
            }
        )
        serve_catalog(data)
        cat = ICMECAT()
        assert cat.intervals.iloc[0]["interval_end"] == T("2000-01-03")

    def test_fallback_icme_start_plus_24h(self, serve_catalog):
        """mo_end_time and mo_start_time missing: interval_end = icme_start + 24 h.

        ON FAILURE: the code is wrong.
        """
        data = pd.DataFrame(
            {
                "icmecat_id": ["TEST"],
                "sc_insitu": ["ULYSSES"],
                "icme_start_time": [T("2000-01-01")],
                "mo_start_time": [pd.NaT],
                "mo_end_time": [pd.NaT],
            }
        )
        serve_catalog(data)
        cat = ICMECAT()
        assert cat.intervals.iloc[0]["interval_end"] == T("2000-01-02")


class TestICMECATStrictIntervals:
    """ICMECAT.strict_intervals keeps only events with a catalog mo_end_time."""

    def test_strict_intervals_excludes_nat(self, serve_catalog):
        """strict_intervals is exactly the rows whose mo_end_time is present.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        cat = ICMECAT()
        assert cat.strict_intervals["icmecat_id"].tolist() == STRICT_IDS

    def test_strict_intervals_rows_equal_their_intervals_rows(self, serve_catalog):
        """Each strict row is the same row of intervals, unchanged.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        cat = ICMECAT()
        strict = cat.strict_intervals
        pd.testing.assert_frame_equal(strict, cat.intervals.loc[strict.index])

    def test_strict_intervals_returns_copy(self, serve_catalog):
        """Writing to strict_intervals leaves intervals unchanged.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        cat = ICMECAT()
        strict = cat.strict_intervals
        assert strict.iloc[0]["icmecat_id"] == "U1"
        strict.iloc[0, strict.columns.get_loc("icmecat_id")] = "MODIFIED"
        assert cat.intervals.iloc[0]["icmecat_id"] == "U1"
        assert cat.strict_intervals.iloc[0]["icmecat_id"] == "U1"


class TestICMECATFilter:
    """ICMECAT.filter() returns a new, filtered catalog."""

    def test_filter_returns_new_instance(self, serve_catalog):
        """filter() returns a different ICMECAT and leaves the original whole.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        cat = ICMECAT()
        filtered = cat.filter("Ulysses")
        assert isinstance(filtered, ICMECAT)
        assert filtered is not cat
        assert cat.data["icmecat_id"].tolist() == ALL_IDS

    def test_filter_sets_spacecraft(self, serve_catalog):
        """filter() sets spacecraft on the new instance only.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        cat = ICMECAT()
        filtered = cat.filter("Ulysses")
        assert filtered.spacecraft == "Ulysses"
        assert cat.spacecraft is None

    def test_filter_only_includes_spacecraft(self, serve_catalog):
        """filter("ulysses") keeps exactly the ULYSSES rows, in data and intervals.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        filtered = ICMECAT().filter("ulysses")
        assert filtered.data["icmecat_id"].tolist() == ULYSSES_IDS
        assert filtered.intervals["interval_end"].tolist() == INTERVAL_END[:3]

    def test_filter_unknown_spacecraft_empty(self, serve_catalog):
        """filter() with a spacecraft absent from the catalog returns no events.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        filtered = ICMECAT().filter("NONEXISTENT")
        assert len(filtered) == 0
        assert len(filtered.intervals) == 0


class TestICMECATContains:
    """ICMECAT.contains() flags times inside strict intervals."""

    def test_contains_returns_series(self, serve_catalog):
        """contains() returns a bool Series.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        result = ICMECAT().contains(pd.Series([T("2000-01-12")]))
        assert isinstance(result, pd.Series)
        assert result.dtype == bool
        assert result.tolist() == [True]

    def test_contains_preserves_index(self, serve_catalog):
        """contains() returns the caller's index.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        times = pd.Series([T("2000-01-12")], index=["custom_index"])
        result = ICMECAT().contains(times)
        assert result.index.tolist() == ["custom_index"]

    def test_contains_true_inside_interval(self, serve_catalog):
        """A time inside each strict interval is flagged, not just the first.

        Strict intervals (icme_start to mo_end): U1 01-10..01-15,
        U2 02-15..02-20, W2 05-01..05-04, S1 06-01..06-03.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        times = pd.Series(
            [T("2000-01-12"), T("2000-02-17"), T("2000-05-03"), T("2000-06-02")]
        )
        assert ICMECAT().contains(times).tolist() == [True, True, True, True]

    def test_contains_false_outside_interval(self, serve_catalog):
        """Times before, between, and after every interval are not flagged.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        times = pd.Series([T("2000-01-05"), T("2000-01-16"), T("2000-07-01")])
        assert ICMECAT().contains(times).tolist() == [False, False, False]

    def test_contains_ignores_fallback_intervals(self, serve_catalog):
        """Times inside only a fallback interval (U3, W1) are not flagged.

        U3 spans 03-20..03-22 and W1 spans 04-01..04-02 only via the
        24 h fallbacks; contains() uses strict intervals.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        times = pd.Series([T("2000-03-21"), T("2000-04-01 12:00")])
        assert ICMECAT().contains(times).tolist() == [False, False]

    def test_contains_boundary_start_inclusive(self, serve_catalog):
        """contains() includes the interval's icme_start_time.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        assert ICMECAT().contains(pd.Series([T("2000-01-10")])).tolist() == [True]

    def test_contains_boundary_end_inclusive(self, serve_catalog):
        """contains() includes the interval's mo_end_time.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        assert ICMECAT().contains(pd.Series([T("2000-01-15")])).tolist() == [True]

    def test_contains_accepts_datetimeindex(self, serve_catalog):
        """contains() accepts a DatetimeIndex and flags it element by element.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        times = pd.DatetimeIndex(["2000-01-12", "2000-01-05"])
        result = ICMECAT().contains(times)
        assert isinstance(result, pd.Series)
        assert result.tolist() == [True, False]

    def test_contains_empty_input(self, serve_catalog):
        """contains() on no times returns an empty bool Series.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        result = ICMECAT().contains(pd.Series([], dtype="datetime64[ns]"))
        assert len(result) == 0
        assert result.dtype == bool


class TestICMECATSummary:
    """ICMECAT.summary() reports counts, coverage and durations.

    Durations (interval_end - icme_start_time) from the conftest table, hours:
    U1 120, U2 120, U3 48, W1 24, W2 72, S1 48.
    """

    def test_summary_returns_dataframe(self, serve_catalog):
        """summary() returns a one-row DataFrame.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        result = ICMECAT().summary()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1

    def test_summary_has_event_count(self, serve_catalog):
        """n_events is the number of catalog rows, 6.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        assert ICMECAT().summary()["n_events"].iloc[0] == 6

    def test_summary_has_strict_count(self, serve_catalog):
        """n_strict is the number of rows with mo_end_time present, 4.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        assert ICMECAT().summary()["n_strict"].iloc[0] == 4

    def test_summary_has_duration_stats(self, serve_catalog):
        """Duration statistics match the hand-computed hours.

        Sorted: 24, 48, 48, 72, 120, 120. Median (48 + 72) / 2 = 60;
        mean 432 / 6 = 72; min 24; max 120.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        row = ICMECAT().summary().iloc[0]
        # Whole hours from whole-hour timestamps: exact up to float rounding.
        assert row["duration_median_hours"] == pytest.approx(60.0, rel=1e-12, abs=0)
        assert row["duration_mean_hours"] == pytest.approx(72.0, rel=1e-12, abs=0)
        assert row["duration_min_hours"] == pytest.approx(24.0, rel=1e-12, abs=0)
        assert row["duration_max_hours"] == pytest.approx(120.0, rel=1e-12, abs=0)

    def test_summary_date_range(self, serve_catalog):
        """date_range runs from the first icme_start to the last interval_end.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        row = ICMECAT().summary().iloc[0]
        assert row["date_range_start"] == T("2000-01-10")
        assert row["date_range_end"] == T("2000-06-03")

    def test_summary_includes_spacecraft_when_filtered(self, serve_catalog):
        """A filtered summary names the spacecraft and counts only its events.

        ULYSSES durations 120, 120, 48 hours: mean 96.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        row = ICMECAT(spacecraft="Ulysses").summary().iloc[0]
        assert row["spacecraft"] == "Ulysses"
        assert row["n_events"] == 3
        # Whole hours: exact up to float rounding.
        assert row["duration_mean_hours"] == pytest.approx(96.0, rel=1e-12, abs=0)


class TestICMECATDunderMethods:
    """len() and repr()."""

    def test_len_returns_event_count(self, serve_catalog):
        """len(ICMECAT) is the number of events, 6.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        assert len(ICMECAT()) == 6

    def test_repr_includes_class_name(self, serve_catalog):
        """repr names the class.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        assert repr(ICMECAT()).startswith("ICMECAT(")

    def test_repr_includes_event_count(self, serve_catalog):
        """repr reports the event count of this instance.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        assert "n_events=6" in repr(ICMECAT())
        assert "n_events=3" in repr(ICMECAT(spacecraft="Ulysses"))

    def test_repr_includes_spacecraft_when_filtered(self, serve_catalog):
        """repr names the spacecraft filter in the caller's spelling.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        assert "'Ulysses'" in repr(ICMECAT(spacecraft="Ulysses"))


class TestICMECATEdgeCases:
    """Empty and degenerate catalogs."""

    def test_empty_catalog_after_filter(self, serve_catalog):
        """Filtering to an absent spacecraft gives an empty, usable catalog.

        ON FAILURE: the code is wrong.
        """
        serve_catalog()
        cat = ICMECAT(spacecraft="NONEXISTENT")
        assert len(cat) == 0
        assert len(cat.intervals) == 0
        assert len(cat.strict_intervals) == 0
        times = pd.Series([T("2000-01-12")])
        assert cat.contains(times).tolist() == [False]
        row = cat.summary().iloc[0]
        assert row["n_events"] == 0
        assert np.isnan(row["duration_mean_hours"])

    def test_all_mo_end_time_missing(self, serve_catalog):
        """With every mo_end_time missing, all intervals use fallbacks; none is strict.

        ON FAILURE: the code is wrong.
        """
        data = pd.DataFrame(
            {
                "icmecat_id": ["A", "B"],
                "sc_insitu": ["ULYSSES", "ULYSSES"],
                "icme_start_time": [T("2000-01-01"), T("2000-02-01")],
                "mo_start_time": [T("2000-01-02"), pd.NaT],
                "mo_end_time": [pd.NaT, pd.NaT],
            }
        )
        serve_catalog(data)
        cat = ICMECAT()
        # A: mo_start + 24 h; B: icme_start + 24 h.
        assert cat.intervals["interval_end"].tolist() == [
            T("2000-01-03"),
            T("2000-02-02"),
        ]
        assert len(cat.strict_intervals) == 0

    def test_contains_with_no_strict_intervals(self, serve_catalog):
        """contains() flags nothing when no event has a mo_end_time.

        2000-01-02 12:00 lies inside A's fallback interval (01-01..01-03).

        ON FAILURE: the code is wrong.
        """
        data = pd.DataFrame(
            {
                "icmecat_id": ["A"],
                "sc_insitu": ["ULYSSES"],
                "icme_start_time": [T("2000-01-01")],
                "mo_start_time": [T("2000-01-02")],
                "mo_end_time": [pd.NaT],
            }
        )
        serve_catalog(data)
        result = ICMECAT().contains(pd.Series([T("2000-01-02 12:00")]))
        assert result.tolist() == [False]


CACHE_NEEDS_PARQUET_ENGINE = pytest.mark.xfail(
    strict=True,
    raises=ImportError,
    reason=(
        "ICMECAT(cache_dir=...) writes icmecat.parquet "
        "(solarwindpy/solar_activity/icme/icmecat.py, _download/_read_cache) but "
        "pyproject.toml declares no parquet engine; expected message 'Unable to "
        "find a usable engine; tried using: 'pyarrow', 'fastparquet''; remove this "
        "marker when pyarrow is a declared dependency or the cache stops using parquet"
    ),
)


class TestICMECATDownloadAndCache:
    """Download failure and the on-disk cache."""

    def test_download_failure_without_cache_raises(self):
        """With no catalog at ICMECAT_URL and no cache, ICMECATDownloadError is raised.

        The autouse ``_no_network`` fixture points ICMECAT_URL at a missing file.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(ICMECATDownloadError, match="Failed to download ICMECAT"):
            ICMECAT()

    @CACHE_NEEDS_PARQUET_ENGINE
    def test_fresh_cache_is_used_without_download(
        self, serve_catalog, tmp_path, monkeypatch
    ):
        """A cache written by one load serves the next even when the URL is gone.

        ON FAILURE: (unexpected pass) a parquet engine is now a declared
        dependency or the cache no longer uses parquet; drop the xfail marker.
        """
        cache_dir = tmp_path / "cache"
        serve_catalog()
        ICMECAT(cache_dir=cache_dir)
        monkeypatch.setattr(icmecat, "ICMECAT_URL", str(tmp_path / "gone.csv"))
        cat = ICMECAT(cache_dir=cache_dir)
        assert cat.data["icmecat_id"].tolist() == ALL_IDS

    @CACHE_NEEDS_PARQUET_ENGINE
    def test_stale_cache_served_with_warning_when_download_fails(
        self, serve_catalog, tmp_path, monkeypatch
    ):
        """A cache older than 30 days is served, with a warning, if download fails.

        ON FAILURE: (unexpected pass) a parquet engine is now a declared
        dependency or the cache no longer uses parquet; drop the xfail marker.
        """
        cache_dir = tmp_path / "cache"
        serve_catalog()
        ICMECAT(cache_dir=cache_dir)
        forty_days_ago = time.time() - 40 * 86400
        os.utime(cache_dir / "icmecat.parquet", (forty_days_ago, forty_days_ago))
        monkeypatch.setattr(icmecat, "ICMECAT_URL", str(tmp_path / "gone.csv"))
        with pytest.warns(UserWarning, match="serving cached data that is 40 days old"):
            cat = ICMECAT(cache_dir=cache_dir)
        assert cat.data["icmecat_id"].tolist() == ALL_IDS
