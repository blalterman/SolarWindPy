"""Tests for power law fit functions."""

import inspect
import numpy as np
import pytest
from scipy.optimize import curve_fit

from solarwindpy.fitfunctions.power_laws import (
    PowerLaw,
    PowerLawPlusC,
    PowerLawOffCenter,
)
from solarwindpy.fitfunctions.core import InsufficientDataError

# Noise-free fits: rel=1e-6 is far above optimizer convergence, far below any real bug.
NOISE_FREE = dict(rel=1e-6, abs=0)
# Closed-form evaluation: only floating-point rounding separates the two sides.
EXACT = dict(rel=1e-12, abs=0)


@pytest.mark.parametrize(
    "cls, expected_params, sample_args, expected_value",
    [
        # 3 * 2^1.5 = 6 sqrt(2)
        (PowerLaw, ("x", "A", "b"), (2.0, 3.0, 1.5), 6 * np.sqrt(2.0)),
        # 6 sqrt(2) + 1
        (
            PowerLawPlusC,
            ("x", "A", "b", "c"),
            (2.0, 3.0, 1.5, 1.0),
            6 * np.sqrt(2.0) + 1,
        ),
        # 3 * 1.5^1.5 = 4.5 sqrt(1.5)
        (
            PowerLawOffCenter,
            ("x", "A", "b", "x0"),
            (2.0, 3.0, 1.5, 0.5),
            4.5 * np.sqrt(1.5),
        ),
    ],
)
def test_function_signature_and_output(
    cls, expected_params, sample_args, expected_value
):
    """The model takes ``(x, *params)`` in documented order and evaluates by hand.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([1.0, 4.0, 9.0])
    obj = cls(x, y)

    sig = inspect.signature(obj.function)
    assert tuple(sig.parameters.keys()) == expected_params

    assert obj.function(*sample_args) == pytest.approx(expected_value, **EXACT)


@pytest.fixture
def power_law_data():
    """Noisy y = 2 x^-1.5, x in [0.5, 5], noise sigma 0.02, unit weights.

    The smallest model value is 2 * 5^-1.5 = 0.179, nine noise sigmas above zero,
    so the data stay positive without clipping.
    """
    rng = np.random.default_rng(42)
    x = np.linspace(0.5, 5.0, 20)
    A, b = 2.0, -1.5
    noise = rng.normal(0, 0.02, size=x.shape)
    y = A * x**b + noise
    w = np.ones_like(x)
    return x, y, w


@pytest.mark.parametrize("cls", [PowerLaw, PowerLawPlusC, PowerLawOffCenter])
def test_p0_zero_size_input(cls):
    """Asking for an initial guess with no data raises InsufficientDataError.

    ON FAILURE: the code is wrong.
    """
    x = np.array([])
    y = np.array([])
    obj = cls(x, y)

    with pytest.raises(InsufficientDataError):
        _ = obj.p0


@pytest.mark.parametrize("cls", [PowerLaw, PowerLawPlusC, PowerLawOffCenter])
def test_power_law_p0_is_fixed(cls, power_law_data):
    """p0 has one finite guess per parameter and does not depend on the data.

    The module docstring promises initial guesses that are "fixed values, not
    estimated from the data".

    ON FAILURE: the code is wrong, unless the author now estimates p0 from data.
    """
    x, y, w = power_law_data
    p0 = cls(x, y).p0
    p0_other = cls(np.array([1.0, 10.0, 100.0]), np.array([7.0, -3.0, 50.0])).p0

    assert len(p0) == len(cls(x, y).argnames)
    assert np.all(np.isfinite(p0))
    assert p0 == p0_other


@pytest.mark.parametrize(
    "cls, expected_tex",
    [
        (PowerLaw, r"f(x)=A x^b"),
        (PowerLawPlusC, r"f(x)=A x^b + c"),
        (PowerLawOffCenter, r"f(x)=A (x-x_0)^b"),
    ],
)
def test_TeX_function_strings(cls, expected_tex):
    """Each class reports its documented LaTeX model string.

    ON FAILURE: the code is wrong, unless the author changed the TeX wording.
    """
    x = np.array([1.0, 2.0, 4.0])
    y = np.array([2.0, 1.0, 0.5])
    obj = cls(x, y)
    assert obj.TeX_function == expected_tex


@pytest.mark.parametrize(
    "cls, truth",
    [
        (PowerLaw, {"A": 2.0, "b": -1.5}),
        (PowerLawPlusC, {"A": 2.0, "b": -1.5, "c": 0.0}),
        (PowerLawOffCenter, {"A": 2.0, "b": -1.5, "x0": 0.0}),
    ],
)
def test_make_fit_success(cls, truth, power_law_data):
    """A fit to noisy 2 x^-1.5 recovers each parameter within 4 error bars.

    ON FAILURE: the code is wrong.
    """
    x, y, w = power_law_data
    obj = cls(x, y)
    obj.make_fit()

    assert set(obj.popt) == set(truth)
    for name, value in truth.items():
        # Fixed seed (default_rng(42)); 4 error bars per TEST_PATTERNS.
        assert abs(obj.popt[name] - value) < 4 * obj.psigma[name], name


@pytest.mark.parametrize("cls", [PowerLaw, PowerLawPlusC, PowerLawOffCenter])
def test_make_fit_insufficient_data(cls):
    """One point cannot fit a multi-parameter model: raise, or return the error.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0])
    y = np.array([1.0])
    obj = cls(x, y)

    with pytest.raises(InsufficientDataError):
        obj.make_fit()

    result = obj.make_fit(return_exception=True)
    assert isinstance(result, InsufficientDataError)
    assert "insufficient data" in str(result).lower()


