#!/usr/bin/env python
"""Tests for Hist2D binning, aggregation, and plotting.

Expected values here are derived independently of ``hist2d.py``: either
constructed by the test (a grid whose per-bin population the test chose), or
computed with numpy/scipy from the same inputs, or required by an identity
(marginalisation, normalisation, round trip through a log axis).

A figure's *appearance* is not derivable and is not asserted anywhere in this
file. What is asserted about a plot is the data handed to matplotlib: the
values in the ``QuadMesh``, the coordinates of its cells, the vertices of the
edge lines. Those are the numbers the science depends on; the rendering is not.
"""

import pytest
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from scipy.signal import savgol_filter  # noqa: E402

from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402

PANDAS_3 = int(pd.__version__.split(".")[0]) >= 3

# `id_data_above_contour` seeds a float64 Series with NaN and then writes
# pd.Interval objects into it. pandas 2 silently widened the dtype to object;
# pandas 3 raises LossySetitemError instead. The behaviour under test is the
# same either way, so the tests below state it unconditionally and are marked
# expected-to-fail only where the library refuses the assignment.
#
# Strict, because an unexpected pass is the signal that the dtype has been
# fixed and the marker should go. That all three tests in the class do fail
# was measured on pandas 3.0.5, not assumed; note that no CI job currently
# runs pandas 3, so the first contributor to install it is the one who will
# see this marker do its work.
broken_on_pandas_3 = pytest.mark.xfail(
    PANDAS_3,
    strict=True,
    reason=(
        "id_data_above_contour assigns pd.Interval values into a float64 "
        "Series, which pandas 3 rejects (LossySetitemError). Verified on "
        "pandas 3.0.5. Remove this marker once the Series is built with an "
        "object or Categorical dtype."
    ),
)


@pytest.fixture
def hist2d_instance():
    """Create a Hist2D instance for testing."""
    np.random.seed(42)
    x = pd.Series(np.random.randn(500), name="x")
    y = pd.Series(np.random.randn(500), name="y")
    return Hist2D(x, y, nbins=20, axnorm="t")


# ---------------------------------------------------------------------------
# A grid whose contents the test chooses, so every expectation below is an
# input rather than a recorded output.
#
# Both edge arrays are exact at 5 decimal places, which is the precision at
# which `calc_bins_intervals` stores interval endpoints; choosing them that way
# keeps rounding out of the comparisons.
# ---------------------------------------------------------------------------

XEDGES = np.array([0.0, 0.25, 0.50, 0.75, 1.00])  # 4 bins in x
YEDGES = np.array([0.0, 0.20, 0.40, 0.60, 0.80, 1.00])  # 5 bins in y

# Rows index y, columns index x -- the orientation `agg().unstack("x")` uses.
# The shape is deliberately non-square so a transposition cannot pass.
# Zeros leave bins empty, so the first/last occupied bin per column differs
# between columns and `get_border` has something non-trivial to find.
KNOWN_COUNTS = np.array(
    [
        [3, 0, 2, 5],
        [1, 4, 0, 2],
        [0, 2, 6, 1],
        [4, 1, 3, 0],
        [2, 5, 0, 0],
    ]
)


def _bin_centers(edges):
    return 0.5 * (edges[:-1] + edges[1:])


def _points_from_counts(counts, xedges, yedges):
    """Place ``counts[i, j]`` points at the center of bin (j, i)."""
    xc = _bin_centers(xedges)
    yc = _bin_centers(yedges)
    xs = []
    ys = []
    for i in range(counts.shape[0]):
        for j in range(counts.shape[1]):
            xs.extend([xc[j]] * counts[i, j])
            ys.extend([yc[i]] * counts[i, j])
    return pd.Series(xs, name="x"), pd.Series(ys, name="y")


@pytest.fixture
def known_counts():
    """The count matrix the ``known_hist`` fixture was built to reproduce."""
    return KNOWN_COUNTS.astype(float)


@pytest.fixture
def known_hist():
    """A Hist2D whose per-bin counts are ``KNOWN_COUNTS`` by construction."""
    x, y = _points_from_counts(KNOWN_COUNTS, XEDGES, YEDGES)
    return Hist2D(x, y, nbins=[XEDGES, YEDGES])


@pytest.fixture
def z_valued_hist():
    """A Hist2D whose per-bin count and per-bin mean disagree by construction.

    Every point in a bin carries the same z, so the bin's mean is exactly that
    value. Setting it to ``7 - count`` makes the bins with many observations
    the bins with a small mean, so a threshold on the count and the same
    threshold on the value select different sets. Returns the histogram, the
    count matrix, and the mean matrix (NaN where a bin is empty).
    """
    counts = KNOWN_COUNTS
    z_means = np.where(counts == 0, np.nan, 7.0 - counts)

    xc = _bin_centers(XEDGES)
    yc = _bin_centers(YEDGES)
    xs, ys, zs = [], [], []
    for i in range(counts.shape[0]):
        for j in range(counts.shape[1]):
            xs.extend([xc[j]] * counts[i, j])
            ys.extend([yc[i]] * counts[i, j])
            zs.extend([z_means[i, j]] * counts[i, j])

    hist = Hist2D(
        pd.Series(xs, name="x"),
        pd.Series(ys, name="y"),
        pd.Series(zs, name="z"),
        nbins=[XEDGES, YEDGES],
    )
    return hist, counts, z_means


@pytest.fixture
def smoothable_hist():
    """A Hist2D wide enough in x that a savgol window of 5 is meaningful.

    61 x-bins is not arbitrary: `_plot_one_edge` defaults `window_length` to
    floor(n / 10), decremented to the next odd number, and defaults
    `polyorder` to 3. Fewer columns make the default window too narrow for that
    polynomial order and scipy refuses outright, which would mask the parameter
    mix-up this fixture exists to expose.
    """
    xedges = np.round(np.linspace(0.0, 1.0, 62), 5)
    yedges = np.round(np.linspace(0.0, 1.0, 9), 5)
    ny, nx = len(yedges) - 1, len(xedges) - 1

    # The occupied band moves up and down with x, so neither border is flat.
    # A flat border is invariant under savgol at any polynomial order, which
    # would make the smoothing comparisons vacuous.
    counts = np.zeros((ny, nx), dtype=int)
    for j in range(nx):
        lo = j % 3
        hi = ny - 1 - (j % 4)
        for i in range(lo, hi + 1):
            counts[i, j] = 1 + ((3 * i + 7 * j) % 5)

    x, y = _points_from_counts(counts, xedges, yedges)
    return Hist2D(x, y, nbins=[xedges, yedges])


def _expected_grid(counts):
    """``counts`` with empty bins as NaN, matching an unstacked aggregation."""
    expected = counts.astype(float)
    return np.where(expected == 0, np.nan, expected)


