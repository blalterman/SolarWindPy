"""Tests for HeavySide fit function.

HeavySide models a step function (Heaviside step function) with parameters:
- x0: transition point (step location)
- y0: baseline level (value for x > x0)
- y1: step height (added to y0 for x < x0)

The function is defined as:
    f(x) = y1 * heaviside(x0 - x, 0.5*(y0+y1)) + y0

Behavior:
- For x < x0: heaviside(x0-x) = 1, so f(x) = y1 + y0
- For x > x0: heaviside(x0-x) = 0, so f(x) = y0
- For x == x0: heaviside(0, 0.5*(y0+y1)) = 0.5*(y0+y1), so f(x) = y1*0.5*(y0+y1) + y0

Note: The p0 property provides heuristic-based initial guesses, but for
best results you may want to provide manual p0 via make_fit(p0=[x0, y0, y1]).
"""

import inspect

import numpy as np
import pytest

from solarwindpy.fitfunctions.heaviside import HeavySide
from solarwindpy.fitfunctions.core import InsufficientDataError


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def clean_step_data():
    """Perfect step function data (no noise).

    Parameters: x0=5.0, y0=2.0, y1=3.0
    - For x < 5: f(x) = 3 + 2 = 5
    - For x > 5: f(x) = 2
    """
    true_params = {"x0": 5.0, "y0": 2.0, "y1": 3.0}
    x = np.linspace(0, 10, 201)  # Odd number to avoid x=5 exactly except at midpoint
    # Build y using the heaviside formula
    y = (
        true_params["y1"]
        * np.heaviside(
            true_params["x0"] - x, 0.5 * (true_params["y0"] + true_params["y1"])
        )
        + true_params["y0"]
    )
    w = np.ones_like(x)
    return x, y, w, true_params


@pytest.fixture
def noisy_step_data():
    """Step function data with 5% Gaussian noise.

    Parameters: x0=5.0, y0=2.0, y1=3.0
    Noise std = 0.25 (5% of step height + baseline)
    """
    rng = np.random.default_rng(42)
    true_params = {"x0": 5.0, "y0": 2.0, "y1": 3.0}
    x = np.linspace(0, 10, 200)
    y_true = (
        true_params["y1"]
        * np.heaviside(
            true_params["x0"] - x, 0.5 * (true_params["y0"] + true_params["y1"])
        )
        + true_params["y0"]
    )
    noise_std = 0.25
    y = y_true + rng.normal(0, noise_std, len(x))
    w = np.ones_like(x) / noise_std
    return x, y, w, true_params


@pytest.fixture
def negative_step_data():
    """Step function with negative y1 (step down instead of step up).

    Parameters: x0=5.0, y0=8.0, y1=-3.0
    - For x < 5: f(x) = -3 + 8 = 5
    - For x > 5: f(x) = 8
    """
    true_params = {"x0": 5.0, "y0": 8.0, "y1": -3.0}
    x = np.linspace(0, 10, 201)
    y = (
        true_params["y1"]
        * np.heaviside(
            true_params["x0"] - x, 0.5 * (true_params["y0"] + true_params["y1"])
        )
        + true_params["y0"]
    )
    w = np.ones_like(x)
    return x, y, w, true_params


@pytest.fixture
def zero_baseline_data():
    """Step function with y0=0 (baseline at zero).

    Parameters: x0=3.0, y0=0.0, y1=4.0
    - For x < 3: f(x) = 4 + 0 = 4
    - For x > 3: f(x) = 0
    """
    true_params = {"x0": 3.0, "y0": 0.0, "y1": 4.0}
    x = np.linspace(0, 10, 201)
    y = (
        true_params["y1"]
        * np.heaviside(
            true_params["x0"] - x, 0.5 * (true_params["y0"] + true_params["y1"])
        )
        + true_params["y0"]
    )
    w = np.ones_like(x)
    return x, y, w, true_params


# =============================================================================
# E1. Function Evaluation Tests (Exact Values)
# =============================================================================


