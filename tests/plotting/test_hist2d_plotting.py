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

import inspect
import subprocess
import sys
import textwrap
import warnings

import pytest
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from scipy.ndimage import gaussian_filter  # noqa: E402
from scipy.signal import savgol_filter  # noqa: E402

from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402
from solarwindpy.plotting.labels.special import Count  # noqa: E402
from tests.tolerances import exact  # noqa: E402


class _ProjectionMovesEdgeSamples(AssertionError):
    """Raised when a projection's counts differ from numpy.histogram's."""


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


class TestContourGrid:
    """Contours are traced on bin centres; the mesh is drawn on bin edges.

    The edge side (mesh coordinates and values) is asserted in
    ``TestMakePlot``; this class covers the centre side.
    """

    def test_contour_vertices_lie_within_the_bin_centres(self, known_hist):
        """Every contour vertex lies inside the span of the bin centres.

        ``XEDGES`` and ``YEDGES`` give centres from 0.125 to 0.875 and from 0.1
        to 0.9; a contour traced on the edges could reach 0 and 1.

        ON FAILURE: the code is wrong.
        """
        x_mid = 0.5 * (XEDGES[1:] + XEDGES[:-1])
        y_mid = 0.5 * (YEDGES[1:] + YEDGES[:-1])
        fig, ax = plt.subplots()
        *_, qset = known_hist.plot_contours(ax=ax, cbar=False, levels=[0.5, 1.5, 2.5])
        vertices = np.concatenate([seg for segs in qset.allsegs for seg in segs])
        plt.close(fig)
        assert vertices.size  # the fixture: the chosen levels draw contours
        assert vertices[:, 0].min() >= x_mid.min() * (1 - 1e-12)
        assert vertices[:, 0].max() <= x_mid.max() * (1 + 1e-12)
        assert vertices[:, 1].min() >= y_mid.min() * (1 - 1e-12)
        assert vertices[:, 1].max() <= y_mid.max() * (1 + 1e-12)


class TestPlotHistWithContours:
    """Tests for plot_hist_with_contours method."""

    def test_returns_its_axes_the_mesh_colorbar_and_the_contours_drawn(
        self, known_hist
    ):
        """The documented ``(ax, cbar, qset)`` are the objects on the plot.

        ``ax`` is the Axes supplied, ``cbar`` colours the mesh under the
        contours and carries ``labels.z``, and ``qset`` is the contour set
        drawn on ``ax`` at the requested levels. No text is drawn: the method
        does not label contours.

        ON FAILURE: the code is wrong, or the documented return contract
        changed.
        """
        known_hist.set_axnorm("t")
        _, supplied = plt.subplots()
        ax, cbar, qset = known_hist.plot_hist_with_contours(
            ax=supplied, levels=[0.3, 0.6]
        )
        assert ax is supplied
        assert cbar.mappable is _quadmesh(ax)
        assert cbar.ax.get_ylabel() == str(known_hist.labels.z)
        assert qset in ax.collections
        np.testing.assert_array_equal(qset.levels, [0.3, 0.6])
        assert len(ax.texts) == 0
        plt.close("all")

    def test_use_contourf_switches_between_filled_and_line_contours(
        self, hist2d_instance
    ):
        """``use_contourf=True`` draws filled contours; False draws lines.

        ON FAILURE: the code is wrong.
        """
        _, _, filled = hist2d_instance.plot_hist_with_contours(use_contourf=True)
        _, _, lines = hist2d_instance.plot_hist_with_contours(use_contourf=False)
        assert filled.filled is True
        assert lines.filled is False
        plt.close("all")

    # --- Integration Tests (correctness) ---

    def test_contour_levels_correct_for_axnorm_t(self, hist2d_instance):
        """Contour levels should match expected values for axnorm='t'.

        ON FAILURE: the code is wrong, or the author changed the "t" defaults
        in `_get_contour_levels`.
        """
        ax, cbar, qset = hist2d_instance.plot_hist_with_contours()
        # For axnorm="t", default levels are [0.01, 0.1, 0.3, 0.7, 0.99]
        expected_levels = [0.01, 0.1, 0.3, 0.7, 0.99]
        np.testing.assert_allclose(
            qset.levels,
            expected_levels,
            err_msg="Contour levels should match expected for axnorm='t'",
        )
        plt.close("all")

    def test_colorbar_range_valid_for_normalized_data(self, hist2d_instance):
        """Colorbar range should be within [0, 1] for normalized data.

        ON FAILURE: the code is wrong.
        """
        ax, cbar, qset = hist2d_instance.plot_hist_with_contours()
        # For axnorm="t" (total normalized), values should be in [0, 1]
        assert cbar.vmin >= 0, "Colorbar vmin should be >= 0"
        assert cbar.vmax <= 1, "Colorbar vmax should be <= 1"
        plt.close("all")

    def test_gaussian_filter_changes_contour_data(self, hist2d_instance):
        """Gaussian filtering should produce different contours than unfiltered.

        ON FAILURE: the code is wrong.
        """
        # Get unfiltered contours
        ax1, _, qset1 = hist2d_instance.plot_hist_with_contours(gaussian_filter_std=0)
        unfiltered_data = qset1.allsegs

        # Get filtered contours
        ax2, _, qset2 = hist2d_instance.plot_hist_with_contours(gaussian_filter_std=2)
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

    def test_pcolormesh_data_matches_prep_agg(self, known_hist, known_counts):
        """The mesh under the contours carries the peak-normalised counts.

        With ``axnorm="t"`` each bin is its count over the largest count;
        empty bins are blank.

        ON FAILURE: the code is wrong.
        """
        known_hist.set_axnorm("t")
        ax, cbar, qset = known_hist.plot_hist_with_contours()
        values = np.ma.filled(_quadmesh(ax).get_array().astype(float), np.nan)
        expected = _expected_grid(known_counts) / known_counts.max()
        assert np.asarray(values.reshape(expected.shape)) == exact(
            expected, nan_ok=True
        )
        plt.close("all")

    def test_mesh_aggregates_with_the_callers_fcn(self, z_valued_hist):
        """``fcn`` reaches the mesh: with ``"count"`` it shows counts, not means.

        The fixture's per-bin mean is ``7 - count``, so the default mean and the
        requested count differ in every occupied bin.

        ON FAILURE: the code is wrong.
        """
        hist, counts, _ = z_valued_hist
        ax, _, _ = hist.plot_hist_with_contours(fcn="count", cbar=False)
        values = np.ma.filled(_quadmesh(ax).get_array().astype(float), np.nan)
        expected = _expected_grid(counts)  # empty bins are blank
        assert np.asarray(values.reshape(expected.shape)) == exact(
            expected, nan_ok=True
        )
        plt.close("all")

    def test_nan_aware_filter_contours_the_normalised_convolution(
        self, known_hist, known_counts
    ):
        """With ``nan_aware_filter`` the contours trace the normalised convolution.

        ``KNOWN_COUNTS`` leaves bins empty, so the grid has NaN gaps. The
        expectation is computed here from the algorithm the docstring names
        (Knutsson & Westin 1993, normalised convolution): smooth the grid with
        gaps set to 0, divide by the smoothed validity mask, and keep the gaps
        blank. Contouring that grid at the same levels must reproduce the
        overlay vertex for vertex.

        ON FAILURE: the code is wrong.
        """
        levels = [0.2, 0.4, 0.6]
        sigma = 1.0
        known_hist.set_axnorm("t")
        _, _, qset = known_hist.plot_hist_with_contours(
            cbar=False,
            levels=levels,
            use_contourf=True,
            gaussian_filter_std=sigma,
            nan_aware_filter=True,
        )

        # axnorm "t" divides every bin by the largest bin count in the grid.
        grid = _expected_grid(known_counts) / known_counts.max()
        valid = ~np.isnan(grid)
        smoothed = gaussian_filter(np.where(valid, grid, 0.0), sigma) / gaussian_filter(
            valid.astype(float), sigma
        )
        smoothed[~valid] = np.nan
        XX, YY = np.meshgrid(_bin_centers(XEDGES), _bin_centers(YEDGES))
        _, ref_ax = plt.subplots()
        expected = ref_ax.contourf(XX, YY, np.ma.masked_invalid(smoothed), levels)

        assert sum(len(segs) for segs in expected.allsegs) > 0  # contours exist
        assert len(qset.allsegs) == len(expected.allsegs)
        for got_at_level, want_at_level in zip(qset.allsegs, expected.allsegs):
            assert len(got_at_level) == len(want_at_level)
            for got, want in zip(got_at_level, want_at_level):
                assert np.asarray(got) == exact(want)
        plt.close("all")