def _quadmesh(ax):
    meshes = [
        c for c in ax.collections if isinstance(c, matplotlib.collections.QuadMesh)
    ]
    assert len(meshes) == 1, f"expected exactly one QuadMesh, found {len(meshes)}"
    return meshes[0]


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


class TestBinContract:
    """What `calc_bins_intervals` promises about the bins it produces.

    The docstring names `np.histogram_bin_edges` as the source of the edges for
    an integer/str `nbins`, so numpy supplies the expectation directly.
    """

    @pytest.mark.parametrize("nbins", [5, 12, 33])
    def test_integer_nbins_matches_numpy_histogram_bin_edges(self, nbins):
        """Edges equal `np.histogram_bin_edges`, rounded to the stored precision.

        ON FAILURE: the code is wrong, unless the docstring's promise to use
        `np.histogram_bin_edges` was deliberately withdrawn.
        """
        rng = np.random.default_rng(11)
        x = pd.Series(rng.normal(0.0, 3.0, 400), name="x")
        y = pd.Series(rng.normal(5.0, 1.0, 400), name="y")

        h = Hist2D(x, y, nbins=nbins)

        for name, data in (("x", x), ("y", y)):
            expected = np.histogram_bin_edges(data.values, nbins).round(5)
            np.testing.assert_allclose(h.edges[name].values, expected)
            assert h.edges[name].size == nbins + 1

    def test_explicit_edges_are_used_verbatim(self):
        """Edges handed in per axis come back unchanged.

        ON FAILURE: the code is wrong -- explicit bins must not be recomputed.
        """
        h = Hist2D(
            *_points_from_counts(KNOWN_COUNTS, XEDGES, YEDGES), nbins=[XEDGES, YEDGES]
        )
        np.testing.assert_allclose(h.edges["x"].values, XEDGES)
        np.testing.assert_allclose(h.edges["y"].values, YEDGES)

    @pytest.mark.parametrize("nbins", [4, 17])
    def test_edges_are_strictly_increasing(self, nbins):
        """Bin edges increase; no zero-width or inverted bin.

        ON FAILURE: the code is wrong.
        """
        rng = np.random.default_rng(12)
        h = Hist2D(
            pd.Series(rng.normal(size=300)),
            pd.Series(rng.normal(size=300)),
            nbins=nbins,
        )
        for name in ("x", "y"):
            edges = h.edges[name].values
            assert np.all(np.diff(edges) > 0), f"{name} edges are not increasing"

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Auto-computed edges are rounded to `precision` (default 5) after "
            "np.histogram_bin_edges has set them to the data extrema, so both "
            "outer edges can move *inside* the data range and orphan the "
            "extreme observations. Replaces nothing -- this path had no test. "
            "Remove the xfail when the outer edges are rounded outwards."
        ),
    )
    @pytest.mark.parametrize("nbins", [4, 17])
    def test_edges_span_the_data(self, nbins):
        """Every observation falls inside the outer edges.

        ON FAILURE (i.e. an unexpected pass): the rounding has been made
        outward-only; drop the xfail marker.
        """
        rng = np.random.default_rng(13)
        x = pd.Series(rng.normal(size=300))
        y = pd.Series(rng.normal(size=300))
        h = Hist2D(x, y, nbins=nbins)
        for name, data in (("x", x), ("y", y)):
            edges = h.edges[name].values
            assert edges[0] <= data.min()
            assert data.max() <= edges[-1]

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Auto-binned data loses its extreme observations. The bins are "
            "right-closed, so the leftmost edge -- which np.histogram_bin_edges "
            "sets to exactly data.min() -- belongs to no bin; numpy avoids the "
            "mirror-image problem by closing its last bin on both ends. "
            "Precision rounding of the outer edges compounds it. Replaces "
            "nothing -- this path had no test. Remove the xfail when the outer "
            "bins are closed on both ends."
        ),
    )
    def test_auto_bins_retain_every_observation(self):
        """A histogram partitions its data: the counts must sum to N.

        ON FAILURE (i.e. an unexpected pass): the outer bins now hold their
        endpoints; drop the xfail marker.
        """
        rng = np.random.default_rng(13)
        x = pd.Series(rng.normal(size=300))
        y = pd.Series(rng.normal(size=300))
        h = Hist2D(x, y, nbins=4)
        assert h.agg().sum() == x.size

    def test_binning_is_deterministic(self):
        """The same data binned twice gives the same edges.

        ON FAILURE: the code is wrong -- results would not be reproducible.
        """
        rng = np.random.default_rng(14)
        x = pd.Series(rng.normal(size=300))
        y = pd.Series(rng.normal(size=300))
        first = Hist2D(x, y, nbins=9)
        second = Hist2D(x, y, nbins=9)
        for name in ("x", "y"):
            np.testing.assert_array_equal(
                first.edges[name].values, second.edges[name].values
            )

    def test_intervals_tile_the_edges_without_gaps(self):
        """Adjacent intervals share an endpoint and are right-closed.

        Right-closed matters: it decides which bin a point sitting exactly on an
        edge lands in, and every independently computed expectation in this file
        depends on that convention.

        ON FAILURE: the code is wrong.
        """
        h = Hist2D(
            *_points_from_counts(KNOWN_COUNTS, XEDGES, YEDGES), nbins=[XEDGES, YEDGES]
        )
        for name, edges in (("x", XEDGES), ("y", YEDGES)):
            intervals = h.intervals[name]
            assert intervals.closed == "right"
            np.testing.assert_allclose(intervals.left.values, edges[:-1])
            np.testing.assert_allclose(intervals.right.values, edges[1:])

    def test_nbins_may_be_specified_per_axis(self):
        """A two-element `nbins` gives x and y their own bin counts.

        ON FAILURE: the code is wrong.
        """
        rng = np.random.default_rng(15)
        h = Hist2D(
            pd.Series(rng.normal(size=400)),
            pd.Series(rng.normal(size=400)),
            nbins=[6, 13],
        )
        assert h.edges["x"].size == 7
        assert h.edges["y"].size == 14