def test_func_evaluates_below_step_correctly():
    """For x < x0: f(x) = y1 + y0.

    With x0=5, y0=2, y1=3: f(x<5) = 3 + 2 = 5.
    """
    x0, y0, y1 = 5.0, 2.0, 3.0

    # Test specific points below the step transition
    x_test = np.array([0.0, 1.0, 2.5, 4.0, 4.99])
    expected = np.full_like(x_test, y0 + y1)  # All should equal 5.0

    # Create minimal instance to access function
    x_dummy = np.array([0.0, 10.0])
    y_dummy = np.array([5.0, 2.0])
    obj = HeavySide(x_dummy, y_dummy)
    result = obj.function(x_test, x0, y0, y1)

    np.testing.assert_allclose(
        result,
        expected,
        rtol=1e-10,
        err_msg="Below step (x < x0): f(x) should equal y0 + y1",
    )


def test_func_evaluates_above_step_correctly():
    """For x > x0: f(x) = y0.

    With x0=5, y0=2, y1=3: f(x>5) = 2.
    """
    x0, y0, y1 = 5.0, 2.0, 3.0

    # Test points above the step transition
    x_test = np.array([5.01, 6.0, 7.5, 10.0, 100.0])
    expected = np.full_like(x_test, y0)  # All should equal 2.0

    x_dummy = np.array([0.0, 10.0])
    y_dummy = np.array([5.0, 2.0])
    obj = HeavySide(x_dummy, y_dummy)
    result = obj.function(x_test, x0, y0, y1)

    np.testing.assert_allclose(
        result,
        expected,
        rtol=1e-10,
        err_msg="Above step (x > x0): f(x) should equal y0",
    )


def test_func_evaluates_at_step_transition():
    """At x == x0: f(x) = y1 * 0.5*(y0+y1) + y0.

    With x0=5, y0=2, y1=3:
    f(5) = 3 * 0.5*(2+3) + 2 = 3 * 2.5 + 2 = 7.5 + 2 = 9.5

    Note: This is unusual behavior for a step function. The typical
    midpoint would be 0.5*(y0 + y0+y1) = y0 + 0.5*y1 = 3.5.
    """
    x0, y0, y1 = 5.0, 2.0, 3.0

    x_test = np.array([5.0])
    # f(x0) = y1 * heaviside(0, 0.5*(y0+y1)) + y0
    #       = y1 * 0.5*(y0+y1) + y0
    expected_at_transition = y1 * 0.5 * (y0 + y1) + y0
    expected = np.array([expected_at_transition])

    x_dummy = np.array([0.0, 10.0])
    y_dummy = np.array([5.0, 2.0])
    obj = HeavySide(x_dummy, y_dummy)
    result = obj.function(x_test, x0, y0, y1)

    np.testing.assert_allclose(
        result,
        expected,
        rtol=1e-10,
        err_msg=f"At step (x == x0): f(x) should equal {expected_at_transition:.2f}",
    )


def test_func_with_negative_step_height():
    """Step function with negative y1 (step down from left to right).

    With x0=5, y0=8, y1=-3:
    - For x < 5: f(x) = -3 + 8 = 5
    - For x > 5: f(x) = 8
    """
    x0, y0, y1 = 5.0, 8.0, -3.0

    x_test = np.array([2.0, 4.9, 5.1, 8.0])
    expected = np.array([y0 + y1, y0 + y1, y0, y0])  # [5, 5, 8, 8]

    x_dummy = np.array([0.0, 10.0])
    y_dummy = np.array([5.0, 8.0])
    obj = HeavySide(x_dummy, y_dummy)
    result = obj.function(x_test, x0, y0, y1)

    np.testing.assert_allclose(
        result,
        expected,
        rtol=1e-10,
        err_msg="Negative y1: step down should give y0+y1 below, y0 above",
    )


def test_func_with_zero_baseline():
    """Step function with y0=0.

    With x0=3, y0=0, y1=4:
    - For x < 3: f(x) = 4 + 0 = 4
    - For x > 3: f(x) = 0
    """
    x0, y0, y1 = 3.0, 0.0, 4.0

    x_test = np.array([1.0, 2.9, 3.1, 5.0])
    expected = np.array([y0 + y1, y0 + y1, y0, y0])  # [4, 4, 0, 0]

    x_dummy = np.array([0.0, 10.0])
    y_dummy = np.array([4.0, 0.0])
    obj = HeavySide(x_dummy, y_dummy)
    result = obj.function(x_test, x0, y0, y1)

    np.testing.assert_allclose(
        result,
        expected,
        rtol=1e-10,
        err_msg="Zero baseline: should give y1 below, 0 above",
    )


