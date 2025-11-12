#!/usr/bin/env python
"""Test SSNExtrema class.

This module tests the SSNExtrema class from solar_activity.sunspot_number.sidc:
- CSV parsing and data loading
- Error handling for invalid arguments
- Data format validation
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from solarwindpy.solar_activity.sunspot_number.sidc import SSNExtrema


class TestSSNExtrema:
    """Test the SSNExtrema class for solar cycle extrema data."""

    @pytest.fixture
    def sample_ssn_extrema_csv(self):
        """Sample SSN extrema CSV content for testing."""
        # Simulate the format of ssn_extrema.csv with header rows and data
        csv_content = (
            """# Solar Cycle Extrema Data
# Source: SIDC - Royal Observatory of Belgium
# Data format: Cycle Number, Minimum Date, Maximum Date
# 
# Additional header lines (total 45 lines to skip)
"""
            + "\n" * 40
            + """Number,Min,Max
20,1964-10-01,1968-11-01
21,1976-03-01,1979-12-01
22,1986-09-01,1989-07-01
23,1996-05-01,2000-03-01
24,2008-12-01,2014-04-01
25,2019-12-01,2025-07-01"""
        )
        return csv_content

    def test_initialization_no_args(self):
        """Test SSNExtrema initialization with no arguments."""
        # This should work without raising errors
        with (
            patch("pandas.read_csv") as mock_read_csv,
            patch("pathlib.Path.exists", return_value=True),
        ):

            # Mock the CSV data
            mock_data = pd.DataFrame(
                {
                    "Min": ["1964-10-01", "1976-03-01", "1986-09-01"],
                    "Max": ["1968-11-01", "1979-12-01", "1989-07-01"],
                },
                index=[20, 21, 22],
            )
            mock_read_csv.return_value = mock_data

            extrema = SSNExtrema()

            # Verify that the load_or_set_data method was called implicitly
            assert hasattr(extrema, "_data")

    def test_load_or_set_data_empty_args(self, sample_ssn_extrema_csv):
        """Test load_or_set_data with empty args and kwargs."""
        extrema = SSNExtrema.__new__(SSNExtrema)

        # Mock file reading
        with (
            patch("pandas.read_csv") as mock_read_csv,
            patch("pathlib.Path.exists", return_value=True),
        ):

            # Create mock DataFrame that simulates the CSV structure
            raw_data = pd.DataFrame(
                {
                    "Min": ["1964-10-01", "1976-03-01", "1986-09-01"],
                    "Max": ["1968-11-01", "1979-12-01", "1989-07-01"],
                },
                index=[20, 21, 22],
            )

            # Mock the stack/unstack operations
            stacked = pd.Series(
                [
                    "1964-10-01",
                    "1968-11-01",
                    "1976-03-01",
                    "1979-12-01",
                    "1986-09-01",
                    "1989-07-01",
                ]
            )
            unstacked = pd.DataFrame(
                {
                    "Min": [
                        pd.Timestamp("1964-10-01"),
                        pd.Timestamp("1976-03-01"),
                        pd.Timestamp("1986-09-01"),
                    ],
                    "Max": [
                        pd.Timestamp("1968-11-01"),
                        pd.Timestamp("1979-12-01"),
                        pd.Timestamp("1989-07-01"),
                    ],
                },
                index=[20, 21, 22],
            )
            unstacked.columns.names = ["kind"]

            mock_read_csv.return_value = raw_data

            with (
                patch.object(pd.DataFrame, "stack", return_value=stacked),
                patch("pandas.to_datetime", return_value=stacked),
                patch.object(pd.Series, "unstack", return_value=unstacked),
            ):

                extrema.load_or_set_data()

                # Verify CSV was read with correct parameters
                mock_read_csv.assert_called_once()
                args, kwargs = mock_read_csv.call_args
                assert kwargs["header"] == 0
                assert kwargs["skiprows"] == 45
                assert kwargs["index_col"] == 0

                # Verify data was set
                assert hasattr(extrema, "_data")
                assert extrema._data.columns.names == ["kind"]

    def test_load_or_set_data_with_args_raises_error(self):
        """Test that passing args/kwargs raises ValueError."""
        extrema = SSNExtrema.__new__(SSNExtrema)

        # Should raise ValueError when passing arguments
        with pytest.raises(
            ValueError, match="SSNExtrema expects empty args and kwargs"
        ):
            extrema.load_or_set_data("some_arg")

    def test_load_or_set_data_with_kwargs_raises_error(self):
        """Test that passing kwargs raises ValueError."""
        extrema = SSNExtrema.__new__(SSNExtrema)

        # Should raise ValueError when passing keyword arguments
        with pytest.raises(
            ValueError, match="SSNExtrema expects empty args and kwargs"
        ):
            extrema.load_or_set_data(some_kwarg="value")

    def test_load_or_set_data_with_both_args_and_kwargs_raises_error(self):
        """Test that passing both args and kwargs raises ValueError."""
        extrema = SSNExtrema.__new__(SSNExtrema)

        # Should raise ValueError when passing both
        with pytest.raises(
            ValueError, match="SSNExtrema expects empty args and kwargs"
        ):
            extrema.load_or_set_data("arg", kwarg="value")

    def test_inheritance_from_indicator_extrema(self):
        """Test that SSNExtrema inherits from IndicatorExtrema."""
        from solarwindpy.solar_activity.base import IndicatorExtrema

        with (
            patch("pandas.read_csv") as mock_read_csv,
            patch("pathlib.Path.exists", return_value=True),
        ):

            # Mock the CSV data
            mock_data = pd.DataFrame(
                {"Min": ["1964-10-01"], "Max": ["1968-11-01"]}, index=[20]
            )
            mock_read_csv.return_value = mock_data

            extrema = SSNExtrema()
            assert isinstance(extrema, IndicatorExtrema)

    def test_csv_file_path_resolution(self):
        """Test that the CSV file path is resolved correctly."""
        extrema = SSNExtrema.__new__(SSNExtrema)

        with (
            patch("pandas.read_csv") as mock_read_csv,
            patch("pathlib.Path.exists", return_value=True),
        ):

            mock_data = pd.DataFrame(
                {"Min": ["1964-10-01"], "Max": ["1968-11-01"]}, index=[20]
            )
            mock_read_csv.return_value = mock_data

            extrema.load_or_set_data()

            # Check that read_csv was called with the expected path
            args, kwargs = mock_read_csv.call_args
            called_path = args[0]

            # The path should end with ssn_extrema.csv
            assert str(called_path).endswith("ssn_extrema.csv")
            assert "sunspot_number" in str(called_path)

    def test_data_format_after_loading(self):
        """Test that data has correct format after loading."""
        with (
            patch("pandas.read_csv") as mock_read_csv,
            patch("pathlib.Path.exists", return_value=True),
        ):

            # Mock the CSV reading and processing
            raw_data = pd.DataFrame(
                {
                    "Min": ["2008-12-01", "2019-12-01"],
                    "Max": ["2014-04-01", "2025-07-01"],
                },
                index=[24, 25],
            )

            processed_data = pd.DataFrame(
                {
                    "Min": [pd.Timestamp("2008-12-01"), pd.Timestamp("2019-12-01")],
                    "Max": [pd.Timestamp("2014-04-01"), pd.Timestamp("2025-07-01")],
                },
                index=[24, 25],
            )
            processed_data.columns.names = ["kind"]

            mock_read_csv.return_value = raw_data

            # Mock the datetime conversion process
            with patch(
                "solarwindpy.solar_activity.sunspot_number.sidc.pd.to_datetime"
            ) as mock_to_datetime:
                # Mock stack operation
                stacked_data = pd.Series(
                    ["2008-12-01", "2014-04-01", "2019-12-01", "2025-07-01"]
                )

                # Mock to_datetime to return datetime series
                datetime_series = pd.Series(
                    [
                        pd.Timestamp("2008-12-01"),
                        pd.Timestamp("2014-04-01"),
                        pd.Timestamp("2019-12-01"),
                        pd.Timestamp("2025-07-01"),
                    ]
                )
                mock_to_datetime.return_value = datetime_series

                with (
                    patch.object(pd.DataFrame, "stack", return_value=stacked_data),
                    patch.object(pd.Series, "unstack", return_value=processed_data),
                    patch.object(
                        SSNExtrema, "calculate_intervals"
                    ),  # Skip interval calculation that uses "today"
                ):

                    extrema = SSNExtrema()

                    # Verify data structure
                    assert hasattr(extrema, "_data")
                    assert extrema._data.columns.names == ["kind"]
                    assert "Min" in extrema._data.columns
                    assert "Max" in extrema._data.columns


class TestSSNExtremaEdgeCases:
    """Test edge cases and error conditions for SSNExtrema."""

    def test_file_not_found_handling(self):
        """Test behavior when CSV file doesn't exist."""
        with (
            patch("pathlib.Path.exists", return_value=False),
            patch("pandas.read_csv") as mock_read_csv,
        ):

            # read_csv should still be called even if file check fails
            # (pandas will handle the FileNotFoundError)
            mock_read_csv.side_effect = FileNotFoundError("File not found")

            with pytest.raises(FileNotFoundError):
                SSNExtrema()

    def test_malformed_csv_handling(self):
        """Test behavior with malformed CSV data."""
        with (
            patch("pandas.read_csv") as mock_read_csv,
            patch("pathlib.Path.exists", return_value=True),
        ):

            # Simulate malformed CSV that causes parsing error
            mock_read_csv.side_effect = pd.errors.ParserError("Malformed CSV")

            with pytest.raises(pd.errors.ParserError):
                SSNExtrema()

    def test_empty_csv_handling(self):
        """Test behavior with empty CSV data."""
        with (
            patch("pandas.read_csv") as mock_read_csv,
            patch("pathlib.Path.exists", return_value=True),
        ):

            # Empty DataFrame
            empty_data = pd.DataFrame()
            mock_read_csv.return_value = empty_data

            extrema = SSNExtrema.__new__(SSNExtrema)

            # Should handle empty data gracefully (might raise error in stack/unstack)
            try:
                extrema.load_or_set_data()
            except (ValueError, IndexError):
                # These are acceptable errors for empty data
                pass

    def test_invalid_date_format_handling(self):
        """Test behavior with invalid date formats in CSV."""
        with (
            patch("pandas.read_csv") as mock_read_csv,
            patch("pathlib.Path.exists", return_value=True),
        ):

            # Data with invalid date formats
            invalid_data = pd.DataFrame(
                {
                    "Min": ["invalid-date", "1976-03-01"],
                    "Max": ["1968-11-01", "another-invalid-date"],
                },
                index=[20, 21],
            )
            mock_read_csv.return_value = invalid_data

            extrema = SSNExtrema.__new__(SSNExtrema)

            # pandas.to_datetime should handle invalid dates (might raise error or coerce)
            with patch(
                "solarwindpy.solar_activity.sunspot_number.sidc.pd.to_datetime"
            ) as mock_to_datetime:
                mock_to_datetime.side_effect = ValueError("Invalid date format")

                with pytest.raises(ValueError):
                    extrema.load_or_set_data()

    def test_class_name_in_error_message(self):
        """Test that class name appears correctly in error messages."""
        extrema = SSNExtrema.__new__(SSNExtrema)

        # Test that the error message contains the correct class name
        with pytest.raises(ValueError) as exc_info:
            extrema.load_or_set_data("arg")

        assert "SSNExtrema" in str(exc_info.value)

    def test_method_signature_validation(self):
        """Test that method accepts various argument patterns for validation."""
        extrema = SSNExtrema.__new__(SSNExtrema)

        # Test different argument patterns that should all raise errors
        error_cases = [
            (["arg1"], {}),
            ([], {"key": "value"}),
            (["arg1", "arg2"], {}),
            (["arg"], {"key": "value"}),
            ([], {"key1": "value1", "key2": "value2"}),
        ]

        for args, kwargs in error_cases:
            with pytest.raises(
                ValueError, match="SSNExtrema expects empty args and kwargs"
            ):
                extrema.load_or_set_data(*args, **kwargs)

    def test_successful_initialization_creates_expected_attributes(self):
        """Test that successful initialization creates expected attributes."""
        with (
            patch("pandas.read_csv") as mock_read_csv,
            patch("pathlib.Path.exists", return_value=True),
        ):

            # Mock successful CSV loading
            mock_data = pd.DataFrame(
                {"Min": ["2008-12-01"], "Max": ["2014-04-01"]}, index=[24]
            )

            processed_data = pd.DataFrame(
                {
                    "Min": [pd.Timestamp("2008-12-01")],
                    "Max": [pd.Timestamp("2014-04-01")],
                },
                index=[24],
            )
            processed_data.columns.names = ["kind"]

            mock_read_csv.return_value = mock_data

            with (
                patch("pandas.to_datetime"),
                patch.object(pd.DataFrame, "stack"),
                patch.object(pd.Series, "unstack", return_value=processed_data),
            ):

                extrema = SSNExtrema()

                # Check that the object has expected attributes from parent class
                assert hasattr(extrema, "_data")
                # IndicatorExtrema parent should provide additional attributes
                assert hasattr(extrema, "data")  # Property from parent
