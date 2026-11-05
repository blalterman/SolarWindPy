#!/usr/bin/env python
r"""Scatter plot utilities with optional color mapping."""

__all__ = [
    "Scatter",
]

from matplotlib import pyplot as plt

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
    >>> ax, collection, cbar = s.make_plot()
    >>> collection.get_offsets().tolist()
    [[1.0, 4.0], [2.0, 5.0], [3.0, 6.0]]
    >>> collection.get_array().tolist()
    [7.0, 8.0, 9.0]
    >>> cbar is None
    False
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

    def make_plot(self, ax=None, cbar=True, cbar_kwargs=None, **kwargs):
        r"""Make a scatter plot on `ax` using `ax.scatter`.

        Parameters
        ----------
        ax: mpl.axes.Axes, None
            If None, create an `Axes` instance from `plt.subplots`.
        cbar: bool
            If True, create color bar with `labels.z`.
        cbar_kwargs: dict, None
            If not None, kwargs passed to `self._make_cbar`.
        kwargs:
            Passed to `ax.scatter`.

        Returns
        -------
        ax: mpl.axes.Axes
        collection: mpl.collections.PathCollection
            The points.
        cbar: mpl.colorbar.Colorbar or None
            The colorbar if `cbar` is True and z varies, else None.

        Notes
        -----
        Points whose z is outside ``alim`` (see ``set_alim``) are not drawn,
        do not enter the colour scale, and do not set the axis limits. With
        ``kind="quantile"`` the thresholds are quantiles of the plotted z.
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
        else:
            zkey = None

        collection = ax.scatter(x="x", y="y", c=zkey, data=data, **kwargs)

        if cbar and zkey is not None:
            cbar_kwargs = self._prepare_cbar_kwargs(cbar_kwargs, ax)
            cbar = self._make_cbar(collection, **cbar_kwargs)
        else:
            cbar = None

        self._format_axis(ax, collection, data)

        return ax, collection, cbar
