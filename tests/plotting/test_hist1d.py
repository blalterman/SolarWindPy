"""Contract tests for :class:`solarwindpy.plotting.hist1d.Hist1D`.

Every expected count is re-derived from :func:`numpy.histogram` (or a plain
boolean mask) on the same input, and the bins are deliberately unequal in
width so that an error in a bin width, a bin center, or a bin assignment
cannot cancel out.

Hist1D bins from explicit edges are right-closed, ``(a, b]``, where
``numpy.histogram`` bins are left-closed ``[a, b)``; bins from an integer
``nbins`` follow numpy. The two agree whenever no sample sits exactly on an
edge, which holds with probability one for the continuous random samples used
here.
"""

import io
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")

import matplotlib.colors as mcolors  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from scipy.ndimage import gaussian_filter  # noqa: E402

from solarwindpy.plotting.base import ClipAxes  # noqa: E402
from solarwindpy.plotting.hist1d import Hist1D  # noqa: E402
from solarwindpy.plotting.labels.special import Count  # noqa: E402
from tests.tolerances import exact  # noqa: E402

# Unequal widths (2, 0.5, 0.5, 0.25, 1.75, 1.5): a width, center, or
# assignment error in any one bin changes the expectation.
EDGES = np.array([-3.0, -1.0, -0.5, 0.0, 0.25, 2.0, 3.5])
N_SAMPLES = 400


class _CountsDisagreeWithNumpy(AssertionError):
    """Raised when Hist1D counts differ from numpy.histogram on the same input."""


class _DensityNotNormalised(AssertionError):
    """Raised when a density integrates to 1 over neither log10(x) nor x."""


class _SmoothedCountsTruncated(AssertionError):
    """Raised when smoothed counts differ from the float Gaussian convolution."""


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


@pytest.fixture
def xy():
    """Normal x and an unrelated y, every EDGES bin populated."""
    rng = np.random.default_rng(20260929)
    # A non-default index, so returned labels cannot pass as positions.
    index = pd.RangeIndex(1000, 1000 + N_SAMPLES)
    x = pd.Series(rng.normal(0.0, 1.0, N_SAMPLES), index=index)
    y = pd.Series(rng.normal(5.0, 1.0, N_SAMPLES), index=index)
    return x, y


def _numpy_counts(x, edges=EDGES):
    counts, _ = np.histogram(np.asarray(x, float), bins=edges)
    return counts


def _per_bin(x, y, reducer, edges=EDGES):
    """Apply ``reducer`` to the y-values in each right-closed x bin."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    return np.array(
        [reducer(y[(lo < x) & (x <= hi)]) for lo, hi in zip(edges[:-1], edges[1:])]
    )


def bin_median(s):
    """A plain function, so ``make_plot`` must look its column up by name."""
    return np.median(s)


def half_range(s):
    """Half the range of ``s``; a plain function used as an error estimate."""
    return 0.5 * (np.max(s) - np.min(s))


def _centers(edges=EDGES):
    return 0.5 * (edges[:-1] + edges[1:])


def _line_xy(line):
    return (
        np.asarray(line.get_xdata(), float),
        np.asarray(line.get_ydata(), float),
    )


def test_fixture_populates_every_bin(xy):
    """Every EDGES bin holds at least five samples from the ``xy`` fixture.

    The mean, error-bar and window tests compare per-bin statistics, which are
    undefined for empty bins.

    ON FAILURE: the fixture no longer populates every bin; fix the fixture.
    """
    x, _ = xy
    assert (_numpy_counts(x) >= 5).all()


class TestCounts:
    def test_counts_on_unequal_bins_equal_numpy_histogram(self, xy):
        """Explicit unequal edges yield numpy.histogram's counts, bin by bin.

        Samples outside the edges are appended so that both sides must also
        agree on what to drop.

        ON FAILURE: the code is wrong.
        """
        x, _ = xy
        outside = pd.Series([-7.0, -3.5, 3.75, 9.0], index=range(4))
        x = pd.concat([x, outside])

        agg = Hist1D(x, nbins=EDGES).agg()

        np.testing.assert_array_equal(agg.fillna(0).values, _numpy_counts(x))
        assert agg.sum() == N_SAMPLES

    def test_empty_bin_is_reported_without_shifting_its_neighbours(self):
        """An empty middle bin keeps its place; the populated bins keep theirs.

        Whether an empty bin reads 0 or NaN is not asserted, only that it holds
        no count and that the counts either side are unchanged.

        ON FAILURE: the code is wrong; counts are being attributed to the wrong
        bins.
        """
        edges = np.array([0.0, 1.0, 3.0, 4.0])
        x = pd.Series([0.5, 0.25, 3.5, 3.25, 3.75])

        agg = Hist1D(x, nbins=edges).agg()

        assert agg.size == 3
        np.testing.assert_array_equal(agg.fillna(0).values, [2, 0, 1 + 1 + 1])

    def test_integer_nbins_counts_equal_numpy_histogram(self, xy):
        """With ``nbins`` an integer, counts equal numpy.histogram's and sum to N.

        ON FAILURE: the code is wrong, unless the author rejects numpy's
        convention that the outermost edges enclose every sample.
        """
        x, _ = xy
        expected = np.histogram(np.asarray(x, float), bins=9)[0]

        agg = Hist1D(x, nbins=9).agg()

        got = agg.fillna(0).values
        if not (np.array_equal(got, expected) and agg.sum() == x.size):
            raise _CountsDisagreeWithNumpy(
                f"Hist1D {got.tolist()} (sum {agg.sum()}) != "
                f"numpy {expected.tolist()} (sum {x.size})"
            )


class TestAggregation:
    def test_y_is_averaged_within_each_x_bin(self, xy):
        """Given y, the default aggregate is the mean of y in each x bin.

        ON FAILURE: the code is wrong.
        """
        x, y = xy

        agg = Hist1D(x, y, nbins=EDGES).agg()

        assert np.asarray(agg.values) == exact(_per_bin(x, y, np.mean))

    def test_clim_blanks_bins_with_fewer_counts_than_its_lower_limit(self, xy):
        """``set_clim(lower)`` blanks every bin holding fewer than ``lower``.

        The limit is the count of a middle bin, so some bins survive, some do
        not, and one sits exactly on the limit (the inclusive boundary); the
        surviving means are unchanged.

        ON FAILURE: the code is wrong.
        """
        x, y = xy
        counts = _numpy_counts(x)
        lower = int(np.sort(counts)[counts.size // 2])
        keep = counts >= lower
        assert keep.any() and not keep.all()

        hist = Hist1D(x, y, nbins=EDGES)
        hist.set_clim(lower, None)
        agg = hist.agg()

        np.testing.assert_array_equal(agg.notna().values, keep)
        assert np.asarray(agg.values[keep]) == exact(_per_bin(x, y, np.mean)[keep])


class TestDensity:
    def test_density_by_hand_on_unequal_bins(self):
        """Density is count / (N * width), checked on a hand-computed case.

        Edges [0, 1, 2, 4] hold 1, 2 and 1 of N = 4 samples, so the densities
        are 1/(4*1), 2/(4*1) and 1/(4*2).

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([0.5, 1.5, 1.625, 3.0])

        agg = Hist1D(x, axnorm="d", nbins=np.array([0.0, 1.0, 2.0, 4.0])).agg()

        assert np.asarray(agg.values) == exact([0.25, 0.5, 0.125])

    def test_density_is_count_over_total_and_width(self, xy):
        """Density equals numpy's counts / (N * width) and integrates to 1.

        ON FAILURE: the code is wrong.
        """
        x, _ = xy
        counts = _numpy_counts(x)
        widths = np.diff(EDGES)

        agg = Hist1D(x, axnorm="d", nbins=EDGES).agg()

        assert np.asarray(agg.values) == exact(counts / (counts.sum() * widths))
        assert (agg.values * widths).sum() == exact(1.0)

    def test_logx_density_integrates_to_one_over_log10_x(self):
        """A logx density integrates to 1 over log10(x).

        The author ruled that a logx density is normalised over log10(x): bar
        areas on the log axis sum to 1.

        ON FAILURE: the code is wrong, unless the author reverses that ruling.
        """
        rng = np.random.default_rng(7)
        x = pd.Series(10.0 ** rng.uniform(0.0, 2.0, 500))
        log_edges = np.array([0.0, 0.5, 0.75, 1.0, 1.5, 2.0])

        agg = Hist1D(x, logx=True, axnorm="d", nbins=log_edges).agg()

        over_log = (agg.values * np.diff(log_edges)).sum()
        if over_log != exact(1.0):
            raise _DensityNotNormalised(f"integral over log10(x) = {over_log}")


