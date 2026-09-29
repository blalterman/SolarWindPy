# Spent-When: PERMANENT(solarwindpy.fitfunctions drops GaussianPlusHeavySide)
# Supersedes: none
"""Defects fixed in ``solarwindpy.fitfunctions`` source, each with its test.

``GaussianPlusHeavySide`` never moved ``x0``: the Heaviside term is flat in
``x0`` between samples, so a gradient-based optimizer returned the initial
guess. The model is evaluated only at the samples, so every ``x0`` strictly
between the same two neighbouring samples fits equally well. The recoverable
claim is therefore "the fitted step lies between the two samples that bracket
the true step", and that is what these tests assert.
"""

import numpy as np
import pytest

from solarwindpy.fitfunctions import GaussianPlusHeavySide, InsufficientDataError


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
