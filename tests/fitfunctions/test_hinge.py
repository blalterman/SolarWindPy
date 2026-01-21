"""Tests for HingeSaturation fit function.

HingeSaturation models a piecewise linear function with a hinge point (xh, yh):
- Rising region (x < xh): f(x) = m1 * (x - x1) where m1 = yh / (xh - x1)
- Plateau region (x >= xh): f(x) = m2 * (x - x2) where x2 = xh - yh / m2

Parameters:
- xh: x-coordinate of hinge point
- yh: y-coordinate of hinge point
- x1: x-intercept of rising line
- m2: slope of plateau (m2=0 gives constant saturation)
"""

import inspect

import numpy as np
import pytest

from solarwindpy.fitfunctions.hinge import HingeSaturation
from solarwindpy.fitfunctions.core import InsufficientDataError


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def clean_saturation_data():
    """Perfect hinge saturation data (no noise) with m2=0 (flat plateau).

    Parameters: xh=5.0, yh=10.0, x1=0.0, m2=0.0
    This gives m1 = 10/(5-0) = 2.0, so rising region is f(x) = 2x.
    """
    true_params = {"xh": 5.0, "yh": 10.0, "x1": 0.0, "m2": 0.0}
    x = np.linspace(0.1, 15, 200)
    # Build y piecewise to avoid numerical issues
    m1 = true_params["yh"] / (true_params["xh"] - true_params["x1"])
    y = np.where(
        x < true_params["xh"],
        m1 * (x - true_params["x1"]),
        true_params["yh"],  # m2=0 means flat plateau at yh
    )
    w = np.ones_like(x)
    return x, y, w, true_params


@pytest.fixture
def clean_sloped_plateau_data():
    """Perfect hinge data with non-zero m2 (sloped plateau).

    Parameters: xh=5.0, yh=10.0, x1=0.0, m2=0.5
    Rising: f(x) = 2*(x-0) = 2x
    Plateau: f(x) = 0.5*(x - x2) where x2 = 5 - 10/0.5 = -15
    """
    true_params = {"xh": 5.0, "yh": 10.0, "x1": 0.0, "m2": 0.5}
    x = np.linspace(0.1, 15, 200)
    m1 = true_params["yh"] / (true_params["xh"] - true_params["x1"])
    x2 = true_params["xh"] - true_params["yh"] / true_params["m2"]
    y = np.where(
        x < true_params["xh"],
        m1 * (x - true_params["x1"]),
        true_params["m2"] * (x - x2),
    )
    w = np.ones_like(x)
    return x, y, w, true_params


@pytest.fixture
def noisy_saturation_data():
    """Hinge saturation data with 5% Gaussian noise.

    Parameters: xh=5.0, yh=10.0, x1=0.0, m2=0.0
    Noise std = 0.5 (5% of yh)
    """
    rng = np.random.default_rng(42)
    true_params = {"xh": 5.0, "yh": 10.0, "x1": 0.0, "m2": 0.0}
    x = np.linspace(0.5, 15, 200)
    m1 = true_params["yh"] / (true_params["xh"] - true_params["x1"])
    y_true = np.where(
        x < true_params["xh"],
        m1 * (x - true_params["x1"]),
        true_params["yh"],
    )
    noise_std = 0.5
    y = y_true + rng.normal(0, noise_std, len(x))
    w = np.ones_like(x) / noise_std
    return x, y, w, true_params


@pytest.fixture
def offset_x1_data():
    """Hinge data with non-zero x1 (offset x-intercept).

    Parameters: xh=5.0, yh=10.0, x1=1.0, m2=0.0
    m1 = 10/(5-1) = 2.5, so rising region is f(x) = 2.5*(x-1)
    """
    true_params = {"xh": 5.0, "yh": 10.0, "x1": 1.0, "m2": 0.0}
    x = np.linspace(1.1, 15, 200)
    m1 = true_params["yh"] / (true_params["xh"] - true_params["x1"])
    y = np.where(
        x < true_params["xh"],
        m1 * (x - true_params["x1"]),
        true_params["yh"],
    )
    w = np.ones_like(x)
    return x, y, w, true_params


# =============================================================================
# E1. Function Evaluation Tests (Exact Values)
# =============================================================================


def test_func_evaluates_rising_region_correctly():
    """Before hinge: f(x) = m1*(x-x1) where m1 = yh/(xh-x1)."""
    # Parameters: xh=5, yh=10, x1=0, m2=0 → m1 = 10/(5-0) = 2.0
    xh, yh, x1, m2 = 5.0, 10.0, 0.0, 0.0

    # Test specific points in rising region (x < xh)
    x_test = np.array([0.0, 1.0, 2.5, 4.0, 5.0])  # includes hinge point
    # m1 = 2.0, so f(x) = 2*(x-0) = 2x
    expected = np.array([0.0, 2.0, 5.0, 8.0, 10.0])

    # Create minimal instance to access function
    x_dummy = np.array([0.0, 10.0])
    y_dummy = np.array([0.0, 10.0])
    obj = HingeSaturation(x_dummy, y_dummy, guess_xh=xh, guess_yh=yh)
    result = obj.function(x_test, xh, yh, x1, m2)

    np.testing.assert_allclose(
        result,
        expected,
        rtol=1e-10,
        err_msg="Rising region should follow f(x) = m1*(x-x1)",
    )


def test_func_evaluates_saturated_region_correctly():
    """After hinge with m2=0: f(x) = yh (constant plateau)."""
    xh, yh, x1, m2 = 5.0, 10.0, 0.0, 0.0

    # Test points beyond hinge (x > xh)
    x_test = np.array([5.5, 6.0, 10.0, 100.0])
    expected = np.array([10.0, 10.0, 10.0, 10.0])  # saturated at yh

    x_dummy = np.array([0.0, 10.0])
    y_dummy = np.array([0.0, 10.0])
    obj = HingeSaturation(x_dummy, y_dummy, guess_xh=xh, guess_yh=yh)
    result = obj.function(x_test, xh, yh, x1, m2)

    np.testing.assert_allclose(
        result,
        expected,
        rtol=1e-10,
        err_msg="Saturated region with m2=0 should be constant at yh",
    )


def test_func_evaluates_sloped_plateau_correctly():
    """After hinge with m2≠0: f(x) = m2*(x-x2) where x2 = xh - yh/m2."""
    xh, yh, x1, m2 = 5.0, 10.0, 0.0, 0.5
    # x2 = 5 - 10/0.5 = 5 - 20 = -15
    # After hinge: f(x) = 0.5*(x - (-15)) = 0.5*(x + 15)

    x_test = np.array([6.0, 8.0, 10.0])
    # f(6) = 0.5*(6+15) = 10.5
    # f(8) = 0.5*(8+15) = 11.5
    # f(10) = 0.5*(10+15) = 12.5
    expected = np.array([10.5, 11.5, 12.5])

    x_dummy = np.array([0.0, 10.0])
    y_dummy = np.array([0.0, 10.0])
    obj = HingeSaturation(x_dummy, y_dummy, guess_xh=xh, guess_yh=yh)
    result = obj.function(x_test, xh, yh, x1, m2)

    np.testing.assert_allclose(
        result,
        expected,
        rtol=1e-10,
        err_msg="Sloped plateau should follow f(x) = m2*(x-x2)",
    )


# =============================================================================
# E2. Parameter Recovery Tests (Clean Data)
# =============================================================================


def test_fit_recovers_exact_parameters_from_clean_data(clean_saturation_data):
    """Fitting noise-free data should recover parameters within 1%."""
    x, y, w, true_params = clean_saturation_data

    obj = HingeSaturation(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])
    obj.make_fit()

    for param, true_val in true_params.items():
        fitted_val = obj.popt[param]
        # Use absolute tolerance for values near zero
        if abs(true_val) < 0.1:
            assert abs(fitted_val - true_val) < 0.05, (
                f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                f"absolute error exceeds 0.05"
            )
        else:
            rel_error = abs(fitted_val - true_val) / abs(true_val)
            assert rel_error < 0.01, (
                f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                f"rel_error={rel_error:.2%} exceeds 1% tolerance"
            )


def test_fit_recovers_sloped_plateau_parameters(clean_sloped_plateau_data):
    """Fitting clean data with m2≠0 should recover parameters within 2%."""
    x, y, w, true_params = clean_sloped_plateau_data

    obj = HingeSaturation(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])
    obj.make_fit()

    for param, true_val in true_params.items():
        fitted_val = obj.popt[param]
        if abs(true_val) < 0.1:
            assert (
                abs(fitted_val - true_val) < 0.05
            ), f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}"
        else:
            rel_error = abs(fitted_val - true_val) / abs(true_val)
            assert rel_error < 0.02, (
                f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                f"rel_error={rel_error:.2%}"
            )


def test_fit_recovers_offset_x1_parameters(offset_x1_data):
    """Fitting clean data with x1≠0 should recover parameters within 2%."""
    x, y, w, true_params = offset_x1_data

    obj = HingeSaturation(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])
    obj.make_fit()

    for param, true_val in true_params.items():
        fitted_val = obj.popt[param]
        if abs(true_val) < 0.1:
            assert (
                abs(fitted_val - true_val) < 0.05
            ), f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}"
        else:
            rel_error = abs(fitted_val - true_val) / abs(true_val)
            assert rel_error < 0.02, (
                f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                f"rel_error={rel_error:.2%}"
            )


@pytest.mark.parametrize(
    "true_params",
    [
        {"xh": 5.0, "yh": 10.0, "x1": 0.0, "m2": 0.0},  # Classic saturation
        {"xh": 3.0, "yh": 6.0, "x1": 1.0, "m2": 0.0},  # Offset x-intercept
        {"xh": 8.0, "yh": 4.0, "x1": 2.0, "m2": 0.3},  # Sloped plateau
        {"xh": 5.0, "yh": 10.0, "x1": 0.0, "m2": -0.2},  # Declining plateau
    ],
)
def test_fit_recovers_various_parameter_combinations(true_params):
    """Fitting should work for diverse parameter combinations."""
    x_start = true_params["x1"] + 0.1
    x_end = true_params["xh"] + 10
    x = np.linspace(x_start, x_end, 200)

    # Build y from parameters
    m1 = true_params["yh"] / (true_params["xh"] - true_params["x1"])
    if abs(true_params["m2"]) > 1e-10:
        x2 = true_params["xh"] - true_params["yh"] / true_params["m2"]
        y = np.where(
            x < true_params["xh"],
            m1 * (x - true_params["x1"]),
            true_params["m2"] * (x - x2),
        )
    else:
        y = np.where(
            x < true_params["xh"],
            m1 * (x - true_params["x1"]),
            true_params["yh"],
        )

    obj = HingeSaturation(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])
    obj.make_fit()

    for param, true_val in true_params.items():
        fitted_val = obj.popt[param]
        if abs(true_val) < 0.1:
            assert (
                abs(fitted_val - true_val) < 0.05
            ), f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}"
        else:
            rel_error = abs(fitted_val - true_val) / abs(true_val)
            assert rel_error < 0.02, (
                f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                f"rel_error={rel_error:.2%}"
            )


