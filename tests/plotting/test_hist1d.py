# Spent-When: PERMANENT(the repository stops shipping Hist1D)
# Supersedes: none
"""Contract tests for :class:`solarwindpy.plotting.hist1d.Hist1D`.

Every expected count is re-derived from :func:`numpy.histogram` (or a plain
boolean mask) on the same input, and the bins are deliberately unequal in
width so that an error in a bin width, a bin center, or a bin assignment
cannot cancel out.

Hist1D bins are right-closed, ``(a, b]``, where ``numpy.histogram`` bins are
left-closed ``[a, b)``. The two agree whenever no sample sits exactly on an
edge, which holds with probability one for the continuous random samples used
here.
"""

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from scipy.ndimage import gaussian_filter  # noqa: E402

from solarwindpy.plotting.hist1d import Hist1D  # noqa: E402

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

    @pytest.mark.xfail(
        strict=True,
        raises=_CountsDisagreeWithNumpy,
        reason=(
            "AggPlot.calc_bins_intervals (agg_plot.py) derives integer-nbins "
            "edges from the data range, rounds them to 5 decimals (which can "
            "pull either outer edge inside the data) and closes intervals on "
            "the right (which excludes a sample on the first edge), so "
            "make_cut's pd.cut drops the extreme samples; this input counts "
            "398 of 400; remove this marker when the outer edges enclose "
            "every sample (both the rounding and the left end must change)"
        ),
    )
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

        # Tolerance: summation-order differences in a 400-sample mean.
        np.testing.assert_allclose(
            agg.values, _per_bin(x, y, np.mean), rtol=1e-12, atol=0
        )

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
        # Tolerance: summation-order differences in a 400-sample mean.
        np.testing.assert_allclose(
            agg.values[keep], _per_bin(x, y, np.mean)[keep], rtol=1e-12, atol=0
        )


