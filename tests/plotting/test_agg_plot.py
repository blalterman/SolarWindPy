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
the data.
"""

import numpy as np
import pandas as pd
import pytest
from scipy.stats import binned_statistic_2d

from solarwindpy.plotting.agg_plot import AggPlot
from solarwindpy.plotting.hist1d import Hist1D
from solarwindpy.plotting.hist2d import Hist2D

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
        assert np.quantile(x, 0.9999) == pytest.approx(999.009, rel=1e-12, abs=0)


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
        # rel 1e-12: same means summed in a different order.
        np.testing.assert_allclose(
            _grid(h.agg(), X_EDGES, Y_EDGES), expected, rtol=1e-12, atol=0
        )

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
        # rel 1e-12: float rounding only.
        np.testing.assert_allclose(
            _grid(h.agg(fcn=fcn), X_EDGES, Y_EDGES), expected, rtol=1e-12, atol=0
        )

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
        # rel 1e-12: float rounding only.
        np.testing.assert_allclose(
            _grid(h.agg(), X_EDGES, Y_EDGES), expected, rtol=1e-12, atol=0
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
        # rel 1e-12: float rounding only.
        np.testing.assert_allclose(
            _grid(h.agg(), X_EDGES, Y_EDGES), expected, rtol=1e-12, atol=0
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
        # rel 1e-12: log10 then 10** round trip, float rounding only.
        np.testing.assert_allclose(subset["x"], x, rtol=1e-12, atol=0)
        np.testing.assert_allclose(subset["y"], y, rtol=1e-12, atol=0)


# ---------------------------------------------------------------------------
# clip_data
# ---------------------------------------------------------------------------

SERIES = pd.Series(np.arange(1.0, 11.0))
FRAME = pd.DataFrame({"a": np.arange(1.0, 6.0), "b": np.arange(10.0, 60.0, 10.0)})


class TestClipData:
    """``clip_data`` clips to the 0.01st and 99.99th percentiles, or one of them.

    Thresholds come from numpy.quantile (linear interpolation), applied with
    numpy.clip; for 1..10 they are 1 + 9 * 1e-4 = 1.0009 and 10 - 9 * 1e-4 =
    9.9991 by hand.
    """

    def test_series_both_tails_hand_computed(self):
        """Any clip value other than "l"/"u" clips both tails of 1..10.

        ON FAILURE: the code is wrong.
        """
        result = AggPlot.clip_data(SERIES, True)
        expected = np.r_[1.0009, np.arange(2.0, 10.0), 9.9991]
        # rel 1e-12: interpolated quantiles, float rounding only.
        np.testing.assert_allclose(result, expected, rtol=1e-12, atol=0)
        assert isinstance(result, pd.Series)

    def test_dataframe_both_tails_per_column(self):
        """A DataFrame is clipped column by column at its own percentiles.

        ON FAILURE: the code is wrong.
        """
        result = AggPlot.clip_data(FRAME, "both")
        lo = np.quantile(FRAME, 1e-4, axis=0)
        hi = np.quantile(FRAME, 1 - 1e-4, axis=0)
        # rel 1e-12: float rounding only.
        np.testing.assert_allclose(result, np.clip(FRAME, lo, hi), rtol=1e-12, atol=0)
        assert list(result.columns) == ["a", "b"]

    def test_series_lower(self):
        """``"l"`` raises only the low tail: 1 becomes 1.0009, 10 stays 10.

        ON FAILURE: the code is wrong.
        """
        result = AggPlot.clip_data(SERIES, "l")
        expected = SERIES.clip(lower=np.quantile(SERIES, 1e-4))
        # rel 1e-12: float rounding only.
        np.testing.assert_allclose(result, expected, rtol=1e-12, atol=0)
        assert result.iloc[0] == pytest.approx(1.0009, rel=1e-12, abs=0)
        assert result.iloc[-1] == 10.0

    def test_series_upper(self):
        """``"u"`` lowers only the high tail: 10 becomes 9.9991, 1 stays 1.

        ON FAILURE: the code is wrong.
        """
        result = AggPlot.clip_data(SERIES, "u")
        expected = SERIES.clip(upper=np.quantile(SERIES, 1 - 1e-4))
        # rel 1e-12: float rounding only.
        np.testing.assert_allclose(result, expected, rtol=1e-12, atol=0)
        assert result.iloc[-1] == pytest.approx(9.9991, rel=1e-12, abs=0)
        assert result.iloc[0] == 1.0

    def test_dataframe_lower(self):
        """``"l"`` clips each column's low tail at that column's percentile.

        ON FAILURE: the code is wrong.
        """
        result = AggPlot.clip_data(FRAME, "l")
        lo = np.quantile(FRAME, 1e-4, axis=0)
        # rel 1e-12: float rounding only.
        np.testing.assert_allclose(result, np.clip(FRAME, lo, None), rtol=1e-12, atol=0)

    def test_dataframe_upper(self):
        """``"u"`` clips each column's high tail at that column's percentile.

        ON FAILURE: the code is wrong.
        """
        result = AggPlot.clip_data(FRAME, "u")
        hi = np.quantile(FRAME, 1 - 1e-4, axis=0)
        # rel 1e-12: float rounding only.
        np.testing.assert_allclose(result, np.clip(FRAME, None, hi), rtol=1e-12, atol=0)

    def test_tail_selector_is_case_insensitive(self):
        """``"L"``/``"Lower"`` act as ``"l"``, and ``"U"``/``"Upper"`` as ``"u"``.

        ON FAILURE: the code is wrong.
        """
        lower = SERIES.clip(lower=np.quantile(SERIES, 1e-4))
        upper = SERIES.clip(upper=np.quantile(SERIES, 1 - 1e-4))
        for mode, expected in (
            ("L", lower),
            ("Lower", lower),
            ("U", upper),
            ("Upper", upper),
        ):
            # rel 1e-12: float rounding only.
            np.testing.assert_allclose(
                AggPlot.clip_data(SERIES, mode), expected, rtol=1e-12, atol=0
            )

    def test_rejects_non_pandas_input_with_typeerror(self):
        """A list is neither Series nor DataFrame and raises TypeError.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(TypeError, match="Unexpected object"):
            AggPlot.clip_data([1.0, 2.0, 3.0], True)