# =============================================================================
# E3. Noisy Data Tests (Precision Bounds)
# =============================================================================


def test_fit_with_noise_recovers_parameters_within_2sigma(noisy_saturation_data):
    """Fitted parameters should be within 2σ of true values (95% confidence).

    With 4 parameters, testing each at 1σ (68%) gives only (0.68)^4 ≈ 21% joint
    probability of all passing. Using 2σ (95%) gives (0.95)^4 ≈ 81% joint
    probability, which is robust for automated testing.

    For well-behaved Gaussian noise, we expect deviations < 2σ with high confidence.
    """
    x, y, w, true_params = noisy_saturation_data

    obj = HingeSaturation(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])
    obj.make_fit()

    for param, true_val in true_params.items():
        fitted_val = obj.popt[param]
        sigma = obj.psigma[param]
        deviation = abs(fitted_val - true_val)

        # 2σ gives 95% confidence per parameter, ~81% joint for 4 parameters
        assert deviation < 2 * sigma, (
            f"{param}: |fitted({fitted_val:.4f}) - true({true_val:.4f})| = "
            f"{deviation:.4f} exceeds 2σ = {2*sigma:.4f}"
        )


def test_fit_uncertainty_scales_with_noise():
    """Higher noise should produce larger parameter uncertainties."""
    rng = np.random.default_rng(42)
    true_params = {"xh": 5.0, "yh": 10.0, "x1": 0.0, "m2": 0.0}
    x = np.linspace(0.5, 15, 200)
    m1 = true_params["yh"] / (true_params["xh"] - true_params["x1"])
    y_true = np.where(
        x < true_params["xh"],
        m1 * (x - true_params["x1"]),
        true_params["yh"],
    )

    # Low noise fit
    y_low = y_true + rng.normal(0, 0.2, len(x))
    fit_low = HingeSaturation(
        x, y_low, guess_xh=true_params["xh"], guess_yh=true_params["yh"]
    )
    fit_low.make_fit()

    # High noise fit (different seed for independence)
    rng2 = np.random.default_rng(43)
    y_high = y_true + rng2.normal(0, 1.0, len(x))
    fit_high = HingeSaturation(
        x, y_high, guess_xh=true_params["xh"], guess_yh=true_params["yh"]
    )
    fit_high.make_fit()

    # High noise should have larger uncertainties for most parameters
    # (xh and yh are the primary parameters affected by noise)
    for param in ["xh", "yh"]:
        assert fit_high.psigma[param] > fit_low.psigma[param], (
            f"{param}: high_noise_sigma={fit_high.psigma[param]:.4f} should be "
            f"> low_noise_sigma={fit_low.psigma[param]:.4f}"
        )


# =============================================================================
# E4. Initial Parameter Estimation Tests
# =============================================================================


def test_p0_returns_list_with_correct_length(clean_saturation_data):
    """p0 should return a list with 4 elements."""
    x, y, w, true_params = clean_saturation_data
    obj = HingeSaturation(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])

    p0 = obj.p0
    assert isinstance(p0, list), f"p0 should be a list, got {type(p0)}"
    assert len(p0) == 4, f"p0 should have 4 elements (xh, yh, x1, m2), got {len(p0)}"


def test_p0_enables_successful_convergence(noisy_saturation_data):
    """Fit should converge when initialized with estimated p0."""
    x, y, w, true_params = noisy_saturation_data

    obj = HingeSaturation(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])
    obj.make_fit()

    # Fit should have converged (popt should exist and be finite)
    assert all(
        np.isfinite(v) for v in obj.popt.values()
    ), f"Fit did not converge: popt={obj.popt}"


# =============================================================================
# E5. Derived Quantity Tests (Internal Consistency)
# =============================================================================


def test_fitted_m1_is_consistent_with_xh_yh_x1(offset_x1_data):
    """Verify m1 = yh / (xh - x1) relationship holds for fitted params."""
    x, y, w, true_params = offset_x1_data
    # True m1 = 10 / (5 - 1) = 2.5

    obj = HingeSaturation(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])
    obj.make_fit()

    xh, yh, x1 = obj.popt["xh"], obj.popt["yh"], obj.popt["x1"]
    m1_from_params = yh / (xh - x1)

    # Verify by evaluating function in rising region
    x_rising = np.array([2.0, 3.0])  # Well before hinge
    y_rising = obj(x_rising)

    # y(x) = m1 * (x - x1) → m1 = y / (x - x1)
    m1_from_values = y_rising / (x_rising - x1)

    np.testing.assert_allclose(
        m1_from_values,
        m1_from_params,
        rtol=1e-6,
        err_msg="m1 derived from function values should match m1 from parameters",
    )


def test_hinge_point_is_continuous(clean_sloped_plateau_data):
    """Function value at xh should equal yh (continuity at hinge)."""
    x, y, w, true_params = clean_sloped_plateau_data

    obj = HingeSaturation(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])
    obj.make_fit()

    # Evaluate exactly at fitted xh
    xh = obj.popt["xh"]
    yh_expected = obj.popt["yh"]
    y_at_hinge = obj(np.array([xh]))[0]

    np.testing.assert_allclose(
        y_at_hinge,
        yh_expected,
        rtol=1e-6,
        err_msg=f"f(xh={xh:.3f}) = {y_at_hinge:.3f} should equal yh={yh_expected:.3f}",
    )


# =============================================================================
# E6. Edge Case and Error Handling Tests
# =============================================================================


def test_weighted_fit_respects_weights():
    """Weighted fitting should correctly use sigma to weight observations.

    In FitFunction, weights are interpreted as uncertainties (sigma). Points
    with larger sigma have MORE uncertainty and thus LESS influence on the fit.

    Test strategy: Apply non-uniform sigma values and verify the fit converges
    correctly. HingeSaturation's min() function makes it inherently robust to
    plateau outliers, so we test that weighting works by verifying accurate
    parameter recovery with realistic sigma values.
    """
    rng = np.random.default_rng(42)
    true_params = {"xh": 5.0, "yh": 10.0, "x1": 0.0, "m2": 0.0}

    x = np.linspace(0.5, 15, 100)
    m1 = true_params["yh"] / (true_params["xh"] - true_params["x1"])
    y_true = np.where(
        x < true_params["xh"],
        m1 * (x - true_params["x1"]),
        true_params["yh"],
    )

    # Add heteroscedastic noise: larger noise in rising region, smaller in plateau
    sigma_true = np.where(x < true_params["xh"], 0.5, 0.1)
    noise = rng.normal(0, 1, len(x)) * sigma_true
    y = y_true + noise

    # Fit with correct sigma values
    fit_weighted = HingeSaturation(
        x, y, weights=sigma_true, guess_xh=true_params["xh"], guess_yh=true_params["yh"]
    )
    fit_weighted.make_fit()

    # Verify fit converged and parameters are accurate
    assert all(
        np.isfinite(v) for v in fit_weighted.popt.values()
    ), f"Weighted fit did not converge: popt={fit_weighted.popt}"

    # With proper weighting, should recover true parameters within 5%
    for param, true_val in true_params.items():
        fitted_val = fit_weighted.popt[param]
        if abs(true_val) < 0.1:
            # Absolute tolerance for values near zero
            assert (
                abs(fitted_val - true_val) < 0.1
            ), f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}"
        else:
            rel_error = abs(fitted_val - true_val) / abs(true_val)
            assert rel_error < 0.05, (
                f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                f"rel_error={rel_error:.2%} exceeds 5%"
            )


def test_insufficient_data_raises_error():
    """Fitting with insufficient data should raise InsufficientDataError."""
    x = np.array([1.0, 2.0])  # Only 2 points for 4 parameters
    y = np.array([2.0, 4.0])

    obj = HingeSaturation(x, y, guess_xh=5.0, guess_yh=10.0)

    with pytest.raises(InsufficientDataError):
        obj.make_fit()


def test_function_signature():
    """Test that function has correct parameter signature."""
    x = np.array([0.0, 5.0, 10.0])
    y = np.array([0.0, 10.0, 10.0])
    obj = HingeSaturation(x, y, guess_xh=5.0, guess_yh=10.0)

    sig = inspect.signature(obj.function)
    params = tuple(sig.parameters.keys())

    assert params == (
        "x",
        "xh",
        "yh",
        "x1",
        "m2",
    ), f"Function should have signature (x, xh, yh, x1, m2), got {params}"


def test_tex_function_property():
    """Test that TeX_function returns expected LaTeX string."""
    x = np.array([0.0, 5.0, 10.0])
    y = np.array([0.0, 10.0, 10.0])
    obj = HingeSaturation(x, y, guess_xh=5.0, guess_yh=10.0)

    tex = obj.TeX_function
    assert isinstance(tex, str), f"TeX_function should return str, got {type(tex)}"
    assert r"\min" in tex, "TeX_function should contain \\min"
    assert "y_1" in tex or "y_i" in tex, "TeX_function should reference y components"


def test_callable_interface(clean_saturation_data):
    """Test that fitted object is callable and returns correct shape."""
    x, y, w, true_params = clean_saturation_data

    obj = HingeSaturation(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])
    obj.make_fit()

    # Test callable interface
    x_test = np.array([1.0, 5.0, 10.0])
    y_pred = obj(x_test)

    assert (
        y_pred.shape == x_test.shape
    ), f"Predicted shape {y_pred.shape} should match input shape {x_test.shape}"
    assert np.all(np.isfinite(y_pred)), "All predicted values should be finite"


def test_popt_has_correct_keys(clean_saturation_data):
    """Test that popt contains expected parameter names."""
    x, y, w, true_params = clean_saturation_data

    obj = HingeSaturation(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])
    obj.make_fit()

    expected_keys = {"xh", "yh", "x1", "m2"}
    actual_keys = set(obj.popt.keys())

    assert (
        actual_keys == expected_keys
    ), f"popt keys should be {expected_keys}, got {actual_keys}"


def test_psigma_has_same_keys_as_popt(noisy_saturation_data):
    """Test that psigma has same keys as popt."""
    x, y, w, true_params = noisy_saturation_data

    obj = HingeSaturation(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])
    obj.make_fit()

    assert set(obj.psigma.keys()) == set(obj.popt.keys()), (
        f"psigma keys {set(obj.psigma.keys())} should match "
        f"popt keys {set(obj.popt.keys())}"
    )


def test_psigma_values_are_positive(noisy_saturation_data):
    """Test that all parameter uncertainties are positive."""
    x, y, w, true_params = noisy_saturation_data

    obj = HingeSaturation(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])
    obj.make_fit()

    for param, sigma in obj.psigma.items():
        assert sigma > 0, f"psigma['{param}'] = {sigma} should be positive"