class TestDensity:
    def test_density_by_hand_on_unequal_bins(self):
        """Density is count / (N * width), checked on a hand-computed case.

        Edges [0, 1, 2, 4] hold 1, 2 and 1 of N = 4 samples, so the densities
        are 1/(4*1), 2/(4*1) and 1/(4*2).

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([0.5, 1.5, 1.625, 3.0])

        agg = Hist1D(x, axnorm="d", nbins=np.array([0.0, 1.0, 2.0, 4.0])).agg()

        # Tolerance: exact binary fractions, only rounding can differ.
        np.testing.assert_allclose(agg.values, [0.25, 0.5, 0.125], rtol=1e-12, atol=0)

    def test_density_is_count_over_total_and_width(self, xy):
        """Density equals numpy's counts / (N * width) and integrates to 1.

        ON FAILURE: the code is wrong.
        """
        x, _ = xy
        counts = _numpy_counts(x)
        widths = np.diff(EDGES)

        agg = Hist1D(x, axnorm="d", nbins=EDGES).agg()

        # Tolerance: one division per bin.
        np.testing.assert_allclose(
            agg.values, counts / (counts.sum() * widths), rtol=1e-12, atol=0
        )
        assert (agg.values * widths).sum() == pytest.approx(1.0, rel=1e-12, abs=0)

    @pytest.mark.xfail(
        strict=True,
        raises=_DensityNotNormalised,
        reason=(
            "Hist1D._axis_normalizer (hist1d.py) divides log-space counts by "
            "10**(log-space bin width), which is neither the log10 width nor "
            "the linear width, so a logx density integrates to 1 over neither "
            "variable; remove this marker when the logx density is normalised "
            "over log10(x) or over x (the author chooses which)"
        ),
    )
    def test_logx_density_integrates_to_one(self):
        """A logx density integrates to 1 over log10(x) or over x.

        Either normalisation is a PDF; the test accepts both and rejects any
        density that is a PDF over neither.

        ON FAILURE: the code is wrong.
        """
        rng = np.random.default_rng(7)
        x = pd.Series(10.0 ** rng.uniform(0.0, 2.0, 500))
        log_edges = np.array([0.0, 0.5, 0.75, 1.0, 1.5, 2.0])

        agg = Hist1D(x, logx=True, axnorm="d", nbins=log_edges).agg()

        over_log = (agg.values * np.diff(log_edges)).sum()
        over_linear = (agg.values * np.diff(10.0**log_edges)).sum()
        # Tolerance: a handful of float divisions and sums.
        if not (
            np.isclose(over_log, 1, rtol=1e-9) or np.isclose(over_linear, 1, rtol=1e-9)
        ):
            raise _DensityNotNormalised(
                f"integral over log10(x) = {over_log}, over x = {over_linear}"
            )


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
        # Tolerance: log10 then power round trip.
        np.testing.assert_allclose(
            line_x, np.sqrt(linear[:-1] * linear[1:]), rtol=1e-12, atol=0
        )
        np.testing.assert_array_equal(line_y, _numpy_counts(np.log10(x), log_edges))

    def test_without_an_axis_it_draws_the_counts_on_new_axes(self, xy):
        """``make_plot()`` with no axis returns new axes holding the counts.

        ON FAILURE: the code is wrong.
        """
        x, _ = xy

        ax, _ = Hist1D(x, nbins=EDGES).make_plot()

        line_x, line_y = _line_xy(ax.lines[0])
        np.testing.assert_allclose(line_x, _centers(), rtol=1e-12, atol=0)
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
        _, container = Hist1D(x, y, nbins=EDGES).make_plot(ax, fcn=fcn)

        line_x, line_y = _line_xy(container.lines[0])
        # Tolerance: summation-order differences in per-bin statistics.
        np.testing.assert_allclose(line_x, _centers(), rtol=1e-12, atol=0)
        np.testing.assert_allclose(line_y, expected_y, rtol=1e-12, atol=0)
        (bars,) = container.lines[2]
        segments = np.array(bars.get_segments())
        np.testing.assert_allclose(segments[:, :, 0].T, [_centers()] * 2, rtol=1e-12)
        np.testing.assert_allclose(
            np.sort(segments[:, :, 1], axis=1),
            np.column_stack([expected_y - expected_dy, expected_y + expected_dy]),
            rtol=1e-12,
            atol=0,
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

        # Tolerance: summation-order differences in the means.
        np.testing.assert_allclose(
            _line_xy(ax.lines[0])[1], expected, rtol=1e-12, atol=0
        )

    @pytest.mark.xfail(
        strict=True,
        raises=_SmoothedCountsTruncated,
        reason=(
            "Hist1D.make_plot (hist1d.py) passes integer counts to "
            "scipy.ndimage.gaussian_filter, whose output keeps the input dtype, "
            "so smoothed counts are truncated to integers; remove this marker "
            "when make_plot smooths a float copy of the aggregate"
        ),
    )
    def test_gaussian_smoothing_of_counts_is_not_truncated(self, xy):
        """Smoothed counts equal scipy's Gaussian filter of the float counts.

        ON FAILURE: the code is wrong.
        """
        x, _ = xy
        expected = gaussian_filter(_numpy_counts(x).astype(float), 1.0)

        _, ax = plt.subplots()
        Hist1D(x, nbins=EDGES).make_plot(ax, gaussian_filter_std=1.0)

        got = _line_xy(ax.lines[0])[1]
        # Tolerance: float convolution of small integers.
        if not np.allclose(got, expected, rtol=1e-12, atol=0):
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
        _, (line, band) = Hist1D(x, y, nbins=EDGES).make_plot(
            ax, fcn=("mean", "std"), plot_window=True
        )

        # Tolerance: summation-order differences in per-bin statistics.
        np.testing.assert_allclose(_line_xy(line[0])[1], mean, rtol=1e-12, atol=0)
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
        np.testing.assert_allclose(vertices, expected, rtol=1e-12, atol=0)

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
        # Tolerance: summation-order differences in per-bin statistics.
        np.testing.assert_allclose(_line_xy(central)[1], mean, rtol=1e-12, atol=0)
        np.testing.assert_allclose(_line_xy(upper)[1], mean + std, rtol=1e-12, atol=0)
        np.testing.assert_allclose(_line_xy(lower)[1], mean - std, rtol=1e-12, atol=0)

    @pytest.mark.xfail(
        strict=True,
        raises=TypeError,
        reason=(
            "Hist1D.make_plot (hist1d.py) swaps (dx, dy) under transpose_axes, "
            "so plot_window computes y - dy with dy None; expected "
            "'unsupported operand type(s) for -: ... NoneType'; remove this "
            "marker when the transposed window uses the swapped uncertainty"
        ),
    )
    def test_transposed_plot_window_spans_x_minus_to_plus_dx(self, xy):
        """Transposed, the band spans value -/+ error horizontally at each center.

        ON FAILURE: the code is wrong.
        """
        x, y = xy
        mean = _per_bin(x, y, np.mean)
        std = _per_bin(x, y, lambda s: np.std(s, ddof=1))

        _, ax = plt.subplots()
        _, (_, band) = Hist1D(x, y, nbins=EDGES).make_plot(
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
        np.testing.assert_allclose(vertices, expected, rtol=1e-12, atol=0)


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
        # Tolerance: one division per row.
        np.testing.assert_allclose(
            cdf["position"].values,
            np.linspace(0.0, 1.0, inside.size),
            rtol=1e-12,
            atol=0,
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

        # Tolerance: log10 then power round trip.
        np.testing.assert_allclose(
            cdf["x"].values, np.sort(x.values), rtol=1e-12, atol=0
        )

    def test_cdf_of_aggregated_y_raises_value_error(self, xy):
        """A cdf is refused when y holds values rather than counts.

        ON FAILURE: the code is wrong.
        """
        x, y = xy
        with pytest.raises(ValueError, match="Only able to convert data to a cdf"):
            Hist1D(x, y, nbins=EDGES).construct_cdf(only_plotted=False)

    def test_default_cdf_with_every_bin_plotted_is_the_whole_binned_sample(self, xy):
        """With every bin populated, the default cdf equals the unfiltered one.

        ON FAILURE: the code is wrong.
        """
        x, _ = xy
        hist = Hist1D(x, nbins=EDGES)

        pd.testing.assert_frame_equal(
            hist.construct_cdf(), hist.construct_cdf(only_plotted=False)
        )


def test_take_data_in_yrange_returns_labels_inside_each_bins_window(xy):
    """Each x bin keeps the samples whose y lies in that bin's (bottom, top].

    Bottoms differ from bin to bin, so a window applied to the wrong bin
    selects a different set; the result is index labels, not positions.

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