class TestPlotContours:
    """Tests for plot_contours method."""

    def test_single_level_no_boundary_norm_error(self, hist2d_instance):
        """Single-level contours should not raise BoundaryNorm ValueError.

        BoundaryNorm requires at least 2 boundaries. When levels has only 1 element,
        plot_contours should skip BoundaryNorm creation and let matplotlib handle it.
        Note: cbar=False is required because matplotlib's colorbar also requires 2+ levels.

        Regression test for: ValueError: You must provide at least 2 boundaries

        ON FAILURE: the code is wrong.
        """
        ax, mappable, qset = hist2d_instance.plot_contours(levels=[0.5], cbar=False)
        assert len(qset.levels) == 1
        assert qset.levels[0] == 0.5
        plt.close("all")

    def test_multiple_levels_preserved(self, hist2d_instance):
        """Multiple levels should be preserved in returned contour set.

        ON FAILURE: the code is wrong.
        """
        levels = [0.3, 0.5, 0.7]
        ax, mappable, qset = hist2d_instance.plot_contours(levels=levels)
        assert len(qset.levels) == 3
        np.testing.assert_allclose(qset.levels, levels)
        plt.close("all")

    def test_use_contourf_true_returns_filled_contours(self, hist2d_instance):
        """use_contourf=True should return filled QuadContourSet.

        ON FAILURE: the code is wrong.
        """
        ax, _, qset = hist2d_instance.plot_contours(use_contourf=True)
        assert qset.filled is True
        plt.close("all")

    def test_use_contourf_false_returns_line_contours(self, hist2d_instance):
        """use_contourf=False should return unfilled QuadContourSet.

        ON FAILURE: the code is wrong.
        """
        ax, _, qset = hist2d_instance.plot_contours(use_contourf=False)
        assert qset.filled is False
        plt.close("all")

    def test_cbar_true_returns_the_colorbar_of_the_contours(self, hist2d_instance):
        """With cbar=True the second value is a colorbar of the drawn contours.

        It colours ``qset``, the contour set on ``ax``, and carries
        ``labels.z``, as the ``cbar`` parameter documents.

        ON FAILURE: the code is wrong.
        """
        ax, mappable, qset = hist2d_instance.plot_contours(cbar=True)
        assert isinstance(mappable, matplotlib.colorbar.Colorbar)
        assert mappable.mappable is qset
        assert qset in ax.collections
        assert mappable.ax.get_ylabel() == str(hist2d_instance.labels.z)
        plt.close("all")

    def test_cbar_false_returns_the_contour_set_itself(self, hist2d_instance):
        """With cbar=False the second value is the contour set drawn on ``ax``.

        ON FAILURE: the code is wrong.
        """
        ax, mappable, qset = hist2d_instance.plot_contours(cbar=False)
        assert mappable is qset
        assert qset in ax.collections
        plt.close("all")


