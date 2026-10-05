"""Tests for exponential fit functions."""

import inspect
import numpy as np
import pytest
from scipy.optimize import curve_fit

from solarwindpy.fitfunctions.exponentials import (
    Exponential,
    ExponentialPlusC,
    ExponentialCDF,
)
from solarwindpy.fitfunctions.core import InsufficientDataError

# Noise-free fits: rel=1e-6 is far above optimizer convergence, far below any real bug.
NOISE_FREE = dict(rel=1e-6, abs=0)
# Closed-form evaluation: only floating-point rounding separates the two sides.
EXACT = dict(rel=1e-12, abs=0)

E_INV = 0.36787944117144233  # e^-1


@pytest.mark.parametrize(
    "cls, expected_params, sample_args, expected_value",
    [
        # 2 e^-1
        (Exponential, ("x", "c", "A"), (1.0, 1.0, 2.0), 2 * E_INV),
        # 2 e^-1 + 0.5
        (ExponentialPlusC, ("x", "c", "A", "d"), (1.0, 1.0, 2.0, 0.5), 2 * E_INV + 0.5),
        # y0 (1 - e^-1) with y0 = 3
        (ExponentialCDF, ("x", "c"), (1.0, 1.0), 3 * (1 - E_INV)),
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

    if cls is ExponentialCDF:
        obj.set_y0(3.0)  # Not 1, so an ignored amplitude fails.

    sig = inspect.signature(obj.function)
    assert tuple(sig.parameters.keys()) == expected_params

    assert obj.function(*sample_args) == pytest.approx(expected_value, **EXACT)


@pytest.fixture
def exponential_data():
    """Noisy y = 3 exp(-0.8 x), x in [0, 3], noise sigma 0.05, unit weights."""
    rng = np.random.default_rng(42)
    x = np.linspace(0, 3, 30)
    c, A = 0.8, 3.0
    noise = rng.normal(0, 0.05, size=x.shape)
    y = A * np.exp(-c * x) + noise
    w = np.ones_like(x)
    return x, y, w


@pytest.mark.parametrize("cls", [Exponential, ExponentialPlusC, ExponentialCDF])
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
    """From its default initial guess, Exponential recovers c = 0.8, A = 3 exactly.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(0, 3, 30)
    obj = Exponential(x, 3.0 * np.exp(-0.8 * x))
    obj.make_fit()

    assert obj.popt["c"] == pytest.approx(0.8, **NOISE_FREE)
    assert obj.popt["A"] == pytest.approx(3.0, **NOISE_FREE)


def test_exponential_plus_c_p0_estimation():
    """From its default initial guess, ExponentialPlusC recovers c, A, d exactly.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(0, 3, 30)
    obj = ExponentialPlusC(x, 3.0 * np.exp(-0.8 * x) + 0.5)
    obj.make_fit()

    assert obj.popt["c"] == pytest.approx(0.8, **NOISE_FREE)
    assert obj.popt["A"] == pytest.approx(3.0, **NOISE_FREE)
    assert obj.popt["d"] == pytest.approx(0.5, **NOISE_FREE)


def test_exponential_cdf_p0_estimation():
    """From its default initial guess, ExponentialCDF recovers c = 0.8 exactly.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(0, 3, 30)
    obj = ExponentialCDF(x, 1.0 - np.exp(-0.8 * x))
    obj.set_y0(1.0)
    obj.make_fit()

    assert obj.popt["c"] == pytest.approx(0.8, **NOISE_FREE)


@pytest.mark.parametrize(
    "cls, expected_tex",
    [
        (Exponential, r"f(x)=A \cdot e^{-cx}"),
        (ExponentialPlusC, r"f(x)=A \cdot e^{-cx} + d"),
        (ExponentialCDF, r"f(x)=A \left(1 - e^{-cx}\right)"),
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
        (Exponential, {"c": 0.8, "A": 3.0}),
        (ExponentialPlusC, {"c": 0.8, "A": 3.0, "d": 0.0}),
    ]:
        obj = cls(x, y)
        obj.make_fit()

        assert set(obj.popt) == set(truth)
        for name, value in truth.items():
            # Fixed seed (default_rng(42)); 4 error bars per TEST_PATTERNS.
            assert abs(obj.popt[name] - value) < 4 * obj.psigma[name], (cls, name)


def test_make_fit_success_cdf():
    """A fit to noisy 1 - exp(-0.8 x) with y0 = 1 recovers c within 4 error bars.

    ON FAILURE: the code is wrong.
    """
    rng = np.random.default_rng(42)
    x = np.linspace(0, 3, 30)
    y = 1.0 - np.exp(-0.8 * x) + rng.normal(0, 0.05, size=x.shape)

    obj = ExponentialCDF(x, y)
    obj.set_y0(1.0)
    obj.make_fit()

    # Fixed seed; 4 error bars per TEST_PATTERNS.
    assert abs(obj.popt["c"] - 0.8) < 4 * obj.psigma["c"]


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

        result = obj.make_fit(return_exception=True)
        assert isinstance(result, InsufficientDataError)
        assert "insufficient data" in str(result).lower()


def test_exponential_cdf_fits_one_point():
    """ExponentialCDF has one free parameter, so one point suffices to fit it.

    The point (1, 1 - e^-0.8) with y0 = 1 fixes c = 0.8.

    ON FAILURE: the code is wrong.
    """
    obj = ExponentialCDF(np.array([1.0]), np.array([1.0 - np.exp(-0.8)]))
    obj.set_y0(1.0)

    # Zero degrees of freedom: the covariance warning is expected, not the subject.
    with pytest.warns(Warning):
        assert obj.make_fit() is None
    # One point leaves the optimizer's own xtol (1e-8) as the accuracy limit.
    assert obj.popt["c"] == pytest.approx(0.8, rel=1e-6, abs=0)


def test_exponential_numerical_stability():
    """Exponential evaluates exp(-100) without underflow to zero.

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 10.0, 100.0])
    y = np.array([1.0, 0.1, 0.01])
    obj = Exponential(x, y)

    # e^-100 = 3.720075976020836e-44; abs=0 because the value is tiny.
    assert obj.function(100.0, 1.0, 1.0) == pytest.approx(
        3.720075976020836e-44, **EXACT
    )


