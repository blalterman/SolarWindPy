# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
"""The ``p0`` contract shared by every fit function.

A ``p0`` returns one finite guess per parameter, or None when the data make a
guess impossible; the fit then starts from ``fallback_p0()`` (the feasible
default, ones when unbounded, unless the class overrides it). ``make_fit`` rejects a guess holding NaN or infinity with a
``ValueError`` naming the class and the parameter. The contract is stated in
``FitFunction.p0``'s docstring.
"""

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

import solarwindpy
from solarwindpy.fitfunctions.composite import (
    GaussianPlusHeavySide,
    GaussianTimesHeavySide,
    GaussianTimesHeavySidePlusHeavySide,
)
from solarwindpy.fitfunctions.core import FitFunction, InsufficientDataError
from solarwindpy.fitfunctions.gaussians import Gaussian, GaussianLn, GaussianNormalized
from solarwindpy.fitfunctions.heaviside import HeavySide
from solarwindpy.fitfunctions.hinge import (
    HingeAtPoint,
    HingeMax,
    HingeMin,
    HingeSaturation,
    Saturation,
    TwoLine,
)
from tests.tolerances import exact, noise_free


def _line(x, m, b):
    return m * x + b


class _FixedGuessLine(FitFunction):
    """A line whose ``p0`` is the class's ``guess``, to exercise the base class."""

    guess = None

    @property
    def function(self):
        return _line

    @property
    def p0(self):
        return self.guess

    @property
    def TeX_function(self):
        return "m x + b"


class _NanGuessLine(_FixedGuessLine):
    guess = [np.nan, 1.0]


class _NoGuessLine(_FixedGuessLine):
    guess = None


# Exact line y = 2x + 1 on distinct x: any start converges to (2, 1).
LINE_X = np.arange(6.0)
LINE_Y = 2.0 * LINE_X + 1.0


def test_nan_in_a_subclass_guess_raises_value_error_naming_class_and_parameter():
    """A ``p0`` holding NaN is refused before scipy, naming the class and ``m``.

    Without the check scipy reports "Initial guess is outside of provided
    bounds", which names neither.

    ON FAILURE: the code is wrong.
    """
    fit = _NanGuessLine(LINE_X, LINE_Y)
    msg = r"^_NanGuessLine initial guess is not finite: m=nan\."
    with pytest.raises(ValueError, match=msg):
        fit.make_fit()
    err = fit.make_fit(return_exception=True)
    assert isinstance(err, ValueError) and "m=nan" in str(err), repr(err)


def test_infinite_caller_p0_raises_value_error_naming_the_parameter():
    """A caller's ``p0=`` holding infinity gets the same check, naming ``b``.

    ON FAILURE: the code is wrong.
    """
    fit = _NoGuessLine(LINE_X, LINE_Y)
    msg = r"^_NoGuessLine initial guess is not finite: b=inf\."
    with pytest.raises(ValueError, match=msg):
        fit.make_fit(p0=[2.0, np.inf])


def test_wrong_length_caller_p0_names_entries_by_position():
    """A caller's ``p0=`` of the wrong length names its bad entry ``p0[i]``.

    Three guesses for the two parameters ``m, b`` cannot be matched to names,
    so the NaN in the second entry is reported as ``p0[1]``.

    ON FAILURE: the code is wrong.
    """
    fit = _NoGuessLine(LINE_X, LINE_Y)
    msg = r"^_NoGuessLine initial guess is not finite: p0\[1\]=nan\."
    with pytest.raises(ValueError, match=msg):
        fit.make_fit(p0=[2.0, np.nan, 1.0])


def test_malformed_bounds_with_no_guess_are_returned_by_the_x0_scan():
    """``GaussianPlusHeavySide`` with ``p0`` None returns, not raises, a bounds error.

    y summing to zero gives ``p0`` None, so ``make_fit`` builds the feasible
    default from ``bounds``. A three-element ``bounds`` is malformed (it must
    be a (lower, upper) pair); with ``return_exception=True`` the resulting
    ValueError comes back, as the base ``make_fit`` documents.

    ON FAILURE: the code is wrong.
    """
    x = np.arange(6.0)
    fit = GaussianPlusHeavySide(x, np.array([1.0, -1, 1, -1, 1, -1]))
    assert fit.p0 is None, fit.p0
    err = fit.make_fit(return_exception=True, bounds=(0.0, 1.0, 2.0))
    assert isinstance(err, ValueError), err


