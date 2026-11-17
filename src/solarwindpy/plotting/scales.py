#!/usr/bin/env python
r"""Scales that map a plotted variable onto how its marks look, with their guides.

A scale holds one encoding channel of a plot: the norm that maps the data to
[0, 1], what [0, 1] becomes on the marks, and the guide that reads the marks
back, such as a colorbar. Build one, pass it to a plot's ``make_plot``, and
pass the same one to several plots to draw them on one scale.
"""

__all__ = [
    "ColorScale",
]

from collections.abc import Mapping
from types import MappingProxyType

import matplotlib as mpl
from matplotlib.cm import ScalarMappable


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


class ColorScale:
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
        norm = _checked_norm(norm)
        if not isinstance(cbar, bool):
            raise TypeError(f"cbar must be True or False, not {type(cbar).__name__}")
        if cbar_kwargs is None:
            cbar_kwargs = {}
        if not isinstance(cbar_kwargs, Mapping):
            raise TypeError(
                "cbar_kwargs must be a mapping or None, "
                f"not {type(cbar_kwargs).__name__}"
            )
        self._norm = norm
        self._cmap = cmap
        self._cbar = cbar
        self._cbar_kwargs = MappingProxyType(dict(cbar_kwargs))

    @property
    def norm(self):
        r"""The ``Normalize`` from z to [0, 1], or None for the plot's default."""
        return self._norm

    @property
    def cmap(self):
        r"""The colormap, as given, or None for the plot's default."""
        return self._cmap

    @property
    def cbar(self):
        r"""True if a colorbar is drawn."""
        return self._cbar

    @property
    def cbar_kwargs(self):
        r"""Read-only mapping passed to the colorbar."""
        return self._cbar_kwargs

    def __repr__(self):
        r"""The class, then one ``key: value`` line per setting.

        The norm shows its class and its current ``vmin`` and ``vmax``, to
        four significant figures, None while unset; the colormap shows its
        name. ``print`` shows the same text.
        """
        fields = {
            "norm": self._norm_text(),
            "cmap": getattr(self.cmap, "name", self.cmap),
            "cbar": self.cbar,
            "cbar_kwargs": dict(self.cbar_kwargs),
        }
        lines = [f"  {k}: {v}" for k, v in fields.items()]
        return "\n".join([self.__class__.__name__, *lines])

    def _norm_text(self):
        r"""``Class(vmin=..., vmax=...)``, or None without a norm."""
        norm = self.norm
        if norm is None:
            return None

        def fmt(v):
            return None if v is None else f"{v:.4g}"

        return f"{type(norm).__name__}(vmin={fmt(norm.vmin)}, vmax={fmt(norm.vmax)})"
