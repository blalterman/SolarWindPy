#!/usr/bin/env python
r"""Scatter plot utilities with optional color mapping."""

__all__ = [
    "Scatter",
]

import numpy as np
import matplotlib as mpl
from matplotlib import cbook
from matplotlib import pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.collections import LineCollection
from matplotlib.legend import Legend
from matplotlib.lines import Line2D

from ..tools import _warn
from . import base, labels, scales

# Every spelling of the segments' colour that LineCollection accepts, and
# ``c``, which ``ax.scatter`` accepts.
_COLOR_KEYS = ("color", "c", "colors", "edgecolor", "edgecolors", "ec")

#: Each marker variable's scale class and the ``ax.scatter`` keyword it sets.
_MARKERS = {
    "size": (scales.SizeScale, "s"),
    "alpha": (scales.AlphaScale, "alpha"),
}
#: Colour of the size key's markers: a neutral grey, whatever the points'.
_KEY_COLOR = "0.5"


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

    >>> from solarwindpy.plotting.scales import SizeScale
    >>> s = Scatter(x, y, size=pd.Series([1.0, 2.0, 3.0]))
    >>> ax, collection, segments, guides = s.make_plot(
    ...     size_scale=SizeScale(range=(10, 30))
    ... )
    >>> collection.get_sizes().tolist()
    [10.0, 20.0, 30.0]
    >>> [t.get_text() for t in guides.size.get_texts()]
    ['1', '1.5', '2', '2.5', '3']
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
            ``make_plot``'s ``size_scale``. Aligned by label to x and y, as z
            is; a point whose size is NaN or infinite is not plotted. Held
            in ``data`` as the column ``"size"``.
        alpha: pd.Series or array-like, optional
            A value per point that sets its opacity through ``make_plot``'s
            ``alpha_scale``. Aligned and dropped as ``size`` is, and held in
            ``data`` as the column ``"alpha"``.
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
        self._labels = base.ScatterLabels(
            x="x",
            y="y",
            z="z" if z is not None else None,
            size="size" if size is not None else None,
            alpha="alpha" if alpha is not None else None,
        )
        self.set_log(x=bool(logx), y=bool(logy))

    @property
    def labels(self):
        r"""``ScatterLabels`` namedtuple of the x, y, z, size and alpha labels.

        z, size and alpha are None unless the plot holds that variable.
        """
        return self._labels

    def _set_labels(self, **kwargs):
        r"""Store the labels as ``Base._set_labels`` does, with ``size`` and ``alpha``."""
        size = kwargs.pop("size", self.labels.size)
        alpha = kwargs.pop("alpha", self.labels.alpha)
        super()._set_labels(**kwargs)
        self._labels = base.ScatterLabels(*self._labels, size=size, alpha=alpha)

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
        *,
        color_scale=None,
        size_scale=None,
        alpha_scale=None,
        draw_order="auto",
        draw_ascending=None,
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
            z (see Notes). Not with an alpha variable.
        connect_kwargs: dict, None
            Passed to :class:`~matplotlib.collections.LineCollection`, e.g.
            ``linewidth``, ``alpha`` or ``zorder``. The defaults are a
            ``linewidth`` of 0.75 and a ``zorder`` just below the points'.
            ``facecolor`` has no visible effect, since lines have no faces.
            A colour, under any of the keys ``color``, ``c``, ``colors``,
            ``edgecolor``, ``edgecolors`` or ``ec``, applies only without a
            varying z (see Notes); at most one of them may be given.
            Not modified.
        color_scale: ColorScale, None
            The colour settings as one object (see
            :class:`~solarwindpy.plotting.scales.ColorScale`), in place of
            ``norm``, ``cmap``, ``cbar`` and ``cbar_kwargs``; given with any of
            them, raises ``TypeError``.
        size_scale: SizeScale, None
            How the size variable becomes marker area, and its key (see
            :class:`~solarwindpy.plotting.scales.SizeScale`). None means
            ``SizeScale()``. Only with a size variable.
        alpha_scale: AlphaScale, None
            How the alpha variable becomes opacity, and its bar (see
            :class:`~solarwindpy.plotting.scales.AlphaScale`). None means
            ``AlphaScale()``. Only with an alpha variable.
        draw_order: {"auto", None, "size", "alpha"}
            Which points are drawn last, so on top. ``"size"`` or
            ``"alpha"`` draws the points sorted by their marker area or
            opacity. The sort is by the marker value, not the data: under a
            reversed range the largest values are drawn first when
            ascending. Ties keep row order. None draws them in row order.
            ``"auto"``, the default, is ``"alpha"`` with an alpha variable,
            so the faintest points are drawn on top of the opaque ones that
            would hide them, and None without one. The segments of
            ``connect`` are unaffected.
        draw_ascending: bool, None
            If True, draw from the lowest marker value to the highest, so
            the largest or most opaque points are on top; if False, the
            reverse. None, the default, means False for ``"alpha"``, the
            faintest on top, and True for ``"size"``, the largest on top.
            Ignored when the points are drawn in row order.
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
            ``color`` is the colorbar if `cbar` is True and z varies;
            ``size`` is the size key, a ``matplotlib.legend.Legend`` added
            to ``ax`` as an extra artist, so a legend ``ax`` has, or one a
            later ``ax.legend()`` draws, is drawn beside it; ``alpha`` is
            the alpha bar, a colorbar. Each is None when not drawn.

        Raises
        ------
        TypeError
            If ``s`` is given with a size variable or ``alpha`` with an
            alpha variable; if ``size_scale``, ``alpha_scale`` or
            ``draw_order`` names a variable the Scatter does not hold, or a
            scale is not of its channel's class; if ``connect`` is True with
            an alpha variable; or if ``color_scale`` is given with ``norm``,
            ``cmap``, ``cbar`` or ``cbar_kwargs``.
        ValueError
            If ``draw_order`` is not ``"auto"``, None, ``"size"`` or
            ``"alpha"``.

        Notes
        -----
        Points whose z is outside ``alim`` (see ``set_alim``) are not drawn,
        do not enter the colour scale, and do not set the axis limits. With
        ``kind="quantile"`` the thresholds are quantiles of the plotted z.

        A point is not drawn where x, y, z, size or alpha is NaN or infinite,
        where ``mask`` excludes it, where z is outside ``alim``, or where the
        norm of ``size_scale`` or ``alpha_scale`` masks its value (a value
        <= 0 under ``LogNorm``). Such a point enters neither the colour
        scale nor the size and alpha norms, and does not set the axis
        limits. A point <= 0 on a log axis is left for matplotlib to drop,
        so it still enters the colour scale and the norms. The size and
        alpha mappings run on the drawn points, after ``clip``.

        The size key and the alpha bar are drawn from the scales that drew
        the points, so they read the points exactly: the key's markers have
        the areas points of those sizes get, and the bar's alpha at each
        value is the opacity a point of that value gets. The alpha bar lies
        horizontally above the axes, and the z colorbar stands on their
        right; a ``location``, ``orientation`` or ``cax`` in the alpha
        scale's ``cbar_kwargs`` places the bar instead. When z colours the
        points the alpha bar is black; else it is the points' colour. Their
        titles are ``labels.size`` and ``labels.alpha``. The z colorbar
        stays opaque whatever the points' alpha.

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
        sets, or the points' colour if it sets none. The segments do not set
        the axis limits.
        """
        scale = self._color_scale(kwargs, color_scale, cbar, cbar_kwargs)
        markers, order = self._marker_scales(
            kwargs, size_scale, alpha_scale, connect, draw_order, draw_ascending
        )

        if ax is None:
            fig, ax = plt.subplots()

        data = self.data
        for k, clip in self.clip._asdict().items():
            if clip:
                data[k] = self.clip_data(data.loc[:, k], clip)

        data = data.loc[self._apply_alim(data.loc[:, "z"]).notna()]
        data, mapped = self._map_markers(data, markers)

        if data.loc[:, "z"].unique().size > 1:
            zkey = "z"
            kwargs["norm"], kwargs["cmap"] = self._norm_and_cmap(
                scale, data.loc[:, "z"].to_numpy()
            )
        else:
            zkey = None

        # The draw order sorts the points only; segments keep row order.
        drawn = data
        if order is not None:
            channel, ascending = order
            value = mapped[_MARKERS[channel][1]]
            rank = np.argsort(value if ascending else -value, kind="stable")
            drawn = data.iloc[rank]
            mapped = {k: v[rank] for k, v in mapped.items()}
        kwargs.update(mapped)

        collection = ax.scatter(x="x", y="y", c=zkey, data=drawn, **kwargs)

        segments = None
        if connect:
            segments = self._connect(ax, collection, data, zkey, connect_kwargs)

        cbar = None if zkey is None else self._make_cbar(collection, scale, ax)
        guides = base.Guides(
            color=cbar,
            size=self._size_key(ax, collection, markers.get("size")),
            alpha=self._alpha_bar(ax, collection, markers.get("alpha"), zkey),
        )

        self._format_axis(ax, collection, data)

        return ax, collection, segments, guides

    def _marker_scales(
        self, kwargs, size_scale, alpha_scale, connect, draw_order, draw_ascending
    ):
        r"""Check the size and alpha settings; return each variable's scale and the draw order.

        Parameters
        ----------
        kwargs : dict
            The keywords ``make_plot`` passes to ``ax.scatter``.
        size_scale, alpha_scale : SizeScale, AlphaScale or None
            The caller's scales.
        connect : bool
            The caller's ``connect``.
        draw_order : str or None
            The caller's ``draw_order``.
        draw_ascending : bool or None
            The caller's ``draw_ascending``.

        Returns
        -------
        markers : dict
            For each variable the plot holds, its column name mapped to its
            scale, the default scale when none was given.
        order : tuple or None
            ``(column, ascending)`` to sort the points by that column's
            marker value, or None for row order; ``"auto"`` and a None
            ``draw_ascending`` resolved as ``make_plot`` describes.

        Raises
        ------
        TypeError, ValueError
            See ``make_plot``.
        """
        held = self._source.columns
        given = {"size": size_scale, "alpha": alpha_scale}
        markers = {}
        for col, scale in given.items():
            cls, key = _MARKERS[col]
            name = f"{col}_scale"
            article = "an" if col == "alpha" else "a"
            if scale is not None and not isinstance(scale, cls):
                raise TypeError(
                    f"{name} must be a {cls.__name__} or None, "
                    f"not {type(scale).__name__}"
                )
            if col not in held:
                if scale is not None:
                    raise TypeError(
                        f"make_plot got {name} without {article} {col} "
                        f"variable; pass {col} to Scatter."
                    )
                continue
            if key in kwargs:
                raise TypeError(
                    f"make_plot got {key}= while this Scatter has {article} "
                    f"{col} variable; set its mapping with {name}, or build "
                    f"the Scatter without {col}."
                )
            markers[col] = cls() if scale is None else scale

        if connect and "alpha" in markers:
            raise TypeError(
                "make_plot got connect=True while this Scatter has an alpha "
                "variable; segments between points of different alpha are "
                "not drawn. Build the Scatter without alpha to connect it."
            )
        if draw_order not in ("auto", None, *_MARKERS):
            raise ValueError(
                "draw_order must be 'auto', None, 'size' or 'alpha', "
                f"not {draw_order!r}"
            )
        if draw_order == "auto":
            draw_order = "alpha" if "alpha" in markers else None
        if draw_order is None:
            return markers, None
        if draw_order not in markers:
            article = "an" if draw_order == "alpha" else "a"
            raise TypeError(
                f"make_plot got draw_order={draw_order!r} without {article} "
                f"{draw_order} variable; pass {draw_order} to Scatter."
            )
        if draw_ascending is None:
            draw_ascending = draw_order != "alpha"
        return markers, (draw_order, draw_ascending)

    @staticmethod
    def _map_markers(data, markers):
        r"""Map each marker variable of the drawn points onto its scale's range.

        A point any scale's norm masks is not drawn. A norm whose limits
        were unset is autoscaled once more on the points left, so a point
        that is not drawn sets no limit.

        Parameters
        ----------
        data : pd.DataFrame
            The points left after mask, NaN, ``clip`` and ``alim``.
        markers : dict
            Column name to scale, from ``_marker_scales``.

        Returns
        -------
        data : pd.DataFrame
            The points drawn.
        mapped : dict
            Each ``ax.scatter`` keyword (``s``, ``alpha``) to its values.
        """
        limits = {col: (s.norm.vmin, s.norm.vmax) for col, s in markers.items()}
        values = {col: s._marker_values(data.loc[:, col]) for col, s in markers.items()}
        drawn = np.ones(len(data), dtype=bool)
        for v in values.values():
            drawn &= ~np.ma.getmaskarray(v)
        if not drawn.all():
            data = data.loc[drawn]
            for col, s in markers.items():
                s.norm.vmin, s.norm.vmax = limits[col]
                values[col] = s._marker_values(data.loc[:, col])
        return data, {_MARKERS[col][1]: np.ma.getdata(v) for col, v in values.items()}

    def _size_key(self, ax, points, scale):
        r"""Add the legend of marker areas ``scale`` sets to ``ax``, or return None.

        Each entry is a marker of the points' shape whose area is the one
        ``scale`` gives a point of that size, opaque and grey, labelled
        with the size. A key value the norm masks is left out. The key is
        added with ``ax.add_artist``, not as ``ax``'s legend, so it leaves
        that legend to the caller.

        Returns
        -------
        matplotlib.legend.Legend or None
            None without a size variable or with ``scale.key`` False.
        """
        if scale is None or not scale.key:
            return None
        values = np.asarray(scale._key_values(), dtype=float)
        areas = scale._marker_values(values)
        shown = ~np.ma.getmaskarray(areas)
        marker = points.get_paths()[0]
        handles = [
            Line2D(
                [],
                [],
                linestyle="",
                marker=marker,
                markersize=np.sqrt(area),
                color=_KEY_COLOR,
                alpha=1,
            )
            for area in np.ma.getdata(areas)[shown]
        ]
        texts = [f"{v:g}" for v in values[shown]]
        kwargs = dict(scale.key_kwargs)
        if "title" in kwargs:
            labels.base._warn_if_plain({"key_kwargs['title']": kwargs["title"]})
        title = self.labels.size
        kwargs.setdefault("title", None if title is None else str(title))
        key = ax.add_artist(Legend(ax, handles, texts, **kwargs))
        # add_artist clips an artist to the axes, which takes it out of the
        # layout; ax.legend() leaves its legend unclipped, so this does too.
        key.set_clip_on(False)
        return key

    def _alpha_bar(self, ax, points, scale, zkey):
        r"""Draw the alpha bar ``scale`` sets above ``ax``, or return None.

        The bar is a colorbar on ``scale.norm`` of one colour, black when
        ``zkey`` is set, else the points' colour, whose alpha runs from
        ``scale.range[0]`` to ``scale.range[1]``. It lies horizontally
        above ``ax``, clear of a z colorbar on the right, unless
        ``scale.cbar_kwargs`` sets ``location``, ``orientation`` or
        ``cax``, which place it as matplotlib does.

        Returns
        -------
        matplotlib.colorbar.Colorbar or None
            None without an alpha variable or with ``scale.cbar`` False.
        """
        if scale is None or not scale.cbar:
            return None
        rgb = (0.0, 0.0, 0.0) if zkey else mpl.colors.to_rgb(points.get_facecolor()[0])
        lo, hi = scale.range
        cmap = mpl.colors.LinearSegmentedColormap.from_list(
            "alpha", [(*rgb, lo), (*rgb, hi)]
        )
        mappable = ScalarMappable(norm=scale.norm, cmap=cmap)
        defaults = {}
        if not {"location", "orientation", "cax"} & set(scale.cbar_kwargs):
            defaults["location"] = "top"
        return self._make_cbar(mappable, scale, ax, channel="alpha", **defaults)

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
