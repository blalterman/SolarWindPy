#!/usr/bin/env python
r"""Power-law fit functions.

This module provides :class:`~solarwindpy.fitfunctions.core.FitFunction`
subclasses for power laws of the form :math:`f(x) = A x^b`, with an
optional additive constant or a shifted origin. Their initial guesses are
fixed values, not estimated from the data.
"""

__all__ = [
    "PowerLaw",
    "PowerLawPlusC",
    "PowerLawOffCenter",
]

import numpy as np
from scipy.optimize._lsq.least_squares import prepare_bounds

from .core import FitFunction


class PowerLaw(FitFunction):
    r"""Power law :math:`f(x) = A x^b`.

    Parameters are ``A`` (amplitude) and ``b`` (exponent).
    """

    @property
    def function(self):
        r"""The model :math:`A x^b` as ``f(x, A, b)``."""

        def power_law(x, A, b):
            """Evaluate ``A * x**b``."""
            return A * (x**b)

        return power_law

    @property
    def p0(self):
        r"""Return initial guesses ``[A, b]`` for the fit."""
        self._require_sufficient_data()

        p0 = [1, 1]
        return p0

    @property
    def TeX_function(self):
        r"""LaTeX form of the model."""
        TeX = r"f(x)=A x^b"
        return TeX


class PowerLawPlusC(FitFunction):
    r"""Power law with an additive constant, :math:`f(x) = A x^b + c`.

    Parameters are ``A`` (amplitude), ``b`` (exponent) and ``c`` (offset).
    """

    @property
    def function(self):
        r"""The model :math:`A x^b + c` as ``f(x, A, b, c)``."""

        def power_law(x, A, b, c):
            """Evaluate ``A * x**b + c``."""
            return (A * (x**b)) + c

        return power_law

    @property
    def p0(self):
        r"""Return initial guesses ``[A, b, c]`` for the fit."""
        self._require_sufficient_data()

        p0 = [1, 1, 0]
        return p0

    @property
    def TeX_function(self):
        r"""LaTeX form of the model."""
        TeX = r"f(x)=A x^b + c"
        return TeX


class PowerLawOffCenter(FitFunction):
    r"""Power law about a shifted origin, :math:`f(x) = A (x - x_0)^b`.

    Parameters are ``A`` (amplitude), ``b`` (exponent) and ``x0`` (origin).

    Notes
    -----
    The model is defined only for :math:`x > x_0`: a negative base has no
    real non-integer power. :meth:`make_fit` therefore bounds ``x0`` below
    the smallest used ``x``, within any bounds the caller passes.
    """

    def make_fit(self, return_exception=False, **kwargs):
        r"""Fit with ``x0`` bounded below the smallest used ``x``.

        The upper bound on ``x0`` is the largest float below the smallest used
        ``x``, or the caller's upper bound if that is lower. Otherwise as
        :meth:`~solarwindpy.fitfunctions.core.FitFunction.make_fit`.
        """
        x = self.observations.used.x
        try:
            bounds = self._bounds_array(kwargs.get("bounds", (-np.inf, np.inf)))
            lb, ub = prepare_bounds(bounds, len(self.argnames))
        except ValueError:
            # Malformed bounds: the base fit reports them, honouring
            # return_exception.
            lb = None
        if x.size and lb is not None:
            ub = np.array(ub, dtype=float)
            i = self.argnames.index("x0")
            ub[i] = min(ub[i], np.nextafter(x.min(), -np.inf))
            kwargs["bounds"] = (lb, ub)
        return super().make_fit(return_exception=return_exception, **kwargs)

    @property
    def function(self):
        r"""The model :math:`A (x - x_0)^b` as ``f(x, A, b, x0)``."""

        def power_law(x, A, b, x0):
            """Evaluate ``A * (x - x0)**b``."""
            return A * ((x - x0) ** b)

        return power_law

    @property
    def p0(self):
        r"""Return initial guesses ``[A, b, x0]`` for the fit."""
        self._require_sufficient_data()

        p0 = [1, 1, 0]
        return p0

    @property
    def TeX_function(self):
        r"""LaTeX form of the model."""
        TeX = r"f(x)=A (x-x_0)^b"
        return TeX
