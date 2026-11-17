#!/usr/bin/env python
r"""Scales that map a plotted variable onto how its marks look, with their guides.

A scale holds one encoding channel of a plot: the norm that maps the data to
[0, 1], what [0, 1] becomes on the marks, and the guide that reads the marks
back, such as a colorbar. Build one, pass it to a plot's ``make_plot``, and
pass the same one to several plots to draw them on one scale.
"""

__all__ = [
    "ColorScale",
    "SizeScale",
    "AlphaScale",
]

from collections.abc import Mapping
from numbers import Real
from types import MappingProxyType

import numpy as np
import matplotlib as mpl
from matplotlib.cm import ScalarMappable
from matplotlib.ticker import LogLocator, MaxNLocator


def _fmt(v):
    r"""``v`` to four significant figures, or None."""
    return None if v is None else f"{v:.4g}"


def _numbers(values):
    r"""``values`` as a list of floats, or None unless it is a sequence of real numbers."""
    if isinstance(values, (str, bytes)):
        return None
    try:
        items = list(values)
    except TypeError:
        return None
    if not all(isinstance(v, Real) and not isinstance(v, bool) for v in items):
        return None
    return [float(v) for v in items]


class _Scale:
    r"""What every scale shares: its norm, the checks of its settings, its text.

    A subclass stores its norm as ``_norm`` and lists its settings in
    ``_fields``, which ``repr`` and ``print`` show one per line.
    """

    @property
    def norm(self):
        r"""The ``Normalize`` from the data to [0, 1]."""
        return self._norm

    @staticmethod
    def _checked_norm(norm):
        r"""``norm`` as a ``Normalize`` or None, a scale name converted by matplotlib.

        Raises
        ------
        TypeError
            If ``norm`` is neither None, a ``Normalize`` nor a str.
        ValueError
            If ``norm`` is a str that names no matplotlib scale.
        """
        if isinstance(norm, str):
            # matplotlib's own conversion of a scale name, as its plotting
            # functions do it; it raises ValueError for an unknown name.
            norm = ScalarMappable(norm=norm).norm
        if norm is not None and not isinstance(norm, mpl.colors.Normalize):
            raise TypeError(
                "norm must be a matplotlib.colors.Normalize, a matplotlib scale "
                f"name or None, not {type(norm).__name__}"
            )
        return norm

    @staticmethod
    def _checked_flag(name, value):
        r"""``value``, which must be a bool, else TypeError naming ``name``."""
        if not isinstance(value, bool):
            raise TypeError(f"{name} must be True or False, not {type(value).__name__}")
        return value

    @staticmethod
    def _checked_kwargs(name, value):
        r"""A read-only copy of ``value``, a mapping or None (empty)."""
        if value is None:
            value = {}
        if not isinstance(value, Mapping):
            raise TypeError(
                f"{name} must be a mapping or None, not {type(value).__name__}"
            )
        return MappingProxyType(dict(value))

    def _fields(self):
        r"""Each setting's text for ``repr``, by name, in order."""
        raise NotImplementedError

    def __repr__(self):
        r"""The class, then one ``key: value`` line per setting.

        The norm shows its class and its current ``vmin`` and ``vmax``, to
        four significant figures, None while unset. ``print`` shows the same
        text.
        """
        lines = [f"  {k}: {v}" for k, v in self._fields().items()]
        return "\n".join([self.__class__.__name__, *lines])

    def _norm_text(self):
        r"""``Class(vmin=..., vmax=...)``, or None without a norm."""
        norm = self.norm
        if norm is None:
            return None
        return f"{type(norm).__name__}(vmin={_fmt(norm.vmin)}, vmax={_fmt(norm.vmax)})"


class _BarScale(_Scale):
    r"""A scale whose guide is a colorbar, set by ``cbar`` and ``cbar_kwargs``."""

    def _set_bar(self, cbar, cbar_kwargs):
        self._cbar = self._checked_flag("cbar", cbar)
        self._cbar_kwargs = self._checked_kwargs("cbar_kwargs", cbar_kwargs)

    @property
    def cbar(self):
        r"""True if a colorbar is drawn."""
        return self._cbar

    @property
    def cbar_kwargs(self):
        r"""Read-only mapping passed to the colorbar."""
        return self._cbar_kwargs


