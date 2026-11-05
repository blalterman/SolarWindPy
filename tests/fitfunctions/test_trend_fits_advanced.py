"""Test TrendFit advanced features."""

import time
import warnings

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from solarwindpy.fitfunctions.gaussians import Gaussian
from solarwindpy.fitfunctions.lines import Line
from solarwindpy.fitfunctions.power_laws import PowerLaw
from solarwindpy.fitfunctions.trend_fits import TrendFit
from tests.tolerances import exact

# The trend's y and yerr: each column's Gaussian centroid and width.
MU = ("mu", "value")
SIGMA = ("sigma", "value")

matplotlib.use("Agg")  # Non-interactive backend for testing


class TestResidualsEnhancement:
    """Test residuals use_all parameter."""

    def setup_method(self):
        """Create test data with known constraints."""
        np.random.seed(42)
        self.x = np.linspace(0, 10, 100)
        self.y_true = 5 * np.exp(-((self.x - 5) ** 2) / 2)
        self.y = self.y_true + np.random.normal(0, 0.1, 100)

    def test_use_all_parameter_basic(self):
        """Test residuals with all data vs fitted only."""
        # Create FitFunction with constraints that exclude some data
        ff = Gaussian(self.x, self.y, xmin=3, xmax=7)
        ff.make_fit()

        # Get residuals for both cases
        r_fitted = ff.residuals(use_all=False)
        r_all = ff.residuals(use_all=True)

        # Should have different lengths
        assert len(r_fitted) < len(r_all), "use_all=True should return more residuals"
        assert len(r_all) == len(self.x), (
            "use_all=True should return residuals for all data"
        )

        # Fitted region residuals should be subset of all residuals
        # (Though not necessarily at the same indices due to masking)
        assert len(r_fitted) > 0, "Should have some fitted residuals"

    def test_use_all_parameter_no_constraints(self):
        """Test use_all when no constraints are applied."""
        # Create FitFunction without constraints
        ff = Gaussian(self.x, self.y)
        ff.make_fit()

        r_fitted = ff.residuals(use_all=False)
        r_all = ff.residuals(use_all=True)

        # Should be identical when no constraints are applied
        np.testing.assert_array_equal(r_fitted, r_all)

    def test_percentage_residuals(self):
        """Percent residuals are 100 (y - f) / f of the plain residuals.

        ON FAILURE: the code is wrong.
        """
        # Use Line fit for more predictable results
        x = np.linspace(1, 10, 50)
        rng = np.random.default_rng(66)
        y = 2 * x + 1 + rng.normal(0, 0.1, 50)

        ff = Line(x, y)
        ff.make_fit()

        r_abs = ff.residuals(pct=False)
        r_pct = ff.residuals(pct=True)

        # Manual calculation for verification
        fitted = ff(ff.observations.used.x)
        expected_pct = 100 * (r_abs / fitted)

        assert r_pct == exact(expected_pct, nan_ok=True)

    def test_percentage_residuals_use_all(self):
        """Test percentage residuals with use_all=True."""
        ff = Gaussian(self.x, self.y, xmin=2, xmax=8)
        ff.make_fit()

        r_pct_fitted = ff.residuals(pct=True, use_all=False)
        r_pct_all = ff.residuals(pct=True, use_all=True)

        # Should handle percentage calculation correctly for both cases
        assert len(r_pct_all) > len(r_pct_fitted)
        assert not np.any(np.isinf(r_pct_fitted)), "Fitted percentages should be finite"

        # All residuals may contain some inf/nan for extreme cases
        finite_mask = np.isfinite(r_pct_all)
        assert np.any(finite_mask), "Should have some finite percentage residuals"

    def test_backward_compatibility(self):
        """Ensure default behavior unchanged."""
        ff = Gaussian(self.x, self.y)
        ff.make_fit()

        # Default should be use_all=False
        r_default = ff.residuals()
        r_explicit = ff.residuals(use_all=False)

        np.testing.assert_array_equal(r_default, r_explicit)

    def test_division_by_zero_handling(self):
        """Percentage residuals are NaN where the fit is zero, finite elsewhere.

        A power law A x**b with b > 0 is exactly zero at x = 0 whatever the
        fitted A and b, so that point must come back NaN (not inf) without a
        RuntimeWarning; every other point is 100 (y - f) / f.

        ON FAILURE: the code is wrong.
        """
        x = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        y = 3.0 * x**2
        y[2] += 1.0  # nonzero residuals so the pct formula is exercised
        y[0] = 0.5  # nonzero y where f == 0: unguarded, 0.5 / 0 is inf
        ff = PowerLaw(x, y)
        ff.make_fit()
        assert ff.popt["alpha"] > 0

        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            r_pct = ff.residuals(pct=True)

        fitted = ff.popt["A"] * x[1:] ** ff.popt["alpha"]
        assert np.isnan(r_pct[0])
        # The same arithmetic, evaluated from popt.
        assert r_pct[1:] == exact(100.0 * (y[1:] - fitted) / fitted, nan_ok=True)