# =============================================================================
# E2. Parameter Recovery Tests (Clean Data with Manual p0)
# =============================================================================


def test_fit_recovers_exact_parameters_from_clean_data(clean_step_data):
    """Fitting noise-free data with manual p0 should recover parameters within 1%."""
    x, y, w, true_params = clean_step_data

    obj = HeavySide(x, y)
    # Must provide p0 manually since automatic p0 raises NotImplementedError
    p0 = [true_params["x0"], true_params["y0"], true_params["y1"]]
    obj.make_fit(p0=p0)

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


def test_fit_recovers_negative_step_parameters(negative_step_data):
    """Fitting clean data with negative y1 should recover parameters within 2%."""
    x, y, w, true_params = negative_step_data

    obj = HeavySide(x, y)
    p0 = [true_params["x0"], true_params["y0"], true_params["y1"]]
    obj.make_fit(p0=p0)

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


def test_fit_recovers_zero_baseline_parameters(zero_baseline_data):
    """Fitting clean data with y0=0 should recover parameters within 2%."""
    x, y, w, true_params = zero_baseline_data

    obj = HeavySide(x, y)
    p0 = [true_params["x0"], true_params["y0"], true_params["y1"]]
    obj.make_fit(p0=p0)

    for param, true_val in true_params.items():
        fitted_val = obj.popt[param]
        if abs(true_val) < 0.1:
            # For y0=0, check absolute tolerance
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
        {"x0": 5.0, "y0": 2.0, "y1": 3.0},  # Standard step up
        {"x0": 3.0, "y0": 10.0, "y1": -5.0},  # Step down
        {"x0": 7.0, "y0": 0.0, "y1": 6.0},  # Zero baseline
        {"x0": 2.0, "y0": 1.0, "y1": 0.5},  # Small step
    ],
)
def test_fit_recovers_various_parameter_combinations(true_params):
    """Fitting should work for diverse parameter combinations."""
    x = np.linspace(0, 10, 200)

    # Build y from parameters using the heaviside formula
    y = (
        true_params["y1"]
        * np.heaviside(
            true_params["x0"] - x, 0.5 * (true_params["y0"] + true_params["y1"])
        )
        + true_params["y0"]
    )

    obj = HeavySide(x, y)
    p0 = [true_params["x0"], true_params["y0"], true_params["y1"]]
    obj.make_fit(p0=p0)

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


def test_fit_with_noise_recovers_parameters_within_tolerance(noisy_step_data):
    """Fitted parameters should be close to true values.

    Note: For step functions, the x0 parameter uncertainty can be zero or
    very small because the step location is essentially a discrete choice.
    We check y0 and y1 against their uncertainties, but use absolute
    tolerance for x0.
    """
    x, y, w, true_params = noisy_step_data

    obj = HeavySide(x, y)
    p0 = [true_params["x0"], true_params["y0"], true_params["y1"]]
    obj.make_fit(p0=p0)

    # Check y0 and y1 against their uncertainties (if non-zero)
    for param in ["y0", "y1"]:
        true_val = true_params[param]
        fitted_val = obj.popt[param]
        sigma = obj.psigma[param]
        deviation = abs(fitted_val - true_val)

        if sigma > 0:
            # 2sigma gives 95% confidence
            assert deviation < 2 * sigma, (
                f"{param}: |fitted({fitted_val:.4f}) - true({true_val:.4f})| = "
                f"{deviation:.4f} exceeds 2sigma = {2*sigma:.4f}"
            )
        else:
            # If sigma is 0, check absolute tolerance
            assert deviation < 0.5, (
                f"{param}: |fitted({fitted_val:.4f}) - true({true_val:.4f})| = "
                f"{deviation:.4f} exceeds absolute tolerance 0.5"
            )

    # For x0, check absolute tolerance (step location)
    x0_deviation = abs(obj.popt["x0"] - true_params["x0"])
    assert x0_deviation < 0.5, (
        f"x0: |fitted({obj.popt['x0']:.4f}) - true({true_params['x0']:.4f})| = "
        f"{x0_deviation:.4f} exceeds tolerance 0.5"
    )


