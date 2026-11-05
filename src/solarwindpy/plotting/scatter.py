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

    Examples
    --------
    >>> import pandas as pd
    >>> import matplotlib.pyplot as plt
    >>> from solarwindpy.plotting.scatter import Scatter
    >>> x = pd.Series([1.0, 2.0, 3.0])
    >>> y = pd.Series([4.0, 5.0, 6.0])
    >>> z = pd.Series([7.0, 8.0, 9.0])
    >>> s = Scatter(x, y, z)
    >>> ax, collection, segments, cbar = s.make_plot()
    >>> collection.get_offsets().tolist()
    [[1.0, 4.0], [2.0, 5.0], [3.0, 6.0]]
    >>> collection.get_array().tolist()
    [7.0, 8.0, 9.0]
    >>> segments is None, cbar is None
    (True, False)
    >>> plt.close("all")
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
        connect=False,
        connect_kwargs=None,
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
        connect: bool
            If True, join the drawn points with line segments in increasing
            z (see Notes).
        connect_kwargs: dict, None
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
        segments: mpl.collections.LineCollection or None
            The segments joining the points if `connect` is True, else None.
        cbar: mpl.colorbar.Colorbar or None
            The colorbar if `cbar` is True and z varies, else None.

        Notes
        -----
        Points whose z is outside ``alim`` (see ``set_alim``) are not drawn,
        do not enter the colour scale, and do not set the axis limits. With
        ``kind="quantile"`` the thresholds are quantiles of the plotted z.

        With ``connect=True`` each drawn point is joined to the drawn point
        next in increasing z, a stable sort, so points with equal z keep the
        order of their rows and the rows need not be sorted. With z the time
        of each point, the segments trace its trajectory; with any other z
        they trace how (x, y) changes as z increases. Without a varying z
        (no z, or one value), the points are joined in row order. A point
        that is not drawn (NaN or infinite, outside ``mask``, outside
        ``alim``, or <= 0 on a log axis) is skipped, not a gap: the points
        on either side of it are joined.

        When z varies, each segment is coloured by the mean z of its two
        points, ``(z_a + z_b) / 2``, through the points' colormap and norm,
        the same objects, so the one colorbar reads both. Otherwise every
        segment has the points' colour, unless ``connect_kwargs`` sets
        ``color``. The segments do not set the axis limits.
        """
        if ax is None:
            fig, ax = plt.subplots()

        data = self.data
        for k, clip in self.clip._asdict().items():
            if clip:
                data[k] = self.clip_data(data.loc[:, k], clip)

        data = data.loc[self._apply_alim(data.loc[:, "z"]).notna()]

        if data.loc[:, "z"].unique().size > 1:
            zkey = "z"
            kwargs["norm"], kwargs["cmap"] = self._color_scale(
                kwargs, data.loc[:, "z"].to_numpy()
            )
        else:
            zkey = None

        collection = ax.scatter(x="x", y="y", c=zkey, data=data, **kwargs)

        segments = None
        if connect:
            segments = self._connect(ax, collection, data, zkey, connect_kwargs)

        if cbar and zkey is not None:
            cbar_kwargs = self._prepare_cbar_kwargs(cbar_kwargs, ax)
            cbar = self._make_cbar(collection, **cbar_kwargs)
        else:
            cbar = None

        self._format_axis(ax, collection, data)

        return ax, collection, segments, cbar

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
            Passed to ``LineCollection``.

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

        kwargs = cbook.normalize_kwargs(connect_kwargs or {}, LineCollection)
        kwargs.setdefault("linewidth", 0.75)
        kwargs.setdefault("zorder", collection.get_zorder() - 0.5)

        if zkey is None:
            kwargs.setdefault("color", collection.get_facecolor()[0])
            segments = LineCollection(np.stack([xy[:-1], xy[1:]], axis=1), **kwargs)
        else:
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
