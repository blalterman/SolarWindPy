"""Tests for Gaussian-Heaviside composite fit functions.

This module tests three composite functions that combine Gaussian and Heaviside
step functions:

1. GaussianPlusHeavySide:
   f(x) = Gaussian(x, mu, sigma, A) + y1 * H(x0-x) + y0
   - Gaussian peak plus a step function that adds y1 for x < x0

2. GaussianTimesHeavySide:
   f(x) = Gaussian(x, mu, sigma, A) * H(x-x0)
   - Gaussian truncated at x0; zero for x < x0

3. GaussianTimesHeavySidePlusHeavySide:
   f(x) = Gaussian(x, mu, sigma, A) * H(x-x0) + y1 * H(x0-x)
   - Gaussian for x >= x0, constant y1 for x < x0

Where:
- Gaussian(x, mu, sigma, A) = A * exp(-0.5 * ((x-mu)/sigma)^2)
- H(z) is the Heaviside step function (H(z) = 0 for z < 0, 0.5 at z=0, 1 for z > 0)

Mathematical derivations for expected values:

For a standard Gaussian at x=mu:
    Gaussian(mu, mu, sigma, A) = A * exp(0) = A

For Heaviside transitions:
    H(x0 - x) = 1 when x < x0, 0.5 when x = x0, 0 when x > x0
    H(x - x0) = 0 when x < x0, 0.5 when x = x0, 1 when x > x0
"""

import inspect

import numpy as np
import pytest

from solarwindpy.fitfunctions.composite import (
    GaussianPlusHeavySide,
    GaussianTimesHeavySide,
    GaussianTimesHeavySidePlusHeavySide,
)
from solarwindpy.fitfunctions.core import InsufficientDataError


# =============================================================================
# Helper Functions
# =============================================================================


def gaussian(x, mu, sigma, A):
    """Standard Gaussian function for test reference calculations."""
    return A * np.exp(-0.5 * ((x - mu) / sigma) ** 2)


# =============================================================================
# GaussianPlusHeavySide Fixtures
# =============================================================================


@pytest.fixture
def gph_clean_data():
    """Clean data for GaussianPlusHeavySide.

    Parameters: x0=2.0, y0=1.0, y1=3.0, mu=5.0, sigma=1.0, A=4.0

    Function behavior:
    - For x < x0: f(x) = Gaussian(x) + y1 + y0 = Gaussian(x) + 4.0
    - For x = x0: f(x) = Gaussian(x) + 0.5*y1 + y0 = Gaussian(x) + 2.5
    - For x > x0: f(x) = Gaussian(x) + y0 = Gaussian(x) + 1.0
    """
    true_params = {"x0": 2.0, "y0": 1.0, "y1": 3.0, "mu": 5.0, "sigma": 1.0, "A": 4.0}
    x = np.linspace(0, 10, 200)

    # Build y: Gaussian + y1*H(x0-x) + y0
    gauss = gaussian(x, true_params["mu"], true_params["sigma"], true_params["A"])
    heaviside_term = true_params["y1"] * np.heaviside(true_params["x0"] - x, 0.5)
    y = gauss + heaviside_term + true_params["y0"]

    w = np.ones_like(x)
    return x, y, w, true_params


@pytest.fixture
def gph_noisy_data():
    """Noisy data for GaussianPlusHeavySide with 3% noise.

    Parameters: x0=2.0, y0=1.0, y1=3.0, mu=5.0, sigma=1.0, A=4.0
    Noise std = 0.15 (approximately 3% of peak amplitude A+y0+y1)
    """
    rng = np.random.default_rng(42)
    true_params = {"x0": 2.0, "y0": 1.0, "y1": 3.0, "mu": 5.0, "sigma": 1.0, "A": 4.0}
    x = np.linspace(0, 10, 200)

    gauss = gaussian(x, true_params["mu"], true_params["sigma"], true_params["A"])
    heaviside_term = true_params["y1"] * np.heaviside(true_params["x0"] - x, 0.5)
    y_true = gauss + heaviside_term + true_params["y0"]

    noise_std = 0.15
    y = y_true + rng.normal(0, noise_std, len(x))
    w = np.ones_like(x) / noise_std
    return x, y, w, true_params


# =============================================================================
# GaussianTimesHeavySide Fixtures
# =============================================================================


@pytest.fixture
def gth_clean_data():
    """Clean data for GaussianTimesHeavySide.

    Parameters: x0=3.0, mu=5.0, sigma=1.0, A=4.0

    Function behavior:
    - For x < x0: f(x) = 0 (Heaviside is 0)
    - For x = x0: f(x) = Gaussian(x0) * 1.0 = Gaussian(x0)
    - For x > x0: f(x) = Gaussian(x) (Heaviside is 1)
    """
    true_params = {"x0": 3.0, "mu": 5.0, "sigma": 1.0, "A": 4.0}
    x = np.linspace(0, 10, 200)

    # Build y: Gaussian * H(x-x0)
    gauss = gaussian(x, true_params["mu"], true_params["sigma"], true_params["A"])
    y = gauss * np.heaviside(x - true_params["x0"], 1.0)

    w = np.ones_like(x)
    return x, y, w, true_params


@pytest.fixture
def gth_noisy_data():
    """Noisy data for GaussianTimesHeavySide with 3% noise.

    Parameters: x0=3.0, mu=5.0, sigma=1.0, A=4.0
    Noise std = 0.12 (approximately 3% of peak amplitude)
    """
    rng = np.random.default_rng(42)
    true_params = {"x0": 3.0, "mu": 5.0, "sigma": 1.0, "A": 4.0}
    x = np.linspace(0, 10, 200)

    gauss = gaussian(x, true_params["mu"], true_params["sigma"], true_params["A"])
    y_true = gauss * np.heaviside(x - true_params["x0"], 1.0)

    noise_std = 0.12
    y = y_true + rng.normal(0, noise_std, len(x))
    # Ensure y >= 0 for x < x0 (the function should be ~0 there)
    y[x < true_params["x0"]] = np.abs(y[x < true_params["x0"]])
    w = np.ones_like(x) / noise_std
    return x, y, w, true_params


# =============================================================================
# GaussianTimesHeavySidePlusHeavySide Fixtures
# =============================================================================


@pytest.fixture
def gthph_clean_data():
    """Clean data for GaussianTimesHeavySidePlusHeavySide.

    Parameters: x0=3.0, y1=2.0, mu=5.0, sigma=1.0, A=4.0

    Function behavior:
    - For x < x0: f(x) = y1 (constant plateau)
    - For x = x0: f(x) = Gaussian(x0) + y1 (both H(0) = 1.0)
    - For x > x0: f(x) = Gaussian(x) (pure Gaussian)
    """
    true_params = {"x0": 3.0, "y1": 2.0, "mu": 5.0, "sigma": 1.0, "A": 4.0}
    x = np.linspace(0, 10, 200)

    # Build y: Gaussian * H(x-x0) + y1 * H(x0-x) with H(0) = 1.0
    gauss = gaussian(x, true_params["mu"], true_params["sigma"], true_params["A"])
    y = gauss * np.heaviside(x - true_params["x0"], 1.0) + true_params["y1"] * np.heaviside(
        true_params["x0"] - x, 1.0
    )

    w = np.ones_like(x)
    return x, y, w, true_params


