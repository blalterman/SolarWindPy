"""Plotting helpers for solar activity indicators."""

__all__ = [
    "IndicatorPlot",
    "SSNPlot",
    "plot_on_colorbar",
    "ssn_scale_top",
]

import numpy as np

from matplotlib import dates as mdates
from matplotlib import ticker

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
        self._set_data(indicator, ykey, plasma_index)
        self.set_log(x=False, y=False)
        self._labels = base.AxesLabels(x=labels.epochs.DateTime("Year"), y="y")

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

    def _set_data(self, indicator, ykey, plasma_index):
        r"""Set :attr:`indicator`, :attr:`ykey`, and :attr:`plasma_index`.

        Called only by the constructor; a second call raises ``ValueError``.
        """
        self._claim_data()
        self._indicator = indicator
        self._plasma_index = plasma_index
        self._ykey = ykey

    def make_plot(self, ax=None):
        r"""Plot :attr:`plot_data` against time.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            Axes to draw on. A new figure is created if None.

        Returns
        -------
        ax : matplotlib.axes.Axes
        line : matplotlib.lines.Line2D
            The indicator's line.
        guides : Guides
            Every field None: an indicator plot draws no guide. The slot
            keeps the return order ``(ax, artists..., guides)`` shared by
            every plot.
        """
        if ax is None:
            fig, ax = subplots()

        data = self.plot_data
        x = mdates.date2num(data.index)
        (line,) = ax.plot(x, data, color="k", ls="--", marker=None)

        self._format_axis(ax)

        return ax, line, base.Guides()


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
        r"""Format ``ax`` as :class:`IndicatorPlot` does, with SSN from 0 to a top.

        The top is :func:`ssn_scale_top` of :attr:`plot_data`, the same scale
        :func:`plot_on_colorbar` uses.
        """
        super(SSNPlot, self)._format_axis(ax)
        ax.set_ylim(0, ssn_scale_top(self.plot_data))


def ssn_scale_top(ssn):
    r"""Top of an SSN scale that starts at 0 and holds all of ``ssn``.

    The peak of ``ssn`` rounded up to the next multiple of 100, and never
    less than 100, so the series always stays inside the scale and a
    quiet or empty series cannot give a zero-height scale.

    Parameters
    ----------
    ssn : pandas.Series
        Sunspot numbers to fit on the scale.

    Returns
    -------
    int
        The scale top.
    """
    # Python's max keeps 100 when the peak is NaN (an empty series).
    return int(max(100, np.ceil(ssn.max() / 100.0) * 100))


def plot_on_colorbar(indicator, cax, t0, t1, vertical_cbar=True):
    r"""Plot the sunspot number along a colour bar.

    The sunspot numbers between ``t0`` and ``t1`` are scaled onto the colour
    bar's value axis over ``[0, top]``, where ``top`` is :func:`ssn_scale_top`
    of the window, so the line always stays inside the scale. Major ticks are
    labelled 0, ``top / 2`` and ``top``; minor ticks fall every 25.

    Parameters
    ----------
    indicator : solarwindpy.solar_activity.sunspot_number.sidc.SIDC
        Sunspot-number indicator whose ``ssn`` column is drawn.
    cax : matplotlib.axes.Axes
        The colour bar's axes.
    t0, t1 : datetime-like
        Start and end of the window plotted.
    vertical_cbar : bool
        If True, the colour bar is vertical: time runs along its y-axis
        and the SSN scale along its x-axis. If False, the axes swap and the
        time axis's ticks and label move to the top.

    Returns
    -------
    cax : matplotlib.axes.Axes
    underlay : matplotlib.lines.Line2D
        The solid white line drawn under the overlay.
    overlay : matplotlib.lines.Line2D
        The dash-dotted black sunspot-number line.
    guides : Guides
        Every field None: the function receives only the colour bar's axes,
        not the :class:`matplotlib.colorbar.Colorbar`, and draws no guide of
        its own. The slot keeps the return order ``(ax, artists..., guides)``
        shared by every plot.
    """
    ssn = indicator.data.loc[t0:t1, "ssn"]
    time = mdates.date2num(ssn.index)

    if vertical_cbar:
        ssn_axis, time_axis = cax.xaxis, cax.yaxis
    else:
        ssn_axis, time_axis = cax.yaxis, cax.xaxis

    v0, v1 = ssn_axis.get_view_interval()
    top = ssn_scale_top(ssn)
    scaled = ((ssn / top) * (v1 - v0)) + v0
    points = (scaled, time) if vertical_cbar else (time, scaled)

    (underlay,) = cax.plot(*points, ls="-", color="w", lw=1)
    (overlay,) = cax.plot(*points, ls=(0, (7, 3, 2, 3, 2, 3, 2, 3)), color="k", lw=1)

    ssn_axis.set_label_text(r"$\mathrm{SSN} \; \left[\#\right]$")
    v0, v1 = ssn_axis.get_view_interval()
    ssn_axis.set_ticks([v0, 0.5 * (v0 + v1), v1])
    # The top is a multiple of 100, so the middle label is an integer.
    ssn_axis.set_ticklabels((0, top // 2, top))
    ssn_axis.set_tick_params(rotation=25)
    ssn_axis.set_minor_locator(ticker.MultipleLocator(25))

    if vertical_cbar:
        time_axis.set_tick_params(left=True)
    else:
        time_axis.set_tick_params(top=True)
        time_axis.set_ticks_position("top")
        time_axis.set_label_position("top")

    return cax, underlay, overlay, base.Guides()
