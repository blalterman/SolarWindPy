"""Tests for power law fit functions."""

import inspect
import re
import warnings

import numpy as np
import pytest
from scipy.optimize import curve_fit

from solarwindpy.fitfunctions.power_laws import (
    PowerLaw,
    PowerLawPlusC,
    PowerLawOffCenter,
)
from solarwindpy.fitfunctions.core import InsufficientDataError
from tests.tolerances import NOISE_FREE_REL, exact, noise_free


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

    assert obj.function(*sample_args) == exact(expected_value)


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

    assert obj.popt["A"] == noise_free(A)
    assert obj.popt["b"] == noise_free(b)
    assert obj(x) == noise_free(y)


def test_power_law_plus_c_perfect_fit():
    """PowerLawPlusC recovers A = 16, b = -2, c = 2 from 18, 6, 3, 2.25.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 2.0, 4.0, 8.0])
    A, b, c = 16.0, -2.0, 2.0
    y = np.array([18.0, 6.0, 3.0, 2.25])

    obj = PowerLawPlusC(x, y)
    obj.make_fit()

    assert obj.popt["A"] == noise_free(A)
    assert obj.popt["b"] == noise_free(b)
    assert obj.popt["c"] == noise_free(c)
    assert obj(x) == noise_free(y)


def test_power_law_off_center_perfect_fit():
    """PowerLawOffCenter recovers A = 4, b = 2, x0 = 1 from 4, 16, 64, 256.

    ON FAILURE: the code is wrong.
    """
    x = np.array([2.0, 3.0, 5.0, 9.0])
    A, b, x0 = 4.0, 2.0, 1.0
    y = np.array([4.0, 16.0, 64.0, 256.0])  # 4 * (1, 2, 4, 8)^2

    obj = PowerLawOffCenter(x, y)
    obj.make_fit()

    assert obj.popt["A"] == noise_free(A)
    assert obj.popt["b"] == noise_free(b)
    assert obj.popt["x0"] == noise_free(x0)
    assert obj(x) == noise_free(y)


def test_power_law_numerical_stability():
    """PowerLaw evaluates extreme exponents: 0.1^-10 = 1e10 and 10^0.1.

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.1, 1.0, 10.0])
    y = np.array([10.0, 1.0, 0.1])

    obj = PowerLaw(x, y)

    assert obj.function(0.1, 1.0, -10.0) == exact(1e10)
    # 10^0.1 = 1.2589254117941673 (tenth root of 10).
    assert obj.function(10.0, 1.0, 0.1) == exact(1.2589254117941673)


def test_power_law_zero_handling():
    """PowerLaw is x itself at b = 1 near zero, and the constant A at b = 0.

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.01, 1.0, 100.0])
    y = np.array([1.0, 1.0, 1.0])

    obj = PowerLaw(x, y)

    assert obj.function(0.01, 1.0, 1.0) == exact(0.01)
    assert obj.function(2.0, 5.0, 0.0) == exact(5.0)


def test_power_law_off_center_centering():
    """PowerLawOffCenter measures x from x0: 2 (x - 1.5) at x = 2..5 is 1, 3, 5, 7.

    ON FAILURE: the code is wrong.
    """
    x = np.array([2.0, 3.0, 4.0, 5.0])
    x0 = 1.5

    obj = PowerLawOffCenter(x, np.ones_like(x))

    result = obj.function(x, 2.0, 1.0, x0)
    assert result == exact([1.0, 3.0, 5.0, 7.0])


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
    assert obj(x_test) == noise_free(expected)


def test_power_law_off_center_bounds_x0_below_the_data():
    """``make_fit`` keeps ``x0`` below the smallest used x, where the model is defined.

    Unbounded, the fit to 16 / x^2 on x = 1, 2, 4, 8 steps ``x0`` above 1
    during its search, and numpy warns "invalid value encountered in power"
    (a negative base has no real non-integer power). This test makes that
    warning an error.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 2.0, 4.0, 8.0])
    obj = PowerLawOffCenter(x, 16.0 * x**-2.0)
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        obj.make_fit()

    # The largest float below 1: x0 < x for every used x.
    assert obj.fit_bounds["x0"].upper == np.nextafter(1.0, -np.inf)
    assert obj.fit_bounds["x0"].lower == -np.inf
    assert obj.popt["x0"] < 1.0


