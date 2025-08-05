#!/usr/bin/env python
r"""Convenience accessors for histogram style plotters.

This module re-exports :class:`AggPlot`, :class:`Hist1D`, and
:class:`Hist2D` so they can be imported directly from
:mod:`solarwindpy.plotting.histograms`.
"""

from . import agg_plot
from . import hist1d
from . import hist2d

AggPlot = agg_plot.AggPlot
Hist1D = hist1d.Hist1D
Hist2D = hist2d.Hist2D

# import pdb  # noqa: F401
# import logging

# import numpy as np
# import pandas as pd
# import matplotlib as mpl

# from types import FunctionType
# from numbers import Number
# from matplotlib import pyplot as plt
# from abc import abstractproperty, abstractmethod
# from collections import namedtuple
# from scipy.signal import savgol_filter

# try:
#     from astropy.stats import knuth_bin_width
# except ModuleNotFoundError:
#     pass

# from . import tools
# from . import base
# from . import labels as labels_module

# # import os
# # import psutil


# # def log_mem_usage():
# #    usage = psutil.Process(os.getpid()).memory_info()
# #    usage = "\n".join(
# #        ["{} {:.3f} GB".format(k, v * 1e-9) for k, v in usage._asdict().items()]
# #    )
# #    logging.getLogger("main").warning("Memory usage\n%s", usage)


# class AggPlot(base.Base):
#     r"""ABC for aggregating data in 1D and 2D.

#     Properties
#     ----------
#     logger, data, bins, clip, cut, logx, labels.x, labels.y, clim, agg_axes

#     Methods
#     -------
#     set_<>:
#         Set property <>.

#     calc_bins, make_cut, agg, clip_data, make_plot

#     Abstract Properties
#     -------------------
#     path, _gb_axes

#     Abstract Methods
#     ----------------
#     __init__, set_labels.y, set_path, set_data, _format_axis, make_plot
#     """

#     @property
#     def edges(self):
#         return {k: v.left.union(v.right) for k, v in self.intervals.items()}

#     @property
#     def categoricals(self):
#         return dict(self._categoricals)

#     @property
#     def intervals(self):
#         #         return dict(self._intervals)
#         return {k: pd.IntervalIndex(v) for k, v in self.categoricals.items()}

#     @property
#     def cut(self):
#         return self._cut

#     @property
#     def clim(self):
#         return self._clim

#     @property
#     def agg_axes(self):
#         r"""The axis to aggregate into, e.g. the z variable in an (x, y, z) heatmap.
#         """
#         tko = [c for c in self.data.columns if c not in self._gb_axes]
#         assert len(tko) == 1
#         tko = tko[0]
#         return tko

#     @property
#     def joint(self):
#         r"""A combination of the categorical and continuous data for use in `Groupby`.
#         """
#         #         cut = self.cut
#         #         tko = self.agg_axes

#         #         self.logger.debug(f"Joining data ({tko}) with cat ({cut.columns.values})")

#         #         other = self.data.loc[cut.index, tko]

#         #         #         joint = pd.concat([cut, other.to_frame(name=tko)], axis=1, sort=True)
#         #         joint = cut.copy(deep=True)
#         #         joint.loc[:, tko] = other
#         #         joint.sort_index(axis=1, inplace=True)
#         #         return joint

#         cut = self.cut
#         tk_target = self.agg_axes
#         target = self.data.loc[cut.index, tk_target]

#         mi = pd.MultiIndex.from_frame(cut)
#         target.index = mi

#         return target

#     @property
#     def grouped(self):
#         r"""`joint.groupby` with appropriate axes passes.
#         """
#         #         tko = self.agg_axes
#         #         gb = self.data.loc[:, tko].groupby([v for k, v in self.cut.items()], observed=False)
#         #         gb = self.joint.groupby(list(self._gb_axes))

#         #         cut = self.cut
#         #         tk_target = self.agg_axes
#         #         target = self.data.loc[cut.index, tk_target]

#         #         mi = pd.MultiIndex.from_frame(cut)
#         #         target.index = mi

#         target = self.joint
#         gb_axes = list(self._gb_axes)
#         gb = target.groupby(gb_axes, axis=0, observed=True)

#         #         agg_axes = self.agg_axes
#         #         gb = (
#         #             self.joint.set_index(gb_axes)
#         #             .loc[:, agg_axes]
#         #             .groupby(gb_axes, axis=0, observed=False)
#         #         )
#         return gb

#     @property
#     def axnorm(self):
#         r"""Data normalization in plot.

#         Not `mpl.colors.Normalize` instance. That is passed as a `kwarg` to
#         `make_plot`.
#         """
#         return self._axnorm

#     # Old version that cuts at percentiles.
#     @staticmethod
#     def clip_data(data, clip):
#         q0 = 0.0001
#         q1 = 0.9999
#         pct = data.quantile([q0, q1])
#         lo = pct.loc[q0]
#         up = pct.loc[q1]

#         if isinstance(data, pd.Series):
#             ax = 0
#         elif isinstance(data, pd.DataFrame):
#             ax = 1
#         else:
#             raise TypeError("Unexpected object %s" % type(data))

#         if isinstance(clip, str) and clip.lower()[0] == "l":
#             data = data.clip_lower(lo, axis=ax)
#         elif isinstance(clip, str) and clip.lower()[0] == "u":
#             data = data.clip_upper(up, axis=ax)
#         else:
#             data = data.clip(lo, up, axis=ax)
#         return data

#     # New version that uses binning to cut.
#     #     @staticmethod
#     #     def clip_data(data, bins, clip):
#     #         q0 = 0.001
#     #         q1 = 0.999
#     #         pct = data.quantile([q0, q1])
#     #         lo  = pct.loc[q0]
#     #         up  = pct.loc[q1]
#     #         lo = bins.iloc[0]
#     #         up = bins.iloc[-1]
#     #         if isinstance(clip, str) and clip.lower()[0] == "l":
#     #             data = data.clip_lower(lo)
#     #         elif isinstance(clip, str) and clip.lower()[0] == "u":
#     #             data = data.clip_upper(up)
#     #         else:
#     #             data = data.clip(lo, up)
#     #         return data

#     def set_clim(self, lower=None, upper=None):
#         f"""Set the minimum (lower) and maximum (upper) alowed number of
#         counts/bin to return aftter calling :py:meth:`{self.__class__.__name__}.add()`.
#         """
#         assert isinstance(lower, Number) or lower is None
#         assert isinstance(upper, Number) or upper is None
#         self._clim = (lower, upper)

#     def calc_bins_intervals(self, nbins=101, precision=None):
#         r"""
#         Calculate histogram bins.

#         nbins: int, str, array-like
#             If int, use np.histogram to calculate the bin edges.
#             If str and nbins == "knuth", use `astropy.stats.knuth_bin_width`
#             to calculate optimal bin widths.
#             If str and nbins != "knuth", use `np.histogram(data, bins=nbins)`
#             to calculate bins.
#             If array-like, treat as bins.

#         precision: int or None
#             Precision at which to store intervals. If None, default to 3.
#         """
#         data = self.data
#         bins = {}
#         intervals = {}

#         if precision is None:
#             precision = 5

#         gb_axes = self._gb_axes

#         if isinstance(nbins, (str, int)) or (
#             hasattr(nbins, "__iter__") and len(nbins) != len(gb_axes)
#         ):
#             # Single paramter for `nbins`.
#             nbins = {k: nbins for k in gb_axes}