class TestAggregatedValues:
    """The aggregation reproduces a grid the test populated itself."""

    def test_axes_are_reported_in_increasing_bin_order(self, known_hist):
        """Unstacked rows/columns are the y/x bins, ascending.

        Every value comparison below indexes positionally, so the ordering is
        the premise they all rest on.

        ON FAILURE: the code is wrong; the grid would be scrambled relative to
        its axes and every plot built from it mislabelled.
        """
        grid = known_hist.agg().unstack("x")
        np.testing.assert_allclose([c.left for c in grid.columns], XEDGES[:-1])
        np.testing.assert_allclose([c.right for c in grid.columns], XEDGES[1:])
        np.testing.assert_allclose([r.left for r in grid.index], YEDGES[:-1])
        np.testing.assert_allclose([r.right for r in grid.index], YEDGES[1:])

    def test_counts_reproduce_the_constructed_grid(self, known_hist, known_counts):
        """Counts equal the population the fixture placed in each bin.

        ON FAILURE: the code is wrong.
        """
        grid = known_hist.agg().unstack("x")
        np.testing.assert_allclose(grid.values, _expected_grid(known_counts))

    def test_counts_conserve_the_observations(self, known_hist, known_counts):
        """Every observation is counted exactly once.

        ON FAILURE: the code is wrong -- data is being dropped or double
        counted.
        """
        assert known_hist.agg().sum() == known_counts.sum()

    def test_mean_aggregation_matches_numpy(self):
        """Per-bin mean equals `np.mean` over the points in that bin.

        ON FAILURE: the code is wrong.
        """
        x, y = _points_from_counts(KNOWN_COUNTS, XEDGES, YEDGES)
        rng = np.random.default_rng(16)
        z = pd.Series(rng.uniform(0.0, 10.0, x.size), name="z")

        h = Hist2D(x, y, z, nbins=[XEDGES, YEDGES])
        grid = h.agg(fcn="mean").unstack("x")

        for i, ylo, yhi in zip(range(len(YEDGES) - 1), YEDGES[:-1], YEDGES[1:]):
            for j, xlo, xhi in zip(range(len(XEDGES) - 1), XEDGES[:-1], XEDGES[1:]):
                inside = (xlo < x) & (x <= xhi) & (ylo < y) & (y <= yhi)
                if not inside.any():
                    continue
                np.testing.assert_allclose(
                    grid.iloc[i, j], np.mean(z.values[inside.values])
                )

    def test_std_aggregation_matches_numpy(self):
        """Per-bin standard deviation equals `np.std(..., ddof=1)`.

        ddof=1 is pandas' documented default for `Series.std`.

        ON FAILURE: the code is wrong.
        """
        counts = np.full_like(KNOWN_COUNTS, 4)
        x, y = _points_from_counts(counts, XEDGES, YEDGES)
        rng = np.random.default_rng(17)
        z = pd.Series(rng.uniform(0.0, 10.0, x.size), name="z")

        h = Hist2D(x, y, z, nbins=[XEDGES, YEDGES])
        grid = h.agg(fcn="std").unstack("x")

        for i, ylo, yhi in zip(range(len(YEDGES) - 1), YEDGES[:-1], YEDGES[1:]):
            for j, xlo, xhi in zip(range(len(XEDGES) - 1), XEDGES[:-1], XEDGES[1:]):
                inside = (xlo < x) & (x <= xhi) & (ylo < y) & (y <= yhi)
                np.testing.assert_allclose(
                    grid.iloc[i, j], np.std(z.values[inside.values], ddof=1)
                )

    def test_right_closed_convention_places_edge_points(self):
        """A point sitting on an interior edge falls in the lower bin.

        This is the direct consequence of `closed="right"`: bin (a, b] contains
        b, not a.

        ON FAILURE: the code is wrong, or the closure convention changed -- in
        which case the constructed expectations elsewhere in this file need
        rederiving, not silencing.
        """
        x = pd.Series([0.25, 0.25, 0.25])
        y = pd.Series([0.2, 0.2, 0.2])
        h = Hist2D(x, y, nbins=[XEDGES, YEDGES])
        grid = h.agg().unstack("x")

        assert grid.columns[0].right == pytest.approx(0.25)
        assert grid.index[0].right == pytest.approx(0.2)
        assert grid.iloc[0, 0] == 3


class TestMakePlot:
    """What `make_plot` hands to `pcolormesh`, not what the figure looks like."""

    def test_mesh_values_reproduce_the_constructed_grid(self, known_hist, known_counts):
        """The QuadMesh carries the counts the fixture placed in each bin.

        ON FAILURE: the code is wrong -- the figure would show numbers that are
        not the data.
        """
        ax, _ = known_hist.make_plot()
        values = np.ma.filled(_quadmesh(ax).get_array().astype(float), np.nan)
        np.testing.assert_allclose(
            values.reshape(len(YEDGES) - 1, len(XEDGES) - 1),
            _expected_grid(known_counts),
        )
        plt.close("all")

    def test_mesh_coordinates_are_the_bin_edges(self, known_hist):
        """Cell corners sit on the bin edges that were requested.

        ON FAILURE: the code is wrong -- the grid would be drawn at the wrong
        coordinates.
        """
        ax, _ = known_hist.make_plot()
        coords = _quadmesh(ax).get_coordinates()
        np.testing.assert_allclose(coords[0, :, 0], XEDGES)
        np.testing.assert_allclose(coords[:, 0, 1], YEDGES)
        plt.close("all")

    def test_log_axes_round_trip_to_the_original_coordinates(self, known_counts):
        """With logx/logy, the mesh is drawn at the linear edges supplied.

        Hist2D stores log10 of the data and re-exponentiates for plotting. The
        composition of those two steps is the identity, so the plotted edges
        must be the edges the caller passed in.

        ON FAILURE: the code is wrong.
        """
        xedges = np.array([1.0, 10.0, 100.0, 1000.0])
        yedges = np.array([1.0, 100.0, 10000.0])
        counts = np.array([[2, 3, 1], [4, 1, 5]])
        x, y = _points_from_counts(counts, np.log10(xedges), np.log10(yedges))

        h = Hist2D(
            10.0**x,
            10.0**y,
            logx=True,
            logy=True,
            nbins=[np.log10(xedges), np.log10(yedges)],
        )
        ax, _ = h.make_plot()
        coords = _quadmesh(ax).get_coordinates()

        np.testing.assert_allclose(coords[0, :, 0], xedges)
        np.testing.assert_allclose(coords[:, 0, 1], yedges)
        plt.close("all")

    def test_returns_colorbar_when_requested(self, known_hist):
        """`cbar=True` returns the Colorbar, per the documented return value.

        ON FAILURE: the code is wrong, or the documented return contract
        changed.
        """
        ax, returned = known_hist.make_plot(cbar=True)
        assert isinstance(returned, matplotlib.colorbar.Colorbar)
        plt.close("all")

    def test_returns_the_mappable_when_no_colorbar(self, known_hist):
        """`cbar=False` returns the QuadMesh, per the documented return value.

        ON FAILURE: the code is wrong, or the documented return contract
        changed.
        """
        ax, returned = known_hist.make_plot(cbar=False)
        assert isinstance(returned, matplotlib.collections.QuadMesh)
        plt.close("all")

    def test_draws_on_the_axes_it_is_given(self, known_hist):
        """A supplied Axes is used rather than a fresh one.

        ON FAILURE: the code is wrong -- composed figures would silently lose
        panels.
        """
        fig, ax = plt.subplots()
        returned, _ = known_hist.make_plot(ax=ax, cbar=False)
        assert returned is ax
        assert len(ax.collections) == 1
        plt.close("all")

    def test_alpha_decreases_as_the_spread_increases(self):
        """`alpha_fcn` makes the least-scattered bin the most opaque.

        The stated intent is "smallest STD is most opaque". Four bins are given
        z-samples of strictly increasing standard deviation, so the opacity must
        be strictly decreasing across them in row-major order.

        ON FAILURE: the code is wrong.
        """
        xedges = np.array([0.0, 0.5, 1.0])
        yedges = np.array([0.0, 0.5, 1.0])
        # z-samples chosen so std is 0, 1, 2, 3 for bins (y0,x0) (y0,x1)
        # (y1,x0) (y1,x1) -- strictly increasing in row-major order.
        samples = {
            (0, 0): [1.0, 1.0, 1.0],
            (0, 1): [0.0, 1.0, 2.0],
            (1, 0): [0.0, 2.0, 4.0],
            (1, 1): [0.0, 3.0, 6.0],
        }
        xc = _bin_centers(xedges)
        yc = _bin_centers(yedges)
        xs, ys, zs = [], [], []
        for (i, j), zz in samples.items():
            xs.extend([xc[j]] * len(zz))
            ys.extend([yc[i]] * len(zz))
            zs.extend(zz)

        expected_std = [
            np.std(samples[k], ddof=1) for k in [(0, 0), (0, 1), (1, 0), (1, 1)]
        ]
        assert np.all(np.diff(expected_std) > 0), "fixture premise: std increases"

        h = Hist2D(pd.Series(xs), pd.Series(ys), pd.Series(zs), nbins=[xedges, yedges])
        ax, _ = h.make_plot(alpha_fcn="std", cbar=False)
        alpha = _quadmesh(ax).get_facecolors()[:, 3]

        assert alpha.min() >= 0.0 and alpha.max() <= 1.0
        assert np.all(
            np.diff(alpha) < 0
        ), f"opacity not decreasing with spread: {alpha}"
        plt.close("all")


