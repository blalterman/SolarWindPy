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


def _y_near(x, y, xh):
    r"""The ``y`` of the observation whose ``x`` is nearest ``xh``."""
    return y[np.argmin(np.abs(x - xh))]


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

    Parameters
    ----------
    xobs : array-like
        Independent variable observations.
    yobs : array-like
        Dependent variable observations.
    guess_xh : float, optional
        The x of the hinge, ``xh``, where the estimate splits the data between
        the two lines. None, the default, estimates it from the data as the
        median used x. A full start goes to
        :meth:`~solarwindpy.fitfunctions.core.FitFunction.make_fit` as
        ``p0=``, as in every fit function.
    **kwargs
        Passed to :class:`~solarwindpy.fitfunctions.core.FitFunction`.

    Notes
    -----
    When the data give no estimate, the all-ones default start is a singular
    point of these models (the two lines' intercepts coincide), so ``p0``
    logs a warning and returns the reference hinge instead, translated to the
    class's parameters. The reference hinge is the package author's fit of
    the Wind:SWE helium abundance against solar wind speed,
    https://doi.org/10.3847/2041-8213/adb48e: the saturation point
    :math:`(x_h, y_h) = (433, 4.19)` (uncertainties 4 and 0.05), the rising
    line's x-intercept, the vanishing speed, :math:`x_1 = 302` (uncertainty
    4), and the fast-wind slope :math:`m_2 = 0.0010` (uncertainty 0.0002).
    The rising line's slope :math:`m_1 = y_h / (x_h - x_1) = 4.19 / 131` and
    the plateau line's x-intercept :math:`x_2 = x_h - y_h / m_2 = -3757`,
    which puts that line through the hinge, follow from them.

    The same reference hinge is a useful explicit start for solar wind speed
    trends: ``HingeAtPoint(v, y, guess_xh=433)`` splits at 433 km/s, and
    ``make_fit(p0=...)`` starts from the full hinge when :math:`y_h = 4.19`
    matters too. It is a usage note: it is not ``guess_xh``'s default.

    Examples
    --------
    Every hinge fit function shares ``p0``, shown here with :class:`TwoLine`,
    whose parameters are ``[x1, x2, m1, m2]``. Two lines meeting at (5, 10),
    with data on both sides of ``guess_xh``, give the estimate:

    >>> import numpy as np
    >>> from solarwindpy.fitfunctions.hinge import TwoLine
    >>> x = np.linspace(0, 15, 100)
    >>> y = np.minimum(2 * x, -(x - 15))
    >>> [f"{v:.4g}" for v in TwoLine(x, y, guess_xh=5.0).p0]
    ['0', '15', '2', '-1']

    With ``guess_xh`` past every point, the second line has no data and no
    estimate, so ``p0`` logs a warning and returns the reference hinge:

    >>> [f"{v:.4g}" for v in TwoLine(x, y, guess_xh=20.0).p0]
    ['302', '-3757', '0.03198', '0.001']
    """

    # The reference hinge, described and cited in the class Notes: the
    # paper's four fitted values, and the two parameters derived from them.
    _XH = 433.0
    _YH = 4.19
    _X1 = 302.0
    _M2 = 0.0010
    _M1 = _YH / (_XH - _X1)
    _X2 = _XH - _YH / _M2

    #: TeX of every hinge parameter, as the model strings write it.
    _HINGE_TEX = {
        "xh": "x_h",
        "yh": "y_h",
        "x1": "x_1",
        "x2": "x_2",
        "m1": "m_1",
        "m2": "m_2",
        "theta": r"\theta",
    }

    def __init__(self, xobs, yobs, guess_xh=None, **kwargs):
        # Documented in the class docstring (see FitFunctionMeta).
        super().__init__(xobs, yobs, **kwargs)
        self._guess_xh = guess_xh

    @property
    def _TeX_argnames(self):
        r"""The TeX of this class's parameters, e.g. ``xh`` as ``x_h``."""
        return {name: self._HINGE_TEX[name] for name in self.argnames}

    @property
    def guess_xh(self):
        r"""The hinge x given at construction, or None to estimate it from the data."""
        return self._guess_xh

    def _split_x(self):
        r"""Where the estimate splits the data: :attr:`guess_xh`, or the median used x."""
        if self.guess_xh is not None:
            return self.guess_xh
        return float(np.median(self.observations.used.x))

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
        """
        self._require_sufficient_data()
        estimate = self._estimate()
        bad = {
            name: value
            for name, value in zip(self.argnames, estimate)
            if not np.isfinite(value)
        }
        if bad:
            self.logger.warning(
                f"The data gave no estimate. Undefined estimates {bad}; "
                f"the {type(self).__name__} class description states when an "
                "estimate is undefined."
            )
            return self._reference_start()
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
    ``p0`` estimates ``[xh, yh, x1, m2]`` from the data. ``xh`` is the split
    (``guess_xh``, or the median used x) and ``yh`` the ``y`` of the
    observation nearest it; ``x1`` comes from a linear fit to the rising region
    (x < xh), or is the data minimum when that region has fewer than two
    points or the fit is flat, and is undefined when the region's points
    share one ``x`` (no slope); ``m2`` is the median slope in the plateau
    region (x >= xh), is 0 when that region has fewer than two points, and
    is undefined when it has repeated ``x``. When an estimate is undefined,
    ``p0`` returns the reference hinge of :class:`Hinge` as
    ``[xh, yh, x1, m2]``. Unlike :class:`HingeMin` and :class:`HingeAtPoint`,
    a short region keeps its own fallback: ``m2 = 0`` is a flat plateau at
    ``yh``, which the model evaluates directly, so that start is not
    singular.

    Examples
    --------
    >>> import numpy as np
    >>> from solarwindpy.fitfunctions.hinge import HingeSaturation
    >>> x = np.linspace(0, 15, 100)
    >>> y = np.where(x < 5, 2*x, 10)  # Saturation at y=10 for x>=5
    >>> fit = HingeSaturation(x, y, guess_xh=5)
    >>> fit.make_fit()
    >>> print(f"Hinge at ({fit.popt['xh']:.2f}, {fit.popt['yh']:.2f})")
    Hinge at (5.00, 10.00)
    """

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
        x = self.observations.used.x
        y = self.observations.used.y
        xh = self._split_x()
        yh = _y_near(x, y, xh)

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

    The lines intersect at the saturation point :math:`(x_h, y_h)` where:

    - :math:`x_h = \frac{m_1 x_1 - m_2 x_2}{m_1 - m_2}`
    - :math:`y_h = m_1 (x_h - x_1) = m_2 (x_h - x_2)`

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
    xh : float
        x-coordinate of intersection point (derived property).
    yh : float
        y-coordinate of intersection point (derived property).
    theta : float
        Angle between the two lines in radians (derived property).

    Notes
    -----
    ``p0`` estimates ``[x1, x2, m1, m2]`` from the data on each side of the
    split (``guess_xh``, or the median used x): at or below it and above it. A repeated
    point has no slope and is skipped. Each side needs at least two points
    with distinct ``x`` for a slope, and a nonzero slope for an x-intercept;
    otherwise an estimate is undefined, and ``p0`` returns the reference
    hinge of :class:`Hinge` as ``[x1, x2, m1, m2]``.

    Examples
    --------
    >>> import numpy as np
    >>> from solarwindpy.fitfunctions.hinge import TwoLine
    >>> x = np.linspace(0, 15, 100)
    >>> y = np.minimum(2*(x-0), -1*(x-15))  # Two lines intersecting at (5, 10)
    >>> fit = TwoLine(x, y, guess_xh=5.0)
    >>> fit.make_fit()
    >>> print(f"Intersection at ({fit.xh:.2f}, {fit.yh:.2f})")
    Intersection at (5.00, 10.00)
    """

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
    def xh(self) -> float:
        r"""x-coordinate of the intersection (saturation) point.

        Calculated as:

        .. math::

            x_h = \frac{m_1 x_1 - m_2 x_2}{m_1 - m_2}
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
    def yh(self) -> float:
        r"""y-coordinate of the intersection (saturation) point.

        Calculated as:

        .. math::

            y_h = m_1 (x_h - x_1)
        """
        popt = self.popt
        x1 = popt["x1"]
        m1 = popt["m1"]
        xh = self.xh
        return m1 * (xh - x1)

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

        xh = self._split_x()
        tk = x <= xh

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

    Parameters are :math:`(x_1, x_h, y_h, \theta)` where:

    - :math:`x_1`: x-intercept of the rising line
    - :math:`x_h`: x-coordinate of saturation point
    - :math:`y_h`: y-coordinate of saturation point
    - :math:`\theta`: angle between the two lines (radians)

    The slopes are derived as:

    - :math:`m_1 = y_h / (x_h - x_1)`
    - :math:`m_2 = \tan(\arctan(m_1) - \theta)`

    Attributes
    ----------
    x1 : float
        x-intercept of rising line (fitted parameter).
    xh : float
        x-coordinate of saturation point (fitted parameter).
    yh : float
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
    ``p0`` estimates ``[x1, xh, yh, theta]`` from the data on each side of
    ``xh``, the split (``guess_xh``, or the median used x): at or below it
    and above it. Each side
    needs at least two points with distinct ``x`` for a slope, and the
    rising side a nonzero slope for ``x1``; otherwise an estimate is
    undefined, and ``p0`` returns the reference hinge of :class:`Hinge` as
    ``[x1, xh, yh, theta]``, where
    :math:`\theta = \arctan(m_1) - \arctan(m_2)` inverts the model's
    :math:`m_2 = \tan(\arctan(m_1) - \theta)`.

    Examples
    --------
    >>> import numpy as np
    >>> from solarwindpy.fitfunctions.hinge import Saturation
    >>> x = np.linspace(0, 15, 100)
    >>> y = np.minimum(2*(x-0), -1*(x-15))
    >>> fit = Saturation(x, y, guess_xh=5.0)
    >>> fit.make_fit()
    >>> print(f"Saturation at ({fit.popt['xh']:.2f}, {fit.popt['yh']:.2f})")
    Saturation at (5.00, 10.00)
    """

    @property
    def function(self):
        r"""The saturation function.

        Returns
        -------
        callable
            Function with signature ``f(x, x1, xh, yh, theta)``.
        """

        def saturation(x, x1, xh, yh, theta):
            r"""Evaluate saturation model.

            Parameters
            ----------
            x : array-like
                Independent variable values.
            x1 : float
                x-intercept of rising line.
            xh : float
                x-coordinate of saturation point.
            yh : float
                y-coordinate of saturation point.
            theta : float
                Angle between lines in radians.

            Returns
            -------
            numpy.ndarray
                Model values at x.
            """
            m1 = yh / (xh - x1)
            m2 = np.tan(np.arctan(m1) - theta)
            x2 = xh - (yh / m2)

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

            m_1 = \frac{y_h}{x_h - x_1}
        """
        popt = self.popt
        yh = popt["yh"]
        xh = popt["xh"]
        x1 = popt["x1"]
        return yh / (xh - x1)

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

            x_2 = x_h - \frac{y_h}{m_2}
        """
        popt = self.popt
        yh = popt["yh"]
        xh = popt["xh"]
        m2 = self.m2
        return xh - (yh / m2)

    def _estimate(self):
        def estimate_line(x, y):
            m = _median_slope(x, y)
            x0 = _x_intercept(x, y, m)
            # A vertical line (infinite m) gives no saturation value.
            yh = m * (xh - x0) if np.isfinite(m) else np.nan
            return x0, m, yh

        x = self.observations.used.x
        y = self.observations.used.y

        xh = self._split_x()
        tk = x <= xh

        x1, m1, s1 = estimate_line(x[tk], y[tk])
        x2, m2, s2 = estimate_line(x[~tk], y[~tk])

        yh = np.nan if np.isnan([s1, s2]).all() else np.nanmedian([s1, s2])
        if not (np.isfinite(m1) and np.isfinite(m2)):
            theta = np.nan
        elif 1 + m1 * m2 == 0:
            # Perpendicular lines: the arctan argument is infinite. The exact
            # test is intentional, not an isclose candidate: near-perpendicular
            # lines give a large finite argument, which arctan handles.
            theta = np.copysign(np.pi / 2, m1 - m2)
        else:
            theta = np.arctan((m1 - m2) / (1 + m1 * m2))

        return [x1, xh, yh, theta]

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
                r"f \, \left(x, x_1, x_h, y_h, \theta\right)=\min\left(y_1, \, y_2\right)",
                r"y_i = m_i(x - x_i)",
                r"x_h = \frac{m_2 x_2 - m_1 x_1}{m_2 - m_1}",
                r"y_h = m_i (x_h - x_i)",
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

    Both lines pass through the hinge point :math:`(x_h, y_h)` where
    :math:`y_h = m_1 (x_h - x_1)`. The second slope is constrained by:

    .. math::

        m_2 = m_1 \frac{x_h - x_1}{x_h - x_2}

    Attributes
    ----------
    m1 : float
        Slope of first line (fitted parameter).
    x1 : float
        x-intercept of first line (fitted parameter).
    x2 : float
        x-intercept of second line (fitted parameter).
    xh : float
        x-coordinate of hinge point (fitted parameter).
    m2 : float
        Slope of second line (derived property).
    theta : float
        Angle between the two lines in radians (derived property).

    Notes
    -----
    ``p0`` estimates ``[m1, x1, x2, xh]`` from the data on each side of
    ``xh``, the split (``guess_xh``, or the median used x): below it and at
    or above it. Each side needs at
    least two points for a slope, and a nonzero slope for an x-intercept;
    the lower side skips a repeated point, and on the upper side repeated
    ``x`` leave the slope undefined. Otherwise an estimate is undefined, and
    ``p0`` returns the reference hinge of :class:`Hinge` as
    ``[m1, x1, x2, xh]``; the model's
    :math:`m_2 = m_1 (x_h - x_1) / (x_h - x_2)` then recovers the reference
    :math:`m_2`. When either side is short, the whole start is the reference
    hinge: the other side's estimate is not kept.

    Examples
    --------
    >>> import numpy as np
    >>> from solarwindpy.fitfunctions.hinge import HingeMin
    >>> x = np.linspace(0, 15, 100)
    >>> y = np.minimum(2*(x-0), -2*(x-10))  # Two lines meeting at (5, 10)
    >>> fit = HingeMin(x, y, guess_xh=5.0)
    >>> fit.make_fit()
    >>> print(f"Hinge at x={fit.popt['xh']:.2f}")
    Hinge at x=5.00
    """

    # The model combines the two lines with this; HingeMax uses np.maximum.
    _combine = staticmethod(np.minimum)

    @property
    def function(self):
        r"""The hinge function.

        Returns
        -------
        callable
            Function with signature ``f(x, m1, x1, x2, xh)``.
        """
        combine = self._combine

        def hinge(x, m1, x1, x2, xh):
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
            xh : float
                x-coordinate of hinge point.

            Returns
            -------
            numpy.ndarray
                Model values at x.
            """
            m2 = m1 * (xh - x1) / (xh - x2)
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

            m_2 = m_1 \frac{x_h - x_1}{x_h - x_2}
        """
        popt = self.popt
        xh = popt["xh"]
        m1 = popt["m1"]
        x1 = popt["x1"]
        x2 = popt["x2"]
        return m1 * (xh - x1) / (xh - x2)

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
        xh = self._split_x()

        # A side with fewer than 2 points has no slope: its estimates are NaN.
        m1 = x1 = x2 = np.nan

        # Estimate m1 and x1 from region below hinge
        tk_below = x < xh
        if tk_below.sum() >= 2:
            m1 = _median_slope(x[tk_below], y[tk_below])
            x1 = _x_intercept(x[tk_below], y[tk_below], m1)

        # Estimate x2 from the slope of the plateau region
        tk_above = x >= xh
        if tk_above.sum() >= 2:
            m2 = _median_slope(x[tk_above], y[tk_above], skip_nan=False)
            x2 = _x_intercept(x[tk_above], y[tk_above], m2)

        return [m1, x1, x2, xh]

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
                r"m_2 = m_1 \frac{x_h - x_1}{x_h - x_2}",
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

    Both lines pass through the hinge point :math:`(x_h, y_h)` where
    :math:`y_h = m_1 (x_h - x_1)`. The second slope is constrained by:

    .. math::

        m_2 = m_1 \frac{x_h - x_1}{x_h - x_2}

    This is :class:`HingeMin` with ``np.maximum`` instead of ``np.minimum``,
    suitable for V-shaped patterns opening upward. It shares HingeMin's
    parameters, estimate and derived properties.

    Notes
    -----
    ``p0`` estimates ``[m1, x1, x2, xh]`` as :class:`HingeMin` does, and an
    estimate is undefined in the same cases. Its reference start is
    HingeMin's, the reference hinge of :class:`Hinge` as
    ``[m1, x1, x2, xh]``: combined with the maximum, the same two lines give
    a convex start that hinges at the same point.

    Examples
    --------
    >>> import numpy as np
    >>> from solarwindpy.fitfunctions.hinge import HingeMax
    >>> x = np.linspace(0, 15, 100)
    >>> y = np.maximum(-2*(x-0), 2*(x-10))  # V-shape with vertex at (5, -10)
    >>> fit = HingeMax(x, y, guess_xh=5.0)
    >>> fit.make_fit()
    >>> print(f"Hinge at x={fit.popt['xh']:.2f}")
    Hinge at x=5.00
    """

    _combine = staticmethod(np.maximum)

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
                r"m_2 = m_1 \frac{x_h - x_1}{x_h - x_2}",
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
    ``xh``, the split (``guess_xh``, or the median used x): ``yh`` is the ``y`` at the observation nearest
    ``xh``, and the slopes come from each side of it: below it (x < xh) and
    at or above it. Each side needs at least two points for a slope; the
    lower side skips a repeated point, and on the upper side repeated ``x``
    leave the slope undefined. Otherwise a slope is undefined, and ``p0``
    returns the reference hinge of :class:`Hinge` as ``[xh, yh, m1, m2]``.
    When either side is short, the whole start is the reference hinge: the
    other side's estimate is not kept.

    Examples
    --------
    >>> import numpy as np
    >>> from solarwindpy.fitfunctions.hinge import HingeAtPoint
    >>> x = np.linspace(0, 15, 100)
    >>> y = np.minimum(2*(x-0), -1*(x-15))  # Hinge at (5, 10)
    >>> fit = HingeAtPoint(x, y, guess_xh=5.0)
    >>> fit.make_fit()
    >>> print(f"Hinge at ({fit.popt['xh']:.2f}, {fit.popt['yh']:.2f})")
    Hinge at (5.00, 10.00)
    """

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
        x = self.observations.used.x
        y = self.observations.used.y
        xh = self._split_x()

        # Estimate yh from data near the hinge point
        yh = _y_near(x, y, xh)

        # A side with fewer than 2 points has no slope: its estimate is NaN.
        m1 = m2 = np.nan

        # Estimate m1 from region below hinge
        tk_below = x < xh
        if tk_below.sum() >= 2:
            m1 = _median_slope(x[tk_below], y[tk_below])

        # Estimate m2 from region above hinge
        tk_above = x >= xh
        if tk_above.sum() >= 2:
            m2 = _median_slope(x[tk_above], y[tk_above], skip_nan=False)

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