#         elif len(nbins) == len(gb_axes):
#             # Passed one bin spec per axis
#             nbins = {k: v for k, v in zip(gb_axes, nbins)}

#         else:
#             msg = f"Unrecognized `nbins`\ntype: {type(nbins)}\n bins:{nbins}"
#             raise ValueError(msg)

#         for k in self._gb_axes:
#             b = nbins[k]
#             # Numpy and Astropy don't like NaNs when calculating bins.
#             # Infinities in bins (typically from log10(0)) also create problems.
#             d = data.loc[:, k].replace([-np.inf, np.inf], np.nan).dropna()

#             if isinstance(b, str):
#                 b = b.lower()

#             if isinstance(b, str) and b == "knuth":
#                 try:
#                     assert knuth_bin_width
#                 except NameError:
#                     raise NameError("Astropy is unavailable.")

#                 dx, b = knuth_bin_width(d, return_bins=True)

#             else:
#                 try:
#                     b = np.histogram_bin_edges(d, b)
#                 except MemoryError:
#                     # Clip the extremely large values and extremely small outliers.
#                     lo, up = d.quantile([0.0005, 0.9995])
#                     b = np.histogram_bin_edges(d.clip(lo, up), b)
#                 except AttributeError:
#                     c, b = np.histogram(d, b)

#             assert np.unique(b).size == b.size
#             try:
#                 assert not np.isnan(b).any()
#             except TypeError:
#                 assert not b.isna().any()

#             b = b.round(precision)

#             zipped = zip(b[:-1], b[1:])
#             i = [pd.Interval(*b0b1, closed="right") for b0b1 in zipped]

#             bins[k] = b
#             #             intervals[k] = pd.IntervalIndex(i)
#             intervals[k] = pd.CategoricalIndex(i)

#         bins = tuple(bins.items())
#         intervals = tuple(intervals.items())
#         #         self._intervals = intervals
#         self._categoricals = intervals

#     def make_cut(self):
#         r"""Calculate the `Categorical` quantities for the aggregation axes.
#         """
#         intervals = self.intervals
#         data = self.data

#         cut = {}
#         for k in self._gb_axes:
#             d = data.loc[:, k]
#             i = intervals[k]

#             if self.clip:
#                 d = self.clip_data(d, self.clip)

#             c = pd.cut(d, i)
#             cut[k] = c

#         cut = pd.DataFrame.from_dict(cut, orient="columns")
#         self._cut = cut

#     def _agg_runner(self, cut, tko, gb, fcn, **kwargs):
#         r"""Refactored out the actual doing of the aggregation so that :py:class:`OrbitPlot`
#         can aggregate (Inbound, Outbound, and Both).
#         """
#         self.logger.debug(f"aggregating {tko} data along {cut.columns.values}")

#         if fcn is None:
#             other = self.data.loc[cut.index, tko]
#             if other.dropna().unique().size == 1:
#                 fcn = "count"
#             else:
#                 fcn = "mean"

#         agg = gb.agg(fcn, **kwargs)  # .loc[:, tko]

#         c0, c1 = self.clim
#         if c0 is not None or c1 is not None:
#             cnt = gb.agg("count")  # .loc[:, tko]
#             tk = pd.Series(True, index=agg.index)
#             #             tk  = pd.DataFrame(True,
#             #                                index=agg.index,
#             #                                columns=agg.columns
#             #                               )
#             if c0 is not None:
#                 tk = tk & (cnt >= c0)
#             if c1 is not None:
#                 tk = tk & (cnt <= c1)

#             agg = agg.where(tk)

#         #         #         Using `observed=False` in `self.grouped` raised a TypeError because mixed Categoricals and np.nans. (20200229)
#         #         # Ensure all bins are represented in the data. (20190605)
#         # #         for k, v in self.intervals.items():
#         #         for k, v in self.categoricals.items():
#         #             # if > 1 intervals, pass level. Otherwise, don't as this raises a NotImplementedError. (20190619)
#         #             agg = agg.reindex(index=v, level=k if agg.index.nlevels > 1 else None)

#         return agg

#     def _agg_reindexer(self, agg):
#         #         Using `observed=False` in `self.grouped` raised a TypeError because mixed Categoricals and np.nans. (20200229)
#         # Ensure all bins are represented in the data. (20190605)
#         #         for k, v in self.intervals.items():
#         for k, v in self.categoricals.items():
#             # if > 1 intervals, pass level. Otherwise, don't as this raises a NotImplementedError. (20190619)
#             agg = agg.reindex(index=v, level=k if agg.index.nlevels > 1 else None)

#         return agg

#     def agg(self, fcn=None, **kwargs):
#         r"""Perform the aggregation along the agg axes.

#         If either of the count limits specified in `clim` are not None, apply them.

#         `fcn` allows you to specify a specific function for aggregation. Otherwise,
#         automatically choose "count" or "mean" based on the uniqueness of the aggregated
#         values.
#         """
#         cut = self.cut
#         tko = self.agg_axes

#         self.logger.info(
#             f"Starting {self.__class__.__name__!s} aggregation of ({tko}) in ({cut.columns.values})\n%s",
#             "\n".join([f"{k!s}: {v!s}" for k, v in self.labels._asdict().items()]),
#         )

#         gb = self.grouped

#         agg = self._agg_runner(cut, tko, gb, fcn, **kwargs)

#         return agg

#     def get_plotted_data_boolean_series(self):
#         f"""A boolean `pd.Series` identifing each measurement that is plotted.

#         Note: The Series is indexed identically to the data stored in the :py:class:`{self.__class__.__name__}`.
#               To align with another index, you may want to use:

#                   tk = {self.__class__.__name__}.get_plotted_data_boolean_series()
#                   idx = tk.replace(False, np.nan).dropna().index
#         """
#         agg = self.agg().dropna()
#         cut = self.cut

#         tk = pd.Series(True, index=cut.index)
#         for k, v in cut.items():
#             chk = agg.index.get_level_values(k)
#             # Use the codes directly because the categoricals are
#             # failing with some Pandas numpy ufunc use. (20200611)
#             chk = pd.CategoricalIndex(chk)
#             tk_ax = v.cat.codes.isin(chk.codes)
#             tk = tk & tk_ax

#         self.logger.info(
#             f"Taking {tk.sum()!s} ({100*tk.mean():.1f}%) {self.__class__.__name__} spectra"
#         )

#         return tk

#     #     Old version that cuts at percentiles.
#     #     @staticmethod
#     #     def clip_data(data, clip):
#     #         q0 = 0.0001
#     #         q1 = 0.9999
#     #         pct = data.quantile([q0, q1])
#     #         lo = pct.loc[q0]
#     #         up = pct.loc[q1]
#     #
#     #         if isinstance(data, pd.Series):
#     #             ax = 0
#     #         elif isinstance(data, pd.DataFrame):
#     #             ax = 1
#     #         else:
#     #             raise TypeError("Unexpected object %s" % type(data))
#     #
#     #         if isinstance(clip, str) and clip.lower()[0] == "l":
#     #             data = data.clip_lower(lo, axis=ax)
#     #         elif isinstance(clip, str) and clip.lower()[0] == "u":
#     #             data = data.clip_upper(up, axis=ax)
#     #         else:
#     #             data = data.clip(lo, up, axis=ax)
#     #         return data
#     #
#     #     New version that uses binning to cut.
#     #         @staticmethod
#     #         def clip_data(data, bins, clip):
#     #             q0 = 0.001
#     #             q1 = 0.999
#     #             pct = data.quantile([q0, q1])
#     #             lo  = pct.loc[q0]
#     #             up  = pct.loc[q1]
#     #             lo = bins.iloc[0]
#     #             up = bins.iloc[-1]
#     #             if isinstance(clip, str) and clip.lower()[0] == "l":
#     #                 data = data.clip_lower(lo)
#     #             elif isinstance(clip, str) and clip.lower()[0] == "u":
#     #                 data = data.clip_upper(up)
#     #             else:
#     #                 data = data.clip(lo, up)
#     #             return data