class TestLimitColorNorm:
    """`limit_color_norm` clips the colour range to the bulk of the z-values."""

    def test_clips_to_quantiles_of_the_z_data(self):
        """The limits are quantiles of z: inside the data range and ordered.

        The exact quantiles are a seam -- see
        `test_limit_color_norm_quantiles_are_undetermined` below -- so only the
        bounding property is asserted here.

        ON FAILURE: the code is wrong; a colour limit outside the data range is
        meaningless.
        """
        rng = np.random.default_rng(18)
        x, y = _points_from_counts(np.full_like(KNOWN_COUNTS, 4), XEDGES, YEDGES)
        z = pd.Series(rng.uniform(0.0, 10.0, x.size), name="z")
        h = Hist2D(x, y, z, nbins=[XEDGES, YEDGES])

        norm = matplotlib.colors.Normalize()
        h._limit_color_norm(norm)

        assert z.min() <= norm.vmin < norm.vmax <= z.max()
        assert norm.clip is True

    def test_is_a_no_op_for_bounded_normalisations(self):
        """Column/row normalised data already spans [0, 1] and is left alone.

        The code says so in as many words: "Don't limit us to (1%, 99%)
        interval."

        ON FAILURE: the code is wrong -- clipping an already-bounded scale
        would hide the column maxima that define it.
        """
        rng = np.random.default_rng(19)
        x, y = _points_from_counts(np.full_like(KNOWN_COUNTS, 4), XEDGES, YEDGES)
        z = pd.Series(rng.uniform(0.0, 10.0, x.size), name="z")

        for axnorm in ("c", "r"):
            h = Hist2D(x, y, z, nbins=[XEDGES, YEDGES], axnorm=axnorm)
            norm = matplotlib.colors.Normalize()
            h._limit_color_norm(norm)
            assert norm.vmin is None
            assert norm.vmax is None
            assert norm.clip is False

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "make_plot(limit_color_norm=True) raises AttributeError when axnorm "
            "is None, because no default norm is built and None has no .vmin. "
            "Replaces nothing -- this path had no test. Remove the xfail when "
            "the guard lands."
        ),
    )
    def test_limit_color_norm_works_without_a_normalisation(self, known_hist):
        """`limit_color_norm=True` is documented for any Hist2D, axnorm or not.

        ON FAILURE (i.e. an unexpected pass): the guard has landed; drop the
        xfail marker.
        """
        known_hist.make_plot(limit_color_norm=True, cbar=False)
        plt.close("all")


class TestAggregationLimits:
    """`set_alim` and `set_clim` filter the grid after and before aggregating."""

    def test_alim_keeps_exactly_the_bins_inside_the_range(self, known_hist):
        """After `set_alim(lo, hi)`, a bin survives iff its value is in [lo, hi].

        The unfiltered grid supplies the expectation, so this is a round trip
        rather than a recorded set of survivors.

        ON FAILURE: the code is wrong.
        """
        unfiltered = known_hist.agg()
        lo, hi = 2.0, 4.0

        known_hist.set_alim(lo, hi)
        filtered = known_hist.agg()

        expected_kept = unfiltered.between(lo, hi) & unfiltered.notna()
        np.testing.assert_array_equal(filtered.notna().values, expected_kept.values)
        np.testing.assert_allclose(
            filtered.dropna().values, unfiltered[expected_kept].values
        )

    def test_alim_lower_bound_alone_is_one_sided(self, known_hist):
        """`set_alim(lo)` drops bins below `lo` and keeps everything above.

        ON FAILURE: the code is wrong.
        """
        unfiltered = known_hist.agg()
        known_hist.set_alim(3.0, None)
        filtered = known_hist.agg()
        np.testing.assert_array_equal(
            filtered.notna().values, (unfiltered >= 3.0).values
        )

    def test_clim_filters_on_the_population_not_the_value(self, z_valued_hist):
        """`set_clim` thresholds on the bin count, whatever the aggregate is.

        The z-values are assigned so each bin's mean is 7 minus its count,
        which makes "count >= 3" and "mean >= 3" pick out different bins. On a
        count-only histogram the aggregate *is* the count and the two limits
        are indistinguishable, so this has to be checked with z present.

        ON FAILURE: the code is wrong -- it is thresholding on the aggregated
        value rather than on how many observations produced it.
        """
        hist, counts, _ = z_valued_hist
        hist.set_clim(3, None)

        filtered = hist.agg().unstack("x")
        np.testing.assert_array_equal(filtered.notna().values, counts >= 3)

    def test_clim_and_alim_are_different_filters(self, z_valued_hist):
        """The count limit and the value limit select different bins here.

        This is the premise the test above rests on: without it, that test
        could pass on an implementation that confused the two.

        ON FAILURE: the fixture no longer separates the two filters, so the
        test above has stopped constraining anything -- fix the fixture, not
        this assertion.
        """
        hist, counts, z_means = z_valued_hist

        hist.set_clim(3, None)
        by_count = hist.agg().notna()

        hist.set_clim(None, None)
        hist.set_alim(3.0, None)
        by_value = hist.agg().notna()

        assert not by_count.equals(by_value)
        # Bins that never appear in the aggregation unstack to NaN; they are
        # simply "not selected".
        np.testing.assert_array_equal(
            by_count.unstack("x").fillna(False).values.astype(bool), counts >= 3
        )
        np.testing.assert_array_equal(
            by_value.unstack("x").fillna(False).values.astype(bool),
            np.nan_to_num(z_means, nan=0.0) >= 3.0,
        )


