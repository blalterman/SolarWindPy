#!/usr/bin/env python
r"""Fit functions for exponential models.

Classes in this module implement exponential decay and related forms
using the :class:`~solarwindpy.fitfunctions.core.FitFunction` API.
They provide reasonable starting parameters and formatted LaTeX output
for visualization.
"""
import pdb  # noqa: F401
import numpy as np

from numbers import Number

from .core import FitFunction


class Exponential(FitFunction):
    def __init__(self, xobs, yobs, **kwargs):
        """Fit ``A * exp(-c x)`` to the data."""
        super().__init__(xobs, yobs, **kwargs)

    @property
    def function(self):
        def exp(x, c, A):
            return A * np.exp(-(c * x))

        return exp

    @property
    def p0(self):
        r"""Return initial guesses ``[c, A]`` for the fit."""
        assert self.sufficient_data

        y = self.observations.used.y

        c = 1.0
        try:
            A = y.max()
        except ValueError as e:
            chk = (
                r"zero-size array to reduction operation maximum "
                "which has no identity"
            )
            if e.message.startswith(chk):
                msg = (
                    "There is no maximum of a zero-size array. "
                    "Please check input data."
                )
                raise ValueError(msg)

        p0 = [c, A]
        return p0

    @property
    def TeX_function(self):
        TeX = r"f(x)=A \cdot e^{-cx}"
        return TeX


class ExponentialPlusC(FitFunction):
    def __init__(self, xobs, yobs, **kwargs):
        """Fit ``A * exp(-c x) + d`` to the data."""
        super().__init__(xobs, yobs, **kwargs)

    @property
    def function(self):
        def expc(x, c, A, d):
            return (A * np.exp(-(c * x))) + d

        return expc

    @property
    def p0(self):
        r"""Return initial guesses ``[c, A, d]`` for the fit."""
        assert self.sufficient_data

        y = self.observations.used.y

        c = 1.0
        d = 0.0
        try:
            A = y.max()
        except ValueError as e:
            chk = (
                r"zero-size array to reduction operation maximum "
                "which has no identity"
            )
            if e.message.startswith(chk):
                msg = (
                    "There is no maximum of a zero-size array. "
                    "Please check input data."
                )
                raise ValueError(msg)

        p0 = [c, A, d]
        return p0

    @property
    def TeX_function(self):
        TeX = r"f(x)=A \cdot e^{-cx} + d"
        return TeX


class ExponentialCDF(FitFunction):
    def __init__(self, xobs, yobs, **kwargs):
        """Fit an exponential cumulative distribution function."""
        super().__init__(xobs, yobs, **kwargs)

    @property
    def function(self):
        def exp_cdf(x, c):
            return self.y0 * (1.0 - np.exp(-(c * x)))

        return exp_cdf

    @property
    def y0(self):
        r"""Amplitude of the CDF."""
        return self._y0

    def set_y0(self, new):
        assert isinstance(new, Number)
        self._y0 = new

    @property
    def p0(self):
        r"""Return initial guess ``[c]`` for the fit."""
        assert self.sufficient_data

        y = self.observations.used.y

        c = y.mean()

        p0 = [c]
        return p0

    @property
    def TeX_function(self):
        TeX = r"f(x)=A \left(1 - e^{-cx}\right)"
        return TeX

    def set_TeX_info(self, **kwargs):
        """Include ``A`` value in the TeX annotation."""

        # HACK: assumes integer A
        #       If not integer, will need to format float or exp.
        additional_info = kwargs.pop("additional_info", [])
        if not isinstance(additional_info, list):
            additional_info = [additional_info]
        info_A = r"$A = %s$" % self.y0
        additional_info = [info_A] + additional_info

        super(ExponentialCDF, self).set_TeX_info(
            additional_info=additional_info, **kwargs
        )