#     @abstractproperty
#     def _gb_axes(self):
#         r"""The axes or columns over which the `groupby` aggregation takes place.

#         1D cases aggregate over `x`. 2D cases aggregate over `x` and `y`.
#         """
#         pass

#     @abstractmethod
#     def set_axnorm(self, new):
#         r"""The method by which the gridded data is normalized.
#         """
#         pass


# class Hist1D(AggPlot):
#     r"""Create 1D plot of `x`, optionally aggregating `y` in bins of `x`.

#     Properties
#     ----------
#     _gb_axes, path

#     Methods
#     -------
#     set_path, set_data, agg, _format_axis, make_plot
#     """

#     def __init__(
#         self,
#         x,
#         y=None,
#         logx=False,
#         axnorm=None,
#         clip_data=False,
#         nbins=101,
#         bin_precision=None,
#     ):
#         r"""
#         Parameters
#         ----------
#         x: pd.Series
#             Data from which to create bins.
#         y: pd.Series, None
#             If not None, the values to aggregate in bins of `x`. If None,
#             aggregate counts of `x`.
#         logx: bool
#             If True, compute bins in log-space.
#         axnorm: None, str
#         Normalize the histogram.
#             key  normalization
#             ---  -------------
#             t    total
#             d    density
#         clip_data: bool
#             If True, remove the extreme values at 0.001 and 0.999 percentiles
#             before calculating bins or aggregating.
#         nbins: int, str, array-like
#             Dispatched to `np.histogram_bin_edges` or `pd.cut` depending on
#             input type and value.
#         """
#         super(Hist1D, self).__init__()
#         self.set_log(x=logx)
#         self.set_axnorm(axnorm)
#         self.set_data(x, y, clip_data)
#         self.set_labels(x="x", y=labels_module.Count(norm=axnorm) if y is None else "y")
#         self.calc_bins_intervals(nbins=nbins, precision=bin_precision)
#         self.make_cut()
#         self.set_clim(None, None)

#     @property
#     def _gb_axes(self):
#         return ("x",)

#     def set_path(self, new, add_scale=True):
#         path, x, y, z, scale_info = super(Hist1D, self).set_path(new, add_scale)

#         if new == "auto":
#             path = path / x / y

#         else:
#             assert x is None
#             assert y is None

#         if add_scale:
#             assert scale_info is not None
#             scale_info = scale_info[0]
#             path = path / scale_info

#         self._path = path

#     set_path.__doc__ = base.Base.set_path.__doc__

#     def set_data(self, x, y, clip):
#         data = pd.DataFrame({"x": np.log10(np.abs(x)) if self.log.x else x})

#         if y is None:
#             y = pd.Series(1, index=x.index)
#         data.loc[:, "y"] = y

#         self._data = data
#         self._clip = clip

#     def set_axnorm(self, new):
#         r"""The method by which the gridded data is normalized.

# ===== =============================================================
#  key                           description
# ===== =============================================================
#  d     Density normalize
#  t     Total normalize
# ===== =============================================================
# """
#         if new is not None:
#             new = new.lower()[0]
#             assert new == "d"

#         ylbl = self.labels.y
#         if isinstance(ylbl, labels_module.Count):
#             ylbl.set_axnorm(new)
#             ylbl.build_label()

#         self._axnorm = new

#     def construct_cdf(self, only_plotted=True):
#         r"""Convert the obsered measuremets.

#         Returns
#         -------
#         cdf: pd.DataFrame
#             "x" column is the value of the measuremnt.
#             "position" column is the normalized position in the cdf.
#             To plot the cdf:

#                 cdf.plot(x="x", y="cdf")
#         """
#         data = self.data
#         if not data.loc[:, "y"].unique().size <= 2:
#             raise ValueError("Only able to convert data to a cdf if it is a histogram.")

#         tk = self.cut.loc[:, "x"].notna()
#         if only_plotted:
#             tk = tk & self.get_plotted_data_boolean_series()

#         x = data.loc[tk, "x"]
#         cdf = x.sort_values().reset_index(drop=True)

#         if self.log.x:
#             cdf = 10.0 ** cdf

#         cdf = cdf.to_frame()
#         cdf.loc[:, "position"] = cdf.index / cdf.index.max()

#         return cdf

#     def _axis_normalizer(self, agg):
#         r"""Takes care of row, column, total, and density normaliation.

#         Written basically as `staticmethod` so that can be called in `OrbitHist2D`, but
#         as actual method with `self` passed so we have access to `self.log` for density
#         normalization.
#         """

#         axnorm = self.axnorm
#         if axnorm is None:
#             pass
#         elif axnorm == "d":
#             n = agg.sum()
#             dx = pd.Series(pd.IntervalIndex(agg.index).length, index=agg.index)
#             if self.log.x:
#                 dx = 10.0 ** dx
#             agg = agg.divide(dx.multiply(n))

#         elif axnorm == "t":
#             agg = agg.divide(agg.max())

#         else:
#             raise ValueError("Unrecognized axnorm: %s" % axnorm)

#         return agg

#     def agg(self, **kwargs):
#         if self.axnorm == "d":
#             fcn = kwargs.get("fcn", None)
#             if (fcn != "count") & (fcn is not None):
#                 raise ValueError("Unable to calculate a PDF with non-count aggregation")

#         agg = super(Hist1D, self).agg(**kwargs)
#         agg = self._axis_normalizer(agg)
#         agg = self._agg_reindexer(agg)

#         return agg

#     def set_labels(self, **kwargs):

#         if "z" in kwargs:
#             raise ValueError(r"{} doesn't have a z-label".format(self))

#         y = kwargs.pop("y", self.labels.y)
#         if isinstance(y, labels_module.Count):
#             y.set_axnorm(self.axnorm)
#             y.build_label()

#         super(Hist1D, self).set_labels(y=y, **kwargs)

#     def make_plot(self, ax=None, fcn=None, **kwargs):
#         f"""Make a plot.

#         Parameters
#         ----------
#         ax: None, mpl.axis.Axis
#             If `None`, create a subplot axis.
#         fcn: None, str, aggregative function, or 2-tuple of strings
#             Passed directly to `{self.__class__.__name__}.agg`. If
#             None, use the default aggregation function. If str or a
#             single aggregative function, use it.
#         kwargs:
#             Passed directly to `ax.plot`.
#         """
#         agg = self.agg(fcn=fcn)
#         x = pd.IntervalIndex(agg.index).mid

#         if fcn is None or isinstance(fcn, str):
#             y = agg
#             dy = None

#         elif len(fcn) == 2:

#             f0, f1 = fcn
#             if isinstance(f0, FunctionType):
#                 f0 = f0.__name__
#             if isinstance(f1, FunctionType):
#                 f1 = f1.__name__

