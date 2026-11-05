"""Tests for exponential fit functions."""

import inspect
import numpy as np
import pytest
from scipy.optimize import curve_fit

from solarwindpy.fitfunctions.exponentials import (
    Exponential,
    ExponentialPlusC,
)
from solarwindpy.fitfunctions.core import InsufficientDataError
from tests.tolerances import NOISE_FREE_REL, exact, noise_free, printed
from tests.fitfunctions._attempt import attempt_fit

E_INV = 0.36787944117144233  # e^-1


@pytest.mark.parametrize(
    "cls, expected_params, sample_args, expected_value",
    [
        # 2 e^-1
        (Exponential, ("x", "k", "A"), (1.0, 1.0, 2.0), 2 * E_INV),
        # 2 e^-1 + 0.5
        (
            ExponentialPlusC,
            ("x", "k", "y0", "A"),
            (1.0, 1.0, 0.5, 2.0),
            2 * E_INV + 0.5,
        ),
    ],
)
def test_function_signature_and_output(
    cls, expected_params, sample_args, expected_value
):
    """The model takes ``(x, *params)`` in documented order and evaluates by hand.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(0.0, 2.0, 10)
    y = np.ones_like(x)
    obj = cls(x, y)

    sig = inspect.signature(obj.function)
    assert tuple(sig.parameters.keys()) == expected_params

    assert obj.function(*sample_args) == exact(expected_value)


@pytest.fixture
def exponential_data():
    """Noisy y = 3 exp(-0.8 x), x in [0, 3], noise sigma 0.05, unit weights."""
    rng = np.random.default_rng(42)
    x = np.linspace(0, 3, 30)
    k, A = 0.8, 3.0
    noise = rng.normal(0, 0.05, size=x.shape)
    y = A * np.exp(-k * x) + noise
    w = np.ones_like(x)
    return x, y, w


@pytest.mark.parametrize("cls", [Exponential, ExponentialPlusC])
def test_p0_zero_size_input(cls):
    """Asking for an initial guess with no data raises InsufficientDataError.

    ON FAILURE: the code is wrong.
    """
    x = np.array([])
    y = np.array([])
    obj = cls(x, y)

    with pytest.raises(InsufficientDataError):
        _ = obj.p0


def test_exponential_p0_estimation():
    """From its default initial guess, Exponential recovers k = 0.8, A = 3 exactly.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(0, 3, 30)
    obj = Exponential(x, 3.0 * np.exp(-0.8 * x))
    obj.make_fit()

    assert obj.popt["k"] == noise_free(0.8)
    assert obj.popt["A"] == noise_free(3.0)


def test_exponential_plus_c_p0_estimation():
    """From its default initial guess, ExponentialPlusC recovers k, A, y0 exactly.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(0, 3, 30)
    obj = ExponentialPlusC(x, 3.0 * np.exp(-0.8 * x) + 0.5)
    obj.make_fit()

    assert obj.popt["k"] == noise_free(0.8)
    assert obj.popt["A"] == noise_free(3.0)
    assert obj.popt["y0"] == noise_free(0.5)


def test_exponential_plus_c_names_its_constant_y0():
    """ExponentialPlusC calls its added constant ``y0``, and no parameter ``c``.

    The rate was once ``c``, so an old ``popt["c"]`` must raise KeyError rather
    than silently return the constant. Data are 3 exp(-0.8 x) + 0.5.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(0, 3, 30)
    obj = ExponentialPlusC(x, 3.0 * np.exp(-0.8 * x) + 0.5)
    obj.make_fit()

    assert set(obj.popt) == {"k", "A", "y0"}
    assert obj.popt["y0"] == noise_free(0.5)
    with pytest.raises(KeyError):
        obj.popt["c"]
    assert obj.TeX_function == r"f(x)=A \cdot e^{-kx} + y_0"


@pytest.mark.parametrize(
    "cls, expected_tex",
    [
        (Exponential, r"f(x)=A \cdot e^{-kx}"),
        (ExponentialPlusC, r"f(x)=A \cdot e^{-kx} + y_0"),
    ],
)
def test_TeX_function_strings(cls, expected_tex):
    """Each class reports its documented LaTeX model string.

    ON FAILURE: the code is wrong, unless the author changed the TeX wording.
    """
    x = np.array([1.0, 2.0])
    y = np.array([1.0, 0.5])
    obj = cls(x, y)
    assert obj.TeX_function == expected_tex


