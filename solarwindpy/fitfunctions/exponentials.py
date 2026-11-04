#!/usr/bin/env python
r"""Fit functions for exponential models.

Classes in this module implement exponential decay and related forms
using the :class:`~solarwindpy.fitfunctions.core.FitFunction` API.
Each defines the model, an initial guess, and its LaTeX form.
"""

__all__ = [
    "Exponential",
    "ExponentialPlusC",
]

import numpy as np

from .core import FitFunction


class Exponential(FitFunction):
    r"""Exponential decay :math:`f(x) = A e^{-k x}`.

    Parameters are ``k`` (rate) and ``A`` (amplitude at ``x = 0``).
    """

    @property
    def function(self):
        r"""The model :math:`A e^{-k x}` as ``f(x, k, A)``."""

        def exp(x, k, A):
            """Evaluate ``A * exp(-k * x)``."""
            return A * np.exp(-(k * x))

        return exp

    @property
    def p0(self):
        r"""Return initial guesses ``[k, A]`` for the fit."""
        self._require_sufficient_data()

        y = self.observations.used.y

        k = 1.0
        A = y.max()

        p0 = [k, A]
        return p0

    @property
    def TeX_function(self):
        r"""LaTeX form of the model."""
        TeX = r"f(x)=A \cdot e^{-kx}"
        return TeX


class ExponentialPlusC(FitFunction):
    r"""Exponential decay plus a constant, :math:`f(x) = A e^{-k x} + c`.

    Parameters are ``k`` (rate), ``A`` (amplitude) and ``c`` (offset).
    """

    @property
    def function(self):
        r"""The model :math:`A e^{-k x} + c` as ``f(x, k, A, c)``."""

        def expc(x, k, A, c):
            """Evaluate ``A * exp(-k * x) + c``."""
            return (A * np.exp(-(k * x))) + c

        return expc

    @property
    def p0(self):
        r"""Return initial guesses ``[k, A, c]`` for the fit."""
        self._require_sufficient_data()

        y = self.observations.used.y

        k = 1.0
        c = 0.0
        A = y.max()

        p0 = [k, A, c]
        return p0

    @property
    def TeX_function(self):
        r"""LaTeX form of the model."""
        TeX = r"f(x)=A \cdot e^{-kx} + c"
        return TeX