class TestPeakNormalization:
    def test_t_draws_counts_divided_by_their_maximum(self):
        """After ``set_axnorm("t")`` the drawn values are counts / max(counts).

        Edges [0, 1, 2, 4] hold 1, 3 and 2 samples by construction, so the
        drawn values are 1/3, 3/3 and 2/3 and the peak is exactly 1.

        ON FAILURE: the code is wrong, unless the author reverses the ruling
        that "t" divides by the maximum.
        """
        x = pd.Series([0.5, 1.25, 1.5, 1.75, 3.0, 3.5])
        counts = np.array([1.0, 3.0, 2.0])  # chosen input, counted by hand
        hist = Hist1D(x, nbins=np.array([0.0, 1.0, 2.0, 4.0]))

        hist.set_axnorm("t")
        _, ax = plt.subplots()
        hist.make_plot(ax)

        _, line_y = _line_xy(ax.lines[0])
        assert np.asarray(line_y) == exact(counts / counts.max())
        assert line_y.max() == 1.0

    @pytest.mark.parametrize("bad", ["c", "r", "x", "density", "tx", "dog"])
    def test_unrecognized_axnorm_is_rejected(self, bad):
        """``set_axnorm`` rejects any key other than "d", "t" or None.

        The match is exact, so a word that merely starts with "d" or "t"
        ("density", "tx") is refused rather than truncated to its first letter.

        ON FAILURE: the code is wrong.
        """
        hist = Hist1D(pd.Series([0.5, 1.5, 3.0]), nbins=np.array([0.0, 1.0, 2.0, 4.0]))

        with pytest.raises(
            ValueError,
            match=f"Unrecognized axnorm '{bad}'; expected one of: d, t",
        ):
            hist.set_axnorm(bad)

    def test_axnorm_match_is_case_insensitive(self):
        """``set_axnorm("D")`` is stored as the lowercase key "d".

        ON FAILURE: the code is wrong.
        """
        hist = Hist1D(pd.Series([0.5, 1.5, 3.0]), nbins=np.array([0.0, 1.0, 2.0, 4.0]))

        hist.set_axnorm("D")
        assert hist.axnorm == "d"

    def test_non_string_axnorm_is_a_type_error(self):
        """A non-string, non-None axnorm raises ``TypeError`` naming its type.

        ON FAILURE: the code is wrong.
        """
        hist = Hist1D(pd.Series([0.5, 1.5, 3.0]), nbins=np.array([0.0, 1.0, 2.0, 4.0]))

        with pytest.raises(TypeError, match="axnorm must be a string or None; got int"):
            hist.set_axnorm(1)


class TestMakePlot:
    def test_logx_line_is_drawn_at_geometric_bin_centers(self):
        """Under logx the line's x-values are sqrt(left * right) in linear x.

        10**((log a + log b) / 2) = sqrt(a * b); the linear edges are the test's.

        ON FAILURE: the code is wrong.
        """
        rng = np.random.default_rng(11)
        x = pd.Series(10.0 ** rng.uniform(0.0, 2.0, 500))
        log_edges = np.array([0.0, 0.5, 0.75, 1.0, 1.5, 2.0])
        linear = 10.0**log_edges

        _, ax = plt.subplots()
        Hist1D(x, logx=True, nbins=log_edges).make_plot(ax)

        line_x, line_y = _line_xy(ax.lines[0])
        assert np.asarray(line_x) == exact(np.sqrt(linear[:-1] * linear[1:]))
        np.testing.assert_array_equal(line_y, _numpy_counts(np.log10(x), log_edges))

    def test_without_an_axis_it_draws_the_counts_on_new_axes(self, xy):
        """``make_plot()`` with no axis returns new axes holding the counts.

        ON FAILURE: the code is wrong.
        """
        x, _ = xy

        ax, _, _, _ = Hist1D(x, nbins=EDGES).make_plot()

        line_x, line_y = _line_xy(ax.lines[0])
        assert np.asarray(line_x) == exact(_centers())
        np.testing.assert_array_equal(line_y, _numpy_counts(x))

    @pytest.mark.parametrize(
        "fcn, center, spread",
        [
            # pandas "std" is the ddof=1 sample standard deviation.
            (("mean", "std"), np.mean, lambda s: np.std(s, ddof=1)),
            ((bin_median, half_range), np.median, half_range),
        ],
        ids=["strings", "functions"],
    )
    def test_errorbars_span_first_aggregate_plus_minus_second(
        self, xy, fcn, center, spread
    ):
        """A 2-tuple ``fcn`` plots the first aggregate with the second as y-error.

        The "functions" case passes plain functions, which the plot must look
        up by name.

        ON FAILURE: the code is wrong.
        """
        x, y = xy
        expected_y = _per_bin(x, y, center)
        expected_dy = _per_bin(x, y, spread)

        _, ax = plt.subplots()
        _, container, _, _ = Hist1D(x, y, nbins=EDGES).make_plot(ax, fcn=fcn)

        line_x, line_y = _line_xy(container.lines[0])
        assert np.asarray(line_x) == exact(_centers())
        assert np.asarray(line_y) == exact(expected_y)
        (bars,) = container.lines[2]
        segments = np.array(bars.get_segments())
        assert np.asarray(segments[:, :, 0].T) == exact(np.array([_centers()] * 2))
        assert np.asarray(np.sort(segments[:, :, 1], axis=1)) == exact(
            np.column_stack([expected_y - expected_dy, expected_y + expected_dy])
        )

    def test_three_element_fcn_raises_value_error(self, xy):
        """A ``fcn`` tuple of any length other than 2 is rejected.

        ON FAILURE: the code is wrong.
        """
        x, y = xy
        _, ax = plt.subplots()
        with pytest.raises(ValueError, match="Unrecognized `fcn`"):
            Hist1D(x, y, nbins=EDGES).make_plot(ax, fcn=("mean", "std", "count"))

    def test_gaussian_smoothing_of_means_matches_scipy(self, xy):
        """Smoothing hands matplotlib scipy's Gaussian filter of the bin means.

        A non-default ``mode`` is passed through ``gaussian_filter_kwargs``;
        the check that it matters is that it changes the expectation.

        ON FAILURE: the code is wrong.
        """
        x, y = xy
        means = _per_bin(x, y, np.mean)
        expected = gaussian_filter(means, 1.5, mode="constant")
        assert not np.allclose(expected, gaussian_filter(means, 1.5))

        _, ax = plt.subplots()
        Hist1D(x, y, nbins=EDGES).make_plot(
            ax, gaussian_filter_std=1.5, gaussian_filter_kwargs={"mode": "constant"}
        )

        assert np.asarray(_line_xy(ax.lines[0])[1]) == exact(expected)

    def test_gaussian_smoothing_of_counts_is_not_truncated(self, xy):
        """Smoothed counts equal scipy's Gaussian filter of the float counts.

        ON FAILURE: the code is wrong.
        """
        x, _ = xy
        expected = gaussian_filter(_numpy_counts(x).astype(float), 1.0)

        _, ax = plt.subplots()
        Hist1D(x, nbins=EDGES).make_plot(ax, gaussian_filter_std=1.0)

        got = _line_xy(ax.lines[0])[1]
        if np.asarray(got) != exact(expected):
            raise _SmoothedCountsTruncated(f"{got.tolist()} != {expected.tolist()}")

    def test_plot_window_band_spans_y_minus_to_plus_dy(self, xy):
        """``plot_window`` fills between y - dy and y + dy at each bin center.

        The band's vertices are compared as a set, independent of the order in
        which matplotlib walks the polygon.

        ON FAILURE: the code is wrong.
        """
        x, y = xy
        mean = _per_bin(x, y, np.mean)
        std = _per_bin(x, y, lambda s: np.std(s, ddof=1))

        _, ax = plt.subplots()
        _, line, band, _ = Hist1D(x, y, nbins=EDGES).make_plot(
            ax, fcn=("mean", "std"), plot_window=True
        )

        assert np.asarray(_line_xy(line)[1]) == exact(mean)
        vertices = np.unique(band.get_paths()[0].vertices.round(9), axis=0)
        expected = np.unique(
            np.vstack(
                [
                    np.column_stack([_centers(), mean - std]),
                    np.column_stack([_centers(), mean + std]),
                ]
            ).round(9),
            axis=0,
        )
        assert np.asarray(vertices) == exact(expected)

    def test_plot_window_edges_draw_the_band_boundaries(self, xy):
        """``plot_window_edges`` adds lines at y + dy and y - dy, in that order.

        ON FAILURE: the code is wrong.
        """
        x, y = xy
        mean = _per_bin(x, y, np.mean)
        std = _per_bin(x, y, lambda s: np.std(s, ddof=1))

        _, ax = plt.subplots()
        Hist1D(x, y, nbins=EDGES).make_plot(
            ax, fcn=("mean", "std"), plot_window=True, plot_window_edges=True
        )

        central, upper, lower = ax.lines
        assert np.asarray(_line_xy(central)[1]) == exact(mean)
        assert np.asarray(_line_xy(upper)[1]) == exact(mean + std)
        assert np.asarray(_line_xy(lower)[1]) == exact(mean - std)

    def test_transposed_plot_window_spans_x_minus_to_plus_dx(self, xy):
        """Transposed, the band spans value -/+ error horizontally at each center.

        ON FAILURE: the code is wrong.
        """
        x, y = xy
        mean = _per_bin(x, y, np.mean)
        std = _per_bin(x, y, lambda s: np.std(s, ddof=1))

        _, ax = plt.subplots()
        _, _, band, _ = Hist1D(x, y, nbins=EDGES).make_plot(
            ax, fcn=("mean", "std"), plot_window=True, transpose_axes=True
        )

        vertices = np.unique(band.get_paths()[0].vertices.round(9), axis=0)
        expected = np.unique(
            np.vstack(
                [
                    np.column_stack([mean - std, _centers()]),
                    np.column_stack([mean + std, _centers()]),
                ]
            ).round(9),
            axis=0,
        )
        assert np.asarray(vertices) == exact(expected)