def test_power_law_perfect_fit():
    """PowerLaw recovers A = 16, b = -2 from 16, 4, 1, 0.25 at x = 1, 2, 4, 8.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 2.0, 4.0, 8.0])
    A, b = 16.0, -2.0
    y = np.array([16.0, 4.0, 1.0, 0.25])

    obj = PowerLaw(x, y)
    obj.make_fit()

    assert obj.popt["A"] == pytest.approx(A, **NOISE_FREE)
    assert obj.popt["b"] == pytest.approx(b, **NOISE_FREE)
    assert obj(x) == pytest.approx(y, **NOISE_FREE)


def test_power_law_plus_c_perfect_fit():
    """PowerLawPlusC recovers A = 16, b = -2, c = 2 from 18, 6, 3, 2.25.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 2.0, 4.0, 8.0])
    A, b, c = 16.0, -2.0, 2.0
    y = np.array([18.0, 6.0, 3.0, 2.25])

    obj = PowerLawPlusC(x, y)
    obj.make_fit()

    assert obj.popt["A"] == pytest.approx(A, **NOISE_FREE)
    assert obj.popt["b"] == pytest.approx(b, **NOISE_FREE)
    assert obj.popt["c"] == pytest.approx(c, **NOISE_FREE)
    assert obj(x) == pytest.approx(y, **NOISE_FREE)


def test_power_law_off_center_perfect_fit():
    """PowerLawOffCenter recovers A = 4, b = 2, x0 = 1 from 4, 16, 64, 256.

    ON FAILURE: the code is wrong.
    """
    x = np.array([2.0, 3.0, 5.0, 9.0])
    A, b, x0 = 4.0, 2.0, 1.0
    y = np.array([4.0, 16.0, 64.0, 256.0])  # 4 * (1, 2, 4, 8)^2

    obj = PowerLawOffCenter(x, y)
    obj.make_fit()

    assert obj.popt["A"] == pytest.approx(A, **NOISE_FREE)
    assert obj.popt["b"] == pytest.approx(b, **NOISE_FREE)
    assert obj.popt["x0"] == pytest.approx(x0, **NOISE_FREE)
    assert obj(x) == pytest.approx(y, **NOISE_FREE)


def test_power_law_numerical_stability():
    """PowerLaw evaluates extreme exponents: 0.1^-10 = 1e10 and 10^0.1.

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.1, 1.0, 10.0])
    y = np.array([10.0, 1.0, 0.1])

    obj = PowerLaw(x, y)

    assert obj.function(0.1, 1.0, -10.0) == pytest.approx(1e10, **EXACT)
    # 10^0.1 = 1.2589254117941673 (tenth root of 10).
    assert obj.function(10.0, 1.0, 0.1) == pytest.approx(1.2589254117941673, **EXACT)


def test_power_law_zero_handling():
    """PowerLaw is x itself at b = 1 near zero, and the constant A at b = 0.

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.01, 1.0, 100.0])
    y = np.array([1.0, 1.0, 1.0])

    obj = PowerLaw(x, y)

    assert obj.function(0.01, 1.0, 1.0) == pytest.approx(0.01, **EXACT)
    assert obj.function(2.0, 5.0, 0.0) == pytest.approx(5.0, **EXACT)


def test_power_law_off_center_centering():
    """PowerLawOffCenter measures x from x0: 2 (x - 1.5) at x = 2..5 is 1, 3, 5, 7.

    ON FAILURE: the code is wrong.
    """
    x = np.array([2.0, 3.0, 4.0, 5.0])
    x0 = 1.5

    obj = PowerLawOffCenter(x, np.ones_like(x))

    result = obj.function(x, 2.0, 1.0, x0)
    assert result == pytest.approx([1.0, 3.0, 5.0, 7.0], **EXACT)