#             y = agg.loc[:, f0]
#             dy = agg.loc[:, f1]

#         else:
#             raise ValueError(f"Unrecognized `fcn` ({fcn})")

#         if ax is None:
#             fig, ax = plt.subplots()

#         if self.log.x:
#             x = 10.0 ** x

#         drawstyle = kwargs.pop("drawstyle", "steps-mid")
#         pl, cl, bl = ax.errorbar(x, y, yerr=dy, drawstyle=drawstyle, **kwargs)

#         self._format_axis(ax)

#         return ax


# class Hist2D(base.Plot2D, AggPlot):
#     r"""Create a 2D histogram with an optional z-value using an equal number
#     of bins along the x and y axis.

#     Parameters
#     ----------
#     x, y: pd.Series
#         x and y data to aggregate
#     z: None, pd.Series
#         If not None, the z-value to aggregate.
#     axnorm: str
#         Normalize the histogram.
#             key  normalization
#             ---  -------------
#             c    column
#             r    row
#             t    total
#             d    density
#     logx, logy: bool
#         If True, log10 scale the axis.

#     Properties
#     ----------
#     data:
#     bins:
#     cut:
#     axnorm:
#     log<x,y>:
#     <x,y,z>label:
#     path: None, Path

#     Methods
#     -------
#     calc_bins:
#         calculate the x, y bins.
#     make_cut:
#         Utilize the calculated bins to convert (x, y) into pd.Categoral
#         or pd.Interval values used in aggregation.
#     set_[x,y,z]label:
#         Set the x, y, or z label.
#     agg:
#         Aggregate the data in the bins.
#         If z-value is None, count the number of points in each bin.
#         If z-value is not None, calculate the mean for each bin.
#     make_plot:
#         Make a 2D plot of the data with an optional color bar.
#     """

#     def __init__(
#         self,
#         x,
#         y,
#         z=None,
#         axnorm=None,
#         logx=False,
#         logy=False,
#         clip_data=False,
#         nbins=101,
#         bin_precision=None,
#     ):
#         super(Hist2D, self).__init__()
#         self.set_log(x=logx, y=logy)
#         self.set_data(x, y, z, clip_data)
#         self.set_labels(
#             x="x", y="y", z=labels_module.Count(norm=axnorm) if z is None else "z"
#         )

#         self.set_axnorm(axnorm)
#         self.calc_bins_intervals(nbins=nbins, precision=bin_precision)
#         self.make_cut()
#         self.set_clim(None, None)

#     @property
#     def _gb_axes(self):
#         return ("x", "y")

#     def _maybe_convert_to_log_scale(self, x, y):
#         if self.log.x:
#             x = 10.0 ** x
#         if self.log.y:
#             y = 10.0 ** y

#         return x, y

#     #     def set_path(self, new, add_scale=True):
#     #         # Bug: path doesn't auto-set log information.
#     #         path, x, y, z, scale_info = super(Hist2D, self).set_path(new, add_scale)

#     #         if new == "auto":
#     #             path = path / x / y / z

#     #         else:
#     #             assert x is None
#     #             assert y is None
#     #             assert z is None

#     #         if add_scale:
#     #             assert scale_info is not None

#     #             scale_info = "-".join(scale_info)

#     #             if bool(len(path.parts)) and path.parts[-1].endswith("norm"):
#     #                 # Insert <norm> at end of path so scale order is (x, y, z).
#     #                 path = path.parts
#     #                 path = path[:-1] + (scale_info + "-" + path[-1],)
#     #                 path = Path(*path)
#     #             else:
#     #                 path = path / scale_info

#     #         self._path = path

#     #     set_path.__doc__ = base.Base.set_path.__doc__

#     def set_labels(self, **kwargs):

#         z = kwargs.pop("z", self.labels.z)
#         if isinstance(z, labels_module.Count):
#             try:
#                 z.set_axnorm(self.axnorm)
#             except AttributeError:
#                 pass

#             z.build_label()

#         super(Hist2D, self).set_labels(z=z, **kwargs)

#     #     def set_data(self, x, y, z, clip):
#     #         data = pd.DataFrame(
#     #             {
#     #                 "x": np.log10(np.abs(x)) if self.log.x else x,
#     #                 "y": np.log10(np.abs(y)) if self.log.y else y,
#     #             }
#     #         )
#     #
#     #
#     #         if z is None:
#     #             z = pd.Series(1, index=x.index)
#     #
#     #         data.loc[:, "z"] = z
#     #         data = data.dropna()
#     #         if not data.shape[0]:
#     #             raise ValueError(
#     #                 "You can't build a %s with data that is exclusively NaNs"
#     #                 % self.__class__.__name__
#     #             )
#     #
#     #         self._data = data
#     #         self._clip = clip

#     def set_data(self, x, y, z, clip):
#         super(Hist2D, self).set_data(x, y, z, clip)
#         data = self.data
#         if self.log.x:
#             data.loc[:, "x"] = np.log10(np.abs(data.loc[:, "x"]))
#         if self.log.y:
#             data.loc[:, "y"] = np.log10(np.abs(data.loc[:, "y"]))
#         self._data = data

#     def set_axnorm(self, new):
#         r"""The method by which the gridded data is normalized.

# ===== =============================================================
#  key                           description
# ===== =============================================================
#  c     Column normalize
#  d     Density normalize
#  r     Row normalize
#  t     Total normalize
# ===== =============================================================
# """
#         if new is not None:
#             new = new.lower()[0]
#             assert new in ("c", "r", "t", "d")

#         zlbl = self.labels.z
#         if isinstance(zlbl, labels_module.Count):
#             zlbl.set_axnorm(new)
#             zlbl.build_label()

#         self._axnorm = new

#     def _axis_normalizer(self, agg):
#         r"""Takes care of row, column, total, and density normaliation.

#         Written basically as `staticmethod` so that can be called in `OrbitHist2D`, but
#         as actual method with `self` passed so we have access to `self.log` for density
#         normalization.
#         """

#         axnorm = self.axnorm
#         if axnorm is None:
#             pass
#         elif axnorm == "c":
#             agg = agg.divide(agg.max(level="x"), level="x")
#         elif axnorm == "r":
#             agg = agg.divide(agg.max(level="y"), level="y")
#         elif axnorm == "t":
#             agg = agg.divide(agg.max())
#         elif axnorm == "d":
#             N = agg.sum().sum()
#             x = pd.IntervalIndex(agg.index.get_level_values("x").unique())
#             y = pd.IntervalIndex(agg.index.get_level_values("y").unique())
#             dx = pd.Series(
#                 x.length, index=x
#             )  # dx = pd.Series(x.right - x.left, index=x)
#             dy = pd.Series(
#                 y.length, index=y
#             )  # dy = pd.Series(y.right - y.left, index=y)

#             if self.log.x:
#                 dx = 10.0 ** dx
#             if self.log.y:
#                 dy = 10.0 ** dy

#             agg = agg.divide(dx, level="x").divide(dy, level="y").divide(N)

#         elif hasattr(axnorm, "__iter__"):
#             kind, fcn = axnorm
#             if kind == "c":
#                 agg = agg.divide(agg.agg(fcn, level="x"), level="x")
#             elif kind == "r":
#                 agg = agg.divide(agg.agg(fcn, level="y"), level="y")
#             else:
#                 raise ValueError(f"Unrecognized axnorm with function ({kind}, {fcn})")
#         else:
#             raise ValueError(f"Unrecognized axnorm ({axnorm})")