class TestGetBorder:
    """The top and bottom occupied bin in each column."""

    def test_border_is_the_extreme_occupied_bin_per_column(
        self, known_hist, known_counts
    ):
        """Top/bottom name the last/first populated y-bin of each x-column.

        Both the occupancy and the contents come from the fixture's count
        matrix, so the whole expectation is constructed.

        ON FAILURE: the code is wrong.
        """
        border = known_hist.get_border()
        counts = known_counts

        for j in range(counts.shape[1]):
            occupied = np.flatnonzero(counts[:, j] > 0)
            xiv = pd.Interval(XEDGES[j], XEDGES[j + 1], closed="right")

            top_i = occupied[-1]
            bot_i = occupied[0]
            top_key = (
                pd.Interval(YEDGES[top_i], YEDGES[top_i + 1], closed="right"),
                xiv,
            )
            bot_key = (
                pd.Interval(YEDGES[bot_i], YEDGES[bot_i + 1], closed="right"),
                xiv,
            )

            assert border.top[top_key] == counts[top_i, j]
            assert border.bottom[bot_key] == counts[bot_i, j]

    def test_border_index_is_named_y_then_x(self, known_hist):
        """The border index levels are labelled, so callers can group on them.

        ON FAILURE: the code is wrong.
        """
        border = known_hist.get_border()
        assert border.top.index.names == ["y", "x"]
        assert border.bottom.index.names == ["y", "x"]


class TestPlotEdges:
    """The vertices `plot_edges` sends to `ax.plot`."""

    def test_unsmoothed_edges_trace_the_border_bin_centers(
        self, known_hist, known_counts
    ):
        """Without smoothing the line passes through the border bin centers.

        ON FAILURE: the code is wrong.
        """
        counts = known_counts
        xc = _bin_centers(XEDGES)
        yc = _bin_centers(YEDGES)
        expected_x = xc
        expected_top = np.array(
            [yc[np.flatnonzero(counts[:, j] > 0)[-1]] for j in range(counts.shape[1])]
        )
        expected_bottom = np.array(
            [yc[np.flatnonzero(counts[:, j] > 0)[0]] for j in range(counts.shape[1])]
        )

        fig, ax = plt.subplots()
        (top_line,), (bottom_line,) = known_hist.plot_edges(ax, smooth=False)

        np.testing.assert_allclose(np.asarray(top_line.get_xdata(), float), expected_x)
        np.testing.assert_allclose(
            np.asarray(top_line.get_ydata(), float), expected_top
        )
        np.testing.assert_allclose(
            np.asarray(bottom_line.get_xdata(), float), expected_x
        )
        np.testing.assert_allclose(
            np.asarray(bottom_line.get_ydata(), float), expected_bottom
        )
        plt.close("all")

    def test_limits_drop_vertices_outside_them(self, known_hist):
        """`xlim`/`ylim` keep only vertices inside the closed range.

        ON FAILURE: the code is wrong.
        """
        fig, ax = plt.subplots()
        (top_line,), _ = known_hist.plot_edges(
            ax, smooth=False, xlim=(0.3, 0.8), ylim=(None, None)
        )
        kept = np.asarray(top_line.get_xdata(), float)
        assert kept.size > 0
        assert np.all((0.3 <= kept) & (kept <= 0.8))
        np.testing.assert_allclose(kept, _bin_centers(XEDGES)[1:3])
        plt.close("all")

    def test_log_axes_place_the_edges_at_linear_coordinates(self):
        """On log axes the edge vertices come back in the original units.

        Hist2D works in log10 internally and re-exponentiates for plotting, so
        the vertices must be the geometric centers of the decade bins the
        caller supplied -- a value numpy computes here directly.

        ON FAILURE: the code is wrong.
        """
        xedges = np.array([1.0, 10.0, 100.0, 1000.0])
        yedges = np.array([1.0, 100.0, 10000.0])
        counts = np.array([[2, 3, 1], [4, 1, 5]])
        log_x, log_y = np.log10(xedges), np.log10(yedges)
        x, y = _points_from_counts(counts, log_x, log_y)

        h = Hist2D(10.0**x, 10.0**y, logx=True, logy=True, nbins=[log_x, log_y])

        fig, ax = plt.subplots()
        (top_line,), _ = h.plot_edges(ax, smooth=False)

        np.testing.assert_allclose(
            np.asarray(top_line.get_xdata(), float),
            10.0 ** _bin_centers(log_x),
            rtol=1e-10,
        )
        # Every column of `counts` is populated in the upper y-bin.
        np.testing.assert_allclose(
            np.asarray(top_line.get_ydata(), float),
            np.full(len(xedges) - 1, 10.0 ** _bin_centers(log_y)[-1]),
            rtol=1e-10,
        )
        plt.close("all")

    def test_smoothing_applies_savitzky_golay(self, smoothable_hist):
        """With `smooth=True` the y-vertices are the savgol filter of the raw ones.

        scipy computes the expectation from the unsmoothed line, so nothing is
        captured from hist2d.

        Only the top edge is checked here; the bottom edge is the subject of
        `test_both_edges_get_the_smoothing_the_caller_asked_for` below.

        ON FAILURE: the code is wrong.
        """
        fig, ax = plt.subplots()
        (raw,), _ = smoothable_hist.plot_edges(ax, smooth=False)
        (smoothed,), _ = smoothable_hist.plot_edges(
            ax, smooth=True, sg_kwargs=dict(window_length=5, polyorder=2)
        )

        expected = savgol_filter(np.asarray(raw.get_ydata(), float), 5, 2)
        np.testing.assert_allclose(
            np.asarray(smoothed.get_ydata(), float), expected, rtol=1e-10
        )
        plt.close("all")

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "plot_edges hands the *same* sg_kwargs dict to both _plot_one_edge "
            "calls, and _plot_one_edge pops window_length/polyorder out of it. "
            "The top edge consumes the caller's parameters and the bottom edge "
            "silently falls back to window_length=floor(n/10) (5 here) and "
            "polyorder=3. No exception is raised: the bottom edge is simply "
            "smoothed differently from the top, and the assertion below is "
            "what catches it. Replaces nothing -- this path had no test. "
            "Remove the xfail once sg_kwargs is copied per edge."
        ),
    )
    def test_both_edges_get_the_smoothing_the_caller_asked_for(self, smoothable_hist):
        """Top and bottom must be smoothed with the same requested parameters.

        Two edges of one distribution smoothed on different window lengths are
        not comparable to each other.

        ON FAILURE (i.e. an unexpected pass): sg_kwargs is no longer shared;
        drop the xfail marker.
        """
        # Both parameters differ from the defaults the bottom edge falls back
        # to (window_length 5, polyorder 3), so the discrepancy is wide rather
        # than a few points near the ends.
        fig, ax = plt.subplots()
        _, (raw_bottom,) = smoothable_hist.plot_edges(ax, smooth=False)
        _, (smoothed_bottom,) = smoothable_hist.plot_edges(
            ax, smooth=True, sg_kwargs=dict(window_length=21, polyorder=1)
        )

        expected = savgol_filter(np.asarray(raw_bottom.get_ydata(), float), 21, 1)
        np.testing.assert_allclose(
            np.asarray(smoothed_bottom.get_ydata(), float), expected, rtol=1e-10
        )
        plt.close("all")


