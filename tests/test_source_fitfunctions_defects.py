# Spent-When: PERMANENT(solarwindpy.fitfunctions drops GaussianPlusHeavySide)
# Supersedes: none
"""Defects fixed in ``solarwindpy.fitfunctions`` source, each with its test.

``GaussianPlusHeavySide`` never moved ``x0``: the Heaviside term is flat in
``x0`` between samples, so a gradient-based optimizer returned the initial
guess. The model is evaluated only at the samples, so every ``x0`` strictly
between the same two neighbouring samples fits equally well. The recoverable
claim is therefore "the fitted step lies between the two samples that bracket
the true step", and that is what those tests assert.
"""

import pickle

import numpy as np
import pandas as pd
import pytest

from solarwindpy.fitfunctions.composite import GaussianPlusHeavySide
from solarwindpy.fitfunctions.core import InsufficientDataError
from solarwindpy.fitfunctions.lines import Line, LineXintercept
from tests.tolerances import exact, noise_free


def _model(x, x0, y0, y1, mu, sigma, A):
    """Gaussian plus a step of height ``y1`` below ``x0``, written independently."""
    return A * np.exp(-0.5 * ((x - mu) / sigma) ** 2) + y1 * (x < x0) + y0


def _bracket(x, x0):
    """Return the neighbouring samples ``(lo, hi)`` with ``lo < x0 < hi``."""
    return x[x < x0].max(), x[x > x0].min()


# Step positions chosen off the sample grid (spacing 10/199), so the true step
# falls strictly between two samples and its bracket is unambiguous.
PARAMS = [
    {"x0": 2.0, "y0": 1.0, "y1": 3.0, "mu": 5.0, "sigma": 1.0, "A": 4.0},
    {"x0": 4.0, "y0": 0.5, "y1": 2.0, "mu": 6.0, "sigma": 0.8, "A": 3.0},
    {"x0": 1.0, "y0": 2.0, "y1": 1.0, "mu": 4.0, "sigma": 1.5, "A": 5.0},
]


@pytest.mark.parametrize("true", PARAMS, ids=["x0=2", "x0=4", "x0=1"])
def test_gaussian_plus_heavyside_fits_x0_between_bracketing_samples(true):
    """Noise-free data: fitted ``x0`` lies between the samples bracketing the truth.

    The expected interval comes from the input grid and the chosen ``x0``.
    Before the fix, ``x0`` stayed at ``p0``'s ``0.75 * weighted mean`` (about
    3.05 for the first case), outside every bracket here.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(0, 10, 200)
    y = _model(x, **true)

    fit = GaussianPlusHeavySide(x, y)
    fit.make_fit()

    lo, hi = _bracket(x, true["x0"])
    assert lo < fit.popt["x0"] < hi


def test_gaussian_plus_heavyside_fits_x0_between_bracketing_samples_with_noise():
    """Noisy data (fixed seed): fitted ``x0`` still lies in the true bracket.

    The step height ``y1 = 3`` is 20 noise standard deviations (0.15), so
    assigning even one sample to the wrong side of the step raises the cost by
    about ``y1**2``, far more than the noise can offset.

    ON FAILURE: the code is wrong.
    """
    true = PARAMS[0]
    rng = np.random.default_rng(42)
    x = np.linspace(0, 10, 200)
    y = _model(x, **true) + rng.normal(0, 0.15, x.size)

    fit = GaussianPlusHeavySide(x, y)
    fit.make_fit()

    lo, hi = _bracket(x, true["x0"])
    assert lo < fit.popt["x0"] < hi


def test_gaussian_plus_heavyside_returns_insufficient_data_error():
    """Fewer samples than parameters: ``make_fit(return_exception=True)`` returns it.

    Six parameters and three samples; the scan over ``x0`` must not run first
    and fail differently.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 2.0, 3.0])
    fit = GaussianPlusHeavySide(x, x)

    assert isinstance(fit.make_fit(return_exception=True), InsufficientDataError)


def _x0_bounds(lo, hi):
    """Bounds dict that limits only ``x0`` (and keeps ``sigma`` positive)."""
    free = (-np.inf, np.inf)
    return {
        "x0": (lo, hi),
        "y0": free,
        "y1": free,
        "mu": free,
        "sigma": (0.0, np.inf),
        "A": free,
    }


@pytest.mark.parametrize(
    "lo,hi,expect_lo,expect_hi",
    [
        # Bounds hold the true step (x0 = 2) but exclude p0's x0 (about 3.05):
        # the fit lands in the true step's bracket on the sample grid.
        (1.5, 2.5, *_bracket(np.linspace(0, 10, 200), 2.0)),
        # Bounds far from the step: every gap outside them is infeasible, so
        # the fitted x0 is the best feasible gap, inside the caller's bounds.
        (8.0, 9.0, 8.0, 9.0),
    ],
    ids=["bounds-hold-step", "bounds-exclude-step"],
)
def test_gaussian_plus_heavyside_scan_respects_caller_x0_bounds(
    lo, hi, expect_lo, expect_hi
):
    """A caller's ``x0`` bounds confine the gap scan, so the refit stays feasible.

    Gap midpoints outside the bounds must be skipped by the scan; if one were
    chosen, the final refit would start outside the bounds and fail.

    ON FAILURE: the code is wrong.
    """
    true = PARAMS[0]
    x = np.linspace(0, 10, 200)
    y = _model(x, **true)

    fit = GaussianPlusHeavySide(x, y)
    assert fit.make_fit(return_exception=True, bounds=_x0_bounds(lo, hi)) is None
    assert expect_lo < fit.popt["x0"] < expect_hi


