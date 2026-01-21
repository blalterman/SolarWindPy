r"""Hinge (piecewise linear) fit functions.

This module provides fit functions for piecewise linear models with a
hinge point, commonly used for modeling saturation behavior.
"""

from __future__ import annotations

from collections import namedtuple

import numpy as np

from .core import FitFunction


# Named tuple for x-intercepts used by HingeAtPoint
XIntercepts = namedtuple("XIntercepts", "x1,x2")


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


class TwoLine(FitFunction):
    r"""Piecewise linear function with two intersecting lines using minimum.

    The model consists of two linear segments:

    .. math::

        f(x) = \min(y_1, y_2)

    where:

    - :math:`y_1 = m_1 (x - x_1)`
    - :math:`y_2 = m_2 (x - x_2)`

    The lines intersect at the saturation point :math:`(x_s, s)` where:

    - :math:`x_s = \frac{m_1 x_1 - m_2 x_2}{m_1 - m_2}`
    - :math:`s = m_1 (x_s - x_1) = m_2 (x_s - x_2)`

    Parameters
    ----------
    xobs : array-like
        Independent variable observations.
    yobs : array-like
        Dependent variable observations.
    guess_xs : float, optional
        Initial guess for saturation x-coordinate. Default is 425.0.
    **kwargs
        Additional arguments passed to :class:`FitFunction`.

    Attributes
    ----------
    x1 : float
        x-intercept of first line (fitted parameter).
    x2 : float
        x-intercept of second line (fitted parameter).
    m1 : float
        Slope of first line (fitted parameter).
    m2 : float
        Slope of second line (fitted parameter).
    xs : float
        x-coordinate of intersection point (derived property).
    s : float
        y-coordinate of intersection point (derived property).
    theta : float
        Angle between the two lines in radians (derived property).

    Examples
    --------
    >>> import numpy as np
    >>> from solarwindpy.fitfunctions import TwoLine
    >>> x = np.linspace(0, 15, 100)
    >>> y = np.minimum(2*(x-0), -1*(x-15))  # Two lines intersecting at (5, 10)
    >>> fit = TwoLine(x, y, guess_xs=5.0)
    >>> fit.make_fit()
    >>> print(f"Intersection at ({fit.xs:.2f}, {fit.s:.2f})")
    Intersection at (5.00, 10.00)
    """

    def __init__(
        self,
        xobs,
        yobs,
        guess_xs: float = 425.0,
        **kwargs,
    ):
        super().__init__(xobs, yobs, **kwargs)
        self._guess_xs = guess_xs

    @property
    def guess_xs(self) -> float:
        r"""Initial guess for saturation x-coordinate used in p0 calculation."""
        return self._guess_xs

    @property
    def function(self):
        r"""The two-line minimum function.

        Returns
        -------
        callable
            Function with signature ``f(x, x1, x2, m1, m2)``.
        """

        def twoline(x, x1, x2, m1, m2):
            r"""Evaluate two-line minimum model.

            Parameters
            ----------
            x : array-like
                Independent variable values.
            x1 : float
                x-intercept of first line.
            x2 : float
                x-intercept of second line.
            m1 : float
                Slope of first line.
            m2 : float
                Slope of second line.

            Returns
            -------
            numpy.ndarray
                Model values at x.
            """
            l1 = m1 * (x - x1)
            l2 = m2 * (x - x2)
            out = np.minimum(l1, l2)
            return out

        return twoline

    @property
    def xs(self) -> float:
        r"""x-coordinate of the intersection (saturation) point.

        Calculated as:

        .. math::

            x_s = \frac{m_1 x_1 - m_2 x_2}{m_1 - m_2}
        """
        popt = self.popt
        x1 = popt["x1"]
        x2 = popt["x2"]
        m1 = popt["m1"]
        m2 = popt["m2"]
        n = (m1 * x1) - (m2 * x2)
        d = m1 - m2
        return n / d

    @property
    def s(self) -> float:
        r"""y-coordinate of the intersection (saturation) point.

        Calculated as:

        .. math::

            s = m_1 (x_s - x_1)
        """
        popt = self.popt
        x1 = popt["x1"]
        m1 = popt["m1"]
        xs = self.xs
        return m1 * (xs - x1)

    @property
    def theta(self) -> float:
        r"""Angle between the two lines in radians.

        Calculated as:

        .. math::

            \theta = \arctan(m_1) - \arctan(m_2)
        """
        m1 = self.popt["m1"]
        m2 = self.popt["m2"]
        return np.arctan(m1) - np.arctan(m2)

    @property
    def p0(self) -> list:
        r"""Calculate initial parameter guess.

        The initial guess is derived from the data by estimating slopes
        and intercepts in regions separated by ``guess_xs``.

        Returns
        -------
        list
            Initial guesses as [x1, x2, m1, m2].

        Raises
        ------
        AssertionError
            If insufficient data for estimation.

        Notes
        -----
        # TODO: Convert to data-driven p0 estimation (see GH issue #XX)
        Uses hardcoded xs=425 as the default separation point, which is
        appropriate for solar wind speed analysis.
        """
        assert self.sufficient_data

        def estimate_line(x, y, tk, xs):
            x = x[tk]
            y = y[tk]

            m_set = np.ediff1d(y) / np.ediff1d(x)
            m = np.nanmedian(m_set)
            x0 = np.nanmedian(x - (y / m))
            return x0, m

        x = self.observations.used.x
        y = self.observations.used.y

        # TODO: Convert to data-driven p0 estimation (see GH issue #XX)
        xs = self._guess_xs
        tk = x <= xs

        x1, m1 = estimate_line(x, y, tk, xs)
        x2, m2 = estimate_line(x, y, ~tk, xs)

        p0 = [x1, x2, m1, m2]
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
                r"f(x) \, =\min\left(y_1, \, y_2\right)",
                r"y_i = m_i(x - x_i)",
            ]
        )
        return tex


