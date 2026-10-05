"""Tests for linear fit functions."""

import inspect
import numpy as np
import pytest

from solarwindpy.fitfunctions.lines import (
    Line,
    LineXintercept,
)
from solarwindpy.fitfunctions.core import InsufficientDataError

# Noise-free fits: rel=1e-6 is far above optimizer convergence, far below any real bug.
NOISE_FREE = dict(rel=1e-6, abs=0)


@pytest.mark.parametrize(
    "cls, expected_params, sample_args, expected_result",
    [
        (Line, ("x", "m", "b"), (2.0, 1.5, 0.5), 3.5),  # 1.5*2.0 + 0.5
        (LineXintercept, ("x", "m", "x0"), (2.0, 1.5, 1.0), 1.5),  # 1.5*(2.0-1.0)
    ],
)
def test_function_signature_and_output(
    cls, expected_params, sample_args, expected_result
):
    """The model takes ``(x, *params)`` in documented order and evaluates by hand.

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 1.0, 2.0])
    y = np.array([0.5, 2.0, 3.5])
    obj = cls(x, y)

    sig = inspect.signature(obj.function)
    assert tuple(sig.parameters.keys()) == expected_params

    # Exact arithmetic on binary-representable inputs.
    assert obj.function(*sample_args) == pytest.approx(
        expected_result, rel=1e-12, abs=0
    )


@pytest.mark.parametrize("cls", [Line, LineXintercept])
def test_p0_zero_size_input(cls):
    """Asking for an initial guess with no data raises InsufficientDataError.

    ON FAILURE: the code is wrong.
    """
    x = np.array([])
    y = np.array([])
    obj = cls(x, y)

    with pytest.raises(InsufficientDataError):
        _ = obj.p0


def test_line_p0_estimation():
    """On exact line data y = 2x + 1, Line's initial guess is [m, b] = [2, 1].

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 1.0, 2.0, 3.0])
    y = 2.0 * x + 1.0

    p0 = Line(x, y).p0

    assert p0 == pytest.approx([2.0, 1.0], **NOISE_FREE)


def test_line_x_intercept_p0_estimation():
    """On exact data y = 2(x - 1.5), LineXintercept's guess is [m, x0] = [2, 1.5].

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 1.0, 2.0, 3.0])
    y = 2.0 * (x - 1.5)

    p0 = LineXintercept(x, y).p0

    assert p0 == pytest.approx([2.0, 1.5], **NOISE_FREE)


@pytest.mark.parametrize(
    "cls, expected_tex",
    [
        (Line, r"f(x)=m \cdot x + b"),
        (LineXintercept, r"f(x)=m \cdot (x - x_0)"),
    ],
)
def test_TeX_function_strings(cls, expected_tex):
    """Each class reports its documented LaTeX model string.

    ON FAILURE: the code is wrong, unless the author changed the TeX wording.
    """
    x = np.array([1.0, 2.0])
    y = np.array([2.0, 4.0])
    obj = cls(x, y)
    assert obj.TeX_function == expected_tex


@pytest.mark.parametrize(
    "cls, truth",
    [
        (Line, {"m": 2.0, "b": 1.0}),
        # y = 2x + 1 = 2(x - (-0.5)), so x0 = -0.5.
        (LineXintercept, {"m": 2.0, "x0": -0.5}),
    ],
)
def test_make_fit_success(cls, truth, simple_linear_data):
    """A fit to noisy y = 2x + 1 recovers each parameter within 4 error bars.

    ON FAILURE: the code is wrong.
    """
    x, y, w = simple_linear_data
    obj = cls(x, y)
    obj.make_fit()

    assert set(obj.popt) == set(truth)
    for name, value in truth.items():
        # Fixed seed (conftest default_rng(42)); 4 error bars per TEST_PATTERNS.
        assert abs(obj.popt[name] - value) < 4 * obj.psigma[name], name


@pytest.mark.parametrize("cls", [Line, LineXintercept])
def test_make_fit_insufficient_data(cls):
    """One point cannot fit two parameters: raise, or return the error on request.

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