@pytest.mark.parametrize(
    "cls, offset",
    [
        (PowerLaw, 0.0),
        (PowerLawPlusC, 0.5),
        (PowerLawOffCenter, 0.0),
    ],
)
def test_str_and_call_methods(cls, offset):
    """``str`` names the class; calling a noise-free fit evaluates the true curve.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 2.0, 4.0, 8.0])
    obj = cls(x, 16.0 * x**-2.0 + offset)
    obj.make_fit()

    assert cls.__name__ in str(obj)

    # Points off the fitted grid: 16 / x^2 + offset.
    x_test = np.array([0.5, 3.0, 16.0])
    expected = np.array([64.0, 16.0 / 9.0, 0.0625]) + offset
    assert obj(x_test) == pytest.approx(expected, **NOISE_FREE)


def test_power_law_with_weights():
    """Weights are 1-sigma errors: the fit equals scipy's weighted ``curve_fit``.

    The perturbations are small enough (|r/sigma| <= 0.02) that the default
    Huber loss (f_scale=0.1) stays quadratic, so the minimizer is the weighted
    least-squares solution that ``scipy.optimize.curve_fit(sigma=...)`` finds.

    ON FAILURE: the code is wrong, unless the default loss no longer reduces
    to least squares for residuals below f_scale.
    """
    x = np.arange(1.0, 7.0, 0.5)
    y = 2.0 * x**-1.5 + 0.01 * np.array([1, -1] * 6)
    sigma = np.linspace(0.5, 2.0, 12)

    obj = PowerLaw(x, y, weights=sigma)
    obj.make_fit()

    def model(x, A, b):
        return A * x**b

    weighted, _ = curve_fit(model, x, y, p0=[1.0, 1.0], sigma=sigma)
    unweighted, _ = curve_fit(model, x, y, p0=[1.0, 1.0])
    # Weighted and unweighted differ by ~1e-3, far outside rel=1e-6, so ignoring
    # the weights fails the first assertion.
    assert [obj.popt["A"], obj.popt["b"]] == pytest.approx(weighted, **NOISE_FREE)
    assert list(weighted) != pytest.approx(unweighted, **NOISE_FREE)


def test_power_law_scaling_behavior():
    """A fit to 2/x scales by 2^b = 1/2 when x doubles.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 2.0, 4.0, 8.0])
    y = np.array([2.0, 1.0, 0.5, 0.25])  # 2 / x

    obj = PowerLaw(x, y)
    obj.make_fit()

    assert obj(4.0) / obj(2.0) == pytest.approx(0.5, **NOISE_FREE)


@pytest.mark.parametrize("cls", [PowerLaw, PowerLawPlusC, PowerLawOffCenter])
def test_property_access_before_fit(cls):
    """Fit results do not exist before ``make_fit``: popt and pcov raise.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([2.0, 1.0, 0.5])
    obj = cls(x, y)

    with pytest.raises(AttributeError):
        _ = obj.popt
    with pytest.raises(AttributeError):
        _ = obj.pcov


def test_power_law_negative_x_handling():
    """PowerLaw with an even exponent is real and symmetric for negative x.

    ON FAILURE: the code is wrong.
    """
    x = np.array([-2.0, -1.0, 1.0, 2.0])

    obj = PowerLaw(x, np.ones_like(x))

    assert obj.function(x, 1.0, 2.0) == pytest.approx([4.0, 1.0, 1.0, 4.0], **EXACT)


def test_power_law_integer_vs_float_exponents():
    """Integer and float exponents give 2 x^2 = 2, 8, 18 alike.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 2.0, 3.0])
    A = 2.0

    obj = PowerLaw(x, np.ones_like(x))

    assert obj.function(x, A, 2) == pytest.approx([2.0, 8.0, 18.0], **EXACT)
    assert obj.function(x, A, 2.0) == pytest.approx([2.0, 8.0, 18.0], **EXACT)


def test_power_law_edge_case_exponents():
    """b = 1, 0, -1 give a line, a constant, and an inverse.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 2.0, 4.0])
    obj = PowerLaw(x, np.ones_like(x))

    assert obj.function(x, 3.0, 1.0) == pytest.approx([3.0, 6.0, 12.0], **EXACT)
    assert obj.function(x, 5.0, 0.0) == pytest.approx([5.0, 5.0, 5.0], **EXACT)
    assert obj.function(x, 2.0, -1.0) == pytest.approx([2.0, 1.0, 0.5], **EXACT)
