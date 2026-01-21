r"""Hinge (piecewise linear) fit functions.

This module provides fit functions for piecewise linear models with a
hinge point, commonly used for modeling saturation behavior.
"""

from __future__ import annotations

import numpy as np

from .core import FitFunction


class HingeSaturation(FitFunction):
    r"""Piecewise linear function with hinge point for saturation modeling.

    The model consists of two linear segments joined at a hinge point (xh, yh):

    - Rising region (x < xh): :math:`f(x) = m_1 (x - x_1)`
    - Plateau region (x >= xh): :math:`f(x) = m_2 (x - x_2)`

    where the slopes and intercepts are related by continuity at the hinge:

    - :math:`m_1 = y_h / (x_h - x_1)`
    - :math:`x_2 = x_h - y_h / m_2`

    Parameters
    ----------
    xobs : array-like
        Independent variable observations.
    yobs : array-like
        Dependent variable observations.
    guess_xh : float, optional
        Initial guess for hinge x-coordinate. Default is 326.
    guess_yh : float, optional
        Initial guess for hinge y-coordinate. Default is 0.5.
    **kwargs
        Additional arguments passed to :class:`FitFunction`.

    Attributes
    ----------
    xh : float
        Hinge x-coordinate (fitted parameter).
    yh : float
        Hinge y-coordinate (fitted parameter).
    x1 : float
        x-intercept of rising line (fitted parameter).
    m2 : float
        Slope of plateau region (fitted parameter). m2=0 gives constant saturation.

    Examples
    --------
    >>> import numpy as np
    >>> from solarwindpy.fitfunctions import HingeSaturation
    >>> x = np.linspace(0, 15, 100)
    >>> y = np.where(x < 5, 2*x, 10)  # Saturation at y=10 for x>=5
    >>> fit = HingeSaturation(x, y, guess_xh=5, guess_yh=10)
    >>> fit.make_fit()
    >>> print(f"Hinge at ({fit.popt['xh']:.2f}, {fit.popt['yh']:.2f})")
    Hinge at (5.00, 10.00)
    """

    def __init__(
        self,
        xobs,
        yobs,
        guess_xh: float = 326,
        guess_yh: float = 0.5,
        **kwargs,
    ):
        super().__init__(xobs, yobs, **kwargs)
        self._saturation_guess = (guess_xh, guess_yh)

    @property
    def saturation_guess(self) -> tuple[float, float]:
        r"""Guess for saturation transition (xh, yh) used in p0 calculation."""
        return self._saturation_guess

    @property
    def function(self):
        r"""The hinge saturation function.

        Returns
        -------
        callable
            Function with signature ``f(x, xh, yh, x1, m2)``.
        """

        def hinge_saturation(x, xh, yh, x1, m2):
            r"""Evaluate hinge saturation model.

            Parameters
            ----------
            x : array-like
                Independent variable values.
            xh : float
                Hinge x-coordinate.
            yh : float
                Hinge y-coordinate.
            x1 : float
                x-intercept of rising line.
            m2 : float
                Slope of plateau region.

            Returns
            -------
            numpy.ndarray
                Model values at x.
            """
            m1 = yh / (xh - x1)
            x2 = xh - (yh / m2) if abs(m2) > 1e-15 else np.inf

            y1 = m1 * (x - x1)
            y2 = m2 * (x - x2) if abs(m2) > 1e-15 else yh * np.ones_like(x)

            out = np.minimum(y1, y2)
            return out

        return hinge_saturation

    @property
    def p0(self) -> list:
        r"""Calculate initial parameter guess.

        The initial guess is derived from:
        - ``saturation_guess`` for (xh, yh)
        - Estimated x1 from linear fit to rising region, or data minimum
        - Median slope in plateau region for m2

        Returns
        -------
        list
            Initial guesses as [xh, yh, x1, m2].

        Raises
        ------
        AssertionError
            If insufficient data for estimation.
        """
        assert self.sufficient_data

        xh, yh = self.saturation_guess

        x = self.observations.used.x
        y = self.observations.used.y

        # Estimate x1 from data in rising region
        # m1 = yh / (xh - x1), so x1 = xh - yh/m1
        rising_mask = x < xh
        if rising_mask.sum() >= 2:
            x_rising = x[rising_mask]
            y_rising = y[rising_mask]
            # Simple linear regression to estimate slope m1
            m1_est = np.polyfit(x_rising, y_rising, 1)[0]
            if abs(m1_est) > 1e-10:
                x1 = xh - yh / m1_est
            else:
                x1 = x.min()
        else:
            # Fall back to minimum x value
            x1 = x.min()

        # Estimate m2 from slope in plateau region
        plateau_mask = x >= xh
        if plateau_mask.sum() >= 2:
            m2 = np.median(np.ediff1d(y[plateau_mask]) / np.ediff1d(x[plateau_mask]))
        else:
            m2 = 0.0

        p0 = [xh, yh, x1, m2]
        return p0

    @property
    def TeX_function(self) -> str:
        r"""LaTeX representation of the model.

        Returns
        -------
        str
            Multi-line LaTeX string describing the piecewise function.
        """
        tex = "\n".join(
            [
                r"f(x)=\min(y_1, \, y_2)",
                r"y_i = m_i(x-x_i)",
                r"m_1 = \frac{y_h}{x_h - x_1}",
                r"x_2 = x_h - \frac{y_h}{m_2}",
            ]
        )
        return tex