class _MarkerScale(_Scale):
    r"""A scale from a per-point variable onto a marker value, over ``range``.

    ``norm(values)``, clipped to [0, 1], is ``f``; the marker value is
    ``lo + f * (hi - lo)`` for ``range = (lo, hi)``. A subclass sets the
    bounds a range end must lie in and the units ``repr`` shows.
    """

    #: Closed interval each end of ``range`` must lie in.
    _range_bounds = (-np.inf, np.inf)
    #: What a range end is, for the error that a bound is broken.
    _range_rule = ""
    #: Units of ``range`` shown by ``repr``.
    _range_units = ""

    def _set_norm_and_range(self, norm, ends):
        norm = self._checked_norm(norm)
        self._norm = mpl.colors.Normalize() if norm is None else norm
        self._range = self._checked_range(ends)

    def _checked_range(self, ends):
        r"""``ends`` as a tuple of two floats, checked against ``_range_bounds``.

        Raises
        ------
        TypeError
            If ``ends`` is not two real numbers.
        ValueError
            If an end is not finite or lies outside ``_range_bounds``.
        """
        values = _numbers(ends)
        if values is None or len(values) != 2:
            raise TypeError(f"range must be two numbers, not {ends!r}")
        if not np.isfinite(values).all():
            raise ValueError(f"range must be finite, not {tuple(values)}")
        lower, upper = self._range_bounds
        if not all(lower <= v <= upper for v in values):
            raise ValueError(f"{self._range_rule}, not range={tuple(values)}")
        return tuple(values)

    @property
    def range(self):
        r"""``(lo, hi)``: the marker values at 0 and 1 of the norm."""
        return self._range

    def _range_text(self):
        lo, hi = self.range
        return f"({_fmt(lo)}, {_fmt(hi)}) {self._range_units}"

    def _marker_values(self, values):
        r"""The marker value of each of ``values``, masked where the norm masks it.

        An unset ``vmin`` or ``vmax`` of the norm is set in place from
        ``values``, as matplotlib does.
        """
        f = np.ma.clip(self.norm(np.asarray(values, dtype=float)), 0, 1)
        lo, hi = self.range
        return lo + f * (hi - lo)


class ColorScale(_BarScale):
    r"""How z becomes a colour, and the colorbar that reads it back.

    The colour settings of a plot's ``make_plot`` as one object. Passed as
    ``make_plot(color_scale=...)`` it replaces the keywords ``norm``,
    ``cmap``, ``cbar`` and ``cbar_kwargs``; the plots build one from those
    keywords when no scale is passed, so both routes draw the same colours.
    The settings are read-only once built.

    Parameters
    ----------
    norm : matplotlib.colors.Normalize or str, optional
        Maps z to [0, 1]: any ``Normalize``, such as ``LogNorm`` or
        ``CenteredNorm``, used as given. Its ``vmin`` and ``vmax`` are in the
        units of z. A str names a matplotlib scale, such as ``"log"``,
        ``"symlog"`` or ``"linear"``, and becomes that scale's norm as
        matplotlib's own plotting functions convert it
        (``matplotlib.cm.ScalarMappable(norm=name).norm``); ``"log"`` gives a
        ``LogNorm``. None means the plot's default: a ``CenteredNorm`` about 0
        when the values hold both signs, otherwise the default of the plot's
        ``axnorm`` (see ``ColorPlot._default_norm``).
    cmap : str or matplotlib.colors.Colormap, optional
        Maps [0, 1] to a colour. None means the plot's default: ``"RdBu_r"``
        when the values hold both signs, otherwise the plot's own default
        (matplotlib's, or ``"Greens_r"`` for a ``BetaRPlot``).
    cbar : bool, default True
        If True, draw a colorbar labelled with the plot's ``labels.z``.
    cbar_kwargs : Mapping, optional
        Passed to :meth:`matplotlib.figure.Figure.colorbar`, e.g. ``cax``,
        ``label`` or ``shrink``. Without ``ax`` or ``cax``, the colorbar is
        drawn beside the plot's axes. Copied when the scale is built.

    Raises
    ------
    TypeError
        If ``norm`` is neither None, a ``Normalize`` nor a str, ``cbar`` is
        not a bool, or ``cbar_kwargs`` is neither None nor a mapping.
    ValueError
        If ``norm`` is a str that names no matplotlib scale (matplotlib's
        error).

    See Also
    --------
    SizeScale, AlphaScale : the marker size and opacity of a ``Scatter``.

    Notes
    -----
    The norm is used as is, never copied, so plots that share a scale share
    its limits. matplotlib fills an unset ``vmin`` or ``vmax`` in place from
    the first plot drawn with the norm, so a scale shared across panels with
    unset limits takes the first panel's; ``print(scale)`` then shows the
    limits used. Set ``vmin`` and ``vmax`` to choose them instead.

    Examples
    --------
    >>> import pandas as pd
    >>> import matplotlib.pyplot as plt
    >>> from matplotlib.colors import Normalize
    >>> from solarwindpy.plotting.scales import ColorScale
    >>> from solarwindpy.plotting.scatter import Scatter
    >>> scale = ColorScale(norm=Normalize(), cmap="viridis")
    >>> print(scale)
    ColorScale
      norm: Normalize(vmin=None, vmax=None)
      cmap: viridis
      cbar: True
      cbar_kwargs: {}

    A plot fills the norm's limits from its z, here 2 to 9:

    >>> z = pd.Series([2.0, 5.0, 9.0])
    >>> ax, points, segments, guides = Scatter(z, z, z).make_plot(color_scale=scale)
    >>> print(scale)
    ColorScale
      norm: Normalize(vmin=2, vmax=9)
      cmap: viridis
      cbar: True
      cbar_kwargs: {}
    >>> guides.color.mappable is points
    True
    >>> plt.close("all")
    """

    def __init__(self, norm=None, cmap=None, cbar=True, cbar_kwargs=None):
        self._norm = self._checked_norm(norm)
        self._cmap = cmap
        self._set_bar(cbar, cbar_kwargs)

    @property
    def norm(self):
        r"""The ``Normalize`` from z to [0, 1], or None for the plot's default."""
        return self._norm

    @property
    def cmap(self):
        r"""The colormap, as given, or None for the plot's default."""
        return self._cmap

    def _fields(self):
        r"""The norm, the colormap by name, and the colorbar's settings."""
        return {
            "norm": self._norm_text(),
            "cmap": getattr(self.cmap, "name", self.cmap),
            "cbar": self.cbar,
            "cbar_kwargs": dict(self.cbar_kwargs),
        }