# =============================================================================
# =============================================================================
#
# TESTS FOR NEW HINGE FIT FUNCTION CLASSES
#
# The following sections test five new FitFunction subclasses:
#   - TwoLine: Two intersecting lines with np.minimum
#   - Saturation: Reparameterized TwoLine with xs, s, theta
#   - HingeMin: Hinge with specified intersection point (minimum)
#   - HingeMax: Hinge with specified intersection point (maximum)
#   - HingeAtPoint: Hinge through a specified (xh, yh) point
#
# =============================================================================
# =============================================================================


from solarwindpy.fitfunctions.hinge import (
    TwoLine,
    Saturation,
    HingeMin,
    HingeMax,
    HingeAtPoint,
)


# =============================================================================
# TwoLine Tests
# =============================================================================
# TwoLine: f(x) = np.minimum(m1*(x-x1), m2*(x-x2))
# Parameters: x1, x2, m1, m2
# Derived: xs = (m1*x1 - m2*x2)/(m1 - m2), s = m1*(xs - x1), theta
# =============================================================================


# -----------------------------------------------------------------------------
# TwoLine Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def clean_twoline_data():
    """Perfect TwoLine data (no noise) with lines intersecting at (5, 10).

    Parameters: x1=0, x2=15, m1=2, m2=-1
    Line1: y = 2*(x - 0) = 2x, passes through (0, 0) and (5, 10)
    Line2: y = -1*(x - 15) = -x + 15, passes through (15, 0) and (5, 10)
    Intersection: xs = (2*0 - (-1)*15)/(2 - (-1)) = 15/3 = 5
                  s = 2*(5 - 0) = 10
    """
    true_params = {"x1": 0.0, "x2": 15.0, "m1": 2.0, "m2": -1.0}
    x = np.linspace(-2, 20, 300)
    y1 = true_params["m1"] * (x - true_params["x1"])
    y2 = true_params["m2"] * (x - true_params["x2"])
    y = np.minimum(y1, y2)
    w = np.ones_like(x)
    return x, y, w, true_params


@pytest.fixture
def noisy_twoline_data():
    """TwoLine data with 5% Gaussian noise.

    Parameters: x1=0, x2=15, m1=2, m2=-1
    Noise std = 0.5 (5% of max value ~10)
    """
    rng = np.random.default_rng(42)
    true_params = {"x1": 0.0, "x2": 15.0, "m1": 2.0, "m2": -1.0}
    x = np.linspace(-2, 20, 300)
    y1 = true_params["m1"] * (x - true_params["x1"])
    y2 = true_params["m2"] * (x - true_params["x2"])
    y_true = np.minimum(y1, y2)
    noise_std = 0.5
    y = y_true + rng.normal(0, noise_std, len(x))
    w = np.ones_like(x) / noise_std
    return x, y, w, true_params


@pytest.fixture
def twoline_parallel_slopes_data():
    """TwoLine where slopes are same sign but different magnitude.

    Parameters: x1=0, x2=10, m1=3, m2=0.5
    Lines intersect where: 3*(x-0) = 0.5*(x-10)
    3x = 0.5x - 5 => 2.5x = -5 => x = -2
    y = 3*(-2) = -6
    """
    true_params = {"x1": 0.0, "x2": 10.0, "m1": 3.0, "m2": 0.5}
    x = np.linspace(-5, 15, 300)
    y1 = true_params["m1"] * (x - true_params["x1"])
    y2 = true_params["m2"] * (x - true_params["x2"])
    y = np.minimum(y1, y2)
    w = np.ones_like(x)
    return x, y, w, true_params


# -----------------------------------------------------------------------------
# TwoLine E1. Function Evaluation Tests
# -----------------------------------------------------------------------------


def test_twoline_func_evaluates_line1_region_correctly():
    """TwoLine should follow line1 where m1*(x-x1) < m2*(x-x2).

    With x1=0, x2=15, m1=2, m2=-1:
    Line1: y = 2x, Line2: y = -x + 15
    Intersection at x=5. For x<5, line1 < line2.
    """
    x1, x2, m1, m2 = 0.0, 15.0, 2.0, -1.0

    x_test = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    # y = 2x for these points
    expected = np.array([0.0, 2.0, 4.0, 6.0, 8.0])

    x_dummy = np.linspace(0, 15, 50)
    y_dummy = np.minimum(m1 * x_dummy, -m2 * (x_dummy - x2))
    obj = TwoLine(x_dummy, y_dummy, guess_xs=5.0)
    result = obj.function(x_test, x1, x2, m1, m2)

    np.testing.assert_allclose(
        result,
        expected,
        rtol=1e-10,
        err_msg="TwoLine should follow line1 in left region",
    )


def test_twoline_func_evaluates_line2_region_correctly():
    """TwoLine should follow line2 where m2*(x-x2) < m1*(x-x1).

    With x1=0, x2=15, m1=2, m2=-1:
    For x>5, line2 = -x + 15 < line1 = 2x.
    """
    x1, x2, m1, m2 = 0.0, 15.0, 2.0, -1.0

    x_test = np.array([6.0, 8.0, 10.0, 12.0, 15.0])
    # y = -x + 15 for these points
    expected = np.array([9.0, 7.0, 5.0, 3.0, 0.0])

    x_dummy = np.linspace(0, 15, 50)
    y_dummy = np.minimum(m1 * x_dummy, -m2 * (x_dummy - x2))
    obj = TwoLine(x_dummy, y_dummy, guess_xs=5.0)
    result = obj.function(x_test, x1, x2, m1, m2)

    np.testing.assert_allclose(
        result,
        expected,
        rtol=1e-10,
        err_msg="TwoLine should follow line2 in right region",
    )


def test_twoline_func_evaluates_intersection_correctly():
    """TwoLine should equal both lines at intersection point.

    Intersection at x=5: y = 2*5 = 10 = -5 + 15 = 10
    """
    x1, x2, m1, m2 = 0.0, 15.0, 2.0, -1.0
    xs = 5.0  # Intersection x

    x_test = np.array([xs])
    expected = np.array([10.0])

    x_dummy = np.linspace(0, 15, 50)
    y_dummy = np.minimum(m1 * x_dummy, -m2 * (x_dummy - x2))
    obj = TwoLine(x_dummy, y_dummy, guess_xs=xs)
    result = obj.function(x_test, x1, x2, m1, m2)

    np.testing.assert_allclose(
        result,
        expected,
        rtol=1e-10,
        err_msg="TwoLine should be continuous at intersection",
    )


# -----------------------------------------------------------------------------
# TwoLine E2. Parameter Recovery Tests (Clean Data)
# -----------------------------------------------------------------------------


def test_twoline_fit_recovers_exact_parameters_from_clean_data(clean_twoline_data):
    """Fitting noise-free TwoLine data should recover parameters within 2%."""
    x, y, w, true_params = clean_twoline_data

    obj = TwoLine(x, y, guess_xs=5.0)
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


def test_twoline_fit_recovers_parallel_slopes_parameters(twoline_parallel_slopes_data):
    """Fitting TwoLine with same-sign slopes should recover parameters within 2%."""
    x, y, w, true_params = twoline_parallel_slopes_data

    obj = TwoLine(x, y, guess_xs=-2.0)
    obj.make_fit()

    for param, true_val in true_params.items():
        fitted_val = obj.popt[param]
        if abs(true_val) < 0.1:
            assert (
                abs(fitted_val - true_val) < 0.1
            ), f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}"
        else:
            rel_error = abs(fitted_val - true_val) / abs(true_val)
            assert rel_error < 0.02, (
                f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                f"rel_error={rel_error:.2%}"
            )


# -----------------------------------------------------------------------------
# TwoLine E3. Noisy Data Tests
# -----------------------------------------------------------------------------


def test_twoline_fit_with_noise_recovers_parameters_within_2sigma(noisy_twoline_data):
    """Fitted TwoLine parameters should be within 2sigma of true values.

    With 4 parameters at 2sigma (95%), joint probability is (0.95)^4 = 81%.
    """
    x, y, w, true_params = noisy_twoline_data

    obj = TwoLine(x, y, guess_xs=5.0)
    obj.make_fit()

    for param, true_val in true_params.items():
        fitted_val = obj.popt[param]
        sigma = obj.psigma[param]
        deviation = abs(fitted_val - true_val)

        assert deviation < 2 * sigma, (
            f"{param}: |fitted({fitted_val:.4f}) - true({true_val:.4f})| = "
            f"{deviation:.4f} exceeds 2sigma = {2*sigma:.4f}"
        )


# -----------------------------------------------------------------------------
# TwoLine E4. Derived Property Tests
# -----------------------------------------------------------------------------


def test_twoline_xs_property_is_consistent(clean_twoline_data):
    """Verify xs = (m1*x1 - m2*x2)/(m1 - m2) for fitted params.

    True params: x1=0, x2=15, m1=2, m2=-1
    xs = (2*0 - (-1)*15)/(2 - (-1)) = 15/3 = 5
    """
    x, y, w, true_params = clean_twoline_data

    obj = TwoLine(x, y, guess_xs=5.0)
    obj.make_fit()

    m1 = obj.popt["m1"]
    m2 = obj.popt["m2"]
    x1 = obj.popt["x1"]
    x2 = obj.popt["x2"]

    xs_expected = (m1 * x1 - m2 * x2) / (m1 - m2)

    np.testing.assert_allclose(
        obj.xs,
        xs_expected,
        rtol=1e-6,
        err_msg="TwoLine.xs should equal (m1*x1 - m2*x2)/(m1 - m2)",
    )


def test_twoline_s_property_is_consistent(clean_twoline_data):
    """Verify s = m1*(xs - x1) for fitted params.

    True params: xs=5, x1=0, m1=2
    s = 2*(5 - 0) = 10
    """
    x, y, w, true_params = clean_twoline_data

    obj = TwoLine(x, y, guess_xs=5.0)
    obj.make_fit()

    m1 = obj.popt["m1"]
    x1 = obj.popt["x1"]
    xs = obj.xs

    s_expected = m1 * (xs - x1)

    np.testing.assert_allclose(
        obj.s,
        s_expected,
        rtol=1e-6,
        err_msg="TwoLine.s should equal m1*(xs - x1)",
    )


def test_twoline_theta_property_is_positive_for_converging_lines(clean_twoline_data):
    """Theta (angle between lines) should be positive for converging lines.

    Lines y=2x and y=-x+15 form an angle. theta = arctan(m1) - arctan(m2).
    theta = arctan(2) - arctan(-1) = 1.107 - (-0.785) = 1.892 rad ~ 108 deg
    """
    x, y, w, true_params = clean_twoline_data

    obj = TwoLine(x, y, guess_xs=5.0)
    obj.make_fit()

    m1 = true_params["m1"]
    m2 = true_params["m2"]
    theta_expected = np.arctan(m1) - np.arctan(m2)

    assert (
        obj.theta > 0
    ), f"theta={obj.theta:.4f} should be positive for converging lines"
    np.testing.assert_allclose(
        obj.theta,
        theta_expected,
        rtol=0.02,
        err_msg=f"TwoLine.theta should be arctan(m1)-arctan(m2)={theta_expected:.4f}",
    )