@pytest.mark.parametrize("cls", [Gaussian, GaussianNormalized])
def test_all_weight_at_one_x_gives_no_gaussian_guess(cls):
    """All the weight at x = 2 means zero width: ``p0`` is None.

    A zero width is under half the sample spacing (0.5), so the samples
    cannot resolve it.

    ON FAILURE: the code is wrong.
    """
    p0 = cls(np.array([1.0, 2, 3]), np.array([0.0, 5, 0])).p0
    assert p0 is None, p0


@pytest.mark.parametrize(
    "peak, resolved",
    [
        # Weights [1, 5.9, 1] at x = [0, 1, 2]: variance 2/7.9, width 0.5032.
        pytest.param(5.9, True, id="width-just-above-half-spacing"),
        # Weights [1, 6.1, 1]: variance 2/8.1, width 0.4969.
        pytest.param(6.1, False, id="width-just-below-half-spacing"),
    ],
)
def test_gaussian_width_must_reach_half_the_x_spacing(peak, resolved):
    """A width just above half the spacing (0.5) is estimated; just below is None.

    ON FAILURE: the code is wrong, unless the author moved the threshold.
    """
    p0 = Gaussian(np.array([0.0, 1, 2]), np.array([1.0, peak, 1])).p0
    if resolved:
        # Hand values: mean 1, width sqrt(2 / (2 + peak)), peak.
        expected = [1.0, np.sqrt(2 / (2 + peak)), peak]
        assert p0 == exact(expected), p0
    else:
        assert p0 is None, p0


def test_gaussianln_guess_recovers_the_model_parameters():
    """On data from the model with m = ln 100, s = 0.3, A = 10, ``p0`` is (m, s, A).

    x is 201 points evenly spaced in ln x from ln 10 to ln 1000, symmetric
    about ln 100 and including x = 100, so the y-weighted mean of ln x is m and
    the peak is A. The grid step (0.023) is far below s and the range spans
    +-7.7 s, so the discrete weighted standard deviation equals s to well
    under 1e-6.

    ON FAILURE: the code is wrong, unless the author changed the estimator.
    """
    m, s, A = np.log(100.0), 0.3, 10.0
    x = np.logspace(1, 3, 201)
    y = A * np.exp(-0.5 * ((np.log(x) - m) / s) ** 2)
    p0 = GaussianLn(x, y).p0
    assert p0 == noise_free([m, s, A]), p0


@pytest.mark.parametrize(
    "x, y",
    [
        # Weights sum to 3e308, which overflows to inf.
        pytest.param([1.0, 2, 3], [1e308, 1e308, 1e308], id="total-overflows"),
        # Weights sum to 3e306 (finite), but x * y reaches 3e308, so the mean
        # overflows.
        pytest.param([100.0, 200, 300], [1e306, 1e306, 1e306], id="moment-overflows"),
    ],
)
def test_overflowing_weighted_moments_give_no_gaussian_guess(x, y):
    """Finite data whose weighted sums overflow give ``p0`` None, not NaN or inf.

    Non-finite observations are masked before ``p0``, so overflow is how a
    non-finite moment can still arise.

    ON FAILURE: the code is wrong.
    """
    with np.errstate(over="ignore", invalid="ignore"):
        p0 = Gaussian(np.array(x), np.array(y)).p0
    assert p0 is None, p0


def test_a_none_guess_fits_from_the_feasible_default():
    """``p0`` None still fits: the exact line is recovered and dof counts parameters.

    ON FAILURE: the code is wrong.
    """
    fit = _NoGuessLine(LINE_X, LINE_Y)
    assert fit.make_fit() is None
    assert fit.popt == noise_free({"m": 2.0, "b": 1.0})
    assert fit.dof == LINE_X.size - 2
    assert fit.initial_guess_info is None


def test_a_none_guess_starts_inside_dict_bounds():
    """With bounds excluding the default ones, ``p0`` None starts inside them.

    ``m`` is bounded to [1.5, 5], so a start at m = 1 would be infeasible.

    ON FAILURE: the code is wrong.
    """
    fit = _NoGuessLine(LINE_X, LINE_Y)
    fit.make_fit(bounds={"m": (1.5, 5.0), "b": (-5.0, 5.0)})
    assert fit.popt == noise_free({"m": 2.0, "b": 1.0})


