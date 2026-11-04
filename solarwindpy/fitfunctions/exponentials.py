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
    r"""Exponential decay :math:`f(x) = A e^{-c x}`.

    Parameters are ``c`` (rate) and ``A`` (amplitude at ``x = 0``).
    """

    @property
    def function(self):
        r"""The model :math:`A e^{-c x}` as ``f(x, c, A)``."""

        def exp(x, c, A):
            """Evaluate ``A * exp(-c * x)``."""
            return A * np.exp(-(c * x))

        return exp

    @property
    def p0(self):
        r"""Return initial guesses ``[c, A]`` for the fit."""
        self._require_sufficient_data()

        y = self.observations.used.y

        c = 1.0
        A = y.max()

        p0 = [c, A]
        return p0

    @property
    def TeX_function(self):
        r"""LaTeX form of the model."""
        TeX = r"f(x)=A \cdot e^{-cx}"
        return TeX


class ExponentialPlusC(FitFunction):
    r"""Exponential decay plus a constant, :math:`f(x) = A e^{-c x} + d`.

    Parameters are ``c`` (rate), ``A`` (amplitude) and ``d`` (offset).
    """

    @property
    def function(self):
        r"""The model :math:`A e^{-c x} + d` as ``f(x, c, A, d)``."""

        def expc(x, c, A, d):
            """Evaluate ``A * exp(-c * x) + d``."""
            return (A * np.exp(-(c * x))) + d

        return expc

    @property
    def p0(self):
        r"""Return initial guesses ``[c, A, d]`` for the fit."""
        self._require_sufficient_data()

        y = self.observations.used.y

        c = 1.0
        d = 0.0
        A = y.max()

        p0 = [c, A, d]
        return p0

    @property
    def TeX_function(self):
        r"""LaTeX form of the model."""
        TeX = r"f(x)=A \cdot e^{-cx} + d"
        return TeX
