"""Unit tests for ICMECAT class.

Tests cover:
- Initialization and data loading
- Spacecraft filtering
- Interval preparation with fallbacks
- Containment checking
- Summary statistics
- Property types, shapes, and dtypes
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestICMECATInitialization:
    """Test ICMECAT class initialization."""

    def test_init_downloads_data(self, mock_icmecat_csv_data):
        """ICMECAT() downloads data on initialization."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            assert cat.data is not None
            assert len(cat) > 0

    def test_init_with_spacecraft_filters(self, mock_icmecat_csv_data):
        """ICMECAT(spacecraft='X') filters to that spacecraft."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT(spacecraft="Ulysses")

            assert cat.spacecraft == "Ulysses"
            assert all(cat.data["sc_insitu"] == "Ulysses")

    def test_init_without_spacecraft_keeps_all(self, mock_icmecat_csv_data):
        """ICMECAT() without spacecraft keeps all events."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            assert cat.spacecraft is None
            assert len(cat.data["sc_insitu"].unique()) > 1


class TestICMECATDataProperty:
    """Test ICMECAT.data property."""

    def test_data_is_dataframe(self, mock_icmecat_csv_data):
        """data property returns a DataFrame."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            assert isinstance(cat.data, pd.DataFrame)

    def test_data_has_required_columns(self, mock_icmecat_csv_data):
        """data has all required columns."""
        required = ["icmecat_id", "sc_insitu", "icme_start_time", "mo_end_time"]

        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            for col in required:
                assert col in cat.data.columns, f"Missing column: {col}"

    def test_data_datetime_dtypes(self, mock_icmecat_csv_data):
        """Datetime columns have datetime64 dtype."""
        datetime_cols = ["icme_start_time", "mo_start_time", "mo_end_time"]

        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            for col in datetime_cols:
                assert pd.api.types.is_datetime64_any_dtype(cat.data[col]), \
                    f"{col} should be datetime64, got {cat.data[col].dtype}"

    def test_data_shape_nonzero(self, mock_icmecat_csv_data):
        """data has non-zero rows."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            assert cat.data.shape[0] > 0
            assert cat.data.shape[1] >= 5


class TestICMECATIntervalsProperty:
    """Test ICMECAT.intervals property."""

    def test_intervals_is_dataframe(self, mock_icmecat_csv_data):
        """intervals property returns a DataFrame."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            assert isinstance(cat.intervals, pd.DataFrame)

    def test_intervals_has_interval_end(self, mock_icmecat_csv_data):
        """intervals has computed interval_end column."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            assert "interval_end" in cat.intervals.columns

    def test_interval_end_no_nulls(self, mock_icmecat_csv_data):
        """interval_end has no NaN values (fallbacks applied)."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            assert cat.intervals["interval_end"].notna().all()

    def test_interval_end_dtype_datetime(self, mock_icmecat_csv_data):
        """interval_end is datetime64."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            assert pd.api.types.is_datetime64_any_dtype(
                cat.intervals["interval_end"]
            )

    def test_interval_end_after_start(self, mock_icmecat_csv_data):
        """interval_end >= icme_start_time for all events."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            assert all(
                cat.intervals["interval_end"] >= cat.intervals["icme_start_time"]
            )


class TestICMECATIntervalFallbacks:
    """Test interval_end fallback logic."""

    def test_fallback_uses_mo_end_when_available(self, simple_icme_intervals):
        """When mo_end_time exists, interval_end equals mo_end_time."""
        with patch("pandas.read_csv", return_value=simple_icme_intervals):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            # First event has mo_end_time
            assert cat.intervals.iloc[0]["interval_end"] == pd.Timestamp("2000-01-15")

    def test_fallback_mo_start_plus_24h(self):
        """Fallback: mo_end_time missing -> mo_start_time + 24h."""
        data = pd.DataFrame({
            "icmecat_id": ["TEST"],
            "sc_insitu": ["Ulysses"],
            "icme_start_time": [pd.Timestamp("2000-01-01")],
            "mo_start_time": [pd.Timestamp("2000-01-02")],
            "mo_end_time": [pd.NaT],
        })

        with patch("pandas.read_csv", return_value=data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            expected = pd.Timestamp("2000-01-03")  # mo_start + 24h
            assert cat.intervals.iloc[0]["interval_end"] == expected

    def test_fallback_icme_start_plus_24h(self):
        """Fallback: both missing -> icme_start_time + 24h."""
        data = pd.DataFrame({
            "icmecat_id": ["TEST"],
            "sc_insitu": ["Ulysses"],
            "icme_start_time": [pd.Timestamp("2000-01-01")],
            "mo_start_time": [pd.NaT],
            "mo_end_time": [pd.NaT],
        })

        with patch("pandas.read_csv", return_value=data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            expected = pd.Timestamp("2000-01-02")  # icme_start + 24h
            assert cat.intervals.iloc[0]["interval_end"] == expected


class TestICMECATStrictIntervals:
    """Test ICMECAT.strict_intervals property."""

    def test_strict_intervals_excludes_nat(self, mock_icmecat_csv_data):
        """strict_intervals only includes events with valid mo_end_time."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            # strict_intervals should have fewer rows if there are NaT values
            assert cat.strict_intervals["mo_end_time"].notna().all()

    def test_strict_intervals_is_subset(self, mock_icmecat_csv_data):
        """strict_intervals is subset of intervals."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            assert len(cat.strict_intervals) <= len(cat.intervals)

    def test_strict_intervals_returns_copy(self, mock_icmecat_csv_data):
        """strict_intervals returns a copy, not a view."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            strict = cat.strict_intervals
            if len(strict) > 0:
                original_id = cat.intervals.iloc[0]["icmecat_id"]
                strict.iloc[0, strict.columns.get_loc("icmecat_id")] = "MODIFIED"
                assert cat.intervals.iloc[0]["icmecat_id"] == original_id