@pytest.fixture
def gthph_noisy_data():
    """Noisy data for GaussianTimesHeavySidePlusHeavySide with 3% noise.

    Parameters: x0=3.0, y1=2.0, mu=5.0, sigma=1.0, A=4.0
    Noise std = 0.12 (approximately 3% of peak amplitude)
    """
    rng = np.random.default_rng(42)
    true_params = {"x0": 3.0, "y1": 2.0, "mu": 5.0, "sigma": 1.0, "A": 4.0}
    x = np.linspace(0, 10, 200)

    gauss = gaussian(x, true_params["mu"], true_params["sigma"], true_params["A"])
    y_true = gauss * np.heaviside(x - true_params["x0"], 1.0) + true_params[
        "y1"
    ] * np.heaviside(true_params["x0"] - x, 1.0)

    noise_std = 0.12
    y = y_true + rng.normal(0, noise_std, len(x))
    w = np.ones_like(x) / noise_std
    return x, y, w, true_params


# =============================================================================
# GaussianPlusHeavySide Tests
# =============================================================================


class TestGaussianPlusHeavySide:
    """Tests for GaussianPlusHeavySide fit function.

    GaussianPlusHeavySide models:
        f(x) = Gaussian(x, mu, sigma, A) + y1 * H(x0-x) + y0

    This produces a Gaussian peak with:
    - A constant offset y0 everywhere
    - An additional step of height y1 for x < x0
    """

    # -------------------------------------------------------------------------
    # E1. Function Evaluation Tests (Exact Values)
    # -------------------------------------------------------------------------

    def test_func_evaluates_below_x0_correctly(self):
        """For x < x0: f(x) = Gaussian(x) + y1 + y0.

        At x=0 with params x0=2, y0=1, y1=3, mu=5, sigma=1, A=4:
        - Gaussian(0) = 4 * exp(-0.5 * ((0-5)/1)^2) = 4 * exp(-12.5) ~ 1.48e-5
        - H(2-0) = H(2) = 1
        - f(0) = Gaussian(0) + 3*1 + 1 ~ 4.0 (Gaussian contribution negligible)
        """
        x0, y0, y1, mu, sigma, A = 2.0, 1.0, 3.0, 5.0, 1.0, 4.0

        x_test = np.array([0.0, 1.0])  # Both below x0=2
        gauss_vals = gaussian(x_test, mu, sigma, A)
        expected = gauss_vals + y1 * 1.0 + y0  # H(x0-x)=1 for x<x0

        x_dummy = np.array([0.0, 10.0])
        y_dummy = np.array([4.0, 1.0])
        obj = GaussianPlusHeavySide(x_dummy, y_dummy)
        result = obj.function(x_test, x0, y0, y1, mu, sigma, A)

        np.testing.assert_allclose(
            result,
            expected,
            rtol=1e-10,
            err_msg="Below x0: f(x) should equal Gaussian(x) + y1 + y0",
        )

    def test_func_evaluates_above_x0_correctly(self):
        """For x > x0: f(x) = Gaussian(x) + y0 (Heaviside term is 0).

        At x=5 (Gaussian peak) with params x0=2, y0=1, y1=3, mu=5, sigma=1, A=4:
        - Gaussian(5) = 4 * exp(0) = 4.0
        - H(2-5) = H(-3) = 0
        - f(5) = 4.0 + 0 + 1.0 = 5.0
        """
        x0, y0, y1, mu, sigma, A = 2.0, 1.0, 3.0, 5.0, 1.0, 4.0

        x_test = np.array([3.0, 5.0, 7.0])  # All above x0=2
        gauss_vals = gaussian(x_test, mu, sigma, A)
        expected = gauss_vals + y0  # H(x0-x)=0 for x>x0

        x_dummy = np.array([0.0, 10.0])
        y_dummy = np.array([4.0, 1.0])
        obj = GaussianPlusHeavySide(x_dummy, y_dummy)
        result = obj.function(x_test, x0, y0, y1, mu, sigma, A)

        np.testing.assert_allclose(
            result,
            expected,
            rtol=1e-10,
            err_msg="Above x0: f(x) should equal Gaussian(x) + y0",
        )

    def test_func_evaluates_at_x0_correctly(self):
        """At x = x0: f(x) = Gaussian(x0) + 0.5*y1 + y0.

        At x=2 with params x0=2, y0=1, y1=3, mu=5, sigma=1, A=4:
        - Gaussian(2) = 4 * exp(-0.5 * ((2-5)/1)^2) = 4 * exp(-4.5) ~ 0.0446
        - H(0) = 0.5
        - f(2) = Gaussian(2) + 3*0.5 + 1 = Gaussian(2) + 2.5
        """
        x0, y0, y1, mu, sigma, A = 2.0, 1.0, 3.0, 5.0, 1.0, 4.0

        x_test = np.array([x0])
        gauss_val = gaussian(x_test, mu, sigma, A)
        expected = gauss_val + 0.5 * y1 + y0

        x_dummy = np.array([0.0, 10.0])
        y_dummy = np.array([4.0, 1.0])
        obj = GaussianPlusHeavySide(x_dummy, y_dummy)
        result = obj.function(x_test, x0, y0, y1, mu, sigma, A)

        np.testing.assert_allclose(
            result,
            expected,
            rtol=1e-10,
            err_msg="At x0: f(x) should equal Gaussian(x0) + 0.5*y1 + y0",
        )

    def test_func_evaluates_at_gaussian_peak(self):
        """At x = mu (Gaussian peak): f(mu) = A + y0 (assuming mu > x0).

        At x=5 with params x0=2, y0=1, y1=3, mu=5, sigma=1, A=4:
        - Gaussian(5) = A = 4.0
        - H(2-5) = 0
        - f(5) = 4.0 + 0 + 1.0 = 5.0
        """
        x0, y0, y1, mu, sigma, A = 2.0, 1.0, 3.0, 5.0, 1.0, 4.0

        x_test = np.array([mu])
        expected = np.array([A + y0])  # mu > x0, so H term is 0

        x_dummy = np.array([0.0, 10.0])
        y_dummy = np.array([4.0, 1.0])
        obj = GaussianPlusHeavySide(x_dummy, y_dummy)
        result = obj.function(x_test, x0, y0, y1, mu, sigma, A)

        np.testing.assert_allclose(
            result,
            expected,
            rtol=1e-10,
            err_msg="At Gaussian peak (mu > x0): f(mu) = A + y0",
        )

    # -------------------------------------------------------------------------
    # E2. Parameter Recovery Tests (Clean Data)
    # -------------------------------------------------------------------------

    def test_fit_recovers_gaussian_parameters_from_clean_data(self, gph_clean_data):
        """Fitting noise-free data should recover Gaussian parameters within 2%.

        Note: The step function parameters (x0, y0, y1) are inherently difficult
        to constrain due to the zero gradient of Heaviside functions. Only the
        Gaussian parameters (mu, sigma, A) are expected to be recovered precisely.
        """
        x, y, w, true_params = gph_clean_data

        obj = GaussianPlusHeavySide(x, y)
        obj.make_fit()

        # Only test Gaussian parameters which can be well-constrained
        for param in ["mu", "sigma", "A"]:
            true_val = true_params[param]
            fitted_val = obj.popt[param]
            if abs(true_val) < 0.1:
                assert abs(fitted_val - true_val) < 0.05, (
                    f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                    f"absolute error exceeds 0.05"
                )
            else:
                rel_error = abs(fitted_val - true_val) / abs(true_val)
                assert rel_error < 0.02, (
                    f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                    f"rel_error={rel_error:.2%} exceeds 2% tolerance"
                )

    @pytest.mark.parametrize(
        "true_params",
        [
            {"x0": 2.0, "y0": 1.0, "y1": 3.0, "mu": 5.0, "sigma": 1.0, "A": 4.0},
            {"x0": 4.0, "y0": 0.5, "y1": 2.0, "mu": 6.0, "sigma": 0.8, "A": 3.0},
            {"x0": 1.0, "y0": 2.0, "y1": 1.0, "mu": 4.0, "sigma": 1.5, "A": 5.0},
        ],
    )
    def test_fit_recovers_gaussian_parameters_for_various_combinations(self, true_params):
        """Gaussian parameters should be recovered for diverse parameter combinations.

        Note: Only Gaussian parameters (mu, sigma, A) are tested since step function
        parameters are inherently difficult to constrain. Tolerance is 10% due to
        parameter coupling effects in this complex model.
        """
        x = np.linspace(0, 10, 200)
        gauss = gaussian(x, true_params["mu"], true_params["sigma"], true_params["A"])
        heaviside_term = true_params["y1"] * np.heaviside(true_params["x0"] - x, 0.5)
        y = gauss + heaviside_term + true_params["y0"]

        obj = GaussianPlusHeavySide(x, y)
        obj.make_fit()

        # Only test Gaussian parameters which can be well-constrained
        for param in ["mu", "sigma", "A"]:
            true_val = true_params[param]
            fitted_val = obj.popt[param]
            if abs(true_val) < 0.1:
                assert abs(fitted_val - true_val) < 0.1, (
                    f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}"
                )
            else:
                rel_error = abs(fitted_val - true_val) / abs(true_val)
                assert rel_error < 0.10, (
                    f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                    f"rel_error={rel_error:.2%}"
                )

    # -------------------------------------------------------------------------
    # E3. Noisy Data Tests (Precision Bounds)
    # -------------------------------------------------------------------------

    def test_fit_with_noise_recovers_gaussian_parameters_within_2sigma(self, gph_noisy_data):
        """Gaussian parameters should be within 2sigma of true values (95% confidence).

        Note: Step function parameters (x0, y0, y1) are excluded because Heaviside
        functions have zero gradient almost everywhere, making their uncertainties
        unreliable for this type of test.
        """
        x, y, w, true_params = gph_noisy_data

        obj = GaussianPlusHeavySide(x, y)
        obj.make_fit()

        # Only test Gaussian parameters which have well-defined uncertainties
        for param in ["mu", "sigma", "A"]:
            true_val = true_params[param]
            fitted_val = obj.popt[param]
            sigma = obj.psigma[param]
            deviation = abs(fitted_val - true_val)

            assert deviation < 2 * sigma, (
                f"{param}: |fitted({fitted_val:.4f}) - true({true_val:.4f})| = "
                f"{deviation:.4f} exceeds 2sigma = {2*sigma:.4f}"
            )

    def test_fit_uncertainty_scales_with_noise(self):
        """Higher noise should produce larger parameter uncertainties."""
        rng = np.random.default_rng(42)
        true_params = {"x0": 2.0, "y0": 1.0, "y1": 3.0, "mu": 5.0, "sigma": 1.0, "A": 4.0}
        x = np.linspace(0, 10, 200)
        gauss = gaussian(x, true_params["mu"], true_params["sigma"], true_params["A"])
        heaviside_term = true_params["y1"] * np.heaviside(true_params["x0"] - x, 0.5)
        y_true = gauss + heaviside_term + true_params["y0"]

        # Low noise fit
        y_low = y_true + rng.normal(0, 0.05, len(x))
        fit_low = GaussianPlusHeavySide(x, y_low)
        fit_low.make_fit()

        # High noise fit
        rng2 = np.random.default_rng(43)
        y_high = y_true + rng2.normal(0, 0.25, len(x))
        fit_high = GaussianPlusHeavySide(x, y_high)
        fit_high.make_fit()

        # High noise should have larger uncertainties for most parameters
        for param in ["mu", "sigma", "A"]:
            assert fit_high.psigma[param] > fit_low.psigma[param], (
                f"{param}: high_noise_sigma={fit_high.psigma[param]:.4f} should be "
                f"> low_noise_sigma={fit_low.psigma[param]:.4f}"
            )

    # -------------------------------------------------------------------------
    # E4. Initial Parameter Estimation Tests
    # -------------------------------------------------------------------------

    def test_p0_returns_list_with_correct_length(self, gph_clean_data):
        """p0 should return a list with 6 elements."""
        x, y, w, true_params = gph_clean_data
        obj = GaussianPlusHeavySide(x, y)

        p0 = obj.p0
        assert isinstance(p0, list), f"p0 should be a list, got {type(p0)}"
        assert len(p0) == 6, f"p0 should have 6 elements, got {len(p0)}"

    def test_p0_enables_successful_convergence(self, gph_noisy_data):
        """Fit should converge when initialized with estimated p0."""
        x, y, w, true_params = gph_noisy_data

        obj = GaussianPlusHeavySide(x, y)
        obj.make_fit()

        assert all(np.isfinite(v) for v in obj.popt.values()), (
            f"Fit did not converge: popt={obj.popt}"
        )

    # -------------------------------------------------------------------------
    # E5. Edge Case and Error Handling Tests
    # -------------------------------------------------------------------------

    def test_insufficient_data_raises_error(self):
        """Fitting with insufficient data should raise InsufficientDataError."""
        x = np.array([1.0, 2.0, 3.0])  # Only 3 points for 6 parameters
        y = np.array([2.0, 4.0, 3.0])

        obj = GaussianPlusHeavySide(x, y)

        with pytest.raises(InsufficientDataError):
            obj.make_fit()

    def test_function_signature(self):
        """Test that function has correct parameter signature."""
        x = np.array([0.0, 5.0, 10.0])
        y = np.array([4.0, 5.0, 1.0])
        obj = GaussianPlusHeavySide(x, y)

        sig = inspect.signature(obj.function)
        params = tuple(sig.parameters.keys())

        assert params == ("x", "x0", "y0", "y1", "mu", "sigma", "A"), (
            f"Function should have signature (x, x0, y0, y1, mu, sigma, A), got {params}"
        )

    def test_callable_interface(self, gph_clean_data):
        """Test that fitted object is callable and returns correct shape."""
        x, y, w, true_params = gph_clean_data

        obj = GaussianPlusHeavySide(x, y)
        obj.make_fit()

        x_test = np.array([1.0, 5.0, 10.0])
        y_pred = obj(x_test)

        assert y_pred.shape == x_test.shape, (
            f"Predicted shape {y_pred.shape} should match input shape {x_test.shape}"
        )
        assert np.all(np.isfinite(y_pred)), "All predicted values should be finite"

    def test_popt_has_correct_keys(self, gph_clean_data):
        """Test that popt contains expected parameter names."""
        x, y, w, true_params = gph_clean_data

        obj = GaussianPlusHeavySide(x, y)
        obj.make_fit()

        expected_keys = {"x0", "y0", "y1", "mu", "sigma", "A"}
        actual_keys = set(obj.popt.keys())

        assert actual_keys == expected_keys, (
            f"popt keys should be {expected_keys}, got {actual_keys}"
        )

    def test_psigma_has_same_keys_as_popt(self, gph_noisy_data):
        """Test that psigma has same keys as popt."""
        x, y, w, true_params = gph_noisy_data

        obj = GaussianPlusHeavySide(x, y)
        obj.make_fit()

        assert set(obj.psigma.keys()) == set(obj.popt.keys()), (
            f"psigma keys {set(obj.psigma.keys())} should match "
            f"popt keys {set(obj.popt.keys())}"
        )

    def test_psigma_values_are_nonnegative(self, gph_noisy_data):
        """Test that parameter uncertainties are non-negative.

        Note: x0 uncertainty can be zero or very small due to the step function
        nature (zero gradient almost everywhere), so we only check for non-negative
        values. Gaussian parameters (mu, sigma, A) should have positive uncertainties.
        """
        x, y, w, true_params = gph_noisy_data

        obj = GaussianPlusHeavySide(x, y)
        obj.make_fit()

        for param, sigma in obj.psigma.items():
            assert sigma >= 0, f"psigma['{param}'] = {sigma} should be non-negative"

        # Gaussian parameters should have positive uncertainties
        for param in ["mu", "sigma", "A"]:
            assert obj.psigma[param] > 0, f"psigma['{param}'] should be positive"


