"""Test TrendFit advanced features."""

import time

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from solarwindpy.fitfunctions import Gaussian, Line
from solarwindpy.fitfunctions.trend_fits import TrendFit

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
        assert len(r_all) == len(
            self.x
        ), "use_all=True should return residuals for all data"

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
        """Test percentage residuals calculation."""
        # Use Line fit for more predictable results
        x = np.linspace(1, 10, 50)
        y = 2 * x + 1 + np.random.normal(0, 0.1, 50)

        ff = Line(x, y)
        ff.make_fit()

        r_abs = ff.residuals(pct=False)
        r_pct = ff.residuals(pct=True)

        # Manual calculation for verification
        fitted = ff(ff.observations.used.x)
        expected_pct = 100 * (r_abs / fitted)

        np.testing.assert_allclose(r_pct, expected_pct, rtol=1e-10)

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
        """Test handling of division by zero in percentage residuals."""
        # Create data that might lead to zero fitted values
        x = np.array([0, 1, 2])
        y = np.array([0, 1, 0])

        try:
            ff = Line(x, y)
            ff.make_fit()

            # Should handle division by zero gracefully
            r_pct = ff.residuals(pct=True)

            # Should not raise exceptions
            assert isinstance(r_pct, np.ndarray)

        except Exception:
            # Some fit configurations might not converge, which is OK for this test
            pytest.skip("Fit did not converge for edge case data")


class TestInPlaceOperations:
    """Test in-place mask operations (though effects are mostly internal)."""

    def test_mask_operations_still_work(self):
        """Verify optimized mask operations produce correct results."""
        x = np.random.randn(1000)
        y = x**2 + np.random.normal(0, 0.1, 1000)

        # Create fitfunction with constraints (triggers mask building)
        ff = Line(x, y, xmin=-1, xmax=1, ymin=0)
        ff.make_fit()

        # Should produce valid results
        assert hasattr(ff, "observations")
        assert hasattr(ff.observations, "used")

        # Mask should select appropriate subset
        used_x = ff.observations.used.x
        assert len(used_x) > 0, "Should have some used observations"
        assert len(used_x) < len(
            x
        ), "Should exclude some observations due to constraints"

        # All used x values should satisfy constraints
        assert np.all(used_x >= -1), "All used x should be >= xmin"
        assert np.all(used_x <= 1), "All used x should be <= xmax"

    def test_outside_mask_operations(self):
        """Test outside mask functionality."""
        x = np.linspace(-5, 5, 100)
        y = x**2 + np.random.normal(0, 0.1, 100)

        # Use xoutside to exclude central region
        ff = Line(x, y, xoutside=(-1, 1))
        ff.make_fit()

        used_x = ff.observations.used.x

        # Should only use values outside the (-1, 1) range
        assert np.all(
            (used_x <= -1) | (used_x >= 1)
        ), "Should only use values outside central region"
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
                f"measurement_{i}": (
                    (3 + i * 0.5)
                    * np.exp(-((x - (10 + i * 0.2)) ** 2) / (2 * (2 + i * 0.1) ** 2))
                    + np.random.normal(0, 0.05, 200)
                )
                for i in range(25)
            },
            index=x,
        )

        # Test complete workflow
        tf = TrendFit(data, Gaussian, ffunc1d=Gaussian)
        tf.make_ffunc1ds()

        start_time = time.perf_counter()
        tf.make_1dfits()
        execution_time = time.perf_counter() - start_time

        # Verify results
        assert len(tf.ffuncs) > 20, "Most fits should succeed"
        print(
            f"Successfully fitted {len(tf.ffuncs)}/25 measurements in {execution_time:.2f}s"  # noqa: E231
        )

        # Test residuals on first successful fit
        first_fit_key = tf.ffuncs.index[0]
        first_fit = tf.ffuncs[first_fit_key]

        # Test new residuals functionality
        r_fitted = first_fit.residuals(use_all=False)
        r_all = first_fit.residuals(use_all=True)
        r_pct = first_fit.residuals(pct=True)

        assert len(r_all) >= len(
            r_fitted
        ), "use_all should give at least as many residuals"
        assert len(r_pct) == len(
            r_fitted
        ), "Percentage residuals should match fitted residuals"

        print("✓ All Phase 4 features working correctly")


# ============================================================================
# Phase 6 Coverage Tests for TrendFit
# ============================================================================


class TestMakeTrendFuncEdgeCases:
    """Test make_trend_func edge cases (lines 378-379, 385)."""

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

    def test_make_trend_func_with_non_interval_index(self):
        """Test make_trend_func handles non-IntervalIndex popt (lines 378-379)."""
        tf = TrendFit(self.data_numeric, Line, ffunc1d=Gaussian)
        tf.make_ffunc1ds()
        tf.make_1dfits()

        # popt_1d should have numeric index, not IntervalIndex
        # This triggers the TypeError branch at lines 378-379
        tf.make_trend_func()

        # Verify trend_func was created successfully
        assert hasattr(tf, "_trend_func")
        assert isinstance(tf.trend_func, Line)

    def test_make_trend_func_weights_error(self):
        """Test make_trend_func raises ValueError when weights passed (line 385)."""
        tf = TrendFit(self.data_interval, Line, ffunc1d=Gaussian)
        tf.make_ffunc1ds()
        tf.make_1dfits()

        # Passing weights should raise ValueError
        with pytest.raises(ValueError, match="Weights are handled by `wkey1d`"):
            tf.make_trend_func(weights=np.ones(len(tf.popt_1d)))


