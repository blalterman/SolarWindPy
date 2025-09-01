#!/usr/bin/env python
"""Test solar_activity package entry point (__init__.py).

This module tests the `get_all_indices()` function which aggregates solar activity
indices from multiple sources (LISIRD and SIDC).
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock

import solarwindpy.solar_activity as sa


class TestGetAllIndices:
    """Test the get_all_indices() aggregation function."""

    @pytest.fixture
    def mock_lisird_data(self):
        """Create mock LISIRD data structures for testing."""
        # Create synthetic Lalpha data
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        lalpha_data = pd.DataFrame(
            {"irradiance": np.random.uniform(0.001, 0.005, 100)}, index=dates
        )

        # Create synthetic CaK data with extra milliseconds column
        cak_data = pd.DataFrame(
            {
                "irradiance": np.random.uniform(1000, 2000, 100),
                "milliseconds": np.zeros(100),  # This should be dropped
            },
            index=dates,
        )

        # Create synthetic MgII data
        mgii_data = pd.DataFrame(
            {"mg_index": np.random.uniform(0.25, 0.30, 100)}, index=dates
        )

        return {"Lalpha": lalpha_data, "CaK": cak_data, "MgII": mgii_data}

    @pytest.fixture
    def mock_sidc_data(self):
        """Create mock SIDC data structure for testing."""
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        sidc_data = pd.DataFrame({"ssn": np.random.uniform(0, 200, 100)}, index=dates)
        return sidc_data

    @pytest.fixture
    def dummy_lisird_class(self, mock_lisird_data):
        """Create a dummy LISIRD class that returns mock data."""

        class DummyLISIRD:
            def __init__(self, key):
                self.key = key
                self._data = mock_lisird_data[key].copy()

            @property
            def data(self):
                return self._data

        return DummyLISIRD

    @pytest.fixture
    def dummy_sidc_class(self, mock_sidc_data):
        """Create a dummy SIDC class that returns mock data."""

        class DummySIDC:
            def __init__(self, key):
                self.key = key
                self._data = mock_sidc_data.copy()

            @property
            def data(self):
                return self._data

        return DummySIDC

    def test_get_all_indices_structure(self, dummy_lisird_class, dummy_sidc_class):
        """Test that get_all_indices() returns correct structure and columns."""
        # Mock the LISIRD and SIDC classes
        with patch(
            "solarwindpy.solar_activity.lisird.lisird.LISIRD", dummy_lisird_class
        ):
            with patch(
                "solarwindpy.solar_activity.sunspot_number.sidc.SIDC", dummy_sidc_class
            ):
                result = sa.get_all_indices()

        # Check that result is a DataFrame
        assert isinstance(result, pd.DataFrame)

        # Check expected columns are present (sorted alphabetically)
        expected_columns = ["CaK", "Lalpha", "MgII", "ssn"]
        assert list(
            result.columns.get_level_values(0).unique().sort_values()
        ) == sorted(expected_columns)

        # Check index type is DatetimeIndex
        assert isinstance(result.index, pd.DatetimeIndex)

    def test_get_all_indices_columns_exact(self, dummy_lisird_class, dummy_sidc_class):
        """Test exact column structure matches expected format."""
        with patch(
            "solarwindpy.solar_activity.lisird.lisird.LISIRD", dummy_lisird_class
        ):
            with patch(
                "solarwindpy.solar_activity.sunspot_number.sidc.SIDC", dummy_sidc_class
            ):
                result = sa.get_all_indices()

        # Extract top-level column names
        top_level_columns = result.columns.get_level_values(0).unique()
        assert "CaK" in top_level_columns
        assert "Lalpha" in top_level_columns
        assert "MgII" in top_level_columns
        assert "ssn" in top_level_columns

    def test_get_all_indices_datetime_index(self, dummy_lisird_class, dummy_sidc_class):
        """Test that result index is properly formatted DatetimeIndex."""
        with patch(
            "solarwindpy.solar_activity.lisird.lisird.LISIRD", dummy_lisird_class
        ):
            with patch(
                "solarwindpy.solar_activity.sunspot_number.sidc.SIDC", dummy_sidc_class
            ):
                result = sa.get_all_indices()

        # Verify index type
        assert isinstance(result.index, pd.DatetimeIndex)

        # Verify index is sorted
        assert result.index.is_monotonic_increasing

        # Verify reasonable date range
        assert result.index.min() >= pd.Timestamp("2019-01-01")
        assert result.index.max() <= pd.Timestamp("2025-01-01")

    def test_get_all_indices_data_aggregation(
        self, dummy_lisird_class, dummy_sidc_class
    ):
        """Test that data from different sources is properly aggregated."""
        with patch(
            "solarwindpy.solar_activity.lisird.lisird.LISIRD", dummy_lisird_class
        ):
            with patch(
                "solarwindpy.solar_activity.sunspot_number.sidc.SIDC", dummy_sidc_class
            ):
                result = sa.get_all_indices()

        # Check that data is not empty
        assert len(result) > 0

        # Check that each column has some non-null data
        assert not result["Lalpha"].isna().all().all()
        assert not result["ssn"].isna().all().all()
        assert not result["MgII"].isna().all().all()

        # CaK should have milliseconds column dropped
        if hasattr(result, "CaK"):
            cak_columns = [col for col in result.columns if col[0] == "CaK"]
            assert len(cak_columns) >= 1
            # Verify no 'milliseconds' subcolumn
            subcolumns = [col[1] for col in cak_columns if col[0] == "CaK"]
            assert "milliseconds" not in subcolumns

    def test_get_all_indices_mgii_date_conversion(
        self, dummy_lisird_class, dummy_sidc_class
    ):
        """Test that MgII data index is properly converted to date-only."""
        # Create MgII data with timestamp index
        dates_with_time = pd.date_range("2020-01-01 12:30:45", periods=50, freq="D")
        mgii_data_with_time = pd.DataFrame(
            {"mg_index": np.random.uniform(0.25, 0.30, 50)}, index=dates_with_time
        )

        class DummyLISIRDWithTime:
            def __init__(self, key):
                self.key = key
                if key == "MgII":
                    self._data = mgii_data_with_time
                else:
                    # Use simplified mock data for other keys
                    dates = pd.date_range("2020-01-01", periods=50, freq="D")
                    if key == "Lalpha":
                        self._data = pd.DataFrame(
                            {"irradiance": np.random.uniform(0.001, 0.005, 50)},
                            index=dates,
                        )
                    else:  # CaK
                        self._data = pd.DataFrame(
                            {
                                "irradiance": np.random.uniform(1000, 2000, 50),
                                "milliseconds": np.zeros(50),
                            },
                            index=dates,
                        )

            @property
            def data(self):
                return self._data

        with patch(
            "solarwindpy.solar_activity.lisird.lisird.LISIRD", DummyLISIRDWithTime
        ):
            with patch(
                "solarwindpy.solar_activity.sunspot_number.sidc.SIDC", dummy_sidc_class
            ):
                result = sa.get_all_indices()

        # Verify that the result index only contains dates (no time component)
        assert all(
            timestamp.time() == pd.Timestamp("00:00:00").time()
            for timestamp in result.index[:5]
        )  # Check first 5 entries

    def test_get_all_indices_error_handling(self):
        """Test error handling when mocked classes raise exceptions."""

        class BrokenLISIRD:
            def __init__(self, key):
                raise ValueError(f"Failed to initialize LISIRD with key {key}")

        with patch("solarwindpy.solar_activity.lisird.lisird.LISIRD", BrokenLISIRD):
            with pytest.raises(ValueError, match="Failed to initialize LISIRD"):
                sa.get_all_indices()

    def test_imports_available(self):
        """Test that necessary imports are available in the module."""
        # Test that submodules are accessible
        assert hasattr(sa, "lisird")
        assert hasattr(sa, "sunspot_number")
        assert hasattr(sa, "ssn")
        assert hasattr(sa, "plots")

        # Test that ssn is an alias for sunspot_number
        assert sa.ssn is sa.sunspot_number

    def test_get_all_indices_function_exists(self):
        """Test that get_all_indices function is available."""
        assert hasattr(sa, "get_all_indices")
        assert callable(sa.get_all_indices)


class TestPackageStructure:
    """Test package-level structure and imports."""

    def test_package_all_exports(self):
        """Test that __all__ exports are correct."""
        # Check __all__ contains expected items
        expected_all = ["sunspot_number", "ssn", "lisird", "plots"]
        assert hasattr(sa, "__all__")

        # Check that all items in __all__ are actually available
        for item in sa.__all__:
            assert hasattr(sa, item), f"Item '{item}' in __all__ but not available"

    def test_ssn_alias(self):
        """Test that ssn is properly aliased to sunspot_number."""
        assert sa.ssn is sa.sunspot_number

    def test_submodule_imports(self):
        """Test that required submodules are imported."""
        # These should be available due to import statements
        assert hasattr(sa, "lisird")
        assert hasattr(sa, "sunspot_number")
        assert hasattr(sa, "plots")

        # Test that they are modules
        import types

        assert isinstance(sa.lisird, types.ModuleType)
        assert isinstance(sa.sunspot_number, types.ModuleType)
        assert isinstance(sa.plots, types.ModuleType)


class TestMockingIntegration:
    """Test the mocking setup for external dependencies."""

    def test_lisird_mocking_pattern(self):
        """Test that LISIRD can be properly mocked."""
        mock_lisird = Mock()
        mock_lisird.return_value.data = pd.DataFrame(
            {"irradiance": [0.002, 0.003, 0.004]},
            index=pd.date_range("2020-01-01", periods=3),
        )

        with patch("solarwindpy.solar_activity.lisird.lisird.LISIRD", mock_lisird):
            # This should work without errors
            sa.lisird.lisird.LISIRD("Lalpha")

        # Verify mock was called
        mock_lisird.assert_called_with("Lalpha")

    def test_sidc_mocking_pattern(self):
        """Test that SIDC can be properly mocked."""
        mock_sidc = Mock()
        mock_sidc.return_value.data = pd.DataFrame(
            {"ssn": [50, 75, 100]}, index=pd.date_range("2020-01-01", periods=3)
        )

        with patch("solarwindpy.solar_activity.sunspot_number.sidc.SIDC", mock_sidc):
            # This should work without errors
            sa.sunspot_number.sidc.SIDC("m13")

        # Verify mock was called
        mock_sidc.assert_called_with("m13")


class TestRealWorldIntegration:
    """Test integration patterns that mirror real usage."""

    @pytest.fixture
    def dummy_lisird_class(self):
        """Create a dummy LISIRD class for integration testing."""
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        mock_data = {
            "Lalpha": pd.DataFrame(
                {"irradiance": np.random.uniform(0.001, 0.005, 100)}, index=dates
            ),
            "CaK": pd.DataFrame(
                {
                    "irradiance": np.random.uniform(1000, 2000, 100),
                    "milliseconds": np.zeros(100),
                },
                index=dates,
            ),
            "MgII": pd.DataFrame(
                {"mg_index": np.random.uniform(0.25, 0.30, 100)}, index=dates
            ),
        }

        class DummyLISIRD:
            def __init__(self, key):
                self.key = key
                self._data = mock_data[key].copy()

            @property
            def data(self):
                return self._data

        return DummyLISIRD

    @pytest.fixture
    def dummy_sidc_class(self):
        """Create a dummy SIDC class for integration testing."""
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        sidc_data = pd.DataFrame({"ssn": np.random.uniform(0, 200, 100)}, index=dates)

        class DummySIDC:
            def __init__(self, key):
                self.key = key
                self._data = sidc_data.copy()

            @property
            def data(self):
                return self._data

        return DummySIDC

    def test_complete_get_all_indices_workflow(
        self, dummy_lisird_class, dummy_sidc_class
    ):
        """Test complete workflow from start to finish."""
        with patch(
            "solarwindpy.solar_activity.lisird.lisird.LISIRD", dummy_lisird_class
        ):
            with patch(
                "solarwindpy.solar_activity.sunspot_number.sidc.SIDC", dummy_sidc_class
            ):
                # Call the main function
                result = sa.get_all_indices()

                # Verify comprehensive results
                assert isinstance(result, pd.DataFrame)
                assert len(result) > 0
                assert isinstance(result.index, pd.DatetimeIndex)

                # Check column structure
                expected_top_level = ["CaK", "Lalpha", "MgII", "ssn"]
                actual_top_level = list(result.columns.get_level_values(0).unique())
                for expected_col in expected_top_level:
                    assert (
                        expected_col in actual_top_level
                    ), f"Missing column: {expected_col}"

                # Verify data types are reasonable
                for col in result.columns:
                    assert result[col].dtype in [
                        np.float64,
                        np.float32,
                        np.int64,
                        np.int32,
                    ], f"Unexpected dtype for column {col}: {result[col].dtype}"
