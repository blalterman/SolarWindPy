#!/usr/bin/env python
r"""Simple linear fit functions.

This module defines :class:`~solarwindpy.fitfunctions.core.FitFunction`
subclasses for straight-line models.  They are primarily used for
quick trend estimation and serve as basic examples of the
FitFunction interface.
"""
import pdb  # noqa: F401
import numpy as np

from .core import FitFunction


class Line(FitFunction):
    def __init__(self, xobs, yobs, **kwargs):
        """Create a line fit to ``(xobs, yobs)`` data."""
        super().__init__(xobs, yobs, **kwargs)

    @property
    def function(self):
        def line(x, m, b):
            return (m * x) + b

        return line

    @property
    def p0(self):
        r"""Calculate the initial guess for the line parameters.

        If this fails, return :py:meth:`curve_fit`'s default value `None`.

        Return
        ------
        p0 : list
            The initial guesses as [m, b].
        """
        assert self.sufficient_data

        x = self.observations.used.x
        y = self.observations.used.y
        dy, dx = np.ediff1d(y), np.ediff1d(x)

        m = dy / dx
        m = np.median(m)
        b = (m * x) - y
        b = np.median(b)

        p0 = [m, b]

        if not (np.all(np.isfinite(dx)) and (np.all(np.abs(dx) > 0))):
            self.logger.warning(f"Slope estimate failed (dx = {dx}).\nReturning None.")
            p0 = None

        return p0

    @property
    def TeX_function(self):
        TeX = r"f(x)=m \cdot x + b"
        return TeX

    @property
    def x_intercept(self):
        return -self.popt["b"] / self.popt["m"]


class LineXintercept(FitFunction):
    def __init__(self, xobs, yobs, **kwargs):
        super().__init__(xobs, yobs, **kwargs)

    @property
    def function(self):
        def line(x, m, x0):
            return m * (x - x0)

        return line

    @property
    def p0(self):
        r"""Calculate the initial guess for the line parameters.

        If this fails, return :py:meth:`curve_fit`'s default value `None`.

        Return
        ------
        p0 : list
            The initial guesses as [m, b].
        """
        assert self.sufficient_data

        x = self.observations.used.x
        y = self.observations.used.y
        dy, dx = np.ediff1d(y), np.ediff1d(x)

        m = dy / dx
        m = np.median(m)
        b = (m * x) - y
        b = np.median(b)

        x0 = -b / m
        p0 = [m, x0]

        if not (np.all(np.isfinite(dx)) and (np.all(np.abs(dx) > 0))):
            self.logger.warning(f"Slope estimate failed (dx = {dx}).\nReturning None.")
            p0 = None

        return p0

    @property
    def TeX_function(self):
        TeX = r"f(x)=m \cdot (x - x_0)"
        return TeX

    @property
    def y_intercept(self):
        return -self.popt["x0"] * self.popt["m"]
