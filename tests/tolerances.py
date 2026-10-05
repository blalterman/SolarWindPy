# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
"""The tolerance rule for SolarWindPy tests.

Every approximate comparison in ``tests/`` that sets a tolerance goes through
one of the functions here; ``tests/test_tolerance_rule.py`` fails when a test
file writes a tolerance keyword of its own. Each function names a kind of
comparison and carries the reason for its tolerance, so a test line states
only where its expected value comes from.

The comparators return ``pytest.approx`` objects, used as
``assert actual == exact(expected)``. Compare pandas objects as numpy arrays
(``series.to_numpy() == exact(...)``): pandas does not defer ``==`` to
``pytest.approx``.

Pass ``nan_ok=True`` where NaN is a correct expected value; a NaN then matches
only a NaN.
"""

import numpy as np
import pytest

#: Relative tolerance of :func:`exact`.
EXACT_REL = 1e-12

#: Relative tolerance of :func:`noise_free`.
NOISE_FREE_REL = 1e-6

#: Error bars allowed by :func:`assert_within_error_bars`.
ERROR_BARS = 4

#: Decimal places to which two CODATA routes to one quantity agree, for
#: ``printed(actual / expected, ...)``. CODATA 2022 (the table scipy >= 1.16
#: carries) prints every mass, mass ratio and electromagnetic constant to at
#: least 11 significant digits, so a quantity formed from the alpha mass and
#: one formed from the alpha/proton mass ratio times m_p agree to 10 decimal
#: places in their ratio, not to float rounding.
CODATA_JOINT_DECIMALS = 10


def exact(expected, *, scale=0.0, nan_ok=False):
    """Compare to a value the test knows exactly.

    For exact SI constants and identities, published values the package stores
    as printed, and values recomputed from chosen inputs by the same or
    reordered float64 arithmetic.

    Tolerance ``rel=1e-12``: thousands of float64 roundings (1.1e-16 each) stay
    inside it, while a wrong coefficient, unit or dropped term moves a result
    by far more.

    Parameters
    ----------
    expected : float, array-like, or mapping
        The known value.
    scale : float, optional
        Magnitude of the terms that combine to give an expected zero. A
        relative tolerance accepts nothing but an exact 0, so the absolute
        tolerance becomes ``1e-12 * scale``. Leave it 0 otherwise:
        ``pytest.approx``'s default absolute margin of 1e-12 accepts any wrong
        value of order 1e-34.
    nan_ok : bool, optional
        NaN in ``expected`` matches NaN.
    """
    return pytest.approx(expected, rel=EXACT_REL, abs=EXACT_REL * scale, nan_ok=nan_ok)


def printed(expected, *, decimals, nan_ok=False):
    """Compare to a value a source prints to ``decimals`` decimal places.

    For published or hand-computed values the package computes rather than
    stores. Tolerance is half the last printed digit,
    ``abs=0.5 * 10**-decimals`` with ``rel=0``: a correctly rounded printed
    value is never further than that from the true one, and a computation that
    disagrees with the source in a printed digit fails.

    The rule holds on a logarithmic scale too: a source printing log10 values
    to ``d`` decimal places is compared in log10 with ``decimals=d``.

    Parameters
    ----------
    expected : float or array-like
        The value as printed.
    decimals : int
        Decimal places printed by the source; negative for a value printed to
        tens, hundreds, and so on.
    nan_ok : bool, optional
        NaN in ``expected`` matches NaN.
    """
    return pytest.approx(expected, rel=0, abs=0.5 * 10.0**-decimals, nan_ok=nan_ok)


def noise_free(expected, *, scale=0.0, nan_ok=False):
    """Compare to a parameter or curve a fit recovers from noise-free data.

    Tolerance ``rel=1e-6``: far above the optimizer's convergence threshold,
    far below any real bug in how the fit wrappers pass data, weights and
    parameters to scipy. scipy owns fit accuracy.

    Parameters
    ----------
    expected : float, array-like, or mapping
        The value the data were generated from.
    scale : float, optional
        Magnitude of the data, for an expected zero (a residual, an error bar,
        a zero slope): the absolute tolerance becomes ``1e-6 * scale``.
    nan_ok : bool, optional
        NaN in ``expected`` matches NaN.
    """
    return pytest.approx(
        expected, rel=NOISE_FREE_REL, abs=NOISE_FREE_REL * scale, nan_ok=nan_ok
    )


def assert_within_error_bars(estimate, error, truth, *, n=ERROR_BARS):
    """Assert a noisy estimate lies within four error bars of the truth.

    For fits to noisy data with a fixed seed, and for sample statistics: each
    quantity must satisfy ``|estimate - truth| <= 4 * error``. Four error bars
    pass for almost any seed, not only a lucky one (a two-sided Gaussian
    false-alarm rate of 6e-5 per quantity, near 1 in 4000 jointly for four
    parameters), while a wrapper that mishandles data or weights moves a
    parameter by many error bars.

    Parameters
    ----------
    estimate, error, truth : float, array-like, or mapping
        The estimate, its one-sigma uncertainty, and the true value. Mappings
        (``popt``, ``psigma``) are compared key by key over ``truth``'s keys.
    n : float, optional
        Error bars allowed. Keep the default unless a source justifies another.

    Raises
    ------
    AssertionError
        Naming each quantity outside ``n`` error bars.
    """
    if hasattr(truth, "keys"):
        rows = [(k, estimate[k], error[k], truth[k]) for k in truth.keys()]
    else:
        est, err, tru = np.broadcast_arrays(
            np.asarray(estimate, dtype=float),
            np.asarray(error, dtype=float),
            np.asarray(truth, dtype=float),
        )
        rows = list(zip(range(est.size), est.flat, err.flat, tru.flat))

    misses = [
        f"{k}: |{e!r} - {t!r}| = {abs(e - t)!r} > {n} x {s!r}"
        for k, e, s, t in rows
        if not abs(e - t) <= n * s
    ]
    assert not misses, "outside error bars: " + "; ".join(misses)