class TestProject1D:
    """Projecting a 2D histogram is marginalisation, and must conserve counts."""

    def test_x_projection_is_the_column_sum(self, known_hist, known_counts):
        """Summing the 2D grid over y gives the 1D x histogram.

        ON FAILURE: the code is wrong. This is the defining property of a
        marginal distribution, not a convention.
        """
        projected = known_hist.project_1d("x", project_counts=True).agg()
        np.testing.assert_allclose(projected.values, known_counts.sum(axis=0))

    def test_y_projection_is_the_row_sum(self, known_hist, known_counts):
        """Summing the 2D grid over x gives the 1D y histogram.

        ON FAILURE: the code is wrong.
        """
        projected = known_hist.project_1d("y", project_counts=True).agg()
        np.testing.assert_allclose(projected.values, known_counts.sum(axis=1))

    @pytest.mark.parametrize("axis", ["x", "y"])
    def test_projection_reuses_the_parent_bin_edges(self, known_hist, axis):
        """The 1D histogram bins on the same edges as the 2D one.

        ON FAILURE: the code is wrong -- a marginal on different bins cannot be
        compared with the grid it came from.
        """
        projected = known_hist.project_1d(axis, project_counts=True)
        np.testing.assert_allclose(
            projected.edges["x"].values, known_hist.edges[axis].values
        )

    def test_projection_conserves_the_total(self, known_hist, known_counts):
        """Both marginals carry the same total as the grid.

        ON FAILURE: the code is wrong.
        """
        for axis in ("x", "y"):
            total = known_hist.project_1d(axis, project_counts=True).agg().sum()
            assert total == known_counts.sum()

    def test_log_axis_projection_round_trips(self):
        """A log-scaled projection re-derives the same decade edges.

        ON FAILURE: the code is wrong.
        """
        xedges = np.array([1.0, 10.0, 100.0, 1000.0])
        yedges = np.array([1.0, 100.0, 10000.0])
        counts = np.array([[2, 3, 1], [4, 1, 5]])
        x, y = _points_from_counts(counts, np.log10(xedges), np.log10(yedges))
        h = Hist2D(
            10.0**x,
            10.0**y,
            logx=True,
            logy=True,
            nbins=[np.log10(xedges), np.log10(yedges)],
        )

        projected = h.project_1d("x", project_counts=True)
        assert projected.log.x is True
        np.testing.assert_allclose(projected.agg().values, counts.sum(axis=0))
        np.testing.assert_allclose(
            10.0 ** projected.edges["x"].values, xedges, rtol=1e-10
        )

    def test_projection_aggregates_z_when_the_histogram_has_z_values(self):
        """With z-values present, the marginal is the mean of z per x-bin.

        numpy computes each expected mean from the same inputs.

        ON FAILURE: the code is wrong.
        """
        x, y = _points_from_counts(KNOWN_COUNTS, XEDGES, YEDGES)
        rng = np.random.default_rng(41)
        z = pd.Series(rng.uniform(0.0, 10.0, x.size), name="z")

        h = Hist2D(x, y, z, nbins=[XEDGES, YEDGES])
        projected = h.project_1d("x").agg()

        expected = [
            np.mean(z.values[((lo < x) & (x <= hi)).values])
            for lo, hi in zip(XEDGES[:-1], XEDGES[1:])
        ]
        np.testing.assert_allclose(projected.values, expected)

    def test_unknown_axis_is_rejected(self, known_hist):
        """Only "x" and "y" can be projected.

        ON FAILURE: the code is wrong -- a typo would silently project the
        wrong axis.
        """
        with pytest.raises(AssertionError):
            known_hist.project_1d("z")


@broken_on_pandas_3
class TestIdDataAboveContour:
    """Labelling observations that sit in a well-populated part of the grid."""

    def test_result_aligns_with_the_stored_data(self, known_hist):
        """The returned Series is index-aligned with the data, as documented.

        The docstring promises it "is purposely the same length as the data
        stored by Hist2D and can be used in groupby operations".

        ON FAILURE: the code is wrong.
        """
        labelled = known_hist.id_data_above_contour(1)
        pd.testing.assert_index_equal(labelled.index, known_hist.data.index)

    def test_every_label_contains_its_own_observation(self, known_hist):
        """A labelled point lies inside the x-interval it was labelled with.

        ON FAILURE: the code is wrong -- the label would not describe the point.
        """
        labelled = known_hist.id_data_above_contour(1)
        x = known_hist.data.x
        marked = labelled.dropna()
        assert marked.size > 0
        for idx, interval in marked.items():
            assert interval.left < x.loc[idx] <= interval.right

    def test_raising_the_threshold_selects_a_subset(self, known_hist):
        """Fewer bins clear a higher level, so fewer points are labelled.

        ON FAILURE: the code is wrong -- selection must be monotone in the
        threshold.
        """
        low = known_hist.id_data_above_contour(1).notna()
        high = known_hist.id_data_above_contour(3).notna()
        assert high.sum() <= low.sum()
        assert not (high & ~low).any()

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "id_data_above_contour raises AttributeError when a column has no "
            "bin at or above `level`: the empty selection's min()/max() is NaN, "
            "which has no .left. Replaces nothing -- this path had no test. "
            "Remove the xfail when empty columns are skipped."
        ),
    )
    def test_columns_with_nothing_above_the_level_are_simply_unlabelled(
        self, known_hist, known_counts
    ):
        """A level above a column's maximum leaves that column's points NaN.

        The docstring already says what should happen: "NaN are observations
        that are below `level`".

        ON FAILURE (i.e. an unexpected pass): the fix has landed; drop the
        xfail marker.
        """
        level = known_counts.max()  # no column other than the peak's clears this
        labelled = known_hist.id_data_above_contour(level)
        assert labelled.notna().sum() < known_hist.data.index.size