# -----------------------------------------------------------------------------
# TwoLine E5. Edge Cases and Interface Tests
# -----------------------------------------------------------------------------


def test_twoline_function_signature():
    """Test that TwoLine function has correct parameter signature."""
    x = np.array([0.0, 5.0, 10.0])
    y = np.array([0.0, 10.0, 5.0])
    obj = TwoLine(x, y, guess_xs=5.0)

    sig = inspect.signature(obj.function)
    params = tuple(sig.parameters.keys())

    assert params == (
        "x",
        "x1",
        "x2",
        "m1",
        "m2",
    ), f"Function should have signature (x, x1, x2, m1, m2), got {params}"


def test_twoline_popt_has_correct_keys(clean_twoline_data):
    """Test that TwoLine popt contains expected parameter names."""
    x, y, w, true_params = clean_twoline_data

    obj = TwoLine(x, y, guess_xs=5.0)
    obj.make_fit()

    expected_keys = {"x1", "x2", "m1", "m2"}
    actual_keys = set(obj.popt.keys())

    assert (
        actual_keys == expected_keys
    ), f"popt keys should be {expected_keys}, got {actual_keys}"


def test_twoline_callable_interface(clean_twoline_data):
    """Test that fitted TwoLine object is callable and returns correct shape."""
    x, y, w, true_params = clean_twoline_data

    obj = TwoLine(x, y, guess_xs=5.0)
    obj.make_fit()

    x_test = np.array([1.0, 5.0, 10.0])
    y_pred = obj(x_test)

    assert (
        y_pred.shape == x_test.shape
    ), f"Predicted shape {y_pred.shape} should match input shape {x_test.shape}"
    assert np.all(np.isfinite(y_pred)), "All predicted values should be finite"


def test_twoline_insufficient_data_raises_error():
    """Fitting TwoLine with insufficient data should raise InsufficientDataError."""
    x = np.array([1.0, 2.0, 3.0])  # Only 3 points for 4 parameters
    y = np.array([2.0, 4.0, 6.0])

    obj = TwoLine(x, y, guess_xs=5.0)

    with pytest.raises(InsufficientDataError):
        obj.make_fit()


# =============================================================================
# Saturation Tests
# =============================================================================
# Saturation: Reparameterized TwoLine with parameters (x1, xs, s, theta)
# function: np.minimum(l1, l2) where m1 = s/(xs-x1), m2 = tan(arctan(m1) - theta)
# Derived: m1, m2, x2
# =============================================================================


# -----------------------------------------------------------------------------
# Saturation Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def clean_saturation_twoline_data():
    """Perfect Saturation data with known x1, xs, s, theta.

    Parameters: x1=0, xs=5, s=10, theta=pi/3 (60 degrees)
    m1 = s/(xs-x1) = 10/(5-0) = 2
    m2 = tan(arctan(2) - pi/3) = tan(1.107 - 1.047) = tan(0.060) = 0.060
    Line1: y = 2*(x - 0) = 2x
    Line2: y = m2*(x - x2) where x2 = xs - s/m2
    """
    true_params = {"x1": 0.0, "xs": 5.0, "s": 10.0, "theta": np.pi / 3}
    m1 = true_params["s"] / (true_params["xs"] - true_params["x1"])
    m2 = np.tan(np.arctan(m1) - true_params["theta"])
    x2 = true_params["xs"] - true_params["s"] / m2

    x = np.linspace(-2, 20, 300)
    y1 = m1 * (x - true_params["x1"])
    y2 = m2 * (x - x2)
    y = np.minimum(y1, y2)
    w = np.ones_like(x)
    return x, y, w, true_params, {"m1": m1, "m2": m2, "x2": x2}


@pytest.fixture
def noisy_saturation_twoline_data():
    """Saturation data with 5% Gaussian noise.

    Parameters: x1=0, xs=5, s=10, theta=pi/4 (45 degrees)
    """
    rng = np.random.default_rng(42)
    true_params = {"x1": 0.0, "xs": 5.0, "s": 10.0, "theta": np.pi / 4}
    m1 = true_params["s"] / (true_params["xs"] - true_params["x1"])
    m2 = np.tan(np.arctan(m1) - true_params["theta"])
    x2 = true_params["xs"] - true_params["s"] / m2

    x = np.linspace(-2, 20, 300)
    y1 = m1 * (x - true_params["x1"])
    y2 = m2 * (x - x2)
    y_true = np.minimum(y1, y2)
    noise_std = 0.5
    y = y_true + rng.normal(0, noise_std, len(x))
    w = np.ones_like(x) / noise_std
    return x, y, w, true_params


@pytest.fixture
def saturation_small_theta_data():
    """Saturation with small theta (nearly parallel lines after hinge).

    Parameters: x1=0, xs=5, s=10, theta=0.1 (about 5.7 degrees)
    """
    true_params = {"x1": 0.0, "xs": 5.0, "s": 10.0, "theta": 0.1}
    m1 = true_params["s"] / (true_params["xs"] - true_params["x1"])
    m2 = np.tan(np.arctan(m1) - true_params["theta"])
    x2 = true_params["xs"] - true_params["s"] / m2

    x = np.linspace(-2, 25, 300)
    y1 = m1 * (x - true_params["x1"])
    y2 = m2 * (x - x2)
    y = np.minimum(y1, y2)
    w = np.ones_like(x)
    return x, y, w, true_params


# -----------------------------------------------------------------------------
# Saturation E1. Function Evaluation Tests
# -----------------------------------------------------------------------------


def test_saturation_func_evaluates_rising_region_correctly():
    """Saturation should follow line1 (rising) before saturation point.

    With x1=0, xs=5, s=10: m1 = 10/5 = 2
    Before xs=5: f(x) = 2*(x - 0) = 2x
    """
    x1, xs, s, theta = 0.0, 5.0, 10.0, np.pi / 4
    m1 = s / (xs - x1)

    x_test = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    expected = m1 * (x_test - x1)  # [0, 2, 4, 6, 8]

    x_dummy = np.linspace(0, 15, 50)
    y_dummy = 2 * x_dummy
    obj = Saturation(x_dummy, y_dummy, guess_xs=xs, guess_s=s)
    result = obj.function(x_test, x1, xs, s, theta)

    np.testing.assert_allclose(
        result,
        expected,
        rtol=1e-10,
        err_msg="Saturation should follow rising line before xs",
    )


def test_saturation_func_passes_through_saturation_point():
    """Saturation function should pass through (xs, s).

    At x=xs: both lines should equal s.
    """
    x1, xs, s, theta = 0.0, 5.0, 10.0, np.pi / 4

    x_test = np.array([xs])
    expected = np.array([s])

    x_dummy = np.linspace(0, 15, 50)
    y_dummy = 2 * x_dummy
    obj = Saturation(x_dummy, y_dummy, guess_xs=xs, guess_s=s)
    result = obj.function(x_test, x1, xs, s, theta)

    np.testing.assert_allclose(
        result,
        expected,
        rtol=1e-10,
        err_msg="Saturation function should pass through (xs, s)",
    )


def test_saturation_func_theta_controls_plateau_slope():
    """Different theta values should produce different plateau slopes.

    theta=0: m2 = m1 (plateau continues at same slope)
    theta>0: m2 < m1 (plateau is less steep)
    """
    x1, xs, s = 0.0, 5.0, 10.0
    m1 = s / (xs - x1)  # = 2

    theta_small = 0.1
    theta_large = np.pi / 3

    m2_small = np.tan(np.arctan(m1) - theta_small)
    m2_large = np.tan(np.arctan(m1) - theta_large)

    # Larger theta should give smaller m2 (less steep plateau)
    assert (
        m2_small > m2_large
    ), f"m2_small={m2_small:.4f} should be > m2_large={m2_large:.4f}"


# -----------------------------------------------------------------------------
# Saturation E2. Parameter Recovery Tests (Clean Data)
# -----------------------------------------------------------------------------


def test_saturation_fit_recovers_exact_parameters_from_clean_data(
    clean_saturation_twoline_data,
):
    """Fitting noise-free Saturation data should recover parameters within 2%."""
    x, y, w, true_params, derived = clean_saturation_twoline_data

    obj = Saturation(x, y, guess_xs=true_params["xs"], guess_s=true_params["s"])
    obj.make_fit()

    for param, true_val in true_params.items():
        fitted_val = obj.popt[param]
        if abs(true_val) < 0.1:
            assert (
                abs(fitted_val - true_val) < 0.05
            ), f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}"
        else:
            rel_error = abs(fitted_val - true_val) / abs(true_val)
            assert rel_error < 0.02, (
                f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                f"rel_error={rel_error:.2%} exceeds 2% tolerance"
            )


def test_saturation_fit_recovers_small_theta_parameters(saturation_small_theta_data):
    """Fitting Saturation with small theta should recover parameters within 5%."""
    x, y, w, true_params = saturation_small_theta_data

    obj = Saturation(x, y, guess_xs=true_params["xs"], guess_s=true_params["s"])
    obj.make_fit()

    # Small theta is harder to fit precisely, use 5% tolerance
    for param, true_val in true_params.items():
        fitted_val = obj.popt[param]
        if abs(true_val) < 0.1:
            assert (
                abs(fitted_val - true_val) < 0.1
            ), f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}"
        else:
            rel_error = abs(fitted_val - true_val) / abs(true_val)
            assert rel_error < 0.05, (
                f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                f"rel_error={rel_error:.2%}"
            )


# -----------------------------------------------------------------------------
# Saturation E3. Noisy Data Tests
# -----------------------------------------------------------------------------


def test_saturation_fit_with_noise_recovers_parameters_within_2sigma(
    noisy_saturation_twoline_data,
):
    """Fitted Saturation parameters should be within 2sigma of true values."""
    x, y, w, true_params = noisy_saturation_twoline_data

    obj = Saturation(x, y, guess_xs=true_params["xs"], guess_s=true_params["s"])
    obj.make_fit()

    for param, true_val in true_params.items():
        fitted_val = obj.popt[param]
        sigma = obj.psigma[param]
        deviation = abs(fitted_val - true_val)

        assert deviation < 2 * sigma, (
            f"{param}: |fitted({fitted_val:.4f}) - true({true_val:.4f})| = "
            f"{deviation:.4f} exceeds 2sigma = {2*sigma:.4f}"
        )


# -----------------------------------------------------------------------------
# Saturation E4. Derived Property Tests
# -----------------------------------------------------------------------------


def test_saturation_m1_property_is_consistent(clean_saturation_twoline_data):
    """Verify m1 = s/(xs - x1) for fitted params."""
    x, y, w, true_params, derived = clean_saturation_twoline_data

    obj = Saturation(x, y, guess_xs=true_params["xs"], guess_s=true_params["s"])
    obj.make_fit()

    s = obj.popt["s"]
    xs = obj.popt["xs"]
    x1 = obj.popt["x1"]

    m1_expected = s / (xs - x1)

    np.testing.assert_allclose(
        obj.m1,
        m1_expected,
        rtol=1e-6,
        err_msg="Saturation.m1 should equal s/(xs - x1)",
    )


