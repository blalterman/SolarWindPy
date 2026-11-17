#!/usr/bin/env python
r"""Scatter plot utilities with optional color mapping."""

__all__ = [
    "Scatter",
]

import numpy as np
import matplotlib as mpl
from matplotlib import cbook
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection

from ..tools import _warn
from . import base

# Every spelling of the segments' colour that LineCollection accepts, and
# ``c``, which ``ax.scatter`` accepts.
_COLOR_KEYS = ("color", "c", "colors", "edgecolor", "edgecolors", "ec")

#: Default marker areas, in pt^2, at 0 and 1 of ``size_norm``: half and twice
#: matplotlib's default marker diameter of 6 pt (``lines.markersize``).
_SIZE_RANGE = (9, 144)
#: Default alphas at 0 and 1 of ``alpha_norm``. 0.15 is the faintest alpha at
#: which a marker stays visible.
_ALPHA_RANGE = (0.15, 1.0)


class Scatter(base.ColorPlot):
    r"""Scatter plot of y against x, optionally colored by z.

    Notes
    -----
    ``logx`` and ``logy`` set only the axis scale. ``Hist2D`` and
    ``SpiralPlot2D`` also store ``log10(abs())`` of a flagged axis, because
    they bin in log space; a ``Scatter`` keeps its data linear. Quantile
    clipping gives nearly the same points either way, since a monotone log
    preserves order. Negative values differ: the binned plots fold them
    into the log axis with ``abs()``, while a ``Scatter`` leaves them for
    matplotlib to drop from its log axis.

    Whether a ``Scatter`` should match the binned plots is open:
    https://github.com/blalterman/SolarWindPy/issues/541.

    Examples
    --------
    >>> import pandas as pd
    >>> import matplotlib.pyplot as plt
    >>> from solarwindpy.plotting.scatter import Scatter
    >>> x = pd.Series([1.0, 2.0, 3.0])
    >>> y = pd.Series([4.0, 5.0, 6.0])
    >>> z = pd.Series([7.0, 8.0, 9.0])
    >>> s = Scatter(x, y, z)
    >>> ax, collection, segments, guides = s.make_plot()
    >>> collection.get_offsets().tolist()
    [[1.0, 4.0], [2.0, 5.0], [3.0, 6.0]]
    >>> collection.get_array().tolist()
    [7.0, 8.0, 9.0]
    >>> segments is None, guides.color.mappable is collection
    (True, True)

    A ``size`` variable sets each marker's area, here on 10 to 30 pt²:

    >>> s = Scatter(x, y, size=pd.Series([1.0, 2.0, 3.0]))
    >>> ax, collection, segments, guides = s.make_plot(size_range=(10, 30))
    >>> collection.get_sizes().tolist()
    [10.0, 20.0, 30.0]
    >>> plt.close("all")
    """

    _clipped_axes = ("x", "y", "z")

    def __init__(
        self,
        x,
        y,
        z=None,
        size=None,
        alpha=None,
        logx=None,
        logy=None,
        clip=None,
        mask=None,
    ):
        r"""Initialize scatter plot data.

        Parameters
        ----------
        x, y: pd.Series
            Data defining (x, y) coordinates.
        z: pd.Series, optional
            If not None, used to specify the color for each point.
        size: pd.Series or array-like, optional
            A value per point that sets its marker area through
            ``make_plot``'s ``size_norm`` and ``size_range``. Aligned by
            label to x and y, as z is; a point whose size is NaN or infinite
            is not plotted. Held in ``data`` as the column ``"size"``.
        alpha: pd.Series or array-like, optional
            A value per point that sets its opacity through ``make_plot``'s
            ``alpha_norm`` and ``alpha_range``. Aligned and dropped as
            ``size`` is, and held in ``data`` as the column ``"alpha"``.
        logx, logy: bool or None
            If True, draw that axis on a log scale. The data stay linear:
            ``clip`` and ``alim`` read the values as given. None means False;
            ``set_log`` can change them later.
        clip: bool, str, Mapping or None
            If True, ``make_plot`` clips x, y and z to their 0.01st and 99.99th
            percentiles with ``Base.clip_data``; ``"l"`` or ``"u"`` clips only
            the lower or upper tail. A mapping such as ``{"z": "u"}`` sets
            each column on its own. None means False. Stored as ``clip``, a
            ``ClipAxes``.
        mask: pd.Series of bool, optional
            Rows to keep, aligned by label to the index of x and y. A point
            is plotted where it is True and x, y and z are not NaN. A label
            missing from ``mask``, or a NaN in it, raises ``ValueError``.
        """
        super(Scatter, self).__init__()
        extra = {k: v for k, v in (("size", size), ("alpha", alpha)) if v is not None}
        self._set_data(x, y, z, clip, mask=mask, extra=extra)
        self._labels = base.AxesLabels(x="x", y="y", z="z" if z is not None else None)
        self.set_log(x=bool(logx), y=bool(logy))

    def _format_axis(self, ax, collection, data):
        super()._format_axis(ax)

        x = data.loc[:, "x"]
        y = data.loc[:, "y"]
        self._fit_view(ax, collection, x.min(), x.max(), y.min(), y.max())

    def make_plot(
        self,
        ax=None,
        cbar=None,
        cbar_kwargs=None,
        connect=False,
        connect_kwargs=None,
        size_norm=None,
        size_range=_SIZE_RANGE,
        alpha_norm=None,
        alpha_range=_ALPHA_RANGE,
        *,
        color_scale=None,
        **kwargs,
    ):
        r"""Make a scatter plot on `ax` using `ax.scatter`.

        Parameters
        ----------
        ax: mpl.axes.Axes, None
            If None, create an `Axes` instance from `plt.subplots`.
        cbar: bool, None
            If True, create color bar with `labels.z`. None, the default,
            means True.
        cbar_kwargs: dict, None
            If not None, kwargs passed to the colorbar; see ``ColorScale``.
        connect: bool
            If True, join the drawn points with line segments in increasing
            z (see Notes).
        connect_kwargs: dict, None
            Passed to :class:`~matplotlib.collections.LineCollection`, e.g.
            ``linewidth``, ``alpha`` or ``zorder``. The defaults are a
            ``linewidth`` of 0.75 and a ``zorder`` just below the points'.
            ``facecolor`` has no visible effect, since lines have no faces.
            A colour, under any of the keys ``color``, ``c``, ``colors``,
            ``edgecolor``, ``edgecolors`` or ``ec``, applies only without a
            varying z (see Notes); at most one of them may be given.
            Not modified.
        size_norm: matplotlib.colors.Normalize, None
            Maps each drawn point's size to [0, 1]. Its ``vmin`` and
            ``vmax``, in the units of size, are the sizes that land at 0 and
            1. Any ``Normalize``, such as ``LogNorm`` or ``PowerNorm``, is
            used as given. None means a new ``Normalize()``, scaled to the
            drawn sizes. Only with a size variable.
        size_range: (float, float)
            Marker areas, in pt², at 0 and 1 of ``size_norm``. A point whose
            normalized size, clipped to [0, 1], is ``f`` gets the area
            ``lo + f * (hi - lo)``, so a size beyond ``vmin`` or ``vmax``
            gets the area at that end. The default is half to twice
            matplotlib's default marker diameter of 6 pt. A reversed pair
            draws large sizes small. Only with a size variable.
        alpha_norm: matplotlib.colors.Normalize, None
            As ``size_norm``, for the alpha variable.
        alpha_range: (float, float)
            Alphas at 0 and 1 of ``alpha_norm``, mapped as ``size_range``
            is. The default starts at 0.15, the faintest alpha at which a
            marker stays visible; a lower end the caller gives is used as
            given. A reversed pair, such as ``(1, 0.15)``, fades large
            values. Only with an alpha variable.
        color_scale: ColorScale, None
            The colour settings as one object (see
            :class:`~solarwindpy.plotting.scales.ColorScale`), in place of
            ``norm``, ``cmap``, ``cbar`` and ``cbar_kwargs``; given with any of
            them, raises ``TypeError``.
        kwargs:
            Passed to `ax.scatter`, except ``s`` with a size variable and
            ``alpha`` with an alpha variable.

        Returns
        -------
        ax: mpl.axes.Axes
        collection: mpl.collections.PathCollection
            The points.
        segments: mpl.collections.LineCollection or None
            The segments joining the points if `connect` is True, else None.
        guides: Guides
            ``color`` is the colorbar if `cbar` is True and z varies, else
            None; ``size`` and ``alpha`` are None.

        Raises
        ------
        TypeError
            If ``s`` is given with a size variable or ``alpha`` with an
            alpha variable, or if ``size_norm`` or ``size_range`` is given
            without a size variable, or ``alpha_norm`` or ``alpha_range``
            without an alpha variable; or if ``color_scale`` is given with
            ``norm``, ``cmap``, ``cbar`` or ``cbar_kwargs``.

        Notes
        -----
        Points whose z is outside ``alim`` (see ``set_alim``) are not drawn,
        do not enter the colour scale, and do not set the axis limits. With
        ``kind="quantile"`` the thresholds are quantiles of the plotted z.

        A point is not drawn where x, y, z, size or alpha is NaN or infinite,
        where ``mask`` excludes it, where z is outside ``alim``, or where
        ``size_norm`` or ``alpha_norm`` masks its value (a value <= 0 under
        ``LogNorm``). Such a point enters neither the colour scale nor the
        size and alpha norms, and does not set the axis limits. A point
        <= 0 on a log axis is left for matplotlib to drop, so it still
        enters the colour scale and the norms. The colorbar stays opaque
        whatever the points' alpha.

        With ``connect=True`` each drawn point is joined to the drawn point
        next in increasing z, a stable sort, so points with equal z keep the
        order of their rows and the rows need not be sorted. With z the time
        of each point, the segments trace its trajectory; with any other z
        they trace how (x, y) changes as z increases. Without a varying z
        (no z, or one value), the points are joined in row order. A point
        that is not drawn (see above), or is <= 0 on a log axis, is skipped,
        not a gap: the points on either side of it are joined.

        When z varies, each segment is coloured by the mean z of its two
        points, ``(z_a + z_b) / 2``, through the points' colormap and norm,
        the same objects, so the one colorbar reads both; a colour in
        ``connect_kwargs`` is then ignored, with a ``UserWarning`` naming its
        key. Otherwise every segment has the colour that ``connect_kwargs``
        sets, or the points' colour if it sets none, at full opacity when an
        alpha variable sets each point's alpha. The segments do not set the
        axis limits.
        """
        scale = self._color_scale(kwargs, color_scale, cbar, cbar_kwargs)
        markers = self._marker_variables(
            kwargs,
            size=(size_norm, size_range, _SIZE_RANGE),
            alpha=(alpha_norm, alpha_range, _ALPHA_RANGE),
        )

        if ax is None:
            fig, ax = plt.subplots()

        data = self.data
        for k, clip in self.clip._asdict().items():
            if clip:
                data[k] = self.clip_data(data.loc[:, k], clip)

        data = data.loc[self._apply_alim(data.loc[:, "z"]).notna()]

        # Map each variable onto its range; a point a norm masks is not drawn.
        mapped = {}
        for col, (key, norm, ends) in markers.items():
            norm = mpl.colors.Normalize() if norm is None else norm
            f = np.ma.clip(norm(data.loc[:, col].to_numpy(dtype=float)), 0, 1)
            lo, hi = ends
            mapped[key] = lo + f * (hi - lo)
        drawn = np.ones(len(data), dtype=bool)
        for v in mapped.values():
            drawn &= ~np.ma.getmaskarray(v)
        if not drawn.all():
            data = data.loc[drawn]
        mapped = {k: np.ma.getdata(v)[drawn] for k, v in mapped.items()}
        kwargs.update(mapped)

        if data.loc[:, "z"].unique().size > 1:
            zkey = "z"
            kwargs["norm"], kwargs["cmap"] = self._norm_and_cmap(
                scale, data.loc[:, "z"].to_numpy()
            )
        else:
            zkey = None

        collection = ax.scatter(x="x", y="y", c=zkey, data=data, **kwargs)

        segments = None
        if connect:
            segments = self._connect(ax, collection, data, zkey, connect_kwargs)

        cbar = None if zkey is None else self._make_cbar(collection, scale, ax)

        self._format_axis(ax, collection, data)

        return ax, collection, segments, base.Guides(color=cbar)

    def _marker_variables(self, kwargs, **variables):
        r"""Check the size and alpha keywords; return those of the variables given.

        Parameters
        ----------
        kwargs : dict
            The keywords ``make_plot`` passes to ``ax.scatter``.
        **variables : tuple
            For ``size`` and ``alpha``, the norm and range ``make_plot`` got
            and the range's default.

        Returns
        -------
        dict
            For each variable the plot holds, its column name mapped to
            ``(scatter keyword, norm, range)``.

        Raises
        ------
        TypeError
            See ``make_plot``.
        """
        held = self._source.columns
        markers = {}
        for col, (norm, ends, default) in variables.items():
            key = "s" if col == "size" else col
            article = "an" if col == "alpha" else "a"
            if col in held:
                if key in kwargs:
                    raise TypeError(
                        f"make_plot got {key}= while this Scatter has {article} "
                        f"{col} variable; set its mapping with {col}_norm and "
                        f"{col}_range, or build the Scatter without {col}."
                    )
                markers[col] = (key, norm, ends)
                continue
            given = [
                name
                for name, v in (
                    (f"{col}_norm", norm is not None),
                    (f"{col}_range", ends is not default),
                )
                if v
            ]
            if given:
                raise TypeError(
                    f"make_plot got {' and '.join(given)} without {article} "
                    f"{col} variable; pass {col} to Scatter."
                )
        return markers

    def _connect(self, ax, collection, data, zkey, connect_kwargs):
        r"""Add segments joining the drawn points to `ax`; see `make_plot`.

        Parameters
        ----------
        ax: mpl.axes.Axes
        collection: mpl.collections.PathCollection
            The points, whose colormap, norm and colour the segments share.
        data: pd.DataFrame
            The points not hidden by ``alim``, in row order.
        zkey: str or None
            ``"z"`` if the points are colour-mapped, else None.
        connect_kwargs: Mapping or None
            Passed to ``LineCollection``, except a colour key, which sets the
            segments' colour only when `zkey` is None.

        Returns
        -------
        matplotlib.collections.LineCollection
        """
        xy = data.loc[:, ["x", "y"]].to_numpy(dtype=float)
        # The data stay linear, so a log axis cannot show a value <= 0.
        drawn = np.ones(xy.shape[0], dtype=bool)
        for i, log in enumerate(self.log):
            if log:
                drawn &= xy[:, i] > 0
        xy = xy[drawn]

        kwargs = dict(connect_kwargs or {})
        given = [k for k in _COLOR_KEYS if k in kwargs]
        if len(given) > 1:
            raise TypeError(
                f"connect_kwargs gives the colour twice, as {given!r}; give one."
            )
        color = kwargs.pop(given[0]) if given else None
        kwargs = cbook.normalize_kwargs(kwargs, LineCollection)
        kwargs.setdefault("linewidth", 0.75)
        kwargs.setdefault("zorder", collection.get_zorder() - 0.5)

        if zkey is None:
            if color is None:
                color = collection.get_facecolor()[0]
                if "alpha" in data.columns:
                    # Each point has its own alpha: take the colour, opaque.
                    color = mpl.colors.to_rgba(color, alpha=1.0)
            segments = LineCollection(
                np.stack([xy[:-1], xy[1:]], axis=1), color=color, **kwargs
            )
        else:
            if given:
                _warn(
                    f"connect_kwargs[{given[0]!r}] is ignored: z varies, so each "
                    "segment is coloured by the mean z of its two points through "
                    "the points' colormap and norm."
                )
            z = data.loc[:, zkey].to_numpy(dtype=float)[drawn]
            order = np.argsort(z, kind="stable")
            xy, z = xy[order], z[order]
            collection.autoscale_None()
            segments = LineCollection(
                np.stack([xy[:-1], xy[1:]], axis=1),
                cmap=collection.get_cmap(),
                norm=collection.norm,
                **kwargs,
            )
            segments.set_array((z[:-1] + z[1:]) / 2)

        ax.add_collection(segments, autolim=False)
        return segments