#         return agg

#     def agg(self, **kwargs):
#         agg = super(Hist2D, self).agg(**kwargs)
#         agg = self._axis_normalizer(agg)
#         agg = self._agg_reindexer(agg)

#         return agg

#     def _make_cbar(self, mappable, **kwargs):
#         ticks = kwargs.pop(
#             "ticks",
#             mpl.ticker.MultipleLocator(0.1) if self.axnorm in ("c", "r") else None,
#         )
#         return super(Hist2D, self)._make_cbar(mappable, ticks=ticks, **kwargs)

#     def _limit_color_norm(self, norm):
#         if self.axnorm in ("c", "r"):
#             # Don't limit us to (1%, 99%) interval.
#             return None

#         pct = self.data.loc[:, "z"].quantile([0.01, 0.99])
#         v0 = pct.loc[0.01]
#         v1 = pct.loc[0.99]
#         if norm.vmin is None:
#             norm.vmin = v0
#         if norm.vmax is None:
#             norm.vmax = v1
#         norm.clip = True

#     def make_plot(
#         self,
#         ax=None,
#         cbar=True,
#         limit_color_norm=False,
#         cbar_kwargs=None,
#         fcn=None,
#         alpha_fcn=None,
#         **kwargs,
#     ):
#         r"""
#         Make a 2D plot on `ax` using `ax.pcolormesh`.

#         Paremeters
#         ----------
#         ax: mpl.axes.Axes, None
#             If None, create an `Axes` instance from `plt.subplots`.
#         cbar: bool
#             If True, create color bar with `labels.z`.
#         limit_color_norm: bool
#             If True, limit the color range to 0.001 and 0.999 percentile range
#             of the z-value, count or otherwise.
#         cbar_kwargs: dict, None
#             If not None, kwargs passed to `self._make_cbar`.
#         fcn: FunctionType, None
#             Aggregation function. If None, automatically select in :py:meth:`agg`.
#         alpha_fcn: None, str
#             If not None, the function used to aggregate the data for setting alpha
#             value.
#         kwargs:
#             Passed to `ax.pcolormesh`.
#             If row or column normalized data, `norm` defaults to `mpl.colors.Normalize(0, 1)`.

#         Returns
#         -------
#         ax: mpl.axes.Axes
#             Axes upon which plot was made.
#         cbar_or_mappable: colorbar.Colorbar, mpl.collections.QuadMesh
#             If `cbar` is True, return the colorbar. Otherwise, return the `Quadmesh` used
#             to create the colorbar.
#         """
#         agg = self.agg(fcn=fcn).unstack("x")
#         x = self.edges["x"]
#         y = self.edges["y"]

#         #         assert x.size == agg.shape[1] + 1
#         #         assert y.size == agg.shape[0] + 1

#         # HACK: Works around `gb.agg(observed=False)` pandas bug. (GH32381)
#         if x.size != agg.shape[1] + 1:
#             #             agg = agg.reindex(columns=self.intervals["x"])
#             agg = agg.reindex(columns=self.categoricals["x"])
#         if y.size != agg.shape[0] + 1:
#             #             agg = agg.reindex(index=self.intervals["y"])
#             agg = agg.reindex(index=self.categoricals["y"])

#         if ax is None:
#             fig, ax = plt.subplots()

#         #         if self.log.x:
#         #             x = 10.0 ** x
#         #         if self.log.y:
#         #             y = 10.0 ** y
#         x, y = self._maybe_convert_to_log_scale(x, y)

#         axnorm = self.axnorm
#         norm = kwargs.pop(
#             "norm",
#             mpl.colors.BoundaryNorm(np.linspace(0, 1, 11), 256, clip=True)
#             if axnorm in ("c", "r")
#             else None,
#         )

#         if limit_color_norm:
#             self._limit_color_norm(norm)

#         C = np.ma.masked_invalid(agg.values)
#         XX, YY = np.meshgrid(x, y)
#         pc = ax.pcolormesh(XX, YY, C, norm=norm, **kwargs)

#         cbar_or_mappable = pc
#         if cbar:
#             if cbar_kwargs is None:
#                 cbar_kwargs = dict()

#             if "cax" not in cbar_kwargs.keys() and "ax" not in cbar_kwargs.keys():
#                 cbar_kwargs["ax"] = ax

#             # Pass `norm` to `self._make_cbar` so that we can choose the ticks to use.
#             cbar = self._make_cbar(pc, norm=norm, **cbar_kwargs)
#             cbar_or_mappable = cbar

#         self._format_axis(ax)

#         color_plot = self.data.loc[:, self.agg_axes].dropna().unique().size > 1
#         if (alpha_fcn is not None) and color_plot:
#             self.logger.warning(
#                 "Make sure you verify alpha actually set. I don't yet trust this."
#             )
#             alpha_agg = self.agg(fcn=alpha_fcn)
#             alpha_agg = alpha_agg.unstack("x")
#             alpha_agg = np.ma.masked_invalid(alpha_agg.values.ravel())
#             # Feature scale then invert so smallest STD
#             # is most opaque.
#             alpha = 1 - mpl.colors.Normalize()(alpha_agg)
#             self.logger.warning("Scaling alpha filter as alpha**0.25")
#             alpha = alpha ** 0.25

#             # Set masked values to zero. Otherwise, masked
#             # values are rendered as black.
#             alpha = alpha.filled(0)
#             # Must draw to initialize `facecolor`s
#             plt.draw()
#             # Remove `pc` from axis so we can redraw with std
#             #             pc.remove()
#             colors = pc.get_facecolors()
#             colors[:, 3] = alpha
#             pc.set_facecolor(colors)
#         #             ax.add_collection(pc)

#         elif alpha_fcn is not None:
#             self.logger.warning("Ignoring `alpha_fcn` because plotting counts")

#         return ax, cbar_or_mappable

#     def get_border(self):
#         r"""Get the top and bottom edges of the plot.

#         Returns
#         -------
#         border: namedtuple
#             Contains "top" and "bottom" fields, each with a :py:class:`pd.Series`.
#         """

#         Border = namedtuple("Border", "top,bottom")
#         top = {}
#         bottom = {}
#         for x, v in self.agg().unstack("x").items():
#             yt = v.last_valid_index()
#             if yt is not None:
#                 z = v.loc[yt]
#                 top[(yt, x)] = z

#             yb = v.first_valid_index()
#             if yb is not None:
#                 z = v.loc[yb]
#                 bottom[(yb, x)] = z

#         top = pd.Series(top)
#         bottom = pd.Series(bottom)
#         for edge in (top, bottom):
#             edge.index.names = ["y", "x"]

#         border = Border(top, bottom)
#         return border

#     def _plot_one_edge(
#         self,
#         ax,
#         edge,
#         smooth=False,
#         sg_kwargs=None,
#         xlim=(None, None),
#         ylim=(None, None),
#         **kwargs,
#     ):
#         x = edge.index.get_level_values("x").mid
#         y = edge.index.get_level_values("y").mid

#         if sg_kwargs is None:
#             sg_kwargs = dict()

#         if smooth:
#             wlength = sg_kwargs.pop("window_length", int(np.floor(y.shape[0] / 10)))
#             polyorder = sg_kwargs.pop("polyorder", 3)

#             if not wlength % 2:
#                 wlength -= 1

#             y = savgol_filter(y, wlength, polyorder, **sg_kwargs)

