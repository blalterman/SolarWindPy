#!/usr/bin/env python
r"""Power-law fit functions.

This module provides :class:`~solarwindpy.fitfunctions.core.FitFunction`
subclasses for power laws of the form :math:`f(x) = A x^b`, with an
optional additive constant or a shifted origin. Their initial guesses are
fixed values, not estimated from the data, except that
:class:`PowerLawOffCenter` starts ``x0`` below the data when any used ``x`` is
not positive.
"""

__all__ = [
    "PowerLaw",
    "PowerLawPlusC",
    "PowerLawOffCenter",
]

import numpy as np

from .core import FitFunction, InsufficientDataError


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
        ``x``, or the caller's upper bound if that is lower. When the caller
        passes no ``p0``, the :attr:`p0` start for ``x0`` is clipped into the
        bounds on ``x0``. Otherwise as
        :meth:`~solarwindpy.fitfunctions.core.FitFunction.make_fit`.

        Raises
        ------
        ValueError
            If the caller's lower bound on ``x0`` leaves it no room below the
            smallest used ``x``, or the caller's ``p0`` starts ``x0`` outside
            its bounds. Returned instead when ``return_exception``.
        """
        x = self.observations.used.x
        n = len(self.argnames)
        try:
            lb, ub = self._bounds_lower_upper(
                kwargs.get("bounds", (-np.inf, np.inf)), n
            )
        except (TypeError, ValueError):
            # Malformed bounds: the base fit reports them, honouring
            # return_exception.
            lb = None
        if x.size and lb is not None:
            i = self.argnames.index("x0")
            ub[i] = min(ub[i], np.nextafter(x.min(), -np.inf))
            e = None
            if lb[i] >= ub[i]:
                e = f"the lower bound on x0 is {lb[i]}"
            elif kwargs.get("p0") is not None:
                try:
                    p0 = np.atleast_1d(np.asarray(kwargs["p0"], dtype=float))
                except (TypeError, ValueError):
                    # Malformed p0: the base fit reports it.
                    p0 = None
                if p0 is not None and p0.size == n and p0[i] > ub[i]:
                    e = (
                        f"the initial guess p0 starts x0 at {p0[i]}, above its "
                        f"upper bound {ub[i]}"
                    )
                elif p0 is not None and p0.size == n and p0[i] < lb[i]:
                    e = (
                        f"the initial guess p0 starts x0 at {p0[i]}, below its "
                        f"lower bound {lb[i]}"
                    )
            elif "p0" not in kwargs:
                try:
                    p0 = list(self.p0)
                except InsufficientDataError:
                    # The base fit reports it, honouring return_exception.
                    pass
                else:
                    p0[i] = float(np.clip(p0[i], lb[i], ub[i]))
                    kwargs["p0"] = p0
            if e is not None:
                e = ValueError(
                    f"{type(self).__name__} needs x0 below the smallest used x "
                    f"({x.min()}), where the model is defined, but {e}."
                )
                if return_exception:
                    return e
                raise e
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
        r"""Return initial guesses ``[A, b, x0]`` for the fit.

        ``A`` and ``b`` start at 1. ``x0`` starts at 0 when every used ``x``
        is positive; otherwise it starts below the smallest used ``x`` by the
        range of the used ``x`` (by 1 when they are all equal), inside the
        bound :meth:`make_fit` places on ``x0``.
        """
        self._require_sufficient_data()

        x = self.observations.used.x
        xmin = x.min()
        if xmin > 0:
            x0 = 0.0
        else:
            span = x.max() - xmin
            x0 = xmin - (span if span > 0 else 1.0)
        p0 = [1, 1, x0]
        return p0

    @property
    def TeX_function(self):
        r"""LaTeX form of the model."""
        TeX = r"f(x)=A (x-x_0)^b"
        return TeX