def test_insufficient_data_check_survives_python_O(tmp_path):
    """Under ``python -O`` too, ``p0`` with too little data raises InsufficientDataError.

    The check was an ``assert``, which ``-O`` strips; a Gaussian then guessed
    from two points for three parameters.

    ON FAILURE: the code is wrong.
    """
    script = tmp_path / "probe.py"
    script.write_text(
        "import numpy as np\n"
        "from solarwindpy.fitfunctions.core import InsufficientDataError\n"
        "from solarwindpy.fitfunctions.gaussians import Gaussian\n"
        "try:\n"
        "    Gaussian(np.array([0.0, 1.0]), np.array([1.0, 2.0])).p0\n"
        "except InsufficientDataError:\n"
        "    print('raised')\n"
        "else:\n"
        "    print('no error')\n"
    )
    root = Path(solarwindpy.__file__).resolve().parents[1]
    out = subprocess.run(
        [sys.executable, "-O", str(script)],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(root), "PATH": ""},
        check=True,
    )
    assert out.stdout.strip() == "raised", out.stdout + out.stderr


def _case(cls, x, y, kwargs, *rest, id):
    return pytest.param(cls, np.array(x), np.array(y), kwargs, *rest, id=id)


# Inputs for which each family's estimate is impossible, and why.
IMPOSSIBLE = [
    # y sums to zero: no weighted mean.
    _case(Gaussian, [0.0, 1, 2, 3], [1.0, -1, 1, -1], {}, id="Gaussian"),
    _case(GaussianNormalized, [0.0, 1, 2, 3], [1.0, -1, 1, -1], {}, id="GaussianNorm"),
    # Weighted mean -2 has no logarithm.
    _case(GaussianLn, [-3.0, -2, -1], [1.0, 2, 1], {}, id="GaussianLn"),
    # No data above guess_x0 = 20.
    _case(
        HeavySide, [0.0, 1, 2, 3, 4], [5.0, 5, 5, 2, 2], {"guess_x0": 20.0}, id="Step"
    ),
    # y sums to zero: no weighted mean.
    _case(
        GaussianPlusHeavySide,
        [0.0, 1, 2, 3, 4, 5],
        [1.0, -1, 1, -1, 1, -1],
        {},
        id="GaussianPlusHeavySide",
    ),
    # No data above guess_x0 = 20 (was "There is no maximum of a zero-size array").
    _case(
        GaussianTimesHeavySide,
        [0.0, 1, 2, 3, 4],
        [1.0, 2, 3, 2, 1],
        {"guess_x0": 20.0},
        id="GaussianTimesHeavySide",
    ),
    # No data at or below guess_x0 = -1: no level y1.
    _case(
        GaussianTimesHeavySidePlusHeavySide,
        [0.0, 1, 2, 3, 4, 5],
        [1.0, 2, 3, 2, 1, 0.5],
        {"guess_x0": -1.0},
        id="GaussianTimesHeavySidePlusHeavySide",
    ),
    # Default xs = 425 leaves no data on the upper side: no slope.
    _case(TwoLine, [0.0, 1, 2, 3, 4, 5], [0.0, 1, 2, 2, 1, 0], {}, id="TwoLine"),
    _case(Saturation, [0.0, 1, 2, 3, 4, 5], [0.0, 1, 2, 2, 1, 0], {}, id="Saturation"),
    # Plateau x = [3, 3, 4] repeats x with a rise: slope inf.
    _case(
        HingeSaturation,
        [0.0, 1, 2, 3, 3, 4],
        [0.0, 1, 2, 2, 2.5, 2.5],
        {"guess_xh": 2.5, "guess_yh": 2.0},
        id="HingeSaturation",
    ),
    # Flat plateau: zero slope, so no x-intercept x2.
    _case(
        HingeMin, [0.0, 1, 2, 3, 4, 5], [0.0, 1, 2, 2, 2, 2], {"guess_h": 2.5}, id="Min"
    ),
    _case(
        HingeMax, [0.0, 1, 2, 3, 4, 5], [0.0, 1, 2, 2, 2, 2], {"guess_h": 2.5}, id="Max"
    ),
    # Lower side x = [0, 0, 1] repeats x with a rise: slope inf.
    _case(
        HingeAtPoint,
        [0.0, 0, 1, 3, 4, 5],
        [0.0, 1, 2, 2, 1, 0],
        {"guess_xh": 2.5, "guess_yh": 2.0},
        id="HingeAtPoint",
    ),
]


