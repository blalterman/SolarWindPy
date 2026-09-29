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

from solarwindpy.fitfunctions import (
    GaussianPlusHeavySide,
    InsufficientDataError,
    Line,
    LineXintercept,
)


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
    assert Line(LINE_X, LINE_Y).p0 == pytest.approx([2.0, 1.0], rel=1e-12, abs=0)


def test_line_x_intercept_p0_is_slope_and_x_intercept_of_exact_line():
    """``LineXintercept.p0`` on exact ``y = 2x + 1`` data is ``[2, -0.5]``.

    ``y = m (x - x0)`` with ``m = 2`` and ``x0 = -b/m = -1/2``. The intercept
    sign error in the old guess made ``x0`` come out as ``+0.5``.

    ON FAILURE: the code is wrong.
    """
    p0 = LineXintercept(LINE_X, LINE_Y).p0
    assert p0 == pytest.approx([2.0, -0.5], rel=1e-12, abs=0)


def test_trend_fit_popt1d_keys_survive_pickle_round_trip():
    """``TrendFit.popt1d_keys`` pickles and unpickles to an equal value.

    Its namedtuple was created with typename ``"Popt1Dkeys"`` but bound to
    ``Popt1DKeys``, so pickle's lookup of the class by name failed.

    ON FAILURE: the code is wrong, unless a test earlier in the run deleted
    ``solarwindpy`` modules from ``sys.modules`` after this import resolved.
    """
    # Resolve at call time: tests/test_circular_imports.py drops and re-imports
    # every solarwindpy module, and pickle requires the class in sys.modules.
    from solarwindpy.fitfunctions import Line, TrendFit

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
    # Noise-free fit: rel=1e-6 is far above optimizer convergence, far below a bug.
    assert fit.popt == pytest.approx({"m": 2.0, "b": 1.0}, rel=1e-6, abs=0)
