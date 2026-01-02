#!/usr/bin/env python
"""Test SIDC class.

This module tests the SIDC main class from solar_activity.sunspot_number.sidc:
- Initialization with loader and SSNExtrema
- Extrema calculation and edge detection
- Normalization functionality
- SSN band cutting and plotting
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from solarwindpy.solar_activity.sunspot_number.sidc import SIDC, SIDCLoader, SSNExtrema


@pytest.fixture
def mock_loader_data():
    """Create mock loader data for testing."""
    dates = pd.date_range("2008-01-01", "2020-12-31", freq="MS")
    # Simulate solar cycle 24 data with realistic SSN values
    cycle_data = []
    cycle_numbers = []
    ssn_values = []

    for i, date in enumerate(dates):
        if date < pd.Timestamp("2019-12-01"):
            cycle_numbers.append(24)
            # Simple sine wave for cycle 24 with realistic SSN range
            phase = (i / len(dates)) * 2 * np.pi
            ssn_values.append(50 + 100 * np.sin(phase) + np.random.normal(0, 10))
        else:
            cycle_numbers.append(25)
            # Beginning of cycle 25
            phase = ((i - 144) / 20) * 0.5 * np.pi
            ssn_values.append(10 + 30 * np.sin(phase) + np.random.normal(0, 5))

    return pd.DataFrame(
        {
            "ssn": ssn_values,
            "std": np.random.uniform(5, 15, len(dates)),
            "n_obs": np.random.randint(10, 25, len(dates)),
            "cycle": cycle_numbers,
            "definitive": True,
        },
        index=dates,
    )


@pytest.fixture
def mock_extrema_data():
    """Create mock extrema data for testing."""
    return pd.DataFrame(
        {
            "Min": [pd.Timestamp("2008-12-01"), pd.Timestamp("2019-12-01")],
            "Max": [pd.Timestamp("2014-04-01"), pd.Timestamp("2025-04-01")],
        },
        index=[24, 25],
    )


class TestSIDC:
    """Test the SIDC main class for sunspot number analysis."""

    @patch("solarwindpy.solar_activity.sunspot_number.sidc.SIDCLoader")
    @patch("solarwindpy.solar_activity.sunspot_number.sidc.SSNExtrema")
    @patch("solarwindpy.solar_activity.sunspot_number.sidc.SIDC_ID")
    def test_initialization(
        self,
        mock_sidc_id_class,
        mock_ssn_extrema_class,
        mock_sidc_loader_class,
        mock_loader_data,
        mock_extrema_data,
    ):
        """Test SIDC initialization with dummy loader and SSNExtrema."""
        # Setup mocks - use spec to make it pass isinstance check
        from solarwindpy.solar_activity.base import ID

        mock_id = Mock(spec=ID)
        mock_id.key = "m"
        mock_id.url = "http://example.com"
        mock_sidc_id_class.return_value = mock_id

        mock_loader = Mock()
        mock_loader.data = mock_loader_data
        mock_sidc_loader_class.return_value = mock_loader

        mock_extrema = Mock()
        mock_extrema.data = mock_extrema_data
        mock_ssn_extrema_class.return_value = mock_extrema

        # Mock methods that get called during initialization
        with (
            patch.object(SIDC, "_init_logger"),
            patch.object(SIDC, "calculate_extrema_kind"),
            patch.object(SIDC, "calculate_edge"),
        ):

            sidc = SIDC("m")

            # Verify initialization steps
            mock_sidc_id_class.assert_called_once_with("m")
            mock_ssn_extrema_class.assert_called_once()
            assert hasattr(sidc, "_loader")
            assert hasattr(sidc, "_extrema")

    @patch("solarwindpy.solar_activity.sunspot_number.sidc.SIDCLoader")
    def test_load_data(self, mock_sidc_loader_class):
        """Test load_data method."""
        mock_loader = Mock()
        mock_sidc_loader_class.return_value = mock_loader

        with patch.object(SIDC, "_init_logger"):
            sidc = SIDC.__new__(SIDC)
            sidc._id = Mock()
            sidc._id.key = "m"
            sidc._id.url = "http://example.com"

            sidc.load_data()

            # Verify loader was created and loaded
            mock_sidc_loader_class.assert_called_once_with("m", "http://example.com")
            mock_loader.load_data.assert_called_once()
            assert sidc._loader == mock_loader

    @patch("solarwindpy.solar_activity.sunspot_number.sidc.SSNExtrema")
    def test_set_extrema(self, mock_ssn_extrema_class):
        """Test set_extrema method."""
        mock_extrema = Mock()
        mock_ssn_extrema_class.return_value = mock_extrema

        with patch.object(SIDC, "_init_logger"):
            sidc = SIDC.__new__(SIDC)

            sidc.set_extrema()

            mock_ssn_extrema_class.assert_called_once()
            assert sidc._extrema == mock_extrema

    def test_calculate_extrema_kind(self, mock_loader_data, mock_extrema_data):
        """Test calculate_extrema_kind method."""
        with patch.object(SIDC, "_init_logger"):
            sidc = SIDC.__new__(SIDC)
            sidc._loader = Mock()
            sidc._loader.data = mock_loader_data.copy()
            sidc._extrema = Mock()
            sidc._extrema.data = mock_extrema_data.copy()

            # Ensure data columns match expected format
            sidc._extrema.data.columns.names = ["kind"]
            sidc._extrema.data.index.name = "Number"

            sidc.calculate_extrema_kind()

            # Verify extremum column was added
            assert "extremum" in sidc._loader.data.columns

            # Check that values are labeled correctly (should contain cycle numbers and Min/Max)
            extremum_values = sidc._loader.data["extremum"].dropna()
            assert len(extremum_values) > 0

            # Values should contain cycle indicators like "24-Min", "24-Max", "25-Min"
            for val in extremum_values:
                assert isinstance(val, str)
                assert any(cycle_str in val for cycle_str in ["24", "25"])
                assert any(ext_str in val for ext_str in ["Min", "Max"])

    def test_calculate_edge(self, mock_loader_data, mock_extrema_data):
        """Test calculate_edge method."""
        with patch.object(SIDC, "_init_logger"):
            sidc = SIDC.__new__(SIDC)
            sidc._loader = Mock()
            sidc._loader.data = mock_loader_data.copy()
            sidc._extrema = Mock()
            sidc._extrema.data = mock_extrema_data.copy()

            # Ensure data columns match expected format
            sidc._extrema.data.columns.names = ["kind"]
            sidc._extrema.data.index.name = "Number"

            sidc.calculate_edge()

            # Verify edge column was added
            assert "edge" in sidc._loader.data.columns

            # Check that values are either "Rise" or "Fall"
            edge_values = sidc._loader.data["edge"].dropna()
            assert len(edge_values) > 0

            for val in edge_values:
                assert val in ["Rise", "Fall"]

    def test_run_normalization_max(self, mock_loader_data, mock_extrema_data):
        """Test run_normalization with max normalization."""
        from solarwindpy.solar_activity.base import ID

        with patch.object(SIDC, "_init_logger"):
            sidc = SIDC.__new__(SIDC)
            sidc._logger = Mock()
            sidc._id = Mock(spec=ID)  # Add missing _id attribute
            sidc._loader = Mock()
            sidc._loader.data = mock_loader_data.copy()
            sidc._extrema = Mock()
            sidc._extrema.data = mock_extrema_data.copy()

            # Mock the extrema.cut_spec_by_interval method
            sidc._extrema.cut_spec_by_interval = Mock()
            cut_data = pd.Series(
                [pd.Interval(0, 100)] * len(mock_loader_data),
                index=mock_loader_data.index,
                name="cycle",
            )
            sidc._extrema.cut_spec_by_interval.return_value = cut_data

            result = sidc.run_normalization(norm_by="max")

            # Verify normalization was applied
            assert isinstance(result, pd.Series)
            assert "nssn" in sidc._loader.data.columns

            # Max normalization divides by max value - can produce negative values if input has negatives
            nssn_values = sidc._loader.data["nssn"].dropna()
            assert nssn_values.max() <= 1  # Max should always be 1 after normalization

    def test_run_normalization_zscore(self, mock_loader_data, mock_extrema_data):
        """Test run_normalization with zscore normalization."""
        with patch.object(SIDC, "_init_logger"):
            sidc = SIDC.__new__(SIDC)
            sidc._logger = Mock()
            sidc._loader = Mock()
            sidc._loader.data = mock_loader_data.copy()
            sidc._extrema = Mock()
            sidc._extrema.data = mock_extrema_data.copy()

            # Mock the extrema.cut_spec_by_interval method
            sidc._extrema.cut_spec_by_interval = Mock()
            cut_data = pd.Series(
                [pd.Interval(0, 100)] * len(mock_loader_data),
                index=mock_loader_data.index,
                name="cycle",
            )
            sidc._extrema.cut_spec_by_interval.return_value = cut_data

            result = sidc.run_normalization(norm_by="zscore")

            # Verify normalization was applied
            assert isinstance(result, pd.Series)
            assert "nssn" in sidc._loader.data.columns

            # Z-score normalized values should have roughly mean=0, std=1
            nssn_values = sidc._loader.data["nssn"].dropna()
            assert abs(nssn_values.mean()) < 0.1  # Close to 0
            assert abs(nssn_values.std() - 1.0) < 0.1  # Close to 1

    def test_run_normalization_invalid_method(self, mock_loader_data):
        """Test run_normalization with invalid method raises error."""
        with patch.object(SIDC, "_init_logger"):
            sidc = SIDC.__new__(SIDC)
            sidc._loader = Mock()
            sidc._loader.data = mock_loader_data.copy()

            with pytest.raises(AssertionError):
                sidc.run_normalization(norm_by="invalid_method")

    def test_cut_spec_by_ssn_band(self, mock_loader_data):
        """Test cut_spec_by_ssn_band method."""
        from solarwindpy.solar_activity.base import ID

        with patch.object(SIDC, "_init_logger"):
            sidc = SIDC.__new__(SIDC)
            sidc._id = Mock(spec=ID)  # Add missing _id attribute
            sidc._loader = Mock()
            sidc._loader.data = mock_loader_data.copy()

            # Create mock interpolated data
            sidc._interpolated = mock_loader_data[["ssn"]].copy()

            # Test the method
            result = sidc.cut_spec_by_ssn_band(key="ssn", dssn=10.0)

            # Verify result
            assert isinstance(result, pd.Series)
            assert result.name == "ssn_band"
            assert hasattr(sidc, "_spec_by_ssn_band")
            assert hasattr(sidc, "_ssn_band_intervals")

    def test_cut_spec_by_ssn_band_normalized_validation(self, mock_loader_data):
        """Test that cut_spec_by_ssn_band validates dssn for normalized data."""
        from solarwindpy.solar_activity.base import ID

        with patch.object(SIDC, "_init_logger"):
            sidc = SIDC.__new__(SIDC)
            sidc._id = Mock(spec=ID)  # Add missing _id attribute
            sidc._loader = Mock()
            sidc._loader.data = mock_loader_data.copy()
            sidc._loader.data["nssn"] = sidc._loader.data["ssn"] / 100  # Normalized

            # Create mock interpolated data
            sidc._interpolated = sidc._loader.data[["nssn"]].copy()

            # Should raise error for dssn >= 1 with normalized data
            with pytest.raises(
                ValueError, match="Normalized SSN requires that dssn < 1"
            ):
                sidc.cut_spec_by_ssn_band(key="nssn", dssn=1.5)

    def test_interpolate_data(self, mock_loader_data):
        """Test interpolate_data method."""
        with patch.object(SIDC, "_init_logger"):
            sidc = SIDC.__new__(SIDC)
            sidc._loader = Mock()
            sidc._loader.data = mock_loader_data.copy()

            # Create target index for interpolation
            target_index = pd.date_range("2010-01-01", "2015-12-31", freq="D")

            # Mock parent interpolate_data method
            expected_result = pd.Series(
                np.random.uniform(10, 100, len(target_index)),
                index=target_index,
                name="ssn",
            )

            with patch.object(
                SIDC.__bases__[0], "interpolate_data", return_value=expected_result
            ):
                result = sidc.interpolate_data(target_index, key="ssn")

                # Verify result
                assert isinstance(result, pd.Series)
                assert len(result) == len(target_index)
                assert hasattr(sidc, "_interpolated")

    def test_properties_access(self, mock_loader_data, mock_extrema_data):
        """Test property accessors."""
        with patch.object(SIDC, "_init_logger"):
            sidc = SIDC.__new__(SIDC)
            sidc._loader = Mock()
            sidc._loader.data = mock_loader_data.copy()
            sidc._extrema = Mock()
            sidc._extrema.data = mock_extrema_data.copy()

            # Set up some internal state
            sidc._spec_by_ssn_band = pd.Series([1, 2, 3])
            sidc._ssn_band_intervals = pd.IntervalIndex([pd.Interval(0, 10)])

            # Test properties
            assert hasattr(sidc, "spec_by_ssn_band")
            assert hasattr(sidc, "ssn_band_intervals")

            assert sidc.spec_by_ssn_band is not None
            assert sidc.ssn_band_intervals is not None

    def test_inheritance_from_activity_indicator(self):
        """Test that SIDC inherits from ActivityIndicator."""
        from solarwindpy.solar_activity.base import ActivityIndicator

        with (
            patch.object(SIDC, "_init_logger"),
            patch.object(SIDC, "load_data"),
            patch.object(SIDC, "set_extrema"),
            patch.object(SIDC, "calculate_extrema_kind"),
            patch.object(SIDC, "calculate_edge"),
        ):

            sidc = SIDC("m")
            assert isinstance(sidc, ActivityIndicator)


class TestSIDCEdgeCases:
    """Test edge cases and error conditions for SIDC."""

    def test_normalized_property_without_nssn_column(self, mock_loader_data):
        """Test normalized property when nssn column doesn't exist."""
        from solarwindpy.solar_activity.base import ID

        with patch.object(SIDC, "_init_logger"):
            sidc = SIDC.__new__(SIDC)
            sidc._id = Mock(spec=ID)  # Add missing _id attribute
            sidc._loader = Mock()
            sidc._loader.data = mock_loader_data.copy()  # No 'nssn' column

            # Mock normalize_ssn method
            expected_normalized = pd.Series(
                np.random.uniform(0, 1, len(mock_loader_data)),
                index=mock_loader_data.index,
                name="nssn",
            )

            with patch.object(
                sidc, "run_normalization", return_value=expected_normalized
            ):
                result = sidc.normalized

                # Should call run_normalization when nssn column doesn't exist
                sidc.run_normalization.assert_called_once()
                assert isinstance(result, pd.Series)

    def test_normalized_property_with_existing_nssn(self, mock_loader_data):
        """Test normalized property when nssn column exists."""
        with patch.object(SIDC, "_init_logger"):
            sidc = SIDC.__new__(SIDC)
            sidc._loader = Mock()
            test_data = mock_loader_data.copy()
            test_data["nssn"] = test_data["ssn"] / 100  # Add normalized column
            sidc._loader.data = test_data

            result = sidc.normalized

            # Should return existing nssn column
            assert isinstance(result, pd.Series)
            assert result.name == "nssn"
            pd.testing.assert_series_equal(result, test_data["nssn"])

    def test_data_property_access(self, mock_loader_data):
        """Test that data property returns loader data."""
        with patch.object(SIDC, "_init_logger"):
            sidc = SIDC.__new__(SIDC)
            sidc._loader = Mock()
            sidc._loader.data = mock_loader_data.copy()

            result = sidc.data

            assert isinstance(result, pd.DataFrame)
            pd.testing.assert_frame_equal(result, mock_loader_data)

    def test_calculate_extrema_kind_empty_data(self):
        """Test calculate_extrema_kind with empty data."""
        with patch.object(SIDC, "_init_logger"):
            sidc = SIDC.__new__(SIDC)
            sidc._loader = Mock()
            sidc._loader.data = pd.DataFrame(columns=["cycle", "ssn"])
            sidc._extrema = Mock()
            sidc._extrema.data = pd.DataFrame(columns=["Min", "Max"])

            # Should handle empty data gracefully
            sidc.calculate_extrema_kind()

            assert "extremum" in sidc._loader.data.columns

    def test_calculate_edge_empty_data(self):
        """Test calculate_edge with empty data."""
        with patch.object(SIDC, "_init_logger"):
            sidc = SIDC.__new__(SIDC)
            sidc._loader = Mock()
            sidc._loader.data = pd.DataFrame(columns=["cycle", "ssn"])
            sidc._extrema = Mock()
            sidc._extrema.data = pd.DataFrame(columns=["Min", "Max"])

            # Should handle empty data gracefully
            sidc.calculate_edge()

            assert "edge" in sidc._loader.data.columns

    def test_plot_on_colorbar_method_exists(self):
        """Test that plot_on_colorbar method exists and is callable."""
        with (
            patch.object(SIDC, "_init_logger"),
            patch.object(SIDC, "load_data"),
            patch.object(SIDC, "set_extrema"),
            patch.object(SIDC, "calculate_extrema_kind"),
            patch.object(SIDC, "calculate_edge"),
        ):

            sidc = SIDC("m")

            assert hasattr(sidc, "plot_on_colorbar")
            assert callable(sidc.plot_on_colorbar)
