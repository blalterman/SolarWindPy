#!/usr/bin/env python
r"""Scatter plot utilities with optional color mapping."""

__all__ = [
    "Scatter",
]

from matplotlib import pyplot as plt

from . import base


class Scatter(base.ColorPlot):
    r"""Scatter plot of y against x, optionally colored by z."""

    _clipped_axes = ("x", "y", "z")

    def __init__(self, x, y, z=None, clip=None, mask=None):
        r"""Initialize scatter plot data.

        Parameters
        ----------
        x, y: pd.Series
            Data defining (x, y) coordinates.
        z: pd.Series, optional
            If not None, used to specify the color for each point.
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
        self._log = base.LogAxes(x=False, y=False)
        self.set_path(None)

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

        return ax, cbar