def test_saturation_m2_property_is_consistent(clean_saturation_twoline_data):
    """Verify m2 = tan(arctan(m1) - theta) for fitted params."""
    x, y, w, true_params, derived = clean_saturation_twoline_data

    obj = Saturation(x, y, guess_xs=true_params["xs"], guess_s=true_params["s"])
    obj.make_fit()

    m1 = obj.m1
    theta = obj.popt["theta"]

    m2_expected = np.tan(np.arctan(m1) - theta)

    np.testing.assert_allclose(
        obj.m2,
        m2_expected,
        rtol=1e-6,
        err_msg="Saturation.m2 should equal tan(arctan(m1) - theta)",
    )


def test_saturation_x2_property_is_consistent(clean_saturation_twoline_data):
    """Verify x2 = xs - s/m2 for fitted params."""
    x, y, w, true_params, derived = clean_saturation_twoline_data

    obj = Saturation(x, y, guess_xs=true_params["xs"], guess_s=true_params["s"])
    obj.make_fit()

    xs = obj.popt["xs"]
    s = obj.popt["s"]
    m2 = obj.m2

    x2_expected = xs - s / m2

    np.testing.assert_allclose(
        obj.x2,
        x2_expected,
        rtol=1e-6,
        err_msg="Saturation.x2 should equal xs - s/m2",
    )


# -----------------------------------------------------------------------------
# Saturation E5. Edge Cases and Interface Tests
# -----------------------------------------------------------------------------


def test_saturation_function_signature():
    """Test that Saturation function has correct parameter signature."""
    x = np.array([0.0, 5.0, 10.0])
    y = np.array([0.0, 10.0, 12.0])
    obj = Saturation(x, y, guess_xs=5.0, guess_s=10.0)

    sig = inspect.signature(obj.function)
    params = tuple(sig.parameters.keys())

    assert params == (
        "x",
        "x1",
        "xs",
        "s",
        "theta",
    ), f"Function should have signature (x, x1, xs, s, theta), got {params}"


def test_saturation_popt_has_correct_keys(clean_saturation_twoline_data):
    """Test that Saturation popt contains expected parameter names."""
    x, y, w, true_params, derived = clean_saturation_twoline_data

    obj = Saturation(x, y, guess_xs=true_params["xs"], guess_s=true_params["s"])
    obj.make_fit()

    expected_keys = {"x1", "xs", "s", "theta"}
    actual_keys = set(obj.popt.keys())

    assert (
        actual_keys == expected_keys
    ), f"popt keys should be {expected_keys}, got {actual_keys}"


def test_saturation_callable_interface(clean_saturation_twoline_data):
    """Test that fitted Saturation object is callable and returns correct shape."""
    x, y, w, true_params, derived = clean_saturation_twoline_data

    obj = Saturation(x, y, guess_xs=true_params["xs"], guess_s=true_params["s"])
    obj.make_fit()

    x_test = np.array([1.0, 5.0, 10.0])
    y_pred = obj(x_test)

    assert (
        y_pred.shape == x_test.shape
    ), f"Predicted shape {y_pred.shape} should match input shape {x_test.shape}"
    assert np.all(np.isfinite(y_pred)), "All predicted values should be finite"


def test_saturation_insufficient_data_raises_error():
    """Fitting Saturation with insufficient data should raise InsufficientDataError."""
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([2.0, 4.0, 6.0])

    obj = Saturation(x, y, guess_xs=5.0, guess_s=10.0)

    with pytest.raises(InsufficientDataError):
        obj.make_fit()


# =============================================================================
# HingeMin Tests
# =============================================================================
# HingeMin: f(x) = np.minimum(l1, l2) where l1 = m1*(x-x1), l2 = m2*(x-x2)
# Parameters: m1, x1, x2, h (hinge x-coordinate)
# Constraint: both lines pass through (h, m1*(h-x1))
# m2 = m1*(h-x1)/(h-x2)
# Derived: m2, theta
# =============================================================================


# -----------------------------------------------------------------------------
# HingeMin Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def clean_hingemin_data():
    """Perfect HingeMin data with lines meeting at hinge point.

    Parameters: m1=2, x1=0, x2=10, h=5
    At hinge h=5: yh = m1*(h-x1) = 2*(5-0) = 10
    m2 = m1*(h-x1)/(h-x2) = 2*(5-0)/(5-10) = 10/(-5) = -2
    Line1: y = 2*(x - 0) = 2x
    Line2: y = -2*(x - 10) = -2x + 20
    Intersection: 2x = -2x + 20 => 4x = 20 => x = 5, y = 10
    """
    true_params = {"m1": 2.0, "x1": 0.0, "x2": 10.0, "h": 5.0}
    yh = true_params["m1"] * (true_params["h"] - true_params["x1"])
    m2 = (
        true_params["m1"]
        * (true_params["h"] - true_params["x1"])
        / (true_params["h"] - true_params["x2"])
    )

    x = np.linspace(-2, 15, 300)
    y1 = true_params["m1"] * (x - true_params["x1"])
    y2 = m2 * (x - true_params["x2"])
    y = np.minimum(y1, y2)
    w = np.ones_like(x)
    return x, y, w, true_params, {"m2": m2, "yh": yh}


@pytest.fixture
def noisy_hingemin_data():
    """HingeMin data with 5% Gaussian noise.

    Parameters: m1=2, x1=0, x2=10, h=5
    """
    rng = np.random.default_rng(42)
    true_params = {"m1": 2.0, "x1": 0.0, "x2": 10.0, "h": 5.0}
    m2 = (
        true_params["m1"]
        * (true_params["h"] - true_params["x1"])
        / (true_params["h"] - true_params["x2"])
    )

    x = np.linspace(-2, 15, 300)
    y1 = true_params["m1"] * (x - true_params["x1"])
    y2 = m2 * (x - true_params["x2"])
    y_true = np.minimum(y1, y2)
    noise_std = 0.5
    y = y_true + rng.normal(0, noise_std, len(x))
    w = np.ones_like(x) / noise_std
    return x, y, w, true_params


@pytest.fixture
def hingemin_positive_slopes_data():
    """HingeMin where both slopes are positive but different.

    Parameters: m1=3, x1=0, x2=-5, h=5
    yh = 3*(5-0) = 15
    m2 = 3*(5-0)/(5-(-5)) = 15/10 = 1.5
    Line1: y = 3x
    Line2: y = 1.5*(x + 5) = 1.5x + 7.5
    """
    true_params = {"m1": 3.0, "x1": 0.0, "x2": -5.0, "h": 5.0}
    m2 = (
        true_params["m1"]
        * (true_params["h"] - true_params["x1"])
        / (true_params["h"] - true_params["x2"])
    )

    x = np.linspace(-3, 15, 300)
    y1 = true_params["m1"] * (x - true_params["x1"])
    y2 = m2 * (x - true_params["x2"])
    y = np.minimum(y1, y2)
    w = np.ones_like(x)
    return x, y, w, true_params


# -----------------------------------------------------------------------------
# HingeMin E1. Function Evaluation Tests
# -----------------------------------------------------------------------------


def test_hingemin_func_evaluates_line1_region_correctly():
    """HingeMin should follow line1 where m1*(x-x1) < m2*(x-x2).

    With m1=2, x1=0, x2=10, h=5: m2=-2
    For x<5: 2x < -2x+20, so line1 dominates minimum.
    """
    m1, x1, x2, h = 2.0, 0.0, 10.0, 5.0
    m2 = m1 * (h - x1) / (h - x2)  # = -2

    x_test = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    expected = m1 * (x_test - x1)  # [0, 2, 4, 6, 8]

    x_dummy = np.linspace(0, 15, 50)
    y_dummy = np.minimum(m1 * x_dummy, m2 * (x_dummy - x2))
    obj = HingeMin(x_dummy, y_dummy, guess_h=h)
    result = obj.function(x_test, m1, x1, x2, h)

    np.testing.assert_allclose(
        result,
        expected,
        rtol=1e-10,
        err_msg="HingeMin should follow line1 in left region",
    )


def test_hingemin_func_evaluates_hinge_point_correctly():
    """HingeMin should pass through hinge point (h, yh).

    At h=5: yh = m1*(h-x1) = 2*5 = 10
    """
    m1, x1, x2, h = 2.0, 0.0, 10.0, 5.0

    x_test = np.array([h])
    expected = np.array([m1 * (h - x1)])  # [10]

    x_dummy = np.linspace(0, 15, 50)
    m2 = m1 * (h - x1) / (h - x2)
    y_dummy = np.minimum(m1 * x_dummy, m2 * (x_dummy - x2))
    obj = HingeMin(x_dummy, y_dummy, guess_h=h)
    result = obj.function(x_test, m1, x1, x2, h)

    np.testing.assert_allclose(
        result,
        expected,
        rtol=1e-10,
        err_msg="HingeMin should pass through hinge point",
    )


def test_hingemin_func_evaluates_line2_region_correctly():
    """HingeMin should follow line2 where m2*(x-x2) < m1*(x-x1).

    For x>5 with our parameters: -2x+20 < 2x
    """
    m1, x1, x2, h = 2.0, 0.0, 10.0, 5.0
    m2 = m1 * (h - x1) / (h - x2)  # = -2

    x_test = np.array([6.0, 7.0, 8.0, 9.0, 10.0])
    expected = m2 * (x_test - x2)  # [-2*(x-10)] = [8, 6, 4, 2, 0]

    x_dummy = np.linspace(0, 15, 50)
    y_dummy = np.minimum(m1 * x_dummy, m2 * (x_dummy - x2))
    obj = HingeMin(x_dummy, y_dummy, guess_h=h)
    result = obj.function(x_test, m1, x1, x2, h)

    np.testing.assert_allclose(
        result,
        expected,
        rtol=1e-10,
        err_msg="HingeMin should follow line2 in right region",
    )


# -----------------------------------------------------------------------------
# HingeMin E2. Parameter Recovery Tests (Clean Data)
# -----------------------------------------------------------------------------


def test_hingemin_fit_recovers_exact_parameters_from_clean_data(clean_hingemin_data):
    """Fitting noise-free HingeMin data should recover parameters within 2%."""
    x, y, w, true_params, derived = clean_hingemin_data

    obj = HingeMin(x, y, guess_h=true_params["h"])
    obj.make_fit()

    for param, true_val in true_params.items():
        fitted_val = obj.popt[param]
        if abs(true_val) < 0.1:
            assert (
                abs(fitted_val - true_val) < 0.05
            ), f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}"
        else:
            rel_error = abs(fitted_val - true_val) / abs(true_val)
            assert rel_error < 0.02, (
                f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                f"rel_error={rel_error:.2%} exceeds 2% tolerance"
            )


