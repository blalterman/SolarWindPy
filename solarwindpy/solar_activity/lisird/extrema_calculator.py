__all__ = ["ExtremaCalculator"]

import pandas as pd
import matplotlib as mpl
import numpy as np

from collections import namedtuple

import solarwindpy as swp


class ExtremaCalculator(object):
    r"""Calculate the minima and maxima for a activity index, defining an
    Indicator Cycle starting at Minima N and ending at Minimum N+1.

    Properties
    ----------
    data: pd.Series
        Activity index, possibly smoothed by `window`.
    raw: pd.Series
        Activity index as passed, not smoothed.
    name: str
        Key identifying index type.
    window: scalar, None
        If not None, the number of days for applying the rolling window.
    threshold: pd.Series
        The threshold for determining Maxima and Minima in a `pd.Series` for each
        point in the `data`.
    extrema_finders: namedtuple
        Contains times when `data` crosses `threshold` (changes) and DateTime information
        binned by the ranges for identifying extrema (`cut`).
    extrema: pd.Series
        Extrema times identifies by extrema type.
    formatted_extrema: pd.DataFrame
        Extrema formatted as the SSN extrema:

            ========== ============ ============
             Interval      Min          Max
            ========== ============ ============
             -1         <DateTime>   <DateTime>
              0         <DateTime>   <DateTime>
              1         <DateTime>   <DateTime>
              ...
              N         <DateTime>   <DateTime>
            ========== ============ ============

    Methods
    -------
    set_name, set_data, set_threshold, find_extrema, make_plot
    """

    def __init__(self, name, activity_index, threshold, window=None):
        r"""Parameters
        ----------
        name: str
            key used to select activity indicator.
        activity_index: pd.Series
            Data as measured for the index.
        threshold: scalar, FunctionType, number
            If scalar, the threshold for selecting data for finding Maxima/Minima.
            If FunctionType, called on `activity_index` (`self.data`) to calculate the threshold.
            If None, pull scalar from an internal dictionary. If not present in dictionary,
            calculate with `np.nanmedian`.
        window: scalar, None
            If not None, the number of days to apply for a rolling window mean.
        """
        self.set_name(name)
        self.set_data(activity_index, window)
        self.set_threshold(threshold)
        self.find_extrema()

    @property
    def data(self):
        return self._data

    @property
    def raw(self):
        return self._raw

    @property
    def name(self):
        r"""Activity index name.
        """
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
    def formatted_extrema(self):
        ext = self.extrema
        minima = ext.loc[ext == "Min"]
        maxima = ext.loc[ext == "Max"]

        min0 = minima.index[0]
        max0 = maxima.index[0]

        if max0 < min0:
            minima = pd.Series(minima.index, np.arange(minima.index.size))
            maxima = pd.Series(maxima.index, np.arange(maxima.index.size) - 1)
        else:
            minima = pd.Series(minima.index, np.arange(minima.index.size))
            maxima = pd.Series(maxima.index, np.arange(maxima.index.size))

        to_save = pd.concat({"Min": minima, "Max": maxima}, axis=1)

        return to_save

    def set_name(self, new):
        if new in ("delk2", "delwb", "k2vk3", "viored", "delk1"):
            raise ValueError(
                "Unable to determine threshold. You need to check this one."
            )
        self._name = str(new)

    def set_data(self, index, window):
        rolled = index.rolling("%sd" % window).mean()
        rolled.index = rolled.index - pd.to_timedelta("%sd" % (window / 2.0))

        self._raw = index
        self._data = rolled
        self._window = window

    def _format_axis(self, ax):
        ax.set_xlim(right=mpl.dates.date2num(pd.to_datetime("2020-01-02")))
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
            {"cut": self.extrema_finders.cut, "indicator": self.data}, axis=1
        )
        gb = joint.groupby("cut")

        ngroup = 0
        for k, v in gb:
            color = "darkorange" if ngroup % 2 else "fuchsia"
            v.plot(ax=ax, color=color, ls="--", label=None)
            ngroup += 1

        ax.legend_.set_visible(False)

    def _plot_extrema_changes(self, ax):
        changes = self.extrema_finders.changes
        changes.plot(ax=ax, color="cyan", marker="P", ls="none", label="Changes")
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
    def _calculate_changes_between_extrema_regions(data, threshold):

        high = data > threshold
        low = data < threshold

        dhigh = high.astype(int).diff() != 0
        dlow = low.astype(int).diff() != 0
        deltas = dlow | dhigh
        changes = data.where(deltas).dropna()
        return changes

    @staticmethod
    def _cut_data_into_extrema_finding_intervals(data, changes):
        bins = changes.index
        if bins[-1] <= data.index[-1]:
            bins = bins.append(pd.DatetimeIndex([data.index[-1]]))
        if bins[0] >= data.index[0]:
            bins = bins.append(pd.DatetimeIndex([data.index[0]]))
        bins = bins.sort_values()

        cut = pd.cut(data.index, bins=bins)
        cut = pd.Series(cut, index=data.index)
        return cut

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
        elif name == "emdx":
            minima = minima.iloc[2:]
        #             maxima = maxima.iloc[:-1]
        elif name == "f107":
            minima = minima.iloc[:-1]
            maxima = maxima.iloc[1:]
        elif name == "k3":
            minima = minima.iloc[1:-1]
        elif name == "mg_index":
            maxima = maxima.iloc[1:]
        elif name == "sd_70":
            minima = minima.iloc[:-1]
        elif name == "sl_70":
            minima = minima.iloc[1:]
        elif name == "viored":
            minima = minima.iloc[1:-1]

        return maxima, minima

    def find_extrema(self):
        # raw = self.raw
        data = self.data
        threshold = self.threshold

        changes = self._calculate_changes_between_extrema_regions(data, threshold)
        cut = self._cut_data_into_extrema_finding_intervals(data, changes)
        maxima, minima = self._find_extrema(threshold, cut, data)  # data -> raw
        maxima, minima = self._validate_extrema(maxima, minima)

        extrema = pd.concat([maxima, minima], axis=0).sort_index()

        ExtremaFinders = namedtuple("ExtremaFinders", "changes,cut")
        ef = ExtremaFinders(changes, cut)
        self._extrema_finders = ef
        self._extrema = extrema

    def make_plot(self, extrema=False, extrema_ranges=False):
        fig, ax = swp.pp.subplots(scale_width=2.5)

        self._plot_data(ax)
        self._plot_threshold(ax)

        if extrema_ranges:
            self._plot_extrema_changes(ax)
            self._plot_extrema_ranges(ax)

        if extrema:
            self._plot_extrema(ax)
        self._format_axis(ax)

        return ax