class TestICMECATFilter:
    """Test ICMECAT.filter() method."""

    def test_filter_returns_new_instance(self, mock_icmecat_csv_data):
        """filter() returns a new ICMECAT instance."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()
            filtered = cat.filter("Ulysses")

            assert isinstance(filtered, ICMECAT)
            assert filtered is not cat

    def test_filter_sets_spacecraft(self, mock_icmecat_csv_data):
        """filter() sets spacecraft property on new instance."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()
            filtered = cat.filter("Ulysses")

            assert filtered.spacecraft == "Ulysses"
            assert cat.spacecraft is None  # Original unchanged

    def test_filter_only_includes_spacecraft(self, mock_icmecat_csv_data):
        """filter() only includes events from specified spacecraft."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()
            filtered = cat.filter("Ulysses")

            assert all(filtered.data["sc_insitu"] == "Ulysses")

    def test_filter_unknown_spacecraft_empty(self, mock_icmecat_csv_data):
        """filter() with unknown spacecraft returns empty catalog."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()
            filtered = cat.filter("NONEXISTENT")

            assert len(filtered) == 0


class TestICMECATContains:
    """Test ICMECAT.contains() method."""

    def test_contains_returns_series(self, simple_icme_intervals):
        """contains() returns a boolean Series."""
        with patch("pandas.read_csv", return_value=simple_icme_intervals):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            times = pd.Series([pd.Timestamp("2000-01-12")])
            result = cat.contains(times)

            assert isinstance(result, pd.Series)
            assert result.dtype == bool

    def test_contains_preserves_index(self, simple_icme_intervals):
        """contains() preserves input index."""
        with patch("pandas.read_csv", return_value=simple_icme_intervals):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            times = pd.Series(
                [pd.Timestamp("2000-01-12")],
                index=["custom_index"]
            )
            result = cat.contains(times)

            assert result.index.tolist() == ["custom_index"]

    def test_contains_true_inside_interval(self, simple_icme_intervals):
        """contains() returns True for times inside an interval."""
        with patch("pandas.read_csv", return_value=simple_icme_intervals):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            # 2000-01-12 is inside first interval (01-10 to 01-15)
            times = pd.Series([pd.Timestamp("2000-01-12")])
            result = cat.contains(times)

            assert result.iloc[0] == True

    def test_contains_false_outside_interval(self, simple_icme_intervals):
        """contains() returns False for times outside all intervals."""
        with patch("pandas.read_csv", return_value=simple_icme_intervals):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            # 2000-01-05 is before first interval
            times = pd.Series([pd.Timestamp("2000-01-05")])
            result = cat.contains(times)

            assert result.iloc[0] == False

    def test_contains_boundary_start_inclusive(self, simple_icme_intervals):
        """contains() includes interval start time."""
        with patch("pandas.read_csv", return_value=simple_icme_intervals):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            # Exactly at start of first interval
            times = pd.Series([pd.Timestamp("2000-01-10")])
            result = cat.contains(times)

            assert result.iloc[0] == True

    def test_contains_boundary_end_inclusive(self, simple_icme_intervals):
        """contains() includes interval end time."""
        with patch("pandas.read_csv", return_value=simple_icme_intervals):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            # Exactly at end of first interval
            times = pd.Series([pd.Timestamp("2000-01-15")])
            result = cat.contains(times)

            assert result.iloc[0] == True

    def test_contains_accepts_datetimeindex(self, simple_icme_intervals):
        """contains() accepts DatetimeIndex input."""
        with patch("pandas.read_csv", return_value=simple_icme_intervals):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            times = pd.DatetimeIndex(["2000-01-12", "2000-01-05"])
            result = cat.contains(times)

            assert isinstance(result, pd.Series)
            assert len(result) == 2

    def test_contains_empty_input(self, simple_icme_intervals):
        """contains() handles empty input gracefully."""
        with patch("pandas.read_csv", return_value=simple_icme_intervals):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            times = pd.Series([], dtype="datetime64[ns]")
            result = cat.contains(times)

            assert len(result) == 0
            assert result.dtype == bool