def test_hingemin_fit_recovers_positive_slopes_parameters(
    hingemin_positive_slopes_data,
):
    """Fitting HingeMin with positive slopes should recover parameters within 2%."""
    x, y, w, true_params = hingemin_positive_slopes_data

    obj = HingeMin(x, y, guess_h=true_params["h"])
    obj.make_fit()

    for param, true_val in true_params.items():
        fitted_val = obj.popt[param]
        if abs(true_val) < 0.1:
            assert (
                abs(fitted_val - true_val) < 0.1
            ), f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}"
        else:
            rel_error = abs(fitted_val - true_val) / abs(true_val)
            assert rel_error < 0.02, (
                f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                f"rel_error={rel_error:.2%}"
            )


# -----------------------------------------------------------------------------
# HingeMin E3. Noisy Data Tests
# -----------------------------------------------------------------------------


def test_hingemin_fit_with_noise_recovers_parameters_within_2sigma(noisy_hingemin_data):
    """Fitted HingeMin parameters should be within 2sigma of true values."""
    x, y, w, true_params = noisy_hingemin_data

    obj = HingeMin(x, y, guess_h=true_params["h"])
    obj.make_fit()

    for param, true_val in true_params.items():
        fitted_val = obj.popt[param]
        sigma = obj.psigma[param]
        deviation = abs(fitted_val - true_val)

        assert deviation < 2 * sigma, (
            f"{param}: |fitted({fitted_val:.4f}) - true({true_val:.4f})| = "
            f"{deviation:.4f} exceeds 2sigma = {2*sigma:.4f}"
        )


# -----------------------------------------------------------------------------
# HingeMin E4. Derived Property Tests
# -----------------------------------------------------------------------------


def test_hingemin_m2_property_is_consistent(clean_hingemin_data):
    """Verify m2 = m1*(h-x1)/(h-x2) for fitted params.

    True: m2 = 2*(5-0)/(5-10) = 10/(-5) = -2
    """
    x, y, w, true_params, derived = clean_hingemin_data

    obj = HingeMin(x, y, guess_h=true_params["h"])
    obj.make_fit()

    m1 = obj.popt["m1"]
    x1 = obj.popt["x1"]
    x2 = obj.popt["x2"]
    h = obj.popt["h"]

    m2_expected = m1 * (h - x1) / (h - x2)

    np.testing.assert_allclose(
        obj.m2,
        m2_expected,
        rtol=1e-6,
        err_msg="HingeMin.m2 should equal m1*(h-x1)/(h-x2)",
    )


def test_hingemin_theta_property_is_consistent(clean_hingemin_data):
    """Verify theta = arctan(m1) - arctan(m2) for fitted params."""
    x, y, w, true_params, derived = clean_hingemin_data

    obj = HingeMin(x, y, guess_h=true_params["h"])
    obj.make_fit()

    m1 = obj.popt["m1"]
    m2 = obj.m2
    theta_expected = np.arctan(m1) - np.arctan(m2)

    np.testing.assert_allclose(
        obj.theta,
        theta_expected,
        rtol=1e-6,
        err_msg="HingeMin.theta should equal arctan(m1) - arctan(m2)",
    )


def test_hingemin_lines_intersect_at_hinge(clean_hingemin_data):
    """Verify both lines pass through (h, yh) where yh = m1*(h-x1)."""
    x, y, w, true_params, derived = clean_hingemin_data

    obj = HingeMin(x, y, guess_h=true_params["h"])
    obj.make_fit()

    h = obj.popt["h"]
    m1 = obj.popt["m1"]
    x1 = obj.popt["x1"]
    x2 = obj.popt["x2"]
    m2 = obj.m2

    yh_from_line1 = m1 * (h - x1)
    yh_from_line2 = m2 * (h - x2)

    np.testing.assert_allclose(
        yh_from_line1,
        yh_from_line2,
        rtol=1e-6,
        err_msg="Both lines should pass through hinge point",
    )


# -----------------------------------------------------------------------------
# HingeMin E5. Edge Cases and Interface Tests
# -----------------------------------------------------------------------------


def test_hingemin_function_signature():
    """Test that HingeMin function has correct parameter signature."""
    x = np.array([0.0, 5.0, 10.0])
    y = np.array([0.0, 10.0, 0.0])
    obj = HingeMin(x, y, guess_h=5.0)

    sig = inspect.signature(obj.function)
    params = tuple(sig.parameters.keys())

    assert params == (
        "x",
        "m1",
        "x1",
        "x2",
        "h",
    ), f"Function should have signature (x, m1, x1, x2, h), got {params}"


def test_hingemin_popt_has_correct_keys(clean_hingemin_data):
    """Test that HingeMin popt contains expected parameter names."""
    x, y, w, true_params, derived = clean_hingemin_data

    obj = HingeMin(x, y, guess_h=true_params["h"])
    obj.make_fit()

    expected_keys = {"m1", "x1", "x2", "h"}
    actual_keys = set(obj.popt.keys())

    assert (
        actual_keys == expected_keys
    ), f"popt keys should be {expected_keys}, got {actual_keys}"


def test_hingemin_callable_interface(clean_hingemin_data):
    """Test that fitted HingeMin object is callable and returns correct shape."""
    x, y, w, true_params, derived = clean_hingemin_data

    obj = HingeMin(x, y, guess_h=true_params["h"])
    obj.make_fit()

    x_test = np.array([1.0, 5.0, 9.0])
    y_pred = obj(x_test)

    assert (
        y_pred.shape == x_test.shape
    ), f"Predicted shape {y_pred.shape} should match input shape {x_test.shape}"
    assert np.all(np.isfinite(y_pred)), "All predicted values should be finite"


def test_hingemin_insufficient_data_raises_error():
    """Fitting HingeMin with insufficient data should raise InsufficientDataError."""
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([2.0, 4.0, 3.0])

    obj = HingeMin(x, y, guess_h=2.0)

    with pytest.raises(InsufficientDataError):
        obj.make_fit()


# =============================================================================
# HingeMax Tests
# =============================================================================
# HingeMax: f(x) = np.maximum(l1, l2) where l1 = m1*(x-x1), l2 = m2*(x-x2)
# Parameters: m1, x1, x2, h (hinge x-coordinate)
# Constraint: both lines pass through (h, m1*(h-x1))
# m2 = m1*(h-x1)/(h-x2)
# Derived: m2, theta
# =============================================================================


# -----------------------------------------------------------------------------
# HingeMax Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def clean_hingemax_data():
    """Perfect HingeMax data with lines meeting at hinge point.

    Parameters: m1=-2, x1=0, x2=10, h=5
    At hinge h=5: yh = m1*(h-x1) = -2*(5-0) = -10
    m2 = m1*(h-x1)/(h-x2) = -2*(5-0)/(5-10) = -10/(-5) = 2
    Line1: y = -2*(x - 0) = -2x
    Line2: y = 2*(x - 10) = 2x - 20
    max(-2x, 2x-20) forms a V-shape opening upward with vertex at (5, -10)
    """
    true_params = {"m1": -2.0, "x1": 0.0, "x2": 10.0, "h": 5.0}
    yh = true_params["m1"] * (true_params["h"] - true_params["x1"])
    m2 = (
        true_params["m1"]
        * (true_params["h"] - true_params["x1"])
        / (true_params["h"] - true_params["x2"])
    )

    x = np.linspace(-2, 15, 300)
    y1 = true_params["m1"] * (x - true_params["x1"])
    y2 = m2 * (x - true_params["x2"])
    y = np.maximum(y1, y2)
    w = np.ones_like(x)
    return x, y, w, true_params, {"m2": m2, "yh": yh}


@pytest.fixture
def noisy_hingemax_data():
    """HingeMax data with 5% Gaussian noise.

    Parameters: m1=-2, x1=0, x2=10, h=5
    """
    rng = np.random.default_rng(42)
    true_params = {"m1": -2.0, "x1": 0.0, "x2": 10.0, "h": 5.0}
    m2 = (
        true_params["m1"]
        * (true_params["h"] - true_params["x1"])
        / (true_params["h"] - true_params["x2"])
    )

    x = np.linspace(-2, 15, 300)
    y1 = true_params["m1"] * (x - true_params["x1"])
    y2 = m2 * (x - true_params["x2"])
    y_true = np.maximum(y1, y2)
    noise_std = 0.5
    y = y_true + rng.normal(0, noise_std, len(x))
    w = np.ones_like(x) / noise_std
    return x, y, w, true_params


@pytest.fixture
def hingemax_negative_slopes_data():
    """HingeMax where both slopes are negative.

    Parameters: m1=-3, x1=0, x2=-5, h=5
    yh = -3*(5-0) = -15
    m2 = -3*(5-0)/(5-(-5)) = -15/10 = -1.5
    Line1: y = -3x
    Line2: y = -1.5*(x + 5) = -1.5x - 7.5
    """
    true_params = {"m1": -3.0, "x1": 0.0, "x2": -5.0, "h": 5.0}
    m2 = (
        true_params["m1"]
        * (true_params["h"] - true_params["x1"])
        / (true_params["h"] - true_params["x2"])
    )

    x = np.linspace(-3, 15, 300)
    y1 = true_params["m1"] * (x - true_params["x1"])
    y2 = m2 * (x - true_params["x2"])
    y = np.maximum(y1, y2)
    w = np.ones_like(x)
    return x, y, w, true_params


# -----------------------------------------------------------------------------
# HingeMax E1. Function Evaluation Tests
# -----------------------------------------------------------------------------


def test_hingemax_func_evaluates_line1_region_correctly():
    """HingeMax should follow line1 where m1*(x-x1) > m2*(x-x2).

    With m1=-2, x1=0, x2=10, h=5: m2=2
    For x<5: -2x > 2x-20, so line1 dominates maximum.
    """
    m1, x1, x2, h = -2.0, 0.0, 10.0, 5.0
    m2 = m1 * (h - x1) / (h - x2)  # = 2

    x_test = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    expected = m1 * (x_test - x1)  # [0, -2, -4, -6, -8]

    x_dummy = np.linspace(0, 15, 50)
    y_dummy = np.maximum(m1 * x_dummy, m2 * (x_dummy - x2))
    obj = HingeMax(x_dummy, y_dummy, guess_h=h)
    result = obj.function(x_test, m1, x1, x2, h)

    np.testing.assert_allclose(
        result,
        expected,
        rtol=1e-10,
        err_msg="HingeMax should follow line1 in left region",
    )


def test_hingemax_func_evaluates_hinge_point_correctly():
    """HingeMax should pass through hinge point (h, yh).

    At h=5: yh = m1*(h-x1) = -2*5 = -10
    """
    m1, x1, x2, h = -2.0, 0.0, 10.0, 5.0

    x_test = np.array([h])
    expected = np.array([m1 * (h - x1)])  # [-10]

    x_dummy = np.linspace(0, 15, 50)
    m2 = m1 * (h - x1) / (h - x2)
    y_dummy = np.maximum(m1 * x_dummy, m2 * (x_dummy - x2))
    obj = HingeMax(x_dummy, y_dummy, guess_h=h)
    result = obj.function(x_test, m1, x1, x2, h)

    np.testing.assert_allclose(
        result,
        expected,
        rtol=1e-10,
        err_msg="HingeMax should pass through hinge point",
    )