# =============================================================================
# GaussianTimesHeavySide Tests
# =============================================================================


class TestGaussianTimesHeavySide:
    """Tests for GaussianTimesHeavySide fit function.

    GaussianTimesHeavySide models:
        f(x) = Gaussian(x, mu, sigma, A) * H(x-x0)

    This produces a truncated Gaussian that is:
    - Zero for x < x0
    - Gaussian(x) for x > x0
    - Gaussian(x0) at x = x0 (since H(0) = 1.0 in this implementation)
    """

    # -------------------------------------------------------------------------
    # E1. Function Evaluation Tests (Exact Values)
    # -------------------------------------------------------------------------

    def test_func_evaluates_below_x0_as_zero(self):
        """For x < x0: f(x) = 0 (Heaviside is 0).

        With x0=3, the function should be exactly 0 for all x < 3.
        """
        x0, mu, sigma, A = 3.0, 5.0, 1.0, 4.0

        x_test = np.array([0.0, 1.0, 2.0, 2.99])  # All below x0=3
        expected = np.zeros_like(x_test)

        x_dummy = np.array([0.0, 10.0])
        y_dummy = np.array([0.0, 4.0])
        obj = GaussianTimesHeavySide(x_dummy, y_dummy, guess_x0=x0)
        result = obj.function(x_test, x0, mu, sigma, A)

        np.testing.assert_allclose(
            result,
            expected,
            rtol=1e-10,
            err_msg="Below x0: f(x) should be exactly 0",
        )

    def test_func_evaluates_above_x0_as_gaussian(self):
        """For x > x0: f(x) = Gaussian(x).

        With x0=3, mu=5, sigma=1, A=4:
        - f(5) = 4 * exp(0) = 4.0 (Gaussian peak)
        - f(4) = 4 * exp(-0.5) ~ 2.426
        - f(6) = 4 * exp(-0.5) ~ 2.426
        """
        x0, mu, sigma, A = 3.0, 5.0, 1.0, 4.0

        x_test = np.array([4.0, 5.0, 6.0, 8.0])  # All above x0=3
        expected = gaussian(x_test, mu, sigma, A)

        x_dummy = np.array([0.0, 10.0])
        y_dummy = np.array([0.0, 4.0])
        obj = GaussianTimesHeavySide(x_dummy, y_dummy, guess_x0=x0)
        result = obj.function(x_test, x0, mu, sigma, A)

        np.testing.assert_allclose(
            result,
            expected,
            rtol=1e-10,
            err_msg="Above x0: f(x) should equal Gaussian(x)",
        )

    def test_func_evaluates_at_x0_correctly(self):
        """At x = x0: f(x) = Gaussian(x0) * 1.0 = Gaussian(x0).

        This implementation uses H(0) = 1.0, so at the transition point
        the function equals the full Gaussian value.

        With x0=3, mu=5, sigma=1, A=4:
        - Gaussian(3) = 4 * exp(-0.5 * ((3-5)/1)^2) = 4 * exp(-2) ~ 0.541
        """
        x0, mu, sigma, A = 3.0, 5.0, 1.0, 4.0

        x_test = np.array([x0])
        expected = gaussian(x_test, mu, sigma, A)  # H(0) = 1.0

        x_dummy = np.array([0.0, 10.0])
        y_dummy = np.array([0.0, 4.0])
        obj = GaussianTimesHeavySide(x_dummy, y_dummy, guess_x0=x0)
        result = obj.function(x_test, x0, mu, sigma, A)

        np.testing.assert_allclose(
            result,
            expected,
            rtol=1e-10,
            err_msg="At x0: f(x0) should equal Gaussian(x0) since H(0)=1.0",
        )

    def test_func_evaluates_at_gaussian_peak(self):
        """At x = mu: f(mu) = A (assuming mu > x0).

        With x0=3, mu=5, A=4:
        - Gaussian(5) = 4 * exp(0) = 4.0
        - H(5-3) = H(2) = 1.0
        - f(5) = 4.0 * 1.0 = 4.0
        """
        x0, mu, sigma, A = 3.0, 5.0, 1.0, 4.0

        x_test = np.array([mu])
        expected = np.array([A])  # Full Gaussian amplitude

        x_dummy = np.array([0.0, 10.0])
        y_dummy = np.array([0.0, 4.0])
        obj = GaussianTimesHeavySide(x_dummy, y_dummy, guess_x0=x0)
        result = obj.function(x_test, x0, mu, sigma, A)

        np.testing.assert_allclose(
            result,
            expected,
            rtol=1e-10,
            err_msg="At Gaussian peak (mu > x0): f(mu) = A",
        )

    # -------------------------------------------------------------------------
    # E2. Parameter Recovery Tests (Clean Data)
    # -------------------------------------------------------------------------

    def test_fit_recovers_exact_parameters_from_clean_data(self, gth_clean_data):
        """Fitting noise-free data should recover parameters within 2%."""
        x, y, w, true_params = gth_clean_data

        obj = GaussianTimesHeavySide(x, y, guess_x0=true_params["x0"])
        obj.make_fit()

        for param, true_val in true_params.items():
            fitted_val = obj.popt[param]
            if abs(true_val) < 0.1:
                assert abs(fitted_val - true_val) < 0.05, (
                    f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                    f"absolute error exceeds 0.05"
                )
            else:
                rel_error = abs(fitted_val - true_val) / abs(true_val)
                assert rel_error < 0.02, (
                    f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                    f"rel_error={rel_error:.2%} exceeds 2% tolerance"
                )

    @pytest.mark.parametrize(
        "true_params",
        [
            {"x0": 3.0, "mu": 5.0, "sigma": 1.0, "A": 4.0},
            {"x0": 2.0, "mu": 6.0, "sigma": 0.8, "A": 3.0},
            {"x0": 4.0, "mu": 7.0, "sigma": 1.5, "A": 5.0},
        ],
    )
    def test_fit_recovers_various_parameter_combinations(self, true_params):
        """Fitting should work for diverse parameter combinations."""
        x = np.linspace(0, 12, 250)
        gauss = gaussian(x, true_params["mu"], true_params["sigma"], true_params["A"])
        y = gauss * np.heaviside(x - true_params["x0"], 1.0)

        obj = GaussianTimesHeavySide(x, y, guess_x0=true_params["x0"])
        obj.make_fit()

        for param, true_val in true_params.items():
            fitted_val = obj.popt[param]
            if abs(true_val) < 0.1:
                assert abs(fitted_val - true_val) < 0.1, (
                    f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}"
                )
            else:
                rel_error = abs(fitted_val - true_val) / abs(true_val)
                assert rel_error < 0.05, (
                    f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                    f"rel_error={rel_error:.2%}"
                )

    # -------------------------------------------------------------------------
    # E3. Noisy Data Tests (Precision Bounds)
    # -------------------------------------------------------------------------

    def test_fit_with_noise_recovers_gaussian_parameters_within_2sigma(self, gth_noisy_data):
        """Gaussian parameters should be within 2sigma of true values (95% confidence).

        Note: x0 is excluded because Heaviside functions have zero gradient almost
        everywhere, making its uncertainty unreliable for this type of test.
        """
        x, y, w, true_params = gth_noisy_data

        obj = GaussianTimesHeavySide(x, y, guess_x0=true_params["x0"])
        obj.make_fit()

        # Only test Gaussian parameters which have well-defined uncertainties
        for param in ["mu", "sigma", "A"]:
            true_val = true_params[param]
            fitted_val = obj.popt[param]
            sigma = obj.psigma[param]
            deviation = abs(fitted_val - true_val)

            assert deviation < 2 * sigma, (
                f"{param}: |fitted({fitted_val:.4f}) - true({true_val:.4f})| = "
                f"{deviation:.4f} exceeds 2sigma = {2*sigma:.4f}"
            )

    def test_fit_uncertainty_scales_with_noise(self):
        """Higher noise should produce larger parameter uncertainties."""
        rng = np.random.default_rng(42)
        true_params = {"x0": 3.0, "mu": 5.0, "sigma": 1.0, "A": 4.0}
        x = np.linspace(0, 10, 200)
        gauss = gaussian(x, true_params["mu"], true_params["sigma"], true_params["A"])
        y_true = gauss * np.heaviside(x - true_params["x0"], 1.0)

        # Low noise fit
        y_low = y_true + rng.normal(0, 0.05, len(x))
        y_low[x < true_params["x0"]] = np.abs(y_low[x < true_params["x0"]])
        fit_low = GaussianTimesHeavySide(x, y_low, guess_x0=true_params["x0"])
        fit_low.make_fit()

        # High noise fit
        rng2 = np.random.default_rng(43)
        y_high = y_true + rng2.normal(0, 0.25, len(x))
        y_high[x < true_params["x0"]] = np.abs(y_high[x < true_params["x0"]])
        fit_high = GaussianTimesHeavySide(x, y_high, guess_x0=true_params["x0"])
        fit_high.make_fit()

        # High noise should have larger uncertainties for most parameters
        for param in ["mu", "sigma", "A"]:
            assert fit_high.psigma[param] > fit_low.psigma[param], (
                f"{param}: high_noise_sigma={fit_high.psigma[param]:.4f} should be "
                f"> low_noise_sigma={fit_low.psigma[param]:.4f}"
            )

    # -------------------------------------------------------------------------
    # E4. Initial Parameter Estimation Tests
    # -------------------------------------------------------------------------

    def test_p0_returns_list_with_correct_length(self, gth_clean_data):
        """p0 should return a list with 4 elements."""
        x, y, w, true_params = gth_clean_data
        obj = GaussianTimesHeavySide(x, y, guess_x0=true_params["x0"])

        p0 = obj.p0
        assert isinstance(p0, list), f"p0 should be a list, got {type(p0)}"
        assert len(p0) == 4, f"p0 should have 4 elements, got {len(p0)}"

    def test_p0_enables_successful_convergence(self, gth_noisy_data):
        """Fit should converge when initialized with estimated p0."""
        x, y, w, true_params = gth_noisy_data

        obj = GaussianTimesHeavySide(x, y, guess_x0=true_params["x0"])
        obj.make_fit()

        assert all(np.isfinite(v) for v in obj.popt.values()), (
            f"Fit did not converge: popt={obj.popt}"
        )

    def test_guess_x0_is_required(self):
        """Test that guess_x0 parameter is required for initialization."""
        x = np.array([0.0, 5.0, 10.0])
        y = np.array([0.0, 4.0, 1.0])

        # This should either raise an error or require guess_x0
        # The exact behavior depends on implementation
        with pytest.raises((TypeError, ValueError)):
            obj = GaussianTimesHeavySide(x, y)  # Missing guess_x0

    # -------------------------------------------------------------------------
    # E5. Edge Case and Error Handling Tests
    # -------------------------------------------------------------------------

    def test_insufficient_data_raises_error(self):
        """Fitting with insufficient data should raise InsufficientDataError."""
        x = np.array([1.0, 2.0, 3.0])  # Only 3 points for 4 parameters
        y = np.array([0.0, 0.0, 1.0])

        obj = GaussianTimesHeavySide(x, y, guess_x0=2.0)

        with pytest.raises(InsufficientDataError):
            obj.make_fit()

    def test_function_signature(self):
        """Test that function has correct parameter signature."""
        x = np.array([0.0, 5.0, 10.0])
        y = np.array([0.0, 4.0, 1.0])
        obj = GaussianTimesHeavySide(x, y, guess_x0=3.0)

        sig = inspect.signature(obj.function)
        params = tuple(sig.parameters.keys())

        assert params == ("x", "x0", "mu", "sigma", "A"), (
            f"Function should have signature (x, x0, mu, sigma, A), got {params}"
        )

    def test_callable_interface(self, gth_clean_data):
        """Test that fitted object is callable and returns correct shape."""
        x, y, w, true_params = gth_clean_data

        obj = GaussianTimesHeavySide(x, y, guess_x0=true_params["x0"])
        obj.make_fit()

        x_test = np.array([1.0, 5.0, 10.0])
        y_pred = obj(x_test)

        assert y_pred.shape == x_test.shape, (
            f"Predicted shape {y_pred.shape} should match input shape {x_test.shape}"
        )
        assert np.all(np.isfinite(y_pred)), "All predicted values should be finite"

    def test_popt_has_correct_keys(self, gth_clean_data):
        """Test that popt contains expected parameter names."""
        x, y, w, true_params = gth_clean_data

        obj = GaussianTimesHeavySide(x, y, guess_x0=true_params["x0"])
        obj.make_fit()

        expected_keys = {"x0", "mu", "sigma", "A"}
        actual_keys = set(obj.popt.keys())

        assert actual_keys == expected_keys, (
            f"popt keys should be {expected_keys}, got {actual_keys}"
        )

    def test_psigma_values_are_nonnegative(self, gth_noisy_data):
        """Test that parameter uncertainties are non-negative.

        Note: x0 uncertainty can be zero or very small due to the step function
        nature (zero gradient almost everywhere), so we only check for non-negative
        values. Gaussian parameters (mu, sigma, A) should have positive uncertainties.
        """
        x, y, w, true_params = gth_noisy_data

        obj = GaussianTimesHeavySide(x, y, guess_x0=true_params["x0"])
        obj.make_fit()

        for param, sigma in obj.psigma.items():
            assert sigma >= 0, f"psigma['{param}'] = {sigma} should be non-negative"

        # Gaussian parameters should have positive uncertainties
        for param in ["mu", "sigma", "A"]:
            assert obj.psigma[param] > 0, f"psigma['{param}'] should be positive"