def test_line_x_intercept_property():
    """Line fitted to y = 2x - 4 crosses y = 0 at x = 2.

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 1.0, 2.0, 3.0])
    y = np.array([-4.0, -2.0, 0.0, 2.0])

    obj = Line(x, y)
    obj.make_fit()

    assert obj.x_intercept == pytest.approx(2.0, **NOISE_FREE)


def test_line_x_intercept_y_intercept_property():
    """LineXintercept fitted to y = 2(x - 1) crosses x = 0 at y = -2.

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 1.0, 2.0, 3.0])
    y = np.array([-2.0, 0.0, 2.0, 4.0])

    obj = LineXintercept(x, y)
    obj.make_fit()

    assert obj.y_intercept == pytest.approx(-2.0, **NOISE_FREE)


def test_line_perfect_fit():
    """Line recovers m = 1.5, b = -0.7 from noise-free data and reproduces it.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(0, 5, 10)
    m_true, b_true = 1.5, -0.7
    y = m_true * x + b_true

    obj = Line(x, y)
    obj.make_fit()

    assert obj.popt["m"] == pytest.approx(m_true, **NOISE_FREE)
    assert obj.popt["b"] == pytest.approx(b_true, **NOISE_FREE)
    assert obj(x) == pytest.approx(y, **NOISE_FREE)


def test_line_x_intercept_perfect_fit():
    """LineXintercept recovers m = 2, x0 = 1.5 from noise-free data.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(-2, 3, 10)
    m_true, x0_true = 2.0, 1.5
    y = m_true * (x - x0_true)

    obj = LineXintercept(x, y)
    obj.make_fit()

    assert obj.popt["m"] == pytest.approx(m_true, **NOISE_FREE)
    assert obj.popt["x0"] == pytest.approx(x0_true, **NOISE_FREE)
    assert obj(x) == pytest.approx(y, **NOISE_FREE)


@pytest.mark.parametrize("cls", [Line, LineXintercept])
def test_str_and_call_methods(cls):
    """``str`` names the class; calling a fit to y = 2x + 1 evaluates that line.

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 1.0, 2.0, 3.0])
    obj = cls(x, 2.0 * x + 1.0)
    obj.make_fit()

    assert cls.__name__ in str(obj)

    # Points off the fitted grid: 2*0.5+1, 2*1.5+1, 2*7+1.
    x_test = np.array([0.5, 1.5, 7.0])
    assert obj(x_test) == pytest.approx([2.0, 4.0, 15.0], **NOISE_FREE)


def test_line_with_weights():
    """Weights are 1-sigma errors: the fit equals weighted least squares.

    The perturbations are small enough (|r/sigma| <= 0.04) that the default
    Huber loss (f_scale=0.1) stays quadratic, so the minimizer is the
    weighted least-squares line, computed independently by ``np.polyfit``.

    ON FAILURE: the code is wrong, unless the default loss no longer reduces
    to least squares for residuals below f_scale.
    """
    x = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
    y = 2.0 * x + 1.0 + np.array([0.02, -0.02, 0.02, -0.02, 0.02, -0.02])
    sigma = np.array([0.5, 0.5, 1.0, 1.0, 2.0, 2.0])

    obj = Line(x, y, weights=sigma)
    obj.make_fit()

    m_w, b_w = np.polyfit(x, y, 1, w=1.0 / sigma)
    m_u, b_u = np.polyfit(x, y, 1)
    assert [obj.popt["m"], obj.popt["b"]] == pytest.approx([m_w, b_w], **NOISE_FREE)
    # Ignoring the weights must fail the line above by a wide margin: the
    # weighted and unweighted answers differ by over 100x the fit tolerance.
    gap = np.max(np.abs(np.array([m_w, b_w]) / np.array([m_u, b_u]) - 1))
    assert gap > 100 * NOISE_FREE["rel"]


def test_line_horizontal_data():
    """Line fitted to y = 3 has slope 0 and intercept 3.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(0, 5, 10)
    y = np.full_like(x, 3.0)

    obj = Line(x, y)
    obj.make_fit()

    # True slope is 0, so rel is meaningless; 1e-9 is optimizer noise on O(1) data.
    assert obj.popt["m"] == pytest.approx(0.0, abs=1e-9)
    assert obj.popt["b"] == pytest.approx(3.0, **NOISE_FREE)