def test_hingemax_func_evaluates_line2_region_correctly():
    """HingeMax should follow line2 where m2*(x-x2) > m1*(x-x1).

    For x>5 with our parameters: 2x-20 > -2x
    """
    m1, x1, x2, h = -2.0, 0.0, 10.0, 5.0
    m2 = m1 * (h - x1) / (h - x2)  # = 2

    x_test = np.array([6.0, 7.0, 8.0, 9.0, 10.0])
    expected = m2 * (x_test - x2)  # [2*(x-10)] = [-8, -6, -4, -2, 0]

    x_dummy = np.linspace(0, 15, 50)
    y_dummy = np.maximum(m1 * x_dummy, m2 * (x_dummy - x2))
    obj = HingeMax(x_dummy, y_dummy, guess_h=h)
    result = obj.function(x_test, m1, x1, x2, h)

    np.testing.assert_allclose(
        result,
        expected,
        rtol=1e-10,
        err_msg="HingeMax should follow line2 in right region",
    )


# -----------------------------------------------------------------------------
# HingeMax E2. Parameter Recovery Tests (Clean Data)
# -----------------------------------------------------------------------------


def test_hingemax_fit_recovers_exact_parameters_from_clean_data(clean_hingemax_data):
    """Fitting noise-free HingeMax data should recover parameters within 2%."""
    x, y, w, true_params, derived = clean_hingemax_data

    obj = HingeMax(x, y, guess_h=true_params["h"])
    obj.make_fit()

    for param, true_val in true_params.items():
        fitted_val = obj.popt[param]
        if abs(true_val) < 0.1:
            assert (
                abs(fitted_val - true_val) < 0.05
            ), f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}"
        else:
            rel_error = abs(fitted_val - true_val) / abs(true_val)
            assert rel_error < 0.02, (
                f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                f"rel_error={rel_error:.2%} exceeds 2% tolerance"
            )


def test_hingemax_fit_recovers_negative_slopes_parameters(
    hingemax_negative_slopes_data,
):
    """Fitting HingeMax with negative slopes should recover parameters within 2%."""
    x, y, w, true_params = hingemax_negative_slopes_data

    obj = HingeMax(x, y, guess_h=true_params["h"])
    obj.make_fit()

    for param, true_val in true_params.items():
        fitted_val = obj.popt[param]
        if abs(true_val) < 0.1:
            assert (
                abs(fitted_val - true_val) < 0.1
            ), f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}"
        else:
            rel_error = abs(fitted_val - true_val) / abs(true_val)
            assert rel_error < 0.02, (
                f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                f"rel_error={rel_error:.2%}"
            )


# -----------------------------------------------------------------------------
# HingeMax E3. Noisy Data Tests
# -----------------------------------------------------------------------------


def test_hingemax_fit_with_noise_recovers_parameters_within_2sigma(noisy_hingemax_data):
    """Fitted HingeMax parameters should be within 2sigma of true values."""
    x, y, w, true_params = noisy_hingemax_data

    obj = HingeMax(x, y, guess_h=true_params["h"])
    obj.make_fit()

    for param, true_val in true_params.items():
        fitted_val = obj.popt[param]
        sigma = obj.psigma[param]
        deviation = abs(fitted_val - true_val)

        assert deviation < 2 * sigma, (
            f"{param}: |fitted({fitted_val:.4f}) - true({true_val:.4f})| = "
            f"{deviation:.4f} exceeds 2sigma = {2*sigma:.4f}"
        )


# -----------------------------------------------------------------------------
# HingeMax E4. Derived Property Tests
# -----------------------------------------------------------------------------


def test_hingemax_m2_property_is_consistent(clean_hingemax_data):
    """Verify m2 = m1*(h-x1)/(h-x2) for fitted params.

    True: m2 = -2*(5-0)/(5-10) = -10/(-5) = 2
    """
    x, y, w, true_params, derived = clean_hingemax_data

    obj = HingeMax(x, y, guess_h=true_params["h"])
    obj.make_fit()

    m1 = obj.popt["m1"]
    x1 = obj.popt["x1"]
    x2 = obj.popt["x2"]
    h = obj.popt["h"]

    m2_expected = m1 * (h - x1) / (h - x2)

    np.testing.assert_allclose(
        obj.m2,
        m2_expected,
        rtol=1e-6,
        err_msg="HingeMax.m2 should equal m1*(h-x1)/(h-x2)",
    )


def test_hingemax_theta_property_is_consistent(clean_hingemax_data):
    """Verify theta = arctan(m1) - arctan(m2) for fitted params."""
    x, y, w, true_params, derived = clean_hingemax_data

    obj = HingeMax(x, y, guess_h=true_params["h"])
    obj.make_fit()

    m1 = obj.popt["m1"]
    m2 = obj.m2
    theta_expected = np.arctan(m1) - np.arctan(m2)

    np.testing.assert_allclose(
        obj.theta,
        theta_expected,
        rtol=1e-6,
        err_msg="HingeMax.theta should equal arctan(m1) - arctan(m2)",
    )


def test_hingemax_lines_intersect_at_hinge(clean_hingemax_data):
    """Verify both lines pass through (h, yh) where yh = m1*(h-x1)."""
    x, y, w, true_params, derived = clean_hingemax_data

    obj = HingeMax(x, y, guess_h=true_params["h"])
    obj.make_fit()

    h = obj.popt["h"]
    m1 = obj.popt["m1"]
    x1 = obj.popt["x1"]
    x2 = obj.popt["x2"]
    m2 = obj.m2

    yh_from_line1 = m1 * (h - x1)
    yh_from_line2 = m2 * (h - x2)

    np.testing.assert_allclose(
        yh_from_line1,
        yh_from_line2,
        rtol=1e-6,
        err_msg="Both lines should pass through hinge point",
    )


# -----------------------------------------------------------------------------
# HingeMax E5. Edge Cases and Interface Tests
# -----------------------------------------------------------------------------


def test_hingemax_function_signature():
    """Test that HingeMax function has correct parameter signature."""
    x = np.array([0.0, 5.0, 10.0])
    y = np.array([0.0, -10.0, 0.0])
    obj = HingeMax(x, y, guess_h=5.0)

    sig = inspect.signature(obj.function)
    params = tuple(sig.parameters.keys())

    assert params == (
        "x",
        "m1",
        "x1",
        "x2",
        "h",
    ), f"Function should have signature (x, m1, x1, x2, h), got {params}"


def test_hingemax_popt_has_correct_keys(clean_hingemax_data):
    """Test that HingeMax popt contains expected parameter names."""
    x, y, w, true_params, derived = clean_hingemax_data

    obj = HingeMax(x, y, guess_h=true_params["h"])
    obj.make_fit()

    expected_keys = {"m1", "x1", "x2", "h"}
    actual_keys = set(obj.popt.keys())

    assert (
        actual_keys == expected_keys
    ), f"popt keys should be {expected_keys}, got {actual_keys}"


def test_hingemax_callable_interface(clean_hingemax_data):
    """Test that fitted HingeMax object is callable and returns correct shape."""
    x, y, w, true_params, derived = clean_hingemax_data

    obj = HingeMax(x, y, guess_h=true_params["h"])
    obj.make_fit()

    x_test = np.array([1.0, 5.0, 9.0])
    y_pred = obj(x_test)

    assert (
        y_pred.shape == x_test.shape
    ), f"Predicted shape {y_pred.shape} should match input shape {x_test.shape}"
    assert np.all(np.isfinite(y_pred)), "All predicted values should be finite"


def test_hingemax_insufficient_data_raises_error():
    """Fitting HingeMax with insufficient data should raise InsufficientDataError."""
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([-2.0, -4.0, -3.0])

    obj = HingeMax(x, y, guess_h=2.0)

    with pytest.raises(InsufficientDataError):
        obj.make_fit()


# =============================================================================
# HingeAtPoint Tests
# =============================================================================
# HingeAtPoint: f(x) = np.minimum(y1, y2) where lines pass through (xh, yh)
# Parameters: xh, yh, m1, m2
# x1 = xh - yh/m1, x2 = xh - yh/m2
# Derived: x_intercepts (namedtuple with x1, x2)
# =============================================================================


# -----------------------------------------------------------------------------
# HingeAtPoint Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def clean_hingeatpoint_data():
    """Perfect HingeAtPoint data with lines meeting at (xh, yh).

    Parameters: xh=5, yh=10, m1=2, m2=-1
    x1 = 5 - 10/2 = 0
    x2 = 5 - 10/(-1) = 15
    Line1: y = 2*(x - 0) = 2x
    Line2: y = -1*(x - 15) = -x + 15
    """
    true_params = {"xh": 5.0, "yh": 10.0, "m1": 2.0, "m2": -1.0}
    x1 = true_params["xh"] - true_params["yh"] / true_params["m1"]
    x2 = true_params["xh"] - true_params["yh"] / true_params["m2"]

    x = np.linspace(-2, 20, 300)
    y1 = true_params["m1"] * (x - x1)
    y2 = true_params["m2"] * (x - x2)
    y = np.minimum(y1, y2)
    w = np.ones_like(x)
    return x, y, w, true_params, {"x1": x1, "x2": x2}


@pytest.fixture
def noisy_hingeatpoint_data():
    """HingeAtPoint data with 5% Gaussian noise.

    Parameters: xh=5, yh=10, m1=2, m2=-1
    """
    rng = np.random.default_rng(42)
    true_params = {"xh": 5.0, "yh": 10.0, "m1": 2.0, "m2": -1.0}
    x1 = true_params["xh"] - true_params["yh"] / true_params["m1"]
    x2 = true_params["xh"] - true_params["yh"] / true_params["m2"]

    x = np.linspace(-2, 20, 300)
    y1 = true_params["m1"] * (x - x1)
    y2 = true_params["m2"] * (x - x2)
    y_true = np.minimum(y1, y2)
    noise_std = 0.5
    y = y_true + rng.normal(0, noise_std, len(x))
    w = np.ones_like(x) / noise_std
    return x, y, w, true_params


@pytest.fixture
def hingeatpoint_positive_slopes_data():
    """HingeAtPoint where both slopes are positive.

    Parameters: xh=5, yh=10, m1=3, m2=0.5
    x1 = 5 - 10/3 = 1.667
    x2 = 5 - 10/0.5 = -15
    """
    true_params = {"xh": 5.0, "yh": 10.0, "m1": 3.0, "m2": 0.5}
    x1 = true_params["xh"] - true_params["yh"] / true_params["m1"]
    x2 = true_params["xh"] - true_params["yh"] / true_params["m2"]

    x = np.linspace(-5, 15, 300)
    y1 = true_params["m1"] * (x - x1)
    y2 = true_params["m2"] * (x - x2)
    y = np.minimum(y1, y2)
    w = np.ones_like(x)
    return x, y, w, true_params