class Saturation(FitFunction):
    r"""Piecewise linear function reparameterized for saturation analysis.

    This is an alternative parameterization of :class:`TwoLine` where the
    saturation point coordinates and the angle between lines are used
    directly as parameters:

    .. math::

        f(x) = \min(y_1, y_2)

    Parameters are :math:`(x_1, x_s, s, \theta)` where:

    - :math:`x_1`: x-intercept of the rising line
    - :math:`x_s`: x-coordinate of saturation point
    - :math:`s`: y-coordinate of saturation point
    - :math:`\theta`: angle between the two lines (radians)

    The slopes are derived as:

    - :math:`m_1 = s / (x_s - x_1)`
    - :math:`m_2 = \tan(\arctan(m_1) - \theta)`

    Parameters
    ----------
    xobs : array-like
        Independent variable observations.
    yobs : array-like
        Dependent variable observations.
    guess_xs : float, optional
        Initial guess for saturation x-coordinate. Default is 425.0.
    guess_s : float, optional
        Initial guess for saturation y-value. Default is 0.5.
    **kwargs
        Additional arguments passed to :class:`FitFunction`.

    Attributes
    ----------
    x1 : float
        x-intercept of rising line (fitted parameter).
    xs : float
        x-coordinate of saturation point (fitted parameter).
    s : float
        y-coordinate of saturation point (fitted parameter).
    theta : float
        Angle between lines (fitted parameter, radians).
    m1 : float
        Slope of rising line (derived property).
    m2 : float
        Slope of plateau line (derived property).
    x2 : float
        x-intercept of plateau line (derived property).

    Examples
    --------
    >>> import numpy as np
    >>> from solarwindpy.fitfunctions import Saturation
    >>> x = np.linspace(0, 15, 100)
    >>> y = np.minimum(2*(x-0), -1*(x-15))
    >>> fit = Saturation(x, y, guess_xs=5.0, guess_s=10.0)
    >>> fit.make_fit()
    >>> print(f"Saturation at ({fit.popt['xs']:.2f}, {fit.popt['s']:.2f})")
    Saturation at (5.00, 10.00)
    """

    def __init__(
        self,
        xobs,
        yobs,
        guess_xs: float = 425.0,
        guess_s: float = 0.5,
        **kwargs,
    ):
        super().__init__(xobs, yobs, **kwargs)
        self._saturation_guess = (guess_xs, guess_s)

    @property
    def saturation_guess(self) -> tuple[float, float]:
        r"""Guess for saturation transition (xs, s) used in p0 calculation."""
        return self._saturation_guess

    @property
    def function(self):
        r"""The saturation function.

        Returns
        -------
        callable
            Function with signature ``f(x, x1, xs, s, theta)``.
        """

        def saturation(x, x1, xs, s, theta):
            r"""Evaluate saturation model.

            Parameters
            ----------
            x : array-like
                Independent variable values.
            x1 : float
                x-intercept of rising line.
            xs : float
                x-coordinate of saturation point.
            s : float
                y-coordinate of saturation point.
            theta : float
                Angle between lines in radians.

            Returns
            -------
            numpy.ndarray
                Model values at x.
            """
            m1 = s / (xs - x1)
            m2 = np.tan(np.arctan(m1) - theta)
            x2 = xs - (s / m2)

            l1 = m1 * (x - x1)
            l2 = m2 * (x - x2)
            out = np.minimum(l1, l2)
            return out

        return saturation

    @property
    def m1(self) -> float:
        r"""Slope of the rising line.

        Calculated as:

        .. math::

            m_1 = \frac{s}{x_s - x_1}
        """
        popt = self.popt
        s = popt["s"]
        xs = popt["xs"]
        x1 = popt["x1"]
        return s / (xs - x1)

    @property
    def m2(self) -> float:
        r"""Slope of the plateau line.

        Calculated as:

        .. math::

            m_2 = \tan(\arctan(m_1) - \theta)
        """
        popt = self.popt
        theta = popt["theta"]
        m1 = self.m1
        return np.tan(np.arctan(m1) - theta)

    @property
    def x2(self) -> float:
        r"""x-intercept of the plateau line.

        Calculated as:

        .. math::

            x_2 = x_s - \frac{s}{m_2}
        """
        popt = self.popt
        s = popt["s"]
        xs = popt["xs"]
        m2 = self.m2
        return xs - (s / m2)

    @property
    def p0(self) -> list:
        r"""Calculate initial parameter guess.

        The initial guess is derived from the data by estimating slopes
        and intercepts in regions separated by the saturation guess.

        Returns
        -------
        list
            Initial guesses as [x1, xs, s, theta].

        Raises
        ------
        AssertionError
            If insufficient data for estimation.

        Notes
        -----
        # TODO: Convert to data-driven p0 estimation (see GH issue #XX)
        Uses hardcoded xs=425 as the default separation point, which is
        appropriate for solar wind speed analysis.
        """
        assert self.sufficient_data

        def estimate_line(x, y, tk, xs):
            x = x[tk]
            y = y[tk]

            m_set = np.ediff1d(y) / np.ediff1d(x)
            m = np.nanmedian(m_set)
            x0 = np.nanmedian(x - (y / m))
            s = m * (xs - x0)
            return x0, m, s

        x = self.observations.used.x
        y = self.observations.used.y

        # TODO: Convert to data-driven p0 estimation (see GH issue #XX)
        xs, _ = self.saturation_guess
        tk = x <= xs

        x1, m1, s1 = estimate_line(x, y, tk, xs)
        x2, m2, s2 = estimate_line(x, y, ~tk, xs)

        s = np.nanmedian([s1, s2])
        theta = np.arctan((m1 - m2) / (1 + m1 * m2))

        p0 = [x1, xs, s, theta]
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
                r"f \, \left(x, x_1, x_s, s, \theta\right)=\min\left(y_1, \, y_2\right)",
                r"y_i = m_i(x - x_i)",
                r"x_s = \frac{m_2 x_2 - m_1 x_1}{m_2 - m_1}",
                r"s = m_i (x_s - x_i)",
                r"\theta = \arctan\left(\frac{m_1 - m_2}{1 + m_1 m_2}\right)",
            ]
        )
        return tex


