#!/usr/bin/env python
"""Tests for ``solarwindpy.plotting.tools.nan_gaussian_filter``.

The filter is normalized convolution (Knutsson & Westin 1993, "Normalized
and differential convolution", Proc. IEEE CVPR, pp. 515-523, as cited in the
function's docstring): smooth the data with NaNs zeroed, smooth a
validity mask the same way, divide, and restore the NaNs. Expected values come
from ``scipy.ndimage.gaussian_filter`` where no NaNs are present, from a
brute-force weighted mean built with numpy, and from a hand-computed case.
"""

import math

import numpy as np
import pytest
from scipy.ndimage import gaussian_filter

from solarwindpy.plotting.tools import nan_gaussian_filter


def _brute_force_normalized_convolution(array, sigma, truncate=4.0):
    """Weighted mean of the valid cells around each cell, zero padded.

    Independent of scipy: the Gaussian weights are built here from
    exp(-d**2 / (2 sigma**2)) out to scipy's kernel radius,
    int(truncate * sigma + 0.5). Normalization of the kernel cancels in the
    ratio, so it is omitted.
    """
    radius = int(truncate * sigma + 0.5)
    offsets = np.arange(-radius, radius + 1)
    kernel = np.exp(-(offsets**2) / (2.0 * sigma**2))

    valid = ~np.isnan(array)
    out = np.full(array.shape, np.nan)
    nrows, ncols = array.shape
    for i in range(nrows):
        for j in range(ncols):
            if not valid[i, j]:
                continue
            num = 0.0
            den = 0.0
            for di, wi in zip(offsets, kernel):
                for dj, wj in zip(offsets, kernel):
                    k, m = i + di, j + dj
                    if 0 <= k < nrows and 0 <= m < ncols and valid[k, m]:
                        num += wi * wj * array[k, m]
                        den += wi * wj
            out[i, j] = num / den
    return out


class TestNanGaussianFilter:
    """Normalized convolution: values, NaN handling, and kwargs passthrough."""

    def test_without_nans_equals_scipy_gaussian_filter(self):
        """With no NaNs the validity mask is all ones and filters to one.

        So the result is ``scipy.ndimage.gaussian_filter`` of the data.
        ON FAILURE: the code is wrong.
        """
        arr = np.random.default_rng(42).random((10, 12))
        result = nan_gaussian_filter(arr, sigma=1.5)
        expected = gaussian_filter(arr, sigma=1.5)
        # rel 1e-12: only float rounding in dividing by a mask that filters to ~1.
        np.testing.assert_allclose(result, expected, rtol=1e-12, atol=0)

    def test_hand_computed_neighbour_average_across_a_hole(self):
        """Row ``[1, nan, 2]``, sigma 1, zero padding.

        Cell 0 sees itself (weight e^0 = 1) and cell 2 (weight e^(-2^2/2) =
        e^-2); the vertical kernel factor cancels in the ratio. So
        result[0, 0] = (1 + 2 e^-2) / (1 + e^-2) and, by symmetry,
        result[0, 2] = (2 + e^-2) / (1 + e^-2).
        ON FAILURE: the code is wrong.
        """
        arr = np.array([[1.0, np.nan, 2.0]])
        result = nan_gaussian_filter(arr, sigma=1.0, mode="constant")
        w = math.exp(-2.0)
        # rel 1e-12: exact closed form, float rounding only.
        assert result[0, 0] == pytest.approx((1 + 2 * w) / (1 + w), rel=1e-12, abs=0)
        assert result[0, 2] == pytest.approx((2 + w) / (1 + w), rel=1e-12, abs=0)
        assert np.isnan(result[0, 1])

    def test_matches_brute_force_normalized_convolution(self):
        """Every valid cell is the Gaussian-weighted mean of its valid neighbours.

        Compared against a numpy brute force with zero padding
        (``mode="constant"``), which also shows kwargs reach scipy.
        ON FAILURE: the code is wrong.
        """
        rng = np.random.default_rng(7)
        arr = rng.random((7, 9))
        arr[rng.random(arr.shape) < 0.25] = np.nan
        result = nan_gaussian_filter(arr, sigma=1.3, mode="constant")
        expected = _brute_force_normalized_convolution(arr, sigma=1.3)
        # rel 1e-12: same sums in a different order, float rounding only.
        np.testing.assert_allclose(result, expected, rtol=1e-12, atol=0)

    def test_kwargs_change_the_result_as_scipy_predicts(self):
        """``truncate`` is forwarded: a radius-1 kernel changes the output.

        With truncate=1 and sigma=1 the kernel radius is int(1 + 0.5) = 1, which
        the brute force reproduces; the default radius 4 gives a different answer.
        ON FAILURE: the code is wrong.
        """
        rng = np.random.default_rng(11)
        arr = rng.random((6, 6))
        arr[2, 3] = np.nan
        narrow = nan_gaussian_filter(arr, sigma=1.0, mode="constant", truncate=1.0)
        expected = _brute_force_normalized_convolution(arr, sigma=1.0, truncate=1.0)
        # rel 1e-12: float rounding only.
        np.testing.assert_allclose(narrow, expected, rtol=1e-12, atol=0)
        wide = nan_gaussian_filter(arr, sigma=1.0, mode="constant")
        assert not np.allclose(narrow[~np.isnan(arr)], wide[~np.isnan(arr)])

    def test_constant_field_with_holes_stays_constant(self):
        """A weighted mean of equal values is that value, however many are missing.

        ``scipy.ndimage.gaussian_filter`` alone would spread NaN to every
        neighbour instead.
        ON FAILURE: the code is wrong.
        """
        arr = np.full((8, 8), 3.5)
        arr[[0, 3, 3, 7], [0, 3, 4, 7]] = np.nan
        result = nan_gaussian_filter(arr, sigma=2.0)
        valid = ~np.isnan(arr)
        # rel 1e-12: ratio of two sums of the same weights, float rounding only.
        np.testing.assert_allclose(result[valid], 3.5, rtol=1e-12, atol=0)

    def test_nans_are_preserved_and_nothing_else_becomes_nan(self):
        """The output is NaN exactly where the input is, including edges and corners.

        ON FAILURE: the code is wrong.
        """
        arr = np.random.default_rng(42).random((10, 10))
        holes = [(0, 0), (9, 9), (5, 5), (3, 7)]
        for ij in holes:
            arr[ij] = np.nan
        result = nan_gaussian_filter(arr, sigma=1.0)
        np.testing.assert_array_equal(np.isnan(result), np.isnan(arr))

    def test_input_array_is_not_modified(self):
        """The caller's array keeps its NaNs and values.

        ON FAILURE: the code is wrong.
        """
        arr = np.random.default_rng(3).random((5, 5))
        arr[1, 2] = np.nan
        before = arr.copy()
        nan_gaussian_filter(arr, sigma=1.0)
        np.testing.assert_array_equal(arr, before)

    def test_integer_array_is_filtered_like_its_float_copy(self):
        """An integer count grid smooths to the same values as its float copy.

        ON FAILURE: the code is wrong.
        """
        counts = np.array([[0, 10, 0], [0, 0, 5]])
        result = nan_gaussian_filter(counts, sigma=1.0)
        expected = nan_gaussian_filter(counts.astype(float), sigma=1.0)
        # rel 1e-12: identical computation on identical values.
        np.testing.assert_allclose(result, expected, rtol=1e-12, atol=0)
