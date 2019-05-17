#!/usr/bin/env python
r"""Aggregate, create, and save 1D and 2D plots.
"""

import pdb  # noqa: F401
import logging

import numpy as np
import pandas as pd
import matplotlib as mpl

from matplotlib import pyplot as plt
from numbers import Number
from abc import abstractproperty
from pathlib import Path

try:
    from astropy.stats import knuth_bin_width
except ModuleNotFoundError:
    pass

from . import tools
from . import base
from . import labels as labels_module


class AggPlot(base.Base):
    r"""ABC for aggregating data in 1D and 2D.

    Properties
    ----------
    logger, data, bins, clip, cut, logx, labels.x, labels.y, clim, agg_axes

    Methods
    -------
    set_<>:
        Set property <>.

    calc_bins, make_cut, agg, clip_data, make_plot

    Abstract Properties
    ---------_---------
    path, _agg_axes

    Abstract Methods
    ---------_------
    __init__, set_labels.y, set_path, set_data, _format_axis, make_plot
    """

    @property
    def edges(self):
        return {k: v.left.union(v.right) for k, v in self.intervals.items()}

    @property
    def intervals(self):
        return dict(self._intervals)

    @property
    def cut(self):
        return self._cut

    @property
    def clim(self):
        return self._clim

    @property
    def agg_axes(self):
        tko = [c for c in self.data.columns if c not in self._agg_axes]
        assert len(tko) == 1
        tko = tko[0]
        return tko

    @property
    def joint(self):
        r"""A combination of the categorical and continuous data for use in `Groupby`.
        """
        cut = self.cut
        tko = self.agg_axes

        self.logger.info("""Joining data (%s) with cat (%s)""", tko, cut.columns.values)

        other = self.data.loc[cut.index, tko]

        joint = cut.copy(deep=True)
        joint.loc[:, other.name] = other
        joint.sort_index(axis=1, inplace=True)

        return joint

    @property
    def grouped(self):
        r"""`joint.groupby` with appropriate axes passes.
        """
        gb = self.joint.groupby(list(self._agg_axes))
        return gb

    @property
    def clip(self):
        return self._clip

    def set_clim(self, bottom, top):
        assert isinstance(bottom, Number) or bottom is None
        assert isinstance(top, Number) or top is None
        self._clim = (bottom, top)

    def calc_bins_intervals(self, nbins=101, precision=None):
        r"""
        Calculate histogram bins.

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
            precision = 3

        agg_axes = self._agg_axes

        if isinstance(nbins, (str, int)) or (
            hasattr(nbins, "__iter__") and len(nbins) != len(agg_axes)
        ):
            # Single paramter for `nbins`.
            nbins = {k: nbins for k in agg_axes}

        elif len(nbins) == len(agg_axes):
            # Passed one bin spec per axis
            nbins = {k: v for k, v in zip(agg_axes, nbins)}

        else:
            msg = "Unrecognized `nbins`\ntype: {}\n bins:{}"
            raise ValueError(msg.format(type(nbins), nbins))

        for k in self._agg_axes:
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
            assert not np.isnan(b).any()

            b = b.round(precision)

            zipped = zip(b[:-1], b[1:])
            i = [pd.Interval(*b0b1, closed="right") for b0b1 in zipped]

            bins[k] = b
            intervals[k] = pd.IntervalIndex(i)

        bins = tuple(bins.items())
        intervals = tuple(intervals.items())
        self._intervals = intervals

    def make_cut(self):
        r"""Calculate the `Categorical` quantities for the aggregation axes.
        """
        intervals = self.intervals
        data = self.data

        cut = {}
        for k in self._agg_axes:
            d = data.loc[:, k]
            i = intervals[k]

            if self.clip:
                d = self.clip_data(d, self.clip)

            c = pd.cut(d, i)
            cut[k] = c

        cut = pd.DataFrame.from_dict(cut, orient="columns")
        self._cut = cut

    def agg(self, fcn=None):
        r"""Perform the aggregation along the agg axes.

        If either of the count limits specified in `clim` are not None, apply them.

        `fcn` allows you to specify a specific function for aggregation. Otherwise,
        automatically choose "count" or "mean" based on the uniqueness of the aggregated
        values.
        """

        cut = self.cut
        tko = self.agg_axes

        self.logger.info("""aggregating %s data along %s""", tko, cut.columns.values)

        gb = self.grouped

        if fcn is None:
            other = self.data.loc[cut.index, tko]
            if other.dropna().unique().size == 1:
                fcn = "count"
            else:
                fcn = "mean"

        agg = gb.agg(fcn).loc[:, tko]

        c0, c1 = self.clim
        if c0 is not None or c1 is not None:
            cnt = gb.agg("count").loc[:, tko]
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

        return agg

    # Old version that cuts at percentiles.
    @staticmethod
    def clip_data(data, clip):
        q0 = 0.001
        q1 = 0.999
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

    @abstractproperty
    def _agg_axes(self):
        r"""The axes over which the aggregation takes place.

        1D cases aggregate over `x`. 2D cases aggregate over `x` and `y`.
        """
        pass


class Hist1D(AggPlot):
    r"""Create 1D plot of `x`, optionally aggregating `y` in bins of `x`.

    Properties
    ----------
    _agg_axes, path

    Methods
    -------
    set_path, set_data, agg, _format_axis, make_plot
    """

    def __init__(
        self, x, y=None, logx=False, clip_data=False, nbins=101, bin_precision=None
    ):
        r"""
        Parameters
        ----------
        x: pd.Series
            Data from which to create bins.
        y: pd.Series, None
            If not None, the values to aggregate in bins of `x`. If None,
            aggregate counts of `x`.
        logx: bool
            If True, compute bins in log-space.
        clip_data: bool
            If True, remove the extreme values at 0.001 and 0.999 percentiles
            before calculating bins or aggregating.
        nbins: int, str, array-like
            Dispatched to `np.histogram_bin_edges` or `pd.cut` depending on
            input type and value.
        """
        super(Hist1D, self).__init__()
        self.set_data(x, y, logx, clip_data)
        self.calc_bins_intervals(nbins=nbins, precision=bin_precision)
        self.make_cut()
        self._labels = base.AxesLabels(
            x="x", y=labels_module.Count() if y is None else "y"
        )
        self.set_path(None)
        self.set_clim(None, None)

    @property
    def _agg_axes(self):
        return ("x",)

    def set_path(self, new, add_scale=True):
        path, x, y, z, scale_info = super(Hist1D, self).set_path(new, add_scale)

        if new == "auto":

            #             n_unique_y = self.data.loc[:, "y"].dropna().unique().size

            #             if (y == "y") and (n_unique_y == 1):
            #                 y = "count"

            #             elif n_unique_y > 1:
            #                 # Expect aggregating data.
            #                 pass

            #             else:
            #                 raise ValueError("Unable to auto set y-component of path")

            path = path / x / y

        else:
            assert x is None
            assert y is None

        if add_scale:
            assert scale_info is not None
            scale_info = scale_info[0]
            path = path / scale_info

        self._path = path

    set_path.__doc__ = base.Base.set_path.__doc__

    def set_data(self, x, y, logx, clip):
        logx = bool(logx)
        #         if logx:
        #             x = np.abs(x)
        #             x = np.log10(x[x > 0])
        data = pd.DataFrame({"x": np.log10(np.abs(x)) if logx else x})

        #         if clip:
        #             data = self.clip_data(data, clip)

        if y is None:
            y = pd.Series(1, index=x.index)
        data.loc[:, "y"] = y

        self._data = data
        self._log = base.LogAxes(x=logx)
        self._clip = clip

    def agg(self, **kwargs):
        intervals = self.intervals["x"]
        agg = super(Hist1D, self).agg(**kwargs)
        agg = agg.reindex(intervals)
        return agg

    def _format_axis(self, ax):
        xlbl = self.labels.x
        if xlbl is not None:
            ax.set_xlabel(xlbl)

        ylbl = self.labels.y
        if ylbl is not None:
            ax.set_ylabel(ylbl)

        if self.log.x:
            ax.set_xscale("log")

        ax.grid(True, which="major", axis="both")

    def make_plot(self, ax=None, **kwargs):
        r"""Make a plot on `ax`.

        If `ax` is None, create a `mpl.subplots` axis.

        `**kwargs` passed directly to `ax.plot`.

        `drawstyle` defaults to `steps-mid`.
        """
        agg = self.agg()
        #         tko = self.agg_axes
        x = pd.IntervalIndex(agg.index).mid
        y = agg

        if ax is None:
            fig, ax = plt.subplots()

        if self.log.x:
            x = 10.0 ** x

        drawstyle = kwargs.pop("drawstyle", "steps-mid")
        ax.plot(x, y, drawstyle=drawstyle, **kwargs)

        self._format_axis(ax)

        return ax


class Hist2D(AggPlot):
    r"""Create a 2D histogram with an optional z-value using an equal number
    of bins along the x and y axis.

    Parameters
    ----------
    x, y: pd.Series
        x and y data to aggregate
    z: None, pd.Series
        If not None, the z-value to aggregate.
    axnorm: str
        Normalize the histogram.
            key  normalization
            ---  -------------
            c    column
            r    row
            t    total
            d    density
    logx, logy: bool
        If True, log10 scale the axis.

    Properties
    ----------
    data:
    bins:
    cut:
    axnorm:
    log<x,y>:
    <x,y,z>label:
    path: None, Path

    Methods
    -------
    calc_bins:
        calculate the x, y bins.
    make_cut:
        Utilize the calculated bins to convert (x, y) into pd.Categoral
        or pd.Interval values used in aggregation.
    set_[x,y,z]label:
        Set the x, y, or z label.
    agg:
        Aggregate the data in the bins.
        If z-value is None, count the number of points in each bin.
        If z-value is not None, calculate the mean for each bin.
    make_plot:
        Make a 2D plot of the data with an optional color bar.
    """

    def __init__(
        self,
        x,
        y,
        z=None,
        axnorm=None,
        logx=False,
        logy=False,
        clip_data=False,
        nbins=101,
        bin_precision=None,
    ):
        super(Hist2D, self).__init__()
        self.set_data(x, y, z, logx, logy, clip_data)
        self._labels = base.AxesLabels(
            x="x", y="y", z=labels_module.Count(norm=axnorm) if z is None else "z"
        )
        self.set_axnorm(axnorm)
        self.calc_bins_intervals(nbins=nbins, precision=bin_precision)
        self.make_cut()
        self.set_path(None)
        self.set_clim(None, None)

    @property
    def _agg_axes(self):
        return ("x", "y")

    @property
    def axnorm(self):
        r"""Data normalization in plot.

        Not `mpl.colors.Normalize` instance. That is passed as a `kwarg` to
        `make_plot`.
        """
        return self._axnorm

    def set_path(self, new, add_scale=True):
        # Bug: path doesn't auto-set log information.
        path, x, y, z, scale_info = super(Hist2D, self).set_path(new, add_scale)

        if new == "auto":

            #             n_unique_z = self.data.loc[:, "z"].unique().size

            #             if (z == "z") and (n_unique_z == 1):
            #                 z = "count"

            #             elif n_unique_z > 1:
            #                 # Expect aggregating data.
            #                 pass

            #             else:
            #                 raise ValueError("Unable to auto set z-component of path")

            path = path / x / y / z

        else:
            assert x is None
            assert y is None
            assert z is None

        if add_scale:
            assert scale_info is not None

            #             axnorm = self.axnorm
            #             if axnorm is not None:
            #                 axnorm = axnorm.capitalize() + "norm"
            #                 scale_info = scale_info
            scale_info = "-".join(scale_info)

            if bool(len(path.parts)) and path.parts[-1].endswith("norm"):
                # Insert <norm> at end of path so scale order is (x, y, z).
                path = path.parts
                path = path[:-1] + (scale_info + "-" + path[-1],)
                path = Path(*path)
            else:
                path = path / scale_info

        self._path = path

    set_path.__doc__ = base.Base.set_path.__doc__

    def set_labels(self, **kwargs):

        z = kwargs.pop("z", self.labels.z)
        if isinstance(z, labels_module.Count):
            z.set_axnorm(self.axnorm)
            z.build_label()

        super(Hist2D, self).set_labels(z=z, **kwargs)

    #     def _add_meta_to_zlbl(self, zlbl):
    #         # BUG: path's won't auto create if they are strings.
    #         axnorm = self.axnorm
    #         if axnorm == "c":
    #             prefix = "Col."
    #         elif axnorm == "d":
    #             prefix = "Density"
    #         elif axnorm == "r":
    #             prefix = "Row"
    #         elif axnorm == "t":
    #             prefix = "Total"
    #         else:
    #             prefix = ""

    #         if zlbl is not None:
    #             fmt = r"$\mathrm{%s \; Norm.} \; %s \; [\#]$"
    #             if prefix:
    #                 try:
    #                     zlbl = fmt % (prefix, zlbl.tex)
    #                 except AttributeError:
    #                     zlbl = fmt % (prefix, r"\mathrm{" + zlbl + "}")

    #         elif self.data.loc[:, "z"].dropna().unique().size == 1:
    #             if prefix:
    #                 zlbl = r"$\mathrm{%s \; Norm. \; Count} \; [\#]$" % prefix
    #             else:
    #                 zlbl = r"$\mathrm{Count} \; [\#]$"

    #         return zlbl

    def set_data(self, x, y, z, logx, logy, clip):
        logx = bool(logx)
        logy = bool(logy)
        data = pd.DataFrame(
            {
                "x": np.log10(np.abs(x)) if logx else x,
                "y": np.log10(np.abs(y)) if logy else y,
            }
        )

        #         if clip:
        #             data = self.clip_data(data, clip)

        if z is None:
            z = pd.Series(1, index=x.index)

        data.loc[:, "z"] = z

        data = data.dropna()
        if not data.shape[0]:
            raise ValueError(
                "You can't build a %s with data that is exclusively NaNs"
                % self.__class__.__name__
            )

        self._data = data
        self._log = base.LogAxes(x=logx, y=logy)
        self._clip = clip

    def set_axnorm(self, new):
        r"""The method by which the gridded data is normalized.