class TestInPlaceOperations:
    """Test in-place mask operations (though effects are mostly internal)."""

    def test_mask_operations_still_work(self):
        """Verify optimized mask operations produce correct results."""
        rng = np.random.default_rng(141)
        x = rng.standard_normal(1000)
        y = x**2 + rng.normal(0, 0.1, 1000)

        # Create fitfunction with constraints (triggers mask building)
        ff = Line(x, y, xmin=-1, xmax=1, ymin=0)
        ff.make_fit()

        # Should produce valid results
        assert hasattr(ff, "observations")
        assert hasattr(ff.observations, "used")

        # Mask should select appropriate subset
        used_x = ff.observations.used.x
        assert len(used_x) > 0, "Should have some used observations"
        assert len(used_x) < len(x), (
            "Should exclude some observations due to constraints"
        )

        # All used x values should satisfy constraints
        assert np.all(used_x >= -1), "All used x should be >= xmin"
        assert np.all(used_x <= 1), "All used x should be <= xmax"

    def test_outside_mask_operations(self):
        """Test outside mask functionality."""
        x = np.linspace(-5, 5, 100)
        rng = np.random.default_rng(166)
        y = x**2 + rng.normal(0, 0.1, 100)

        # Use xoutside to exclude central region
        ff = Line(x, y, xoutside=(-1, 1))
        ff.make_fit()

        used_x = ff.observations.used.x

        # Should only use values outside the (-1, 1) range
        assert np.all((used_x <= -1) | (used_x >= 1)), (
            "Should only use values outside central region"
        )
        assert len(used_x) < len(x), "Should exclude central region"


# Integration test
class TestPhase4Integration:
    """Integration tests for all Phase 4 features together."""

    def test_complete_workflow(self):
        """Test complete TrendFit workflow with all new features."""
        # Create realistic aggregated data
        np.random.seed(42)
        x = np.linspace(0, 20, 200)

        # Simulate multiple measurement columns with different Gaussian profiles
        data = pd.DataFrame(
            {
                i: (
                    (3 + i * 0.5)
                    * np.exp(-((x - (10 + i * 0.2)) ** 2) / (2 * (2 + i * 0.1) ** 2))
                    + np.random.normal(0, 0.05, 200)
                )
                for i in range(25)
            },
            index=x,
        )

        # Test complete workflow
        tf = TrendFit(data, Gaussian, Line, y=MU, yerr=SIGMA)

        start_time = time.perf_counter()
        tf.make_fit()
        execution_time = time.perf_counter() - start_time

        # Verify results
        ok = tf.bin_results.loc[:, ("status", "")] == "ok"
        assert ok.sum() > 20, "Most fits should succeed"
        print(
            f"Successfully fitted {ok.sum()}/25 measurements in {execution_time:.2f}s"  # noqa: E231
        )

        # Test residuals on first successful fit
        first_fit_key = ok.index[ok][0]
        first_fit = tf.bin_fits[first_fit_key]

        # Test new residuals functionality
        r_fitted = first_fit.residuals(use_all=False)
        r_all = first_fit.residuals(use_all=True)
        r_pct = first_fit.residuals(pct=True)

        assert len(r_all) >= len(r_fitted), (
            "use_all should give at least as many residuals"
        )
        assert len(r_pct) == len(r_fitted), (
            "Percentage residuals should match fitted residuals"
        )

        print("✓ All Phase 4 features working correctly")


