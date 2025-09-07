#!/usr/bin/env python
"""Regression tests for pandas 2.3.1+ compatibility in hist2d.py.

These tests verify that the axis normalization methods work correctly
after replacing deprecated .max(level=...) syntax with .groupby(level=...).max().
"""

import numpy as np
import pandas as pd
import pytest

from solarwindpy.plotting.hist2d import Hist2D


class TestHist2DPandasCompatibility:
    """Test pandas 2.3.1+ compatibility for Hist2D axis normalization."""

    def setup_method(self):
        """Set up test data for each test."""
        np.random.seed(42)
        n = 1000

        # Create test data with known distributions
        self.x_data = pd.Series(np.random.normal(0, 1, n), name="x")
        self.y_data = pd.Series(np.random.normal(0, 1, n), name="y")
        self.z_data = pd.Series(np.random.uniform(0, 10, n), name="z")

    def test_column_normalize(self):
        """Test column normalize (axnorm='c')."""
        hist = Hist2D(self.x_data, self.y_data, self.z_data, nbins=10)
        hist.set_axnorm("c")

        # Get normalized aggregation
        agg = hist.agg()
        agg_unstacked = agg.unstack("x")

        # Check that max value in each column is 1.0 (or NaN)
        for col in agg_unstacked.columns:
            col_max = agg_unstacked[col].max()
            if not pd.isna(col_max):
                assert np.isclose(
                    col_max, 1.0, atol=1e-10
                ), f"Column {col} max is {col_max}, expected 1.0"

        # Check that all non-NaN values are between 0 and 1
        non_nan_values = agg.dropna()
        assert (
            non_nan_values >= 0
        ).all(), "Found negative values after column normalization"
        assert (
            non_nan_values <= 1.0001
        ).all(), "Found values > 1 after column normalization"

    def test_row_normalize(self):
        """Test row normalize (axnorm='r')."""
        hist = Hist2D(self.x_data, self.y_data, self.z_data, nbins=10)
        hist.set_axnorm("r")

        # Get normalized aggregation
        agg = hist.agg()
        agg_unstacked = agg.unstack("x")

        # Check that max value in each row is 1.0 (or NaN)
        for row_idx in agg_unstacked.index:
            row_max = agg_unstacked.loc[row_idx].max()
            if not pd.isna(row_max):
                assert np.isclose(
                    row_max, 1.0, atol=1e-10
                ), f"Row {row_idx} max is {row_max}, expected 1.0"

        # Check that all non-NaN values are between 0 and 1
        non_nan_values = agg.dropna()
        assert (
            non_nan_values >= 0
        ).all(), "Found negative values after row normalization"
        assert (
            non_nan_values <= 1.0001
        ).all(), "Found values > 1 after row normalization"

    def test_total_normalize(self):
        """Test total normalize (axnorm='t')."""
        hist = Hist2D(self.x_data, self.y_data, self.z_data, nbins=10)
        hist.set_axnorm("t")

        # Get normalized aggregation
        agg = hist.agg()

        # Check that max value overall is 1.0
        max_val = agg.max()
        assert np.isclose(
            max_val, 1.0, atol=1e-10
        ), f"Total max is {max_val}, expected 1.0"

        # Check that all non-NaN values are between 0 and 1
        non_nan_values = agg.dropna()
        assert (
            non_nan_values >= 0
        ).all(), "Found negative values after total normalization"
        assert (
            non_nan_values <= 1.0001
        ).all(), "Found values > 1 after total normalization"

    def test_density_normalize(self):
        """Test density normalize (axnorm='d').

        This should create a true 2D probability density function where
        the integral over the entire domain equals 1.
        """
        hist = Hist2D(self.x_data, self.y_data, self.z_data, nbins=10)
        hist.set_axnorm("d")

        # Get normalized aggregation
        agg = hist.agg()

        # Get bin widths for integration
        x_intervals = hist.intervals["x"]
        y_intervals = hist.intervals["y"]

        # Calculate dx and dy for each bin
        dx_values = pd.Series(
            [interval.length for interval in x_intervals], index=x_intervals
        )
        dy_values = pd.Series(
            [interval.length for interval in y_intervals], index=y_intervals
        )

        # Compute the integral: sum(agg * dx * dy)
        agg_unstacked = agg.unstack("x")
        total_integral = 0
        for y_idx, y_interval in enumerate(agg_unstacked.index):
            for x_idx, x_interval in enumerate(agg_unstacked.columns):
                value = agg_unstacked.iloc[y_idx, x_idx]
                if not pd.isna(value):
                    dx = dx_values[x_interval]
                    dy = dy_values[y_interval]
                    total_integral += value * dx * dy

        # The integral should be close to 1
        assert np.isclose(
            total_integral, 1.0, atol=0.01
        ), f"Density integral is {total_integral}, expected 1.0"

        # Values should be non-negative
        non_nan_values = agg.dropna()
        assert (
            non_nan_values >= 0
        ).all(), "Found negative values after density normalization"

    def test_pdfs_in_each_column(self):
        """Test PDFs in each column (axnorm='cd').

        This creates PDFs in each column, so integrating over y for each x should give 1.
        """
        hist = Hist2D(self.x_data, self.y_data, self.z_data, nbins=10)
        hist.set_axnorm("cd")

        # Get normalized aggregation
        agg = hist.agg()
        agg_unstacked = agg.unstack("x")

        # Get y bin widths for integration
        y_intervals = hist.intervals["y"]
        dy_values = pd.Series(
            [interval.length for interval in y_intervals], index=y_intervals
        )

        # For each column, integrate over y
        for col in agg_unstacked.columns:
            col_data = agg_unstacked[col]
            integral = 0
            for y_idx, y_interval in enumerate(col_data.index):
                value = col_data.iloc[y_idx]
                if not pd.isna(value):
                    dy = dy_values[y_interval]
                    integral += value * dy

            # Each column should integrate to 1 (if it has data)
            if integral > 0:  # Only check columns with data
                assert np.isclose(
                    integral, 1.0, atol=0.01
                ), f"Column {col} PDF integral is {integral}, expected 1.0"

        # Values should be non-negative
        non_nan_values = agg.dropna()
        assert (
            non_nan_values >= 0
        ).all(), "Found negative values after PDFs in each column"

    def test_pdfs_in_each_row(self):
        """Test PDFs in each row (axnorm='rd').

        This creates PDFs in each row, so integrating over x for each y should give 1.
        """
        hist = Hist2D(self.x_data, self.y_data, self.z_data, nbins=10)
        hist.set_axnorm("rd")

        # Get normalized aggregation
        agg = hist.agg()
        agg_unstacked = agg.unstack("x")

        # Get x bin widths for integration
        x_intervals = hist.intervals["x"]
        dx_values = pd.Series(
            [interval.length for interval in x_intervals], index=x_intervals
        )

        # For each row, integrate over x
        for row in agg_unstacked.index:
            row_data = agg_unstacked.loc[row]
            integral = 0
            for x_idx, x_interval in enumerate(row_data.index):
                value = row_data.iloc[x_idx]
                if not pd.isna(value):
                    dx = dx_values[x_interval]
                    integral += value * dx

            # Each row should integrate to 1 (if it has data)
            if integral > 0:  # Only check rows with data
                assert np.isclose(
                    integral, 1.0, atol=0.01
                ), f"Row {row} PDF integral is {integral}, expected 1.0"

        # Values should be non-negative
        non_nan_values = agg.dropna()
        assert (
            non_nan_values >= 0
        ).all(), "Found negative values after PDFs in each row"

    def test_no_normalization(self):
        """Test that no normalization (axnorm=None) works correctly."""
        hist = Hist2D(self.x_data, self.y_data, self.z_data, nbins=10)
        hist.set_axnorm(None)

        # Get aggregation without normalization
        agg = hist.agg()

        # Values should be the raw aggregated z values
        assert agg is not None
        assert not agg.isna().all(), "All values are NaN without normalization"

        # Check that values are in reasonable range for raw z data (0-10)
        non_nan_values = agg.dropna()
        assert non_nan_values.min() >= 0, "Found negative values in raw aggregation"
        assert (
            non_nan_values.max() <= 10.1
        ), "Found unexpectedly large values in raw aggregation"

    def test_edge_case_single_bin(self):
        """Test normalization with data that falls into a single bin."""
        # Create data that falls into one bin
        x_single = pd.Series([0.5] * 100, name="x")
        y_single = pd.Series([0.5] * 100, name="y")
        z_single = pd.Series(np.random.uniform(1, 2, 100), name="z")

        hist = Hist2D(x_single, y_single, z_single, nbins=10)
        hist.set_axnorm("c")

        # Get normalized aggregation
        agg = hist.agg()

        # Should have mostly NaN except for the single bin
        non_nan_count = agg.notna().sum()
        assert non_nan_count == 1, f"Expected 1 non-NaN value, got {non_nan_count}"

        # The single value should be 1.0 after normalization
        non_nan_value = agg.dropna().iloc[0]
        assert np.isclose(
            non_nan_value, 1.0, atol=1e-10
        ), f"Single bin value is {non_nan_value}, expected 1.0"

    def test_edge_case_with_nans(self):
        """Test normalization with NaN values in input data."""
        # Add some NaN values to the data
        x_with_nan = self.x_data.copy()
        y_with_nan = self.y_data.copy()
        z_with_nan = self.z_data.copy()

        # Insert NaNs at random positions
        nan_indices = np.random.choice(len(x_with_nan), 50, replace=False)
        x_with_nan.iloc[nan_indices] = np.nan
        y_with_nan.iloc[nan_indices[:25]] = np.nan
        z_with_nan.iloc[nan_indices[25:]] = np.nan

        hist = Hist2D(x_with_nan, y_with_nan, z_with_nan, nbins=10)
        hist.set_axnorm("c")

        # Should handle NaNs gracefully
        agg = hist.agg()
        assert agg is not None

        # Check that non-NaN values are properly normalized
        non_nan_values = agg.dropna()
        if len(non_nan_values) > 0:
            assert (non_nan_values >= 0).all(), "Found negative values with NaN input"
            assert (non_nan_values <= 1.0001).all(), "Found values > 1 with NaN input"

    def test_count_aggregation_with_column_normalize(self):
        """Test column normalize with count aggregation (no z values)."""
        # Create hist2d without z values (count aggregation)
        hist = Hist2D(self.x_data, self.y_data, nbins=10)
        hist.set_axnorm("c")

        # Get normalized aggregation
        agg = hist.agg()
        agg_unstacked = agg.unstack("x")

        # Check that max value in each column is 1.0 (or NaN)
        for col in agg_unstacked.columns:
            col_max = agg_unstacked[col].max()
            if not pd.isna(col_max):
                assert np.isclose(
                    col_max, 1.0, atol=1e-10
                ), f"Column {col} max is {col_max}, expected 1.0"

    def test_log_scale_with_normalization(self):
        """Test normalization with log-scaled data."""
        # Use positive data for log scale
        x_positive = pd.Series(np.random.uniform(1, 100, 1000), name="x")
        y_positive = pd.Series(np.random.uniform(1, 100, 1000), name="y")
        z_positive = pd.Series(np.random.uniform(1, 10, 1000), name="z")

        hist = Hist2D(
            x_positive, y_positive, z_positive, nbins=10, logx=True, logy=True
        )
        hist.set_axnorm("c")

        # Get normalized aggregation
        agg = hist.agg()

        # Check normalization works with log scale
        assert agg is not None
        assert not agg.isna().all(), "All values are NaN with log scale"

        # Check that values are properly normalized
        non_nan_values = agg.dropna()
        assert (non_nan_values >= 0).all(), "Found negative values with log scale"
        assert (non_nan_values <= 1.0001).all(), "Found values > 1 with log scale"

    def test_all_documented_normalizations(self):
        """Test that all documented normalization options work without error."""
        documented_options = [
            (None, "no normalization"),
            ("c", "column normalize"),
            ("r", "row normalize"),
            ("t", "total normalize"),
            ("d", "density normalize"),
            ("cd", "PDFs in each column"),
            ("rd", "PDFs in each row"),
        ]

        for option, description in documented_options:
            hist = Hist2D(self.x_data, self.y_data, self.z_data, nbins=10)
            hist.set_axnorm(option)

            # Should be able to get aggregation without error
            agg = hist.agg()
            assert (
                agg is not None
            ), f"Failed to get aggregation with axnorm={option} ({description})"

            # Should have at least some non-NaN values
            if option is not None:  # None means no normalization
                non_nan_count = agg.notna().sum()
                assert (
                    non_nan_count > 0
                ), f"No non-NaN values with axnorm={option} ({description})"

    def test_density_normalize_with_counts(self):
        """Test density normalize with count data (no z values).

        This should create a proper 2D probability density where integral = 1.
        """
        hist = Hist2D(self.x_data, self.y_data, nbins=10)
        hist.set_axnorm("d")

        # Get normalized aggregation
        agg = hist.agg()

        # Get bin widths for integration
        x_intervals = hist.intervals["x"]
        y_intervals = hist.intervals["y"]

        # Calculate dx and dy for each bin
        dx_values = pd.Series(
            [interval.length for interval in x_intervals], index=x_intervals
        )
        dy_values = pd.Series(
            [interval.length for interval in y_intervals], index=y_intervals
        )

        # Compute the integral
        agg_unstacked = agg.unstack("x")
        total_integral = 0
        for y_idx, y_interval in enumerate(agg_unstacked.index):
            for x_idx, x_interval in enumerate(agg_unstacked.columns):
                value = agg_unstacked.iloc[y_idx, x_idx]
                if not pd.isna(value):
                    dx = dx_values[x_interval]
                    dy = dy_values[y_interval]
                    total_integral += value * dx * dy

        # The integral should be close to 1
        assert np.isclose(
            total_integral, 1.0, atol=0.01
        ), f"Count density integral is {total_integral}, expected 1.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
