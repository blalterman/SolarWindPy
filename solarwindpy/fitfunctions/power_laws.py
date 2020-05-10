#!/usr/bin/env python
r""":py:mod:`Exponential` and similar `FitFunction` subclasses.
"""
import pdb  # noqa: F401

from .core import FitFunction


class PowerLaw(FitFunction):
    def __init__(self, xobs, yobs, **kwargs):
        super().__init__(xobs, yobs, **kwargs)

    @property
    def function(self):
        def power_law(x, A, b):
            return A * (x ** b)

        return power_law

    @property
    def p0(self):
        r"""Calculate the initial guess for the Exponential parameters.

        Return
        ------
        p0 : list
            The initial guesses as [c, A].
        """
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
        super().__init__(xobs, yobs, **kwargs)

    @property
    def function(self):
        def power_law(x, A, b, c):
            return (A * (x ** b)) + c

        return power_law

    @property
    def p0(self):
        r"""Calculate the initial guess for the Exponential parameters.

        Return
        ------
        p0 : list
            The initial guesses as [c, A].
        """
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
        f""":py:class:`Fitfunction` for a power law centered at (x - x_0) with no constant offset.
        """
        super().__init__(xobs, yobs, **kwargs)

    @property
    def function(self):
        def power_law(x, A, b, x0):
            return A * ((x - x0) ** b)

        return power_law

    @property
    def p0(self):
        r"""Calculate the initial guess for the Exponential parameters.

        Return
        ------
        p0 : list
            The initial guesses as [c, A].
        """
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
        TeX = r"f(x)=A (x - x_0)^b"
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