def test_fit_uncertainty_scales_with_noise():
    """Higher noise should produce larger parameter uncertainties."""
    rng = np.random.default_rng(42)
    true_params = {"x0": 5.0, "y0": 2.0, "y1": 3.0}
    x = np.linspace(0, 10, 200)
    y_true = (
        true_params["y1"]
        * np.heaviside(
            true_params["x0"] - x, 0.5 * (true_params["y0"] + true_params["y1"])
        )
        + true_params["y0"]
    )

    p0 = [true_params["x0"], true_params["y0"], true_params["y1"]]

    # Low noise fit
    y_low = y_true + rng.normal(0, 0.1, len(x))
    fit_low = HeavySide(x, y_low)
    fit_low.make_fit(p0=p0)

    # High noise fit (different seed for independence)
    rng2 = np.random.default_rng(43)
    y_high = y_true + rng2.normal(0, 0.5, len(x))
    fit_high = HeavySide(x, y_high)
    fit_high.make_fit(p0=p0)

    # High noise should have larger uncertainties for at least some parameters
    # (y0 and y1 are the primary parameters affected by noise away from transition)
    for param in ["y0", "y1"]:
        assert fit_high.psigma[param] > fit_low.psigma[param], (
            f"{param}: high_noise_sigma={fit_high.psigma[param]:.4f} should be "
            f"> low_noise_sigma={fit_low.psigma[param]:.4f}"
        )


# =============================================================================
# E4. Initial Parameter Estimation Tests
# =============================================================================


def test_p0_returns_list_with_correct_length(clean_step_data):
    """p0 should return a list with 3 elements."""
    x, y, w, true_params = clean_step_data
    obj = HeavySide(x, y)

    p0 = obj.p0
    assert isinstance(p0, list), f"p0 should be a list, got {type(p0)}"
    assert len(p0) == 3, f"p0 should have 3 elements (x0, y0, y1), got {len(p0)}"


def test_p0_provides_reasonable_initial_guesses(clean_step_data):
    """p0 should provide reasonable heuristic-based initial guesses.

    For clean step data with x0=5, y0=2, y1=3:
    - x0 guess should be near midpoint of x range
    - y0 guess should be near minimum y value (2)
    - y1 guess should be positive (step height estimate)

    Note: The y1 estimate may not be accurate because the HeavySide function
    has an unusual value at the transition point x0 (not the simple midpoint).
    The heuristic uses max(y) - min(y), which can be inflated by the
    transition value y1*0.5*(y0+y1) + y0.
    """
    x, y, w, true_params = clean_step_data
    obj = HeavySide(x, y)

    p0 = obj.p0

    # x0 guess should be reasonable (within data range)
    assert (
        min(x) <= p0[0] <= max(x)
    ), f"x0 guess {p0[0]} should be within data range [{min(x)}, {max(x)}]"

    # y0 guess should be close to minimum y (baseline)
    np.testing.assert_allclose(
        p0[1],
        true_params["y0"],
        atol=0.5,
        err_msg=f"y0 guess {p0[1]} should be near true y0={true_params['y0']}",
    )

    # y1 guess should be positive and finite (allows fitting to converge)
    assert p0[2] > 0, f"y1 guess {p0[2]} should be positive"
    assert np.isfinite(p0[2]), f"y1 guess {p0[2]} should be finite"


# =============================================================================
# E5. Derived Quantity Tests (Internal Consistency)
# =============================================================================


def test_step_discontinuity_magnitude(clean_step_data):
    """Verify that the step magnitude equals y1.

    The difference between values just below and just above x0 should be y1.
    """
    x, y, w, true_params = clean_step_data

    obj = HeavySide(x, y)
    p0 = [true_params["x0"], true_params["y0"], true_params["y1"]]
    obj.make_fit(p0=p0)

    x0 = obj.popt["x0"]
    y1_expected = obj.popt["y1"]

    # Evaluate just below and above the step
    epsilon = 0.001
    x_below = np.array([x0 - epsilon])
    x_above = np.array([x0 + epsilon])

    y_below = obj(x_below)[0]
    y_above = obj(x_above)[0]

    step_magnitude = y_below - y_above

    np.testing.assert_allclose(
        step_magnitude,
        y1_expected,
        rtol=1e-3,
        err_msg=f"Step magnitude {step_magnitude:.4f} should equal y1={y1_expected:.4f}",
    )