#         if self.log.x:
#             x = 10.0 ** x
#         if self.log.y:
#             y = 10.0 ** y

#         x0, x1 = xlim
#         y0, y1 = ylim

#         tk = np.full_like(x, True, dtype=bool)
#         if x0 is not None:
#             tk = tk & (x0 <= x)
#         if x1 is not None:
#             tk = tk & (x <= x1)
#         if y0 is not None:
#             tk = tk & (y0 <= y)
#         if y1 is not None:
#             tk = tk & (y <= y1)

#         #         if (~tk).any():
#         x = x[tk]
#         y = y[tk]

#         return ax.plot(x, y, **kwargs)

#     def plot_edges(self, ax, smooth=True, sg_kwargs=None, **kwargs):
#         r"""Overplot the edges.

#         Parameters
#         ----------
#         ax:
#             Axis on which to plot.
#         smooth: bool
#             If True, apply a Savitzky-Golay filter (:py:func:`scipy.signal.savgol_filter`)
#             to the y-values before plotting to smooth the curve.
#         sg_kwargs: dict, None
#             If not None, dict of kwargs passed to Savitzky-Golay filter. Also allows
#             for setting of `window_length` and `polyorder` as kwargs. They default to
#             10\% of the number of observations (`window_length`) and 3 (`polyorder`).
#             Note that because `window_length` must be odd, if the 10\% value is even, we
#             take 1-window_length.
#         kwargs:
#             Passed to `ax.plot`
#         """

#         top, bottom = self.get_border()

#         color = kwargs.pop("color", "cyan")
#         label = kwargs.pop("label", None)
#         etop = self._plot_one_edge(
#             ax, top, smooth, sg_kwargs, color=color, label=label, **kwargs
#         )
#         ebottom = self._plot_one_edge(
#             ax, bottom, smooth, sg_kwargs, color=color, **kwargs
#         )

#         return etop, ebottom

#     def _get_contour_levels(self, levels):
#         if (levels is not None) or (self.axnorm is None):
#             pass

#         elif (levels is None) and (self.axnorm == "t"):
#             levels = [0.01, 0.1, 0.3, 0.7, 0.99]

#         elif (levels is None) and (self.axnorm == "d"):
#             levels = [3e-5, 1e-4, 3e-4, 1e-3, 1.7e-3, 2.3e-3]

#         elif (levels is None) and (self.axnorm in ["r", "c"]):
#             levels = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

#         else:
#             raise ValueError(
#                 f"Unrecognized axis normalization {self.axnorm} for default levels."
#             )

#         return levels

#     def _verify_contour_passthrough_kwargs(
#         self, ax, clabel_kwargs, edges_kwargs, cbar_kwargs
#     ):
#         if clabel_kwargs is None:
#             clabel_kwargs = dict()
#         if edges_kwargs is None:
#             edges_kwargs = dict()
#         if cbar_kwargs is None:
#             cbar_kwargs = dict()
#         if "cax" not in cbar_kwargs.keys() and "ax" not in cbar_kwargs.keys():
#             cbar_kwargs["ax"] = ax

#         return clabel_kwargs, edges_kwargs, cbar_kwargs

#     def plot_contours(
#         self,
#         ax=None,
#         label_levels=True,
#         cbar=True,
#         limit_color_norm=False,
#         cbar_kwargs=None,
#         fcn=None,
#         plot_edges=True,
#         edges_kwargs=None,
#         clabel_kwargs=None,
#         skip_max_clbl=True,
#         use_contourf=False,
#         gaussian_filter_std=0,
#         gaussian_filter_kwargs=None,
#         **kwargs,
#     ):
#         f"""Make a contour plot on `ax` using `ax.contour`.

#         Paremeters
#         ----------
#         ax: mpl.axes.Axes, None
#             If None, create an `Axes` instance from `plt.subplots`.
#         label_levels: bool
#             If True, add labels to contours with `ax.clabel`.
#         cbar: bool
#             If True, create color bar with `labels.z`.
#         limit_color_norm: bool
#             If True, limit the color range to 0.001 and 0.999 percentile range
#             of the z-value, count or otherwise.
#         cbar_kwargs: dict, None
#             If not None, kwargs passed to `self._make_cbar`.
#         fcn: FunctionType, None
#             Aggregation function. If None, automatically select in :py:meth:`agg`.
#         plot_edges: bool
#             If True, plot the smoothed, extreme edges of the 2D histogram.
#         edges_kwargs: None, dict
#             Passed to {self.plot_edges!s}.
#         clabel_kwargs: None, dict
#             If not None, dictionary of kwargs passed to `ax.clabel`.
#         skip_max_clbl: bool
#             If True, don't label the maximum contour. Primarily used when the maximum
#             contour is, effectively, a point.
#         maximum_color:
#             The color for the maximum of the PDF.
#         use_contourf: bool
#             If True, use `ax.contourf`. Else use `ax.contour`.
#         gaussian_filter_std: int
#             If > 0, apply `scipy.ndimage.gaussian_filter` to the z-values using the
#             standard deviation specified by `gaussian_filter_std`.
#         gaussian_filter_kwargs: None, dict
#             If not None and gaussian_filter_std > 0, passed to :py:meth:`scipy.ndimage.gaussian_filter`
#         kwargs:
#             Passed to :py:meth:`ax.pcolormesh`.
#             If row or column normalized data, `norm` defaults to `mpl.colors.Normalize(0, 1)`.
#         """
#         levels = kwargs.pop("levels", None)
#         cmap = kwargs.pop("cmap", None)
#         norm = kwargs.pop(
#             "norm",
#             mpl.colors.BoundaryNorm(np.linspace(0, 1, 11), 256, clip=True)
#             if self.axnorm in ("c", "r")
#             else None,
#         )
#         linestyles = kwargs.pop(
#             "linestyles",
#             [
#                 "-",
#                 ":",
#                 "--",
#                 (0, (7, 3, 1, 3, 1, 3, 1, 3, 1, 3)),
#                 "--",
#                 ":",
#                 "-",
#                 (0, (7, 3, 1, 3, 1, 3)),
#             ],
#         )

#         if ax is None:
#             fig, ax = plt.subplots()

#         clabel_kwargs, edges_kwargs, cbar_kwargs = self._verify_contour_passthrough_kwargs(
#             ax, clabel_kwargs, edges_kwargs, cbar_kwargs
#         )

#         inline = clabel_kwargs.pop("inline", True)
#         inline_spacing = clabel_kwargs.pop("inline_spacing", -3)
#         fmt = clabel_kwargs.pop("fmt", "%s")

#         agg = self.agg(fcn=fcn).unstack("x")
#         x = self.intervals["x"].mid
#         y = self.intervals["y"].mid

#         #         assert x.size == agg.shape[1]
#         #         assert y.size == agg.shape[0]

#         # HACK: Works around `gb.agg(observed=False)` pandas bug. (GH32381)
#         if x.size != agg.shape[1]:
#             #             agg = agg.reindex(columns=self.intervals["x"])
#             agg = agg.reindex(columns=self.categoricals["x"])
#         if y.size != agg.shape[0]:
#             #             agg = agg.reindex(index=self.intervals["y"])
#             agg = agg.reindex(index=self.categoricals["y"])

#         x, y = self._maybe_convert_to_log_scale(x, y)

#         XX, YY = np.meshgrid(x, y)

