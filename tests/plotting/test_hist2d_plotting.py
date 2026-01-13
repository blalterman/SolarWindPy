#!/usr/bin/env python
"""Tests for Hist2D plotting methods.

Tests for:
- _prep_agg_for_plot: Data preparation helper for pcolormesh/contour plots
- plot_hist_with_contours: Combined pcolormesh + contour plotting method
"""

import pytest
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402


@pytest.fixture
def hist2d_instance():
    """Create a Hist2D instance for testing."""
    np.random.seed(42)
    x = pd.Series(np.random.randn(500), name="x")
    y = pd.Series(np.random.randn(500), name="y")
    return Hist2D(x, y, nbins=20, axnorm="t")


class TestPrepAggForPlot:
    """Tests for _prep_agg_for_plot method."""

    # --- Unit Tests (structure) ---

    def test_use_edges_returns_n_plus_1_points(self, hist2d_instance):
        """With use_edges=True, coordinates have n+1 points for n bins.

        pcolormesh requires bin edges (vertices), so for n bins we need n+1 edge points.
        """
        C, x, y = hist2d_instance._prep_agg_for_plot(use_edges=True)
        assert x.size == C.shape[1] + 1
        assert y.size == C.shape[0] + 1

    def test_use_centers_returns_n_points(self, hist2d_instance):
        """With use_edges=False, coordinates have n points for n bins.

        contour/contourf requires bin centers, so for n bins we need n center points.
        """
        C, x, y = hist2d_instance._prep_agg_for_plot(use_edges=False)
        assert x.size == C.shape[1]
        assert y.size == C.shape[0]

    def test_mask_invalid_returns_masked_array(self, hist2d_instance):
        """With mask_invalid=True, returns np.ma.MaskedArray."""
        C, x, y = hist2d_instance._prep_agg_for_plot(mask_invalid=True)
        assert isinstance(C, np.ma.MaskedArray)

    def test_no_mask_returns_ndarray(self, hist2d_instance):
        """With mask_invalid=False, returns regular ndarray."""
        C, x, y = hist2d_instance._prep_agg_for_plot(mask_invalid=False)
        assert isinstance(C, np.ndarray)
        assert not isinstance(C, np.ma.MaskedArray)

    # --- Integration Tests (values) ---

    def test_c_values_match_agg(self, hist2d_instance):
        """C array values should match agg().unstack().values after reindexing.

        _prep_agg_for_plot reindexes to ensure all bins are present, so we must
        apply the same reindexing to the expected values for comparison.
        """
        C, x, y = hist2d_instance._prep_agg_for_plot(use_edges=True, mask_invalid=False)
        # Apply same reindexing that _prep_agg_for_plot does
        agg = hist2d_instance.agg().unstack("x")
        agg = agg.reindex(columns=hist2d_instance.categoricals["x"])
        agg = agg.reindex(index=hist2d_instance.categoricals["y"])
        expected = agg.values
        # Handle potential reindexing by comparing non-NaN values
        np.testing.assert_array_equal(
            np.isnan(C),
            np.isnan(expected),
            err_msg="NaN locations should match",
        )
        valid_mask = ~np.isnan(C)
        np.testing.assert_allclose(
            C[valid_mask],
            expected[valid_mask],
            err_msg="Non-NaN values should match",
        )

    def test_edge_coords_match_edges(self, hist2d_instance):
        """With use_edges=True, coordinates should match self.edges."""
        C, x, y = hist2d_instance._prep_agg_for_plot(use_edges=True)
        expected_x = hist2d_instance.edges["x"]
        expected_y = hist2d_instance.edges["y"]
        np.testing.assert_allclose(x, expected_x)
        np.testing.assert_allclose(y, expected_y)

    def test_center_coords_match_intervals(self, hist2d_instance):
        """With use_edges=False, coordinates should match intervals.mid."""
        C, x, y = hist2d_instance._prep_agg_for_plot(use_edges=False)
        expected_x = hist2d_instance.intervals["x"].mid.values
        expected_y = hist2d_instance.intervals["y"].mid.values
        np.testing.assert_allclose(x, expected_x)
        np.testing.assert_allclose(y, expected_y)