class TestTakeDataInYRangeAcrossX:
    """Selecting observations inside a per-column y-range."""

    def test_selection_matches_an_independent_numpy_mask(self, known_hist):
        """The returned indices are exactly those numpy would select.

        ON FAILURE: the code is wrong.
        """
        columns = known_hist.agg().unstack("x").columns
        ranges = pd.DataFrame({"bottom": 0.2, "top": 0.6}, index=columns)

        taken = known_hist.take_data_in_yrange_across_x(
            ranges,
            lambda key, expected_logx=False: (key.left, key.right),
            lambda row, expected_logy=False: (row.bottom, row.top),
        )

        x = known_hist.data.x.values
        y = known_hist.data.y.values
        expected = np.flatnonzero(
            (XEDGES[0] < x) & (x <= XEDGES[-1]) & (0.2 < y) & (y <= 0.6)
        )
        np.testing.assert_array_equal(taken, expected)

    def test_per_column_ranges_are_honoured_independently(self, known_hist):
        """Different y-ranges per column select different points per column.

        ON FAILURE: the code is wrong -- a single range would be applied
        everywhere.
        """
        columns = known_hist.agg().unstack("x").columns
        bottoms = [0.0, 0.4, 0.0, 0.6]
        tops = [0.2, 1.0, 0.4, 1.0]
        ranges = pd.DataFrame({"bottom": bottoms, "top": tops}, index=columns)

        taken = known_hist.take_data_in_yrange_across_x(
            ranges,
            lambda key, expected_logx=False: (key.left, key.right),
            lambda row, expected_logy=False: (row.bottom, row.top),
        )

        x = known_hist.data.x.values
        y = known_hist.data.y.values
        mask = np.zeros(x.size, dtype=bool)
        for j, (b, t) in enumerate(zip(bottoms, tops)):
            mask |= (XEDGES[j] < x) & (x <= XEDGES[j + 1]) & (b < y) & (y <= t)
        np.testing.assert_array_equal(taken, np.flatnonzero(mask))

    def test_returned_indices_are_sorted(self, known_hist):
        """The documented return is a sorted index array.

        ON FAILURE: the code is wrong.
        """
        columns = known_hist.agg().unstack("x").columns
        ranges = pd.DataFrame({"bottom": 0.0, "top": 1.0}, index=columns)
        taken = known_hist.take_data_in_yrange_across_x(
            ranges,
            lambda key, expected_logx=False: (key.left, key.right),
            lambda row, expected_logy=False: (row.bottom, row.top),
        )
        assert np.all(np.diff(taken) > 0)

    def test_a_selector_naming_unavailable_bins_is_rejected(self, known_hist):
        """A selector indexed on bins the histogram does not have raises.

        Silently ignoring them would return a selection quietly narrower than
        the caller asked for.

        ON FAILURE: the code is wrong.
        """
        foreign = pd.IntervalIndex.from_breaks(
            [0.0, 0.1, 0.2, 0.3, 0.4, 1.0], closed="right"
        )
        ranges = pd.DataFrame({"bottom": 0.0, "top": 1.0}, index=foreign)

        with pytest.raises(ValueError, match="Need a way to drop values"):
            known_hist.take_data_in_yrange_across_x(
                ranges,
                lambda key, expected_logx=False: (key.left, key.right),
                lambda row, expected_logy=False: (row.bottom, row.top),
            )

    def test_inverted_bounds_are_rejected(self, known_hist):
        """A range whose bottom exceeds its top is an error, not an empty set.

        ON FAILURE: the code is wrong -- silently returning nothing would hide
        the caller's mistake.
        """
        columns = known_hist.agg().unstack("x").columns
        ranges = pd.DataFrame({"bottom": 0.9, "top": 0.1}, index=columns)
        with pytest.raises(AssertionError):
            known_hist.take_data_in_yrange_across_x(
                ranges,
                lambda key, expected_logx=False: (key.left, key.right),
                lambda row, expected_logy=False: (row.bottom, row.top),
            )


class TestDefaultContourLevels:
    """Properties the default levels must have, rather than their literal values.

    The literal defaults are editorial choices with no derivation available, so
    only what must be true of any admissible choice is asserted.
    """

    @pytest.mark.parametrize("axnorm", ["t", "d", "c", "r"])
    def test_defaults_are_strictly_increasing(self, known_hist, axnorm):
        """Contour levels must increase; matplotlib requires it.

        ON FAILURE: the code is wrong.
        """
        known_hist.set_axnorm(axnorm)
        levels = known_hist._get_contour_levels(None)
        assert np.all(np.diff(levels) > 0)

    @pytest.mark.parametrize("axnorm", ["t", "c", "r"])
    def test_defaults_lie_inside_the_normalised_range(self, known_hist, axnorm):
        """For a normalisation bounded by 1, no level may exceed 1.

        Total/column/row normalisation divide by a maximum, so every value is in
        [0, 1]; a level outside that range could never be drawn.

        ON FAILURE: the code is wrong.
        """
        known_hist.set_axnorm(axnorm)
        levels = np.asarray(known_hist._get_contour_levels(None))
        assert levels.min() >= 0.0
        assert levels.max() <= 1.0

    def test_explicit_levels_are_passed_through_untouched(self, known_hist):
        """Caller-supplied levels override the defaults for every axnorm.

        ON FAILURE: the code is wrong.
        """
        requested = [0.05, 0.25, 0.75]
        for axnorm in (None, "t", "d", "c", "r", "cd", "rd"):
            known_hist.set_axnorm(axnorm)
            assert known_hist._get_contour_levels(requested) is requested

    def test_no_default_without_a_normalisation(self, known_hist):
        """Unnormalised counts have no scale, so there is no default level set.

        ON FAILURE: the code is wrong -- a fixed level list cannot suit
        arbitrary raw counts.
        """
        known_hist.set_axnorm(None)
        assert known_hist._get_contour_levels(None) is None

    def test_unrecognised_normalisation_is_rejected(self, known_hist):
        """An axnorm with no default level set raises rather than guessing.

        ON FAILURE: the code is wrong.
        """
        known_hist._axnorm = ("c", "sum")
        with pytest.raises(ValueError, match="Unrecognized axis normalization"):
            known_hist._get_contour_levels(None)