#         C = agg.values
#         if gaussian_filter_std:
#             from scipy.ndimage import gaussian_filter

#             if gaussian_filter_kwargs is None:
#                 gaussian_filter_kwargs = dict()

#             C = gaussian_filter(C, gaussian_filter_std, **gaussian_filter_kwargs)

#         C = np.ma.masked_invalid(C)

#         assert XX.shape == C.shape
#         assert YY.shape == C.shape

#         class nf(float):
#             # Source: https://matplotlib.org/3.1.0/gallery/images_contours_and_fields/contour_label_demo.html
#             # Define a class that forces representation of float to look a certain way
#             # This remove trailing zero so '1.0' becomes '1'
#             def __repr__(self):
#                 return str(self).rstrip("0")

#         levels = self._get_contour_levels(levels)

#         contour_fcn = ax.contour
#         if use_contourf:
#             contour_fcn = ax.contourf

#         if levels is None:
#             args = [XX, YY, C]
#         else:
#             args = [XX, YY, C, levels]

#         qset = contour_fcn(*args, linestyles=linestyles, cmap=cmap, norm=norm, **kwargs)

#         try:
#             args = (qset, levels[:-1] if skip_max_clbl else levels)
#         except TypeError:
#             # None can't be subscripted.
#             args = (qset,)

#         lbls = None
#         if label_levels:
#             qset.levels = [nf(level) for level in qset.levels]
#             lbls = ax.clabel(
#                 *args, inline=inline, inline_spacing=inline_spacing, fmt=fmt
#             )

#         if plot_edges:
#             etop, ebottom = self.plot_edges(ax, **edges_kwargs)

#         cbar_or_mappable = qset
#         if cbar:
#             # Pass `norm` to `self._make_cbar` so that we can choose the ticks to use.
#             cbar = self._make_cbar(qset, norm=norm, **cbar_kwargs)
#             cbar_or_mappable = cbar

#         self._format_axis(ax)

#         return ax, lbls, cbar_or_mappable, qset

#     def project_1d(self, axis, only_plotted=True, project_counts=False, **kwargs):
#         f"""Make a `Hist1D` from the data stored in this `His2D`.

#         Parameters
#         ----------
#         axis: str
#             "x" or "y", specifying the axis to project into 1D.
#         only_plotted: bool
#             If True, only pass data that appears in the {self.__class__.__name__} plot
#             to the :py:class:`Hist1D`.
#         project_counts: bool
#             If True, only send the variable plotted along `axis` to :py:class:`Hist1D`.
#             Otherwise, send both axes (but not z-values).
#         kwargs:
#             Passed to `Hist1D`. Primarily to allow specifying `bin_precision`.

#         Returns
#         -------
#         h1: :py:class:`Hist1D`
#         """
#         axis = axis.lower()
#         assert axis in ("x", "y")

#         data = self.data

#         if data.loc[:, "z"].unique().size >= 2:
#             # Either all 1 or 1 and NaN.
#             other = "z"
#         else:
#             possible_axes = {"x", "y"}
#             possible_axes.remove(axis)
#             other = possible_axes.pop()

#         logx = self.log._asdict()[axis]
#         x = self.data.loc[:, axis]
#         if logx:
#             # Need to convert back to regular from log-space for data setting.
#             x = 10.0 ** x

#         y = self.data.loc[:, other] if not project_counts else None
#         logy = False  # Defined b/c project_counts option.
#         if y is not None:
#             # Only select y-values plotted.
#             logy = self.log._asdict()[other]
#             yedges = self.edges[other].values
#             y = y.where((yedges[0] <= y) & (y <= yedges[-1]))
#             if logy:
#                 y = 10.0 ** y

#         if only_plotted:
#             tk = self.get_plotted_data_boolean_series()
#             x = x.loc[tk]
#             if y is not None:
#                 y = y.loc[tk]

#         h1 = Hist1D(
#             x,
#             y=y,
#             logx=logx,
#             clip_data=False,  # Any clipping will be addressed by bins.
#             nbins=self.edges[axis].values,
#             **kwargs,
#         )

#         h1.set_log(y=logy)  # Need to propagate logy.
#         h1.set_labels(x=self.labels._asdict()[axis])
#         if not project_counts:
#             h1.set_labels(y=self.labels._asdict()[other])

#         h1.set_path("auto")

#         return h1


# class GridHist2D(object):
#     r"""A grid of 2D heatmaps separating the data based on a categorical value.

#     Properties
#     ----------
#     data: pd.DataFrame

#     axnorm: str or None
#         Specify if column, row, total, or density normalization should be used.
#     log: namedtuple
#         Contains booleans identifying axes to log-scale.
#     nbins: int or str
#         Pass to `np.histogram_bin_edges` or `astropy.stats.knuth_bin_width`
#         depending on the input.
#     labels: namedtuple
#         Contains axis labels. Recomend using `labels.TeXlabel` so
#     grouped: pd.Groupeby
#         The data grouped by the categorical.
#     hist2ds: pd.Series
#         The `Hist2D` objects created for each axis. Index is the unique
#         categorical values.
#     fig: mpl.figure.Figure
#         The figure upon which the axes are placed.
#     axes: pd.Series
#         Contains the mpl axes upon which plots are drawn. Index should be
#         identical to `hist2ds`.
#     cbars: pd.Series
#         Contains the colorbar instances. Similar to `hist2ds` and `axes`.
#     cnorms: mpl.color.Normalize or pd.Series
#         mpl.colors.Normalize instance or a pd.Series of them with one for
#         each unique categorical value.
#     use_gs: bool
#         An attempt at the code is written, but not implemented because some
#         minor details need to be worked out. Ideally, if True, use a single
#         colorbar for the entire grid.

#     Methods
#     -------
#     set_<>: setters
#         For data, nbins, axnorm, log, labels, cnorms.
#     make_h2ds:
#         Make the `Hist2D` objects.
#     make_plots:
#         Make the `Hist2D` plots.
#     """

#     def __init__(self, x, y, cat, z=None):
#         r"""Create 2D heatmaps of x, y, and optional z data in a grid for which
#         each unique element in `cat` specifies one plot.

#         Parameters
#         ----------
#         x, y, z: pd.Series or np.array
#             The data to aggregate. pd.Series is prefered.
#         cat: pd.Categorial
#             The categorial series used to create subsets of the data for each
#             grid element.

#         """
#         self.set_nbins(101)
#         self.set_axnorm(None)
#         self.set_log(x=False, y=False)
#         self.set_data(x, y, cat, z)
#         self._labels = base.AxesLabels("x", "y")  # Unsure how else to set defaults.
#         self.set_cnorms(None)

#     @property
#     def data(self):
#         return self._data

#     @property
#     def axnorm(self):
#         r"""Axis normalization."""
#         return self._axnorm

#     @property
#     def logger(self):
#         return self._log

#     @property
#     def nbins(self):
#         return self._nbins

#     @property
#     def log(self):
#         r"""LogAxes booleans.
#         """
#         return self._log

#     @property
#     def labels(self):
#         return self._labels

#     @property
#     def grouped(self):
#         return self.data.groupby("cat")

#     @property
#     def hist2ds(self):
#         try:
#             return self._h2ds
#         except AttributeError:
#             return self.make_h2ds()

#     @property
#     def fig(self):
#         try:
#             return self._fig
#         except AttributeError:
#             return self.init_fig()[0]

#     @property
#     def axes(self):
#         try:
#             return self._axes
#         except AttributeError:
#             return self.init_fig()[1]

