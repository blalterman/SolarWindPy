"""Weighted residuals, Jacobians, feasible starts and covariances for least squares.

:meth:`solarwindpy.fitfunctions.core.FitFunction.make_fit` minimizes with
:func:`scipy.optimize.least_squares` and follows the conventions of
:func:`scipy.optimize.curve_fit`: a 1-d ``sigma`` weights each residual by
``1 / sigma``, and the parameter covariance is the pseudo-inverse of
``J^T J``. These helpers are written from the behavior described in the
NumPy and SciPy public documentation.
"""

import numpy as np
from scipy.linalg import svd

# Private to fitfunctions: no public names.
__all__ = []


def weighted_residual(function, xdata, ydata, sigma):
    """Build a residual callable for ``scipy.optimize.least_squares``.

    Parameters
    ----------
    function : callable
        Model, called as ``function(xdata, *params)``; returns a 1-d array
        with the same length as ``ydata``.
    xdata : array_like
        Independent variable passed to ``function``.
    ydata : array_like
        Observed values, 1-d.
    sigma : array_like or None
        Per-point uncertainties, 1-d with the same length as ``ydata``.
        ``None`` means unweighted residuals.

    Returns
    -------
    residual : callable
        ``residual(params)`` returns ``function(xdata, *params) - ydata``,
        multiplied by ``1 / sigma`` when ``sigma`` is given.
    """
    if sigma is None:

        def residual(params):
            return function(xdata, *params) - ydata

    else:
        weights = 1.0 / np.asarray(sigma)

        def residual(params):
            return weights * (function(xdata, *params) - ydata)

    return residual


def weighted_jacobian(jac, xdata, sigma):
    """Build a Jacobian callable for ``least_squares``'s ``jac`` argument.

    Parameters
    ----------
    jac : callable
        Model Jacobian, called as ``jac(xdata, *params)``; returns a 2-d
        array of shape (n_points, n_params).
    xdata : array_like
        Independent variable passed to ``jac``.
    sigma : array_like or None
        Per-point uncertainties, 1-d of length n_points. ``None`` means
        the Jacobian is not weighted.

    Returns
    -------
    jacobian : callable
        ``jacobian(params)`` returns the model Jacobian as a 2-d array, with
        each row scaled by ``1 / sigma`` of its point when ``sigma`` is given.
    """
    if sigma is None:

        def jacobian(params):
            return np.atleast_2d(jac(xdata, *params))

    else:
        weights = 1.0 / np.asarray(sigma)

        def jacobian(params):
            return weights[:, np.newaxis] * np.asarray(jac(xdata, *params))

    return jacobian


def feasible_start(lb, ub):
    """Choose a starting parameter vector inside the given bounds.

    Parameters
    ----------
    lb : numpy.ndarray
        Lower bounds, 1-d float array; entries may be ``-np.inf``.
    ub : numpy.ndarray
        Upper bounds, 1-d float array of the same length; entries may be
        ``np.inf``.

    Returns
    -------
    p0 : numpy.ndarray
        Float array: the midpoint where both bounds are finite, ``lb + 1``
        where only the lower bound is finite, ``ub - 1`` where only the
        upper bound is finite, and ``1`` where neither is finite.
    """
    lb = np.asarray(lb, dtype=float)
    ub = np.asarray(ub, dtype=float)
    p0 = np.ones_like(lb, dtype=float)

    lb_finite = np.isfinite(lb)
    ub_finite = np.isfinite(ub)

    both = lb_finite & ub_finite
    lower_only = lb_finite & ~ub_finite
    upper_only = ~lb_finite & ub_finite

    p0[both] = 0.5 * (lb[both] + ub[both])
    p0[lower_only] = lb[lower_only] + 1
    p0[upper_only] = ub[upper_only] - 1
    return p0


def pseudo_inverse_covariance(jac_at_solution):
    """Pseudo-inverse of ``J^T J`` computed from the SVD of ``J``.

    Parameters
    ----------
    jac_at_solution : numpy.ndarray
        Weighted Jacobian ``J`` at the solution, 2-d of shape (m, n).

    Returns
    -------
    cov : numpy.ndarray
        The (n, n) Moore-Penrose pseudo-inverse of ``J^T J``. Singular
        values at or below ``eps * max(m, n) * s_max`` are discarded.
    """
    _, s, VT = svd(jac_at_solution, full_matrices=False)
    threshold = np.finfo(float).eps * max(jac_at_solution.shape) * s[0]
    s = s[s > threshold]
    VT = VT[: s.size]
    return np.dot(VT.T / s**2, VT)