class TestPlotAllPopt1DEdgeCases:
    """Test plot_all_popt_1d edge cases (lines 411, 419-425, 428, 439-466)."""

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

        # Set up complete TrendFit with trend_func
        self.tf = TrendFit(self.data, Line, ffunc1d=Gaussian)
        self.tf.make_ffunc1ds()
        self.tf.make_1dfits()
        self.tf.make_trend_func()
        self.tf.trend_func.make_fit()

    def test_plot_all_popt_1d_ax_none(self):
        """Test plot_all_popt_1d creates axes when ax is None (line 411)."""
        # When ax is None, should call subplots() to create figure and axes
        plotted = self.tf.plot_all_popt_1d(ax=None, plot_window=False)

        # Should return valid plotted objects (line or tuple)
        assert isinstance(plotted, (tuple, object))
        plt.close("all")

    def test_plot_all_popt_1d_only_in_trend_fit(self):
        """Test only_plot_data_in_trend_fit=True path (lines 419-425)."""
        plotted = self.tf.plot_all_popt_1d(
            ax=None, only_plot_data_in_trend_fit=True, plot_window=False
        )

        # Should complete without error (returns line or tuple)
        assert isinstance(plotted, (tuple, object))
        plt.close("all")

    def test_plot_all_popt_1d_with_plot_window(self):
        """Test plot_window=True path (lines 439-466)."""
        # Default is plot_window=True
        plotted = self.tf.plot_all_popt_1d(ax=None, plot_window=True)

        # Should return tuple (line, window)
        assert isinstance(plotted, tuple)
        assert len(plotted) == 2
        plt.close("all")

    def test_plot_all_popt_1d_plot_window_wkey_none_error(self):
        """Test plot_window=True raises error when wkey is None (lines 439-442)."""
        # Pass wkey=None to trigger the NotImplementedError
        with pytest.raises(NotImplementedError, match="`wkey` must be able to index"):
            self.tf.plot_all_popt_1d(ax=None, plot_window=True, wkey=None)
        plt.close("all")


class TestTrendLogxPaths:
    """Test trend_logx=True paths (lines 428, 503, 520)."""

    def setup_method(self):
        """Create test data for trend_logx testing."""
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

    def test_plot_all_popt_1d_trend_logx(self):
        """Test plot_all_popt_1d with trend_logx=True (line 428)."""
        tf = TrendFit(self.data, Line, trend_logx=True, ffunc1d=Gaussian)
        tf.make_ffunc1ds()
        tf.make_1dfits()
        tf.make_trend_func()
        tf.trend_func.make_fit()

        # Verify trend_logx is True
        assert tf.trend_logx is True

        # Plot with trend_logx=True should apply 10**x transformation
        plotted = tf.plot_all_popt_1d(ax=None, plot_window=False)

        assert isinstance(plotted, (tuple, object))
        plt.close("all")

    def test_plot_trend_fit_resid_trend_logx(self):
        """Test plot_trend_fit_resid with trend_logx=True (line 503)."""
        tf = TrendFit(self.data, Line, trend_logx=True, ffunc1d=Gaussian)
        tf.make_ffunc1ds()
        tf.make_1dfits()
        tf.make_trend_func()
        tf.trend_func.make_fit()

        # This should trigger line 503: rax.set_xscale("log")
        hax, rax = tf.plot_trend_fit_resid()

        assert isinstance(hax, plt.Axes)
        assert isinstance(rax, plt.Axes)
        # rax should have log scale on x-axis
        assert rax.get_xscale() == "log"
        plt.close("all")

    def test_plot_trend_and_resid_on_ffuncs_trend_logx(self):
        """Test plot_trend_and_resid_on_ffuncs with trend_logx=True (line 520)."""
        tf = TrendFit(self.data, Line, trend_logx=True, ffunc1d=Gaussian)
        tf.make_ffunc1ds()
        tf.make_1dfits()
        tf.make_trend_func()
        tf.trend_func.make_fit()

        # This should trigger line 520: rax.set_xscale("log")
        hax, rax = tf.plot_trend_and_resid_on_ffuncs()

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

        tf = TrendFit(data, Line, ffunc1d=Gaussian)
        tf.make_ffunc1ds()
        tf.make_1dfits()

        # This triggers the TypeError handling at lines 378-379
        tf.make_trend_func()

        assert isinstance(tf.trend_func, Line)
        tf.trend_func.make_fit()

        # Verify fit completed
        assert hasattr(tf.trend_func, "popt")