class TestColorScale:
    """The colour normalisation `make_plot` chooses and the one it is given."""

    @pytest.mark.parametrize("axnorm", ["c", "r"])
    def test_bounded_normalisation_spans_zero_to_one(self, known_hist, axnorm):
        """Data normalised to [0, 1] gets a colour scale spanning [0, 1].

        Column and row normalisation divide by a maximum, so the full range is
        known in advance; a scale narrower than that would clip real values and
        one wider would waste the colormap.

        ON FAILURE: the code is wrong.
        """
        known_hist.set_axnorm(axnorm)
        ax, mappable = known_hist.make_plot(cbar=False)

        assert mappable.norm.vmin == 0.0
        assert mappable.norm.vmax == 1.0
        plt.close("all")

    def test_caller_supplied_norm_overrides_the_default(self, known_hist):
        """An explicit `norm` wins over whatever the axnorm would have chosen.

        ON FAILURE: the code is wrong -- the caller could not control the
        colour scale.
        """
        known_hist.set_axnorm("c")
        requested = matplotlib.colors.Normalize(vmin=0.2, vmax=0.4)
        ax, mappable = known_hist.make_plot(cbar=False, norm=requested)

        assert mappable.norm is requested
        plt.close("all")

    def test_combined_plot_also_honours_a_supplied_norm(self, known_hist):
        """`plot_hist_with_contours` shares the caller's norm with both layers.

        A background and an overlay drawn on different colour scales would not
        be comparable to each other.

        ON FAILURE: the code is wrong.
        """
        known_hist.set_axnorm("t")
        requested = matplotlib.colors.Normalize(vmin=0.0, vmax=1.0)
        ax, cbar, qset, lbls = known_hist.plot_hist_with_contours(
            cbar=False, norm=requested
        )

        assert _quadmesh(ax).norm is requested
        assert qset.norm is requested
        plt.close("all")


class TestContourFiltering:
    """Smoothing the grid before contouring it."""

    @pytest.fixture
    def complete_hist(self):
        """A Hist2D with every bin populated, so the grid has no NaN."""
        edges = np.round(np.linspace(0.0, 1.0, 9), 5)
        rng = np.random.default_rng(31)
        counts = rng.integers(1, 9, size=(len(edges) - 1, len(edges) - 1))
        x, y = _points_from_counts(counts, edges, edges)
        return Hist2D(x, y, nbins=[edges, edges], axnorm="t")

    def test_nan_aware_filter_reduces_to_the_plain_filter_without_gaps(
        self, complete_hist
    ):
        """With no missing bins the two filters must agree exactly.

        `nan_aware_filter` is a normalised convolution: the weighted average is
        divided by the summed weight of the *valid* neighbours. When every
        neighbour is valid that divisor is the full kernel sum, and the
        expression collapses to an ordinary Gaussian convolution. So this is an
        identity the implementation has to satisfy, not a recorded agreement.

        ON FAILURE: the code is wrong -- one of the two filters is not doing
        what its name says.
        """
        assert not np.isnan(complete_hist.agg().unstack("x").values).any()

        plain = complete_hist.plot_contours(
            gaussian_filter_std=1.5,
            nan_aware_filter=False,
            cbar=False,
            label_levels=False,
        )[3]
        nan_aware = complete_hist.plot_contours(
            gaussian_filter_std=1.5,
            nan_aware_filter=True,
            cbar=False,
            label_levels=False,
        )[3]

        assert len(plain.allsegs) == len(nan_aware.allsegs)
        for at_plain, at_nan_aware in zip(plain.allsegs, nan_aware.allsegs):
            assert len(at_plain) == len(at_nan_aware)
            for left, right in zip(at_plain, at_nan_aware):
                np.testing.assert_allclose(left, right)
        plt.close("all")


class TestContourLabels:
    """The text `clabel` writes onto the contours."""

    def test_labels_name_only_levels_that_were_asked_for(self, known_hist):
        """Every label reads back as one of the requested contour levels.

        ON FAILURE: the code is wrong -- a contour would be annotated with a
        value it does not represent.
        """
        known_hist.set_axnorm("t")
        levels = [0.1, 0.3, 0.5, 0.7]
        ax, lbls, cbar, qset = known_hist.plot_contours(
            levels=levels, label_levels=True, cbar=False
        )

        assert lbls is not None
        for text in lbls:
            assert float(text.get_text()) in levels
        plt.close("all")

    def test_the_maximum_level_is_left_unlabelled_by_default(self, known_hist):
        """`skip_max_clbl` defaults to True, so the top contour gets no text.

        The documented reason is that the maximum contour is "effectively, a
        point", which a label would cover entirely.

        ON FAILURE: the code is wrong, or the default changed.
        """
        known_hist.set_axnorm("t")
        levels = [0.1, 0.3, 0.5, 0.7]
        ax, lbls, cbar, qset = known_hist.plot_contours(
            levels=levels, label_levels=True, cbar=False
        )

        labelled = {float(text.get_text()) for text in lbls}
        assert max(levels) not in labelled
        plt.close("all")

    def test_combined_plot_labels_its_contours_on_request(self, known_hist):
        """`plot_hist_with_contours(label_levels=True)` returns the labels.

        ON FAILURE: the code is wrong -- the documented return value is
        missing.
        """
        known_hist.set_axnorm("t")
        levels = [0.1, 0.3, 0.5, 0.7]
        ax, cbar, qset, lbls = known_hist.plot_hist_with_contours(
            levels=levels, label_levels=True, cbar=False
        )

        assert lbls is not None
        for text in lbls:
            assert float(text.get_text()) in levels
        plt.close("all")


class TestJointPlot:
    """The joint 2D-plus-marginals figure."""

    def test_marginal_panels_carry_the_projected_counts(self, known_hist, known_counts):
        """The side panels plot the marginals of the central grid.

        ON FAILURE: the code is wrong -- the marginals would not describe the
        heatmap they flank.
        """
        hax, xax, yax, cbar = known_hist.make_joint_h2_h1_plot(project_counts=True)

        np.testing.assert_allclose(
            np.asarray(xax.lines[0].get_ydata(), float), known_counts.sum(axis=0)
        )
        # The y panel is drawn transposed, so its counts are the x-data.
        np.testing.assert_allclose(
            np.asarray(yax.lines[0].get_xdata(), float), known_counts.sum(axis=1)
        )
        plt.close("all")

    def test_marginal_panels_share_the_central_axes(self, known_hist):
        """The panels are aligned with the heatmap they annotate.

        ON FAILURE: the code is wrong -- the marginals would be drawn against a
        different scale than the grid beside them.
        """
        hax, xax, yax, cbar = known_hist.make_joint_h2_h1_plot()
        assert hax.get_xlim() == xax.get_xlim()
        assert hax.get_ylim() == yax.get_ylim()
        assert isinstance(cbar, matplotlib.colorbar.Colorbar)
        plt.close("all")


if __name__ == "__main__":
    pytest.main([__file__])