# The author's reference hinge, translated by hand into each hinge class's
# parameters: (xh, yh) = (433, 4.12), x-intercept x1 = 250, m1 = 4.12 / 183,
# m2 = 0.01 m1, and the plateau line's x-intercept x2 = 433 - 4.12 / m2,
# which is 433 - 100 * 183 = -17867.
M1 = 4.12 / 183
M2 = 0.01 * M1
HINGE_START = {
    HingeSaturation: [433.0, 4.12, 250.0, M2],
    TwoLine: [250.0, -17867.0, M1, M2],
    # theta = arctan(m1) - arctan(m2) inverts m2 = tan(arctan(m1) - theta).
    Saturation: [250.0, 433.0, 4.12, np.arctan(M1) - np.arctan(M2)],
    HingeMin: [M1, 250.0, -17867.0, 433.0],
    HingeAtPoint: [433.0, 4.12, M1, M2],
}


def _start(cls, n):
    """The start a None-p0 fit of ``cls`` should use: its hinge point, or ones."""
    return np.array(HINGE_START.get(cls, np.ones(n)))


@pytest.mark.parametrize("cls, x, y, kwargs", IMPOSSIBLE)
def test_impossible_estimate_gives_none_and_fits_from_the_fallback_start(
    cls, x, y, kwargs
):
    """An input with no estimate gives ``p0`` None, and the fit starts from the fallback.

    The fallback is the author's hinge point for the hinge classes and ones
    (the feasible default for unbounded parameters) otherwise. The fit with
    ``p0`` None must end exactly as the fit given that start as ``p0=``, and is
    never refused with the non-finite-guess ValueError. Whether the start
    converges is scipy's business: all ones is singular for GaussianLn on
    negative x, and scipy then reports "Residuals are not finite in the initial
    point" on both routes alike. The hinge start is finite everywhere, so the
    hinge fits never report that. HingeMax has no start yet and returns
    NotImplementedError.

    ON FAILURE: the code is wrong.
    """
    fit = cls(x, y, **kwargs)
    assert fit.p0 is None, fit.p0

    got = fit.make_fit(return_exception=True)
    if cls is HingeMax:
        assert isinstance(got, NotImplementedError), got
        return

    explicit = cls(x, y, **kwargs)
    expected = explicit.make_fit(
        return_exception=True, p0=_start(cls, len(fit.argnames))
    )
    assert "initial guess is not finite" not in str(got), got
    assert type(got) is type(expected), (got, expected)
    assert str(got) == str(expected), (got, expected)
    if cls in HINGE_START:
        assert "Residuals are not finite" not in str(got), got
    if got is None:
        # Same start, same solver: identical results.
        assert fit.popt == explicit.popt


@pytest.mark.parametrize("cls", list(HINGE_START), ids=lambda c: c.__name__)
def test_hinge_fallback_start_is_the_authors_point(cls):
    """Each hinge class's ``fallback_p0`` is the hand-translated author's point.

    The model evaluated there on x from 0 to 1000 is finite everywhere.

    ON FAILURE: the code is wrong, unless the author moved the reference hinge.
    """
    fit = cls(np.arange(6.0), np.arange(6.0))
    start = fit.fallback_p0()
    assert start == exact(HINGE_START[cls]), start
    with np.errstate(divide="raise", invalid="raise"):
        values = fit.function(np.linspace(0.0, 1000.0, 101), *start)
    assert np.all(np.isfinite(values)), values


def test_hingemax_has_no_fallback_start_yet():
    """``HingeMax.fallback_p0`` raises NotImplementedError until a point is chosen.

    ON FAILURE: (unexpected pass) a HingeMax start has landed; update this test.
    """
    fit = HingeMax(np.arange(6.0), np.arange(6.0))
    with pytest.raises(NotImplementedError, match="no default start defined yet"):
        fit.fallback_p0()


