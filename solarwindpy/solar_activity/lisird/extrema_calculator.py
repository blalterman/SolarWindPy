"""Tools for calculating extrema in LISIRD activity indices."""

__all__ = ["ExtremaCalculator"]

import pdb  # noqa: F401

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
        return self._data

    @property
    def raw(self):
        return self._raw

    @property
    def name(self):
        r"""Activity index name."""
        return self._name

    @property
    def window(self):
        return self._window

    @property
    def threshold(self):
        return self._threshold

    @property
    def extrema_finders(self):
        return self._extrema_finders

    @property
    def extrema(self):
        return self._extrema

    @property
    def threshold_crossings(self):
        return self._threshold_crossings

    @property
    def data_in_extrema_finding_intervals(self):
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
        if new in ("delk2", "delwb", "k2vk3", "viored", "delk1"):
            raise ValueError(
                "Unable to determine threshold. You need to check this one."
            )
        self._name = str(new)

    def set_data(self, index, window):

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
        x = mpl.dates.date2num(self.data.index)
        y = self.data.values
        ax.plot(x, y, color="C0", label="Rolled")

    #         x = mpl.dates.date2num(self.raw.index)
    #         y = self.raw.values
    #         ax.plot(x, y, color="C2", label="Raw")

    def _plot_threshold(self, ax):
        x = mpl.dates.date2num(self.data.index)
        y = self.threshold
        ax.plot(x, y, color="C1", label="{:.5f}".format(self.threshold.unique()[0]))

    def _plot_extrema_ranges(self, ax):
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
        crossings = self.threshold_crossings
        crossings.plot(ax=ax, color="cyan", marker="P", ls="none", label="Changes")
        ax.legend()

    def _plot_extrema(self, ax):
        maxima = self.data.loc[self.extrema.index].loc[self.extrema == "Max"]
        minima = self.data.loc[self.extrema.index].loc[self.extrema == "Min"]

        for ex, c, lbl in zip((maxima, minima), ("red", "limegreen"), ("Max", "Min")):
            x = mpl.dates.date2num(ex.index)
            y = ex
            ax.plot(x, y, color=c, label=lbl, ls="none", marker="*")

    def set_threshold(self, threshold):
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
        name = self.name
        if name == "LymanAlpha":
            maxima = maxima.iloc[1:]
        elif name == "delk1":
            minima = minima.iloc[1:-1]
        #         elif name == "emdx":
        #             minima = minima.iloc[2:]
        #             maxima = maxima.iloc[:-1]
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
        # raw = self.raw
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