class SizeScale(_MarkerScale):
    r"""How a ``Scatter``'s size variable becomes marker area, and the key that reads it.

    Passed as ``Scatter.make_plot(size_scale=...)``. Each drawn point's size
    goes through ``norm`` to ``f`` in [0, 1], clipped, then to the area
    ``lo + f * (hi - lo)`` in pt² for ``range = (lo, hi)``, as ``cmap`` maps
    [0, 1] to a colour. The key is a legend of marker areas at chosen sizes,
    drawn from the same norm and range, so it reads the points exactly. The
    settings are read-only once built.

    Parameters
    ----------
    norm : matplotlib.colors.Normalize or str, optional
        Maps the size variable to [0, 1]: any ``Normalize``, such as
        ``LogNorm`` for a quantity spanning decades, used as given. Its
        ``vmin`` and ``vmax`` are in the units of the size variable: the
        values drawn at ``lo`` and ``hi``. A str names a matplotlib scale, as
        for ``ColorScale``. None means a new ``Normalize()``.
    range : (float, float), default (9, 144)
        Marker areas, in pt², at 0 and 1 of the norm: by default half to
        twice matplotlib's default marker diameter of 6 pt. Each end is a
        finite number >= 0. A reversed pair, such as ``(144, 9)``, draws
        large values small.
    key : bool or sequence of float, default True
        The sizes the key shows, in the units of the size variable. True
        chooses them from the norm's ``vmin`` and ``vmax`` (see Notes);
        False or None draws no key.
    key_kwargs : Mapping, optional
        Passed to :class:`matplotlib.legend.Legend`, e.g. ``loc``, ``ncols``
        or ``title``. Copied when the scale is built.

    Raises
    ------
    TypeError
        If ``norm`` is neither None, a ``Normalize`` nor a str; ``range`` is
        not two numbers; ``key`` is neither a bool, None nor a sequence of
        numbers; or ``key_kwargs`` is neither None nor a mapping.
    ValueError
        If an end of ``range`` is not finite or is negative; a value of
        ``key`` is not finite, or ``key`` is empty; or ``norm`` is a str that
        names no matplotlib scale.

    See Also
    --------
    AlphaScale : the marker opacity of a ``Scatter``.
    ColorScale : the colour of a plot.

    Notes
    -----
    A size beyond the norm's ``vmin`` or ``vmax`` is drawn at the area of
    that end. A size the norm masks, such as one <= 0 under ``LogNorm``, is
    not drawn.

    The norm is used as is, never copied, so plots that share a scale share
    its limits. matplotlib fills an unset ``vmin`` or ``vmax`` in place from
    the first plot's drawn sizes, so a scale shared across panels with unset
    limits takes the first panel's; ``print(scale)`` then shows the limits
    used. Set ``vmin`` and ``vmax`` to choose them instead.

    With ``key=True`` the key shows round values from ``vmin`` to ``vmax``.
    Under a ``LogNorm`` they are the decades within them
    (:class:`~matplotlib.ticker.LogLocator`) when three or more fit, else
    the 1, 2, 5 steps of each decade when two to five fit. Otherwise, and
    under any other norm, they are the values of
    :class:`~matplotlib.ticker.MaxNLocator` with four bins. The key's markers
    are opaque and grey, whatever the points' colour and alpha. Its title is
    the plot's ``labels.size``. The key is added to the axes as an extra
    artist, not as their legend, so it is drawn beside any legend the axes
    have or later get from ``ax.legend()``.

    Examples
    --------
    >>> import pandas as pd
    >>> import matplotlib.pyplot as plt
    >>> from matplotlib.colors import LogNorm
    >>> from solarwindpy.plotting.scales import SizeScale
    >>> from solarwindpy.plotting.scatter import Scatter
    >>> scale = SizeScale(norm=LogNorm(), range=(10, 30), key=[1, 10, 100])
    >>> print(scale)
    SizeScale
      norm: LogNorm(vmin=None, vmax=None)
      range: (10, 30) pt² area
      key: (1, 10, 100)
      key_kwargs: {}

    A plot fills the norm's limits from its drawn sizes, here 1 to 100:

    >>> x = pd.Series([1.0, 2.0, 3.0])
    >>> sc = Scatter(x, x, size=pd.Series([1.0, 10.0, 100.0]))
    >>> ax, points, segments, guides = sc.make_plot(size_scale=scale)
    >>> points.get_sizes().tolist()
    [10.0, 20.0, 30.0]
    >>> print(scale)
    SizeScale
      norm: LogNorm(vmin=1, vmax=100)
      range: (10, 30) pt² area
      key: (1, 10, 100)
      key_kwargs: {}
    >>> [t.get_text() for t in guides.size.get_texts()]
    ['1', '10', '100']
    >>> plt.close("all")
    """

    _range_bounds = (0.0, np.inf)
    _range_rule = "marker areas must be >= 0 pt²"
    _range_units = "pt² area"

    def __init__(self, norm=None, range=(9, 144), key=True, key_kwargs=None):
        self._set_norm_and_range(norm, range)
        self._key = self._checked_key(key)
        self._key_kwargs = self._checked_kwargs("key_kwargs", key_kwargs)

    @staticmethod
    def _checked_key(key):
        r"""``key`` as a bool or a tuple of finite floats; None is False."""
        if key is None:
            return False
        if isinstance(key, bool):
            return key
        values = _numbers(key)
        if values is None:
            raise TypeError(
                "key must be True, False, None or a sequence of data values, "
                f"not {key!r}"
            )
        if not values:
            raise ValueError("key needs at least one value; pass False for no key")
        if not np.isfinite(values).all():
            raise ValueError(f"key values must be finite, not {tuple(values)}")
        return tuple(values)

    @property
    def key(self):
        r"""True, False, or the tuple of sizes the key shows."""
        return self._key

    @property
    def key_kwargs(self):
        r"""Read-only mapping passed to ``matplotlib.legend.Legend``."""
        return self._key_kwargs

    def _fields(self):
        r"""The norm, the range in pt², and the key's settings."""
        key = self.key
        if not isinstance(key, bool):
            key = f"({', '.join(_fmt(v) for v in key)})"
        return {
            "norm": self._norm_text(),
            "range": self._range_text(),
            "key": key,
            "key_kwargs": dict(self.key_kwargs),
        }

    def _key_values(self):
        r"""The sizes the key shows: ``key`` as given, or chosen as Notes describe.

        Called once the norm's limits are set.
        """
        if self.key is not True:
            return self.key
        vmin, vmax = self.norm.vmin, self.norm.vmax
        slack = 1e-9 * (vmax - vmin)

        def within(locator):
            ticks = locator.tick_values(vmin, vmax)
            return tuple(float(t) for t in ticks if vmin - slack <= t <= vmax + slack)

        if isinstance(self.norm, mpl.colors.LogNorm):
            decades = within(LogLocator(numticks=5))
            if len(decades) >= 3:
                return decades
            steps = within(LogLocator(subs=(1.0, 2.0, 5.0)))
            if 2 <= len(steps) <= 5:
                return steps
        return within(MaxNLocator(nbins=4)) or (float(vmin),)