#     @property
#     def cbars(self):
#         return self._cbars

#     @property
#     def cnorms(self):
#         r"""Color normalization (mpl.colors.Normalize instance)."""
#         return self._cnorms

#     @property
#     def use_gs(self):
#         return self._use_gs

#     @property
#     def path(self):
#         raise NotImplementedError("Just haven't sat down to write this.")

#     def _init_logger(self):
#         self._logger = logging.getLogger(
#             "{}.{}".format(__name__, self.__class__.__name__)
#         )

#     def set_nbins(self, new):
#         self._nbins = new

#     def set_axnorm(self, new):
#         self._axnorm = new

#     def set_cnorms(self, new):
#         self._cnorms = new

#     def set_log(self, x=None, y=None):
#         if x is None:
#             x = self.log.x
#         if y is None:
#             y = self.log.y
#         log = base.LogAxes(x, y)
#         self._log = log

#     def set_data(self, x, y, cat, z):
#         data = {"x": x, "y": y, "cat": cat}
#         if z is not None:
#             data["z"] = z
#         data = pd.concat(data, axis=1)
#         self._data = data

#     def set_labels(self, **kwargs):
#         r"""Set or update x, y, or z labels. Any label not specified in kwargs
#         is propagated from `self.labels.<x, y, or z>`.
#         """

#         x = kwargs.pop("x", self.labels.x)
#         y = kwargs.pop("y", self.labels.y)
#         z = kwargs.pop("z", self.labels.z)

#         if len(kwargs.keys()):
#             raise KeyError("Unexpected kwarg: {}".format(kwargs.keys()))

#         self._labels = base.AxesLabels(x, y, z)

#     def set_fig_axes(self, fig, axes, use_gs=False):
#         self._set_fig(fig)
#         self._set_axes(axes)
#         self._use_gs = bool(use_gs)

#     def _set_fig(self, new):
#         self._fig = new

#     def _set_axes(self, new):
#         if new.size != len(self.grouped.groups.keys()) + 1:
#             msg = "Number of axes must match number of Categoricals + 1 for All."
#             raise ValueError(msg)

#         keys = ["All"] + sorted(self.grouped.groups.keys())
#         axes = pd.Series(new.ravel(), index=pd.CategoricalIndex(keys))

#         self._axes = axes

#     def init_fig(self, use_gs=False, layout="auto", scale=1.5):

#         if layout == "auto":
#             raise NotImplementedError(
#                 """Need some densest packing algorithm I haven't
# found yet"""
#             )

#         assert len(layout) == 2
#         nrows, ncols = layout

#         if use_gs:
#             raise NotImplementedError(
#                 """Unsure how to consistently store single cax or
# deal with variable layouts."""
#             )
#             fig = plt.figure(figsize=np.array([8, 6]) * scale)

#             gs = mpl.gridspec.GridSpec(
#                 3,
#                 5,
#                 width_ratios=[1, 1, 1, 1, 0.1],
#                 height_ratios=[1, 1, 1],
#                 hspace=0,
#                 wspace=0,
#                 figure=fig,
#             )

#             axes = np.array(12 * [np.nan], dtype=object).reshape(3, 4)
#             sharer = None
#             for i in np.arange(0, 3):
#                 for j in np.arange(0, 4):
#                     if i and j:
#                         a = plt.subplot(gs[i, j], sharex=sharer, sharey=sharer)
#                     else:
#                         a = plt.subplot(gs[i, j])
#                         sharer = a
#                     axes[i, j] = a

#             others = axes.ravel().tolist()
#             a0 = others.pop(8)
#             a0.get_shared_x_axes().join(a0, *others)
#             a0.get_shared_y_axes().join(a0, *others)

#             for ax in axes[:-1, 1:].ravel():
#                 # All off
#                 ax.tick_params(labelbottom=False, labelleft=False)
#                 ax.xaxis.label.set_visible(False)
#                 ax.yaxis.label.set_visible(False)
#             for ax in axes[:-1, 0].ravel():
#                 # 0th column x-labels off.
#                 ax.tick_params(which="x", labelbottom=False)
#                 ax.xaxis.label.set_visible(False)
#             for ax in axes[-1, 1:].ravel():
#                 # Nth row y-labels off.
#                 ax.tick_params(which="y", labelleft=False)
#                 ax.yaxis.label.set_visible(False)

#         #             cax = plt.subplot(gs[:, -1])

#         else:
#             fig, axes = tools.subplots(
#                 nrows=nrows, ncols=ncols, scale_width=scale, scale_height=scale
#             )
#         #             cax = None

#         self.set_fig_axes(fig, axes, use_gs)
#         return fig, axes

#     def _build_one_hist2d(self, x, y, z):
#         h2d = Hist2D(
#             x,
#             y,
#             z=z,
#             logx=self.log.x,
#             logy=self.log.y,
#             clip_data=False,
#             nbins=self.nbins,
#         )
#         h2d.set_axnorm(self.axnorm)

#         xlbl, ylbl, zlbl = self.labels.x, self.labels.y, self.labels.z
#         h2d.set_labels(x=xlbl, y=ylbl, z=zlbl)

#         return h2d

#     def make_h2ds(self):
#         grouped = self.grouped

#         # Build case that doesn't include subgroups.

#         x = self.data.loc[:, "x"]
#         y = self.data.loc[:, "y"]
#         try:
#             z = self.data.loc[:, "z"]
#         except KeyError:
#             z = None

#         hall = self._build_one_hist2d(x, y, z)

#         h2ds = {"All": hall}
#         for k, g in grouped:
#             x = g.loc[:, "x"]
#             y = g.loc[:, "y"]
#             try:
#                 z = g.loc[:, "z"]
#             except KeyError:
#                 z = None

#             h2ds[k] = self._build_one_hist2d(x, y, z)

#         h2ds = pd.Series(h2ds)
#         self._h2ds = h2ds
#         return h2ds

#     @staticmethod
#     def _make_axis_text_label(key):
#         r"""Format the `key` identifying the Categorial group for this axis. To modify,
# sublcass `GridHist2D` and redefine this staticmethod.
# """
#         return key

#     def _format_axes(self):
#         axes = self.axes
#         for k, ax in axes.items():
#             lbl = self._make_axis_text_label(k)
#             ax.text(
#                 0.025,
#                 0.95,
#                 lbl,
#                 transform=ax.transAxes,
#                 va="top",
#                 fontdict={"color": "k"},
#                 bbox={"color": "wheat"},
#             )

#         # ax.set_xlim(-1, 1)
#         # ax.set_ylim(-1, 1)

#     def make_plots(self, **kwargs):
#         h2ds = self.hist2ds
#         axes = self.axes

#         cbars = {}
#         cnorms = self.cnorms
#         for k, h2d in h2ds.items():
#             if isinstance(cnorms, mpl.colors.Normalize) or cnorms is None:
#                 cnorm = cnorms
#             else:
#                 cnorm = cnorms.loc[k]

#             ax = axes.loc[k]
#             ax, cbar = h2d.make_plot(ax=ax, norm=cnorm, **kwargs)
#             if not self.use_gs:
#                 cbars[k] = cbar
#             else:
#                 raise NotImplementedError(
#                     "Unsure how to handle `use_gs == True` for color bars."
#                 )
#         cbars = pd.Series(cbars)

#         self._format_axes()
#         self._cbars = cbars