class HingeMin(FitFunction):
    r"""Piecewise linear function with hinge point using minimum.

    The model consists of two linear segments joined at a hinge point:

    .. math::

        f(x) = \min(y_1, y_2)

    where:

    - :math:`y_1 = m_1 (x - x_1)`
    - :math:`y_2 = m_2 (x - x_2)`

    Both lines pass through the hinge point :math:`(h, y_h)` where
    :math:`y_h = m_1 (h - x_1)`. The second slope is constrained by:

    .. math::

        m_2 = m_1 \frac{h - x_1}{h - x_2}

    Parameters
    ----------
    xobs : array-like
        Independent variable observations.
    yobs : array-like
        Dependent variable observations.
    guess_h : float, optional
        Initial guess for hinge x-coordinate. Default is 400.0.
    **kwargs
        Additional arguments passed to :class:`FitFunction`.

    Attributes
    ----------
    m1 : float
        Slope of first line (fitted parameter).
    x1 : float
        x-intercept of first line (fitted parameter).
    x2 : float
        x-intercept of second line (fitted parameter).
    h : float
        x-coordinate of hinge point (fitted parameter).
    m2 : float
        Slope of second line (derived property).
    theta : float
        Angle between the two lines in radians (derived property).

    Examples
    --------
    >>> import numpy as np
    >>> from solarwindpy.fitfunctions import HingeMin
    >>> x = np.linspace(0, 15, 100)
    >>> y = np.minimum(2*(x-0), -2*(x-10))  # Two lines meeting at (5, 10)
    >>> fit = HingeMin(x, y, guess_h=5.0)
    >>> fit.make_fit()
    >>> print(f"Hinge at x={fit.popt['h']:.2f}")
    Hinge at x=5.00
    """

    def __init__(
        self,
        xobs,
        yobs,
        guess_h: float = 400.0,
        **kwargs,
    ):
        super().__init__(xobs, yobs, **kwargs)
        self._guess_h = guess_h

    @property
    def guess_h(self) -> float:
        r"""Initial guess for hinge x-coordinate used in p0 calculation."""
        return self._guess_h

    @property
    def function(self):
        r"""The hinge minimum function.

        Returns
        -------
        callable
            Function with signature ``f(x, m1, x1, x2, h)``.
        """

        def hinge(x, m1, x1, x2, h):
            r"""Evaluate hinge minimum model.

            Parameters
            ----------
            x : array-like
                Independent variable values.
            m1 : float
                Slope of first line.
            x1 : float
                x-intercept of first line.
            x2 : float
                x-intercept of second line.
            h : float
                x-coordinate of hinge point.

            Returns
            -------
            numpy.ndarray
                Model values at x.
            """
            m2 = m1 * (h - x1) / (h - x2)
            l1 = m1 * (x - x1)
            l2 = m2 * (x - x2)
            out = np.minimum(l1, l2)
            return out

        return hinge

    @property
    def m2(self) -> float:
        r"""Slope of the second line.

        Derived from the constraint that both lines pass through the hinge:

        .. math::

            m_2 = m_1 \frac{h - x_1}{h - x_2}
        """
        popt = self.popt
        h = popt["h"]
        m1 = popt["m1"]
        x1 = popt["x1"]
        x2 = popt["x2"]
        return m1 * (h - x1) / (h - x2)

    @property
    def theta(self) -> float:
        r"""Angle between the two lines in radians.

        Calculated using arctan2 for proper quadrant handling:

        .. math::

            \theta = \arctan2(m_1 - m_2, 1 + m_1 m_2)
        """
        m1 = self.popt["m1"]
        m2 = self.m2
        top = m1 - m2
        bottom = 1 + (m1 * m2)
        return np.arctan2(top, bottom)

    @property
    def p0(self) -> list:
        r"""Calculate initial parameter guess.

        The initial guess estimates slopes and intercepts from the data
        in regions separated by the hinge guess.

        Returns
        -------
        list
            Initial guesses as [m1, x1, x2, h].

        Raises
        ------
        AssertionError
            If insufficient data for estimation.

        Notes
        -----
        # TODO: Convert to data-driven p0 estimation (see GH issue #XX)
        Default guess_h=400 is appropriate for solar wind speed analysis.
        """
        assert self.sufficient_data

        x = self.observations.used.x
        y = self.observations.used.y
        h = self._guess_h

        # Estimate m1 and x1 from region below hinge
        tk_below = x < h
        if tk_below.sum() >= 2:
            m1_set = np.ediff1d(y[tk_below]) / np.ediff1d(x[tk_below])
            m1 = np.nanmedian(m1_set)
            x1 = np.nanmedian(x[tk_below] - (y[tk_below] / m1))
        else:
            # Fall back to simple estimate
            m1 = (y.max() - y.min()) / (x.max() - x.min())
            x1 = x.min()

        # Estimate m2 and x2 from plateau region
        tk_above = x >= h
        if tk_above.sum() >= 2:
            m2 = np.median(np.ediff1d(y[tk_above]) / np.ediff1d(x[tk_above]))
            x2 = np.median(x[tk_above] - (y[tk_above] / m2))
        else:
            m2 = 0.0
            x2 = h

        p0 = [m1, x1, x2, h]
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
                r"f(x)=\min(m_1(x-x_1), \, m_2(x-x_2))",
                r"m_2 = m_1 \frac{h - x_1}{h - x_2}",
            ]
        )
        return tex