class AlphaScale(_MarkerScale, _BarScale):
    r"""How a ``Scatter``'s alpha variable becomes opacity, and the bar that reads it.

    Passed as ``Scatter.make_plot(alpha_scale=...)``. Each drawn point's
    alpha variable goes through ``norm`` to ``f`` in [0, 1], clipped, then
    to the opacity ``lo + f * (hi - lo)`` for ``range = (lo, hi)``, as
    ``cmap`` maps [0, 1] to a colour. The alpha bar is a colorbar of one
    colour whose alpha runs from ``lo`` to ``hi``, on the same norm, so its
    ticks are in the variable's units. The settings are read-only once
    built.

    Parameters
    ----------
    norm : matplotlib.colors.Normalize or str, optional
        Maps the alpha variable to [0, 1], as for ``SizeScale``. None means
        a new ``Normalize()``.
    range : (float, float), default (0.15, 1.0)
        Opacities at 0 and 1 of the norm, each in [0, 1]. The default starts
        at 0.15, the faintest alpha at which a marker stays visible; a lower
        end given here is used as given. A reversed pair, such as
        ``(1, 0.15)``, fades large values.
    cbar : bool, default True
        If True, draw the alpha bar, labelled with the plot's
        ``labels.alpha``.
    cbar_kwargs : Mapping, optional
        Passed to :meth:`matplotlib.figure.Figure.colorbar`, as for
        ``ColorScale``. The bar lies horizontally above the plot's axes
        unless these set ``location``, ``orientation`` or ``cax``. Copied
        when the scale is built.

    Raises
    ------
    TypeError
        If ``norm`` is neither None, a ``Normalize`` nor a str; ``range`` is
        not two numbers; ``cbar`` is not a bool; or ``cbar_kwargs`` is
        neither None nor a mapping.
    ValueError
        If an end of ``range`` lies outside [0, 1] or is not finite, or
        ``norm`` is a str that names no matplotlib scale.

    See Also
    --------
    SizeScale : the marker size of a ``Scatter``.
    ColorScale : the colour of a plot.

    Notes
    -----
    A value beyond the norm's ``vmin`` or ``vmax`` is drawn at the opacity
    of that end. A value the norm masks, such as one <= 0 under
    ``LogNorm``, is not drawn.

    The norm is used as is, never copied, so plots that share a scale share
    its limits. matplotlib fills an unset ``vmin`` or ``vmax`` in place from
    the first plot's drawn values, so a scale shared across panels with
    unset limits takes the first panel's; ``print(scale)`` then shows the
    limits used. Set ``vmin`` and ``vmax`` to choose them instead.

    The bar's colour is black when z colours the points, else the points'
    own colour.

    Examples
    --------
    >>> import pandas as pd
    >>> import matplotlib.pyplot as plt
    >>> from solarwindpy.plotting.scales import AlphaScale
    >>> from solarwindpy.plotting.scatter import Scatter
    >>> scale = AlphaScale(range=(1, 0.25))
    >>> print(scale)
    AlphaScale
      norm: Normalize(vmin=None, vmax=None)
      range: (1, 0.25) alpha
      cbar: True
      cbar_kwargs: {}

    A plot fills the norm's limits from its drawn values, here 0 to 10, and
    the reversed range fades the largest:

    >>> x = pd.Series([1.0, 2.0, 3.0])
    >>> sc = Scatter(x, x, alpha=pd.Series([0.0, 5.0, 10.0]))
    >>> ax, points, segments, guides = sc.make_plot(alpha_scale=scale)
    >>> points.get_alpha().tolist()
    [1.0, 0.625, 0.25]
    >>> print(scale)
    AlphaScale
      norm: Normalize(vmin=0, vmax=10)
      range: (1, 0.25) alpha
      cbar: True
      cbar_kwargs: {}
    >>> guides.alpha.norm is scale.norm
    True
    >>> plt.close("all")
    """

    _range_bounds = (0.0, 1.0)
    _range_rule = "alphas must lie in [0, 1]"
    _range_units = "alpha"

    def __init__(self, norm=None, range=(0.15, 1.0), cbar=True, cbar_kwargs=None):
        self._set_norm_and_range(norm, range)
        self._set_bar(cbar, cbar_kwargs)

    def _fields(self):
        r"""The norm, the range of alpha, and the alpha bar's settings."""
        return {
            "norm": self._norm_text(),
            "range": self._range_text(),
            "cbar": self.cbar,
            "cbar_kwargs": dict(self.cbar_kwargs),
        }
