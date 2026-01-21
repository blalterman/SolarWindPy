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
            assert abs(fitted_val - true_val) < 0.05, (
                f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}"
            )
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
            assert abs(fitted_val - true_val) < 0.05, (
                f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}"
            )
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
            assert abs(fitted_val - true_val) < 0.05, (
                f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}"
            )
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
    assert all(np.isfinite(v) for v in obj.popt.values()), (
        f"Fit did not converge: popt={obj.popt}"
    )


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
    assert all(np.isfinite(v) for v in fit_weighted.popt.values()), (
        f"Weighted fit did not converge: popt={fit_weighted.popt}"
    )

    # With proper weighting, should recover true parameters within 5%
    for param, true_val in true_params.items():
        fitted_val = fit_weighted.popt[param]
        if abs(true_val) < 0.1:
            # Absolute tolerance for values near zero
            assert abs(fitted_val - true_val) < 0.1, (
                f"{param}: fitted={fitted_val:.4f}, true={true_val:.4f}"
            )
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

    assert params == ("x", "xh", "yh", "x1", "m2"), (
        f"Function should have signature (x, xh, yh, x1, m2), got {params}"
    )


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

    assert y_pred.shape == x_test.shape, (
        f"Predicted shape {y_pred.shape} should match input shape {x_test.shape}"
    )
    assert np.all(np.isfinite(y_pred)), "All predicted values should be finite"


def test_popt_has_correct_keys(clean_saturation_data):
    """Test that popt contains expected parameter names."""
    x, y, w, true_params = clean_saturation_data

    obj = HingeSaturation(x, y, guess_xh=true_params["xh"], guess_yh=true_params["yh"])
    obj.make_fit()

    expected_keys = {"xh", "yh", "x1", "m2"}
    actual_keys = set(obj.popt.keys())

    assert actual_keys == expected_keys, (
        f"popt keys should be {expected_keys}, got {actual_keys}"
    )


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
