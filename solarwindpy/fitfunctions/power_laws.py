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

from .core import FitFunction


class PowerLaw(FitFunction):
    r"""Power law :math:`f(x) = A x^b`.

    Parameters are ``A`` (amplitude) and ``b`` (exponent).
    """

    def __init__(self, xobs, yobs, **kwargs):
        """Initialize a power-law fit to the observations."""
        super().__init__(xobs, yobs, **kwargs)

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
        assert self.sufficient_data

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

    def __init__(self, xobs, yobs, **kwargs):
        """Initialize a power law with constant offset.

        Parameters
        ----------
        xobs, yobs : array-like
            Observed values to fit.
        **kwargs : dict
            Forwarded to :class:`~solarwindpy.fitfunctions.core.FitFunction`.
        """

        super().__init__(xobs, yobs, **kwargs)

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
        assert self.sufficient_data

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
    """

    def __init__(self, xobs, yobs, **kwargs):
        r"""Initialize a power law centered at ``x - x_0`` without offset."""
        super().__init__(xobs, yobs, **kwargs)

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
        assert self.sufficient_data

        p0 = [1, 1, 0]
        return p0

    @property
    def TeX_function(self):
        r"""LaTeX form of the model."""
        TeX = r"f(x)=A (x-x_0)^b"
        return TeX
