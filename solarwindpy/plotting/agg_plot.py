#!/usr/bin/env python
r"""Abstract helpers for aggregated plotting.

These classes calculate bin edges, perform data aggregation, and provide
common functionality used by :mod:`solarwindpy` histogram plots.
"""

import pdb  # noqa: F401

import numpy as np
import pandas as pd

from numbers import Number
from abc import abstractproperty, abstractmethod

try:
    from astropy.stats import knuth_bin_width
except ModuleNotFoundError:
    pass

from . import base

# import os
# import psutil


# def log_mem_usage():
#    usage = psutil.Process(os.getpid()).memory_info()
#    usage = "\n".join(
#        ["{} {:.3f} GB".format(k, v * 1e-9) for k, v in usage._asdict().items()]
#    )
#    logging.getLogger("main").warning("Memory usage\n%s", usage)


class AggPlot(base.Base):
    r"""ABC for aggregating data in 1D and 2D.

    Attributes
    ----------
    logger, data, bins, clip, cut, logx, labels.x, labels.y, clim, agg_axes
    path, _gb_axes (abstract)

    Methods
    -------
    set_<>:
        Set property <>.

    calc_bins, make_cut, agg, clip_data, make_plot
    __init__, set_labels.y, set_path, set_data, _format_axis, make_plot (abstract)
    """

    @property
    def edges(self):
        return {k: v.left.union(v.right) for k, v in self.intervals.items()}

    @property
    def categoricals(self):
        return dict(self._categoricals)

    @property
    def intervals(self):
        #         return dict(self._intervals)
        return {k: pd.IntervalIndex(v) for k, v in self.categoricals.items()}

    @property
    def cut(self):
        return self._cut

    @property
    def clim(self):
        return self._clim

    @property
    def alim(self):
        return self._alim

    @property
    def agg_axes(self):
        r"""The axis to aggregate into, e.g. the z variable in an (x, y, z) heatmap."""
        tko = [c for c in self.data.columns if c not in self._gb_axes]
        assert len(tko) == 1
        tko = tko[0]
        return tko

    @property
    def joint(self):
        r"""Combines the categorical and continuous data for `Groupby`."""
        #         cut = self.cut
        #         tko = self.agg_axes

        #         self.logger.debug(f"Joining data ({tko}) with cat ({cut.columns.values})")

        #         other = self.data.loc[cut.index, tko]

        #         #         joint = pd.concat([cut, other.to_frame(name=tko)], axis=1, sort=True)
        #         joint = cut.copy(deep=True)
        #         joint.loc[:, tko] = other
        #         joint.sort_index(axis=1, inplace=True)
        #         return joint

        cut = self.cut
        tk_target = self.agg_axes
        target = self.data.loc[cut.index, tk_target]

        mi = pd.MultiIndex.from_frame(cut)
        target.index = mi

        return target

    @property
    def grouped(self):
        r"""`joint.groupby` with appropriate axes passes."""
        #         tko = self.agg_axes
        #         gb = self.data.loc[:, tko].groupby([v for k, v in self.cut.items()], observed=False)
        #         gb = self.joint.groupby(list(self._gb_axes))

        #         cut = self.cut
        #         tk_target = self.agg_axes
        #         target = self.data.loc[cut.index, tk_target]

        #         mi = pd.MultiIndex.from_frame(cut)
        #         target.index = mi

        target = self.joint
        gb_axes = list(self._gb_axes)
        gb = target.groupby(gb_axes, axis=0, observed=True)

        #         agg_axes = self.agg_axes
        #         gb = (
        #             self.joint.set_index(gb_axes)
        #             .loc[:, agg_axes]
        #             .groupby(gb_axes, axis=0, observed=False)
        #         )
        return gb

    @property
    def axnorm(self):
        r"""Data normalization in plot.

        Not `mpl.colors.Normalize` instance. That is passed as a `kwarg` to
        `make_plot`.
        """
        return self._axnorm

    # Old version that cuts at percentiles.
    @staticmethod
    def clip_data(data, clip):
        q0 = 0.0001
        q1 = 0.9999
        pct = data.quantile([q0, q1])
        lo = pct.loc[q0]
        up = pct.loc[q1]

        if isinstance(data, pd.Series):
            ax = 0
        elif isinstance(data, pd.DataFrame):
            ax = 1
        else:
            raise TypeError("Unexpected object %s" % type(data))

        if isinstance(clip, str) and clip.lower()[0] == "l":
            data = data.clip_lower(lo, axis=ax)
        elif isinstance(clip, str) and clip.lower()[0] == "u":
            data = data.clip_upper(up, axis=ax)
        else:
            data = data.clip(lo, up, axis=ax)
        return data

    # New version that uses binning to cut.
    #     @staticmethod
    #     def clip_data(data, bins, clip):
    #         q0 = 0.001
    #         q1 = 0.999
    #         pct = data.quantile([q0, q1])
    #         lo  = pct.loc[q0]
    #         up  = pct.loc[q1]
    #         lo = bins.iloc[0]
    #         up = bins.iloc[-1]
    #         if isinstance(clip, str) and clip.lower()[0] == "l":
    #             data = data.clip_lower(lo)
    #         elif isinstance(clip, str) and clip.lower()[0] == "u":
    #             data = data.clip_upper(up)
    #         else:
    #             data = data.clip(lo, up)
    #         return data

    def set_clim(self, lower=None, upper=None):
        """Set the minimum (lower) and maximum (upper) allowed number of.

        counts per bin to return after calling :py:meth:`agg`.
        """
        assert isinstance(lower, Number) or lower is None
        assert isinstance(upper, Number) or upper is None
        self._clim = (lower, upper)

    def set_alim(self, lower=None, upper=None):
        r"""Set the minimum (lower) and maximum (upper) allowed value when.

        aggregating. This is different from `clim` because it uses the
        `agg_fcn`. So behavior will change based on `axnorm`, etc.
        """
        assert isinstance(lower, Number) or lower is None
        assert isinstance(upper, Number) or upper is None
        self._alim = (lower, upper)

    def calc_bins_intervals(self, nbins=101, precision=None):
        r"""Calculate histogram bins.

        nbins: int, str, array-like
            If int, use np.histogram to calculate the bin edges.
            If str and nbins == "knuth", use `astropy.stats.knuth_bin_width`
            to calculate optimal bin widths.
            If str and nbins != "knuth", use `np.histogram(data, bins=nbins)`
            to calculate bins.
            If array-like, treat as bins.

        precision: int or None
            Precision at which to store intervals. If None, default to 3.
        """
        data = self.data
        bins = {}
        intervals = {}

        if precision is None:
            precision = 5

        gb_axes = self._gb_axes

        if isinstance(nbins, (str, int)) or (
            hasattr(nbins, "__iter__") and len(nbins) != len(gb_axes)
        ):
            # Single paramter for `nbins`.
            nbins = {k: nbins for k in gb_axes}

        elif len(nbins) == len(gb_axes):
            # Passed one bin spec per axis
            nbins = {k: v for k, v in zip(gb_axes, nbins)}

        else:
            msg = f"Unrecognized `nbins`\ntype: {type(nbins)}\n bins:{nbins}"
            raise ValueError(msg)

        for k in self._gb_axes:
            b = nbins[k]
            # Numpy and Astropy don't like NaNs when calculating bins.
            # Infinities in bins (typically from log10(0)) also create problems.
            d = data.loc[:, k].replace([-np.inf, np.inf], np.nan).dropna()

            if isinstance(b, str):
                b = b.lower()

            if isinstance(b, str) and b == "knuth":
                try:
                    assert knuth_bin_width
                except NameError:
                    raise NameError("Astropy is unavailable.")

                dx, b = knuth_bin_width(d, return_bins=True)

            else:
                try:
                    b = np.histogram_bin_edges(d, b)
                except MemoryError:
                    # Clip the extremely large values and extremely small outliers.
                    lo, up = d.quantile([0.0005, 0.9995])
                    b = np.histogram_bin_edges(d.clip(lo, up), b)
                except AttributeError:
                    c, b = np.histogram(d, b)

            assert np.unique(b).size == b.size
            try:
                assert not np.isnan(b).any()
            except TypeError:
                assert not b.isna().any()

            b = b.round(precision)

            zipped = zip(b[:-1], b[1:])
            i = [pd.Interval(*b0b1, closed="right") for b0b1 in zipped]

            bins[k] = b
            #             intervals[k] = pd.IntervalIndex(i)
            intervals[k] = pd.CategoricalIndex(i)

        bins = tuple(bins.items())
        intervals = tuple(intervals.items())
        #         self._intervals = intervals
        self._categoricals = intervals

    def make_cut(self):
        r"""Calculate the `Categorical` quantities for the aggregation axes."""
        intervals = self.intervals
        data = self.data

        cut = {}
        for k in self._gb_axes:
            d = data.loc[:, k]
            i = intervals[k]

            if self.clip:
                d = self.clip_data(d, self.clip)

            c = pd.cut(d, i)
            cut[k] = c

        cut = pd.DataFrame.from_dict(cut, orient="columns")
        self._cut = cut

    def _agg_runner(self, cut, tko, gb, fcn, **kwargs):
        r"""Refactored out the aggregation.

        This enables compatibility with :py:class:`OrbitPlot` aggregation of
        different orbit legs (Inbound, Outbound, and Both).
        """
        self.logger.debug(f"aggregating {tko} data along {cut.columns.values}")

        if fcn is None:
            other = self.data.loc[cut.index, tko]
            if other.dropna().unique().size == 1:
                fcn = "count"
            else:
                fcn = "mean"

        agg = gb.agg(fcn, **kwargs)  # .loc[:, tko]

        c0, c1 = self.clim
        if c0 is not None or c1 is not None:
            cnt = gb.agg("count")  # .loc[:, tko]
            tk = pd.Series(True, index=agg.index)
            #             tk  = pd.DataFrame(True,
            #                                index=agg.index,
            #                                columns=agg.columns
            #                               )
            if c0 is not None:
                tk = tk & (cnt >= c0)
            if c1 is not None:
                tk = tk & (cnt <= c1)

            agg = agg.where(tk)

        #         #         Using `observed=False` in `self.grouped` raised a TypeError because mixed Categoricals and np.nans. (20200229)
        #         # Ensure all bins are represented in the data. (20190605)
        # #         for k, v in self.intervals.items():
        #         for k, v in self.categoricals.items():
        #             # if > 1 intervals, pass level. Otherwise, don't as this raises a NotImplementedError. (20190619)
        #             agg = agg.reindex(index=v, level=k if agg.index.nlevels > 1 else None)

        return agg

    def _agg_reindexer(self, agg):
        #         Using `observed=False` in `self.grouped` raised a TypeError because mixed Categoricals and np.nans. (20200229)
        # Ensure all bins are represented in the data. (20190605)
        #         for k, v in self.intervals.items():
        for k, v in self.categoricals.items():
            # if > 1 intervals, pass level. Otherwise, don't as this raises a NotImplementedError. (20190619)
            agg = agg.reindex(index=v, level=k if agg.index.nlevels > 1 else None)

        return agg

    def agg(self, fcn=None, **kwargs):
        r"""Perform the aggregation along the agg axes.

        If either of the count limits specified in `clim` are not None, apply them.

        `fcn` allows you to specify a specific function for aggregation. Otherwise,
        automatically choose "count" or "mean" based on the uniqueness of the aggregated
        values.
        """
        cut = self.cut
        tko = self.agg_axes

        lbls = {k: str(v).replace("\n", " ") for k, v in self.labels._asdict().items()}
        self.logger.info(
            f"Starting {self.__class__.__name__!s} aggregation of ({tko}) in ({cut.columns.values})\n%s",
            "\n".join([f"""{k!s}: {v!s}""" for k, v in lbls.items()]),
        )

        gb = self.grouped

        agg = self._agg_runner(cut, tko, gb, fcn, **kwargs)

        return agg

    def get_plotted_data_boolean_series(self):
        """Return a boolean ``pd.Series`` identifying each plotted measurement.

        The series shares the same index as the stored data. To align with a different
        index you may need to adjust the returned series.
        """
        agg = self.agg().dropna()
        cut = self.cut

        tk = pd.Series(True, index=cut.index)
        for k, v in cut.items():
            idx = agg.index.get_level_values(k)
            # Use the codes directly because the categoricals are
            # failing with some Pandas numpy ufunc use. (20200611)
            # Also need to ensure codes are consistent between the
            # two objects. (20201111)
            cat = v.unique()
            codes = cat.codes
            mapper = pd.Series(codes, index=cat)
            mapped_idx = idx.map(mapper)
            mapped_v = v.map(mapper)

            tk_ax = mapped_v.isin(mapped_idx)
            tk = tk & tk_ax

        self.logger.info(
            f"Taking {tk.sum()!s} ({100 * tk.mean():.1f}%) {self.__class__.__name__} spectra"
        )

        return tk

    def get_subset_above_threshold(self, threshold, fcn="count"):
        r"""Get the subset of data above a given threshold using `fcn` to.

        aggregate. If `axnorm` set, this is used.
        """
        agg = self.agg(fcn=fcn)
        tk = agg >= threshold
        tk = tk.loc[tk]

        tk_h2 = pd.Series(True, index=self.data.index)
        for k, v in self.cut.items():
            tk_ax = pd.IntervalIndex(v).isin(tk.index.get_level_values(k).unique())
            tk_h2 = tk_h2 & tk_ax

        subset = self.data.loc[tk_h2].copy(deep=True)
        for k, log in self.log._asdict().items():
            if log:
                subset.loc[:, k] = 10 ** subset.loc[:, k]

        return subset, tk_h2

    #     Old version that cuts at percentiles.
    #     @staticmethod
    #     def clip_data(data, clip):
    #         q0 = 0.0001
    #         q1 = 0.9999
    #         pct = data.quantile([q0, q1])
    #         lo = pct.loc[q0]
    #         up = pct.loc[q1]
    #
    #         if isinstance(data, pd.Series):
    #             ax = 0
    #         elif isinstance(data, pd.DataFrame):
    #             ax = 1
    #         else:
    #             raise TypeError("Unexpected object %s" % type(data))
    #
    #         if isinstance(clip, str) and clip.lower()[0] == "l":
    #             data = data.clip_lower(lo, axis=ax)
    #         elif isinstance(clip, str) and clip.lower()[0] == "u":
    #             data = data.clip_upper(up, axis=ax)
    #         else:
    #             data = data.clip(lo, up, axis=ax)
    #         return data
    #
    #     New version that uses binning to cut.
    #         @staticmethod
    #         def clip_data(data, bins, clip):
    #             q0 = 0.001
    #             q1 = 0.999
    #             pct = data.quantile([q0, q1])
    #             lo  = pct.loc[q0]
    #             up  = pct.loc[q1]
    #             lo = bins.iloc[0]
    #             up = bins.iloc[-1]
    #             if isinstance(clip, str) and clip.lower()[0] == "l":
    #                 data = data.clip_lower(lo)
    #             elif isinstance(clip, str) and clip.lower()[0] == "u":
    #                 data = data.clip_upper(up)
    #             else:
    #                 data = data.clip(lo, up)
    #             return data

    @abstractproperty
    def _gb_axes(self):
        r"""The axes or columns over which the `groupby` aggregation takes place.

        1D cases aggregate over `x`. 2D cases aggregate over `x` and `y`.
        """
        pass

    @abstractmethod
    def set_axnorm(self, new):
        r"""The method by which the gridded data is normalized."""
        pass
