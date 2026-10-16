#!/usr/bin/env python
"""Tests for ``solarwindpy.plotting.agg_plot.AggPlot``.

``AggPlot`` is abstract; its behaviour is exercised through the real public
subclasses ``Hist1D`` and ``Hist2D`` built from chosen inputs. Expected values
come from numpy (``histogram_bin_edges``, ``histogram``, ``histogram2d``,
``digitize``, ``quantile``, ``clip``), ``scipy.stats.binned_statistic_2d``,
``astropy.stats.knuth_bin_width``, and hand computations.

Edges from an integer ``nbins`` follow ``numpy.histogram``: the outer edges
enclose every sample and the bins are closed on the left, the last also on the
right (``tests/plotting/test_hist2d_plotting.py``, ``test_edges_span_the_data``,
``test_auto_bins_retain_every_observation``). Explicit edges give right-closed
bins, so tests here that count observations use explicit edges that bracket
the data. An ``IntervalIndex`` keeps the side its bins close on.
"""

import numpy as np
import pandas as pd
import pytest
from scipy.stats import binned_statistic_2d

from solarwindpy.plotting.hist1d import Hist1D
from solarwindpy.plotting.hist2d import Hist2D
from tests.tolerances import exact

# Non-square grid (4 x-bins, 3 y-bins) so a transposed result cannot pass.
X_EDGES = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
Y_EDGES = np.array([0.0, 2.0, 4.0, 6.0])
N = 200


@pytest.fixture
def xyz():
    """Continuous x, y inside the explicit edges, and a varying z.

    Uniform draws land exactly on an edge with probability zero.
    """
    rng = np.random.default_rng(20260929)
    x = pd.Series(rng.uniform(0.0, 4.0, N))
    y = pd.Series(rng.uniform(0.0, 6.0, N))
    z = pd.Series(rng.normal(10.0, 3.0, N))
    return x, y, z


def _grid(agg, x_edges, y_edges):
    """Lay a (x-interval, y-interval) Series out as a 2-D array, NaN where absent."""
    out = np.full((x_edges.size - 1, y_edges.size - 1), np.nan)
    for (ix, iy), v in agg.items():
        i = np.searchsorted(x_edges, ix.left)
        j = np.searchsorted(y_edges, iy.left)
        out[i, j] = v
    return out


def _bin_index(values, edges):
    """0-based bin of each value for data strictly inside the edges."""
    return np.digitize(values, edges) - 1


# ---------------------------------------------------------------------------
# Bin edges: calc_bins_intervals, edges, intervals
# ---------------------------------------------------------------------------