@pytest.mark.parametrize(
    "x0_upper, expected",
    [
        pytest.param(0.5, 0.5, id="caller-bound-below-data-kept"),
        pytest.param(5.0, np.nextafter(1.0, -np.inf), id="caller-bound-above-data-cut"),
    ],
)
def test_power_law_off_center_bound_respects_the_caller(x0_upper, expected):
    """A caller's bounds are kept, with the upper bound on ``x0`` cut below the data.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 2.0, 4.0, 8.0])
    obj = PowerLawOffCenter(x, 16.0 * x**-2.0)
    obj.make_fit(bounds=([0.0, -5.0, -3.0], [100.0, 5.0, x0_upper]))

    assert obj.fit_bounds["A"] == (0.0, 100.0)
    assert obj.fit_bounds["b"] == (-5.0, 5.0)
    assert obj.fit_bounds["x0"] == (-3.0, expected)


@pytest.mark.parametrize(
    "x, x0",
    [
        # 4 (x + 1)^2 at x = 0, 1, 3, 7 is 4, 16, 64, 256: x0 = -1.
        pytest.param([0.0, 1.0, 3.0, 7.0], -1.0, id="x-reaches-zero"),
        pytest.param([-0.5, 0.0, 2.0, 6.0], -1.5, id="x-negative"),
        # Positive control: the same curve on x > 0, where p0 starts x0 at 0.
        pytest.param([2.0, 3.0, 5.0, 9.0], 1.0, id="x-positive"),
    ],
)
def test_power_law_off_center_fits_data_at_or_below_zero(x, x0):
    """``p0`` starts ``x0`` below the smallest used x, so data with x <= 0 fit.

    With ``x0`` started at 0, any used x <= 0 puts the start above the upper
    bound ``make_fit`` places on ``x0`` and scipy refuses it ("x0 is
    infeasible").

    ON FAILURE: the code is wrong.
    """
    x = np.array(x)
    y = 4.0 * (x - x0) ** 2  # A = 4, b = 2
    obj = PowerLawOffCenter(x, y)
    assert obj.p0[2] < x.min()

    obj.make_fit()
    assert obj.popt["A"] == noise_free(4.0)
    assert obj.popt["b"] == noise_free(2.0)
    assert obj.popt["x0"] == noise_free(x0)


@pytest.mark.parametrize("x0_lower", [1.0, 2.0])
def test_power_law_off_center_refuses_a_bound_with_no_room_below_the_data(x0_lower):
    """A caller's lower bound on ``x0`` at or above the smallest x raises ValueError.

    The error names ``x0`` and the smallest used x, and ``return_exception``
    returns it. The positive control fits the same data with the lower bound
    moved below the data.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 2.0, 4.0, 8.0])
    obj = PowerLawOffCenter(x, 16.0 * x**-2.0)
    bounds = ([0.0, -5.0, x0_lower], [100.0, 5.0, 10.0])
    match = r"needs x0 below the smallest used x \(1\.0\)"

    with pytest.raises(ValueError, match=match):
        obj.make_fit(bounds=bounds)
    assert re.search(match, str(obj.make_fit(return_exception=True, bounds=bounds)))

    # Positive control: a lower bound below the data fits.
    bounds[0][2] = -3.0
    obj.make_fit(bounds=bounds)
    # 16 / x^2 = 16 (x - 0)^-2; x is of order 1.
    assert obj.popt["x0"] == noise_free(0.0, scale=1.0)


