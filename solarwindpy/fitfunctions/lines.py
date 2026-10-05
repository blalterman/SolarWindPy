#!/usr/bin/env python
r"""Simple linear fit functions.

This module defines :class:`~solarwindpy.fitfunctions.core.FitFunction`
subclasses for straight-line models.  They are primarily used for
quick trend estimation and serve as basic examples of the
FitFunction interface.
"""

__all__ = [
    "Line",
    "LineXintercept",
]

import numpy as np

from .core import FitFunction


def _median_slope_intercept(fitfunction):
    r"""Estimate a line's slope and intercept from the used observations.

    The slope is the median of the slopes between consecutive points and the
    intercept the median of ``y - m x``. The x-steps are checked before any
    division, so repeated or non-finite ``x`` returns ``None`` without a
    divide-by-zero warning.

    Parameters
    ----------
    fitfunction : FitFunction
        The fit function whose used observations are estimated from.

    Returns
    -------
    tuple of float or None
        ``(m, b)``, or ``None`` if the slope cannot be estimated.
    """
    assert fitfunction.sufficient_data

    x = fitfunction.observations.used.x
    y = fitfunction.observations.used.y
    dx = np.ediff1d(x)

    if not (np.all(np.isfinite(dx)) and np.all(np.abs(dx) > 0)):
        fitfunction.logger.warning(
            f"Slope estimate failed (dx = {dx}).\nReturning None."
        )
        return None

    m = np.median(np.ediff1d(y) / dx)
    b = np.median(y - (m * x))
    return m, b


class Line(FitFunction):
    """Linear fit function for straight line relationships.

    Fits data to the form: y = m*x + b
    """

    def __init__(self, xobs, yobs, **kwargs):
        # Docstring inherited from FitFunction
        super().__init__(xobs, yobs, **kwargs)

    @property
    def function(self):
        def line(x, m, b):
            return (m * x) + b

        return line

    @property
    def p0(self):
        r"""Calculate the initial guess for the line parameters.

        If the slope cannot be estimated (non-finite or repeated ``x``),
        return ``None``, which :func:`scipy.optimize.curve_fit` also takes to mean
        no initial guess.

        Returns
        -------
        p0 : list or None
            The initial guesses as [m, b].
        """
        estimate = _median_slope_intercept(self)
        if estimate is None:
            return None

        m, b = estimate
        return [m, b]

    @property
    def TeX_function(self):
        TeX = r"f(x)=m \cdot x + b"
        return TeX

    @property
    def x_intercept(self):
        """Calculate the x-intercept of the fitted line.

        Returns
        -------
        float
            The x value where the line crosses y=0.
        """
        return -self.popt["b"] / self.popt["m"]


class LineXintercept(FitFunction):
    """Linear fit with explicit x-intercept parameterization.

    Fits data to the form: y = m * (x - x0)
    where x0 is the x-intercept.
    """

    def __init__(self, xobs, yobs, **kwargs):
        """Initialize linear fit with x-intercept parameterization.

        Notes
        -----
        This parameterization is useful when fitting data where the
        x-intercept has physical meaning, such as threshold energies
        or cutoff velocities in solar wind measurements.
        """
        super().__init__(xobs, yobs, **kwargs)

    @property
    def function(self):
        def line(x, m, x0):
            return m * (x - x0)

        return line

    @property
    def p0(self):
        r"""Calculate the initial guess for the line parameters.

        If the slope cannot be estimated (non-finite or repeated ``x``), or
        the estimated slope is zero (a flat line has no x-intercept), return
        ``None``, which :func:`scipy.optimize.curve_fit` also takes to mean no
        initial guess. Neither case emits a divide-by-zero warning.

        Returns
        -------
        p0 : list or None
            The initial guesses as [m, x0], where ``x0 = -b / m`` is the
            x-intercept of the estimated line.
        """
        estimate = _median_slope_intercept(self)
        if estimate is None:
            return None

        m, b = estimate
        if m == 0:
            self.logger.warning(
                "Estimated slope is 0, so no x-intercept.\nReturning None."
            )
            return None

        return [m, -b / m]

    @property
    def TeX_function(self):
        TeX = r"f(x)=m \cdot (x - x_0)"
        return TeX

    @property
    def y_intercept(self):
        """Calculate the y-intercept of the fitted line.

        Returns
        -------
        float
            The y value where the line crosses x=0.
        """
        return -self.popt["x0"] * self.popt["m"]
