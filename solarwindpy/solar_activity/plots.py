"""Plotting helpers for solar activity indicators."""

__all__ = [
    "IndicatorPlot",
    "SSNPlot",
]

from matplotlib import dates as mdates

from abc import abstractmethod

from ..plotting import base, labels
from ..plotting.tools import subplots


class IndicatorPlot(base.Base):
    """Base class for plotting a solar activity indicator.

    Parameters
    ----------
    indicator : solarwindpy.solar_activity.base.ActivityIndicator
        Object providing the time series to plot.
    ykey : str
        Column in ``indicator.data`` to display.
    plasma_index : pandas.DatetimeIndex, optional
        Restrict plotted data to this index.
    """

    def __init__(self, indicator, ykey, plasma_index=None):
        r"""Store the indicator and set linear axes with a year x-label."""
        self.set_data(indicator, ykey, plasma_index)
        self.set_log(x=False, y=False)
        self._labels = base.AxesLabels(x=labels.datetime.DateTime("Year"), y="y")

    @abstractmethod
    def _format_axis(self, ax):
        r"""Set yearly date ticks, axis scales, and axis labels on ``ax``."""
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
        r"""The activity indicator being plotted."""
        return self._indicator

    @property
    def plasma_index(self):
        r"""Times of the plasma data, or ``None`` to plot the whole record."""
        return self._plasma_index

    @property
    def ykey(self):
        r"""Column of ``indicator.data`` that is plotted."""
        return self._ykey

    @property
    def plot_data(self):
        r"""``indicator.data[ykey]`` from the start of :attr:`plasma_index` onward."""
        pidx = self.plasma_index
        if pidx is not None:
            pidx = pidx.min()
        return self.indicator.data.loc[pidx:, self.ykey]

    def set_path(self, new, add_scale=True):
        r"""Set the path figures are saved under.

        Parameters
        ----------
        new : str or pathlib.Path
            ``"auto"`` builds the path from the axis labels.
        add_scale : bool, optional
            If True, append the axis scales to the path.
        """
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
        r"""Set :attr:`indicator`, :attr:`ykey`, and :attr:`plasma_index`."""
        self._indicator = indicator
        self._plasma_index = plasma_index
        self._ykey = ykey

    def make_plot(self, ax=None):
        r"""Plot :attr:`plot_data` against time.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            Axes to draw on. A new figure is created if None.
        """
        if ax is None:
            fig, ax = subplots()

        data = self.plot_data
        x = mdates.date2num(data.index)
        ax.plot(x, data, color="k", ls="--", marker=None)

        self._format_axis(ax)


class SSNPlot(IndicatorPlot):
    """Plotter specialised for sunspot number."""

    def __init__(self, indicator, **kwargs):
        r"""Plot the ``ssn`` column of ``indicator``, labeled by its key.

        Parameters
        ----------
        indicator : solarwindpy.solar_activity.sunspot_number.sidc.SIDC
            Sunspot-number indicator.
        **kwargs
            Passed to :class:`IndicatorPlot`, e.g. ``plasma_index``.
        """
        super(SSNPlot, self).__init__(indicator, "ssn", **kwargs)
        self.set_labels(y=labels.special.SSN(indicator.id.key))

    def _format_axis(self, ax):
        r"""Format ``ax`` as :class:`IndicatorPlot` does, with SSN from 0 to 200."""
        super(SSNPlot, self)._format_axis(ax)
        ax.set_ylim(0, 200)