@pytest.mark.parametrize("x0_start", [1.0, 2.0])
def test_power_law_off_center_refuses_a_caller_p0_above_the_data(x0_start):
    """A caller's ``p0`` starting ``x0`` at or above the smallest x raises ValueError.

    The error names ``x0``, the smallest used x and the start, in place of
    scipy's "x0 is infeasible", and ``return_exception`` returns it. The
    positive control fits the same data from a start below the data.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 2.0, 4.0, 8.0])
    obj = PowerLawOffCenter(x, 16.0 * x**-2.0)
    p0 = [1.0, 1.0, x0_start]
    match = (
        r"needs x0 below the smallest used x \(1\.0\).*p0 starts x0 at "
        + re.escape(str(x0_start))
    )

    with pytest.raises(ValueError, match=match):
        obj.make_fit(p0=p0)
    assert re.search(match, str(obj.make_fit(return_exception=True, p0=p0)))

    # Positive control: a start below the data fits.
    p0[2] = -1.0
    obj.make_fit(p0=p0)
    # 16 / x^2 = 16 (x - 0)^-2; x is of order 1.
    assert obj.popt["x0"] == noise_free(0.0, scale=1.0)


@pytest.mark.parametrize(
    "x0_bounds, x0",
    [
        # p0 starts x0 at 0, below the caller's lower bound 0.5.
        pytest.param((0.5, 10.0), 0.75, id="start-below-lower-bound"),
        # p0 starts x0 at 0, above the caller's upper bound -1.
        pytest.param((-3.0, -1.0), -1.5, id="start-above-upper-bound"),
        # Positive control: the start 0 is already inside the bounds.
        pytest.param((-3.0, 10.0), 0.5, id="start-inside-bounds"),
    ],
)
def test_power_law_off_center_clips_its_x0_start_into_the_bounds(x0_bounds, x0):
    """``make_fit`` clips the :attr:`p0` start for ``x0`` into the caller's bounds.

    Without the clip, a start outside ``[lb, ub]`` makes scipy refuse the fit
    ("x0 is infeasible").

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 2.0, 4.0, 8.0])
    y = 4.0 * (x - x0) ** 2  # A = 4, b = 2
    obj = PowerLawOffCenter(x, y)
    assert obj.p0[2] == exact(0.0)

    obj.make_fit(bounds=([0.0, -5.0, x0_bounds[0]], [100.0, 5.0, x0_bounds[1]]))
    assert obj.popt["A"] == noise_free(4.0)
    assert obj.popt["b"] == noise_free(2.0)
    assert obj.popt["x0"] == noise_free(x0)


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
    assert [obj.popt["A"], obj.popt["b"]] == noise_free(weighted)
    # Ignoring the weights must fail the line above by a wide margin: the
    # weighted and unweighted answers differ by over 100x the fit tolerance.
    gap = np.max(np.abs(weighted / unweighted - 1))
    assert gap > 100 * NOISE_FREE_REL


def test_power_law_scaling_behavior():
    """A fit to 2/x scales by 2^b = 1/2 when x doubles.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 2.0, 4.0, 8.0])
    y = np.array([2.0, 1.0, 0.5, 0.25])  # 2 / x

    obj = PowerLaw(x, y)
    obj.make_fit()

    assert obj(4.0) / obj(2.0) == noise_free(0.5)


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

    assert obj.function(x, 1.0, 2.0) == exact([4.0, 1.0, 1.0, 4.0])


def test_power_law_integer_vs_float_exponents():
    """Integer and float exponents give 2 x^2 = 2, 8, 18 alike.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 2.0, 3.0])
    A = 2.0

    obj = PowerLaw(x, np.ones_like(x))

    assert obj.function(x, A, 2) == exact([2.0, 8.0, 18.0])
    assert obj.function(x, A, 2.0) == exact([2.0, 8.0, 18.0])


def test_power_law_edge_case_exponents():
    """b = 1, 0, -1 give a line, a constant, and an inverse.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 2.0, 4.0])
    obj = PowerLaw(x, np.ones_like(x))

    assert obj.function(x, 3.0, 1.0) == exact([3.0, 6.0, 12.0])
    assert obj.function(x, 5.0, 0.0) == exact([5.0, 5.0, 5.0])
    assert obj.function(x, 2.0, -1.0) == exact([2.0, 1.0, 0.5])
