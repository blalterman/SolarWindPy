#!/usr/bin/env python
r"""Utilities for fitting power-law models.

This module provides :class:`~solarwindpy.fitfunctions.core.FitFunction`
subclasses to fit power-law relations of the form ``f(x) = A x^b`` with
optional offsets or centering.  These classes supply sensible initial
guesses and convenience properties for plotting and LaTeX reporting.
"""
import pdb  # noqa: F401

from .core import FitFunction


class PowerLaw(FitFunction):
    def __init__(self, xobs, yobs, **kwargs):
        # Docstring inherited from FitFunction
        super().__init__(xobs, yobs, **kwargs)

    @property
    def function(self):
        def power_law(x, A, b):
            return A * (x**b)

        return power_law

    @property
    def p0(self):
        r"""Return initial guesses ``[A, b]`` for the fit."""
        assert self.sufficient_data

        #         y = self.yobs

        #         c = 1.0
        #         try:
        #             A = y.max()
        #         except ValueError as e:
        #             chk = (
        #                 r"zero-size array to reduction operation maximum "
        #                 "which has no identity"
        #             )
        #             if e.message.startswith(chk):
        #                 msg = (
        #                     "There is no maximum of a zero-size array. "
        #                     "Please check input data."
        #                 )
        #                 raise ValueError(msg)

        p0 = [1, 1]
        return p0

    @property
    def TeX_function(self):
        TeX = r"f(x)=A x^b"
        return TeX


class PowerLawPlusC(FitFunction):
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
        def power_law(x, A, b, c):
            return (A * (x**b)) + c

        return power_law

    @property
    def p0(self):
        r"""Return initial guesses ``[A, b, c]`` for the fit."""
        assert self.sufficient_data

        #         y = self.yobs

        #         c = 1.0
        #         try:
        #             A = y.max()
        #         except ValueError as e:
        #             chk = (
        #                 r"zero-size array to reduction operation maximum "
        #                 "which has no identity"
        #             )
        #             if e.message.startswith(chk):
        #                 msg = (
        #                     "There is no maximum of a zero-size array. "
        #                     "Please check input data."
        #                 )
        #                 raise ValueError(msg)

        p0 = [1, 1, 0]
        return p0

    @property
    def TeX_function(self):
        TeX = r"f(x)=A x^b + c"
        return TeX


class PowerLawOffCenter(FitFunction):
    def __init__(self, xobs, yobs, **kwargs):
        r"""Initialize a power law centered at ``x - x_0`` without offset."""
        super().__init__(xobs, yobs, **kwargs)

    @property
    def function(self):
        def power_law(x, A, b, x0):
            return A * ((x - x0) ** b)

        return power_law

    @property
    def p0(self):
        r"""Return initial guesses ``[A, b, x0]`` for the fit."""
        assert self.sufficient_data

        #         y = self.yobs

        #         c = 1.0
        #         try:
        #             A = y.max()
        #         except ValueError as e:
        #             chk = (
        #                 r"zero-size array to reduction operation maximum "
        #                 "which has no identity"
        #             )
        #             if e.message.startswith(chk):
        #                 msg = (
        #                     "There is no maximum of a zero-size array. "
        #                     "Please check input data."
        #                 )
        #                 raise ValueError(msg)

        p0 = [1, 1, 0]
        return p0

    @property
    def TeX_function(self):
        TeX = r"f(x)=A (x-x_0)^b"
        return TeX


# class PowerLaw2(FitFunction):
#     def __init__(self, xobs, yobs, **kwargs):
#         f""":py:class:`Fitfunction` for a power law centered at (x - x_0) with a constant offset.
#         """
#         super().__init__(xobs, yobs, **kwargs)

#     @property
#     def function(self):
#         def power_law(x, A, b, c, x0):
#             return (A * ((x - x0) ** b) + c)

#         return power_law

#     @property
#     def p0(self):
#         r"""Calculate the initial guess for the Exponential parameters.

#         Return
#         ------
#         p0 : list
#             The initial guesses as [c, A].
#         """
#         assert self.sufficient_data

#         #         y = self.yobs

#         #         c = 1.0
#         #         try:
#         #             A = y.max()
#         #         except ValueError as e:
#         #             chk = (
#         #                 r"zero-size array to reduction operation maximum "
#         #                 "which has no identity"
#         #             )
#         #             if e.message.startswith(chk):
#         #                 msg = (
#         #                     "There is no maximum of a zero-size array. "
#         #                     "Please check input data."
#         #                 )
#         #                 raise ValueError(msg)

#         p0 = [1, 1, 1, 1]
#         return p0

#     @property
#     def TeX_function(self):
#         TeX = r"f(x)=A (x - x_0)^b + c"
#         return TeX