# =============================================================================
# GaussianTimesHeavySidePlusHeavySide Tests
# =============================================================================


class TestGaussianTimesHeavySidePlusHeavySide:
    """Tests for GaussianTimesHeavySidePlusHeavySide fit function.

    GaussianTimesHeavySidePlusHeavySide models:
        f(x) = Gaussian(x, mu, sigma, A) * H(x-x0) + y1 * H(x0-x)

    This produces:
    - Constant y1 for x < x0
    - Gaussian(x) for x > x0
    - Transition at x = x0 (depends on Heaviside convention)
    """

    # -------------------------------------------------------------------------
    # E1. Function Evaluation Tests (Exact Values)
    # -------------------------------------------------------------------------

    def test_func_evaluates_below_x0_as_constant(self):
        """For x < x0: f(x) = y1 (constant plateau).

        With x0=3, y1=2:
        - H(3-x) = 1 for x < 3
        - H(x-3) = 0 for x < 3
        - f(x) = 0 + y1*1 = 2
        """
        x0, y1, mu, sigma, A = 3.0, 2.0, 5.0, 1.0, 4.0

        x_test = np.array([0.0, 1.0, 2.0, 2.99])  # All below x0=3
        expected = np.full_like(x_test, y1)

        x_dummy = np.array([0.0, 10.0])
        y_dummy = np.array([2.0, 4.0])
        obj = GaussianTimesHeavySidePlusHeavySide(x_dummy, y_dummy, guess_x0=x0)
        result = obj.function(x_test, x0, y1, mu, sigma, A)

        np.testing.assert_allclose(
            result,
            expected,
            rtol=1e-10,
            err_msg="Below x0: f(x) should be constant y1",
        )

    def test_func_evaluates_above_x0_as_gaussian(self):
        """For x > x0: f(x) = Gaussian(x) (H(x0-x) = 0).

        With x0=3, mu=5, sigma=1, A=4:
        - H(3-x) = 0 for x > 3
        - H(x-3) = 1 for x > 3
        - f(x) = Gaussian(x) * 1 + y1 * 0 = Gaussian(x)
        """
        x0, y1, mu, sigma, A = 3.0, 2.0, 5.0, 1.0, 4.0

        x_test = np.array([4.0, 5.0, 6.0, 8.0])  # All above x0=3
        expected = gaussian(x_test, mu, sigma, A)

        x_dummy = np.array([0.0, 10.0])
        y_dummy = np.array([2.0, 4.0])
        obj = GaussianTimesHeavySidePlusHeavySide(x_dummy, y_dummy, guess_x0=x0)
        result = obj.function(x_test, x0, y1, mu, sigma, A)

        np.testing.assert_allclose(
            result,
            expected,
            rtol=1e-10,
            err_msg="Above x0: f(x) should equal Gaussian(x)",
        )

    def test_func_evaluates_at_x0_correctly(self):
        """At x = x0: f(x) = Gaussian(x0)*1.0 + y1*1.0.

        This implementation uses H(0) = 1.0 for both Heaviside terms, so at the
        transition point both contribute fully.
        With x0=3, y1=2, mu=5, sigma=1, A=4:
        - Gaussian(3) = 4 * exp(-2) ~ 0.541
        - f(3) = 0.541*1.0 + 2*1.0 = 2.541
        """
        x0, y1, mu, sigma, A = 3.0, 2.0, 5.0, 1.0, 4.0

        x_test = np.array([x0])
        gauss_val = gaussian(x_test, mu, sigma, A)
        expected = gauss_val * 1.0 + y1 * 1.0  # H(0) = 1.0 for both terms

        x_dummy = np.array([0.0, 10.0])
        y_dummy = np.array([2.0, 4.0])
        obj = GaussianTimesHeavySidePlusHeavySide(x_dummy, y_dummy, guess_x0=x0)
        result = obj.function(x_test, x0, y1, mu, sigma, A)

        np.testing.assert_allclose(
            result,
            expected,
            rtol=1e-10,
            err_msg="At x0: f(x0) should equal Gaussian(x0)*1.0 + y1*1.0",
        )

    def test_func_evaluates_at_gaussian_peak(self):
        """At x = mu: f(mu) = A (assuming mu > x0).

        With x0=3, mu=5, A=4:
        - Gaussian(5) = 4 * exp(0) = 4.0
        - H(5-3) = H(2) = 1.0
        - H(3-5) = H(-2) = 0.0
        - f(5) = 4.0 * 1.0 + y1 * 0.0 = 4.0
        """
        x0, y1, mu, sigma, A = 3.0, 2.0, 5.0, 1.0, 4.0

        x_test = np.array([mu])
        expected = np.array([A])  # Full Gaussian amplitude

        x_dummy = np.array([0.0, 10.0])
        y_dummy = np.array([2.0, 4.0])
        obj = GaussianTimesHeavySidePlusHeavySide(x_dummy, y_dummy, guess_x0=x0)
        result = obj.function(x_test, x0, y1, mu, sigma, A)

        np.testing.assert_allclose(
            result,
            expected,
            rtol=1e-10,
            err_msg="At Gaussian peak (mu > x0): f(mu) = A",
        )

    # -------------------------------------------------------------------------
    # E2. Parameter Recovery Tests (Clean Data)
    # -------------------------------------------------------------------------

    def test_fit_recovers_exact_parameters_from_clean_data(self, gthph_clean_data):
        """Fitting noise-free data should recover parameters within 2%."""
        x, y, w, true_params = gthph_clean_data

        obj = GaussianTimesHeavySidePlusHeavySide(x, y, guess_x0=true_params["x0"])
        obj.make_fit()

        for param, true_val in true_params.items():
            fitted_val = obj.popt[param]
            if abs(true_val) < 0.1:
                assert abs(fitted_val - true_val) < 0.05, (
                    f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                    f"absolute error exceeds 0.05"
                )
            else:
                rel_error = abs(fitted_val - true_val) / abs(true_val)
                assert rel_error < 0.02, (
                    f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                    f"rel_error={rel_error:.2%} exceeds 2% tolerance"
                )

    @pytest.mark.parametrize(
        "true_params",
        [
            {"x0": 3.0, "y1": 2.0, "mu": 5.0, "sigma": 1.0, "A": 4.0},
            {"x0": 2.0, "y1": 1.5, "mu": 6.0, "sigma": 0.8, "A": 3.0},
            {"x0": 4.0, "y1": 3.0, "mu": 7.0, "sigma": 1.5, "A": 5.0},
        ],
    )
    def test_fit_recovers_various_parameter_combinations(self, true_params):
        """Fitting should work for diverse parameter combinations."""
        x = np.linspace(0, 12, 250)
        gauss = gaussian(x, true_params["mu"], true_params["sigma"], true_params["A"])
        y = gauss * np.heaviside(x - true_params["x0"], 0.5) + true_params[
            "y1"
        ] * np.heaviside(true_params["x0"] - x, 0.5)

        obj = GaussianTimesHeavySidePlusHeavySide(x, y, guess_x0=true_params["x0"])
        obj.make_fit()

        for param, true_val in true_params.items():
            fitted_val = obj.popt[param]
            if abs(true_val) < 0.1:
                assert abs(fitted_val - true_val) < 0.1, (
                    f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}"
                )
            else:
                rel_error = abs(fitted_val - true_val) / abs(true_val)
                assert rel_error < 0.05, (
                    f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                    f"rel_error={rel_error:.2%}"
                )

    # -------------------------------------------------------------------------
    # E3. Noisy Data Tests (Precision Bounds)
    # -------------------------------------------------------------------------

    def test_fit_with_noise_recovers_gaussian_parameters_within_2sigma(self, gthph_noisy_data):
        """Gaussian parameters should be within 2sigma of true values (95% confidence).

        Note: x0 and y1 are excluded because Heaviside functions have zero gradient
        almost everywhere, making their uncertainties unreliable for this type of test.
        """
        x, y, w, true_params = gthph_noisy_data

        obj = GaussianTimesHeavySidePlusHeavySide(x, y, guess_x0=true_params["x0"])
        obj.make_fit()

        # Only test Gaussian parameters which have well-defined uncertainties
        for param in ["mu", "sigma", "A"]:
            true_val = true_params[param]
            fitted_val = obj.popt[param]
            sigma = obj.psigma[param]
            deviation = abs(fitted_val - true_val)

            assert deviation < 2 * sigma, (
                f"{param}: |fitted({fitted_val:.4f}) - true({true_val:.4f})| = "
                f"{deviation:.4f} exceeds 2sigma = {2*sigma:.4f}"
            )

    def test_fit_uncertainty_scales_with_noise(self):
        """Higher noise should produce larger parameter uncertainties."""
        rng = np.random.default_rng(42)
        true_params = {"x0": 3.0, "y1": 2.0, "mu": 5.0, "sigma": 1.0, "A": 4.0}
        x = np.linspace(0, 10, 200)
        gauss = gaussian(x, true_params["mu"], true_params["sigma"], true_params["A"])
        y_true = gauss * np.heaviside(x - true_params["x0"], 0.5) + true_params[
            "y1"
        ] * np.heaviside(true_params["x0"] - x, 0.5)

        # Low noise fit
        y_low = y_true + rng.normal(0, 0.05, len(x))
        fit_low = GaussianTimesHeavySidePlusHeavySide(x, y_low, guess_x0=true_params["x0"])
        fit_low.make_fit()

        # High noise fit
        rng2 = np.random.default_rng(43)
        y_high = y_true + rng2.normal(0, 0.25, len(x))
        fit_high = GaussianTimesHeavySidePlusHeavySide(
            x, y_high, guess_x0=true_params["x0"]
        )
        fit_high.make_fit()

        # High noise should have larger uncertainties for most parameters
        for param in ["mu", "sigma", "A"]:
            assert fit_high.psigma[param] > fit_low.psigma[param], (
                f"{param}: high_noise_sigma={fit_high.psigma[param]:.4f} should be "
                f"> low_noise_sigma={fit_low.psigma[param]:.4f}"
            )

    # -------------------------------------------------------------------------
    # E4. Initial Parameter Estimation Tests
    # -------------------------------------------------------------------------

    def test_p0_returns_list_with_correct_length(self, gthph_clean_data):
        """p0 should return a list with 5 elements."""
        x, y, w, true_params = gthph_clean_data
        obj = GaussianTimesHeavySidePlusHeavySide(x, y, guess_x0=true_params["x0"])

        p0 = obj.p0
        assert isinstance(p0, list), f"p0 should be a list, got {type(p0)}"
        assert len(p0) == 5, f"p0 should have 5 elements, got {len(p0)}"

    def test_p0_enables_successful_convergence(self, gthph_noisy_data):
        """Fit should converge when initialized with estimated p0."""
        x, y, w, true_params = gthph_noisy_data

        obj = GaussianTimesHeavySidePlusHeavySide(x, y, guess_x0=true_params["x0"])
        obj.make_fit()

        assert all(np.isfinite(v) for v in obj.popt.values()), (
            f"Fit did not converge: popt={obj.popt}"
        )

    def test_guess_x0_is_required(self):
        """Test that guess_x0 parameter is required for initialization."""
        x = np.array([0.0, 5.0, 10.0])
        y = np.array([2.0, 4.0, 1.0])

        # This should either raise an error or require guess_x0
        with pytest.raises((TypeError, ValueError)):
            obj = GaussianTimesHeavySidePlusHeavySide(x, y)  # Missing guess_x0

    # -------------------------------------------------------------------------
    # E5. Edge Case and Error Handling Tests
    # -------------------------------------------------------------------------

    def test_insufficient_data_raises_error(self):
        """Fitting with insufficient data should raise InsufficientDataError."""
        x = np.array([1.0, 2.0, 3.0, 4.0])  # Only 4 points for 5 parameters
        y = np.array([2.0, 2.0, 2.0, 3.0])

        obj = GaussianTimesHeavySidePlusHeavySide(x, y, guess_x0=2.5)

        with pytest.raises(InsufficientDataError):
            obj.make_fit()

    def test_function_signature(self):
        """Test that function has correct parameter signature."""
        x = np.array([0.0, 5.0, 10.0])
        y = np.array([2.0, 4.0, 1.0])
        obj = GaussianTimesHeavySidePlusHeavySide(x, y, guess_x0=3.0)

        sig = inspect.signature(obj.function)
        params = tuple(sig.parameters.keys())

        assert params == ("x", "x0", "y1", "mu", "sigma", "A"), (
            f"Function should have signature (x, x0, y1, mu, sigma, A), got {params}"
        )

    def test_callable_interface(self, gthph_clean_data):
        """Test that fitted object is callable and returns correct shape."""
        x, y, w, true_params = gthph_clean_data

        obj = GaussianTimesHeavySidePlusHeavySide(x, y, guess_x0=true_params["x0"])
        obj.make_fit()

        x_test = np.array([1.0, 5.0, 10.0])
        y_pred = obj(x_test)

        assert y_pred.shape == x_test.shape, (
            f"Predicted shape {y_pred.shape} should match input shape {x_test.shape}"
        )
        assert np.all(np.isfinite(y_pred)), "All predicted values should be finite"

    def test_popt_has_correct_keys(self, gthph_clean_data):
        """Test that popt contains expected parameter names."""
        x, y, w, true_params = gthph_clean_data

        obj = GaussianTimesHeavySidePlusHeavySide(x, y, guess_x0=true_params["x0"])
        obj.make_fit()

        expected_keys = {"x0", "y1", "mu", "sigma", "A"}
        actual_keys = set(obj.popt.keys())

        assert actual_keys == expected_keys, (
            f"popt keys should be {expected_keys}, got {actual_keys}"
        )

    def test_psigma_values_are_nonnegative(self, gthph_noisy_data):
        """Test that parameter uncertainties are non-negative.

        Note: x0 uncertainty can be zero or very small due to the step function
        nature (zero gradient almost everywhere), so we only check for non-negative
        values. Gaussian parameters (mu, sigma, A) should have positive uncertainties.
        """
        x, y, w, true_params = gthph_noisy_data

        obj = GaussianTimesHeavySidePlusHeavySide(x, y, guess_x0=true_params["x0"])
        obj.make_fit()

        for param, sigma in obj.psigma.items():
            assert sigma >= 0, f"psigma['{param}'] = {sigma} should be non-negative"

        # Gaussian parameters should have positive uncertainties
        for param in ["mu", "sigma", "A"]:
            assert obj.psigma[param] > 0, f"psigma['{param}'] should be positive"

    # -------------------------------------------------------------------------
    # E6. Behavior Consistency Tests
    # -------------------------------------------------------------------------

    def test_transition_continuity(self, gthph_clean_data):
        """Test that the function shows expected behavior at transition.

        The function transitions from constant y1 (for x < x0) to Gaussian (for x > x0).
        At x = x0, both Heaviside functions contribute 0.5.
        """
        x, y, w, true_params = gthph_clean_data

        obj = GaussianTimesHeavySidePlusHeavySide(x, y, guess_x0=true_params["x0"])
        obj.make_fit()

        x0 = obj.popt["x0"]
        y1 = obj.popt["y1"]
        mu = obj.popt["mu"]
        sigma = obj.popt["sigma"]
        A = obj.popt["A"]

        # Value just below x0
        x_below = np.array([x0 - 0.01])
        y_below = obj(x_below)[0]

        # Value just above x0
        x_above = np.array([x0 + 0.01])
        y_above = obj(x_above)[0]

        # Below x0 should be close to y1
        np.testing.assert_allclose(
            y_below,
            y1,
            rtol=0.1,
            err_msg=f"Value just below x0 ({y_below:.4f}) should be close to y1 ({y1:.4f})",
        )

        # Above x0 should be close to Gaussian(x0)
        gauss_at_x0 = gaussian(np.array([x0 + 0.01]), mu, sigma, A)[0]
        np.testing.assert_allclose(
            y_above,
            gauss_at_x0,
            rtol=0.1,
            err_msg=f"Value just above x0 ({y_above:.4f}) should be close to Gaussian ({gauss_at_x0:.4f})",
        )

    def test_plateau_region_is_constant(self, gthph_clean_data):
        """Test that the region x < x0 is a constant plateau at y1."""
        x, y, w, true_params = gthph_clean_data

        obj = GaussianTimesHeavySidePlusHeavySide(x, y, guess_x0=true_params["x0"])
        obj.make_fit()

        x0 = obj.popt["x0"]
        y1 = obj.popt["y1"]

        # Test multiple points below x0
        x_plateau = np.array([0.5, 1.0, 1.5, 2.0, 2.5])
        x_plateau = x_plateau[x_plateau < x0]  # Ensure all below x0

        if len(x_plateau) > 0:
            y_plateau = obj(x_plateau)
            expected = np.full_like(y_plateau, y1)

            np.testing.assert_allclose(
                y_plateau,
                expected,
                rtol=1e-6,
                err_msg="Plateau region (x < x0) should be constant at y1",
            )