class HingeMax(FitFunction):
    r"""Piecewise linear function with hinge point using maximum.

    The model consists of two linear segments joined at a hinge point:

    .. math::

        f(x) = \max(y_1, y_2)

    where:

    - :math:`y_1 = m_1 (x - x_1)`
    - :math:`y_2 = m_2 (x - x_2)`

    Both lines pass through the hinge point :math:`(h, y_h)` where
    :math:`y_h = m_1 (h - x_1)`. The second slope is constrained by:

    .. math::

        m_2 = m_1 \frac{h - x_1}{h - x_2}

    This is the same as :class:`HingeMin` but uses ``np.maximum`` instead
    of ``np.minimum``, suitable for V-shaped patterns opening upward.

    Parameters
    ----------
    xobs : array-like
        Independent variable observations.
    yobs : array-like
        Dependent variable observations.
    guess_h : float, optional
        Initial guess for hinge x-coordinate. Default is 400.0.
    **kwargs
        Additional arguments passed to :class:`FitFunction`.

    Attributes
    ----------
    m1 : float
        Slope of first line (fitted parameter).
    x1 : float
        x-intercept of first line (fitted parameter).
    x2 : float
        x-intercept of second line (fitted parameter).
    h : float
        x-coordinate of hinge point (fitted parameter).
    m2 : float
        Slope of second line (derived property).
    theta : float
        Angle between the two lines in radians (derived property).

    Examples
    --------
    >>> import numpy as np
    >>> from solarwindpy.fitfunctions import HingeMax
    >>> x = np.linspace(0, 15, 100)
    >>> y = np.maximum(-2*(x-0), 2*(x-10))  # V-shape with vertex at (5, -10)
    >>> fit = HingeMax(x, y, guess_h=5.0)
    >>> fit.make_fit()
    >>> print(f"Hinge at x={fit.popt['h']:.2f}")
    Hinge at x=5.00
    """

    def __init__(
        self,
        xobs,
        yobs,
        guess_h: float = 400.0,
        **kwargs,
    ):
        super().__init__(xobs, yobs, **kwargs)
        self._guess_h = guess_h

    @property
    def guess_h(self) -> float:
        r"""Initial guess for hinge x-coordinate used in p0 calculation."""
        return self._guess_h

    @property
    def function(self):
        r"""The hinge maximum function.

        Returns
        -------
        callable
            Function with signature ``f(x, m1, x1, x2, h)``.
        """

        def hinge(x, m1, x1, x2, h):
            r"""Evaluate hinge maximum model.

            Parameters
            ----------
            x : array-like
                Independent variable values.
            m1 : float
                Slope of first line.
            x1 : float
                x-intercept of first line.
            x2 : float
                x-intercept of second line.
            h : float
                x-coordinate of hinge point.

            Returns
            -------
            numpy.ndarray
                Model values at x.
            """
            m2 = m1 * (h - x1) / (h - x2)
            l1 = m1 * (x - x1)
            l2 = m2 * (x - x2)
            out = np.maximum(l1, l2)
            return out

        return hinge

    @property
    def m2(self) -> float:
        r"""Slope of the second line.

        Derived from the constraint that both lines pass through the hinge:

        .. math::

            m_2 = m_1 \frac{h - x_1}{h - x_2}
        """
        popt = self.popt
        h = popt["h"]
        m1 = popt["m1"]
        x1 = popt["x1"]
        x2 = popt["x2"]
        return m1 * (h - x1) / (h - x2)

    @property
    def theta(self) -> float:
        r"""Angle between the two lines in radians.

        Calculated using arctan2 for proper quadrant handling:

        .. math::

            \theta = \arctan2(m_1 - m_2, 1 + m_1 m_2)
        """
        m1 = self.popt["m1"]
        m2 = self.m2
        top = m1 - m2
        bottom = 1 + (m1 * m2)
        return np.arctan2(top, bottom)

    @property
    def p0(self) -> list:
        r"""Calculate initial parameter guess.

        The initial guess estimates slopes and intercepts from the data
        in regions separated by the hinge guess.

        Returns
        -------
        list
            Initial guesses as [m1, x1, x2, h].

        Raises
        ------
        AssertionError
            If insufficient data for estimation.

        Notes
        -----
        # TODO: Convert to data-driven p0 estimation (see GH issue #XX)
        Default guess_h=400 is appropriate for solar wind speed analysis.
        """
        assert self.sufficient_data

        x = self.observations.used.x
        y = self.observations.used.y
        h = self._guess_h

        # Estimate m1 and x1 from region below hinge
        tk_below = x < h
        if tk_below.sum() >= 2:
            m1_set = np.ediff1d(y[tk_below]) / np.ediff1d(x[tk_below])
            m1 = np.nanmedian(m1_set)
            x1 = np.nanmedian(x[tk_below] - (y[tk_below] / m1))
        else:
            # Fall back to simple estimate
            m1 = (y.max() - y.min()) / (x.max() - x.min())
            x1 = x.min()

        # Estimate m2 and x2 from plateau region
        tk_above = x >= h
        if tk_above.sum() >= 2:
            m2 = np.median(np.ediff1d(y[tk_above]) / np.ediff1d(x[tk_above]))
            x2 = np.median(x[tk_above] - (y[tk_above] / m2))
        else:
            m2 = 0.0
            x2 = h

        p0 = [m1, x1, x2, h]
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
                r"f(x)=\max(m_1(x-x_1), \, m_2(x-x_2))",
                r"m_2 = m_1 \frac{h - x_1}{h - x_2}",
            ]
        )
        return tex