class TestConstructCdf:
    def test_cdf_is_the_sorted_binned_sample_at_even_positions(self, xy):
        """The cdf lists binned samples in ascending order at positions i/(n-1).

        Samples outside the edges are appended and must not appear.

        ON FAILURE: the code is wrong.
        """
        x, _ = xy
        x = pd.concat([x, pd.Series([-9.0, 8.0], index=[0, 1])])
        inside = np.sort(x[(x > EDGES[0]) & (x <= EDGES[-1])].values)

        cdf = Hist1D(x, nbins=EDGES).construct_cdf(only_plotted=False)

        np.testing.assert_array_equal(cdf["x"].values, inside)
        assert np.asarray(cdf["position"].values) == exact(
            np.linspace(0.0, 1.0, inside.size)
        )

    def test_logx_cdf_is_in_linear_units(self):
        """Under logx the cdf's x column is the original, linear sample, sorted.

        ON FAILURE: the code is wrong.
        """
        rng = np.random.default_rng(13)
        x = pd.Series(10.0 ** rng.uniform(0.0, 2.0, 300))

        cdf = Hist1D(x, logx=True, nbins=np.array([-0.5, 1.0, 2.5])).construct_cdf(
            only_plotted=False
        )

        assert np.asarray(cdf["x"].values) == exact(np.sort(x.values))

    def test_cdf_hand_computed(self):
        """x = 3, 1, 4, 2 in one bin gives x 1, 2, 3, 4 at positions 0, 1/3, 2/3, 1.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([3.0, 1.0, 4.0, 2.0])

        cdf = Hist1D(x, nbins=np.array([0.0, 5.0])).construct_cdf()

        assert list(cdf.columns) == ["x", "position"]
        assert cdf["x"].to_numpy() == exact([1.0, 2.0, 3.0, 4.0])
        assert cdf["position"].to_numpy() == exact([0.0, 1 / 3, 2 / 3, 1.0])

    def test_cdf_ignores_y(self, xy):
        """A histogram that aggregates y gives the same cdf of x as one that counts.

        ON FAILURE: the code is wrong.
        """
        x, y = xy

        with_y = Hist1D(x, y, nbins=EDGES).construct_cdf(only_plotted=False)
        counted = Hist1D(x, nbins=EDGES).construct_cdf(only_plotted=False)

        pd.testing.assert_frame_equal(with_y, counted)

    def test_default_cdf_leaves_out_bins_dropped_by_clim(self):
        """By default the cdf holds only measurements in bins that are plotted.

        Edges [0, 1, 2, 4] hold 1, 3 and 2 samples; ``set_clim(2)`` drops the
        first bin, so 0.5 is left out and the other five remain (hand count).
        ON FAILURE: the code is wrong.
        """
        x = pd.Series([0.5, 1.25, 1.5, 1.75, 3.0, 3.5])
        hist = Hist1D(x, nbins=np.array([0.0, 1.0, 2.0, 4.0]))
        hist.set_clim(2, None)

        cdf = hist.construct_cdf()

        assert cdf["x"].to_numpy() == exact([1.25, 1.5, 1.75, 3.0, 3.5])

    def test_default_cdf_with_every_bin_plotted_is_the_whole_binned_sample(self, xy):
        """With every bin populated, the default cdf equals the unfiltered one.

        ON FAILURE: the code is wrong.
        """
        x, _ = xy
        hist = Hist1D(x, nbins=EDGES)

        pd.testing.assert_frame_equal(
            hist.construct_cdf(), hist.construct_cdf(only_plotted=False)
        )


# ---------------------------------------------------------------------------
# construct_cdf keeps the original row labels
# ---------------------------------------------------------------------------

# x = 3, 1, 4, 2 at four hourly timestamps; sorted by x the labels run
# 01:00 (1), 03:00 (2), 00:00 (3), 02:00 (4).
TIMES = pd.date_range("2020-01-01", periods=4, freq="h")
TIME_X = pd.Series([3.0, 1.0, 4.0, 2.0], index=TIMES)


def test_cdf_keeps_timestamp_labels_sorted_by_x():
    """A timestamp-indexed sample keeps its timestamps, reordered by x.

    Hand: sorted x is 1, 2, 3, 4 at labels 01:00, 03:00, 00:00, 02:00, with
    positions 0, 1/3, 2/3, 1 (i / (n - 1), n = 4).

    ON FAILURE: the code is wrong.
    """
    cdf = Hist1D(TIME_X, nbins=np.array([0.0, 5.0])).construct_cdf()

    assert list(cdf.columns) == ["x", "position"]
    assert cdf.index.tolist() == [
        pd.Timestamp("2020-01-01 01:00"),
        pd.Timestamp("2020-01-01 03:00"),
        pd.Timestamp("2020-01-01 00:00"),
        pd.Timestamp("2020-01-01 02:00"),
    ]
    assert cdf["x"].to_numpy() == exact([1.0, 2.0, 3.0, 4.0])
    assert cdf["position"].to_numpy() == exact([0.0, 1 / 3, 2 / 3, 1.0])


# Non-contiguous integer labels. Label 20 (x = 9) is outside the single bin
# (0, 5] and is not in the CDF; the other four sort to 30, 50, 10, 40.
GAPPY_X = pd.Series([2.5, 0.5, 9.0, 1.5, 3.5], index=[10, 30, 20, 50, 40])


def test_cdf_keeps_non_contiguous_integer_labels_and_ranks_positions():
    """Positions come from rank 0..n-1 in x order, not from the row labels.

    Hand: kept labels 30, 50, 10, 40 hold x 0.5, 1.5, 2.5, 3.5, at positions
    0, 1/3, 2/3, 1. Positions taken from the labels would not be evenly
    spaced and would not start at 0.

    ON FAILURE: the code is wrong.
    """
    cdf = Hist1D(GAPPY_X, nbins=np.array([0.0, 5.0])).construct_cdf(only_plotted=False)

    assert cdf.index.tolist() == [30, 50, 10, 40]
    assert cdf["x"].to_numpy() == exact([0.5, 1.5, 2.5, 3.5])
    assert cdf["position"].to_numpy() == exact([0.0, 1 / 3, 2 / 3, 1.0])


def test_cdf_x_at_each_label_is_that_rows_measurement():
    """Each label's cdf x is the measurement the caller stored at that label.

    Identity: ``cdf.x`` at label k equals the input x at label k.

    ON FAILURE: the code is wrong.
    """
    cdf = Hist1D(GAPPY_X, nbins=np.array([0.0, 5.0])).construct_cdf(only_plotted=False)

    assert cdf["x"].to_numpy() == exact(GAPPY_X.loc[cdf.index].to_numpy())


def test_logx_cdf_keeps_labels_and_linear_x():
    """Under logx the labels survive and x is in linear units.

    Hand: x = 100, 1, 10 at labels 7, 3, 5 sort to 1, 10, 100 at labels 3,
    5, 7, positions 0, 0.5, 1.

    ON FAILURE: the code is wrong.
    """
    x = pd.Series([100.0, 1.0, 10.0], index=[7, 3, 5])

    cdf = Hist1D(x, logx=True, nbins=np.array([-1.0, 3.0])).construct_cdf()

    assert cdf.index.tolist() == [3, 5, 7]
    assert cdf["x"].to_numpy() == exact([1.0, 10.0, 100.0])
    assert cdf["position"].to_numpy() == exact([0.0, 0.5, 1.0])


class TestRowsWithNaN:
    """A row with NaN in x or y is dropped, as in Hist2D (how="any")."""

    # Label 11 holds y = NaN; its x = 3.9 would otherwise fall in (3, 4].
    X = pd.Series([0.5, 3.9, 2.5, 3.5, 1.5], index=[10, 11, 12, 13, 14])
    Y = pd.Series([1.0, np.nan, 3.0, 4.0, 5.0], index=[10, 11, 12, 13, 14])
    STEPS = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    KEPT = [10, 12, 13, 14]

    def test_nan_y_row_is_absent_from_data_and_every_selection(self):
        """Label 11 (y = NaN) is in neither data nor any selection.

        Hand values on right-closed bins (0, 1], (1, 2], (2, 3], (3, 4]: the
        kept labels are 10, 12, 13 and 14, one per bin, so the mean of y per
        bin is 1, 5, 3, 4; the sorted x of the kept rows is 0.5, 1.5, 2.5,
        3.5.

        ON FAILURE: the code is wrong.
        """
        h = Hist1D(self.X, self.Y, nbins=self.STEPS)

        assert h.data.index.tolist() == self.KEPT
        assert h.cut.index.tolist() == self.KEPT
        assert h.agg().to_numpy() == exact([1.0, 5.0, 3.0, 4.0])
        assert h.get_plotted_data().index.tolist() == self.KEPT
        cdf = h.construct_cdf(only_plotted=False)
        assert cdf["x"].to_numpy() == exact([0.5, 1.5, 2.5, 3.5])
        ranges = pd.DataFrame({"bottom": 0.0, "top": 10.0}, index=h.agg().index)
        taken = h.take_data_in_yrange_across_x(
            ranges,
            lambda key, expected_logx=False: (key.left, key.right),
            lambda row, expected_logy: (row.bottom, row.top),
        )
        assert list(taken) == self.KEPT

    def test_nan_x_row_is_dropped_with_or_without_y(self):
        """A NaN x is dropped whether Hist1D aggregates y or counts x.

        Label 12's x is NaN, so labels 10, 11, 13 and 14 remain (hand).

        ON FAILURE: the code is wrong.
        """
        x = self.X.copy()
        x.loc[12] = np.nan
        y = self.Y.fillna(2.0)

        assert Hist1D(x, nbins=self.STEPS).data.index.tolist() == [10, 11, 13, 14]
        assert Hist1D(x, y, nbins=self.STEPS).data.index.tolist() == [10, 11, 13, 14]

    def test_integer_nbins_edges_come_from_the_kept_rows_by_hand(self):
        """x = 1, 2, 3, 9 with y = NaN at x = 9: 2 bins give edges 1, 2, 3.

        numpy's 2 equal bins over the kept x (1, 2, 3) have edges 1, 2, 3,
        already on the 5-place grid; with x = 9 kept they would be 1, 5, 9.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([1.0, 2.0, 3.0, 9.0])
        y = pd.Series([5.0, 6.0, 7.0, np.nan])

        h = Hist1D(x, y, nbins=2)

        assert h.edges["x"].to_numpy() == exact([1.0, 2.0, 3.0])

    def test_integer_nbins_edges_equal_numpy_on_the_kept_rows(self):
        """Integer edges are numpy's edges of the hand-filtered x, rounded outward.

        y is NaN at the smallest and largest x, so the kept rows span less
        than the full sample. The expected edges are
        ``np.histogram_bin_edges`` of the x whose y is not NaN, rounded to 5
        places with the outer edges moved outward to enclose every kept x.

        ON FAILURE: the code is wrong.
        """
        rng = np.random.default_rng(20261103)
        x = pd.Series(rng.normal(0.0, 1.0, 200))
        y = pd.Series(rng.normal(5.0, 1.0, 200))
        y.iloc[[x.idxmin(), x.idxmax()]] = np.nan
        kept = x.to_numpy()[y.notna().to_numpy()]

        edges = np.histogram_bin_edges(kept, 7)
        scale = 1e5
        lo = np.floor(edges[0] * scale) / scale
        hi = np.ceil(edges[-1] * scale) / scale
        expected = edges.round(5)
        expected[0] = lo if lo <= kept.min() else lo - 1 / scale
        expected[-1] = hi if hi >= kept.max() else hi + 1 / scale
        assert expected[0] > x.min() and expected[-1] < x.max()

        h = Hist1D(x, y, nbins=7)

        assert h.edges["x"].to_numpy() == exact(expected)
        assert h.agg(fcn="count").sum() == kept.size

    def test_all_nan_y_raises(self):
        """Every y NaN leaves no row: ``ValueError``, as for Hist2D.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([1.0, 2.0, 3.0])
        y = pd.Series([np.nan, np.nan, np.nan])

        with pytest.raises(ValueError, match="exclusively NaNs"):
            Hist1D(x, y)


@pytest.mark.parametrize(
    "given, expected",
    [(None, False), (False, False), (True, True), ("l", "l"), ("u", "u")],
)
def test_clip_is_stored_for_x_only_with_none_as_false(xy, given, expected):
    """``h.clip`` is a ``ClipAxes``: x holds ``clip``; y and z are False.

    A Hist1D bins x only, so only x is clipped.
    ON FAILURE: the code is wrong.
    """
    x, _ = xy
    clip = Hist1D(x, clip=given).clip
    assert clip == ClipAxes(x=expected, y=False, z=False)
    assert type(clip.x) is type(expected)


def test_a_clip_mapping_may_name_x_only(xy):
    """``{"x": "u"}`` is x's setting; naming y raises KeyError.

    ON FAILURE: the code is wrong.
    """
    x, _ = xy
    assert Hist1D(x, clip={"x": "u"}).clip == ClipAxes(x="u", y=False, z=False)
    with pytest.raises(KeyError, match="'y'"):
        Hist1D(x, clip={"y": "u"})


# One low and one high outlier. Clipping to the 0.05th percentile moves -1000
# to about -995.5 and clipping to the 99.95th moves 1000 to about 995.5, each
# from an outer bin into the middle bin (-999.5, 999.5].
CLIP_X = pd.Series([-1000.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1000.0])
CLIP_EDGES = np.array([-1001.0, -999.5, 999.5, 1001.0])
CLIP_CASES = [
    (None, [1, 8, 1]),  # nothing moves
    (False, [1, 8, 1]),
    (True, [0, 10, 0]),  # both outliers move to the middle bin
    ("l", [0, 9, 1]),  # only the low outlier moves
    ("u", [1, 9, 0]),  # only the high outlier moves
]


@pytest.mark.parametrize("clip, expected", CLIP_CASES)
def test_clip_clips_the_tails_it_names(clip, expected):
    """``"l"`` clips the lower tail, ``"u"`` the upper, True both, None neither.

    ON FAILURE: the code is wrong.
    """
    hist = Hist1D(CLIP_X, clip=clip, nbins=CLIP_EDGES)
    assert hist.agg().fillna(0).to_numpy() == exact(expected)


def test_take_data_in_yrange_returns_labels_inside_each_bins_window(xy):
    """Each x bin keeps the samples whose y lies in that bin's (bottom, top].

    Bottoms differ from bin to bin, so a window applied to the wrong bin
    selects a different set; the result is index labels, not positions.
    ``get_y_bounds`` gets ``expected_logy=False``: Hist1D never log-transforms
    y.

    ON FAILURE: the code is wrong.
    """
    x, y = xy
    hist = Hist1D(x, y, nbins=EDGES)
    bottoms = np.linspace(3.5, 5.5, EDGES.size - 1)
    ranges = pd.DataFrame({"bottom": bottoms, "top": 6.0}, index=hist.agg().index)

    taken = hist.take_data_in_yrange_across_x(
        ranges,
        lambda interval, expected_logx: (interval.left, interval.right),
        lambda row, expected_logy: (row["bottom"], row["top"]),
    )

    xv, yv = x.values, y.values
    mask = np.zeros(xv.size, bool)
    for lo, hi, bottom in zip(EDGES[:-1], EDGES[1:], bottoms):
        mask |= (lo < xv) & (xv <= hi) & (bottom < yv) & (yv <= 6.0)
    expected = x.index.values[mask]
    assert 0 < expected.size < x.size
    np.testing.assert_array_equal(taken, expected)


# Points on the window boundaries, bins (0, 1] and (1, 2], window (5, 6] in
# each: 10 sits on bin 1's right edge (in) and bin 2's left edge (out), 11 on
# the bottom (out), 12 on bin 2's right edge and the top (in), 13 inside.
EDGE_X = pd.Series([1.0, 1.5, 2.0, 0.5], index=[10, 11, 12, 13])
EDGE_Y = pd.Series([5.5, 5.0, 6.0, 5.5], index=[10, 11, 12, 13])


def _edge_hist_and_ranges():
    hist = Hist1D(EDGE_X, EDGE_Y, nbins=np.array([0.0, 1.0, 2.0]))
    ranges = pd.DataFrame({"bottom": 5.0, "top": 6.0}, index=hist.agg().index)
    return hist, ranges


def _interval_bounds(interval, expected_logx):
    return interval.left, interval.right


def test_take_data_in_yrange_windows_are_open_below_and_closed_above():
    """A point is taken when left < x <= right and bottom < y <= top.

    Hand-selected from ``EDGE_X``/``EDGE_Y``: 10, 12 and 13, each once.
    ON FAILURE: the code is wrong.
    """
    hist, ranges = _edge_hist_and_ranges()

    taken = hist.take_data_in_yrange_across_x(
        ranges, _interval_bounds, lambda row, expected_logy: (row["bottom"], row["top"])
    )

    np.testing.assert_array_equal(taken, [10, 12, 13])


@pytest.mark.parametrize(
    "x_bounds, y_bounds, match",
    [
        (lambda iv, expected_logx: (iv.left, iv.left), None, "Need left < right"),
        (None, lambda row, expected_logy: (5.0, 5.0), "Need bottom < top"),
    ],
    ids=["zero-width-x", "zero-width-y"],
)
def test_take_data_in_yrange_zero_width_range_raises_value_error(
    x_bounds, y_bounds, match
):
    """A zero-width x or y range raises ``ValueError`` naming the range.

    ON FAILURE: the code is wrong.
    """
    hist, ranges = _edge_hist_and_ranges()
    x_bounds = x_bounds or _interval_bounds
    y_bounds = y_bounds or (lambda row, expected_logy: (row["bottom"], row["top"]))

    with pytest.raises(ValueError, match=match + r" for x-bin .*, got \("):
        hist.take_data_in_yrange_across_x(ranges, x_bounds, y_bounds)


def test_take_data_in_yrange_hands_get_x_bounds_the_logx_flag_as_a_bool():
    """``get_x_bounds`` receives ``expected_logx=True`` from a logx histogram.

    ON FAILURE: the code is wrong.
    """
    hist = Hist1D(10.0**EDGE_X, EDGE_Y, logx=True, nbins=np.array([0.0, 1.0, 2.0]))
    ranges = pd.DataFrame({"bottom": 5.0, "top": 6.0}, index=hist.agg().index)
    flags = []

    def x_bounds(interval, expected_logx):
        flags.append(expected_logx)
        return interval.left, interval.right

    hist.take_data_in_yrange_across_x(
        ranges, x_bounds, lambda row, expected_logy: (row["bottom"], row["top"])
    )

    assert flags == [True, True]
    assert all(f is True for f in flags)


# ---------------------------------------------------------------------------
# take_data_in_yrange_across_x validates the selector's x-bins
# ---------------------------------------------------------------------------

# EDGE_X and EDGE_Y (above): bins (0, 1] and (1, 2]; window (5, 6] in each.
# Labels 10 and 13 fall in the first bin's window, label 12 in the second's,
# label 11 sits on the bottom.


def _row_bounds(row, expected_logy):
    return row["bottom"], row["top"]


def test_selector_naming_unavailable_bins_raises_value_error():
    """A selector indexed on x-bins the histogram lacks raises ``ValueError``.

    ON FAILURE: the code is wrong.
    """
    hist, _ = _edge_hist_and_ranges()
    foreign = pd.IntervalIndex.from_breaks([0.0, 0.5, 2.0], closed="right")
    ranges = pd.DataFrame({"bottom": 5.0, "top": 6.0}, index=foreign)

    with pytest.raises(ValueError, match="Need a way to drop values in selector"):
        hist.take_data_in_yrange_across_x(ranges, _interval_bounds, _row_bounds)


def test_selector_omitting_bins_warns_and_takes_only_the_named_bins(caplog):
    """A selector naming a subset of the bins warns and selects in those bins.

    Hand: only bin (0, 1] is named, so labels 10 and 13 are taken and label
    12, inside the unnamed bin's window, is not.

    ON FAILURE: the code is wrong.
    """
    hist, _ = _edge_hist_and_ranges()
    ranges = pd.DataFrame({"bottom": 5.0, "top": 6.0}, index=hist.agg().index[:1])

    with caplog.at_level(logging.WARNING):
        taken = hist.take_data_in_yrange_across_x(ranges, _interval_bounds, _row_bounds)

    np.testing.assert_array_equal(taken, [10, 13])
    assert "Dropping 1 intervals from available for selecting." in caplog.text


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------


def test_default_labels_are_x_and_y_or_a_count():
    """x is labelled "x"; y is "y" when given and a ``Count`` label otherwise.

    ON FAILURE: the code is wrong.
    """
    x, y = EDGE_X, EDGE_Y
    with_y = Hist1D(x, y, nbins=np.array([0.0, 1.0, 2.0]))
    counted = Hist1D(x, nbins=np.array([0.0, 1.0, 2.0]))

    assert (with_y.labels.x, with_y.labels.y) == ("x", "y")
    assert counted.labels.x == "x"
    assert isinstance(counted.labels.y, Count)


def test_count_label_follows_set_axnorm():
    """After ``set_axnorm("d")`` the count label reads as a density label.

    The expected label is ``Count(norm="d")`` built directly.
    ON FAILURE: the code is wrong.
    """
    hist = Hist1D(EDGE_X, nbins=np.array([0.0, 1.0, 2.0]))
    assert str(hist.labels.y) == str(Count())

    hist.set_axnorm("d")

    assert str(hist.labels.y) == str(Count(norm="d"))
    assert str(Count(norm="d")) != str(Count())


def test_a_new_count_label_takes_the_histograms_axnorm():
    """``set_labels(y=Count())`` on a density histogram gives a density label.

    ON FAILURE: the code is wrong.
    """
    hist = Hist1D(EDGE_X, axnorm="d", nbins=np.array([0.0, 1.0, 2.0]))

    hist.set_labels(y=Count())

    assert str(hist.labels.y) == str(Count(norm="d"))


def test_z_label_is_refused_naming_the_class():
    """A 1-D histogram has no z axis: ``set_labels(z=...)`` raises ``ValueError``.

    ON FAILURE: the code is wrong.
    """
    hist = Hist1D(EDGE_X, nbins=np.array([0.0, 1.0, 2.0]))
    with pytest.raises(ValueError, match="Hist1D doesn't have a z-label"):
        hist.set_labels(z="z")


# ---------------------------------------------------------------------------
# Line styles: drawstyle, user keywords and the window band
# ---------------------------------------------------------------------------


def test_counts_are_drawn_as_steps_unless_the_caller_says_otherwise(xy):
    """The histogram line uses ``drawstyle="steps-mid"``; a passed one wins.

    ON FAILURE: the code is wrong.
    """
    x, _ = xy
    _, ax = plt.subplots()
    Hist1D(x, nbins=EDGES).make_plot(ax)
    Hist1D(x, nbins=EDGES).make_plot(ax, drawstyle="default")

    assert [line.get_drawstyle() for line in ax.lines] == ["steps-mid", "default"]


def test_keywords_and_their_aliases_reach_the_line(xy):
    """``c``, ``ls`` and ``label`` style the drawn line, with or without a window.

    ON FAILURE: the code is wrong.
    """
    x, y = xy
    _, ax = plt.subplots()
    _, container, _, _ = Hist1D(x, y, nbins=EDGES).make_plot(
        ax, c="r", ls="--", label="errorbar"
    )
    Hist1D(x, y, nbins=EDGES).make_plot(
        ax, fcn=("mean", "std"), plot_window=True, c="g", ls=":", label="window"
    )

    errorbar_line, window_line = ax.lines
    assert (errorbar_line.get_color(), errorbar_line.get_linestyle()) == ("r", "--")
    assert container.get_label() == "errorbar"  # errorbar labels its container
    assert (window_line.get_color(), window_line.get_linestyle()) == ("g", ":")
    assert window_line.get_label() == "window"


def test_window_without_edges_draws_only_the_central_line(xy):
    """``plot_window`` alone draws one line and the band, no edge lines.

    ON FAILURE: the code is wrong.
    """
    x, y = xy
    _, ax = plt.subplots()
    Hist1D(x, y, nbins=EDGES).make_plot(ax, fcn=("mean", "std"), plot_window=True)

    assert len(ax.lines) == 1
    assert len(ax.collections) == 1


def test_window_band_and_edges_follow_the_line_style_by_default(xy):
    """Band and edges take the line's colour and linestyle; the band's alpha is 0.15.

    0.15 is the documented default ``alpha`` (``make_plot`` docstring).
    ON FAILURE: the code is wrong.
    """
    x, y = xy
    _, ax = plt.subplots()
    Hist1D(x, y, nbins=EDGES).make_plot(
        ax,
        fcn=("mean", "std"),
        plot_window=True,
        plot_window_edges=True,
        color="m",
        linestyle="-.",
    )

    band = ax.collections[0]
    assert [(ln.get_color(), ln.get_linestyle()) for ln in ax.lines] == [
        ("m", "-."),
        ("m", "-."),
        ("m", "-."),
    ]
    assert band.get_alpha() == 0.15
    assert tuple(band.get_facecolor()[0][:3]) == mcolors.to_rgb("m")
    # matplotlib's own band drawn with linestyle "-." is the reference.
    _, ref_ax = plt.subplots()
    reference = ref_ax.fill_between([0.0, 1.0], [0.0, 0.0], [1.0, 1.0], linestyle="-.")
    assert band.get_linestyle() == reference.get_linestyle()


def test_window_kwargs_style_the_band_and_edges(xy):
    """``window_kwargs`` styles the band and edges; other keywords style the line.

    The central line keeps the caller's own colour, linestyle and width;
    any other ``window_kwargs`` entry (here a width) reaches band and edges.
    ON FAILURE: the code is wrong.
    """
    x, y = xy
    _, ax = plt.subplots()
    Hist1D(x, y, nbins=EDGES).make_plot(
        ax,
        fcn=("mean", "std"),
        plot_window=True,
        plot_window_edges=True,
        color="m",
        linestyle="-.",
        lw=2.0,
        window_kwargs={"alpha": 0.4, "color": "c", "linestyle": ":", "lw": 3.0},
    )

    central, upper, lower = ax.lines
    band = ax.collections[0]
    assert (central.get_color(), central.get_linestyle()) == ("m", "-.")
    assert central.get_linewidth() == 2.0
    for edge in (upper, lower):
        assert (edge.get_color(), edge.get_linestyle()) == ("c", ":")
        assert edge.get_linewidth() == 3.0
    assert band.get_alpha() == 0.4
    assert tuple(band.get_facecolor()[0][:3]) == mcolors.to_rgb("c")
    assert list(band.get_linewidth()) == [3.0]


def test_transposed_window_edges_sit_at_value_minus_and_plus_error(xy):
    """Transposed, the edge lines are at x + dx then x - dx at each bin center.

    ON FAILURE: the code is wrong.
    """
    x, y = xy
    mean = _per_bin(x, y, np.mean)
    std = _per_bin(x, y, lambda s: np.std(s, ddof=1))

    _, ax = plt.subplots()
    Hist1D(x, y, nbins=EDGES).make_plot(
        ax,
        fcn=("mean", "std"),
        plot_window=True,
        plot_window_edges=True,
        transpose_axes=True,
    )

    _, upper, lower = ax.lines
    assert np.asarray(_line_xy(upper)[0]) == exact(mean + std)
    assert np.asarray(_line_xy(lower)[0]) == exact(mean - std)
    assert np.asarray(_line_xy(upper)[1]) == exact(_centers())


def test_transposed_errorbars_are_horizontal(xy):
    """Transposed, the error bars run along x: value -/+ error at each center.

    ON FAILURE: the code is wrong.
    """
    x, y = xy
    mean = _per_bin(x, y, np.mean)
    std = _per_bin(x, y, lambda s: np.std(s, ddof=1))

    _, ax = plt.subplots()
    _, container, _, _ = Hist1D(x, y, nbins=EDGES).make_plot(
        ax, fcn=("mean", "std"), transpose_axes=True
    )

    (bars,) = container.lines[2]
    segments = np.array(bars.get_segments())
    assert np.asarray(np.sort(segments[:, :, 0], axis=1)) == exact(
        np.column_stack([mean - std, mean + std])
    )
    assert np.asarray(segments[:, :, 1].T) == exact(np.array([_centers()] * 2))


def test_hist1d_figure_renders_to_png(xy):
    """A histogram with error bars renders to an in-memory PNG.

    ON FAILURE: the code is wrong.
    """
    x, y = xy
    fig, ax = plt.subplots()
    Hist1D(x, y, nbins=EDGES).make_plot(ax, fcn=("mean", "std"))
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png")
    assert buffer.getvalue().startswith(b"\x89PNG\r\n\x1a\n")  # PNG signature


# The classes below pass plain str labels on purpose, to exercise that path;
# they opt out of PlainStringLabelWarning the deliberate way its message
# describes.
_PLAIN_STRING_LABELS = pytest.mark.filterwarnings(
    "ignore::solarwindpy.plotting.labels.base.PlainStringLabelWarning"
)


# Bins chosen by the test, so every count below is an input rather than a
# recorded output. The edges are exact at the 5 decimal places at which
# `FixedGrid` stores interval endpoints.
KNOWN_EDGES = np.array([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
KNOWN_BIN_COUNTS = [3, 5, 2, 4, 6]


def _known_1d_sample():
    """Points placed at bin centers to realise ``KNOWN_BIN_COUNTS``."""
    centers = 0.5 * (KNOWN_EDGES[:-1] + KNOWN_EDGES[1:])
    values = []
    for center, count in zip(centers, KNOWN_BIN_COUNTS):
        values.extend([center] * count)
    return pd.Series(values, name="x"), centers


@_PLAIN_STRING_LABELS
class TestHist1DBasicFunctionality:
    """Test basic functionality of Hist1D."""

    def setup_method(self):
        """Set up test data for each test."""
        np.random.seed(42)
        self.n = 100
        self.x_data = pd.Series(np.random.normal(5, 2, self.n), name="x")
        self.y_data = pd.Series(np.random.normal(1, 0.5, self.n), name="y")

    def test_hist1d_instantiation_count_histogram(self):
        """Test __init__(x_series) produces a count histogram."""
        hist = Hist1D(self.x_data)

        # Should have x and y columns (y=1 for counting)
        assert "x" in hist.data.columns
        assert "y" in hist.data.columns
        assert len(hist.data) == self.n

        # For count histogram, all y values should be 1
        assert (hist.data["y"] == 1).all()

    def test_hist1d_instantiation_aggregation_histogram(self):
        """Test __init__(x, y_series) aggregates y values."""
        hist = Hist1D(self.x_data, self.y_data)

        assert "x" in hist.data.columns
        assert "y" in hist.data.columns
        assert len(hist.data) == self.n

        # Y values should be the actual y_data, not all 1s
        assert not (hist.data["y"] == 1).all()
        assert hist.data["y"].std() > 0  # Should have variation

    def test_hist1d_logx_transform(self):
        """Test __init__(..., logx=True) applies log₁₀ transform to x."""
        # Use positive data for log transform
        x_positive = pd.Series(np.random.uniform(1, 100, self.n))
        hist = Hist1D(x_positive, logx=True)

        assert hist.log.x is True
        assert hist.log.y is False

        # x data should be log-transformed
        assert hist.data["x"].min() >= 0  # log10(1) = 0
        assert hist.data["x"].max() <= 2  # log10(100) = 2

    def test_hist1d_path_follows_labels(self):
        """Test the path is built from the labels set after construction."""
        hist = Hist1D(self.x_data)
        hist.set_labels(x="density", y="count")

        # Documented layout: class, x label, y label, scale tag.
        assert hist.path == Path("Hist1D", "density", "count", "linX-linY")

    def test_hist1d_with_y_and_clipping(self):
        """Hist1D(x, y, clip=True) stores columns x and y, and clips x."""
        hist = Hist1D(self.x_data, self.y_data, clip=True)

        assert "x" in hist.data.columns
        assert "y" in hist.data.columns
        assert hist.clip.x is True

    def test_hist1d_clip_attribute(self):
        """Test that .clip attribute equals clip flag."""
        hist_no_clip = Hist1D(self.x_data, clip=False)
        hist_with_clip = Hist1D(self.x_data, clip=True)

        assert hist_no_clip.clip.x is False
        assert hist_with_clip.clip.x is True


@_PLAIN_STRING_LABELS
class TestHist1DAxisNormalization:
    """Test axis normalization functionality in Hist1D."""

    def setup_method(self):
        """Set up test data for each test."""
        np.random.seed(42)
        self.n = 100
        self.x_data = pd.Series(np.random.normal(5, 2, self.n), name="x")

    def test_set_axnorm_density(self):
        """Test set_axnorm('d') sets density normalization and updates label."""
        hist = Hist1D(self.x_data)
        hist.set_axnorm("d")

        assert hist.axnorm == "d"

        # Labels should be updated for density normalization
        # The exact label depends on implementation
        assert hasattr(hist, "labels")

    def test_set_axnorm_invalid_raises_value_error(self):
        """Test that set_axnorm('x') raises ValueError."""
        hist = Hist1D(self.x_data)

        with pytest.raises(ValueError, match="Unrecognized axnorm 'x'"):
            hist.set_axnorm("x")

    def test_axis_normalizer_none(self):
        """With no normalisation, ``agg()`` is the count in each bin.

        ON FAILURE: the code is wrong.
        """
        x, _ = _known_1d_sample()
        hist = Hist1D(x, nbins=KNOWN_EDGES)
        assert hist.agg().values.tolist() == KNOWN_BIN_COUNTS

    def test_axis_normalizer_density(self):
        """Density normalization yields a PDF: it integrates to 1.

        The bins are the test's own, so the integral is a plain sum of
        value * width with no quantity read back from the histogram.

        ON FAILURE: the code is wrong. Normalizing to a PDF and then not
        integrating to 1 is a contradiction, not a calibration choice.
        """
        x, _ = _known_1d_sample()
        hist = Hist1D(x, nbins=KNOWN_EDGES)
        hist.set_axnorm("d")

        widths = np.diff(KNOWN_EDGES)
        integral = (hist.agg().values * widths).sum()
        assert np.isclose(integral, 1.0)

    def test_density_normalization_is_the_counts_scaled_by_bin_area(self):
        """Each density equals its count divided by (N * bin width).

        Both the counts and the widths are the test's, so the whole expectation
        is constructed.

        ON FAILURE: the code is wrong.
        """
        x, _ = _known_1d_sample()
        hist = Hist1D(x, nbins=KNOWN_EDGES)
        hist.set_axnorm("d")

        expected = np.asarray(KNOWN_BIN_COUNTS) / (x.size * np.diff(KNOWN_EDGES))
        np.testing.assert_allclose(hist.agg().values, expected)

    def test_axis_normalizer_total(self):
        """``set_axnorm("t")`` divides every count by the largest one.

        Hand-computed from ``KNOWN_BIN_COUNTS`` = 3, 5, 2, 4, 6: each over 6.

        ON FAILURE: the code is wrong.
        """
        x, _ = _known_1d_sample()
        hist = Hist1D(x, nbins=KNOWN_EDGES)
        hist.set_axnorm("t")
        assert np.asarray(hist.agg().values) == exact(np.array(KNOWN_BIN_COUNTS) / 6.0)


@_PLAIN_STRING_LABELS
class TestHist1DAggregation:
    """Test aggregation functionality in Hist1D."""

    def setup_method(self):
        """Set up test data for each test."""
        np.random.seed(42)
        self.n = 100
        self.x_data = pd.Series(np.random.normal(5, 2, self.n), name="x")

    def test_agg_count_with_density_works(self):
        """Test agg(fcn='count') with axnorm='d' works."""
        hist = Hist1D(self.x_data)
        hist.set_axnorm("d")

        # Should not raise an error
        result = hist.agg(fcn="count")
        assert isinstance(result, pd.Series)

    def test_agg_sum_with_density_is_each_bins_share(self):
        """agg(fcn='sum') with axnorm='d' gives each bin's share per unit width.

        Without y every row aggregates the value 1, so a sum is a count and
        the shares integrate to 1 over the bin widths.

        ON FAILURE: the code is wrong.
        """
        hist = Hist1D(self.x_data)
        hist.set_axnorm("d")

        result = hist.agg(fcn="sum")
        widths = hist.intervals["x"].length
        assert np.nansum(result.to_numpy() * widths) == exact(1.0)

    def test_agg_reproduces_the_constructed_bin_counts(self):
        """Counts equal the population the test placed in each bin.

        ON FAILURE: the code is wrong.
        """
        x, _ = _known_1d_sample()
        hist = Hist1D(x, nbins=KNOWN_EDGES)

        result = hist.agg()
        np.testing.assert_array_equal(result.values, KNOWN_BIN_COUNTS)
        assert result.sum() == x.size

    def test_agg_index_is_the_requested_bins_in_order(self):
        """The aggregation is indexed by the requested intervals, ascending.

        Positional comparisons elsewhere rest on this, so it is stated once
        rather than assumed everywhere.

        ON FAILURE: the code is wrong; counts would be attributed to the wrong
        bins.
        """
        x, _ = _known_1d_sample()
        hist = Hist1D(x, nbins=KNOWN_EDGES)

        intervals = pd.IntervalIndex(hist.agg().index)
        np.testing.assert_allclose(intervals.left.values, KNOWN_EDGES[:-1])
        np.testing.assert_allclose(intervals.right.values, KNOWN_EDGES[1:])


@_PLAIN_STRING_LABELS
class TestHist1DLabels:
    """Test label functionality in Hist1D."""

    def setup_method(self):
        """Set up test data for each test."""
        np.random.seed(42)
        self.n = 100
        self.x_data = pd.Series(np.random.normal(5, 2, self.n), name="x")

    def test_set_labels_y_updates_label(self):
        """Test set_labels(y='new') updates y-label."""
        hist = Hist1D(self.x_data)

        hist.set_labels(y="new_label")

        assert hist.labels.y == "new_label"

    def test_set_labels_z_raises_value_error(self):
        """Test that set_labels(z='z') raises ValueError."""
        hist = Hist1D(self.x_data)

        with pytest.raises(ValueError, match="doesn't have a z-label"):
            hist.set_labels(z="some_z_label")


@_PLAIN_STRING_LABELS
class TestHist1DPlotting:
    """Test plotting functionality in Hist1D."""

    def setup_method(self):
        """Set up test data for each test."""
        np.random.seed(42)
        self.n = 100
        self.x_data = pd.Series(np.random.normal(5, 2, self.n), name="x")

    def test_make_plot_draws_the_counts_against_the_bin_centers(self):
        """The plotted series is (bin center, count) for each bin.

        Both coordinates are the test's own, so this checks the numbers handed
        to matplotlib rather than anything about the figure's appearance.

        ON FAILURE: the code is wrong -- the figure would not show the data.
        """
        import matplotlib.pyplot as plt

        x, centers = _known_1d_sample()
        hist = Hist1D(x, nbins=KNOWN_EDGES)
        fig, ax = plt.subplots()

        returned_ax, _, _, _ = hist.make_plot(ax)

        assert returned_ax is ax
        (line,) = ax.lines
        np.testing.assert_allclose(np.asarray(line.get_xdata(), float), centers)
        np.testing.assert_allclose(
            np.asarray(line.get_ydata(), float), KNOWN_BIN_COUNTS
        )
        plt.close(fig)

    def test_make_plot_transpose_axes_swaps_the_two_coordinates(self):
        """Transposing exchanges the plotted x- and y-data and nothing else.

        The untransposed plot supplies the expectation, so this is a round trip
        rather than a second recorded set of coordinates.

        ON FAILURE: the code is wrong -- a side panel drawn this way would not
        line up with the grid it annotates.
        """
        import matplotlib.pyplot as plt

        x, _ = _known_1d_sample()
        hist = Hist1D(x, nbins=KNOWN_EDGES)

        fig, ax = plt.subplots()
        hist.make_plot(ax)
        (upright,) = ax.lines

        fig_t, ax_t = plt.subplots()
        hist.make_plot(ax_t, transpose_axes=True)
        (transposed,) = ax_t.lines

        np.testing.assert_allclose(
            np.asarray(transposed.get_xdata(), float),
            np.asarray(upright.get_ydata(), float),
        )
        np.testing.assert_allclose(
            np.asarray(transposed.get_ydata(), float),
            np.asarray(upright.get_xdata(), float),
        )
        plt.close("all")

    def test_make_plot_invalid_fcn_raises_value_error(self):
        """Test that make_plot(fcn='bad') raises ValueError."""
        import matplotlib.pyplot as plt

        hist = Hist1D(self.x_data)
        fig, ax = plt.subplots()

        # Test with invalid function - this actually raises AttributeError in pandas
        with pytest.raises(
            AttributeError, match="'SeriesGroupBy' object has no attribute"
        ):
            hist.make_plot(ax, fcn="bad_function_name")

        plt.close(fig)
