#!/usr/bin/env python
"""Tests for NaN-aware Gaussian filtering in solarwindpy.plotting.tools."""

import pytest
import numpy as np
from scipy.ndimage import gaussian_filter

from solarwindpy.plotting.tools import nan_gaussian_filter


class TestNanGaussianFilter:
    """Tests for nan_gaussian_filter function."""

    def test_matches_scipy_without_nans(self):
        """Without NaNs, should match scipy.ndimage.gaussian_filter.

        When no NaNs exist:
        - weights array is all 1.0s
        - gaussian_filter of constant array returns that constant
        - So filtered_weights is 1.0 everywhere
        - result = filtered_data / 1.0 = gaussian_filter(arr)
        """
        np.random.seed(42)
        arr = np.random.rand(10, 10)
        result = nan_gaussian_filter(arr, sigma=1)
        expected = gaussian_filter(arr, sigma=1)
        assert np.allclose(result, expected)

    def test_preserves_nan_locations(self):
        """NaN locations in input should remain NaN in output."""
        np.random.seed(42)
        arr = np.random.rand(10, 10)
        arr[3, 3] = np.nan
        arr[7, 2] = np.nan
        result = nan_gaussian_filter(arr, sigma=1)
        assert np.isnan(result[3, 3])
        assert np.isnan(result[7, 2])
        assert np.isnan(result).sum() == 2

    def test_no_nan_propagation(self):
        """Neighbors of NaN cells should remain valid."""
        np.random.seed(42)
        arr = np.random.rand(10, 10)
        arr[5, 5] = np.nan
        result = nan_gaussian_filter(arr, sigma=1)
        # All 8 neighbors should be valid
        for di in [-1, 0, 1]:
            for dj in [-1, 0, 1]:
                if di == 0 and dj == 0:
                    continue
                assert not np.isnan(result[5 + di, 5 + dj])

    def test_edge_nans(self):
        """NaNs at array edges should be handled correctly."""
        np.random.seed(42)
        arr = np.random.rand(10, 10)
        arr[0, 0] = np.nan
        arr[9, 9] = np.nan
        result = nan_gaussian_filter(arr, sigma=1)
        assert np.isnan(result[0, 0])
        assert np.isnan(result[9, 9])
        assert not np.isnan(result[5, 5])


if __name__ == "__main__":
    pytest.main([__file__])