class HingeAtPoint(FitFunction):
    r"""Piecewise linear function passing through a specified hinge point.

    The model consists of two linear segments that both pass through the
    hinge point :math:`(x_h, y_h)`:

    .. math::

        f(x) = \min(y_1, y_2)

    where:

    - :math:`y_1 = m_1 (x - x_1)` with :math:`x_1 = x_h - y_h / m_1`
    - :math:`y_2 = m_2 (x - x_2)` with :math:`x_2 = x_h - y_h / m_2`

    Parameters
    ----------
    xobs : array-like
        Independent variable observations.
    yobs : array-like
        Dependent variable observations.
    guess_xh : float, optional
        Initial guess for hinge x-coordinate. Default is 400.0.
    guess_yh : float, optional
        Initial guess for hinge y-coordinate. Default is 0.5.
    **kwargs
        Additional arguments passed to :class:`FitFunction`.

    Attributes
    ----------
    xh : float
        x-coordinate of hinge point (fitted parameter).
    yh : float
        y-coordinate of hinge point (fitted parameter).
    m1 : float
        Slope of first line (fitted parameter).
    m2 : float
        Slope of second line (fitted parameter).
    x_intercepts : XIntercepts
        Named tuple with x1 and x2 attributes (derived property).

    Examples
    --------
    >>> import numpy as np
    >>> from solarwindpy.fitfunctions import HingeAtPoint
    >>> x = np.linspace(0, 15, 100)
    >>> y = np.minimum(2*(x-0), -1*(x-15))  # Hinge at (5, 10)
    >>> fit = HingeAtPoint(x, y, guess_xh=5.0, guess_yh=10.0)
    >>> fit.make_fit()
    >>> print(f"Hinge at ({fit.popt['xh']:.2f}, {fit.popt['yh']:.2f})")
    Hinge at (5.00, 10.00)
    """

    def __init__(
        self,
        xobs,
        yobs,
        guess_xh: float = 400.0,
        guess_yh: float = 0.5,
        **kwargs,
    ):
        super().__init__(xobs, yobs, **kwargs)
        self._hinge_guess = (guess_xh, guess_yh)

    @property
    def hinge_guess(self) -> tuple[float, float]:
        r"""Guess for hinge point (xh, yh) used in p0 calculation."""
        return self._hinge_guess

    @property
    def function(self):
        r"""The hinge-at-point function.

        Returns
        -------
        callable
            Function with signature ``f(x, xh, yh, m1, m2)``.
        """

        def hinge_at_point(x, xh, yh, m1, m2):
            r"""Evaluate hinge-at-point model.

            Parameters
            ----------
            x : array-like
                Independent variable values.
            xh : float
                x-coordinate of hinge point.
            yh : float
                y-coordinate of hinge point.
            m1 : float
                Slope of first line.
            m2 : float
                Slope of second line.

            Returns
            -------
            numpy.ndarray
                Model values at x.
            """
            x1 = xh - (yh / m1)
            x2 = xh - (yh / m2)

            y1 = m1 * (x - x1)
            y2 = m2 * (x - x2)

            out = np.minimum(y1, y2)
            return out

        return hinge_at_point

    @property
    def x_intercepts(self) -> XIntercepts:
        r"""x-intercepts of the two lines.

        Returns a named tuple with:

        - x1 = xh - yh / m1
        - x2 = xh - yh / m2
        """
        popt = self.popt
        xh = popt["xh"]
        yh = popt["yh"]
        m1 = popt["m1"]
        m2 = popt["m2"]
        x1 = xh - (yh / m1)
        x2 = xh - (yh / m2)
        return XIntercepts(x1, x2)

    @property
    def p0(self) -> list:
        r"""Calculate initial parameter guess.

        The initial guess uses the hinge_guess for (xh, yh) and estimates
        slopes from the data in regions separated by the hinge guess.

        Returns
        -------
        list
            Initial guesses as [xh, yh, m1, m2].

        Raises
        ------
        AssertionError
            If insufficient data for estimation.

        Notes
        -----
        # TODO: Convert to data-driven p0 estimation (see GH issue #XX)
        Default guess_xh=400 and guess_yh=0.5 are appropriate for solar
        wind speed analysis.
        """
        assert self.sufficient_data

        xh, yh_guess = self._hinge_guess

        x = self.observations.used.x
        y = self.observations.used.y

        # Estimate yh from data near the hinge point
        yh = y[np.argmin(np.abs(x - xh))]

        # Estimate m1 from region below hinge
        tk_below = x < xh
        if tk_below.sum() >= 2:
            m1_set = np.ediff1d(y[tk_below]) / np.ediff1d(x[tk_below])
            m1 = np.nanmedian(m1_set)
        else:
            # Fall back to simple estimate
            m1 = yh / (xh - x.min()) if xh > x.min() else 1.0

        # Estimate m2 from region above hinge
        tk_above = x >= xh
        if tk_above.sum() >= 2:
            m2 = np.median(np.ediff1d(y[tk_above]) / np.ediff1d(x[tk_above]))
        else:
            m2 = 0.0

        p0 = [xh, yh, m1, m2]
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
                r"x_i = x_h - \frac{y_h}{m_i}",
            ]
        )
        return tex
