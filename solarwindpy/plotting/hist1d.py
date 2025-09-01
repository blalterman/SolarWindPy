#!/usr/bin/env python
r"""One-dimensional histogram plotting utilities."""

import pdb  # noqa: F401

import numpy as np
import pandas as pd
import matplotlib as mpl

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

    Attributes
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
        """Create a one-dimensional histogram.

        Parameters
        ----------
        x : pandas.Series
            Data from which to create bins.
        y : pandas.Series or None, optional
            Values to aggregate in bins of ``x``. If ``None``, counts of
            ``x`` are used.
        logx : bool, optional
            If ``True``, compute bins in logarithmic space.
        axnorm : {"t", "d", None}, optional
            Normalisation applied to the histogram. ``"t"`` uses total
            counts and ``"d"`` yields a density.
        clip_data : bool, optional
            Remove extreme values at the 0.001 and 0.999 percentiles before
            binning or aggregation.
        nbins : int or array-like, optional
            Binning strategy passed to :func:`numpy.histogram_bin_edges` or
            :func:`pandas.cut` depending on the input type.
        bin_precision : int, optional
            Precision for decimal bin edges.
        """
        super(Hist1D, self).__init__()
        self.set_log(x=logx)
        self.set_axnorm(axnorm)
        self.set_data(x, y, clip_data)
        self.set_labels(x="x", y=labels_module.Count(norm=axnorm) if y is None else "y")
        self.calc_bins_intervals(nbins=nbins, precision=bin_precision)
        self.make_cut()
        self.set_clim(None, None)
        self.set_alim(None, None)

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
        ===== ============================================================="""
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
            cdf = 10.0**cdf

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
                dx = 10.0**dx
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

    def make_plot(
        self,
        ax=None,
        fcn=None,
        transpose_axes=False,
        gaussian_filter_std=0,
        plot_window=False,
        plot_window_edges=False,
        gaussian_filter_kwargs=None,
        **kwargs,
    ):
        """Make a plot.

        Parameters
        ----------
        ax: None, mpl.axis.Axis
            If `None`, create a subplot axis.
        fcn: None, str, aggregative function, or 2-tuple
            Passed directly to `{self.__class__.__name__}.agg`. If
            None, use the default aggregation function. If str or a
            single aggregative function, use it. If a 2-tuple is passed,
            then the first element aggregates and the second element
            calculates an uncertainty.
        transpose_axes: bool
            If True, plot independent values on y-axis and dependent
            values on x-axis. Primary use case is plotting 1D projection
            of 2D plot adjascent to 2D axis.
        gaussian_filter_std: int
            If > 0, apply `scipy.ndimage.gaussian_filter` to the z-values using the
            standard deviation specified by `gaussian_filter_std`.
        gaussian_filter_kwargs: None, dict
            If not None and gaussian_filter_std > 0, passed to :py:meth:`scipy.ndimage.gaussian_filter`
        plot_window: bool
            Requires two functions passed to `fcn`. Instead of error bars, plots the uncertainty
            window as a semi-transparent band.
        plot_window_edges: bool
            If True, plot solid lines at the window boundaries.
        kwargs:
            Passed directly to `ax.plot`.
        """
        agg = self.agg(fcn=fcn)
        x = pd.IntervalIndex(agg.index).mid

        dx = None  # Initialize default value. Necessary for `transpose_axes`.
        if fcn is None or isinstance(fcn, (str, FunctionType)):
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
            x = 10.0**x

        if gaussian_filter_std:
            from scipy.ndimage import gaussian_filter

            if gaussian_filter_kwargs is None:
                gaussian_filter_kwargs = dict()

            y = gaussian_filter(y, gaussian_filter_std, **gaussian_filter_kwargs)

        drawstyle = kwargs.pop("drawstyle", "steps-mid")

        if transpose_axes:
            x, y = y, x
            dx, dy = dy, dx

        window_kwargs = kwargs.pop("window_kwargs", dict())
        kwargs = mpl.cbook.normalize_kwargs(kwargs, mpl.lines.Line2D._alias_map)
        if plot_window:
            window_plotter = ax.fill_between
            if transpose_axes:
                window_plotter = ax.fill_betweenx

            color = kwargs.pop("color", None)
            ls = kwargs.pop("linestyle", "-")
            label = kwargs.pop("label", None)

            window_alpha = window_kwargs.pop("alpha", 0.15)
            window_color = window_kwargs.pop("color", color)
            window_linestyle = window_kwargs.pop("linestyle", ls)

            line = ax.plot(x, y, color=color, linestyle=ls, label=label, **kwargs)
            if plot_window_edges:
                ax.plot(
                    x,
                    y + dy,
                    color=window_color,
                    linestyle=window_linestyle,
                    **window_kwargs,
                )
                ax.plot(
                    x,
                    y - dy,
                    color=window_color,
                    linestyle=window_linestyle,
                    **window_kwargs,
                )

            polycol = window_plotter(
                x,
                y - dy,
                y + dy,
                color=window_color,
                linestyle=window_linestyle,
                alpha=window_alpha,
                **window_kwargs,
            )

            out = (line, polycol)

        else:
            out = ax.errorbar(x, y, xerr=dx, yerr=dy, drawstyle=drawstyle, **kwargs)

        self._format_axis(ax, transpose_axes=transpose_axes)

        return ax, out

    def take_data_in_yrange_across_x(
        self,
        ranges_by_x,
        get_x_bounds,
        get_y_bounds,
    ):
        r"""Take data within y-ranges across x-values.

        Parameters
        ----------
        ranges_by_x: iterable
            An iterable with keys used to get the left and right bounds for the data
            and values used to get the top and bottom bounds for the data.

        get_x_bounds: function
            First argument is one key of `ranges_by_x` and returns `left, right`.
            Second argument is a kwarg (`expected_logx`) boolean to transform the returned values according
            to whether or not the keys are :math:`log(x)` or :math:`x` in a manner
            that matches data stored in Hist2D.

        get_y_bounds: functions
            Takes on value of `ranges_by_x` and returns `top, bottom`. Second argument
            Second argument is a kwarg (`expected_logx`) boolean to transform the returned values according
            to whether or not the keys are :math:`log(y)` or :math:`y` in a manner
            that matches data stored in Hist2D.

        Returns
        -------
        taken: np.ndarray 1D
            Array of indices for selecting data in interval.
        """

        available_x = self.agg().index
        assert not ranges_by_x.index.symmetric_difference(available_x).size

        data = self.data
        logx = self.log.x
        logy = self.log.y

        taken = []
        for x, at_x in ranges_by_x.iterrows():
            l, r = get_x_bounds(x, expected_logx=logx)
            b, t = get_y_bounds(at_x, expected_logy=logy)

            assert l < r
            assert b < t

            tkx = (l < data.x) & (data.x <= r)
            tky = (b < data.y) & (data.y <= t)
            tk = tkx & tky
            tk = tk.loc[tk].index
            taken.append(tk)

        taken = np.sort(np.concatenate(taken))
        return taken