def test_make_fit_success_regular(exponential_data):
    """Fits to noisy 3 exp(-0.8 x) recover each parameter within 4 error bars.

    ON FAILURE: the code is wrong.
    """
    x, y, w = exponential_data

    for cls, truth in [
        (Exponential, {"k": 0.8, "A": 3.0}),
        (ExponentialPlusC, {"k": 0.8, "A": 3.0, "y0": 0.0}),
    ]:
        obj = cls(x, y)
        obj.make_fit()

        assert set(obj.popt) == set(truth)
        for name, value in truth.items():
            # Fixed seed (default_rng(42)); 4 error bars per TEST_PATTERNS.
            assert abs(obj.popt[name] - value) < 4 * obj.psigma[name], (cls, name)


def test_make_fit_insufficient_data():
    """One point cannot fit the two- and three-parameter models.

    ON FAILURE: the code is wrong.
    """
    for cls in [Exponential, ExponentialPlusC]:
        x = np.array([1.0])
        y = np.array([1.0])
        obj = cls(x, y)

        with pytest.raises(InsufficientDataError):
            obj.make_fit()

        result = attempt_fit(obj)
        assert isinstance(result, InsufficientDataError)
        assert "insufficient data" in str(result).lower()


def test_exponential_numerical_stability():
    """Exponential evaluates exp(-100) without underflow to zero.

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 10.0, 100.0])
    y = np.array([1.0, 0.1, 0.01])
    obj = Exponential(x, y)

    # e^-100 = 3.720075976020836e-44.
    assert obj.function(100.0, 1.0, 1.0) == exact(3.720075976020836e-44)


def test_exponential_plus_c_constant_term():
    """ExponentialPlusC is A at x = 0 plus y0, and A/2 plus y0 one half-life later.

    ON FAILURE: the code is wrong.
    """
    k, A, y0 = 1.0, 2.0, 0.5
    x = np.array([0.0, np.log(2.0) / k])  # 0 and one half-life
    obj = ExponentialPlusC(x, np.ones_like(x))

    # 2 + 0.5 and 2/2 + 0.5
    assert obj.function(x, k, y0, A) == exact([2.5, 1.5])


def test_str_and_call_methods_regular():
    """``str`` names the class; calling a noise-free fit evaluates the true curve.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(0, 3, 30)
    x_test = np.array([0.0, np.log(2.0) / 0.8])  # 0 and one half-life

    for cls, offset in [(Exponential, 0.0), (ExponentialPlusC, 0.5)]:
        obj = cls(x, 3.0 * np.exp(-0.8 * x) + offset)
        obj.make_fit()

        assert cls.__name__ in str(obj)
        # A + y0 at x = 0; A/2 + y0 at the half-life.
        assert obj(x_test) == noise_free([3.0 + offset, 1.5 + offset]), cls


def test_exponential_decay_behavior():
    """A fit to 2 exp(-0.5 x) decays: 2 at x = 0, halving every ln2/0.5.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(0, 3, 10)
    y = 2.0 * np.exp(-0.5 * x)

    obj = Exponential(x, y)
    obj.make_fit()

    half_life = np.log(2.0) / 0.5
    x_test = np.array([0.0, half_life, 2 * half_life])
    assert obj(x_test) == noise_free([2.0, 1.0, 0.5])


@pytest.mark.parametrize("cls", [Exponential, ExponentialPlusC])
def test_property_access_before_fit(cls):
    """Fit results do not exist before ``make_fit``: popt and pcov raise.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([1.0, 0.5, 0.25])
    obj = cls(x, y)

    with pytest.raises(AttributeError):
        _ = obj.popt
    with pytest.raises(AttributeError):
        _ = obj.pcov