class TestBinEdges:
    """``calc_bins_intervals`` turns ``nbins`` into edges and intervals per axis."""

    def test_integer_nbins_gives_equal_width_edges_over_the_data(self):
        """nbins=4 over x in [0, 8] and y in [-1, 3] gives steps of 2 and 1.

        Hand-computed, and equal to numpy.histogram_bin_edges.
        ON FAILURE: the code is wrong.
        """
        x = pd.Series([0.0, 1.0, 3.0, 5.0, 8.0])
        y = pd.Series([-1.0, 0.0, 1.0, 2.0, 3.0])
        h = Hist2D(x, y, nbins=4)
        np.testing.assert_array_equal(h.edges["x"], [0.0, 2.0, 4.0, 6.0, 8.0])
        np.testing.assert_array_equal(h.edges["y"], [-1.0, 0.0, 1.0, 2.0, 3.0])
        np.testing.assert_array_equal(h.edges["x"], np.histogram_bin_edges(x, 4))

    def test_one_nbins_per_axis(self):
        """``nbins=(2, 8)`` gives x steps of 4 and y steps of 0.5.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([0.0, 1.0, 3.0, 5.0, 8.0])
        y = pd.Series([-1.0, 0.0, 1.0, 2.0, 3.0])
        h = Hist2D(x, y, nbins=(2, 8))
        np.testing.assert_array_equal(h.edges["x"], [0.0, 4.0, 8.0])
        np.testing.assert_array_equal(h.edges["y"], np.arange(-1.0, 3.01, 0.5))

    def test_string_rule_is_case_insensitive_and_handed_to_numpy(self, xyz):
        """``nbins="Sturges"`` gives numpy's "sturges" edges, rounded to 5 places.

        ON FAILURE: the code is wrong.
        """
        x, y, _ = xyz
        h = Hist2D(x, y, nbins="Sturges")
        expected = np.histogram_bin_edges(x, "sturges").round(5)
        np.testing.assert_array_equal(h.edges["x"], expected)

    def test_knuth_rule_uses_astropy(self, xyz):
        """``nbins="knuth"`` gives astropy's Knuth-rule edges, rounded to 5 places.

        ON FAILURE: the code is wrong.
        """
        astropy_stats = pytest.importorskip("astropy.stats")
        x, _, _ = xyz
        h = Hist1D(x, nbins="knuth")
        _, bins = astropy_stats.knuth_bin_width(x, return_bins=True)
        np.testing.assert_array_equal(h.edges["x"], bins.round(5))

    def test_explicit_edges_are_used_as_given(self, xyz):
        """An array of edges is used unchanged.

        ON FAILURE: the code is wrong.
        """
        x, _, _ = xyz
        h = Hist1D(x, nbins=X_EDGES)
        np.testing.assert_array_equal(h.edges["x"], X_EDGES)

    @pytest.mark.parametrize(
        "precision, expected",
        [(None, [0.0, 0.33333, 0.66667, 1.0]), (2, [0.0, 0.33, 0.67, 1.0])],
    )
    def test_edges_are_rounded_to_bin_precision(self, precision, expected):
        """Thirds of [0, 1] round to 5 places by default, or to ``bin_precision``.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([0.0, 0.5, 1.0])
        h = Hist1D(x, nbins=3, bin_precision=precision)
        np.testing.assert_array_equal(h.edges["x"], expected)

    def test_non_finite_values_do_not_move_the_edges(self):
        """NaN and +-inf are ignored when the edges are computed.

        Edges over the finite values [0, 2, 4] with nbins=2 are [0, 2, 4].
        ON FAILURE: the code is wrong.
        """
        x = pd.Series([0.0, 2.0, 4.0, np.inf, -np.inf, np.nan])
        h = Hist1D(x, nbins=2)
        np.testing.assert_array_equal(h.edges["x"], [0.0, 2.0, 4.0])

    def test_interval_index_keeps_the_bins_it_was_built_from(self):
        """An integer-nbins histogram's intervals rebuild its left-closed bins.

        Samples sit on all three edges [0, 2, 4]; numpy.histogram counts them.
        ON FAILURE: the code is wrong.
        """
        x = pd.Series([0.0, 1.0, 2.0, 3.0, 4.0, 4.0])
        parent = Hist1D(x, nbins=2)

        rebuilt = Hist1D(x, nbins=parent.intervals["x"])

        assert rebuilt.intervals["x"].equals(parent.intervals["x"])
        expected = np.histogram(x, bins=[0.0, 2.0, 4.0])[0]
        assert rebuilt.agg().to_numpy() == exact(expected.astype(float))

    def test_right_closed_interval_index_keeps_its_bins(self):
        """A right-closed IntervalIndex bins on (0, 2], (2, 4].

        Samples sit on all three edges: x = 0 is in no bin, x = 2 is in the
        first (hand count).
        ON FAILURE: the code is wrong.
        """
        x = pd.Series([0.0, 1.0, 2.0, 3.0, 4.0, 4.0])
        given = pd.IntervalIndex.from_breaks([0.0, 2.0, 4.0], closed="right")

        h = Hist1D(x, nbins=given)

        assert h.intervals["x"].equals(given)
        assert h.agg().to_numpy() == exact([2.0, 3.0])

    def test_interval_index_edges_are_not_rounded_by_default(self):
        """Without ``bin_precision``, an IntervalIndex keeps edges finer than 5 places.

        ON FAILURE: the code is wrong.
        """
        given = pd.IntervalIndex.from_breaks([0.0, 0.1234567, 1.0])

        h = Hist1D(pd.Series([0.05, 0.5]), nbins=given)

        assert h.edges["x"].to_numpy() == exact([0.0, 0.1234567, 1.0])

    def test_hist2d_takes_one_interval_index_per_axis(self):
        """Each axis keeps its own IntervalIndex and closure.

        x bins [0, 2), [2, 4]; y bins (0, 2], (2, 4]. Hand count of the points
        (0, 0) dropped (y = 0 is in no y-bin), (1, 1), (2, 2), (3, 3), (4, 4),
        (4, 2): one in the first x-bin, two and two in the second.
        ON FAILURE: the code is wrong.
        """
        x = pd.Series([0.0, 1.0, 2.0, 3.0, 4.0, 4.0])
        y = pd.Series([0.0, 1.0, 2.0, 3.0, 4.0, 2.0])
        edges = np.array([0.0, 2.0, 4.0])
        ix = pd.IntervalIndex.from_breaks(edges, closed="left")
        iy = pd.IntervalIndex.from_breaks(edges, closed="right")

        h = Hist2D(x, y, nbins=(ix, iy))

        assert h.intervals["x"].equals(ix)
        assert h.intervals["y"].equals(iy)
        expected = np.array([[1.0, np.nan], [2.0, 2.0]])  # hand count, rows x-bins
        assert _grid(h.agg(), edges, edges) == exact(expected, nan_ok=True)

    @pytest.mark.parametrize(
        "given, match",
        [
            (pd.IntervalIndex.from_tuples([(0.0, 1.0), (2.0, 3.0)]), "contiguous"),
            (pd.IntervalIndex.from_tuples([(2.0, 4.0), (0.0, 2.0)]), "contiguous"),
            (pd.IntervalIndex.from_breaks([], closed="right"), "contiguous"),
            (pd.IntervalIndex.from_breaks([0.0, 1.0], closed="both"), "'both'"),
            (pd.IntervalIndex.from_breaks([0.0, 1.0], closed="neither"), "'neither'"),
        ],
        ids=["gap", "non-monotonic", "empty", "closed-both", "closed-neither"],
    )
    def test_interval_index_that_is_not_a_set_of_bins_is_rejected(self, given, match):
        """Only contiguous, increasing, non-empty, left- or right-closed intervals bin.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(ValueError, match=match):
            Hist1D(pd.Series([0.5, 2.5]), nbins=given)

    def test_intervals_run_between_consecutive_edges(self, xyz):
        """Interval k spans edges[k] to edges[k + 1] on each axis.

        ON FAILURE: the code is wrong.
        """
        x, y, _ = xyz
        h = Hist2D(x, y, nbins=[X_EDGES, Y_EDGES])
        for name, edges in (("x", X_EDGES), ("y", Y_EDGES)):
            iv = h.intervals[name]
            np.testing.assert_array_equal(iv.left, edges[:-1])
            np.testing.assert_array_equal(iv.right, edges[1:])
            assert list(h.categoricals[name]) == list(iv)


# ---------------------------------------------------------------------------
# make_cut and clipping
# ---------------------------------------------------------------------------


class TestCut:
    """``make_cut`` assigns each observation to the interval that contains it."""

    def test_each_observation_gets_the_interval_containing_it(self, xyz):
        """The cut interval of each point is the numpy.digitize bin of that point.

        ON FAILURE: the code is wrong.
        """
        x, y, _ = xyz
        h = Hist2D(x, y, nbins=[X_EDGES, Y_EDGES])
        for name, values, edges in (("x", x, X_EDGES), ("y", y, Y_EDGES)):
            left = h.cut[name].map(lambda iv: iv.left).astype(float)
            expected_left = edges[_bin_index(values.to_numpy(), edges)]
            np.testing.assert_array_equal(left.to_numpy(), expected_left)
            assert h.cut.index.equals(h.data.index)

    @pytest.mark.parametrize(
        "clip, expected_right",
        [(False, 1001.0), (True, 999.5)],
        ids=["unclipped", "clipped"],
    )
    def test_clip_data_moves_an_outlier_to_the_bin_of_its_clipped_value(
        self, clip, expected_right
    ):
        """``clip_data=True`` bins the outlier at its 99.99th-percentile value.

        x = 0..9 and 1000: numpy's linear quantile at 0.9999 sits at position
        9.999, so 9 + 0.999 * 991 = 999.009, which is in (5, 999.5]; unclipped,
        1000 is in (999.5, 1001]. The two parametrizations are the fixture
        check: they differ only in clipping.
        ON FAILURE: the code is wrong.
        """
        x = pd.Series(np.r_[np.arange(10.0), 1000.0])
        h = Hist1D(x, clip_data=clip, nbins=[-1.0, 5.0, 999.5, 1001.0])
        assert h.cut["x"].iloc[-1].right == expected_right
        assert np.quantile(x, 0.9999) == exact(999.009)


# ---------------------------------------------------------------------------
# agg, clim, alim
# ---------------------------------------------------------------------------


class TestAgg:
    """``agg`` groups the aggregated column by the cut intervals."""

    def test_counts_match_numpy_histogram2d(self, xyz):
        """Without z, each bin holds the number of points in it.

        ON FAILURE: the code is wrong.
        """
        x, y, _ = xyz
        h = Hist2D(x, y, nbins=[X_EDGES, Y_EDGES])
        expected, _, _ = np.histogram2d(x, y, bins=[X_EDGES, Y_EDGES])
        got = np.nan_to_num(_grid(h.agg(), X_EDGES, Y_EDGES), nan=0.0)
        np.testing.assert_array_equal(got, expected)
        assert got.sum() == N

    def test_1d_counts_match_numpy_histogram(self, xyz):
        """Hist1D without y counts the points in each x bin.

        ON FAILURE: the code is wrong.
        """
        x, _, _ = xyz
        h = Hist1D(x, nbins=X_EDGES)
        expected, _ = np.histogram(x, bins=X_EDGES)
        np.testing.assert_array_equal(h.agg().to_numpy(), expected)

    def test_varying_z_is_averaged_per_bin(self, xyz):
        """With a varying z the default aggregate is the mean of z in each bin.

        ON FAILURE: the code is wrong.
        """
        x, y, z = xyz
        h = Hist2D(x, y, z, nbins=[X_EDGES, Y_EDGES])
        expected = binned_statistic_2d(
            x, y, z, statistic="mean", bins=[X_EDGES, Y_EDGES]
        ).statistic
        assert np.asarray(_grid(h.agg(), X_EDGES, Y_EDGES)) == exact(expected)

    def test_constant_z_is_counted_not_averaged(self, xyz):
        """A z with one unique value is counted, per the ``agg`` docstring.

        z = 7 everywhere gives the counts, not 7.
        ON FAILURE: the code is wrong.
        """
        x, y, _ = xyz
        z = pd.Series(7.0, index=x.index)
        h = Hist2D(x, y, z, nbins=[X_EDGES, Y_EDGES])
        expected, _, _ = np.histogram2d(x, y, bins=[X_EDGES, Y_EDGES])
        got = np.nan_to_num(_grid(h.agg(), X_EDGES, Y_EDGES), nan=0.0)
        np.testing.assert_array_equal(got, expected)

    @pytest.mark.parametrize("fcn", ["median", "max", "std"])
    def test_fcn_selects_the_aggregate(self, xyz, fcn):
        """``agg(fcn=...)`` aggregates with that function.

        Compared to scipy's binned_statistic_2d; std uses ddof=1 as pandas does.
        ON FAILURE: the code is wrong.
        """
        x, y, z = xyz
        h = Hist2D(x, y, z, nbins=[X_EDGES, Y_EDGES])
        statistic = {
            "median": "median",
            "max": "max",
            "std": lambda v: np.std(v, ddof=1),
        }[fcn]
        expected = binned_statistic_2d(
            x, y, z, statistic=statistic, bins=[X_EDGES, Y_EDGES]
        ).statistic
        assert np.asarray(_grid(h.agg(fcn=fcn), X_EDGES, Y_EDGES)) == exact(expected)

    @pytest.mark.parametrize(
        "clim, keep",
        [
            ((12, None), lambda c: c >= 12),
            ((None, 16), lambda c: c <= 16),
            ((12, 16), lambda c: (c >= 12) & (c <= 16)),
        ],
    )
    def test_clim_masks_bins_by_their_count(self, xyz, clim, keep):
        """Bins whose count is outside ``clim`` become NaN; the rest keep their mean.

        Limits 12 and 16 sit inside this fixture's range of counts, so both
        kinds of bin occur (asserted).
        ON FAILURE: the code is wrong.
        """
        x, y, z = xyz
        h = Hist2D(x, y, z, nbins=[X_EDGES, Y_EDGES])
        h.set_clim(*clim)
        counts, _, _ = np.histogram2d(x, y, bins=[X_EDGES, Y_EDGES])
        means = binned_statistic_2d(
            x, y, z, statistic="mean", bins=[X_EDGES, Y_EDGES]
        ).statistic
        kept = keep(counts)
        assert kept.any() and not kept.all()
        expected = np.where(kept, means, np.nan)
        assert np.asarray(_grid(h.agg(), X_EDGES, Y_EDGES)) == exact(
            expected, nan_ok=True
        )
        assert h.clim == clim

    def test_alim_masks_bins_by_their_aggregated_value(self, xyz):
        """Bins whose mean z lies outside ``alim`` become NaN.

        The limits are the 25th and 75th percentiles of the bin means, so both
        kinds of bin occur.
        ON FAILURE: the code is wrong.
        """
        x, y, z = xyz
        h = Hist2D(x, y, z, nbins=[X_EDGES, Y_EDGES])
        means = binned_statistic_2d(
            x, y, z, statistic="mean", bins=[X_EDGES, Y_EDGES]
        ).statistic
        lo, hi = np.nanpercentile(means, [25, 75])
        h.set_alim(lo, hi)
        expected = np.where((means >= lo) & (means <= hi), means, np.nan)
        assert np.asarray(_grid(h.agg(), X_EDGES, Y_EDGES)) == exact(
            expected, nan_ok=True
        )
        assert h.alim == (lo, hi)

    @pytest.mark.parametrize("setter", ["set_clim", "set_alim"])
    @pytest.mark.parametrize(
        "limits", [("2", None), (None, "9"), ([1, 2], None)], ids=str
    )
    def test_limits_must_be_numbers_or_none(self, xyz, setter, limits):
        """A non-numeric limit is rejected.

        ON FAILURE: the code is wrong.
        """
        x, y, _ = xyz
        h = Hist2D(x, y, nbins=[X_EDGES, Y_EDGES])
        with pytest.raises((AssertionError, TypeError, ValueError)):
            getattr(h, setter)(*limits)

    def test_agg_axes_is_the_one_column_not_binned(self, xyz):
        """Hist2D aggregates z over (x, y); Hist1D aggregates y over x.

        ON FAILURE: the code is wrong.
        """
        x, y, z = xyz
        assert Hist2D(x, y, z, nbins=[X_EDGES, Y_EDGES]).agg_axes == "z"
        assert Hist1D(x, y, nbins=X_EDGES).agg_axes == "y"

    def test_joint_is_the_aggregated_column_indexed_by_its_bins(self, xyz):
        """``joint`` holds each z under its (x, y) intervals; groups size to counts.

        ON FAILURE: the code is wrong.
        """
        x, y, z = xyz
        h = Hist2D(x, y, z, nbins=[X_EDGES, Y_EDGES])
        joint = h.joint
        np.testing.assert_array_equal(joint.to_numpy(), z.to_numpy())
        for name in ("x", "y"):
            assert list(joint.index.get_level_values(name)) == list(h.cut[name])
        counts, _, _ = np.histogram2d(x, y, bins=[X_EDGES, Y_EDGES])
        sizes = np.nan_to_num(_grid(h.grouped.size(), X_EDGES, Y_EDGES), nan=0.0)
        np.testing.assert_array_equal(sizes, counts)


# ---------------------------------------------------------------------------
# Selecting the observations behind the plot
# ---------------------------------------------------------------------------


class SelectedPointInDroppedBin(AssertionError):
    """A point whose own (x, y) bin was dropped is still selected."""


def _count_of_own_bin(x, y):
    """Count of the (x, y) bin each point falls in, from numpy.histogram2d."""
    counts, _, _ = np.histogram2d(x, y, bins=[X_EDGES, Y_EDGES])
    return counts[_bin_index(x.to_numpy(), X_EDGES), _bin_index(y.to_numpy(), Y_EDGES)]


def _selected_by_axis_alone(x, y, keep_bin):
    """Points whose x-bin and y-bin each host some kept (x, y) bin."""
    keep_x = keep_bin.any(axis=1)[_bin_index(x.to_numpy(), X_EDGES)]
    keep_y = keep_bin.any(axis=0)[_bin_index(y.to_numpy(), Y_EDGES)]
    return keep_x & keep_y


class TestSelection:
    """Masks and subsets that map aggregated bins back to observations."""

    CLIM = 12
    THRESHOLD = 14

    def test_fixture_has_points_that_only_axis_by_axis_selection_keeps(self, xyz):
        """Some points sit in a dropped bin whose x-bin and y-bin both survive.

        Computed with numpy alone, for count >= CLIM and >= THRESHOLD.
        ON FAILURE: the fixture no longer separates joint-bin selection from
        axis-by-axis selection; fix the fixture.
        """
        x, y, _ = xyz
        counts, _, _ = np.histogram2d(x, y, bins=[X_EDGES, Y_EDGES])
        for limit in (self.CLIM, self.THRESHOLD):
            keep = counts >= limit
            joint = keep[
                _bin_index(x.to_numpy(), X_EDGES), _bin_index(y.to_numpy(), Y_EDGES)
            ]
            marginal = _selected_by_axis_alone(x, y, keep)
            assert (marginal & ~joint).any()
            assert joint.any()

    def test_plotted_mask_marks_every_point_in_a_bin_that_survives_clim(self, xyz):
        """With clim (12, None), every point in a bin of >= 12 points is plotted.

        ON FAILURE: the code is wrong.
        """
        x, y, _ = xyz
        h = Hist2D(x, y, nbins=[X_EDGES, Y_EDGES])
        h.set_clim(self.CLIM, None)
        mask = h.get_plotted_data_boolean_series()
        assert mask.index.equals(h.data.index)
        assert mask[_count_of_own_bin(x, y) >= self.CLIM].all()

    def test_plotted_mask_excludes_points_in_bins_dropped_by_clim(self, xyz):
        """With clim (12, None), no point in a bin of < 12 points is plotted.

        ON FAILURE: the code is wrong.
        """
        x, y, _ = xyz
        h = Hist2D(x, y, nbins=[X_EDGES, Y_EDGES])
        h.set_clim(self.CLIM, None)
        mask = h.get_plotted_data_boolean_series().to_numpy()
        dropped = _count_of_own_bin(x, y) < self.CLIM
        if mask[dropped].any():
            raise SelectedPointInDroppedBin(f"{mask[dropped].sum()} points")

    def test_subset_above_threshold_holds_every_row_in_a_dense_bin(self, xyz):
        """Every row whose bin count is >= 14 is in the subset, unchanged.

        ON FAILURE: the code is wrong.
        """
        x, y, z = xyz
        h = Hist2D(x, y, z, nbins=[X_EDGES, Y_EDGES])
        subset, mask = h.get_subset_above_threshold(self.THRESHOLD)
        dense = _count_of_own_bin(x, y) >= self.THRESHOLD
        assert mask[dense].all()
        pd.testing.assert_frame_equal(subset, h.data.loc[mask])
        expected = pd.DataFrame({"x": x, "y": y, "z": z})[dense]
        pd.testing.assert_frame_equal(subset.loc[expected.index], expected)

    def test_subset_above_threshold_excludes_rows_in_sparse_bins(self, xyz):
        """No row whose bin count is < 14 is in the subset.

        ON FAILURE: the code is wrong.
        """
        x, y, z = xyz
        h = Hist2D(x, y, z, nbins=[X_EDGES, Y_EDGES])
        subset, mask = h.get_subset_above_threshold(self.THRESHOLD)
        sparse = _count_of_own_bin(x, y) < self.THRESHOLD
        if mask.to_numpy()[sparse].any():
            raise SelectedPointInDroppedBin(f"{mask.to_numpy()[sparse].sum()} rows")

    def test_1d_plotted_mask_follows_clim(self, xyz):
        """In 1-D a point is plotted iff its x bin holds >= 52 points.

        np.histogram counts over X_EDGES straddle 52 for this fixture (asserted).
        ON FAILURE: the code is wrong.
        """
        x, _, _ = xyz
        counts, _ = np.histogram(x, bins=X_EDGES)
        expected = (counts >= 52)[_bin_index(x.to_numpy(), X_EDGES)]
        assert 0 < expected.sum() < N
        h = Hist1D(x, nbins=X_EDGES)
        h.set_clim(52, None)
        mask = h.get_plotted_data_boolean_series()
        np.testing.assert_array_equal(mask.to_numpy(), expected)

    def test_1d_subset_above_threshold_keeps_rows_in_dense_bins(self, xyz):
        """In 1-D the subset is the rows whose x bin holds >= 52 points.

        ON FAILURE: the code is wrong.
        """
        x, _, _ = xyz
        counts, _ = np.histogram(x, bins=X_EDGES)
        expected = (counts >= 52)[_bin_index(x.to_numpy(), X_EDGES)]
        h = Hist1D(x, nbins=X_EDGES)
        subset, mask = h.get_subset_above_threshold(52)
        np.testing.assert_array_equal(mask.to_numpy(), expected)
        np.testing.assert_array_equal(subset["x"].to_numpy(), x.to_numpy()[expected])

    def test_subset_above_threshold_returns_linear_values_for_log_axes(self, xyz):
        """With log axes the subset holds x and y in linear units again.

        ON FAILURE: the code is wrong.
        """
        x, y, _ = xyz
        x, y = 10.0**x, 10.0**y
        h = Hist2D(x, y, logx=True, logy=True, nbins=[X_EDGES, Y_EDGES])
        subset, mask = h.get_subset_above_threshold(1)
        assert mask.all()
        assert np.asarray(subset["x"]) == exact(x)
        assert np.asarray(subset["y"]) == exact(y)
        # The histogram's own data stay log10 values: only the subset changed.
        assert np.asarray(h.data["x"]) == exact(np.log10(x))
        assert np.asarray(h.data["y"]) == exact(np.log10(y))


# ---------------------------------------------------------------------------
# nbins validation, outward rounding, and the out-of-memory fallback
# ---------------------------------------------------------------------------


class TestNbinsAndEdges:
    """How ``calc_bins_intervals`` reads ``nbins`` and places the outer edges."""

    def test_numpy_integer_nbins_counts_bins_like_a_python_integer(self, xyz):
        """``np.int64(4)`` and ``np.int32(4)`` give the edges ``4`` gives.

        ON FAILURE: the code is wrong.
        """
        x, y, _ = xyz
        expected = Hist2D(x, y, nbins=4).edges
        for nbins in (np.int64(4), np.int32(4)):
            got = Hist2D(x, y, nbins=nbins).edges
            for axis in ("x", "y"):
                assert got[axis].equals(expected[axis])
        assert Hist1D(x, nbins=np.int64(3)).edges["x"].size == 4

    @pytest.mark.parametrize(
        "nbins, type_name", [(3.5, "float"), (None, "NoneType"), (True, "bool")]
    )
    def test_unusable_nbins_raise_value_error_naming_it(self, xyz, nbins, type_name):
        """A float, None or a bool is not a bin specification: ``ValueError``.

        ON FAILURE: the code is wrong.
        """
        x, _, _ = xyz
        with pytest.raises(
            ValueError, match=f"Unrecognized `nbins` {nbins!r} of type {type_name}"
        ):
            Hist1D(x, nbins=nbins)

    def test_outer_edges_enclose_samples_that_round_inside_them(self):
        """Outer edges move one step outward when rounding would cut a sample off.

        The smallest sample is the float just below 1e-4 and the largest the
        float just above 7.7e-4. Rounded to 5 places they would become 1e-4
        and 7.7e-4, excluding both; the enclosing 5-place edges are 0.00009
        and 0.00078 (hand-derived), and all four samples are counted.
        ON FAILURE: the code is wrong.
        """
        low = np.nextafter(1e-4, 0.0)
        high = np.nextafter(7.7e-4, 1.0)
        x = pd.Series([low, 3e-4, 5e-4, high])

        h = Hist1D(x, nbins=3)

        assert h.edges["x"][0] == exact(0.00009)
        assert h.edges["x"][-1] == exact(0.00078)
        assert h.agg().sum() == 4

    def test_samples_on_interior_edges_are_counted_as_numpy_counts_them(self):
        """x = 0, 1, 2, 3, 4 in 4 integer bins counts 1, 1, 1, 2, as numpy does.

        Each sample sits on an edge: left-closed bins hold their left edge,
        and the last bin also holds its right edge.
        ON FAILURE: the code is wrong.
        """
        x = pd.Series([0.0, 1.0, 2.0, 3.0, 4.0])

        agg = Hist1D(x, nbins=4).agg()

        expected = np.histogram(x, bins=4)[0]
        assert agg.to_numpy() == exact(expected.astype(float))
        assert list(expected) == [1, 1, 1, 2]  # hand count

    # "fd" on a 0.00025 grid over [0, 1) plus one value of 1e14 asks numpy for
    # about 1e15 bins. The grid puts a sample exactly on the lowest fallback
    # edge, which a right-closed first bin leaves out.
    OUT_OF_MEMORY_X = pd.Series(np.r_[np.arange(4000) * 0.00025, 1e14])

    def test_fd_rule_on_an_extreme_outlier_exhausts_memory(self):
        """numpy cannot allocate the "fd" edges of ``OUT_OF_MEMORY_X``.

        And one sample equals the fallback's lowest edge, the 0.05th
        percentile rounded to 5 places (``calc_bins_intervals`` Notes).
        ON FAILURE: the fixture no longer separates the out-of-memory fallback
        from ordinary binning, or no sample sits on its lowest edge; fix the
        fixture.
        """
        x = self.OUT_OF_MEMORY_X
        with pytest.raises(MemoryError):
            np.histogram_bin_edges(x, "fd")
        assert (x == np.round(np.quantile(x, 0.0005), 5)).sum() == 1

    def test_bin_rule_too_large_for_memory_falls_back_and_warns_the_count(self, caplog):
        """An out-of-memory bin rule bins clipped data and warns how many values fall out.

        The warning's count and the counted values add up to every finite
        value (identity), and the outlier is among those left out.
        ON FAILURE: the code is wrong.
        """
        x = self.OUT_OF_MEMORY_X
        with caplog.at_level("WARNING", logger="solarwindpy.plotting"):
            h = Hist1D(x, nbins="fd")

        counted = int(h.agg().sum())
        assert h.edges["x"][-1] < 1e14
        assert f"{x.size - counted} of {x.size} finite values" in caplog.text

    def test_out_of_memory_bins_span_the_documented_percentiles(self):
        """The fallback's outer edges are the 0.05th and 99.95th percentiles.

        "fd" edges run from the clipped data's minimum to its maximum, which
        are those percentiles (``calc_bins_intervals`` Notes), rounded to 5
        places; the percentiles come from numpy.quantile.
        ON FAILURE: the code is wrong.
        """
        x = self.OUT_OF_MEMORY_X
        lo, hi = np.round(np.quantile(x, [0.0005, 0.9995]), 5)

        h = Hist1D(x, nbins="fd")

        assert h.edges["x"][0] == exact(lo)
        assert h.edges["x"][-1] == exact(hi)


class TestAggKeywords:
    """``agg`` hands keywords to the aggregation and applies ``clim`` inclusively."""

    def test_keywords_reach_the_aggregation_function(self, xyz):
        """``agg(fcn="quantile", q=0.25)`` gives each bin's 25th percentile of y.

        ON FAILURE: the code is wrong.
        """
        x, y, _ = xyz
        h = Hist1D(x, y, nbins=X_EDGES)
        bins = _bin_index(x.to_numpy(), X_EDGES)
        expected = [np.quantile(y.to_numpy()[bins == i], 0.25) for i in range(4)]

        assert h.agg(fcn="quantile", q=0.25).to_numpy() == exact(expected)

    def test_upper_clim_keeps_a_bin_whose_count_equals_it(self):
        """``set_clim(None, 2)`` keeps bins of 1 and 2 points and blanks the bin of 3.

        Edges [0, 1, 2, 4] hold 1, 3 and 2 samples (hand count).
        ON FAILURE: the code is wrong.
        """
        x = pd.Series([0.5, 1.25, 1.5, 1.75, 3.0, 3.5])
        h = Hist1D(x, nbins=np.array([0.0, 1.0, 2.0, 4.0]))
        h.set_clim(None, 2)

        assert h.agg().to_numpy() == exact([1.0, np.nan, 2.0], nan_ok=True)