S = np.sqrt(0.5)
# Hand cases: x = [1, 2, 3] weighted by y = [1, 2, 1] has mean 2 and variance 0.5.
NORMAL = [
    _case(Gaussian, [1.0, 2, 3], [1.0, 2, 1], {}, [2.0, S, 2.0], id="Gaussian"),
    # n = peak * sigma * sqrt(2 pi) = 2 sqrt(0.5) sqrt(2 pi) = 2 sqrt(pi).
    _case(
        GaussianNormalized,
        [1.0, 2, 3],
        [1.0, 2, 1],
        {},
        [2.0, S, 2 * np.sqrt(np.pi)],
        id="GaussianNormalized",
    ),
    # ln x = [0, 1, 2] weighted by [1, 2, 1]: m = 1, s = sqrt(0.5), and A is
    # the peak y, 2, not logged.
    _case(
        GaussianLn,
        np.exp([0.0, 1, 2]),
        [1.0, 2, 1],
        {},
        [1.0, S, 2.0],
        id="GaussianLn",
    ),
    # x0 = midpoint 2; median y above is 2, below is 5, so y1 = 3.
    _case(
        HeavySide, [0.0, 1, 2, 3, 4], [5.0, 5, 5, 2, 2], {}, [2.0, 2.0, 3.0], id="Step"
    ),
    # Weighted mean (3 + 8 + 10 + 6) / 6 = 4.5 (variance 11/12) gives x0 = 3.375
    # and y1 = 0.8 * 2; above x0, x = [4, 5, 6] weighted by [2, 2, 1] has mean
    # 24/5 and variance 2.8/5 = 0.56, a width 0.75 above half the spacing 0.5.
    _case(
        GaussianPlusHeavySide,
        [1.0, 2, 3, 4, 5, 6],
        [0.0, 0, 1, 2, 2, 1],
        {},
        [3.375, 0.0, 1.6, 4.8, np.sqrt(0.56), 2.0],
        id="GaussianPlusHeavySide",
    ),
    # Above x0 = 0.5 the data are the [1, 2, 1] case.
    _case(
        GaussianTimesHeavySide,
        [0.0, 1, 2, 3],
        [7.0, 1, 2, 1],
        {"guess_x0": 0.5},
        [0.5, 2.0, S, 2.0],
        id="GaussianTimesHeavySide",
    ),
    # y1 is the mean y at or below x0 = 1.5, which is 7; above x0, x = [2, 3, 4]
    # weighted by [1, 2, 1] has mean 3 and variance 0.5.
    _case(
        GaussianTimesHeavySidePlusHeavySide,
        [0.0, 1, 2, 3, 4],
        [7.0, 7, 1, 2, 1],
        {"guess_x0": 1.5},
        [1.5, 7.0, 3.0, S, 2.0],
        id="GaussianTimesHeavySidePlusHeavySide",
    ),
    # Below 2.5: y = x, so m1 = 1, x1 = 0. Above: y = 5 - x, so m2 = -1, x2 = 5.
    _case(
        TwoLine,
        [0.0, 1, 2, 3, 4, 5],
        [0.0, 1, 2, 2, 1, 0],
        {"guess_xs": 2.5},
        [0.0, 5.0, 1.0, -1.0],
        id="TwoLine",
    ),
    _case(
        HingeMin,
        [0.0, 1, 2, 3, 4, 5],
        [0.0, 1, 2, 2, 1, 0],
        {"guess_h": 2.5},
        [1.0, 0.0, 5.0, 2.5],
        id="HingeMin",
    ),
    # yh is y at the x nearest 2.5 (the first of the tie, x = 2).
    _case(
        HingeAtPoint,
        [0.0, 1, 2, 3, 4, 5],
        [0.0, 1, 2, 2, 1, 0],
        {"guess_xh": 2.5, "guess_yh": 9.0},
        [2.5, 2.0, 1.0, -1.0],
        id="HingeAtPoint",
    ),
]


@pytest.mark.parametrize("cls, x, y, kwargs, expected", NORMAL)
def test_normal_input_estimate_matches_hand_calculation(cls, x, y, kwargs, expected):
    """On an ordinary input each family's ``p0`` is the hand-computed estimate.

    ON FAILURE: the code is wrong, unless the author changed the estimator.
    """
    p0 = cls(x, y, **kwargs).p0
    assert p0 == exact(expected), p0


def test_insufficient_data_still_raises_from_p0():
    """Two points for a three-parameter model: ``p0`` raises InsufficientDataError.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(InsufficientDataError, match="insufficient data"):
        HeavySide(np.array([0.0, 1.0]), np.array([1.0, 2.0])).p0
