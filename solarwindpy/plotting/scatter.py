#!/usr/bin/env python
r"""Scatter plot utilities with optional color mapping."""

import pdb  # noqa: F401

from matplotlib import pyplot as plt

from . import base


class Scatter(base.PlotWithZdata, base.CbarMaker):
    r"""Create a scatter plot.

    Attributes
    ----------

    Methods
    -------

    Notes
    -----
    """

    def __init__(self, x, y, z=None, clip_data=False):
        r"""Initialize scatter plot data.

        Parameters
        ----------
        x, y: pd.Series
            Data defining (x, y) coordinates.
        z: pd.Series, optional
            If not None, used to specify the color for each point.
        clip_data: bool
            If True, remove extreme values at the 0.001 and 0.999 percentitles.
        """
        super(Scatter, self).__init__()
        self.set_data(x, y, z, clip_data)
        self._labels = base.AxesLabels(x="x", y="y", z="z" if z is not None else None)
        self._log = base.LogAxes(x=False, y=False)
        self.set_path(None)

    def _format_axis(self, ax, collection):
        super()._format_axis(ax)

        x = self.data.loc[:, "x"]
        minx, maxx = x.min(), x.max()

        y = self.data.loc[:, "y"]
        miny, maxy = y.min(), y.max()

        # `pulled from the end of `ax.pcolormesh`.
        collection.sticky_edges.x[:] = [minx, maxx]
        collection.sticky_edges.y[:] = [miny, maxy]
        corners = (minx, miny), (maxx, maxy)
        ax.update_datalim(corners)
        ax.autoscale_view()

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
            Passed to `ax.pcolormesh`.
        """
        if ax is None:
            fig, ax = plt.subplots()

        data = self.data
        if self.clip:
            data = self.clip_data(data, self.clip)

        if data.loc[:, "z"].unique().size > 1:
            zkey = "z"
        else:
            zkey = None

        collection = ax.scatter(x="x", y="y", c=zkey, data=data, **kwargs)

        if cbar and zkey is not None:
            if cbar_kwargs is None:
                cbar_kwargs = dict()

            if "cax" not in cbar_kwargs.keys() and "ax" not in cbar_kwargs.keys():
                cbar_kwargs["ax"] = ax

            cbar = self._make_cbar(collection, **cbar_kwargs)
        else:
            cbar = None

        self._format_axis(ax, collection)

        return ax, cbar