def test_line_recovers_near_vertical_slope():
    """Line fitted to x spaced by 1e-4 and y by 10 recovers m = 1e5, b = -1e5.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 1.0001, 1.0002])
    y = np.array([0.0, 10.0, 20.0])  # y = 1e5 (x - 1)

    obj = Line(x, y)
    obj.make_fit()

    assert obj.popt["m"] == pytest.approx(1e5, **NOISE_FREE)
    assert obj.popt["b"] == pytest.approx(-1e5, **NOISE_FREE)


@pytest.mark.parametrize("cls", [Line, LineXintercept])
def test_line_p0_is_none_with_duplicate_x_values(cls):
    """Repeated x leaves no slope estimate, so p0 is None, and the fit still runs.

    The p0 docstring promises None for repeated ``x``. The data are
    y = 2x + 0.05 +/- 0.05 at x in {1, 2}, whose least-squares line is
    m = 2, b = 0.05 (x0 = -0.025); residuals stay inside the Huber quadratic
    region, so the fit equals that line.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 1.0, 2.0, 2.0])
    y = np.array([2.0, 2.1, 4.0, 4.1])

    obj = cls(x, y)
    # The slope estimate divides by the zero x-steps before giving up.
    with pytest.warns(RuntimeWarning, match="divide by zero"):
        assert obj.p0 is None
    obj.make_fit()

    assert obj(np.array([1.0, 2.0])) == pytest.approx([2.05, 4.05], **NOISE_FREE)


@pytest.mark.parametrize("cls", [Line, LineXintercept])
def test_property_access_before_fit(cls):
    """Fit results do not exist before ``make_fit``: popt and pcov raise.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([2.0, 4.0, 6.0])
    obj = cls(x, y)

    with pytest.raises(AttributeError):
        _ = obj.popt
    with pytest.raises(AttributeError):
        _ = obj.pcov


def test_line_intercept_properties_require_fit():
    """Intercepts raise before a fit; after fitting y = 2x + 1 they are -0.5 and 1.

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 1.0, 2.0])
    y = np.array([1.0, 3.0, 5.0])

    line_obj = Line(x, y)
    xint_obj = LineXintercept(x, y)

    with pytest.raises(AttributeError):
        _ = line_obj.x_intercept
    with pytest.raises(AttributeError):
        _ = xint_obj.y_intercept

    line_obj.make_fit()
    xint_obj.make_fit()

    assert line_obj.x_intercept == pytest.approx(-0.5, **NOISE_FREE)
    assert xint_obj.y_intercept == pytest.approx(1.0, **NOISE_FREE)


def test_line_edge_cases():
    """Line fitted to all-zero y is the zero line, m = b = 0.

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 1.0, 2.0])
    y = np.array([0.0, 0.0, 0.0])

    obj = Line(x, y)
    obj.make_fit()

    # Truth is exactly 0, so rel is meaningless; 1e-10 is optimizer noise on O(1) x.
    assert obj.popt["m"] == pytest.approx(0.0, abs=1e-10)
    assert obj.popt["b"] == pytest.approx(0.0, abs=1e-10)


def test_line_numerical_precision():
    """Line fitted to y = 2x at x ~ 1e6 recovers m = 2 and predicts y(1e6 + 0.5).

    ON FAILURE: the code is wrong.
    """
    x = np.array([1e6, 1e6 + 1, 1e6 + 2])
    y = np.array([2e6, 2e6 + 2, 2e6 + 4])

    obj = Line(x, y)
    obj.make_fit()

    assert obj.popt["m"] == pytest.approx(2.0, **NOISE_FREE)
    # 2 * (1e6 + 0.5) = 2e6 + 1. abs=1e-3 is far above float64 resolution at 2e6
    # (~4e-10) and far below a misplaced intercept or slope error of 1e-6.
    assert obj(1e6 + 0.5) == pytest.approx(2e6 + 1.0, rel=0, abs=1e-3)