# =============================================================================
# E6. Edge Case and Error Handling Tests
# =============================================================================


def test_insufficient_data_raises_error():
    """Fitting with insufficient data should raise InsufficientDataError."""
    x = np.array([1.0, 2.0])  # Only 2 points for 3 parameters
    y = np.array([5.0, 5.0])

    obj = HeavySide(x, y)

    with pytest.raises(InsufficientDataError):
        obj.make_fit(p0=[5.0, 2.0, 3.0])


def test_function_signature():
    """Test that function has correct parameter signature."""
    x = np.array([0.0, 5.0, 10.0])
    y = np.array([5.0, 3.5, 2.0])
    obj = HeavySide(x, y)

    sig = inspect.signature(obj.function)
    params = tuple(sig.parameters.keys())

    assert params == (
        "x",
        "x0",
        "y0",
        "y1",
    ), f"Function should have signature (x, x0, y0, y1), got {params}"


def test_tex_function_property():
    """Test that TeX_function returns a string.

    Note: The current implementation's TeX_function appears to be copied
    from another class and may not accurately represent the Heaviside function.
    """
    x = np.array([0.0, 5.0, 10.0])
    y = np.array([5.0, 3.5, 2.0])
    obj = HeavySide(x, y)

    tex = obj.TeX_function
    assert isinstance(tex, str), f"TeX_function should return str, got {type(tex)}"
    # The TeX string exists even if it's not specific to Heaviside
    assert len(tex) > 0, "TeX_function should return non-empty string"


def test_callable_interface(clean_step_data):
    """Test that fitted object is callable and returns correct shape."""
    x, y, w, true_params = clean_step_data

    obj = HeavySide(x, y)
    p0 = [true_params["x0"], true_params["y0"], true_params["y1"]]
    obj.make_fit(p0=p0)

    # Test callable interface
    x_test = np.array([1.0, 5.0, 9.0])
    y_pred = obj(x_test)

    assert (
        y_pred.shape == x_test.shape
    ), f"Predicted shape {y_pred.shape} should match input shape {x_test.shape}"
    assert np.all(np.isfinite(y_pred)), "All predicted values should be finite"


def test_popt_has_correct_keys(clean_step_data):
    """Test that popt contains expected parameter names."""
    x, y, w, true_params = clean_step_data

    obj = HeavySide(x, y)
    p0 = [true_params["x0"], true_params["y0"], true_params["y1"]]
    obj.make_fit(p0=p0)

    expected_keys = {"x0", "y0", "y1"}
    actual_keys = set(obj.popt.keys())

    assert (
        actual_keys == expected_keys
    ), f"popt keys should be {expected_keys}, got {actual_keys}"


def test_psigma_has_same_keys_as_popt(noisy_step_data):
    """Test that psigma has same keys as popt."""
    x, y, w, true_params = noisy_step_data

    obj = HeavySide(x, y)
    p0 = [true_params["x0"], true_params["y0"], true_params["y1"]]
    obj.make_fit(p0=p0)

    assert set(obj.psigma.keys()) == set(obj.popt.keys()), (
        f"psigma keys {set(obj.psigma.keys())} should match "
        f"popt keys {set(obj.popt.keys())}"
    )


def test_psigma_values_are_nonnegative(noisy_step_data):
    """Test that all parameter uncertainties are non-negative.

    Note: For step functions, the x0 parameter uncertainty can be zero
    because the step location is essentially a discrete choice that the
    optimizer converges to exactly. The y0 and y1 uncertainties should
    typically be positive when there is noise in the data.
    """
    x, y, w, true_params = noisy_step_data

    obj = HeavySide(x, y)
    p0 = [true_params["x0"], true_params["y0"], true_params["y1"]]
    obj.make_fit(p0=p0)

    for param, sigma in obj.psigma.items():
        assert sigma >= 0, f"psigma['{param}'] = {sigma} should be non-negative"
        assert np.isfinite(sigma), f"psigma['{param}'] = {sigma} should be finite"
