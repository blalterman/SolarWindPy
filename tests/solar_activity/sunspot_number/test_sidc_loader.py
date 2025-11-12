#!/usr/bin/env python
"""Simplified test SIDCLoader class.

This module tests the core SIDCLoader functionality from solar_activity.sunspot_number.sidc:
- Data conversion and NaN handling
- Basic inheritance and method existence
- URL and key handling
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch

from solarwindpy.solar_activity.sunspot_number.sidc import SIDCLoader, SIDC_ID
from solarwindpy.solar_activity.base import DataLoader


class TestSIDCLoaderCore:
    """Test core SIDCLoader functionality."""

    def test_convert_nans_basic(self):
        """Test convert_nans replaces -1 with np.nan."""
        # Create a minimal loader instance for testing convert_nans method
        with (
            patch.object(DataLoader, "_init_logger"),
            patch.object(DataLoader, "get_data_ctime"),
            patch.object(DataLoader, "get_data_age"),
        ):
            loader = SIDCLoader("m", "http://example.com")

        # Create test DataFrame with -1 values
        test_data = pd.DataFrame(
            {
                "ssn": [10.5, -1, 25.3, -1, 8.7],
                "std": [2.1, 3.4, -1, 5.6, -1],
                "n_obs": [12, 15, -1, 18, 20],
            }
        )

        loader.convert_nans(test_data)

        # Check that -1 values are replaced with NaN
        assert pd.isna(test_data.loc[1, "ssn"])
        assert pd.isna(test_data.loc[3, "ssn"])
        assert pd.isna(test_data.loc[2, "std"])
        assert pd.isna(test_data.loc[4, "std"])
        assert pd.isna(test_data.loc[2, "n_obs"])

        # Check that other values remain unchanged
        assert test_data.loc[0, "ssn"] == 10.5
        assert test_data.loc[2, "ssn"] == 25.3
        assert test_data.loc[4, "ssn"] == 8.7

    def test_convert_nans_no_minus_ones(self):
        """Test convert_nans when there are no -1 values."""
        with (
            patch.object(DataLoader, "_init_logger"),
            patch.object(DataLoader, "get_data_ctime"),
            patch.object(DataLoader, "get_data_age"),
        ):
            loader = SIDCLoader("m", "http://example.com")

        test_data = pd.DataFrame({"ssn": [10.5, 20.3, 25.3], "std": [2.1, 3.4, 4.2]})
        original_data = test_data.copy()

        loader.convert_nans(test_data)

        # Data should remain unchanged
        pd.testing.assert_frame_equal(test_data, original_data)

    def test_convert_nans_all_minus_ones(self):
        """Test convert_nans when all values are -1."""
        with (
            patch.object(DataLoader, "_init_logger"),
            patch.object(DataLoader, "get_data_ctime"),
            patch.object(DataLoader, "get_data_age"),
        ):
            loader = SIDCLoader("m", "http://example.com")

        test_data = pd.DataFrame({"ssn": [-1, -1, -1], "std": [-1, -1, -1]})

        loader.convert_nans(test_data)

        # All values should be NaN
        assert test_data.isna().all().all()

    def test_inheritance_from_data_loader(self):
        """Test that SIDCLoader inherits from DataLoader."""
        from solarwindpy.solar_activity.base import DataLoader

        with (
            patch.object(DataLoader, "_init_logger"),
            patch.object(DataLoader, "get_data_ctime"),
            patch.object(DataLoader, "get_data_age"),
        ):
            loader = SIDCLoader("m", "http://example.com")

        assert isinstance(loader, DataLoader)
        # Check that it has key properties from the base class
        assert loader.key == "m"
        assert loader.url == "http://example.com"

    def test_data_path_property_structure(self):
        """Test that data_path property creates correct path structure."""
        # Mock the parent data_path to avoid filesystem dependencies
        with patch.object(
            SIDCLoader.__bases__[0], "data_path", new_callable=lambda: Path("/tmp/test")
        ):
            with (
                patch.object(DataLoader, "_init_logger"),
                patch.object(DataLoader, "get_data_ctime"),
                patch.object(DataLoader, "get_data_age"),
            ):
                loader = SIDCLoader("m", "http://example.com")

                expected_path = Path("/tmp/test") / "sidc" / "m"
                assert loader.data_path == expected_path

    def test_data_path_with_different_keys(self):
        """Test data_path property with different SIDC keys."""
        test_keys = ["d", "m", "m13", "y", "hd", "hm", "hm13"]

        for key in test_keys:
            with patch.object(
                SIDCLoader.__bases__[0],
                "data_path",
                new_callable=lambda: Path("/tmp/test"),
            ):
                with (
                    patch.object(DataLoader, "_init_logger"),
                    patch.object(DataLoader, "get_data_ctime"),
                    patch.object(DataLoader, "get_data_age"),
                ):
                    loader = SIDCLoader(key, "http://example.com")
                    expected_path = Path("/tmp/test") / "sidc" / key
                    assert loader.data_path == expected_path

    def test_method_existence(self):
        """Test that required methods exist."""
        with (
            patch.object(DataLoader, "_init_logger"),
            patch.object(DataLoader, "get_data_ctime"),
            patch.object(DataLoader, "get_data_age"),
        ):
            loader = SIDCLoader("m", "http://example.com")

        # Check that key methods exist
        assert hasattr(loader, "convert_nans")
        assert callable(loader.convert_nans)
        assert hasattr(loader, "download_data")
        assert callable(loader.download_data)
        assert hasattr(loader, "load_data")
        assert callable(loader.load_data)
        assert hasattr(loader, "data_path")

    @patch("pandas.read_csv")
    def test_download_data_calls_read_csv(self, mock_read_csv, tmp_path):
        """Test that download_data calls pandas.read_csv."""
        # Create a simple mock CSV response
        mock_csv = pd.DataFrame(
            {
                "year": [1996],
                "month": [1],
                "year_fraction": [1996.042],
                "ssn": [17.5],
                "std": [8.0],
                "n_obs": [14],
                "definitive": [True],
            }
        )
        mock_read_csv.return_value = mock_csv

        with (
            patch.object(DataLoader, "_init_logger"),
            patch.object(DataLoader, "get_data_ctime"),
            patch.object(DataLoader, "get_data_age"),
        ):
            loader = SIDCLoader("m", "http://example.com/snmtotcsv.php")
            loader._logger = Mock()  # Mock the logger to avoid logging issues

        new_data_path = tmp_path / "new_data"
        old_data_path = tmp_path / "old_data"

        loader.download_data(new_data_path, old_data_path)

        # Verify that read_csv was called with the URL
        mock_read_csv.assert_called_once()
        args, kwargs = mock_read_csv.call_args
        assert args[0] == "http://example.com/snmtotcsv.php"
        assert kwargs["sep"] == ";"
        assert kwargs["header"] is None

    def test_download_data_invalid_key_raises_error(self, tmp_path):
        """Test that invalid keys in download_data raise NotImplementedError."""
        with (
            patch.object(DataLoader, "_init_logger"),
            patch.object(DataLoader, "get_data_ctime"),
            patch.object(DataLoader, "get_data_age"),
        ):
            loader = SIDCLoader("invalid_key", "http://example.com")
            loader._logger = Mock()

        new_data_path = tmp_path / "new_data"
        old_data_path = tmp_path / "old_data"

        with pytest.raises(
            NotImplementedError, match="You have not yet used the SSN specified"
        ):
            loader.download_data(new_data_path, old_data_path)

    @patch.object(SIDCLoader.__bases__[0], "load_data")  # Mock parent load_data
    @patch("solarwindpy.solar_activity.sunspot_number.sidc.SSNExtrema")
    def test_load_data_calls_parent_and_ssn_extrema(
        self, mock_ssn_extrema_class, mock_parent_load_data
    ):
        """Test that load_data calls parent load_data and uses SSNExtrema."""
        with (
            patch.object(DataLoader, "_init_logger"),
            patch.object(DataLoader, "get_data_ctime"),
            patch.object(DataLoader, "get_data_age"),
        ):
            loader = SIDCLoader("m", "http://example.com")
            loader._logger = Mock()

        # Create mock data for the loader
        test_dates = pd.date_range("2008-01-01", "2010-12-31", freq="MS")
        test_data = pd.DataFrame(
            {
                "ssn": np.random.uniform(10, 100, len(test_dates)),
                "std": np.random.uniform(5, 15, len(test_dates)),
            },
            index=test_dates,
        )
        loader._data = test_data

        # Mock SSNExtrema
        mock_extrema = Mock()
        mock_intervals = pd.DataFrame(
            {
                "Cycle": [
                    pd.Interval(pd.Timestamp("2008-01-01"), pd.Timestamp("2019-12-31")),
                    pd.Interval(pd.Timestamp("2020-01-01"), pd.Timestamp("2030-12-31")),
                ]
            },
            index=[24, 25],
        )
        mock_intervals.index.name = "Number"
        mock_extrema.cycle_intervals = mock_intervals
        mock_ssn_extrema_class.return_value = mock_extrema

        loader.load_data()

        # Verify parent load_data was called
        mock_parent_load_data.assert_called_once()

        # Verify SSNExtrema was instantiated
        mock_ssn_extrema_class.assert_called_once()


class TestSIDCLoaderEdgeCases:
    """Test edge cases for SIDCLoader."""

    def test_convert_nans_mixed_dtypes(self):
        """Test convert_nans with mixed data types."""
        with (
            patch.object(DataLoader, "_init_logger"),
            patch.object(DataLoader, "get_data_ctime"),
            patch.object(DataLoader, "get_data_age"),
        ):
            loader = SIDCLoader("m", "http://example.com")

        test_data = pd.DataFrame(
            {
                "ssn": [10.5, -1, 25.3],  # float
                "n_obs": [12, -1, 18],  # int
                "definitive": [True, False, True],  # bool, shouldn't change
            }
        )

        loader.convert_nans(test_data)

        # Check float column
        assert pd.isna(test_data.loc[1, "ssn"])
        assert test_data.loc[0, "ssn"] == 10.5

        # Check int column
        assert pd.isna(test_data.loc[1, "n_obs"])
        assert test_data.loc[0, "n_obs"] == 12

        # Check bool column (should remain unchanged)
        assert test_data.loc[0, "definitive"]
        assert not test_data.loc[1, "definitive"]

    def test_initialization_with_real_sidc_id(self):
        """Test initialization with a real SIDC_ID object."""
        sidc_id = SIDC_ID("m")

        with (
            patch.object(DataLoader, "_init_logger"),
            patch.object(DataLoader, "get_data_ctime"),
            patch.object(DataLoader, "get_data_age"),
        ):
            loader = SIDCLoader(sidc_id.key, sidc_id.url)

        assert loader.key == "m"
        assert "snmtotcsv.php" in loader.url
        assert isinstance(loader, SIDCLoader)

    def test_path_creation_does_not_create_directories(self):
        """Test that accessing data_path doesn't create actual directories."""
        with patch.object(
            SIDCLoader.__bases__[0],
            "data_path",
            new_callable=lambda: Path("/nonexistent/test"),
        ):
            with (
                patch.object(DataLoader, "_init_logger"),
                patch.object(DataLoader, "get_data_ctime"),
                patch.object(DataLoader, "get_data_age"),
            ):
                loader = SIDCLoader("m", "http://example.com")

                path = loader.data_path
                # Path object should be created but directory shouldn't exist
                assert isinstance(path, Path)
                assert not path.exists()  # Should not create actual directory