===== =============================================================
 key                           description
===== =============================================================
 c     Column normalize
 d     Density normalize.
 r     Row normalize
 t     Total normalize
===== =============================================================
"""
        if new is not None:
            new = new.lower()[0]
            assert new in ("c", "r", "t", "d")

        zlbl = self.labels.z
        if isinstance(zlbl, labels_module.Count):
            zlbl.set_axnorm(new)
            zlbl.build_label()

        self._axnorm = new

    def agg(self, **kwargs):
        agg = super(Hist2D, self).agg(**kwargs)  # .unstack("x")

        axnorm = self.axnorm
        if axnorm is None:
            pass
        elif axnorm == "c":
            agg = agg.divide(agg.max(level="x"), level="x")
        elif axnorm == "r":
            agg = agg.divide(agg.max(level="y"), level="y")
        elif axnorm == "t":
            agg = agg.divide(agg.max())
        elif axnorm == "d":
            N = agg.sum().sum()
            x = pd.IntervalIndex(agg.index.get_level_values("x").unique())
            y = pd.IntervalIndex(agg.index.get_level_values("y").unique())
            dx = pd.Series(x.right - x.left, index=x)
            dy = pd.Series(y.right - y.left, index=y)
            if self.log.x:
                dx = 10.0 ** dx
            if self.log.y:
                dy = 10.0 ** dy

            agg = agg.divide(dx, level="x").divide(dy, level="y").divide(N)

        else:
            raise ValueError("Unrecognized axnorm: %s" % axnorm)

        agg = agg.unstack("x")
        intervals = self.intervals

        agg = agg.reindex(index=intervals["y"], columns=intervals["x"])

        return agg

    def _format_axis(self, ax):
        xlbl = self.labels.x
        ylbl = self.labels.y

        if xlbl is not None:
            ax.set_xlabel(xlbl)
        if ylbl is not None:
            ax.set_ylabel(ylbl)

        if self.log.x:
            ax.set_xscale("log")
        if self.log.y:
            ax.set_yscale("log")

        ax.grid(True, which="major", axis="both")

    def _make_cbar(self, mappable, ax, **kwargs):
        label = kwargs.pop("label", self.labels.z)
        cbar = ax.figure.colorbar(mappable, ax=ax, label=label, **kwargs)
        return cbar

    def _limit_color_norm(self, norm):
        if self.axnorm in ("c", "r"):
            # Don't limit us to (1%, 99%) interval.
            return None

        pct = self.data.loc[:, "z"].quantile([0.01, 0.99])
        v0 = pct.loc[0.01]
        v1 = pct.loc[0.99]
        if norm.vmin is None:
            norm.vmin = v0
        if norm.vmax is None:
            norm.vmax = v1
        norm.clip = True

    def make_plot(
        self, ax=None, cbar=True, limit_color_norm=False, cbar_kwargs=None, **kwargs
    ):
        r"""
        Make a 2D plot on `ax` using `ax.pcolormesh`.

        Paremeters
        ----------
        ax: mpl.axes.Axes, None
            If None, create an `Axes` instance from `plt.subplots`.
        cbar: bool
            If True, create color bar with `labels.z`.
        limit_color_norm: bool
            If True, limit the color range to 0.001 and 0.999 percentile range
            of the z-value, count or otherwise.
        cbar_kwargs: dict, None
            If not None, kwargs passed to `self._make_cbar`.
        kwargs:
            Passed to `ax.pcolormesh`.
            If row or column normalized data, `norm` defaults to `mpl.colors.Normalize(0, 1)`.
        """
        agg = self.agg()
        x = self.edges["x"]
        y = self.edges["y"]

        assert x.size == agg.shape[1] + 1
        assert y.size == agg.shape[0] + 1

        if ax is None:
            fig, ax = plt.subplots()

        if self.log.x:
            x = 10.0 ** x
        if self.log.y:
            y = 10.0 ** y

        axnorm = self.axnorm
        norm = kwargs.pop(
            "norm", mpl.colors.Normalize(0, 1) if axnorm in ("c", "r") else None
        )

        if limit_color_norm:
            self._limit_color_norm(norm)

        C = np.ma.masked_invalid(agg.values)
        XX, YY = np.meshgrid(x, y)
        pc = ax.pcolormesh(XX, YY, C, norm=norm, **kwargs)

        if cbar:
            if cbar_kwargs is None:
                cbar_kwargs = dict()
            cbar = self._make_cbar(pc, ax, **cbar_kwargs)

        self._format_axis(ax)

        return ax, cbar

    def project_1d(self, axis, **kwargs):
        r"""Make a `Hist1D` from the data stored in this `His2D`.

        Parameters
        ----------
        axis: str
            "x" or "y", specifying the axis to project into 1D.
        kwargs:
            Passed to `Hist1D`. Primarily to allow specifying `bin_precision`.

        Returns
        -------
        h1: `Hist1D`
        """
        axis = axis.lower()
        assert axis in ("x", "y")
        h1 = Hist1D(
            self.data[axis],
            y=self.data["z"],
            logx=self.log._asdict()[axis],
            clip_data=False,  # Any clipping will be addressed by bins.
            nbins=self.edges[axis].values,
        )
        h1.set_labels(x=self.labels._asdict()[axis], y=self.labels._asdict()["z"])

        return h1


class GridHist2D(object):
    r"""A grid of 2D heatmaps separating the data based on a categorical value.

    Properties
    ----------
    data: pd.DataFrame

    axnorm: str or None
        Specify if column, row, total, or density normalization should be used.
    log: namedtuple
        Contains booleans identifying axes to log-scale.
    nbins: int or str
        Pass to `np.histogram_bin_edges` or `astropy.stats.knuth_bin_width`
        depending on the input.
    labels: namedtuple
        Contains axis labels. Recomend using `labels.TeXlabel` so
    grouped: pd.Groupeby
        The data grouped by the categorical.
    hist2ds: pd.Series
        The `Hist2D` objects created for each axis. Index is the unique
        categorical values.
    fig: mpl.figure.Figure
        The figure upon which the axes are placed.
    axes: pd.Series
        Contains the mpl axes upon which plots are drawn. Index should be
        identical to `hist2ds`.
    cbars: pd.Series
        Contains the colorbar instances. Similar to `hist2ds` and `axes`.
    cnorms: mpl.color.Normalize or pd.Series
        mpl.colors.Normalize instance or a pd.Series of them with one for
        each unique categorical value.
    use_gs: bool
        An attempt at the code is written, but not implemented because some
        minor details need to be worked out. Ideally, if True, use a single
        colorbar for the entire grid.

    Methods
    -------
    set_<>: setters
        For data, nbins, axnorm, log, labels, cnorms.
    make_h2ds:
        Make the `Hist2D` objects.
    make_plots:
        Make the `Hist2D` plots.
    """

    def __init__(self, x, y, cat, z=None):
        r"""Create 2D heatmaps of x, y, and optional z data in a grid for which
        each unique element in `cat` specifies one plot.

        Parameters
        ----------
        x, y, z: pd.Series or np.array
            The data to aggregate. pd.Series is prefered.
        cat: pd.Categorial
            The categorial series used to create subsets of the data for each
            grid element.

        """
        self.set_nbins(101)
        self.set_axnorm(None)
        self.set_log(x=False, y=False)
        self.set_data(x, y, cat, z)
        self._labels = base.AxesLabels("x", "y")  # Unsure how else to set defaults.
        self.set_cnorms(None)

    @property
    def data(self):
        return self._data

    @property
    def axnorm(self):
        r"""Axis normalization."""
        return self._axnorm

    @property
    def logger(self):
        return self._log

    @property
    def nbins(self):
        return self._nbins

    @property
    def log(self):
        r"""LogAxes booleans.
        """
        return self._log

    @property
    def labels(self):
        return self._labels

    @property
    def grouped(self):
        return self.data.groupby("cat")

    @property
    def hist2ds(self):
        try:
            return self._h2ds
        except AttributeError:
            return self.make_h2ds()

    @property
    def fig(self):
        try:
            return self._fig
        except AttributeError:
            return self.init_fig()[0]

    @property
    def axes(self):
        try:
            return self._axes
        except AttributeError:
            return self.init_fig()[1]

    @property
    def cbars(self):
        return self._cbars

    @property
    def cnorms(self):
        r"""Color normalization (mpl.colors.Normalize instance)."""
        return self._cnorms

    @property
    def use_gs(self):
        return self._use_gs

    @property
    def path(self):
        raise NotImplementedError("Just haven't sat down to write this.")

    def _init_logger(self):
        self._logger = logging.getLogger(
            "{}.{}".format(__name__, self.__class__.__name__)
        )

    def set_nbins(self, new):
        self._nbins = new

    def set_axnorm(self, new):
        self._axnorm = new

    def set_cnorms(self, new):
        self._cnorms = new

    def set_log(self, x=None, y=None):
        if x is None:
            x = self.log.x
        if y is None:
            y = self.log.y
        log = base.LogAxes(x, y)
        self._log = log

    def set_data(self, x, y, cat, z):
        data = {"x": x, "y": y, "cat": cat}
        if z is not None:
            data["z"] = z
        data = pd.concat(data, axis=1)
        self._data = data

    def set_labels(self, **kwargs):
        r"""Set or update x, y, or z labels. Any label not specified in kwargs
        is propagated from `self.labels.<x, y, or z>`.
        """

        x = kwargs.pop("x", self.labels.x)
        y = kwargs.pop("y", self.labels.y)
        z = kwargs.pop("z", self.labels.z)

        if len(kwargs.keys()):
            raise KeyError("Unexpected kwarg: {}".format(kwargs.keys()))

        self._labels = base.AxesLabels(x, y, z)

    def set_fig_axes(self, fig, axes, use_gs=False):
        self._set_fig(fig)
        self._set_axes(axes)
        self._use_gs = bool(use_gs)

    def _set_fig(self, new):
        self._fig = new

    def _set_axes(self, new):
        if new.size != len(self.grouped.groups.keys()) + 1:
            msg = "Number of axes must match number of Categoricals + 1 for All."
            raise ValueError(msg)

        keys = ["All"] + sorted(self.grouped.groups.keys())
        axes = pd.Series(new.ravel(), index=pd.CategoricalIndex(keys))

        self._axes = axes

    def init_fig(self, use_gs=False, layout="auto", scale=1.5):

        if layout == "auto":
            raise NotImplementedError(
                """Need some densest packing algorithm I haven't
