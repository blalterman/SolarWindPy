#!/usr/bin/env python
"""Tests for the Hist1D and Hist2D histogram plotters."""

from pathlib import Path

import pytest
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")

from solarwindpy.plotting.agg_plot import AggPlot  # noqa: E402
from solarwindpy.plotting.hist1d import Hist1D  # noqa: E402
from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402

# Bins chosen by the test, so every count below is an input rather than a
# recorded output. The edges are exact at the 5 decimal places at which
# `calc_bins_intervals` stores interval endpoints.
KNOWN_EDGES = np.array([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
KNOWN_BIN_COUNTS = [3, 5, 2, 4, 6]


def _known_1d_sample():
    """Points placed at bin centers to realise ``KNOWN_BIN_COUNTS``."""
    centers = 0.5 * (KNOWN_EDGES[:-1] + KNOWN_EDGES[1:])
    values = []
    for center, count in zip(centers, KNOWN_BIN_COUNTS):
        values.extend([center] * count)
    return pd.Series(values, name="x"), centers


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

    def test_hist1d_set_path_auto(self):
        """Test set_path('auto') builds path from labels."""
        hist = Hist1D(self.x_data)
        hist.set_labels(x="density", y="count")

        hist.set_path("auto")

        # Documented layout: class, x label, y label, scale tag.
        assert hist.path == Path("Hist1D", "density", "count", "linX")

    def test_hist1d_set_path_custom(self):
        """Test set_path('custom', add_scale=False) sets _path to Path('custom')."""
        from pathlib import Path

        hist = Hist1D(self.x_data)
        hist.set_path("custom", add_scale=False)

        # Should have the custom path
        assert hist.path == Path("custom")

    def test_hist1d_set_data_with_clipping(self):
        """Test set_data(x, y, clip=True) stores DataFrame with columns x,y & clip."""
        hist = Hist1D(self.x_data)
        hist.set_data(self.x_data, self.y_data, clip=True)

        assert "x" in hist.data.columns
        assert "y" in hist.data.columns
        assert hist.clip is True

    def test_hist1d_clip_attribute(self):
        """Test that .clip attribute equals clip flag."""
        hist_no_clip = Hist1D(self.x_data, clip_data=False)
        hist_with_clip = Hist1D(self.x_data, clip_data=True)

        assert hist_no_clip.clip is False
        assert hist_with_clip.clip is True


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

    def test_set_axnorm_invalid_raises_assertion_error(self):
        """Test that set_axnorm('x') raises AssertionError."""
        hist = Hist1D(self.x_data)

        with pytest.raises(AssertionError):
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
        # rel=1e-12: one division of small integers.
        np.testing.assert_allclose(
            hist.agg().values, np.array(KNOWN_BIN_COUNTS) / 6.0, rtol=1e-12, atol=0
        )


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

    def test_agg_sum_with_density_raises_value_error(self):
        """Test that agg(fcn='sum', axnorm='d') raises ValueError."""
        hist = Hist1D(self.x_data)
        hist.set_axnorm("d")

        with pytest.raises(
            ValueError, match="Unable to calculate a PDF with non-count aggregation"
        ):
            hist.agg(fcn="sum")

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

        returned_ax, _ = hist.make_plot(ax)

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


class TestHist2DBasicFunctionality:
    """Test basic functionality of Hist2D."""

    def setup_method(self):
        """Set up test data for each test."""
        np.random.seed(42)
        self.n = 100
        self.x_data = pd.Series(np.random.normal(5, 2, self.n), name="x")
        self.y_data = pd.Series(np.random.normal(10, 3, self.n), name="y")
        self.z_data = pd.Series(np.random.normal(1, 0.5, self.n), name="z")

    def test_hist2d_instantiation_count_heatmap(self):
        """Test __init__(x, y) produces 2D count heatmap."""
        hist = Hist2D(self.x_data, self.y_data)

        # Should have x, y, and z columns (z=1 for counting)
        assert "x" in hist.data.columns
        assert "y" in hist.data.columns
        assert "z" in hist.data.columns
        assert len(hist.data) == self.n

        # For count heatmap, all z values should be 1
        assert (hist.data["z"] == 1).all()

    def test_hist2d_instantiation_aggregation_heatmap(self):
        """Test __init__(x, y, z) aggregates mean of z."""
        hist = Hist2D(self.x_data, self.y_data, self.z_data)

        assert "x" in hist.data.columns
        assert "y" in hist.data.columns
        assert "z" in hist.data.columns
        assert len(hist.data) == self.n

        # Z values should be the actual z_data, not all 1s
        assert not (hist.data["z"] == 1).all()
        assert hist.data["z"].std() > 0  # Should have variation

    def test_hist2d_log_scale_conversion(self):
        """``logx``/``logy`` store log10 coordinates and set both log flags.

        ON FAILURE: the code is wrong.
        """
        # Use positive data for log transform
        x_positive = pd.Series(np.random.uniform(1, 100, self.n))
        y_positive = pd.Series(np.random.uniform(1, 100, self.n))

        hist = Hist2D(x_positive, y_positive, logx=True, logy=True)

        assert hist.log.x is True
        assert hist.log.y is True

        # The stored coordinates are log10 of the inputs, which lie in [1, 100).
        assert hist.data["x"].between(0, 2).all()
        assert hist.data["y"].between(0, 2).all()

    def test_hist2d_set_data_with_log_transform(self):
        """Test set_data(x, y, z, clip) applies log transform."""
        # Use positive data for log transform
        x_positive = pd.Series(np.random.uniform(1, 100, self.n))
        y_positive = pd.Series(np.random.uniform(1, 100, self.n))

        hist = Hist2D(x_positive, y_positive, logx=True, logy=True)

        # Data should be log-transformed
        assert hist.data["x"].min() >= 0  # log10(1) = 0
        assert hist.data["x"].max() <= 2  # log10(100) = 2
        assert hist.data["y"].min() >= 0
        assert hist.data["y"].max() <= 2

    def test_hist2d_set_labels_z(self):
        """Test set_labels(z='z') updates z-label."""
        hist = Hist2D(self.x_data, self.y_data)

        hist.set_labels(z="new_z_label")

        assert hist.labels.z == "new_z_label"


class TestHist2DAxisNormalization:
    """Test axis normalization functionality in Hist2D."""

    def setup_method(self):
        """Set up test data for each test."""
        np.random.seed(42)
        self.n = 100
        self.x_data = pd.Series(np.random.normal(5, 2, self.n), name="x")
        self.y_data = pd.Series(np.random.normal(10, 3, self.n), name="y")

    def test_set_axnorm_valid_options(self):
        """Test that set_axnorm('c'), 'r', 't', 'd' work; invalid → AssertionError."""
        hist = Hist2D(self.x_data, self.y_data)

        # Valid options should work
        valid_options = ["c", "r", "t", "d"]
        for option in valid_options:
            hist.set_axnorm(option)
            assert hist.axnorm == option

        # Invalid option should raise AssertionError
        with pytest.raises(AssertionError):
            hist.set_axnorm("invalid")

    @pytest.mark.parametrize(
        "axnorm, along",
        [("c", "columns"), ("r", "rows")],
    )
    def test_column_and_row_normalization_put_a_one_in_every_line(self, axnorm, along):
        """Dividing by a maximum leaves exactly that maximum equal to 1.

        "c" divides each column by its own maximum and "r" each row by its own,
        so every populated column (respectively row) must peak at 1. Naming both
        cases in one parametrization also catches the two being swapped.

        ON FAILURE: the code is wrong.
        """
        hist = Hist2D(self.x_data, self.y_data, nbins=6, axnorm=axnorm)
        grid = hist.agg().unstack("x")

        axis = 0 if along == "columns" else 1
        maxima = grid.max(axis=axis).dropna()
        assert maxima.size > 0
        np.testing.assert_allclose(maxima.values, 1.0)

    def test_total_normalization_puts_a_single_one_in_the_grid(self):
        """Total normalization divides the grid by its maximum, so a bin holds 1.

        ON FAILURE: the code is wrong -- it is normalizing per-axis rather than
        over the whole grid.
        """
        hist = Hist2D(self.x_data, self.y_data, nbins=6, axnorm="t")
        values = hist.agg().dropna()

        assert np.isclose(values.max(), 1.0)
        assert (values > 1.0).sum() == 0

    def test_density_normalization_integrates_to_one(self):
        """Density normalization makes a 2D PDF: sum of value * bin area is 1.

        The bin areas come from the edges the test supplied, so the integral is
        computed independently of the histogram.

        ON FAILURE: the code is wrong.
        """
        edges = np.round(np.linspace(0.0, 20.0, 9), 5)
        hist = Hist2D(self.x_data, self.y_data, nbins=[edges, edges], axnorm="d")
        agg = hist.agg()

        # Unpopulated bins are absent from the aggregation, so the areas are
        # taken per surviving bin rather than from the full outer product.
        x_bins = pd.IntervalIndex(agg.index.get_level_values("x"))
        y_bins = pd.IntervalIndex(agg.index.get_level_values("y"))
        assert np.isin(x_bins.left.values, edges).all()
        assert np.isin(y_bins.left.values, edges).all()

        integral = np.nansum(agg.values * x_bins.length.values * y_bins.length.values)
        assert np.isclose(integral, 1.0)

    def test_axis_normalizer_invalid_raises_value_error(self):
        """Test that _axis_normalizer('bad') raises ValueError."""
        hist = Hist2D(self.x_data, self.y_data)
        # Hist2D raises AssertionError in set_axnorm, not ValueError
        # So we test AssertionError instead
        with pytest.raises(AssertionError, match="Unrecgonized axnorm"):
            hist.set_axnorm("bad")


class TestModuleIntegration:
    """Test integration between different histogram plotters."""

    def test_hist1d_inherits_from_aggplot(self):
        """Test that Hist1D properly inherits from AggPlot."""
        assert issubclass(Hist1D, AggPlot)

        # Create instance and verify it has AggPlot methods
        np.random.seed(42)
        x_data = pd.Series(np.random.normal(5, 2, 100))
        hist = Hist1D(x_data)

        # Should have AggPlot methods
        assert hasattr(hist, "agg")
        assert hasattr(hist, "edges")
        assert hasattr(hist, "intervals")
        assert hasattr(hist, "categoricals")

    def test_hist2d_inherits_from_aggplot(self):
        """Test that Hist2D properly inherits from AggPlot."""
        assert issubclass(Hist2D, AggPlot)

        # Create instance and verify it has AggPlot methods
        np.random.seed(42)
        x_data = pd.Series(np.random.normal(5, 2, 100))
        y_data = pd.Series(np.random.normal(10, 3, 100))
        hist = Hist2D(x_data, y_data)

        # Should have AggPlot methods
        assert hasattr(hist, "agg")
        assert hasattr(hist, "edges")
        assert hasattr(hist, "intervals")
        assert hasattr(hist, "categoricals")


if __name__ == "__main__":
    pytest.main([__file__])
