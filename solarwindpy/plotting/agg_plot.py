#!/usr/bin/env python
r"""Abstract helpers for aggregated plotting.

These classes calculate bin edges, perform data aggregation, and provide
common functionality used by :mod:`solarwindpy` histogram plots.
"""

import numpy as np
import pandas as pd

from numbers import Integral, Number
from abc import abstractproperty, abstractmethod

try:
    from astropy.stats import knuth_bin_width
except ModuleNotFoundError:
    pass

from . import base


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
        return {k: pd.IntervalIndex(v) for k, v in self.categoricals.items()}

    @property
    def cut(self):
        return self._cut

    @property
    def clim(self):
        return self._clim

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
        cut = self.cut
        tk_target = self.agg_axes
        target = self.data.loc[cut.index, tk_target]

        mi = pd.MultiIndex.from_frame(cut)
        target.index = mi

        return target

    @property
    def grouped(self):
        r"""`joint.groupby` with appropriate axes passes."""

        target = self.joint
        gb_axes = list(self._gb_axes)
        gb = target.groupby(gb_axes, observed=True)

        return gb

    @property
    def axnorm(self):
        r"""Data normalization in plot.

        Not `mpl.colors.Normalize` instance. That is passed as a `kwarg` to
        `make_plot`.
        """
        return self._axnorm

    @staticmethod
    def clip_data(data, clip):
        r"""Clip data to its 0.01st and 99.99th percentiles.

        Parameters
        ----------
        data : pd.Series or pd.DataFrame
            Data to clip. A DataFrame is clipped column by column.
        clip : bool or str
            A string starting with ``"l"`` or ``"u"`` selects the lower or upper
            tail only; any other value clips both tails.

        Returns
        -------
        pd.Series or pd.DataFrame
            The clipped data.

        Raises
        ------
        TypeError
            If ``data`` is neither a Series nor a DataFrame.
        """
        if isinstance(data, pd.Series):
            ax = 0
        elif isinstance(data, pd.DataFrame):
            ax = 1
        else:
            raise TypeError("Unexpected object %s" % type(data))

        q0 = 0.0001
        q1 = 0.9999
        pct = data.quantile([q0, q1])
        lo = pct.loc[q0]
        up = pct.loc[q1]

        if isinstance(clip, str) and clip.lower()[0] == "l":
            data = data.clip(lower=lo, axis=ax)
        elif isinstance(clip, str) and clip.lower()[0] == "u":
            data = data.clip(upper=up, axis=ax)
        else:
            data = data.clip(lo, up, axis=ax)
        return data

    @staticmethod
    def _bin_widths(bins):
        r"""Width of each bin in the binned variable.

        On a log axis the binned variable is ``log10`` of the data, so the
        widths are log10 widths and a density normalised by them integrates
        to 1 over the log axis.

        Parameters
        ----------
        bins : array-like of pd.Interval
            The bins, e.g. an ``IntervalIndex`` or a categorical index of
            intervals.

        Returns
        -------
        pd.Series
            Each bin's width, indexed by ``bins``.
        """
        return pd.Series(pd.IntervalIndex(bins).length, index=bins)

    def set_clim(self, lower=None, upper=None):
        """Set the minimum (lower) and maximum (upper) allowed number of.

        counts per bin to return after calling :py:meth:`agg`.
        """
        assert isinstance(lower, Number) or lower is None
        assert isinstance(upper, Number) or upper is None
        self._clim = (lower, upper)

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
            Decimal places to which bin edges are rounded. If None, 5.

        Notes
        -----
        Edges from an integer ``nbins`` follow :func:`numpy.histogram`: the
        outer edges are rounded outward so they enclose every sample, and each
        bin is closed on the left, the last bin also on the right. Other
        ``nbins`` give right-closed bins, ``(a, b]``.
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

            # Edges from an integer bin count follow `np.histogram`'s convention.
            from_count = isinstance(b, Integral) and not isinstance(b, bool)

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

            closed = "right"
            if from_count:
                # Round the outer edges outward so they enclose every sample.
                scale = 10.0**precision
                lo = np.floor(b[0] * scale) / scale
                hi = np.ceil(b[-1] * scale) / scale
                b = b.round(precision)
                b[0] = lo if lo <= d.min() else lo - 1 / scale
                b[-1] = hi if hi >= d.max() else hi + 1 / scale
                closed = "left"
            else:
                b = b.round(precision)

            zipped = zip(b[:-1], b[1:])
            i = [pd.Interval(*b0b1, closed=closed) for b0b1 in zipped]

            bins[k] = b
            intervals[k] = pd.CategoricalIndex(i)

        bins = tuple(bins.items())
        intervals = tuple(intervals.items())
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
            if i.closed == "left":
                # As in `np.histogram`, the last bin also holds its right edge.
                c[d == i[-1].right] = i[-1]
            cut[k] = c

        cut = pd.DataFrame.from_dict(cut, orient="columns")
        self._cut = cut

    def _agg_reindexer(self, agg):
        # `self.grouped` uses `observed=True`: `observed=False` raised a TypeError
        # with mixed Categoricals and NaNs. (20200229)
        # Ensure all bins are represented in the data. (20190605)
        for k, v in self.categoricals.items():
            # if > 1 intervals, pass level. Otherwise, don't as this raises a NotImplementedError. (20190619)
            # Name the bins so a 1-D result keeps its axis name, e.g. "x".
            agg = agg.reindex(
                index=v.rename(k), level=k if agg.index.nlevels > 1 else None
            )

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
            if c0 is not None:
                tk = tk & (cnt >= c0)
            if c1 is not None:
                tk = tk & (cnt <= c1)

            agg = agg.where(tk)

        return agg

    def _joint_bin_mask(self, kept):
        r"""Boolean ``pd.Series`` marking each observation whose joint bin is kept.

        Parameters
        ----------
        kept : pd.Index or pd.MultiIndex
            Aggregated bins to keep, with one named level per column of ``cut``.

        Returns
        -------
        pd.Series
            True where the observation's bin across every column of ``cut``
            (e.g. the joint (x, y) bin in 2-D) is in ``kept``.
        """
        cut = self.cut
        observed = []
        selected = []
        for k, v in cut.items():
            # Compare category codes: the Categoricals fail with some pandas numpy
            # ufuncs (20200611), and both sides are coded by the same categories.
            categories = v.cat.categories
            observed.append(v.cat.codes.to_numpy())
            selected.append(categories.get_indexer(kept.get_level_values(k)))

        observed = pd.MultiIndex.from_arrays(observed)
        selected = pd.MultiIndex.from_arrays(selected)
        return pd.Series(observed.isin(selected), index=cut.index)

    def get_plotted_data_boolean_series(self):
        """Return a boolean ``pd.Series`` identifying each plotted measurement.

        A measurement is plotted when its joint bin (e.g. its (x, y) bin in 2-D)
        survives aggregation. The series shares the same index as the stored
        data. To align with a different index you may need to adjust the
        returned series.
        """
        agg = self.agg().dropna()
        tk = self._joint_bin_mask(agg.index)

        self.logger.info(
            f"Taking {tk.sum()!s} ({100 * tk.mean():.1f}%) {self.__class__.__name__} spectra"
        )

        return tk

    def get_subset_above_threshold(self, threshold, fcn="count"):
        r"""Get the subset of data above a given threshold using `fcn` to.

        aggregate. If `axnorm` set, this is used. A row is kept when its joint
        bin (e.g. its (x, y) bin in 2-D) meets `threshold`.
        """
        agg = self.agg(fcn=fcn)
        tk = agg >= threshold
        tk = tk.loc[tk]

        tk_h2 = self._joint_bin_mask(tk.index)

        subset = self.data.loc[tk_h2].copy(deep=True)
        for k, log in self.log._asdict().items():
            if log:
                subset.loc[:, k] = 10 ** subset.loc[:, k]

        return subset, tk_h2

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
