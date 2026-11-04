#!/usr/bin/env python
r"""Power-law fit functions.

This module provides :class:`~solarwindpy.fitfunctions.core.FitFunction`
subclasses for power laws of the form :math:`f(x) = A x^{\alpha}`, with an
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

from .core import FitFunction

#: The exponent renders as a Greek alpha in the TeX info.
_ALPHA_TEX = {"alpha": r"\alpha"}


class PowerLaw(FitFunction):
    r"""Power law :math:`f(x) = A x^{\alpha}`.

    Parameters are ``A`` (amplitude) and ``alpha`` (exponent).
    """

    _TeX_argnames = _ALPHA_TEX

    @property
    def function(self):
        r"""The model :math:`A x^{\alpha}` as ``f(x, A, alpha)``."""

        def power_law(x, A, alpha):
            """Evaluate ``A * x**alpha``."""
            return A * (x**alpha)

        return power_law

    @property
    def p0(self):
        r"""Return initial guesses ``[A, alpha]`` for the fit."""
        self._require_sufficient_data()

        p0 = [1, 1]
        return p0

    @property
    def TeX_function(self):
        r"""LaTeX form of the model."""
        TeX = r"f(x)=A x^{\alpha}"
        return TeX


class PowerLawPlusC(FitFunction):
    r"""Power law with an additive constant, :math:`f(x) = A x^{\alpha} + y_0`.

    Parameters are ``A`` (amplitude), ``alpha`` (exponent) and ``y0`` (offset).
    """

    _TeX_argnames = _ALPHA_TEX

    @property
    def function(self):
        r"""The model :math:`A x^{\alpha} + y_0` as ``f(x, A, alpha, y0)``."""

        def power_law(x, A, alpha, y0):
            """Evaluate ``A * x**alpha + y0``."""
            return (A * (x**alpha)) + y0

        return power_law

    @property
    def p0(self):
        r"""Return initial guesses ``[A, alpha, y0]`` for the fit."""
        self._require_sufficient_data()

        p0 = [1, 1, 0]
        return p0

    @property
    def TeX_function(self):
        r"""LaTeX form of the model."""
        TeX = r"f(x)=A x^{\alpha} + y_0"
        return TeX


class PowerLawOffCenter(FitFunction):
    r"""Power law about a shifted origin, :math:`f(x) = A (x - x_0)^{\alpha}`.

    Parameters are ``A`` (amplitude), ``alpha`` (exponent) and ``x0`` (origin).

    Notes
    -----
    The model is defined only for :math:`x > x_0`: a negative base has no
    real non-integer power. :meth:`make_fit` therefore bounds ``x0`` below
    the smallest used ``x``, within any bounds the caller passes.
    """

    _TeX_argnames = _ALPHA_TEX

    def _prepare_fit(self, kwargs):
        r"""Bound ``x0`` below the smallest used ``x``.

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
            its bounds or at NaN or infinity. ``make_fit`` records it as a
            failed fit.
        """
        x = self.observations.used.x
        n = len(self.argnames)
        try:
            lb, ub = self._bounds_lower_upper(
                kwargs.get("bounds", (-np.inf, np.inf)), n
            )
        except (TypeError, ValueError):
            # Malformed bounds: the base fit reports them.
            return kwargs
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
            if p0 is not None and p0.size == n and not np.isfinite(p0[i]):
                e = f"the initial guess p0 starts x0 at {p0[i]}, not a finite number"
            elif p0 is not None and p0.size == n and p0[i] > ub[i]:
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
            p0 = list(self.p0)
            p0[i] = float(np.clip(p0[i], lb[i], ub[i]))
            kwargs["p0"] = p0
        if e is not None:
            raise ValueError(
                f"{type(self).__name__} needs x0 below the smallest used x "
                f"({x.min()}), where the model is defined, but {e}."
            )
        kwargs["bounds"] = (lb, ub)
        return kwargs

    @property
    def function(self):
        r"""The model :math:`A (x - x_0)^{\alpha}` as ``f(x, A, alpha, x0)``."""

        def power_law(x, A, alpha, x0):
            """Evaluate ``A * (x - x0)**alpha``."""
            return A * ((x - x0) ** alpha)

        return power_law

    @property
    def p0(self):
        r"""Return initial guesses ``[A, alpha, x0]`` for the fit.

        ``A`` and ``alpha`` start at 1. ``x0`` starts at 0 when every used ``x``
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
        TeX = r"f(x)=A (x-x_0)^{\alpha}"
        return TeX