class TestICMECATSummary:
    """Test ICMECAT.summary() method."""

    def test_summary_returns_dataframe(self, mock_icmecat_csv_data):
        """summary() returns a DataFrame."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            result = cat.summary()
            assert isinstance(result, pd.DataFrame)

    def test_summary_has_event_count(self, mock_icmecat_csv_data):
        """summary() includes event count."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            result = cat.summary()
            assert "n_events" in result.columns
            assert result["n_events"].iloc[0] == len(cat)

    def test_summary_has_strict_count(self, mock_icmecat_csv_data):
        """summary() includes strict event count."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            result = cat.summary()
            assert "n_strict" in result.columns
            assert result["n_strict"].iloc[0] == len(cat.strict_intervals)

    def test_summary_has_duration_stats(self, mock_icmecat_csv_data):
        """summary() includes duration statistics."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            result = cat.summary()
            duration_cols = ["duration_median_hours", "duration_mean_hours"]
            for col in duration_cols:
                assert col in result.columns

    def test_summary_includes_spacecraft_when_filtered(self, mock_icmecat_csv_data):
        """summary() includes spacecraft when filtered."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT(spacecraft="Ulysses")

            result = cat.summary()
            assert "spacecraft" in result.columns
            assert result["spacecraft"].iloc[0] == "Ulysses"


class TestICMECATDunderMethods:
    """Test ICMECAT special methods (__len__, __repr__)."""

    def test_len_returns_event_count(self, mock_icmecat_csv_data):
        """len(ICMECAT) returns number of events."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            assert len(cat) == len(cat.data)

    def test_repr_includes_class_name(self, mock_icmecat_csv_data):
        """repr includes class name."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            assert "ICMECAT" in repr(cat)

    def test_repr_includes_event_count(self, mock_icmecat_csv_data):
        """repr includes event count."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            assert str(len(cat)) in repr(cat)

    def test_repr_includes_spacecraft_when_filtered(self, mock_icmecat_csv_data):
        """repr includes spacecraft when filtered."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT(spacecraft="Ulysses")

            assert "Ulysses" in repr(cat)


class TestICMECATEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_catalog_after_filter(self, mock_icmecat_csv_data):
        """Handles filtering to zero events gracefully."""
        with patch("pandas.read_csv", return_value=mock_icmecat_csv_data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT(spacecraft="NONEXISTENT")

            assert len(cat) == 0
            assert len(cat.intervals) == 0
            assert len(cat.strict_intervals) == 0

    def test_all_mo_end_time_missing(self):
        """Handles case where all mo_end_time are NaT."""
        data = pd.DataFrame({
            "icmecat_id": ["A", "B"],
            "sc_insitu": ["Ulysses", "Ulysses"],
            "icme_start_time": [pd.Timestamp("2000-01-01"), pd.Timestamp("2000-02-01")],
            "mo_start_time": [pd.Timestamp("2000-01-02"), pd.NaT],
            "mo_end_time": [pd.NaT, pd.NaT],
        })

        with patch("pandas.read_csv", return_value=data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            assert cat.intervals["interval_end"].notna().all()
            assert len(cat.strict_intervals) == 0

    def test_contains_with_no_strict_intervals(self):
        """contains() returns False when no strict intervals exist."""
        data = pd.DataFrame({
            "icmecat_id": ["A"],
            "sc_insitu": ["Ulysses"],
            "icme_start_time": [pd.Timestamp("2000-01-01")],
            "mo_start_time": [pd.Timestamp("2000-01-02")],
            "mo_end_time": [pd.NaT],
        })

        with patch("pandas.read_csv", return_value=data):
            from solarwindpy.solar_activity.icme import ICMECAT
            cat = ICMECAT()

            times = pd.Series([pd.Timestamp("2000-01-05")])
            result = cat.contains(times)

            assert result.iloc[0] == False