found yet"""
            )

        assert len(layout) == 2
        nrows, ncols = layout

        if use_gs:
            raise NotImplementedError(
                """Unsure how to consistently store single cax or
deal with variable layouts."""
            )
            fig = plt.figure(figsize=np.array([8, 6]) * scale)

            gs = mpl.gridspec.GridSpec(
                3,
                5,
                width_ratios=[1, 1, 1, 1, 0.1],
                height_ratios=[1, 1, 1],
                hspace=0,
                wspace=0,
                figure=fig,
            )

            axes = np.array(12 * [np.nan], dtype=object).reshape(3, 4)
            sharer = None
            for i in np.arange(0, 3):
                for j in np.arange(0, 4):
                    if i and j:
                        a = plt.subplot(gs[i, j], sharex=sharer, sharey=sharer)
                    else:
                        a = plt.subplot(gs[i, j])
                        sharer = a
                    axes[i, j] = a

            others = axes.ravel().tolist()
            a0 = others.pop(8)
            a0.get_shared_x_axes().join(a0, *others)
            a0.get_shared_y_axes().join(a0, *others)

            for ax in axes[:-1, 1:].ravel():
                # All off
                ax.tick_params(labelbottom=False, labelleft=False)
                ax.xaxis.label.set_visible(False)
                ax.yaxis.label.set_visible(False)
            for ax in axes[:-1, 0].ravel():
                # 0th column x-labels off.
                ax.tick_params(which="x", labelbottom=False)
                ax.xaxis.label.set_visible(False)
            for ax in axes[-1, 1:].ravel():
                # Nth row y-labels off.
                ax.tick_params(which="y", labelleft=False)
                ax.yaxis.label.set_visible(False)

        #             cax = plt.subplot(gs[:, -1])

        else:
            fig, axes = tools.subplots(
                nrows=nrows, ncols=ncols, scale_width=scale, scale_height=scale
            )
        #             cax = None

        self.set_fig_axes(fig, axes, use_gs)
        return fig, axes

    def _build_one_hist2d(self, x, y, z):
        h2d = Hist2D(
            x,
            y,
            z=z,
            logx=self.log.x,
            logy=self.log.y,
            clip_data=False,
            nbins=self.nbins,
        )
        h2d.set_axnorm(self.axnorm)

        xlbl, ylbl, zlbl = self.labels.x, self.labels.y, self.labels.z
        h2d.set_labels(x=xlbl, y=ylbl, z=zlbl)

        return h2d

    def make_h2ds(self):
        grouped = self.grouped

        # Build case that doesn't include subgroups.

        x = self.data.loc[:, "x"]
        y = self.data.loc[:, "y"]
        try:
            z = self.data.loc[:, "z"]
        except KeyError:
            z = None

        hall = self._build_one_hist2d(x, y, z)

        h2ds = {"All": hall}
        for k, g in grouped:
            x = g.loc[:, "x"]
            y = g.loc[:, "y"]
            try:
                z = g.loc[:, "z"]
            except KeyError:
                z = None

            h2ds[k] = self._build_one_hist2d(x, y, z)

        h2ds = pd.Series(h2ds)
        self._h2ds = h2ds
        return h2ds

    @staticmethod
    def _make_axis_text_label(key):
        r"""Format the `key` identifying the Categorial group for this axis. To modify,
sublcass `GridHist2D` and redefine this staticmethod.
"""
        return key

    def _format_axes(self):
        axes = self.axes
        for k, ax in axes.items():
            lbl = self._make_axis_text_label(k)
            ax.text(
                0.025,
                0.95,
                lbl,
                transform=ax.transAxes,
                va="top",
                fontdict={"color": "k"},
                bbox={"color": "wheat"},
            )

        # ax.set_xlim(-1, 1)
        # ax.set_ylim(-1, 1)

    def make_plots(self, **kwargs):
        h2ds = self.hist2ds
        axes = self.axes

        cbars = {}
        cnorms = self.cnorms
        for k, h2d in h2ds.items():
            if isinstance(cnorms, mpl.colors.Normalize) or cnorms is None:
                cnorm = cnorms
            else:
                cnorm = cnorms.loc[k]

            ax = axes.loc[k]
            ax, cbar = h2d.make_plot(ax=ax, norm=cnorm, **kwargs)
            if not self.use_gs:
                cbars[k] = cbar
            else:
                raise NotImplementedError(
                    "Unsure how to handle `use_gs == True` for color bars."
                )
        cbars = pd.Series(cbars)

        self._format_axes()
        self._cbars = cbars
