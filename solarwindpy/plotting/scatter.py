#!/usr/bin/env python
r"""Aggregate, create, and save 1D and 2D plots.
"""

import pdb  # noqa: F401

import pandas as pd

from matplotlib import pyplot as plt

from . import base


class Scatter(base.Base):
    r"""Create a scatter plot.

    Properties
    ----------

    Methods
    -------

    Abstract Properties
    -------------------

    Abstract Methods
    ----------------

    Notes
    -----

    """

    def __init__(self, x, y, z=None, clip_data=True):
        r"""
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
        self._labels = base.AxesLabels(x="x", y="y", z="z" if z is not None else "z")
        self.set_path(None)

    def set_data(self, x, y, z=None, clip_data=True):
        data = {"x": x, "y": y}
        data = pd.concat(data, axis=1)

        if z is None:
            z = pd.Series(1, index=data.index)

        data.loc[:, "z"] = z
        data = data.dropna()
        self._data = data
        self._clip = bool(clip_data)

    def set_path(self, new):
        path, x, y, z, scale_info = super(Scatter, self).set_path(new, add_scale=False)

        if new == "auto":

            n_unique_z = self.data.loc[:, "z"].unique().size

            if (z == "z") and (n_unique_z == 1):
                z = "count"

            elif n_unique_z > 1:
                # Expect aggregating data.
                pass

            else:
                raise ValueError("Unable to auto set z-component of path")

            path = path / x / y / z

        else:
            assert x is None
            assert y is None
            assert z is None

        self._path = path

    set_path.__doc__ = base.Base.set_path.__doc__

    def set_labels(self, **kwargs):
        z = kwargs.pop("z", self.labels.z)
        super(Scatter, self).set_labels(z=z, **kwargs)

    def _format_axis(self, ax):
        xlbl = self.labels.x
        if xlbl is not None:
            ax.set_xlabel(xlbl)

        ylbl = self.labels.y
        if ylbl is not None:
            ax.set_ylabel(ylbl)

        ax.grid(True, which="major", axis="both")

    def _make_cbar(self, mappable, ax, **kwargs):
        label = kwargs.pop("label", self.labels.z)
        cbar = ax.figure.colorbar(mappable, ax=ax, label=label, **kwargs)
        return cbar

    def make_plot(self, ax=None, cbar=True, cbar_kwargs=None, **kwargs):
        r"""
        Make a scatter plot on `ax` using `ax.scatter`.

        Paremeters
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
            rng = data.quantile([0.0005, 0.9995])
            lo = rng.loc[0.0005]
            up = rng.loc[0.9995]
            data = data.clip(lower=lo, upper=up, axis=1)

        if data.loc[:, "z"].unique().size > 1:
            zkey = "z"
        else:
            zkey = None

        pc = ax.scatter(x="x", y="y", c=zkey, data=data, **kwargs)

        if cbar and zkey is not None:
            if cbar_kwargs is None:
                cbar_kwargs = dict()
            cbar = self._make_cbar(pc, ax, **cbar_kwargs)
        else:
            cbar = None

        self._format_axis(ax)

        return ax, cbar
