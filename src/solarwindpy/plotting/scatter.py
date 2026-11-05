#!/usr/bin/env python
r"""Scatter plot utilities with optional color mapping."""

__all__ = [
    "Scatter",
]

import numpy as np
from matplotlib import cbook
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection

from . import base


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

    This difference is documented for now and needs to be revisited.
    """

    _clipped_axes = ("x", "y", "z")

    def __init__(self, x, y, z=None, logx=None, logy=None, clip=None, mask=None):
        r"""Initialize scatter plot data.

        Parameters
        ----------
        x, y: pd.Series
            Data defining (x, y) coordinates.
        z: pd.Series, optional
            If not None, used to specify the color for each point.
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
        self._set_data(x, y, z, clip, mask=mask)
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
        cbar=True,
        cbar_kwargs=None,
        edges=False,
        edge_kwargs=None,
        **kwargs,
    ):
        r"""Make a scatter plot on `ax` using `ax.scatter`.

        Parameters
        ----------
        ax: mpl.axes.Axes, None
            If None, create an `Axes` instance from `plt.subplots`.
        cbar: bool
            If True, create color bar with `labels.z`.
        cbar_kwargs: dict, None
            If not None, kwargs passed to `self._make_cbar`.
        edges: bool
            If True, join each pair of consecutive points with a line segment
            (see Notes), so a path through the data, e.g. through time, is
            visible.
        edge_kwargs: dict, None
            Passed to :class:`~matplotlib.collections.LineCollection`, e.g.
            ``linewidth``, ``alpha`` or ``zorder``. The defaults are a
            ``linewidth`` of 0.75 and a ``zorder`` just below the points'.
            Not modified.
        kwargs:
            Passed to `ax.scatter`.

        Returns
        -------
        ax: mpl.axes.Axes
        collection: mpl.collections.PathCollection
            The points.
        edges: matplotlib.collections.LineCollection or None
            The segments joining consecutive points if `edges` is True, else
            None.
        cbar: mpl.colorbar.Colorbar or None
            The colorbar if `cbar` is True and z varies, else None.

        Notes
        -----
        Points whose z is outside ``alim`` (see ``set_alim``) are not drawn,
        do not enter the colour scale, and do not set the axis limits. With
        ``kind="quantile"`` the thresholds are quantiles of the plotted z.

        Consecutive points are adjacent rows in the order x, y and z were
        given, by position, not by index label: sort time-indexed data by
        time before building the plot to draw its path through time. A
        segment joins two drawn points only. A row that is not drawn (NaN or
        infinite, outside ``mask``, outside ``alim``, or <= 0 on a log axis)
        breaks the chain: neither of its segments is drawn and its neighbours
        are not joined.

        When z varies, segment i is coloured by ``(z[i] + z[i + 1]) / 2``
        through the points' colormap and norm, the same objects, so the one
        colorbar reads both. Otherwise every segment has the points' colour,
        unless ``edge_kwargs`` sets ``color``. The edges do not set the axis
        limits.
        """
        if ax is None:
            fig, ax = plt.subplots()

        data = self.data
        for k, clip in self.clip._asdict().items():
            if clip:
                data[k] = self.clip_data(data.loc[:, k], clip)

        shown = self._apply_alim(data.loc[:, "z"]).notna()
        data = data.loc[shown]

        if data.loc[:, "z"].unique().size > 1:
            zkey = "z"
        else:
            zkey = None

        collection = ax.scatter(x="x", y="y", c=zkey, data=data, **kwargs)

        lines = None
        if edges:
            lines = self._make_edges(
                ax, collection, data, shown.to_numpy(), zkey, edge_kwargs
            )

        if cbar and zkey is not None:
            cbar_kwargs = self._prepare_cbar_kwargs(cbar_kwargs, ax)
            cbar = self._make_cbar(collection, **cbar_kwargs)
        else:
            cbar = None

        self._format_axis(ax, collection, data)

        return ax, collection, lines, cbar

    def _make_edges(self, ax, collection, data, shown, zkey, edge_kwargs):
        r"""Add segments joining consecutive drawn points to `ax`; see `make_plot`.

        Parameters
        ----------
        ax: mpl.axes.Axes
        collection: mpl.collections.PathCollection
            The points, whose colormap, norm and colour the segments share.
        data: pd.DataFrame
            The drawn points, in source row order.
        shown: np.ndarray of bool
            For each row of ``self.data``, True if ``alim`` keeps it.
        zkey: str or None
            ``"z"`` if the points are colour-mapped, else None.
        edge_kwargs: Mapping or None
            Passed to ``LineCollection``.

        Returns
        -------
        matplotlib.collections.LineCollection
        """
        rows = self._source.rows
        if rows is None:
            position = np.arange(self._source.index.size)
        else:
            position = np.flatnonzero(rows)
        position = position[shown]
        xy = data.loc[:, ["x", "y"]].to_numpy(dtype=float)
        # The data stay linear, so a log axis cannot show a value <= 0.
        drawn = np.ones(position.size, dtype=bool)
        for i, log in enumerate(self.log):
            if log:
                drawn &= xy[:, i] > 0
        joined = (np.diff(position) == 1) & drawn[:-1] & drawn[1:]
        start = np.flatnonzero(joined)

        segments = np.stack([xy[start], xy[start + 1]], axis=1)

        kwargs = cbook.normalize_kwargs(edge_kwargs or {}, LineCollection)
        kwargs.setdefault("linewidth", 0.75)
        kwargs.setdefault("zorder", collection.get_zorder() - 0.5)

        if zkey is None:
            kwargs.setdefault("color", collection.get_facecolor()[0])
            lines = LineCollection(segments, **kwargs)
        else:
            collection.autoscale_None()
            lines = LineCollection(
                segments,
                cmap=collection.get_cmap(),
                norm=collection.norm,
                **kwargs,
            )
            z = data.loc[:, zkey].to_numpy(dtype=float)
            lines.set_array((z[start] + z[start + 1]) / 2)

        ax.add_collection(lines, autolim=False)
        return lines
