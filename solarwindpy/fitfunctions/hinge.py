r"""Hinge (piecewise linear) fit functions.

This module provides fit functions for piecewise linear models with a
hinge point, commonly used for modeling saturation behavior. Each is a
subclass of :class:`Hinge`, which holds what they share.
"""

from __future__ import annotations

__all__ = [
    "HingeSaturation",
    "TwoLine",
    "Saturation",
    "HingeMin",
    "HingeMax",
    "HingeAtPoint",
]

from abc import abstractmethod
from collections import namedtuple

import numpy as np

from .core import FitFunction

# Named tuple for x-intercepts used by HingeAtPoint
_XIntercepts = namedtuple("_XIntercepts", "x1,x2")


def _slopes(x, y):
    r"""Slopes between consecutive points, checked before dividing.

    Where ``x`` repeats, the slope is infinite in the sign of the rise (a
    vertical step), or NaN when ``y`` repeats too (no line).
    """
    dx = np.ediff1d(x)
    dy = np.ediff1d(y)
    out = np.where(dy == 0, np.nan, np.copysign(np.inf, dy))
    np.divide(dy, dx, out=out, where=dx != 0)
    return out


def _median_slope(x, y, skip_nan=True):
    r"""The median of :func:`_slopes`, or NaN when it is undefined.

    With ``skip_nan``, slopes between repeated points are left out; without
    it, any one makes the median undefined. The median is also undefined
    when there is no slope, or when the middle two are vertical steps in
    opposite directions. A vertical step at the middle otherwise gives an
    infinite median.
    """
    slopes = _slopes(x, y)
    nan = np.isnan(slopes)
    if skip_nan:
        slopes = slopes[~nan]
    elif nan.any():
        return np.nan
    if not slopes.size:
        return np.nan
    slopes = np.sort(slopes)
    lo, hi = slopes[(slopes.size - 1) // 2], slopes[slopes.size // 2]
    if np.isinf(lo) and np.isinf(hi) and lo != hi:
        return np.nan
    return np.median(slopes)


def _x_intercept(x, y, m):
    r"""The median x-intercept of lines of slope ``m`` through each point.

    NaN when ``m`` is zero or NaN: a flat line has no x-intercept. For an
    infinite ``m`` (vertical lines) it is the median ``x``.
    """
    if m == 0 or np.isnan(m):
        return np.nan
    return np.median(x - (y / m))


class Hinge(FitFunction):
    r"""Two lines that meet at a hinge: the parent of the hinge fit functions.

    A subclass writes its model (``function`` and ``TeX_function``), its
    estimate (``_estimate``) and the translation of the reference hinge to its
    parameters (``_reference_start``), and describes both in its class Notes.
    ``p0`` is shared: it returns the estimate, or the reference start when the
    data give no estimate.

    Notes
    -----
    When the data give no estimate, the all-ones default start is a singular
    point of these models (the two lines' intercepts coincide), so ``p0``
    logs a warning and returns the package author's reference hinge instead,
    translated to the class's parameters: the hinge
    :math:`(x_h, y_h) = (433, 4.12)`, the rising line's x-intercept
    :math:`x_1 = 250`, its slope :math:`m_1 = y_h / (x_h - x_1) = 4.12 / 183`,
    a small non-zero plateau slope :math:`m_2 = 0.01\,m_1`, and the plateau
    line's x-intercept :math:`x_2 = x_h - y_h / m_2 = -17867`, which puts that
    line through the hinge.

    Examples
    --------
    Every hinge fit function shares ``p0``, shown here with :class:`TwoLine`,
    whose parameters are ``[x1, x2, m1, m2]``. Two lines meeting at (5, 10),
    with data on both sides of ``guess_xs``, give the estimate:

    >>> import numpy as np
    >>> from solarwindpy.fitfunctions.hinge import TwoLine
    >>> x = np.linspace(0, 15, 100)
    >>> y = np.minimum(2 * x, -(x - 15))
    >>> [f"{v:.4g}" for v in TwoLine(x, y, guess_xs=5.0).p0]
    ['0', '15', '2', '-1']

    With ``guess_xs`` past every point, the second line has no data and no
    estimate, so ``p0`` logs a warning and returns the reference hinge:

    >>> [f"{v:.4g}" for v in TwoLine(x, y, guess_xs=20.0).p0]
    ['250', '-1.787e+04', '0.02251', '0.0002251']
    """

    # The author's reference hinge, described in the class Notes.
    _XH = 433.0
    _YH = 4.12
    _X1 = 250.0
    _M1 = _YH / (_XH - _X1)
    _M2 = 0.01 * _M1
    _X2 = _XH - _YH / _M2

    @property
    def p0(self) -> list:
        r"""The initial guess: the estimate from the data, or the reference start.

        ``p0`` returns the class's estimate from the used observations, or,
        when the data give no estimate, the class's reference start. The
        class description (its Notes) states how the class estimates, when an
        estimate is undefined, and what its reference start is.

        Returns
        -------
        list of float
            One finite guess per parameter, in :attr:`argnames` order. When
            the data give no estimate (an estimate is NaN or infinite),
            ``p0`` logs a warning naming the undefined estimates and returns
            the class's reference start instead. It never returns None.

        Raises
        ------
        ~solarwindpy.fitfunctions.core.InsufficientDataError
            If fewer observations are used than the model has parameters.
        NotImplementedError
            If the data give no estimate and the class has no reference start
            yet (:class:`HingeMax`); no warning is logged first. Pass ``p0=``
            to :meth:`~solarwindpy.fitfunctions.core.FitFunction.make_fit`.
        """
        self._require_sufficient_data()
        estimate = self._estimate()
        bad = {
            name: value
            for name, value in zip(self.argnames, estimate)
            if not np.isfinite(value)
        }
        if bad:
            # A class with no reference start raises here, before the warning.
            start = self._reference_start()
            self.logger.warning(
                f"The data gave no estimate. Undefined estimates {bad}; "
                f"the {type(self).__name__} class description states when an "
                "estimate is undefined."
            )
            return start
        return estimate

    @abstractmethod
    def _estimate(self):
        r"""Estimate every parameter from the used observations.

        The estimates are in ``argnames`` order; one the data cannot give is
        NaN or infinite. The class Notes describe the estimate.
        """

    @abstractmethod
    def _reference_start(self):
        r"""Return the reference hinge in the class's parameters, in ``argnames`` order.

        The class Notes give the translation.
        """


class HingeSaturation(Hinge):
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
        Additional arguments passed to
        :class:`~solarwindpy.fitfunctions.core.FitFunction`.

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

    Notes
    -----
    ``p0`` estimates ``[xh, yh, x1, m2]`` from the data. ``(xh, yh)`` is
    ``saturation_guess``; ``x1`` comes from a linear fit to the rising region
    (x < xh), or is the data minimum when that region has fewer than two
    points or the fit is flat, and is undefined when the region's points
    share one ``x`` (no slope); ``m2`` is the median slope in the plateau
    region (x >= xh), and is undefined when the plateau region has repeated
    ``x``. When an estimate is undefined, ``p0`` returns the reference hinge
    of :class:`Hinge` as ``[xh, yh, x1, m2]``.

    Examples
    --------
    >>> import numpy as np
    >>> from solarwindpy.fitfunctions.hinge import HingeSaturation
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

    def _estimate(self):
        xh, yh = self.saturation_guess

        x = self.observations.used.x
        y = self.observations.used.y

        # Estimate x1 from data in rising region
        # m1 = yh / (xh - x1), so x1 = xh - yh/m1
        rising_mask = x < xh
        if rising_mask.sum() >= 2:
            x_rising = x[rising_mask]
            y_rising = y[rising_mask]
            if np.unique(x_rising).size < 2:
                # Repeated x has no slope: polyfit would raise or warn.
                x1 = np.nan
            else:
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
            m2 = _median_slope(x[plateau_mask], y[plateau_mask], skip_nan=False)
        else:
            m2 = 0.0

        return [xh, yh, x1, m2]

    def _reference_start(self):
        return [self._XH, self._YH, self._X1, self._M2]

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


class TwoLine(Hinge):
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
        Additional arguments passed to
        :class:`~solarwindpy.fitfunctions.core.FitFunction`.

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

    Notes
    -----
    ``p0`` estimates ``[x1, x2, m1, m2]`` from the data on each side of
    ``guess_xs``. Each side needs at least two points with distinct ``x`` for
    a slope, and a nonzero slope for an x-intercept; otherwise an estimate is
    undefined, and ``p0`` returns the reference hinge of :class:`Hinge` as
    ``[x1, x2, m1, m2]``. The default ``guess_xs=425`` is appropriate for
    solar wind speed analysis.

    Examples
    --------
    >>> import numpy as np
    >>> from solarwindpy.fitfunctions.hinge import TwoLine
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

    def _estimate(self):
        x = self.observations.used.x
        y = self.observations.used.y

        # TODO: Convert to data-driven p0 estimation (see GH issue #XX)
        xs = self._guess_xs
        tk = x <= xs

        m1 = _median_slope(x[tk], y[tk])
        x1 = _x_intercept(x[tk], y[tk], m1)
        m2 = _median_slope(x[~tk], y[~tk])
        x2 = _x_intercept(x[~tk], y[~tk], m2)

        return [x1, x2, m1, m2]

    def _reference_start(self):
        return [self._X1, self._X2, self._M1, self._M2]

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


class Saturation(Hinge):
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
        Additional arguments passed to
        :class:`~solarwindpy.fitfunctions.core.FitFunction`.

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

    Notes
    -----
    ``p0`` estimates ``[x1, xs, s, theta]`` from the data on each side of
    ``xs``, the first element of ``saturation_guess``. Each side needs at
    least two points with distinct ``x`` for a slope, and the rising side a
    nonzero slope for ``x1``; otherwise an estimate is undefined, and ``p0``
    returns the reference hinge of :class:`Hinge` as
    ``[x1, xs, s, theta] = [x1, xh, yh, theta]``, where
    :math:`\theta = \arctan(m_1) - \arctan(m_2)` inverts the model's
    :math:`m_2 = \tan(\arctan(m_1) - \theta)`. The default ``guess_xs=425``
    is appropriate for solar wind speed analysis.

    Examples
    --------
    >>> import numpy as np
    >>> from solarwindpy.fitfunctions.hinge import Saturation
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

    def _estimate(self):
        def estimate_line(x, y):
            m = _median_slope(x, y)
            x0 = _x_intercept(x, y, m)
            # A vertical line (infinite m) gives no saturation value.
            s = m * (xs - x0) if np.isfinite(m) else np.nan
            return x0, m, s

        x = self.observations.used.x
        y = self.observations.used.y

        # TODO: Convert to data-driven p0 estimation (see GH issue #XX)
        xs, _ = self.saturation_guess
        tk = x <= xs

        x1, m1, s1 = estimate_line(x[tk], y[tk])
        x2, m2, s2 = estimate_line(x[~tk], y[~tk])

        s = np.nan if np.isnan([s1, s2]).all() else np.nanmedian([s1, s2])
        if not (np.isfinite(m1) and np.isfinite(m2)):
            theta = np.nan
        elif 1 + m1 * m2 == 0:
            # Perpendicular lines: the arctan argument is infinite. The exact
            # test is intentional, not an isclose candidate: near-perpendicular
            # lines give a large finite argument, which arctan handles.
            theta = np.copysign(np.pi / 2, m1 - m2)
        else:
            theta = np.arctan((m1 - m2) / (1 + m1 * m2))

        return [x1, xs, s, theta]

    def _reference_start(self):
        theta = np.arctan(self._M1) - np.arctan(self._M2)
        return [self._X1, self._XH, self._YH, theta]

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


class HingeMin(Hinge):
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
        Additional arguments passed to
        :class:`~solarwindpy.fitfunctions.core.FitFunction`.

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

    Notes
    -----
    ``p0`` estimates ``[m1, x1, x2, h]`` from the data on each side of
    ``guess_h``, with ``h = guess_h``. Each side with two or more points
    needs distinct ``x`` for a slope and a nonzero slope for an x-intercept;
    with fewer, ``m1`` falls back to the slope across the x range, which
    needs distinct ``x``. Otherwise an estimate is undefined, and ``p0``
    returns the reference hinge of :class:`Hinge` as ``[m1, x1, x2, h]``
    with ``h = xh``; the model's :math:`m_2 = m_1 (h - x_1) / (h - x_2)`
    then recovers the reference :math:`m_2`. The default ``guess_h=400`` is
    appropriate for solar wind speed analysis.

    Examples
    --------
    >>> import numpy as np
    >>> from solarwindpy.fitfunctions.hinge import HingeMin
    >>> x = np.linspace(0, 15, 100)
    >>> y = np.minimum(2*(x-0), -2*(x-10))  # Two lines meeting at (5, 10)
    >>> fit = HingeMin(x, y, guess_h=5.0)
    >>> fit.make_fit()
    >>> print(f"Hinge at x={fit.popt['h']:.2f}")
    Hinge at x=5.00
    """

    # The model combines the two lines with this; HingeMax uses np.maximum.
    _combine = staticmethod(np.minimum)

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
        r"""The hinge function.

        Returns
        -------
        callable
            Function with signature ``f(x, m1, x1, x2, h)``.
        """
        combine = self._combine

        def hinge(x, m1, x1, x2, h):
            r"""Evaluate the hinge model.

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
            out = combine(l1, l2)
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

    def _estimate(self):
        x = self.observations.used.x
        y = self.observations.used.y
        h = self._guess_h

        # Estimate m1 and x1 from region below hinge
        tk_below = x < h
        if tk_below.sum() >= 2:
            m1 = _median_slope(x[tk_below], y[tk_below])
            x1 = _x_intercept(x[tk_below], y[tk_below], m1)
        else:
            # Fall back to simple estimate
            m1 = _median_slope(
                np.array([x.min(), x.max()]), np.array([y.min(), y.max()])
            )
            x1 = x.min()

        # Estimate m2 and x2 from plateau region
        tk_above = x >= h
        if tk_above.sum() >= 2:
            m2 = _median_slope(x[tk_above], y[tk_above], skip_nan=False)
            x2 = _x_intercept(x[tk_above], y[tk_above], m2)
        else:
            m2 = 0.0
            x2 = h

        return [m1, x1, x2, h]

    def _reference_start(self):
        return [self._M1, self._X1, self._X2, self._XH]

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


class HingeMax(HingeMin):
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

    This is :class:`HingeMin` with ``np.maximum`` instead of ``np.minimum``,
    suitable for V-shaped patterns opening upward. It shares HingeMin's
    parameters, estimate and derived properties.

    Notes
    -----
    ``p0`` estimates ``[m1, x1, x2, h]`` as :class:`HingeMin` does, and an
    estimate is undefined in the same cases. HingeMax has no reference start
    yet: its shape differs from the reference hinge of :class:`Hinge` that
    the other hinge classes start from when the data give no estimate, and
    the author has not chosen one. In that case ``p0`` raises
    ``NotImplementedError`` without logging a warning; pass ``p0=`` to
    :meth:`~solarwindpy.fitfunctions.core.FitFunction.make_fit`.

    Examples
    --------
    >>> import numpy as np
    >>> from solarwindpy.fitfunctions.hinge import HingeMax
    >>> x = np.linspace(0, 15, 100)
    >>> y = np.maximum(-2*(x-0), 2*(x-10))  # V-shape with vertex at (5, -10)
    >>> fit = HingeMax(x, y, guess_h=5.0)
    >>> fit.make_fit()
    >>> print(f"Hinge at x={fit.popt['h']:.2f}")
    Hinge at x=5.00
    """

    _combine = staticmethod(np.maximum)

    def _reference_start(self):
        raise NotImplementedError(
            "HingeMax has no reference start defined yet; pass p0= to make_fit."
        )

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


class HingeAtPoint(Hinge):
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
        Additional arguments passed to
        :class:`~solarwindpy.fitfunctions.core.FitFunction`.

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
    x_intercepts : tuple
        Named tuple with x1 and x2 attributes (derived property).

    Notes
    -----
    ``p0`` estimates ``[xh, yh, m1, m2]`` from the data on each side of
    ``xh``, the first element of ``hinge_guess``: ``yh`` is the ``y`` at the
    observation nearest ``xh``, and the slopes come from each side of it. A
    side with two or more points needs distinct ``x`` for a slope; otherwise
    a slope is undefined, and ``p0`` returns the reference hinge of
    :class:`Hinge` as ``[xh, yh, m1, m2]``. The defaults ``guess_xh=400``
    and ``guess_yh=0.5`` are appropriate for solar wind speed analysis.

    Examples
    --------
    >>> import numpy as np
    >>> from solarwindpy.fitfunctions.hinge import HingeAtPoint
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
    def x_intercepts(self) -> tuple[float, float]:
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
        return _XIntercepts(x1, x2)

    def _estimate(self):
        xh, yh_guess = self._hinge_guess

        x = self.observations.used.x
        y = self.observations.used.y

        # Estimate yh from data near the hinge point
        yh = y[np.argmin(np.abs(x - xh))]

        # Estimate m1 from region below hinge
        tk_below = x < xh
        if tk_below.sum() >= 2:
            m1 = _median_slope(x[tk_below], y[tk_below])
        else:
            # Fall back to simple estimate
            m1 = yh / (xh - x.min()) if xh > x.min() else 1.0

        # Estimate m2 from region above hinge
        tk_above = x >= xh
        if tk_above.sum() >= 2:
            m2 = _median_slope(x[tk_above], y[tk_above], skip_nan=False)
        else:
            m2 = 0.0

        return [xh, yh, m1, m2]

    def _reference_start(self):
        return [self._XH, self._YH, self._M1, self._M2]

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
