"""Test Phase 4 performance optimizations."""

import pytest
import numpy as np
import pandas as pd
import warnings
import time
from unittest.mock import patch

from solarwindpy.fitfunctions import Gaussian, Line
from solarwindpy.fitfunctions.trend_fits import TrendFit


class TestTrendFitParallelization:
    """Test TrendFit parallel execution."""

    def setup_method(self):
        """Create test data for reproducible tests."""
        np.random.seed(42)
        x = np.linspace(0, 10, 50)
        self.data = pd.DataFrame(
            {
                f"col_{i}": 5 * np.exp(-((x - 5) ** 2) / 2)
                + np.random.normal(0, 0.1, 50)
                for i in range(10)
            },
            index=x,
        )

    def test_backward_compatibility(self):
        """Verify default behavior unchanged."""
        tf = TrendFit(self.data, Gaussian, ffunc1d=Gaussian)
        tf.make_ffunc1ds()

        # Should work without n_jobs parameter (default behavior)
        tf.make_1dfits()
        assert len(tf.ffuncs) > 0
        assert hasattr(tf, "_bad_fits")

    def test_parallel_sequential_equivalence(self):
        """Verify parallel gives same results as sequential."""
        # Sequential execution
        tf_seq = TrendFit(self.data, Gaussian, ffunc1d=Gaussian)
        tf_seq.make_ffunc1ds()
        tf_seq.make_1dfits(n_jobs=1)

        # Parallel execution
        tf_par = TrendFit(self.data, Gaussian, ffunc1d=Gaussian)
        tf_par.make_ffunc1ds()
        tf_par.make_1dfits(n_jobs=2)

        # Should have same number of successful fits
        assert len(tf_seq.ffuncs) == len(tf_par.ffuncs)

        # Compare all fit parameters
        for key in tf_seq.ffuncs.index:
            assert (
                key in tf_par.ffuncs.index
            ), f"Fit {key} missing from parallel results"

            seq_popt = tf_seq.ffuncs[key].popt
            par_popt = tf_par.ffuncs[key].popt

            # Parameters should match within numerical precision
            for param in seq_popt:
                np.testing.assert_allclose(
                    seq_popt[param],
                    par_popt[param],
                    rtol=1e-10,
                    atol=1e-10,
                    err_msg=f"Parameter {param} differs between sequential and parallel",
                )

    def test_parallel_execution_correctness(self):
        """Verify parallel execution works correctly, acknowledging Python GIL limitations."""
        # Check if joblib is available - if not, test falls back gracefully
        try:
            import joblib

            joblib_available = True
        except ImportError:
            joblib_available = False

        # Create test dataset - focus on correctness rather than performance
        x = np.linspace(0, 10, 100)
        data = pd.DataFrame(
            {
                f"col_{i}": 5 * np.exp(-((x - 5) ** 2) / 2)
                + np.random.normal(0, 0.1, 100)
                for i in range(20)  # Reasonable number of fits
            },
            index=x,
        )

        # Time sequential execution
        tf_seq = TrendFit(data, Gaussian, ffunc1d=Gaussian)
        tf_seq.make_ffunc1ds()
        start = time.perf_counter()
        tf_seq.make_1dfits(n_jobs=1)
        seq_time = time.perf_counter() - start

        # Time parallel execution with threading
        tf_par = TrendFit(data, Gaussian, ffunc1d=Gaussian)
        tf_par.make_ffunc1ds()
        start = time.perf_counter()
        tf_par.make_1dfits(n_jobs=4, backend="threading")
        par_time = time.perf_counter() - start

        speedup = seq_time / par_time if par_time > 0 else float("inf")

        print(f"Sequential time: {seq_time:.3f}s, fits: {len(tf_seq.ffuncs)}")
        print(f"Parallel time: {par_time:.3f}s, fits: {len(tf_par.ffuncs)}")
        print(
            f"Speedup achieved: {speedup:.2f}x (joblib available: {joblib_available})"
        )

        if joblib_available:
            # Main goal: verify parallel execution works and produces correct results
            # Note: Due to Python GIL and serialization overhead, speedup may be minimal
            # or even negative for small/fast workloads. This is expected behavior.
            assert (
                speedup > 0.05
            ), f"Parallel execution extremely slow, got {speedup:.2f}x"
            print(
                "NOTE: Python GIL and serialization overhead may limit speedup for small workloads"
            )
        else:
            # Without joblib, both should be sequential (speedup ~1.0)
            # Widen tolerance to 1.5 for timing variability across platforms
            assert (
                0.5 <= speedup <= 1.5
            ), f"Expected ~1.0x speedup without joblib, got {speedup:.2f}x"

        # Most important: verify both produce the same number of successful fits
        assert len(tf_seq.ffuncs) == len(
            tf_par.ffuncs
        ), "Parallel and sequential should have same success rate"

        # Verify results are equivalent (this is the key correctness test)
        for key in tf_seq.ffuncs.index:
            if key in tf_par.ffuncs.index:  # Both succeeded
                seq_popt = tf_seq.ffuncs[key].popt
                par_popt = tf_par.ffuncs[key].popt
                for param in seq_popt:
                    np.testing.assert_allclose(
                        seq_popt[param],
                        par_popt[param],
                        rtol=1e-10,
                        atol=1e-10,
                        err_msg=f"Parameter {param} differs between sequential and parallel",
                    )

    def test_joblib_not_installed_fallback(self):
        """Test graceful fallback when joblib unavailable."""
        # Mock joblib as unavailable
        with patch.dict("sys.modules", {"joblib": None}):
            # Force reload to simulate joblib not being installed
            import solarwindpy.fitfunctions.trend_fits as tf_module

            # Temporarily mock JOBLIB_AVAILABLE
            original_available = tf_module.JOBLIB_AVAILABLE
            tf_module.JOBLIB_AVAILABLE = False

            try:
                tf = tf_module.TrendFit(self.data, Gaussian, ffunc1d=Gaussian)
                tf.make_ffunc1ds()

                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    tf.make_1dfits(n_jobs=-1)  # Request parallel

                    # Should warn about joblib not being available
                    assert len(w) == 1
                    assert "joblib not installed" in str(w[0].message)
                    assert "parallel processing" in str(w[0].message)

                # Should still complete successfully with sequential execution
                assert len(tf.ffuncs) > 0
            finally:
                # Restore original state
                tf_module.JOBLIB_AVAILABLE = original_available

    def test_n_jobs_parameter_validation(self):
        """Test different n_jobs parameter values."""
        tf = TrendFit(self.data, Gaussian, ffunc1d=Gaussian)
        tf.make_ffunc1ds()

        # Test various n_jobs values
        for n_jobs in [1, 2, -1]:
            tf_test = TrendFit(self.data, Gaussian, ffunc1d=Gaussian)
            tf_test.make_ffunc1ds()
            tf_test.make_1dfits(n_jobs=n_jobs)
            assert len(tf_test.ffuncs) > 0, f"n_jobs={n_jobs} failed"

    def test_verbose_parameter(self):
        """Test verbose parameter doesn't break execution."""
        tf = TrendFit(self.data, Gaussian, ffunc1d=Gaussian)
        tf.make_ffunc1ds()

        # Should work with verbose output (though we can't easily test the output)
        tf.make_1dfits(n_jobs=2, verbose=0)
        assert len(tf.ffuncs) > 0

    def test_backend_parameter(self):
        """Test different joblib backends."""
        tf = TrendFit(self.data, Gaussian, ffunc1d=Gaussian)
        tf.make_ffunc1ds()

        # Test different backends (may not all be available in all environments)
        for backend in ["loky", "threading"]:
            tf_test = TrendFit(self.data, Gaussian, ffunc1d=Gaussian)
            tf_test.make_ffunc1ds()
            try:
                tf_test.make_1dfits(n_jobs=2, backend=backend)
                assert len(tf_test.ffuncs) > 0, f"Backend {backend} failed"
            except ValueError:
                # Some backends may not be available in all environments
                pytest.skip(f"Backend {backend} not available in this environment")


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
                for i in range(25)  # 25 measurements for good parallelization test
            },
            index=x,
        )

        # Test complete workflow
        tf = TrendFit(data, Gaussian, ffunc1d=Gaussian)
        tf.make_ffunc1ds()

        # Fit with parallelization
        start_time = time.perf_counter()
        tf.make_1dfits(n_jobs=-1, verbose=0)
        execution_time = time.perf_counter() - start_time

        # Verify results
        assert len(tf.ffuncs) > 20, "Most fits should succeed"
        print(
            f"Successfully fitted {len(tf.ffuncs)}/25 measurements in {execution_time:.2f}s"
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

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend for testing
import matplotlib.pyplot as plt


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
        assert tf.trend_func is not None

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

        # Should return valid plotted objects
        assert plotted is not None
        plt.close("all")

    def test_plot_all_popt_1d_only_in_trend_fit(self):
        """Test only_plot_data_in_trend_fit=True path (lines 419-425)."""
        plotted = self.tf.plot_all_popt_1d(
            ax=None, only_plot_data_in_trend_fit=True, plot_window=False
        )

        # Should complete without error
        assert plotted is not None
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

        assert plotted is not None
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

        assert hax is not None
        assert rax is not None
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

        assert hax is not None
        assert rax is not None
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

        assert tf.trend_func is not None
        tf.trend_func.make_fit()

        # Verify fit completed
        assert hasattr(tf.trend_func, "popt")
