"""Tools for calculating extrema in LISIRD activity indices."""

__all__ = ["ExtremaCalculator"]


import pandas as pd
import matplotlib as mpl
import numpy as np

from ...plotting import subplots


class ExtremaCalculator(object):
    r"""Determine extrema in an activity index time series.

    The calculator smooths the input series with a rolling mean and finds
    local minima and maxima based on a threshold value.

    Attributes
    ----------
    data : pandas.Series
        Smoothed version of the activity index.
    raw : pandas.Series
        Unsmoothed input data.
    threshold : pandas.Series
        Threshold used to classify maxima and minima.
    extrema : pandas.Series
        Series with ``"Max"`` or ``"Min"`` labels at the extrema times.
    formatted_extrema : pandas.DataFrame
        Data frame formatted as a solar cycle table with ``Min`` and ``Max``
        columns::

            ========== ============ ============
             Interval      Min          Max
            ========== ============ ============
             -1         <DateTime>   <DateTime>
              0         <DateTime>   <DateTime>
              1         <DateTime>   <DateTime>
              ...
              N         <DateTime>   <DateTime>
            ========== ============ ============
    """

    def __init__(self, name, activity_index, threshold=None, window=600):
        r"""Create the calculator.

        Parameters
        ----------
        name : str
            Identifier for the activity index.
        activity_index : pandas.Series
            Raw activity measurements.
        threshold : float or callable, optional
            If a scalar, it is used directly to classify maxima and minima.
            If a callable, it is invoked with ``activity_index`` to compute the
            threshold. When ``None``, the value is looked up from an internal
            table or computed with :func:`numpy.nanmedian`.
        window : int, optional
            Window length in days for the rolling mean.
        """
        self.set_name(name)
        self.set_data(activity_index, window)
        self.set_threshold(threshold)
        self.find_threshold_crossings()
        self.find_extrema()

    @property
    def data(self):
        r"""Activity index after the rolling mean, :class:`pandas.Series`."""
        return self._data

    @property
    def raw(self):
        r"""Activity index as passed in, before smoothing."""
        return self._raw

    @property
    def name(self):
        r"""Activity index name."""
        return self._name

    @property
    def window(self):
        r"""Rolling-mean window in days, or ``None`` for no smoothing."""
        return self._window

    @property
    def threshold(self):
        r"""Threshold separating maxima from minima, one value per time in :attr:`data`."""
        return self._threshold

    @property
    def extrema_finders(self):
        return self._extrema_finders

    @property
    def extrema(self):
        r"""``"Max"`` or ``"Min"`` labels indexed by the time of each extremum."""
        return self._extrema

    @property
    def threshold_crossings(self):
        r"""Values of :attr:`data` at the times it crosses :attr:`threshold`."""
        return self._threshold_crossings

    @property
    def data_in_extrema_finding_intervals(self):
        r"""Interval between threshold crossings that holds each time in :attr:`data`."""
        return self._data_in_extrema_finding_intervals

    @property
    def formatted_extrema(self):
        """Extrema formatted as a solar-cycle table.

        Returns
        -------
        pandas.DataFrame
            Data frame with ``Min`` and ``Max`` columns indexed by cycle::

                ========== ============ ============
                 Interval      Min          Max
                ========== ============ ============
                 -1         <DateTime>   <DateTime>
                  0         <DateTime>   <DateTime>
                  1         <DateTime>   <DateTime>
                  ...
                  N         <DateTime>   <DateTime>
                ========== ============ ============
        """

        return self._formatted_extrema

    def set_name(self, new):
        r"""Set the activity index name.

        Raises
        ------
        ValueError
            For CaK quantities whose threshold has not been determined.
        """
        if new in ("delk2", "delwb", "k2vk3", "viored", "delk1"):
            raise ValueError(
                "Unable to determine threshold. You need to check this one."
            )
        self._name = str(new)

    def set_data(self, index, window):
        r"""Store the raw index and its rolling mean.

        Parameters
        ----------
        index : pandas.Series
            Activity index with a :class:`pandas.DatetimeIndex`. CaK quantities
            are truncated to start on 1977-01-01.
        window : int or None
            Rolling-mean window in days. The smoothed series is shifted back by
            half a window so each mean is centered on its window. ``None``
            skips smoothing.
        """
        if self.name in ("delk1", "delk2", "delwb", "emdx", "k2vk3", "k3", "viored"):
            # We don't trust CaK before then.
            index = index.loc["1977-01-01":]

        rolled = index
        if window is not None:
            rolled = index.rolling("%sd" % window).mean()
            rolled.index = rolled.index - pd.to_timedelta("%sd" % (window / 2.0))

        self._raw = index
        self._data = rolled
        self._window = window

    def _format_axis(self, ax):
        r"""Set year ticks, the legend, and axis labels on ``ax``."""
        left, _ = ax.get_xlim()
        left = pd.to_datetime(
            "{}-01-01".format(pd.to_datetime(mpl.dates.num2date(left)).year - 1)
        )
        ax.set_xlim(
            left=mpl.dates.date2num(left),
            right=mpl.dates.date2num(pd.to_datetime("2020-01-02")),
        )
        ax.xaxis.set_major_formatter(mpl.dates.DateFormatter("%Y"))
        ax.xaxis.set_major_locator(mpl.dates.YearLocator(2))
        ax.figure.autofmt_xdate()

        hdl, lbl = ax.get_legend_handles_labels()
        hdl = np.asarray(hdl)
        lbl = np.asarray(lbl)
        tk = lbl != "indicator"

        ax.legend(hdl[tk], lbl[tk], loc=0, ncol=1, framealpha=0)
        ax.set_ylabel(self.name)
        ax.set_xlabel("Year")

    def _plot_data(self, ax):
        r"""Plot the smoothed index :attr:`data` on ``ax``."""
        x = mpl.dates.date2num(self.data.index)
        y = self.data.values
        ax.plot(x, y, color="C0", label="Rolled")

    def _plot_threshold(self, ax):
        r"""Plot :attr:`threshold` on ``ax``, labeled with its value."""
        x = mpl.dates.date2num(self.data.index)
        y = self.threshold
        ax.plot(x, y, color="C1", label="{:.5f}".format(self.threshold.unique()[0]))

    def _plot_extrema_ranges(self, ax):
        r"""Plot each extrema-finding interval on ``ax`` in alternating colors."""
        joint = pd.concat(
            {"cut": self.data_in_extrema_finding_intervals, "indicator": self.data},
            axis=1,
        )
        gb = joint.groupby("cut")

        ngroup = 0
        for k, v in gb:
            color = "darkorange" if ngroup % 2 else "fuchsia"
            v.plot(ax=ax, color=color, ls="--", label=None)
            ngroup += 1

        ax.legend_.set_visible(False)

    def _plot_threshold_crossings(self, ax):
        r"""Mark :attr:`threshold_crossings` on ``ax``."""
        crossings = self.threshold_crossings
        crossings.plot(ax=ax, color="cyan", marker="P", ls="none", label="Changes")
        ax.legend()

    def _plot_extrema(self, ax):
        r"""Mark the maxima and minima in :attr:`extrema` on ``ax``."""
        maxima = self.data.loc[self.extrema.index].loc[self.extrema == "Max"]
        minima = self.data.loc[self.extrema.index].loc[self.extrema == "Min"]

        for ex, c, lbl in zip((maxima, minima), ("red", "limegreen"), ("Max", "Min")):
            x = mpl.dates.date2num(ex.index)
            y = ex
            ax.plot(x, y, color=c, label=lbl, ls="none", marker="*")

    def set_threshold(self, threshold):
        r"""Set the threshold that separates maxima from minima.

        Parameters
        ----------
        threshold : float, callable, or None
            A number is used as is. A plain Python function
            (:class:`types.FunctionType`, e.g. a ``def`` or ``lambda``) is
            called with :attr:`data` and its result used. ``None`` selects the
            value tabulated for :attr:`name`; when :attr:`name` is not
            tabulated it selects :func:`numpy.nanmedian`, which is then
            handled as a callable.

        Notes
        -----
        Known defect: only :class:`types.FunctionType` is called. Other
        callables, including :func:`numpy.nanmedian` (and so the ``None``
        fallback for an untabulated :attr:`name`) and
        ``functools.partial`` objects, are stored uncalled, and
        :meth:`find_threshold_crossings` then raises :class:`TypeError`.
        ``tests/test_source_misc_defects.py`` records this with a strict
        ``xfail``.
        """
        from numbers import Number
        from types import FunctionType

        automatic = {
            "LymanAlpha": 4.1,
            "delk1": 0.62,
            "emdx": 0.091,
            "f107": 110.0,
            "k3": 0.066,
            "mg_index": 0.27,
            "sd_70": 13.0,
            "sl_70": 2.0,  # Actually log10(sl_70)
            "viored": 1.29,
        }

        if threshold is None:
            threshold = automatic.get(self.name, np.nanmedian)

        if isinstance(threshold, FunctionType):
            threshold = threshold(self.data)

        elif isinstance(threshold, Number):
            pass

        threshold = pd.Series(threshold, index=self.data.index)
        self._threshold = threshold

    @staticmethod
    def _find_extrema(threshold, cut, data):
        r"""Find one extremum in each interval between threshold crossings.

        An interval whose data lie above the threshold contributes its
        maximum; one whose data lie below contributes its minimum.

        Parameters
        ----------
        threshold : pandas.Series
            Threshold, which must take a single value.
        cut : pandas.Series
            Interval label for each time in ``data``.
        data : pandas.Series
            Activity index.

        Returns
        -------
        maxima, minima : pandas.Series
            ``"Max"`` and ``"Min"`` labels indexed by the time of each extremum.
        """
        joint = pd.concat({"cut": cut, "indicator": data}, axis=1)
        gb = joint.groupby("cut")

        thresh = threshold.unique()
        assert thresh.size == 1
        thresh = thresh[0]

        maxima = {}
        minima = {}
        for k, v in gb:
            # Lots of logic to ensure we only have one minima or one maxima
            v = v.indicator
            vclean = v.dropna()
            if not vclean.size:
                # No valid data in this range
                continue

            is_max = (vclean > thresh).value_counts()
            if is_max.size > 1:
                is_max = is_max.replace(1, np.nan).dropna()
            assert is_max.size == 1

            is_max = is_max.index[0]
            if is_max:
                maxima[k] = vclean.idxmax()
            else:
                minima[k] = vclean.idxmin()

        maxima = pd.Series("Max", index=maxima.values())
        minima = pd.Series("Min", index=minima.values())

        return maxima, minima

    def _validate_extrema(self, maxima, minima):
        r"""Drop spurious extrema.

        Indices with known spurious extrema at the ends of their records have
        those entries removed by name. Then any maximum (or minimum) that
        follows the preceding one by 1000 days or less is dropped.

        Returns
        -------
        maxima, minima : pandas.Series
            The retained extrema.
        """
        name = self.name
        if name == "LymanAlpha":
            maxima = maxima.iloc[1:]
        elif name == "delk1":
            minima = minima.iloc[1:-1]
        elif name == "f107":
            minima = minima.iloc[:-1]
            maxima = maxima.iloc[1:]
        elif name == "mg_index":
            maxima = maxima.iloc[1:]
        elif name == "sd_70":
            minima = minima.iloc[:-1]
        elif name == "sl_70":
            minima = minima.iloc[1:]
        elif name == "viored":
            minima = minima.iloc[1:-1]

        minimum_seperation = pd.to_timedelta("1000d")
        tk_max = maxima.index.to_series().diff() > minimum_seperation
        tk_min = minima.index.to_series().diff() > minimum_seperation

        # 0th entry diff is NaT -> False by default.
        tk_max.iloc[0] = True
        tk_min.iloc[0] = True
        maxima = maxima.loc[tk_max]
        minima = minima.loc[tk_min]

        return maxima, minima

    def find_threshold_crossings(self):
        r"""Find the times at which :attr:`data` crosses :attr:`threshold`.

        Returns
        -------
        pandas.Series
            Values of :attr:`data` at each crossing, also stored as
            :attr:`threshold_crossings`.
        """
        data = self.data
        threshold = self.threshold

        high = data > threshold
        low = data < threshold

        dhigh = high.astype(int).diff() != 0
        dlow = low.astype(int).diff() != 0
        deltas = dlow | dhigh
        crossings = data.where(deltas).dropna()

        self._threshold_crossings = crossings
        return crossings

    def cut_data_into_extrema_finding_intervals(self):
        r"""Assign each time in :attr:`data` to an interval between crossings.

        The bin edges are the times in :attr:`threshold_crossings`, extended to
        the first and last times of :attr:`raw`.

        Returns
        -------
        pandas.Series
            Interval for each time in :attr:`data`, also stored as
            :attr:`data_in_extrema_finding_intervals`.
        """
        data = self.data
        raw = self.raw
        crossings = self.threshold_crossings

        bins = crossings.index
        if bins[-1] < raw.index[-1]:
            bins = bins.append(pd.DatetimeIndex([raw.index[-1]]))
        if bins[0] > raw.index[0]:
            bins = bins.append(pd.DatetimeIndex([raw.index[0]]))

        bins = bins.sort_values()

        cut = pd.cut(data.index, bins=bins)
        cut = pd.Series(cut, index=data.index)
        self._data_in_extrema_finding_intervals = cut
        return cut

    @staticmethod
    def format_extrema(extrema):
        r"""Arrange extrema as a cycle table.

        Parameters
        ----------
        extrema : pandas.Series
            ``"Max"`` or ``"Min"`` labels indexed by time.

        Returns
        -------
        pandas.DataFrame
            ``Min`` and ``Max`` times indexed by ``cycle``. Minima are numbered
            from 0; when the first maximum precedes the first minimum, maxima
            are numbered from -1 so each maximum shares a row with the
            minimum that precedes it.
        """
        minima = extrema.loc[extrema == "Min"]
        maxima = extrema.loc[extrema == "Max"]

        min0 = minima.index[0]
        max0 = maxima.index[0]

        if max0 < min0:
            minima = pd.Series(minima.index, np.arange(minima.index.size))
            maxima = pd.Series(maxima.index, np.arange(maxima.index.size) - 1)
        else:
            minima = pd.Series(minima.index, np.arange(minima.index.size))
            maxima = pd.Series(maxima.index, np.arange(maxima.index.size))

        formatted = pd.concat({"Min": minima, "Max": maxima}, axis=1, names=["kind"])
        formatted.index.name = "cycle"

        return formatted

    def find_extrema(self):
        r"""Find, validate, and tabulate the extrema.

        Sets :attr:`extrema` and :attr:`formatted_extrema`.
        """
        data = self.data
        threshold = self.threshold
        cut = self.cut_data_into_extrema_finding_intervals()

        maxima, minima = self._find_extrema(threshold, cut, data)  # data -> raw
        maxima, minima = self._validate_extrema(maxima, minima)
        extrema = pd.concat([maxima, minima], axis=0).sort_index()
        formatted = self.format_extrema(extrema)

        self._extrema = extrema
        self._formatted_extrema = formatted

    def make_plot(self, crossings=False, extrema=False, ranges=False):
        r"""Plot the smoothed index and its threshold.

        Parameters
        ----------
        crossings : bool, optional
            If True, mark :attr:`threshold_crossings`.
        extrema : bool, optional
            If True, mark the maxima and minima.
        ranges : bool, optional
            If True, color each extrema-finding interval.

        Returns
        -------
        matplotlib.axes.Axes
        """
        fig, ax = subplots(scale_width=2.5)

        self._plot_data(ax)
        self._plot_threshold(ax)

        if crossings:
            self._plot_threshold_crossings(ax)

        if ranges:
            self._plot_extrema_ranges(ax)

        if extrema:
            self._plot_extrema(ax)

        self._format_axis(ax)

        return ax