def test_exponential_plus_c_constant_term():
    """ExponentialPlusC is A at x = 0 plus d, and A/2 plus d one half-life later.

    ON FAILURE: the code is wrong.
    """
    c, A, d = 1.0, 2.0, 0.5
    x = np.array([0.0, np.log(2.0) / c])  # 0 and one half-life
    obj = ExponentialPlusC(x, np.ones_like(x))

    # 2 + 0.5 and 2/2 + 0.5
    assert obj.function(x, c, A, d) == pytest.approx([2.5, 1.5], **EXACT)


def test_exponential_cdf_monotonicity():
    """ExponentialCDF rises monotonically from 0 toward y0, reaching y0/2 at ln2/c.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(0, 5, 20)
    c = 0.5

    obj = ExponentialCDF(x, np.ones_like(x))
    obj.set_y0(3.0)  # Not 1, so an ignored amplitude fails.
    result = obj.function(x, c)

    assert np.all(np.diff(result) > 0)
    assert result[0] == 0.0  # 3 (1 - e^0)
    assert result[-1] < 3.0
    # 3 (1 - 1/2) at the half-life.
    assert obj.function(np.log(2.0) / c, c) == pytest.approx(1.5, **EXACT)


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
        # A + d at x = 0; A/2 + d at the half-life.
        assert obj(x_test) == pytest.approx(
            [3.0 + offset, 1.5 + offset], **NOISE_FREE
        ), cls


def test_str_and_call_methods_cdf():
    """``str`` names ExponentialCDF; calling a noise-free fit evaluates the curve.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(0, 3, 30)
    obj = ExponentialCDF(x, 2.0 * (1.0 - np.exp(-0.8 * x)))
    obj.set_y0(2.0)
    obj.make_fit()

    assert "ExponentialCDF" in str(obj)
    # 2 (1 - 1/2) at the half-life ln2/0.8.
    assert obj(np.log(2.0) / 0.8) == pytest.approx(1.0, **NOISE_FREE)


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
    assert obj(x_test) == pytest.approx([2.0, 1.0, 0.5], **NOISE_FREE)


@pytest.mark.parametrize("cls", [Exponential, ExponentialPlusC, ExponentialCDF])
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

    def model(x, c, A):
        return A * np.exp(-c * x)

    weighted, _ = curve_fit(model, x, y, p0=[1.0, 3.0], sigma=sigma)
    unweighted, _ = curve_fit(model, x, y, p0=[1.0, 3.0])
    assert [obj.popt["c"], obj.popt["A"]] == pytest.approx(weighted, **NOISE_FREE)
    # Ignoring the weights must fail the line above by a wide margin: the
    # weighted and unweighted answers differ by over 100x the fit tolerance.
    gap = np.max(np.abs(weighted / unweighted - 1))
    assert gap > 100 * NOISE_FREE["rel"]


@pytest.mark.parametrize(
    "cls, params, y0, expected",
    [
        # Slow decay, c = 1e-6: e^{-cx} = 1 - cx to 2e-12.
        (Exponential, (1e-6, 1.0), None, [1.0, 1 - 1e-6, 1 - 2e-6]),
        (ExponentialPlusC, (1e-6, 1.0, 0.5), None, [1.5, 1.5 - 1e-6, 1.5 - 2e-6]),
        (ExponentialCDF, (1e-6,), 1.0, [0.0, 1e-6, 2e-6]),
        # Fast decay, c = 100: e^-100 ~ 4e-44 vanishes beside O(1) terms.
        (Exponential, (100.0, 1.0), None, [1.0, 0.0, 0.0]),
        (ExponentialPlusC, (100.0, 1.0, 0.5), None, [1.5, 0.5, 0.5]),
        (ExponentialCDF, (100.0,), 1.0, [0.0, 1.0, 1.0]),
    ],
)
def test_extreme_decay_rates_reach_their_limits(cls, params, y0, expected):
    """At c -> 0 each model is linear in x; at large c it jumps to its x -> inf limit.

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 1.0, 2.0])
    obj = cls(x, np.array([1.0, 0.5, 0.25]))
    if y0 is not None:
        obj.set_y0(y0)

    # abs=1e-11 covers the dropped second-order term (c x)^2 / 2 <= 2e-12 and the
    # e^-100 ~ 4e-44 remainder, and is 1e5 times below the 1e-6 effects asserted.
    assert obj.function(x, *params) == pytest.approx(expected, rel=0, abs=1e-11)


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

        assert len(p0) == len(obj.argnames) == 2  # c, A
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

        assert len(p0) == len(obj.argnames) == 3  # c, A, d
        assert np.all(np.isfinite(p0))


class TestExponentialTeXPhase6:
    """Phase 6 tests for TeX function validation."""

    def test_all_tex_functions_valid(self):
        """Every exponential model's TeX string is distinct from the others.

        ON FAILURE: the code is wrong.
        """
        x = np.linspace(0, 5, 20)
        y = np.exp(-x)

        tex = {
            cls(x, y).TeX_function
            for cls in [Exponential, ExponentialPlusC, ExponentialCDF]
        }
        assert len(tex) == 3