def test_gaussian_plus_heavyside_replaces_the_x0_of_a_caller_p0():
    """A caller's ``p0`` seeds the other parameters; its ``x0`` is replaced by the scan.

    The supplied ``x0 = 9.5`` sits far from the true step at 2. The optimizer
    cannot move ``x0`` (zero gradient between samples), so a fit that kept it
    would report 9.5; the documented scan puts it in the true bracket.

    ON FAILURE: the code is wrong.
    """
    true = PARAMS[0]
    x = np.linspace(0, 10, 200)
    y = _model(x, **true)

    fit = GaussianPlusHeavySide(x, y)
    fit.make_fit(p0=[9.5, 1.0, 3.0, 5.0, 1.0, 4.0])

    lo, hi = _bracket(x, true["x0"])
    assert lo < fit.popt["x0"] < hi


def test_gaussian_plus_heavyside_with_a_single_x_starts_from_the_default():
    """All samples at one ``x``: no width estimate, so the fit starts from ones.

    One distinct ``x`` cannot resolve any Gaussian width, so ``p0`` is None
    rather than the zero-width guess that gave non-finite residuals. With no
    gaps the scan has no candidate, and the fit runs from the feasible
    default: it ends exactly as a fit given ``p0=`` ones.

    ON FAILURE: the code is wrong, unless the author changed the zero-width
    rule in ``_weighted_moments``.
    """
    x = np.full(20, 3.0)
    y = np.linspace(1.0, 2.0, x.size)
    fit = GaussianPlusHeavySide(x, y)
    assert fit.p0 is None, fit.p0

    explicit = GaussianPlusHeavySide(x, y)
    expected = explicit.make_fit(return_exception=True, p0=np.ones(6))
    result = fit.make_fit(return_exception=True)
    assert type(result) is type(expected), (result, expected)
    assert str(result) == str(expected), (result, expected)
    assert "Residuals are not finite" not in str(result), result


# y = 2x + 1 on integer x: slope 2, intercept 1, x-intercept -1/2, all exact
# in floating point, so the initial guesses are compared exactly.
LINE_X = np.arange(10.0)
LINE_Y = 2.0 * LINE_X + 1.0


def test_line_p0_is_slope_and_intercept_of_exact_line():
    """``Line.p0`` on exact ``y = 2x + 1`` data is ``[2, 1]``.

    Before the fix the intercept guess was ``median(m*x - y)``, which is
    ``-b``, so ``p0`` was ``[2, -1]``.

    ON FAILURE: the code is wrong.
    """
    assert Line(LINE_X, LINE_Y).p0 == exact([2.0, 1.0])


def test_line_x_intercept_p0_is_slope_and_x_intercept_of_exact_line():
    """``LineXintercept.p0`` on exact ``y = 2x + 1`` data is ``[2, -0.5]``.

    ``y = m (x - x0)`` with ``m = 2`` and ``x0 = -b/m = -1/2``. The intercept
    sign error in the old guess made ``x0`` come out as ``+0.5``.

    ON FAILURE: the code is wrong.
    """
    p0 = LineXintercept(LINE_X, LINE_Y).p0
    assert p0 == exact([2.0, -0.5])


def test_trend_fit_popt1d_keys_survive_pickle_round_trip():
    """``TrendFit.popt1d_keys`` pickles and unpickles to an equal value.

    Its namedtuple was created with typename ``"Popt1Dkeys"`` but bound to
    ``Popt1DKeys``, so pickle's lookup of the class by name failed.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.fitfunctions.lines import Line
    from solarwindpy.fitfunctions.trend_fits import TrendFit

    agged = pd.DataFrame(
        {0: [1.0, 2.0, 3.0], 1: [2.0, 3.0, 4.0]},
        index=pd.interval_range(0, 3, periods=3),
    )
    keys = TrendFit(agged, Line, ykey1d="mu", wkey1d="sigma").popt1d_keys

    assert pickle.loads(pickle.dumps(keys)) == ("mu", "sigma")


def test_line_fits_exact_data_when_repeated_x_defeats_the_initial_guess():
    """A repeated ``x`` makes ``Line.p0`` return ``None``; the fit still recovers the line.

    ``make_fit`` falls back to a default starting point when ``p0`` is
    ``None``. It used to import ``getargspec_no_self`` from SciPy's private
    ``scipy._lib._util``, which current SciPy no longer has, so the fit raised
    ``ImportError`` even with ``return_exception=True``.

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 1.0, 1.0, 2.0, 3.0, 4.0])
    fit = Line(x, 2.0 * x + 1.0)
    assert fit.p0 is None  # the input exists to exercise this branch

    assert fit.make_fit(return_exception=True) is None
    assert fit.popt == noise_free({"m": 2.0, "b": 1.0})
