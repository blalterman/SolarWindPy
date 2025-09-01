"""Plotting helpers for solar activity indicators."""

import pdb  # noqa: F401
from matplotlib import dates as mdates

# import numpy as np
# import pandas as pd

# from pathlib import Path
from abc import abstractmethod

from ..plotting import base, labels, subplots

# pd.set_option("mode.chained_assignment", "raise")


class IndicatorPlot(base.Base):
    """Base class for plotting a solar activity indicator.

    Parameters
    ----------
    indicator : ActivityIndicator
        Object providing the time series to plot.
    ykey : str
        Column in ``indicator.data`` to display.
    plasma_index : pandas.DatetimeIndex, optional
        Restrict plotted data to this index.
    """

    def __init__(self, indicator, ykey, plasma_index=None):

        self.set_data(indicator, ykey, plasma_index)
        self.set_log(x=False, y=False)
        self._labels = base.AxesLabels(x=labels.special.DateTime("Year"), y="y")

    @abstractmethod
    def _format_axis(self, ax):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_tick_params(which="major", rotation=45)

        if self.log.x:
            ax.set_xscale("log")
        if self.log.y:
            ax.set_yscale("log")

        ax.set_xlabel(self.labels.x)
        ax.set_ylabel(self.labels.y)

        return ax

    @property
    def indicator(self):
        return self._indicator

    @property
    def plasma_index(self):
        return self._plasma_index

    @property
    def ykey(self):
        return self._ykey

    @property
    def plot_data(self):
        pidx = self.plasma_index
        if pidx is not None:
            pidx = pidx.min()
        return self.indicator.data.loc[pidx:, self.ykey]

    def set_path(self, new, add_scale=True):
        path, x, y, z, scale_info = super(IndicatorPlot, self).set_path(new, add_scale)

        if new == "auto":
            path = path / x / y

        else:
            assert x is None
            assert y is None

        if add_scale:
            assert scale_info is not None
            scale_info = "-".join(scale_info)
            path = path / scale_info

        self._path = path

    def set_data(self, indicator, ykey, plasma_index):
        self._indicator = indicator
        self._plasma_index = plasma_index
        self._ykey = ykey

    def make_plot(self, ax=None):
        if ax is None:
            fig, ax = subplots()

        data = self.plot_data
        x = mdates.date2num(data.index)
        ax.plot(x, data, color="k", ls="--", marker=None)

        self._format_axis(ax)


class SSNPlot(IndicatorPlot):
    """Plotter specialised for sunspot number."""

    def __init__(self, indicator, **kwargs):
        super(SSNPlot, self).__init__(indicator, "ssn", **kwargs)
        self.set_labels(y=labels.special.SSN(indicator.id.key))

    def _format_axis(self, ax):
        super(SSNPlot, self)._format_axis(ax)
        ax.set_ylim(0, 200)


# SSNPlot(indicator, plasma_index=plasma.index).make_plot()