# -----------------------------------------------------------------------------
# HingeAtPoint E1. Function Evaluation Tests
# -----------------------------------------------------------------------------


def test_hingeatpoint_func_evaluates_line1_region_correctly():
    """HingeAtPoint should follow line1 where m1*(x-x1) < m2*(x-x2).

    With xh=5, yh=10, m1=2, m2=-1: x1=0, x2=15
    For x<5: 2x < -x+15, so line1 dominates minimum.
    """
    xh, yh, m1, m2 = 5.0, 10.0, 2.0, -1.0
    x1 = xh - yh / m1  # = 0
    x2 = xh - yh / m2  # = 15

    x_test = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    expected = m1 * (x_test - x1)  # [0, 2, 4, 6, 8]

    x_dummy = np.linspace(0, 15, 50)
    y_dummy = np.minimum(m1 * x_dummy, m2 * (x_dummy - x2))
    obj = HingeAtPoint(x_dummy, y_dummy, guess_xh=xh, guess_yh=yh)
    result = obj.function(x_test, xh, yh, m1, m2)

    np.testing.assert_allclose(
        result,
        expected,
        rtol=1e-10,
        err_msg="HingeAtPoint should follow line1 in left region",
    )


def test_hingeatpoint_func_passes_through_hinge_point():
    """HingeAtPoint should pass through (xh, yh).

    At x=xh: f(xh) = yh
    """
    xh, yh, m1, m2 = 5.0, 10.0, 2.0, -1.0

    x_test = np.array([xh])
    expected = np.array([yh])

    x_dummy = np.linspace(0, 15, 50)
    y_dummy = np.minimum(m1 * x_dummy, m2 * (x_dummy - 15))
    obj = HingeAtPoint(x_dummy, y_dummy, guess_xh=xh, guess_yh=yh)
    result = obj.function(x_test, xh, yh, m1, m2)

    np.testing.assert_allclose(
        result,
        expected,
        rtol=1e-10,
        err_msg="HingeAtPoint should pass through (xh, yh)",
    )


def test_hingeatpoint_func_evaluates_line2_region_correctly():
    """HingeAtPoint should follow line2 where m2*(x-x2) < m1*(x-x1).

    For x>5: -x+15 < 2x
    """
    xh, yh, m1, m2 = 5.0, 10.0, 2.0, -1.0
    x1 = xh - yh / m1  # = 0
    x2 = xh - yh / m2  # = 15

    x_test = np.array([6.0, 8.0, 10.0, 12.0, 15.0])
    expected = m2 * (x_test - x2)  # [-1*(x-15)] = [9, 7, 5, 3, 0]

    x_dummy = np.linspace(0, 15, 50)
    y_dummy = np.minimum(m1 * x_dummy, m2 * (x_dummy - x2))
    obj = HingeAtPoint(x_dummy, y_dummy, guess_xh=xh, guess_yh=yh)
    result = obj.function(x_test, xh, yh, m1, m2)

    np.testing.assert_allclose(
        result,
        expected,
        rtol=1e-10,
        err_msg="HingeAtPoint should follow line2 in right region",
    )


# -----------------------------------------------------------------------------
# HingeAtPoint E2. Parameter Recovery Tests (Clean Data)
# -----------------------------------------------------------------------------


def test_hingeatpoint_fit_recovers_exact_parameters_from_clean_data(
    clean_hingeatpoint_data,
):
    """Fitting noise-free HingeAtPoint data should recover parameters within 2%."""
    x, y, w, true_params, derived = clean_hingeatpoint_data

    obj = HingeAtPoint(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])
    obj.make_fit()

    for param, true_val in true_params.items():
        fitted_val = obj.popt[param]
        if abs(true_val) < 0.1:
            assert (
                abs(fitted_val - true_val) < 0.05
            ), f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}"
        else:
            rel_error = abs(fitted_val - true_val) / abs(true_val)
            assert rel_error < 0.02, (
                f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                f"rel_error={rel_error:.2%} exceeds 2% tolerance"
            )


def test_hingeatpoint_fit_recovers_positive_slopes_parameters(
    hingeatpoint_positive_slopes_data,
):
    """Fitting HingeAtPoint with positive slopes should recover parameters within 2%."""
    x, y, w, true_params = hingeatpoint_positive_slopes_data

    obj = HingeAtPoint(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])
    obj.make_fit()

    for param, true_val in true_params.items():
        fitted_val = obj.popt[param]
        if abs(true_val) < 0.1:
            assert (
                abs(fitted_val - true_val) < 0.1
            ), f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}"
        else:
            rel_error = abs(fitted_val - true_val) / abs(true_val)
            assert rel_error < 0.02, (
                f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}, "
                f"rel_error={rel_error:.2%}"
            )


# -----------------------------------------------------------------------------
# HingeAtPoint E3. Noisy Data Tests
# -----------------------------------------------------------------------------


def test_hingeatpoint_fit_with_noise_recovers_parameters_within_2sigma(
    noisy_hingeatpoint_data,
):
    """Fitted HingeAtPoint parameters should be within 2sigma of true values."""
    x, y, w, true_params = noisy_hingeatpoint_data

    obj = HingeAtPoint(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])
    obj.make_fit()

    for param, true_val in true_params.items():
        fitted_val = obj.popt[param]
        sigma = obj.psigma[param]
        deviation = abs(fitted_val - true_val)

        assert deviation < 2 * sigma, (
            f"{param}: |fitted({fitted_val:.4f}) - true({true_val:.4f})| = "
            f"{deviation:.4f} exceeds 2sigma = {2*sigma:.4f}"
        )


# -----------------------------------------------------------------------------
# HingeAtPoint E4. Derived Property Tests
# -----------------------------------------------------------------------------


def test_hingeatpoint_x_intercepts_property_has_correct_values(clean_hingeatpoint_data):
    """Verify x_intercepts.x1 = xh - yh/m1 and x_intercepts.x2 = xh - yh/m2.

    True: x1 = 5 - 10/2 = 0, x2 = 5 - 10/(-1) = 15
    """
    x, y, w, true_params, derived = clean_hingeatpoint_data

    obj = HingeAtPoint(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])
    obj.make_fit()

    xh = obj.popt["xh"]
    yh = obj.popt["yh"]
    m1 = obj.popt["m1"]
    m2 = obj.popt["m2"]

    x1_expected = xh - yh / m1
    x2_expected = xh - yh / m2

    np.testing.assert_allclose(
        obj.x_intercepts.x1,
        x1_expected,
        rtol=1e-6,
        err_msg="x_intercepts.x1 should equal xh - yh/m1",
    )
    np.testing.assert_allclose(
        obj.x_intercepts.x2,
        x2_expected,
        rtol=1e-6,
        err_msg="x_intercepts.x2 should equal xh - yh/m2",
    )


def test_hingeatpoint_x_intercepts_is_namedtuple(clean_hingeatpoint_data):
    """Verify x_intercepts is a namedtuple with x1 and x2 attributes."""
    x, y, w, true_params, derived = clean_hingeatpoint_data

    obj = HingeAtPoint(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])
    obj.make_fit()

    assert hasattr(obj.x_intercepts, "x1"), "x_intercepts should have x1 attribute"
    assert hasattr(obj.x_intercepts, "x2"), "x_intercepts should have x2 attribute"


def test_hingeatpoint_lines_pass_through_hinge(clean_hingeatpoint_data):
    """Verify both lines pass through (xh, yh)."""
    x, y, w, true_params, derived = clean_hingeatpoint_data

    obj = HingeAtPoint(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])
    obj.make_fit()

    xh = obj.popt["xh"]
    yh = obj.popt["yh"]
    m1 = obj.popt["m1"]
    m2 = obj.popt["m2"]
    x1 = obj.x_intercepts.x1
    x2 = obj.x_intercepts.x2

    yh_from_line1 = m1 * (xh - x1)
    yh_from_line2 = m2 * (xh - x2)

    np.testing.assert_allclose(
        yh_from_line1,
        yh,
        rtol=1e-6,
        err_msg="Line1 should pass through (xh, yh)",
    )
    np.testing.assert_allclose(
        yh_from_line2,
        yh,
        rtol=1e-6,
        err_msg="Line2 should pass through (xh, yh)",
    )


# -----------------------------------------------------------------------------
# HingeAtPoint E5. Edge Cases and Interface Tests
# -----------------------------------------------------------------------------


def test_hingeatpoint_function_signature():
    """Test that HingeAtPoint function has correct parameter signature."""
    x = np.array([0.0, 5.0, 10.0])
    y = np.array([0.0, 10.0, 5.0])
    obj = HingeAtPoint(x, y, guess_xh=5.0, guess_yh=10.0)

    sig = inspect.signature(obj.function)
    params = tuple(sig.parameters.keys())

    assert params == (
        "x",
        "xh",
        "yh",
        "m1",
        "m2",
    ), f"Function should have signature (x, xh, yh, m1, m2), got {params}"


def test_hingeatpoint_popt_has_correct_keys(clean_hingeatpoint_data):
    """Test that HingeAtPoint popt contains expected parameter names."""
    x, y, w, true_params, derived = clean_hingeatpoint_data

    obj = HingeAtPoint(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])
    obj.make_fit()

    expected_keys = {"xh", "yh", "m1", "m2"}
    actual_keys = set(obj.popt.keys())

    assert (
        actual_keys == expected_keys
    ), f"popt keys should be {expected_keys}, got {actual_keys}"


def test_hingeatpoint_callable_interface(clean_hingeatpoint_data):
    """Test that fitted HingeAtPoint object is callable and returns correct shape."""
    x, y, w, true_params, derived = clean_hingeatpoint_data

    obj = HingeAtPoint(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])
    obj.make_fit()

    x_test = np.array([1.0, 5.0, 10.0])
    y_pred = obj(x_test)

    assert (
        y_pred.shape == x_test.shape
    ), f"Predicted shape {y_pred.shape} should match input shape {x_test.shape}"
    assert np.all(np.isfinite(y_pred)), "All predicted values should be finite"


def test_hingeatpoint_insufficient_data_raises_error():
    """Fitting HingeAtPoint with insufficient data should raise InsufficientDataError."""
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([2.0, 4.0, 3.0])

    obj = HingeAtPoint(x, y, guess_xh=2.0, guess_yh=4.0)

    with pytest.raises(InsufficientDataError):
        obj.make_fit()


def test_hingeatpoint_psigma_values_are_positive(noisy_hingeatpoint_data):
    """Test that all parameter uncertainties are positive."""
    x, y, w, true_params = noisy_hingeatpoint_data

    obj = HingeAtPoint(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])
    obj.make_fit()

    for param, sigma in obj.psigma.items():
        assert sigma > 0, f"psigma['{param}'] = {sigma} should be positive"