class TestBinContract:
    """What `calc_bins_intervals` promises about the bins it produces.

    The docstring names `np.histogram_bin_edges` as the source of the edges for
    an integer/str `nbins`, so numpy supplies the expectation directly.
    """

    @pytest.mark.parametrize("nbins", [5, 12, 33])
    def test_integer_nbins_matches_numpy_histogram_bin_edges(self, nbins):
        """Edges equal `np.histogram_bin_edges`, rounded to the stored precision.

        Interior edges round to nearest; the outer edges round outward (floor,
        ceil) so they enclose every sample, per numpy.histogram's convention.

        ON FAILURE: the code is wrong, unless the docstring's promise to use
        `np.histogram_bin_edges` was deliberately withdrawn.
        """
        rng = np.random.default_rng(11)
        x = pd.Series(rng.normal(0.0, 3.0, 400), name="x")
        y = pd.Series(rng.normal(5.0, 1.0, 400), name="y")

        h = Hist2D(x, y, nbins=nbins)

        for name, data in (("x", x), ("y", y)):
            numpy_edges = np.histogram_bin_edges(data.values, nbins)
            expected = numpy_edges.round(5)
            expected[0] = np.floor(numpy_edges[0] * 1e5) / 1e5
            expected[-1] = np.ceil(numpy_edges[-1] * 1e5) / 1e5
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

    @pytest.mark.parametrize("nbins", [4, 17])
    def test_edges_span_the_data(self, nbins):
        """Every observation falls inside the outer edges.

        ON FAILURE: the code is wrong.
        """
        rng = np.random.default_rng(13)
        x = pd.Series(rng.normal(size=300))
        y = pd.Series(rng.normal(size=300))
        h = Hist2D(x, y, nbins=nbins)
        for name, data in (("x", x), ("y", y)):
            edges = h.edges[name].values
            assert edges[0] <= data.min()
            assert data.max() <= edges[-1]

    def test_auto_bins_retain_every_observation(self):
        """A histogram partitions its data: the counts must sum to N.

        ON FAILURE: the code is wrong.
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


class TestClipData:
    """``clip_data`` clips the tails it names when points are binned."""

    # One low and one high x outlier. Clipping to the 0.01st percentile moves
    # -1000 to about -999.1 and clipping to the 99.99th moves 1000 to about
    # 999.1, each from an outer x-bin into the middle one (-999.5, 999.5].
    # y is constant, so clipping leaves it alone.
    X = pd.Series([-1000.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1000.0])
    XEDGES = np.array([-1001.0, -999.5, 999.5, 1001.0])

    @pytest.mark.parametrize(
        "clip_data, expected",
        [
            (None, [1, 8, 1]),  # nothing moves
            (False, [1, 8, 1]),
            (True, [0, 10, 0]),  # both outliers move to the middle bin
            ("l", [0, 9, 1]),  # only the low outlier moves
            ("u", [1, 9, 0]),  # only the high outlier moves
        ],
    )
    def test_clip_data_clips_the_tails_it_names(self, clip_data, expected):
        """``"l"`` clips the lower tail, ``"u"`` the upper, True both, None neither.

        ON FAILURE: the code is wrong.
        """
        y = pd.Series(0.5, index=self.X.index)
        h = Hist2D(
            self.X,
            y,
            clip_data=clip_data,
            nbins=[self.XEDGES, np.array([0.0, 1.0])],
        )
        grid = h.agg().unstack("x").reindex(columns=h.intervals["x"])
        counts = grid.fillna(0).sum(axis=0)  # empty x-bins count 0
        assert counts.to_numpy() == exact(expected)

    @pytest.mark.parametrize(
        "given, expected",
        [(None, False), (False, False), (True, True), ("l", "l"), ("u", "u")],
    )
    def test_clip_stores_clip_data_with_none_as_false(self, given, expected):
        """``clip`` keeps ``clip_data`` as given, except None, which becomes False.

        ON FAILURE: the code is wrong.
        """
        clip = Hist2D(self.X, self.X, clip_data=given).clip
        assert clip == expected
        assert type(clip) is type(expected)


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

        assert grid.columns[0].right == exact(XEDGES[1])
        assert grid.index[0].right == exact(YEDGES[1])
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

    def test_returns_colorbar_of_the_mesh_when_requested(self, known_hist):
        """`cbar=True` returns the Colorbar of the drawn mesh, labelled `labels.z`.

        The documented return is the colorbar; the `cbar` parameter documents
        its label.

        ON FAILURE: the code is wrong, or the documented return contract
        changed.
        """
        ax, returned = known_hist.make_plot(cbar=True)
        assert isinstance(returned, matplotlib.colorbar.Colorbar)
        assert returned.mappable is _quadmesh(ax)
        assert returned.ax.get_ylabel() == str(known_hist.labels.z)
        plt.close("all")

    def test_returns_the_drawn_mesh_when_no_colorbar(self, known_hist):
        """`cbar=False` returns the QuadMesh on `ax`, per the documented return.

        ON FAILURE: the code is wrong, or the documented return contract
        changed.
        """
        ax, returned = known_hist.make_plot(cbar=False)
        assert returned is _quadmesh(ax)
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


class TestQuantileAlimInPlots:
    """Quantile ``alim`` limits a plot to the bulk of its values."""

    # Of the 14 occupied bins of KNOWN_COUNTS, sorted 1,1,1,2,2,2,2,3,3,4,4,5,5,6,
    # the 1% quantile sits at position 0.13 (value 1) and the 99% quantile at
    # 12.87, 5 + 0.87 * (6 - 5) = 5.87: only the single 6 lies outside.

    @staticmethod
    def _expected_grid():
        occupied = KNOWN_COUNTS[KNOWN_COUNTS > 0]  # the chosen input's bins
        lo, hi = np.quantile(occupied, [0.01, 0.99])
        assert (lo, hi) == exact((1.0, 5.87))  # by hand
        kept = (KNOWN_COUNTS >= lo) & (KNOWN_COUNTS <= hi)
        return np.where(kept, KNOWN_COUNTS, np.nan)

    def test_make_plot_meshes_only_counts_inside_the_quantiles(self, known_hist):
        """With 1%/99% quantile ``alim``, the mesh holds every count but the 6.

        ON FAILURE: the code is wrong.
        """
        known_hist.set_alim(0.01, 0.99, kind="quantile")
        ax, _ = known_hist.make_plot(cbar=False)
        values = np.ma.filled(np.ma.asarray(_quadmesh(ax).get_array(), float), np.nan)
        np.testing.assert_array_equal(
            values.reshape(KNOWN_COUNTS.shape), self._expected_grid()
        )
        plt.close("all")

    def test_contour_overlay_meshes_only_counts_inside_the_quantiles(self, known_hist):
        """`plot_hist_with_contours` draws the same quantile-limited mesh.

        ON FAILURE: the code is wrong.
        """
        known_hist.set_alim(0.01, 0.99, kind="quantile")
        ax, _, _ = known_hist.plot_hist_with_contours(cbar=False)
        values = np.ma.filled(np.ma.asarray(_quadmesh(ax).get_array(), float), np.nan)
        np.testing.assert_array_equal(
            values.reshape(KNOWN_COUNTS.shape), self._expected_grid()
        )
        plt.close("all")


def _norm_of(method, axnorm):
    """The colour norm ``method`` hands matplotlib for ``axnorm``, no ``norm`` given."""
    x, y = _points_from_counts(KNOWN_COUNTS, XEDGES, YEDGES)
    h = Hist2D(x, y, nbins=[XEDGES, YEDGES], axnorm=axnorm)
    if method == "make_plot":
        ax, _ = h.make_plot(cbar=False)
        return _quadmesh(ax).norm
    if method == "plot_hist_with_contours":
        ax, _, qset = h.plot_hist_with_contours(cbar=False)
        assert qset.norm is _quadmesh(ax).norm
        return qset.norm
    _, _, qset = h.plot_contours(cbar=False)
    return qset.norm


class TestDefaultNorm:
    """Without ``norm``, the three 2D plots colour each ``axnorm`` the same way."""

    METHODS = ["make_plot", "plot_hist_with_contours", "plot_contours"]

    @pytest.mark.parametrize("method", METHODS)
    @pytest.mark.parametrize("axnorm", ["c", "r"])
    def test_row_and_column_norms_get_ten_bands_on_the_unit_interval(
        self, method, axnorm
    ):
        """Row/column-normalised values lie in [0, 1]: ten equal bands.

        ON FAILURE: the code is wrong.
        """
        norm = _norm_of(method, axnorm)
        assert isinstance(norm, matplotlib.colors.BoundaryNorm)
        np.testing.assert_array_equal(norm.boundaries, np.linspace(0, 1, 11))
        plt.close("all")

    @pytest.mark.parametrize("method", METHODS)
    @pytest.mark.parametrize("axnorm", ["d", "cd", "rd"])
    def test_densities_get_a_log_norm(self, method, axnorm):
        """Densities span decades, so every plot colours them on a clipped log scale.

        `Hist2D._default_norm` documents a clipped `LogNorm` for densities, so
        values outside the colour range take the end colours instead of the
        over/under colours.

        ON FAILURE: the code is wrong, unless the author has chosen a linear
        or unclipped default for densities again.
        """
        norm = _norm_of(method, axnorm)
        assert isinstance(norm, matplotlib.colors.LogNorm)
        assert norm.clip is True
        plt.close("all")

    def test_default_density_contour_levels_suit_a_log_norm(self):
        """Density contours keep their default levels, all positive, under LogNorm.

        ON FAILURE: the code is wrong.
        """
        x, y = _points_from_counts(KNOWN_COUNTS, XEDGES, YEDGES)
        h = Hist2D(x, y, nbins=[XEDGES, YEDGES], axnorm="d")
        _, _, qset = h.plot_contours(cbar=False)
        # The defaults written in `_get_contour_levels` for axnorm "d".
        expected = [3e-5, 1e-4, 3e-4, 1e-3, 1.7e-3, 2.3e-3]
        np.testing.assert_array_equal(qset.levels, expected)
        assert np.all(np.asarray(qset.levels) > 0)
        plt.close("all")


class TestPlotSignatures:
    """The 2D plots keep their positional order; ``levels`` is a named parameter."""

    @pytest.mark.parametrize(
        "method, leading",
        [
            ("make_plot", ["ax", "cbar", "cbar_kwargs", "fcn", "alpha_fcn"]),
            (
                "plot_hist_with_contours",
                ["ax", "cbar", "cbar_kwargs", "fcn", "levels", "use_contourf"],
            ),
            (
                "plot_contours",
                ["ax", "cbar", "cbar_kwargs", "fcn", "plot_edges", "edges_kwargs"],
            ),
        ],
    )
    def test_positional_parameters_are_in_the_documented_order(self, method, leading):
        """The leading parameters are the order given in CHANGELOG.md.

        ON FAILURE: the code is wrong, unless the author has reordered the
        signature; then update CHANGELOG.md and this list together.
        """
        params = list(inspect.signature(getattr(Hist2D, method)).parameters)
        stop = 1 + len(leading)
        assert params[1:stop] == leading

    def test_plot_contours_levels_is_a_named_parameter_that_sets_the_levels(
        self, known_hist
    ):
        """``levels`` is the last named parameter of plot_contours and sets the levels.

        ON FAILURE: the code is wrong.
        """
        params = inspect.signature(Hist2D.plot_contours).parameters
        names = [n for n, p in params.items() if p.kind is p.POSITIONAL_OR_KEYWORD]
        assert names[-1] == "levels"
        assert params["levels"].default is None
        levels = [1.5, 2.5, 4.5]  # chosen inside the 1..6 counts of KNOWN_COUNTS
        _, _, qset = known_hist.plot_contours(levels=levels, cbar=False)
        np.testing.assert_array_equal(qset.levels, levels)
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

    def test_quantile_alim_keeps_bins_between_the_quantiles_of_the_counts(
        self, known_hist
    ):
        """`set_alim(0.25, 0.75, kind="quantile")` keeps counts between 2 and 4.

        The quantiles are of the 14 occupied bins of ``KNOWN_COUNTS``; empty
        bins are NaN and excluded. Sorted: 1,1,1,2,2,2,2,3,3,4,4,5,5,6. The
        25% quantile sits at position 3.25, between two 2s, and the 75%
        quantile at 9.75, between two 4s, so both bounds land on data values
        and the inclusive comparison is exercised.

        ON FAILURE: the code is wrong.
        """
        occupied = KNOWN_COUNTS[KNOWN_COUNTS > 0]  # the chosen input's bins
        lo, hi = np.quantile(occupied, [0.25, 0.75])
        assert (lo, hi) == (2.0, 4.0)  # hand-computed, see docstring

        known_hist.set_alim(0.25, 0.75, kind="quantile")
        grid = known_hist.agg().unstack("x").values

        kept = (KNOWN_COUNTS >= lo) & (KNOWN_COUNTS <= hi)
        np.testing.assert_array_equal(~np.isnan(grid), kept)
        np.testing.assert_array_equal(grid[kept], KNOWN_COUNTS[kept])

    def test_quantile_alim_ignores_infinite_values(self):
        """Quantiles are of the finite values; an infinite bin is outside them.

        One point per bin of the 4 x 5 grid, z = 1..19 and one inf. With the
        upper quantile 1.0 the threshold is 19, the largest finite value, so
        every finite bin survives and the inf bin is masked. Were inf pooled,
        the threshold would be inf or NaN.

        ON FAILURE: the code is wrong.
        """
        ones = np.ones_like(KNOWN_COUNTS)
        x, y = _points_from_counts(ones, XEDGES, YEDGES)
        z = np.arange(1.0, ones.size + 1.0)
        z[-1] = np.inf
        h = Hist2D(x, y, pd.Series(z, name="z"), nbins=[XEDGES, YEDGES])

        h.set_alim(None, 1.0, kind="quantile")
        agg = h.agg()

        assert agg.max() == 19.0  # the largest finite z, by construction
        assert agg.notna().sum() == ones.size - 1

    @pytest.mark.parametrize(
        "limits, kind, match",
        [
            ((0.1, 0.9), "percentile", "must be 'value' or 'quantile'"),
            ((-0.1, None), "quantile", "lower=-0.1 must be between 0 and 1"),
            ((None, 1.5), "quantile", "upper=1.5 must be between 0 and 1"),
            ((0.8, 0.2), "quantile", "must be less than upper"),
            ((0.5, 0.5), "quantile", "must be less than upper"),
            ((5.0, 2.0), "value", "value alim lower=5.0 must be less than upper"),
            ((3.0, 3.0), "value", "value alim lower=3.0 must be less than upper"),
        ],
        ids=[
            "kind",
            "below-0",
            "above-1",
            "reversed",
            "equal",
            "value-reversed",
            "value-equal",
        ],
    )
    def test_invalid_alim_is_rejected(self, known_hist, limits, kind, match):
        """An unknown kind, a quantile outside [0, 1], or lower >= upper is refused.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(ValueError, match=match):
            known_hist.set_alim(*limits, kind=kind)

    def test_alim_is_the_limit_pair_and_alim_kind_how_to_read_it(self, known_hist):
        """`alim` is the `(lower, upper)` pair and `alim_kind` defaults to "value".

        ON FAILURE: the code is wrong.
        """
        assert known_hist.alim == (None, None)
        assert known_hist.alim_kind == "value"
        known_hist.set_alim(0.1, 0.9, kind="quantile")
        assert known_hist.alim == (0.1, 0.9)
        assert known_hist.alim_kind == "quantile"
        known_hist.set_alim(2.0, None)
        assert (known_hist.alim, known_hist.alim_kind) == ((2.0, None), "value")


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
        """`xlim`/`ylim` keep vertices inside the range and drop those outside.

        The limits sit between vertices; vertices on a limit are covered by
        the two tests that follow.

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

    def test_vertex_exactly_on_an_x_limit_is_kept(self, known_hist):
        """A vertex whose x equals an `xlim` bound is drawn, per the docstring.

        The x bin centers 0.375 and 0.625 are exact in binary, so passing them
        as the lower and upper limits puts a vertex exactly on each bound.

        ON FAILURE: the code is wrong.
        """
        fig, ax = plt.subplots()
        (top_line,), _ = known_hist.plot_edges(
            ax, smooth=False, xlim=(0.375, 0.625), ylim=(None, None)
        )
        kept = np.asarray(top_line.get_xdata(), float)
        np.testing.assert_array_equal(kept, [0.375, 0.625])
        plt.close("all")

    def test_vertex_exactly_on_a_y_limit_is_kept(self, known_hist):
        """A vertex whose y equals a `ylim` bound is drawn, per the docstring.

        The limits are the smallest and largest y of the unrestricted top
        edge, so every vertex lies on or inside them and all are kept.

        ON FAILURE: the code is wrong.
        """
        fig, ax = plt.subplots()
        (full,), _ = known_hist.plot_edges(ax, smooth=False)
        full_y = np.asarray(full.get_ydata(), float)
        assert full_y.min() < full_y.max()  # both bounds are distinct vertices

        (clipped,), _ = known_hist.plot_edges(
            ax, smooth=False, ylim=(full_y.min(), full_y.max())
        )
        np.testing.assert_array_equal(np.asarray(clipped.get_ydata(), float), full_y)
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

        assert np.asarray(np.asarray(top_line.get_xdata(), float)) == exact(
            10.0 ** _bin_centers(log_x)
        )
        # Every column of `counts` is populated in the upper y-bin.
        assert np.asarray(np.asarray(top_line.get_ydata(), float)) == exact(
            np.full(len(xedges) - 1, 10.0 ** _bin_centers(log_y)[-1])
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
        assert np.asarray(np.asarray(smoothed.get_ydata(), float)) == exact(expected)
        plt.close("all")

    def test_both_edges_get_the_smoothing_the_caller_asked_for(self, smoothable_hist):
        """Top and bottom must be smoothed with the same requested parameters.

        Two edges of one distribution smoothed on different window lengths are
        not comparable to each other.

        ON FAILURE: the code is wrong.
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
        assert np.asarray(np.asarray(smoothed_bottom.get_ydata(), float)) == exact(
            expected
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
        assert np.asarray(10.0 ** projected.edges["x"].values) == exact(xedges)

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

    def test_only_plotted_projection_honours_the_count_limits(
        self, known_hist, known_counts
    ):
        """By default the marginal counts only the bins ``clim`` keeps.

        A lower count limit of 2 blanks the bins holding one observation, so
        they are not plotted and the default ``only_plotted=True`` leaves them
        out of the projection.

        ON FAILURE: the code is wrong.
        """
        known_hist.set_clim(2, None)
        projected = known_hist.project_1d("x", project_counts=True).agg()
        kept = np.where(known_counts >= 2, known_counts, 0)  # the bins clim keeps
        assert projected.to_numpy() == exact(kept.sum(axis=0))

    def test_two_valued_z_is_aggregated_as_data(self):
        """A z taking exactly two values is data: the marginal is its mean per x-bin.

        numpy computes each expected mean from the same inputs.

        ON FAILURE: the code is wrong.
        """
        x, y = _points_from_counts(KNOWN_COUNTS, XEDGES, YEDGES)
        z = pd.Series(np.where(np.arange(x.size) % 3 == 0, 10.0, 0.0), name="z")
        assert z.unique().size == 2

        h = Hist2D(x, y, z, nbins=[XEDGES, YEDGES])
        projected = h.project_1d("x").agg()

        expected = [
            np.mean(z.values[((lo < x) & (x <= hi)).values])
            for lo, hi in zip(XEDGES[:-1], XEDGES[1:])
        ]
        assert projected.to_numpy() == exact(expected)

    def test_projection_without_z_aggregates_the_other_axis(self):
        """Without z and counts, the x marginal is the mean of y per x-bin.

        The y-values sit in the first and last y-bins and exactly on the top
        edge, which the right-closed last bin ``(0.8, 1.0]`` holds. numpy
        computes each expected mean from the same inputs.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([0.125, 0.125, 0.375, 0.375, 0.625, 0.875, 0.875])
        y = pd.Series([0.1, 1.0, 0.95, 0.3, 0.5, 0.1, 0.7])
        h = Hist2D(x, y, nbins=[XEDGES, YEDGES])

        projected = h.project_1d("x", project_counts=False).agg()

        expected = [
            np.mean(y.values[((lo < x) & (x <= hi)).values])
            for lo, hi in zip(XEDGES[:-1], XEDGES[1:])
        ]
        assert projected.to_numpy() == exact(expected)

    def test_y_outside_the_edges_is_nan_in_the_projection(self):
        """With ``only_plotted=False``, y outside the parent's y-edges is NaN.

        The y-edges ``[0.2, 0.4, 0.6]`` are narrower than the data, so 0.1 and
        0.9 lie outside every y-bin.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([0.125, 0.375, 0.625, 0.875])
        y = pd.Series([0.1, 0.3, 0.5, 0.9])
        h = Hist2D(x, y, nbins=[XEDGES, np.array([0.2, 0.4, 0.6])])

        projected = h.project_1d("x", only_plotted=False)

        expected = [np.nan, 0.3, 0.5, np.nan]  # outside, inside, inside, outside
        assert projected.data.y.to_numpy() == exact(expected, nan_ok=True)

    @pytest.mark.parametrize(
        "y, nbins, expected",
        [
            # Explicit edges give right-closed bins (0.2, 0.4], (0.4, 0.6]:
            # 0.2 is in no bin, 0.6 is in the last one.
            (
                [0.2, 0.3, 0.6, 0.7],
                [XEDGES, np.array([0.2, 0.4, 0.6])],
                [np.nan, 0.3, 0.6, np.nan],
            ),
            # An integer bin count gives numpy's bins [0, 2), [2, 4]: both
            # outer edges are inside.
            ([0.0, 1.0, 2.0, 4.0], 2, [0.0, 1.0, 2.0, 4.0]),
        ],
        ids=["right-closed", "left-closed"],
    )
    def test_projection_keeps_exactly_the_y_values_the_parent_bins(
        self, y, nbins, expected
    ):
        """A y on an outer y-edge is kept exactly when the parent bins it.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([0.125, 0.375, 0.625, 0.875])
        h = Hist2D(x, pd.Series(y), nbins=nbins)

        projected = h.project_1d("x", only_plotted=False)

        assert projected.data.y.to_numpy() == exact(expected, nan_ok=True)

    def test_log_axes_round_trip_through_the_projection(self):
        """A log-log projection stores the caller's x and y and stays log-log.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([2.0, 3.0, 20.0, 50.0])
        y = pd.Series([5.0, 500.0, 50.0, 2000.0])
        h = Hist2D(
            x,
            y,
            logx=True,
            logy=True,
            nbins=[np.array([0.0, 1.0, 2.0]), np.array([0.0, 2.0, 4.0])],
        )

        projected = h.project_1d("x")

        assert projected.log == (True, True)
        assert (10.0**projected.data.x).to_numpy() == exact(x.to_numpy())
        assert projected.data.y.to_numpy() == exact(y.to_numpy())

    def test_count_projection_of_a_linear_histogram_is_linear(self, known_hist):
        """Projected counts of a linear histogram have linear axes.

        ON FAILURE: the code is wrong.
        """
        projected = known_hist.project_1d("x", project_counts=True)
        assert projected.log == (False, False)

    def test_bin_precision_reaches_the_projection(self, known_hist):
        """``bin_precision`` is passed to ``Hist1D``, which rounds the edges.

        numpy rounds the parent's edges to one decimal place for the
        expectation.

        ON FAILURE: the code is wrong.
        """
        projected = known_hist.project_1d("x", project_counts=True, bin_precision=1)
        assert projected.edges["x"].to_numpy() == exact(np.round(XEDGES, 1))

    def test_projection_does_not_clip_an_outlier_into_another_bin(self):
        """An x outlier keeps its bin: the marginal equals the parent's columns.

        Clipping to the 99.99th percentile would move x = 1000 to about 999.1,
        out of the last bin ``(999.5, 1000]`` and into ``(0.5, 999.5]``.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9, 0.95, 1000.0])
        y = pd.Series(0.5, index=x.index)
        xedges = np.array([0.0, 0.5, 999.5, 1000.0])
        h = Hist2D(x, y, nbins=[xedges, np.array([0.0, 1.0])])

        projected = h.project_1d("x", project_counts=True).agg()

        assert projected.to_numpy() == exact([4, 5, 1])  # x-values per x-bin

    @pytest.mark.parametrize("axis, other", [("x", "y"), ("y", "x")])
    def test_projection_carries_the_parent_labels(self, known_hist, axis, other):
        """The projection's x and y labels are the parent's projected and other axes.

        ON FAILURE: the code is wrong.
        """
        known_hist.set_labels(x="speed", y="density")
        projected = known_hist.project_1d(axis, project_counts=False)
        assert projected.labels.x == known_hist.labels._asdict()[axis]
        assert projected.labels.y == known_hist.labels._asdict()[other]

    @pytest.mark.parametrize("axis", ["x", "y"])
    def test_count_projection_labels_y_as_a_count(self, known_hist, axis):
        """Projected counts keep the parent's axis label and label y a Count.

        ON FAILURE: the code is wrong.
        """
        known_hist.set_labels(x="speed", y="density")
        projected = known_hist.project_1d(axis, project_counts=True)
        assert projected.labels.x == known_hist.labels._asdict()[axis]
        assert isinstance(projected.labels.y, Count)

    @pytest.mark.xfail(
        strict=True,
        raises=_ProjectionMovesEdgeSamples,
        reason=(
            "project_1d rebins on the parent's edges as explicit edges, which "
            "AggPlot.calc_bins_intervals (solarwindpy/plotting/agg_plot.py) makes "
            "right-closed, while an integer-nbins parent is left-closed like numpy, "
            "so a sample on an edge changes bin or is dropped; remove this marker "
            "when explicit edges can keep the parent's closure"
        ),
    )
    def test_integer_bin_projection_keeps_samples_on_bin_edges(self):
        """Projected counts of an integer-nbins histogram match numpy.histogram.

        The edges are [0, 2, 4]; samples sit on all three of them.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([0.0, 1.0, 2.0, 3.0, 4.0, 4.0])
        y = pd.Series([0.0, 1.0, 2.0, 3.0, 4.0, 2.0])
        h = Hist2D(x, y, nbins=2)
        assert h.edges["x"].to_numpy() == exact([0.0, 2.0, 4.0])

        projected = h.project_1d("x", project_counts=True).agg().to_numpy()

        expected = np.histogram(x, bins=[0.0, 2.0, 4.0])[0]
        if not np.array_equal(projected, expected):
            raise _ProjectionMovesEdgeSamples(f"{projected} != {expected}")

    def test_unknown_axis_is_rejected(self, known_hist):
        """Only "x" and "y" can be projected.

        ON FAILURE: the code is wrong -- a typo would silently project the
        wrong axis.
        """
        with pytest.raises(AssertionError):
            known_hist.project_1d("z")


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

    def test_columns_with_nothing_above_the_level_are_simply_unlabelled(
        self, known_hist, known_counts
    ):
        """A level above a column's maximum leaves that column's points NaN.

        The docstring already says what should happen: "NaN are observations
        that are below `level`".

        ON FAILURE: the code is wrong.
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
        with pytest.raises(ValueError, match="Need bottom < top"):
            known_hist.take_data_in_yrange_across_x(
                ranges,
                lambda key, expected_logx=False: (key.left, key.right),
                lambda row, expected_logy=False: (row.bottom, row.top),
            )

    @pytest.mark.parametrize(
        "get_x_bounds, get_y_bounds, match",
        [
            (
                lambda key, expected_logx: (key.left, key.left),
                lambda row, expected_logy: (0.0, 1.0),
                "Need left < right",
            ),
            (
                lambda key, expected_logx: (key.left, key.right),
                lambda row, expected_logy: (0.5, 0.5),
                "Need bottom < top",
            ),
        ],
        ids=["x", "y"],
    )
    def test_zero_width_ranges_are_rejected(
        self, known_hist, get_x_bounds, get_y_bounds, match
    ):
        """A range of zero width is a ValueError, not an empty selection.

        ON FAILURE: the code is wrong.
        """
        columns = known_hist.agg().unstack("x").columns
        ranges = pd.DataFrame({"bottom": 0.0, "top": 1.0}, index=columns)
        with pytest.raises(ValueError, match=match):
            known_hist.take_data_in_yrange_across_x(ranges, get_x_bounds, get_y_bounds)

    @pytest.mark.parametrize("logx, logy", [(True, False), (False, True)])
    def test_callbacks_receive_the_log_flags_as_bools(self, logx, logy):
        """Each callback gets its axis's log flag, as a bool, by keyword.

        The two axes differ in each case, so swapped flags fail too.

        ON FAILURE: the code is wrong.
        """
        values = pd.Series([1.0, 10.0, 100.0, 1000.0])
        h = Hist2D(values, values[::-1].reset_index(drop=True), logx=logx, logy=logy)
        ranges = pd.DataFrame(
            {"bottom": -np.inf, "top": np.inf}, index=h.agg().unstack("x").columns
        )
        x_flags, y_flags = [], []

        def get_x_bounds(key, **flags):
            x_flags.append(flags)
            return key.left, key.right

        def get_y_bounds(row, **flags):
            y_flags.append(flags)
            return row.bottom, row.top

        h.take_data_in_yrange_across_x(ranges, get_x_bounds, get_y_bounds)

        assert x_flags == [{"expected_logx": logx}] * ranges.shape[0]
        assert y_flags == [{"expected_logy": logy}] * ranges.shape[0]
        assert all(type(f["expected_logx"]) is bool for f in x_flags)
        assert all(type(f["expected_logy"]) is bool for f in y_flags)

    def test_range_bounds_are_open_below_and_closed_above(self):
        """A point is taken when left < x <= right and bottom < y <= top.

        Integer data on a grid put points exactly on all four bounds.

        ON FAILURE: the code is wrong.
        """
        xx, yy = np.meshgrid(np.arange(5.0), np.arange(5.0))
        x, y = pd.Series(xx.ravel()), pd.Series(yy.ravel())
        h = Hist2D(x, y, nbins=[np.array([1.0, 3.0]), np.array([-1.0, 5.0])])
        ranges = pd.DataFrame(
            {"bottom": [1.0], "top": [3.0]}, index=h.agg().unstack("x").columns
        )

        taken = h.take_data_in_yrange_across_x(
            ranges,
            lambda key, expected_logx: (key.left, key.right),
            lambda row, expected_logy: (row.bottom, row.top),
        )

        expected = np.flatnonzero((1 < x) & (x <= 3) & (1 < y) & (y <= 3))
        np.testing.assert_array_equal(taken, expected)


def _contour_levels(hist, levels=None):
    """Levels of the contour set ``plot_contours`` draws for ``hist``."""
    fig, ax = plt.subplots()
    try:
        *_, qset = hist.plot_contours(ax=ax, cbar=False, levels=levels)
        return np.asarray(qset.levels, dtype=float)
    finally:
        plt.close(fig)


class TestDefaultContourLevels:
    """Properties the default levels must have, rather than their literal values.

    The literal defaults are editorial choices with no derivation available, so
    only what must be true of any admissible choice is asserted. Levels are
    read from the contour set ``plot_contours`` returns.
    """

    @pytest.mark.parametrize("axnorm", ["t", "d", "c", "r"])
    def test_defaults_are_strictly_increasing(self, known_hist, axnorm):
        """Contour levels must increase; matplotlib requires it.

        ON FAILURE: the code is wrong.
        """
        known_hist.set_axnorm(axnorm)
        assert np.all(np.diff(_contour_levels(known_hist)) > 0)

    @pytest.mark.parametrize("axnorm", ["t", "c", "r"])
    def test_defaults_lie_inside_the_normalised_range(self, known_hist, axnorm):
        """For a normalisation bounded by 1, no level may exceed 1.

        Total/column/row normalisation divide by a maximum, so every value is in
        [0, 1]; a level outside that range could never be drawn.

        ON FAILURE: the code is wrong.
        """
        known_hist.set_axnorm(axnorm)
        levels = _contour_levels(known_hist)
        assert levels.min() >= 0.0
        assert levels.max() <= 1.0

    def test_explicit_levels_are_passed_through_untouched(self, known_hist):
        """Caller-supplied levels override the defaults for every axnorm.

        ON FAILURE: the code is wrong.
        """
        requested = [0.05, 0.25, 0.75]
        for axnorm in (None, "t", "d", "c", "r", "cd", "rd"):
            known_hist.set_axnorm(axnorm)
            assert _contour_levels(known_hist, requested).tolist() == requested

    def test_no_default_without_a_normalisation(self, known_hist):
        """Unnormalised counts get matplotlib's levels, on the scale of the counts.

        ``KNOWN_COUNTS`` runs to 6, so automatic levels reach past 1; any of the
        fixed default lists (all at most 1) would not.

        ON FAILURE: the code is wrong -- a fixed level list cannot suit
        arbitrary raw counts.
        """
        known_hist.set_axnorm(None)
        assert _contour_levels(known_hist).max() > 1.0


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
        ax, cbar, qset = known_hist.plot_hist_with_contours(cbar=False, norm=requested)

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
        )[2]
        nan_aware = complete_hist.plot_contours(
            gaussian_filter_std=1.5,
            nan_aware_filter=True,
            cbar=False,
        )[2]

        assert len(plain.allsegs) == len(nan_aware.allsegs)
        for at_plain, at_nan_aware in zip(plain.allsegs, nan_aware.allsegs):
            assert len(at_plain) == len(at_nan_aware)
            for left, right in zip(at_plain, at_nan_aware):
                np.testing.assert_allclose(left, right)
        plt.close("all")


class TestNoContourLabels:
    """The contour plots draw no labels and accept no labelling keywords."""

    @pytest.mark.parametrize("method", ["plot_contours", "plot_hist_with_contours"])
    @pytest.mark.parametrize(
        "keyword", ["label_levels", "clabel_kwargs", "skip_max_clbl"]
    )
    def test_removed_labelling_keywords_are_rejected(self, known_hist, method, keyword):
        """A removed labelling keyword fails loudly instead of being ignored.

        Both methods forward unknown keywords to matplotlib (`ax.contour` or
        `ax.pcolormesh`), whose `Artist.set` raises `AttributeError` naming
        the keyword.

        ON FAILURE: the code is wrong -- a contour method accepts a labelling
        keyword again, or swallows unknown keywords silently.
        """
        known_hist.set_axnorm("t")
        with pytest.raises(AttributeError, match=keyword):
            getattr(known_hist, method)(cbar=False, **{keyword: True})
        plt.close("all")

    def test_filled_contours_emit_no_matplotlib_deprecation_warning(self, known_hist):
        """A filled-contour plot draws no text and triggers no deprecation.

        Matplotlib deprecated `clabel` on filled contours in 3.11; labelling
        `contourf` output emitted `MatplotlibDeprecationWarning`.

        ON FAILURE: the code is wrong -- something labels the filled contours
        again, or calls another deprecated matplotlib API.
        """
        known_hist.set_axnorm("t")
        with warnings.catch_warnings():
            warnings.simplefilter("error", matplotlib.MatplotlibDeprecationWarning)
            ax, _, qset = known_hist.plot_contours(
                use_contourf=True, cbar=False, levels=[0.1, 0.3, 0.5, 0.7]
            )
        assert qset.filled is True
        assert len(ax.texts) == 0
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


class TestAxnormKeys:
    """``axnorm`` is one of the string keys documented in ``set_axnorm``."""

    def test_set_axnorm_rejects_a_tuple(self, known_hist):
        """A ``(kind, fcn)`` tuple is not an axnorm key and is refused.

        The refusal is a deliberate ``TypeError`` naming the type, not an
        accident of calling a string method on a tuple.

        ON FAILURE: the code is wrong, unless the author has made tuple axnorm
        a feature.
        """
        with pytest.raises(
            TypeError, match="axnorm must be a string or None; got tuple"
        ):
            known_hist.set_axnorm(("c", "max"))

    @pytest.mark.parametrize("bad", ["x", "total", "column", "cdx"])
    def test_unknown_axnorm_is_a_value_error(self, known_hist, bad):
        """An unknown key raises ``ValueError`` listing every accepted key.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(
            ValueError,
            match=(f"Unrecognized axnorm '{bad}'; expected one of: c, r, t, d, cd, rd"),
        ):
            known_hist.set_axnorm(bad)

    def test_axnorm_match_is_case_insensitive(self, known_hist):
        """``set_axnorm("CD")`` is stored as the lowercase key "cd".

        ON FAILURE: the code is wrong.
        """
        known_hist.set_axnorm("CD")
        assert known_hist.axnorm == "cd"

    def test_validation_survives_python_optimize(self):
        """Invalid axnorm is refused under ``python -O``, which strips asserts.

        A subprocess run with ``-O`` passes unknown keys to Hist1D and Hist2D;
        each must raise set_axnorm's own ``ValueError``. Hist1D gets "c" and
        "density", keys the ``Count`` label accepts (after truncation, for
        "density"), so a missing check cannot hide behind the label rejecting
        the key further downstream.

        ON FAILURE: the code is wrong -- validation relies on ``assert``.
        """
        # The bare ``assert False`` proves -O is in effect: without -O it fires
        # and the script exits non-zero before reaching set_axnorm.
        script = textwrap.dedent("""
            import matplotlib
            matplotlib.use("Agg")
            import pandas as pd
            from solarwindpy.plotting.hist1d import Hist1D
            from solarwindpy.plotting.hist2d import Hist2D

            assert False, "python -O did not strip asserts"
            x = pd.Series([0.5, 1.5, 3.0])
            y = pd.Series([1.5, 2.5, 0.5])
            cases = [(Hist1D(x), "c"), (Hist1D(x), "density"), (Hist2D(x, y), "bogus")]
            for hist, key in cases:
                try:
                    hist.set_axnorm(key)
                except ValueError as err:
                    if str(err).startswith(f"Unrecognized axnorm '{key}'"):
                        continue
                    raise
                raise SystemExit(f"{type(hist).__name__} accepted {key!r}")
            """)
        result = subprocess.run(
            [sys.executable, "-O", "-c", script], capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr + result.stdout


if __name__ == "__main__":
    pytest.main([__file__])
