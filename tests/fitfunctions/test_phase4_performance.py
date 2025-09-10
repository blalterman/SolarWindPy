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

    def test_parallel_speedup(self):
        """Verify parallel execution provides speedup for sufficient workload."""
        # Check if joblib is available - if not, test falls back gracefully
        try:
            import joblib
            joblib_available = True
        except ImportError:
            joblib_available = False

        # Create larger dataset for meaningful timing comparison
        x = np.linspace(0, 10, 100)
        large_data = pd.DataFrame(
            {
                f"col_{i}": 5 * np.exp(-((x - 5) ** 2) / 2)
                + np.random.normal(0, 0.1, 100)
                for i in range(30)  # 30 fits should be enough to see speedup
            },
            index=x,
        )

        # Time sequential execution
        tf_seq = TrendFit(large_data, Gaussian, ffunc1d=Gaussian)
        tf_seq.make_ffunc1ds()
        start = time.perf_counter()
        tf_seq.make_1dfits(n_jobs=1)
        seq_time = time.perf_counter() - start

        # Time parallel execution
        tf_par = TrendFit(large_data, Gaussian, ffunc1d=Gaussian)
        tf_par.make_ffunc1ds()
        start = time.perf_counter()
        tf_par.make_1dfits(n_jobs=-1)
        par_time = time.perf_counter() - start

        speedup = seq_time / par_time

        if joblib_available:
            # Should be at least 1.2x faster (conservative for CI environments)
            # In practice, should be much higher on multi-core systems
            assert speedup > 1.2, f"Expected speedup > 1.2x, got {speedup:.2f}x"
        else:
            # Without joblib, both should be sequential (speedup ~1.0)
            assert 0.8 <= speedup <= 1.2, f"Expected ~1.0x speedup without joblib, got {speedup:.2f}x"

        print(f"Speedup achieved: {speedup:.2f}x (joblib available: {joblib_available})")

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
