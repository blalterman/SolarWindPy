r"""Heaviside step function fit.

This module provides a fit function for a Heaviside (step) function,
commonly used for modeling abrupt transitions in data.
"""

from __future__ import annotations

import numpy as np

from .core import FitFunction


class HeavySide(FitFunction):
    r"""Heaviside step function for modeling abrupt transitions.

    The model is a step function with transition at x0:

    .. math::

        f(x) = y_1 \cdot H(x_0 - x, \tfrac{1}{2}(y_0 + y_1)) + y_0

    where H is the Heaviside step function. The behavior is:

    - For x < x0: :math:`f(x) = y_1 + y_0`
    - For x > x0: :math:`f(x) = y_0`
    - For x == x0: :math:`f(x) = y_1 \cdot \tfrac{1}{2}(y_0 + y_1) + y_0`

    Parameters
    ----------
    xobs : array-like
        Independent variable observations.
    yobs : array-like
        Dependent variable observations.
    guess_x0 : float, optional
        Initial guess for transition x-coordinate. If not provided,
        estimated as the midpoint of the x data range.
    guess_y0 : float, optional
        Initial guess for baseline level (value for x > x0). If not
        provided, estimated from data above the transition.
    guess_y1 : float, optional
        Initial guess for step height. If not provided, estimated
        from data below and above the transition.
    **kwargs
        Additional arguments passed to :class:`FitFunction`.

    Attributes
    ----------
    x0 : float
        Step transition x-coordinate (fitted parameter).
    y0 : float
        Baseline level for x > x0 (fitted parameter).
    y1 : float
        Step height (fitted parameter). The value for x < x0 is y0 + y1.

    Examples
    --------
    >>> import numpy as np
    >>> from solarwindpy.fitfunctions import HeavySide
    >>> x = np.linspace(0, 10, 100)
    >>> y = np.where(x < 5, 5, 2)  # Step down at x=5
    >>> fit = HeavySide(x, y, guess_x0=5, guess_y0=2, guess_y1=3)
    >>> fit.make_fit()
    >>> print(f"Step at x={fit.popt['x0']:.2f}")
    Step at x=5.00

    Notes
    -----
    The initial parameter estimation (p0) uses heuristics based on
    the data distribution. For best results with noisy or complex
    data, providing manual guesses or passing p0 directly to
    make_fit() is recommended.
    """

    def __init__(
        self,
        xobs,
        yobs,
        guess_x0: float | None = None,
        guess_y0: float | None = None,
        guess_y1: float | None = None,
        **kwargs,
    ):
        self._guess_x0 = guess_x0
        self._guess_y0 = guess_y0
        self._guess_y1 = guess_y1
        super().__init__(xobs, yobs, **kwargs)

    @property
    def function(self):
        r"""The Heaviside step function.

        Returns
        -------
        callable
            Function with signature ``f(x, x0, y0, y1)``.
        """

        def heavy_side(x, x0, y0, y1):
            r"""Evaluate Heaviside step function.

            Parameters
            ----------
            x : array-like
                Independent variable values.
            x0 : float
                Step transition x-coordinate.
            y0 : float
                Baseline level (value for x > x0).
            y1 : float
                Step height (y_left - y0 = y1, so y_left = y0 + y1).

            Returns
            -------
            numpy.ndarray
                Model values at x.
            """
            out = y1 * np.heaviside(x0 - x, 0.5 * (y0 + y1)) + y0
            return out

        return heavy_side

    @property
    def p0(self) -> list:
        r"""Calculate initial parameter guess.

        The initial guess is derived from:
        - User-provided guesses if available
        - Otherwise, heuristic estimates from the data

        Returns
        -------
        list
            Initial guesses as [x0, y0, y1].

        Raises
        ------
        AssertionError
            If insufficient data for estimation.
        """
        assert self.sufficient_data

        x = self.observations.used.x
        y = self.observations.used.y

        # Use guesses if provided, otherwise estimate from data
        if self._guess_x0 is not None:
            x0 = self._guess_x0
        else:
            # Estimate x0 as midpoint of data range
            x0 = (x.max() + x.min()) / 2

        if self._guess_y0 is not None and self._guess_y1 is not None:
            y0 = self._guess_y0
            y1 = self._guess_y1
        else:
            # Estimate y0 and y1 from data above and below x0
            y0 = np.median(y[x > x0])  # Value after step
            y1 = np.median(y[x < x0]) - y0  # Step height (y_left - y0)
            if np.isnan(y0):
                y0 = y.mean()
            if np.isnan(y1):
                y1 = 0.0

        p0 = [x0, y0, y1]
        return p0

    @property
    def TeX_function(self) -> str:
        r"""LaTeX representation of the model.

        Returns
        -------
        str
            Multi-line LaTeX string describing the Heaviside function.
        """
        tex = "\n".join(
            [
                r"f(x) = y_1 \cdot H(x_0 - x) + y_0",
                r"x < x_0: f(x) = y_0 + y_1",
                r"x > x_0: f(x) = y_0",
            ]
        )
        return tex