def test_exponential_with_weights():
    """Weights are 1-sigma errors: the fit equals scipy's weighted ``curve_fit``.

    The perturbations are small enough (|r/sigma| <= 0.02) that the default
    Huber loss (f_scale=0.1) stays quadratic, so the minimizer is the weighted
    least-squares solution that ``scipy.optimize.curve_fit(sigma=...)`` finds.

    ON FAILURE: the code is wrong, unless the default loss no longer reduces
    to least squares for residuals below f_scale.
    """
    x = np.linspace(0, 3, 12)
    y = 3.0 * np.exp(-0.8 * x) + 0.01 * np.array([1, -1] * 6)
    sigma = np.linspace(0.5, 2.0, 12)

    obj = Exponential(x, y, weights=sigma)
    obj.make_fit()

    def model(x, k, A):
        return A * np.exp(-k * x)

    weighted, _ = curve_fit(model, x, y, p0=[1.0, 3.0], sigma=sigma)
    unweighted, _ = curve_fit(model, x, y, p0=[1.0, 3.0])
    assert [obj.popt["k"], obj.popt["A"]] == noise_free(weighted)
    # Ignoring the weights must fail the line above by a wide margin: the
    # weighted and unweighted answers differ by over 100x the fit tolerance.
    gap = np.max(np.abs(weighted / unweighted - 1))
    assert gap > 100 * NOISE_FREE_REL


@pytest.mark.parametrize(
    "cls, params, expected",
    [
        # Slow decay, k = 1e-6: e^{-kx} = 1 - kx to 2e-12.
        (Exponential, (1e-6, 1.0), [1.0, 1 - 1e-6, 1 - 2e-6]),
        (ExponentialPlusC, (1e-6, 0.5, 1.0), [1.5, 1.5 - 1e-6, 1.5 - 2e-6]),
        # Fast decay, k = 100: e^-100 ~ 4e-44 vanishes beside O(1) terms.
        (Exponential, (100.0, 1.0), [1.0, 0.0, 0.0]),
        (ExponentialPlusC, (100.0, 0.5, 1.0), [1.5, 0.5, 0.5]),
    ],
)
def test_extreme_decay_rates_reach_their_limits(cls, params, expected):
    """At k -> 0 each model is linear in x; at large k it jumps to its x -> inf limit.

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 1.0, 2.0])
    obj = cls(x, np.array([1.0, 0.5, 0.25]))

    # The limit forms drop (k x)^2 / 2 <= 2e-12 or e^-100 ~ 4e-44, so they hold
    # to 11 decimal places.
    assert obj.function(x, *params) == printed(expected, decimals=11)


# ============================================================================
# Phase 6 Coverage Tests
# ============================================================================


class TestExponentialP0Phase6:
    """Phase 6 tests for exponential p0 estimation."""

    def test_exponential_p0_valid_decay(self):
        """Exponential's p0 has one finite guess per fit parameter, in argnames order.

        ON FAILURE: the code is wrong.
        """
        x = np.linspace(0, 5, 50)
        y = 10.0 * np.exp(-0.5 * x)

        obj = Exponential(x, y)
        p0 = obj.p0

        assert len(p0) == len(obj.argnames) == 2  # k, A
        assert np.all(np.isfinite(p0))


class TestExponentialPlusCPhase6:
    """Phase 6 tests for ExponentialPlusC p0 estimation."""

    def test_exponential_plus_c_p0_valid(self):
        """ExponentialPlusC's p0 has one finite guess per fit parameter.

        ON FAILURE: the code is wrong.
        """
        x = np.linspace(0, 5, 50)
        y = 10.0 * np.exp(-0.5 * x) + 2.0

        obj = ExponentialPlusC(x, y)
        p0 = obj.p0

        assert len(p0) == len(obj.argnames) == 3  # k, y0, A
        assert np.all(np.isfinite(p0))


class TestExponentialTeXPhase6:
    """Phase 6 tests for TeX function validation."""

    def test_all_tex_functions_valid(self):
        """Every exponential model's TeX string is distinct from the others.

        ON FAILURE: the code is wrong.
        """
        x = np.linspace(0, 5, 20)
        y = np.exp(-x)

        tex = {cls(x, y).TeX_function for cls in [Exponential, ExponentialPlusC]}
        assert len(tex) == 2
