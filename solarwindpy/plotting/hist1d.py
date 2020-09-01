#!/usr/bin/env python
r"""Aggregate, create, and save 1D and 2D histograms and binned plots.
"""

import pdb  # noqa: F401

import numpy as np
import pandas as pd

from types import FunctionType
from matplotlib import pyplot as plt

from . import base
from . import labels as labels_module
from .agg_plot import AggPlot

# import os
# import psutil


# def log_mem_usage():
#    usage = psutil.Process(os.getpid()).memory_info()
#    usage = "\n".join(
#        ["{} {:.3f} GB".format(k, v * 1e-9) for k, v in usage._asdict().items()]
#    )
#    logging.getLogger("main").warning("Memory usage\n%s", usage)


class Hist1D(AggPlot):
    r"""Create 1D plot of `x`, optionally aggregating `y` in bins of `x`.

    Properties
    ----------
    _gb_axes, path

    Methods
    -------
    set_path, set_data, agg, _format_axis, make_plot
    """

    def __init__(
        self,
        x,
        y=None,
        logx=False,
        axnorm=None,
        clip_data=False,
        nbins=101,
        bin_precision=None,
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
        axnorm: None, str
        Normalize the histogram.
            key  normalization
            ---  -------------
            t    total
            d    density
        clip_data: bool
            If True, remove the extreme values at 0.001 and 0.999 percentiles
            before calculating bins or aggregating.
        nbins: int, str, array-like
            Dispatched to `np.histogram_bin_edges` or `pd.cut` depending on
            input type and value.
        """
        super(Hist1D, self).__init__()
        self.set_log(x=logx)
        self.set_axnorm(axnorm)
        self.set_data(x, y, clip_data)
        self.set_labels(x="x", y=labels_module.Count(norm=axnorm) if y is None else "y")
        self.calc_bins_intervals(nbins=nbins, precision=bin_precision)
        self.make_cut()
        self.set_clim(None, None)

    @property
    def _gb_axes(self):
        return ("x",)

    def set_path(self, new, add_scale=True):
        path, x, y, z, scale_info = super(Hist1D, self).set_path(new, add_scale)

        if new == "auto":
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

    def set_data(self, x, y, clip):
        data = pd.DataFrame({"x": np.log10(np.abs(x)) if self.log.x else x})

        if y is None:
            y = pd.Series(1, index=x.index)
        data.loc[:, "y"] = y

        self._data = data
        self._clip = clip

    def set_axnorm(self, new):
        r"""The method by which the gridded data is normalized.

===== =============================================================
 key                           description
===== =============================================================
 d     Density normalize
 t     Total normalize
===== =============================================================
"""
        if new is not None:
            new = new.lower()[0]
            assert new == "d"

        ylbl = self.labels.y
        if isinstance(ylbl, labels_module.Count):
            ylbl.set_axnorm(new)
            ylbl.build_label()

        self._axnorm = new

    def construct_cdf(self, only_plotted=True):
        r"""Convert the obsered measuremets.

        Returns
        -------
        cdf: pd.DataFrame
            "x" column is the value of the measuremnt.
            "position" column is the normalized position in the cdf.
            To plot the cdf:

                cdf.plot(x="x", y="cdf")
        """
        data = self.data
        if not data.loc[:, "y"].unique().size <= 2:
            raise ValueError("Only able to convert data to a cdf if it is a histogram.")

        tk = self.cut.loc[:, "x"].notna()
        if only_plotted:
            tk = tk & self.get_plotted_data_boolean_series()

        x = data.loc[tk, "x"]
        cdf = x.sort_values().reset_index(drop=True)

        if self.log.x:
            cdf = 10.0 ** cdf

        cdf = cdf.to_frame()
        cdf.loc[:, "position"] = cdf.index / cdf.index.max()

        return cdf

    def _axis_normalizer(self, agg):
        r"""Takes care of row, column, total, and density normaliation.

        Written basically as `staticmethod` so that can be called in `OrbitHist2D`, but
        as actual method with `self` passed so we have access to `self.log` for density
        normalization.
        """

        axnorm = self.axnorm
        if axnorm is None:
            pass
        elif axnorm == "d":
            n = agg.sum()
            dx = pd.Series(pd.IntervalIndex(agg.index).length, index=agg.index)
            if self.log.x:
                dx = 10.0 ** dx
            agg = agg.divide(dx.multiply(n))

        elif axnorm == "t":
            agg = agg.divide(agg.max())

        else:
            raise ValueError("Unrecognized axnorm: %s" % axnorm)

        return agg

    def agg(self, **kwargs):
        if self.axnorm == "d":
            fcn = kwargs.get("fcn", None)
            if (fcn != "count") & (fcn is not None):
                raise ValueError("Unable to calculate a PDF with non-count aggregation")

        agg = super(Hist1D, self).agg(**kwargs)
        agg = self._axis_normalizer(agg)
        agg = self._agg_reindexer(agg)

        return agg

    def set_labels(self, **kwargs):

        if "z" in kwargs:
            raise ValueError(r"{} doesn't have a z-label".format(self))

        y = kwargs.pop("y", self.labels.y)
        if isinstance(y, labels_module.Count):
            y.set_axnorm(self.axnorm)
            y.build_label()

        super(Hist1D, self).set_labels(y=y, **kwargs)

    def make_plot(self, ax=None, fcn=None, **kwargs):
        f"""Make a plot.

        Parameters
        ----------
        ax: None, mpl.axis.Axis
            If `None`, create a subplot axis.
        fcn: None, str, aggregative function, or 2-tuple of strings
            Passed directly to `{self.__class__.__name__}.agg`. If
            None, use the default aggregation function. If str or a
            single aggregative function, use it.
        kwargs:
            Passed directly to `ax.plot`.
        """
        agg = self.agg(fcn=fcn)
        x = pd.IntervalIndex(agg.index).mid

        if fcn is None or isinstance(fcn, str):
            y = agg
            dy = None

        elif len(fcn) == 2:

            f0, f1 = fcn
            if isinstance(f0, FunctionType):
                f0 = f0.__name__
            if isinstance(f1, FunctionType):
                f1 = f1.__name__

            y = agg.loc[:, f0]
            dy = agg.loc[:, f1]

        else:
            raise ValueError(f"Unrecognized `fcn` ({fcn})")

        if ax is None:
            fig, ax = plt.subplots()

        if self.log.x:
            x = 10.0 ** x

        drawstyle = kwargs.pop("drawstyle", "steps-mid")
        pl, cl, bl = ax.errorbar(x, y, yerr=dy, drawstyle=drawstyle, **kwargs)

        self._format_axis(ax)

        return ax