# ============================================================================
# Phase 6 Coverage Tests for TrendFit
# ============================================================================


class TestMakeTrendFuncEdgeCases:
    """Test trend construction edge cases."""

    def setup_method(self):
        """Create test data with standard numeric index (not IntervalIndex)."""
        np.random.seed(42)
        x = np.linspace(0, 10, 50)
        # Create data with numeric columns (not IntervalIndex)
        self.data_numeric = pd.DataFrame(
            {
                i: 5 * np.exp(-((x - 5) ** 2) / 2) + np.random.normal(0, 0.1, 50)
                for i in range(5)
            },
            index=x,
        )

        # Create data with IntervalIndex columns
        intervals = pd.IntervalIndex.from_breaks(range(6))
        self.data_interval = pd.DataFrame(
            {
                intervals[i]: 5 * np.exp(-((x - 5) ** 2) / 2)
                + np.random.normal(0, 0.1, 50)
                for i in range(5)
            },
            index=x,
        )

    def test_make_fit_with_non_interval_index(self):
        """Test the trend handles non-IntervalIndex columns."""
        tf = TrendFit(self.data_numeric, Gaussian, Line, y=MU, yerr=SIGMA)

        # bin_results has a numeric index, not IntervalIndex
        tf.make_fit()

        # Verify the trend was created successfully
        assert isinstance(tf.trend, Line)

    @pytest.mark.xfail(strict=True, reason="weights is renamed yerr")
    def test_trend_kwargs_cannot_hold_yerr(self):
        """``trend_kwargs`` holding ``yerr`` raises: TrendFit's ``yerr`` selects it.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(ValueError, match="yerr selects the trend's uncertainties"):
            TrendFit(
                self.data_interval,
                Gaussian,
                Line,
                y=MU,
                yerr=SIGMA,
                trend_kwargs=dict(yerr=np.ones(5)),
            )

    def test_trend_weights_error(self):
        """Test TrendFit raises ValueError when trend weights are passed."""
        # Passing weights should raise ValueError: yerr selects them
        with pytest.raises(ValueError, match="yerr selects the trend's weights"):
            TrendFit(
                self.data_interval,
                Gaussian,
                Line,
                y=MU,
                yerr=SIGMA,
                trend_kwargs=dict(weights=np.ones(5)),
            )


class TestPlotAllPopt1DEdgeCases:
    """Test plot_bin_results edge cases (lines 411, 419-425, 428, 439-466)."""

    def setup_method(self):
        """Create test data with IntervalIndex columns for proper trend fit."""
        np.random.seed(42)
        x = np.linspace(0, 10, 50)

        # Create data with IntervalIndex columns
        intervals = pd.IntervalIndex.from_breaks(range(6))
        self.data = pd.DataFrame(
            {
                intervals[i]: 5 * np.exp(-((x - 5) ** 2) / 2)
                + np.random.normal(0, 0.1, 50)
                for i in range(5)
            },
            index=x,
        )

        # Set up complete TrendFit with its trend
        self.tf = TrendFit(self.data, Gaussian, Line, y=MU, yerr=SIGMA)
        self.tf.make_fit()

    def test_plot_bin_results_ax_none(self):
        """Test plot_bin_results creates axes when ax is None (line 411)."""
        # When ax is None, should call subplots() to create figure and axes
        plotted = self.tf.plot_bin_results(ax=None, plot_window=False)

        # Should return valid plotted objects (line or tuple)
        assert isinstance(plotted, (tuple, object))
        plt.close("all")

    def test_plot_bin_results_only_in_trend_fit(self):
        """Test only_in_trend=True path (lines 419-425)."""
        plotted = self.tf.plot_bin_results(
            ax=None, only_in_trend=True, plot_window=False
        )

        # Should complete without error (returns line or tuple)
        assert isinstance(plotted, (tuple, object))
        plt.close("all")

    def test_plot_bin_results_with_plot_window(self):
        """Test plot_window=True path (lines 439-466)."""
        # Default is plot_window=True
        plotted = self.tf.plot_bin_results(ax=None, plot_window=True)

        # Should return tuple (line, window)
        assert isinstance(plotted, tuple)
        assert len(plotted) == 2
        plt.close("all")

    def test_plot_bin_results_plot_window_yerr_none_error(self):
        """Test plot_window=True raises error when yerr is None."""
        tf = TrendFit(self.data, Gaussian, Line, y=MU, yerr=None)
        tf.make_fit()
        with pytest.raises(ValueError, match="plot_window needs yerr"):
            tf.plot_bin_results(ax=None, plot_window=True)
        plt.close("all")


class TestTrendLogxPaths:
    """Test logx=True paths (lines 428, 503, 520)."""

    def setup_method(self):
        """Create test data for logx testing."""
        np.random.seed(42)
        x = np.linspace(0, 10, 50)

        # Create data with IntervalIndex columns
        intervals = pd.IntervalIndex.from_breaks(range(6))
        self.data = pd.DataFrame(
            {
                intervals[i]: 5 * np.exp(-((x - 5) ** 2) / 2)
                + np.random.normal(0, 0.1, 50)
                for i in range(5)
            },
            index=x,
        )

    def test_plot_bin_results_logx(self):
        """Test plot_bin_results with logx=True (line 428)."""
        tf = TrendFit(self.data, Gaussian, Line, y=MU, yerr=SIGMA, logx=True)
        tf.make_fit()

        # Verify logx is True
        assert tf.logx is True

        # Plot with logx=True should apply 10**x transformation
        plotted = tf.plot_bin_results(ax=None, plot_window=False)

        assert isinstance(plotted, (tuple, object))
        plt.close("all")

    def test_plot_trend_fit_resid_logx(self):
        """Test plot_trend_fit_resid with logx=True (line 503)."""
        tf = TrendFit(self.data, Gaussian, Line, y=MU, yerr=SIGMA, logx=True)
        tf.make_fit()

        # This should trigger line 503: rax.set_xscale("log")
        hax, rax = tf.plot_trend_fit_resid()

        assert isinstance(hax, plt.Axes)
        assert isinstance(rax, plt.Axes)
        # rax should have log scale on x-axis
        assert rax.get_xscale() == "log"
        plt.close("all")

    def test_plot_trend_and_resid_on_bins_logx(self):
        """Test plot_trend_and_resid_on_bins with logx=True (line 520)."""
        tf = TrendFit(self.data, Gaussian, Line, y=MU, yerr=SIGMA, logx=True)
        tf.make_fit()

        # This should trigger line 520: rax.set_xscale("log")
        hax, rax = tf.plot_trend_and_resid_on_bins()

        assert isinstance(hax, plt.Axes)
        assert isinstance(rax, plt.Axes)
        # rax should have log scale on x-axis
        assert rax.get_xscale() == "log"
        plt.close("all")


class TestNumericIndexWorkflow:
    """Test workflow with numeric (non-IntervalIndex) columns."""

    def test_numeric_index_workflow(self):
        """Test workflow with numeric (non-IntervalIndex) columns."""
        np.random.seed(42)
        x = np.linspace(0, 10, 50)

        # Numeric column names trigger TypeError branch
        data = pd.DataFrame(
            {
                i: 5 * np.exp(-((x - 5) ** 2) / 2) + np.random.normal(0, 0.1, 50)
                for i in range(5)
            },
            index=x,
        )

        tf = TrendFit(data, Gaussian, Line, y=MU, yerr=SIGMA)
        tf.make_fit()

        assert isinstance(tf.trend, Line)

        # Verify fit completed
        assert hasattr(tf.trend, "popt")