class TestPlotHistWithContours:
    """Tests for plot_hist_with_contours method."""

    # --- Smoke Tests (execution) ---

    def test_returns_expected_tuple(self, hist2d_instance):
        """Returns (ax, cbar, qset, lbls) tuple."""
        ax, cbar, qset, lbls = hist2d_instance.plot_hist_with_contours()
        assert ax is not None
        assert cbar is not None
        assert qset is not None
        plt.close("all")

    def test_no_labels_returns_none(self, hist2d_instance):
        """With label_levels=False, lbls is None."""
        ax, cbar, qset, lbls = hist2d_instance.plot_hist_with_contours(
            label_levels=False
        )
        assert lbls is None
        plt.close("all")

    def test_contourf_parameter(self, hist2d_instance):
        """use_contourf parameter switches between contour and contourf."""
        ax1, _, qset1, _ = hist2d_instance.plot_hist_with_contours(use_contourf=True)
        ax2, _, qset2, _ = hist2d_instance.plot_hist_with_contours(use_contourf=False)
        # Both should work without error
        assert qset1 is not None
        assert qset2 is not None
        plt.close("all")

    # --- Integration Tests (correctness) ---

    def test_contour_levels_correct_for_axnorm_t(self, hist2d_instance):
        """Contour levels should match expected values for axnorm='t'."""
        ax, cbar, qset, lbls = hist2d_instance.plot_hist_with_contours()
        # For axnorm="t", default levels are [0.01, 0.1, 0.3, 0.7, 0.99]
        expected_levels = [0.01, 0.1, 0.3, 0.7, 0.99]
        np.testing.assert_allclose(
            qset.levels,
            expected_levels,
            err_msg="Contour levels should match expected for axnorm='t'",
        )
        plt.close("all")

    def test_colorbar_range_valid_for_normalized_data(self, hist2d_instance):
        """Colorbar range should be within [0, 1] for normalized data."""
        ax, cbar, qset, lbls = hist2d_instance.plot_hist_with_contours()
        # For axnorm="t" (total normalized), values should be in [0, 1]
        assert cbar.vmin >= 0, "Colorbar vmin should be >= 0"
        assert cbar.vmax <= 1, "Colorbar vmax should be <= 1"
        plt.close("all")

    def test_gaussian_filter_changes_contour_data(self, hist2d_instance):
        """Gaussian filtering should produce different contours than unfiltered."""
        # Get unfiltered contours
        ax1, _, qset1, _ = hist2d_instance.plot_hist_with_contours(
            gaussian_filter_std=0
        )
        unfiltered_data = qset1.allsegs

        # Get filtered contours
        ax2, _, qset2, _ = hist2d_instance.plot_hist_with_contours(
            gaussian_filter_std=2
        )
        filtered_data = qset2.allsegs

        # The contour paths should differ (filtering smooths the data)
        # Compare segment counts or shapes as a proxy for "different"
        differs = False
        for level_idx in range(min(len(unfiltered_data), len(filtered_data))):
            if len(unfiltered_data[level_idx]) != len(filtered_data[level_idx]):
                differs = True
                break
        assert differs or len(unfiltered_data) != len(
            filtered_data
        ), "Filtered contours should differ from unfiltered"
        plt.close("all")

    def test_pcolormesh_data_matches_prep_agg(self, hist2d_instance):
        """Pcolormesh data should match _prep_agg_for_plot output."""
        ax, cbar, qset, lbls = hist2d_instance.plot_hist_with_contours()

        # Get the pcolormesh (QuadMesh) from the axes
        quadmesh = [c for c in ax.collections if hasattr(c, "get_array")][0]
        plot_data = quadmesh.get_array()

        # Get expected data from _prep_agg_for_plot
        C_expected, _, _ = hist2d_instance._prep_agg_for_plot(use_edges=True)

        # Compare (flatten both for comparison, handling masked arrays)
        plot_flat = np.ma.filled(plot_data.flatten(), np.nan)
        expected_flat = np.ma.filled(C_expected.flatten(), np.nan)

        # Check NaN locations match
        np.testing.assert_array_equal(
            np.isnan(plot_flat),
            np.isnan(expected_flat),
            err_msg="NaN locations should match",
        )
        plt.close("all")

    def test_nan_aware_filter_works(self, hist2d_instance):
        """nan_aware_filter=True should run without error."""
        ax, cbar, qset, lbls = hist2d_instance.plot_hist_with_contours(
            gaussian_filter_std=1, nan_aware_filter=True
        )
        assert qset is not None
        plt.close("all")


class TestPlotContours:
    """Tests for plot_contours method."""

    def test_single_level_no_boundary_norm_error(self, hist2d_instance):
        """Single-level contours should not raise BoundaryNorm ValueError.

        BoundaryNorm requires at least 2 boundaries. When levels has only 1 element,
        plot_contours should skip BoundaryNorm creation and let matplotlib handle it.
        Note: cbar=False is required because matplotlib's colorbar also requires 2+ levels.

        Regression test for: ValueError: You must provide at least 2 boundaries
        """
        ax, lbls, mappable, qset = hist2d_instance.plot_contours(
            levels=[0.5], cbar=False
        )
        assert len(qset.levels) == 1
        assert qset.levels[0] == 0.5
        plt.close("all")

    def test_multiple_levels_preserved(self, hist2d_instance):
        """Multiple levels should be preserved in returned contour set."""
        levels = [0.3, 0.5, 0.7]
        ax, lbls, mappable, qset = hist2d_instance.plot_contours(levels=levels)
        assert len(qset.levels) == 3
        np.testing.assert_allclose(qset.levels, levels)
        plt.close("all")

    def test_use_contourf_true_returns_filled_contours(self, hist2d_instance):
        """use_contourf=True should return filled QuadContourSet."""
        ax, _, _, qset = hist2d_instance.plot_contours(use_contourf=True)
        assert qset.filled is True
        plt.close("all")

    def test_use_contourf_false_returns_line_contours(self, hist2d_instance):
        """use_contourf=False should return unfilled QuadContourSet."""
        ax, _, _, qset = hist2d_instance.plot_contours(use_contourf=False)
        assert qset.filled is False
        plt.close("all")

    def test_cbar_true_returns_colorbar(self, hist2d_instance):
        """With cbar=True, mappable should be a Colorbar instance."""
        ax, lbls, mappable, qset = hist2d_instance.plot_contours(cbar=True)
        assert isinstance(mappable, matplotlib.colorbar.Colorbar)
        plt.close("all")

    def test_cbar_false_returns_contourset(self, hist2d_instance):
        """With cbar=False, mappable should be the QuadContourSet."""
        ax, lbls, mappable, qset = hist2d_instance.plot_contours(cbar=False)
        assert isinstance(mappable, matplotlib.contour.QuadContourSet)
        plt.close("all")


if __name__ == "__main__":
    pytest.main([__file__])
