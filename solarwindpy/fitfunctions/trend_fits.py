#!/usr/bin/env python
r""":py:mod:`~solarwindpy.fitfunctions.trend_fits`.

Apply a fit along one dimention of a 2D aggregated data and then fit the results of
those 1D fits along the 2nd dimension of the aggregated data.
"""

import pdb  # noqa: F401

# import warnings
import logging  # noqa: F401
import numpy as np
import pandas as pd
import matplotlib as mpl
from collections import namedtuple

from ..plotting import subplots
from . import core
from . import gaussians

Popt1DKeys = namedtuple("Popt1Dkeys", "y,w", defaults=(None, None))


class TrendFit(object):
    def __init__(
        self,
        agged,
        trendfunc,
        trend_logx=False,
        ykey1d="mu",
        wkey1d="sigma",
        ffunc1d=None,
    ):
        r"""Note that `TrendFit.make_1dfits` must be called by the user.

        So that any kwargs may be passed to the 1D `make_fit` method, which are passed to
        `curve_fit`, allowing the user to specify fit methods, bounds, etc.

        Similarly, `TrendFit.trend_fit.make_fit` must be called by the user so
        that kwargs can be appropriately passed to `curve_fit`.

        call signagure after instantiation is:

            0) Set x and y labels: TrendFunc.set_labels(x=<x label>, y=<y label>)
            1) Make the 1D fit functions: TrendFunc.make_ffunc1ds()
            2) TrendFunc.make_1dfits(): Run 1D fits
            3) TrendFunc.make_trend_func(): init trend function
            4) TrendFunc.trend_func.make_fit(): run trend fits

        Parameters
        ----------
        agged: pd.DataFrame
            x-values along the columns and y-values along the index.
        trendfunc: fitfunctoins.FitFunction
            The function to fit the trend of the ffunc1d popts.
        trend_logx: bool
            If True, take :math:`10.0^x` for x-values passed to `trendfunc_class`.
        ykey1d, wkey1d: str
            The keys to select y-values and weights from the 1D `FitFunction`s for
            passing to the `FitFunction` for fitting the trend.
        ffunc1d: fitfunctoins.FitFunction or None
            Applied in each x-bin. If None, `fitfunctions.Gaussian`.
        """
        self.set_agged(agged)
        self.set_fitfunctions(ffunc1d, trendfunc)
        self._trend_logx = bool(trend_logx)
        self._popt1d_keys = Popt1DKeys(ykey1d, wkey1d)

    def __str__(self):
        return self.__class__.__name__

    @property
    def agged(self):
        return self._agged

    @property
    def ffunc1d_class(self):
        r""":py:class:`FitFunction` to apply in each x-bin."""
        return self._ffunc1d_class

    @property
    def trendfunc_class(self):
        r""":py:class:`FitFunction` to apply each `popt`.

        Of the `ffunc1d` along the x-axis.
        """
        return self._trendfunc_class

    @property
    def ffuncs(self):
        r"""The 1D :py:class:`FitFunction` applied in each x-bin."""
        return self._ffuncs

    @property
    def popt_1d(self):
        r"""Optimized parameters from 1D fits."""
        #         return self._popt_1d
        return pd.DataFrame.from_dict(
            self.ffuncs.apply(lambda x: x.popt).to_dict(), orient="index"
        )

    @property
    def psigma_1d(self):
        r"""Fit uncertainties from 1D fits."""
        return pd.DataFrame.from_dict(
            self.ffuncs.apply(lambda x: x.psigma).to_dict(), orient="index"
        )

    @property
    def trend_func(self):
        r"""`trendfunc_class` applied along the x-axis."""
        return self._trend_func

    @property
    def bad_fits(self):
        r"""Bad 1D fits identifyied when running `make_1dfits`."""
        return self._bad_fits

    @property
    def popt1d_keys(self):
        return self._popt1d_keys

    @property
    def trend_logx(self):
        r"""If True, trend's x-axis is log-scaled.

        Should probably change this to pull from `trend_func` somehow, but unsure how to do so.
        """
        return self._trend_logx

    def make_ffunc1ds(self, **kwargs):
        r"""Kwargs passed to `self.ffunc1d(x, y, **kwargs)`."""
        agg = self.agged
        x = agg.index
        try:
            x = pd.IntervalIndex(agg.index).mid.values
        except TypeError:
            x = x.values

        #         ylbl = self.labels.y
        #         zlbl = self.labels.z

        ffuncs = {}
        for k, y in agg.items():
            ff1d = self.ffunc1d_class(x, y.values, **kwargs)
            # These are slices along y traversing the x-axis, so we
            # rotate labels accordingly.
            #             ff1d.set_labels(x=ylbl, y=zlbl)
            ffuncs[k] = ff1d

        ffuncs = pd.Series(ffuncs)
        self._ffuncs = ffuncs

    def make_1dfits(self, **kwargs):
        r"""Removes bad fits from `ffuncs` and saves them in `bad_fits`."""
        # Successful fits return None, which pandas treats as NaN.
        return_exception = kwargs.pop("return_exception", True)
        fit_success = self.ffuncs.apply(
            lambda x: x.make_fit(return_exception=return_exception, **kwargs)
        )
        bad_idx = fit_success.dropna().index
        bad_fits = self.ffuncs.loc[bad_idx]
        self._bad_fits = bad_fits
        self.ffuncs.drop(bad_idx, inplace=True)

    #         self.make_popt_frame()

    def plot_all_ffuncs(self, legend_title_fmt="%.0f", **kwargs):
        r"""Plot all fit functions.

        Parameters
        ----------
        legend_title_fmt: str
            A string template for formatting the legend titles. Use % formatting so we
            can easily instert TeX into `legend_title_fmt` should we desire.
        kwargs:
            Passed to :py:meth:`ffunc.plot_raw_used_fit`.
        """
        axes = {}
        popt = self.popt_1d
        yk, wk = self.popt1d_keys
        yv = popt.loc[:, yk]
        wv = popt.loc[:, wk]

        y0, y1 = (
            self.trend_func.observations.used.y.min(),
            self.trend_func.observations.used.y.max(),
        )
        y_ok = (y0 <= yv) & (yv <= y1)

        w0, w1 = (
            self.trend_func.observations.used.w.min(),
            self.trend_func.observations.used.w.max(),
        )
        w_ok = (w0 <= wv) & (wv <= w1)

        in_trend = y_ok & w_ok

        legend_title = r"${}={} \; {}$" + "\n{}"

        #         xlbl = self.labels.x
        #         try:
        #             xlbl = xlbl.tex
        #         except AttributeError:
        #             pass

        for k, ff in self.ffuncs.items():
            hax, rax = ff.plotter.plot_raw_used_fit_resid(**kwargs)
            hax.legend_.set_title(
                legend_title.format(
                    self.trend_func.plotter.labels.x.tex,
                    (legend_title_fmt % k.mid),
                    self.trend_func.plotter.labels.x.units,
                    "In Fit" if in_trend.loc[k] else "Not In Fit",
                )
            )
            axes[k] = {"hax": hax, "rax": rax}

        axes = pd.DataFrame.from_dict(axes, orient="index")
        return axes

    #     def make_popt_frame(self):
    #         popt = {}
    #         for k, v in self.ffuncs.items():
    #             popt[k] = v.popt

    #         popt = pd.DataFrame.from_dict(popt, orient="index")
    #         self._popt_1d = popt

    def make_trend_func(self, **kwargs):
        r"""Make trend function.

        Parameters
        ----------
        kwargs:
            passed to `trendfunc_class(x, y, **kwargs)`
        """
        popt = self.popt_1d
        if not popt.shape[0]:
            raise ValueError("Insufficient 1D fits to build trend function")

        try:
            x = pd.IntervalIndex(popt.index).mid
        except TypeError:
            x = popt.index

        if self.trend_logx:
            x = 10.0**x

        if "weights" in kwargs:
            raise ValueError("Weights are handled by `wkey1d`")

        ykey, wkey = self.popt1d_keys
        fcn = self.trendfunc_class
        trend = fcn(
            x,
            popt.loc[:, ykey].values,
            weights=popt.loc[:, wkey].values,
            logx=self.trend_logx,
            **kwargs,
        )
        #         trend.set_labels(**self.labels._asdict())

        self._trend_func = trend

    def plot_all_popt_1d(
        self, ax=None, only_plot_data_in_trend_fit=False, plot_window=True, **kwargs
    ):
        r"""Plot all the 1D popt appropriate for identifying the trend on `ax`.

        Plot all the 1D popt appropriate for identifying the trend on
        `ax`.

        kwargs passed to `ax.errorbar`
        """
        if ax is None:
            fig, ax = subplots()

        popt = self.popt_1d
        ykey, wkey = self.popt1d_keys

        x = pd.IntervalIndex(popt.index).mid

        if only_plot_data_in_trend_fit:
            tk = (
                np.isin(x, self.trend_func.observations.used.x)
                & np.isin(popt.loc[:, ykey].values, self.trend_func.observations.used.y)
                & np.isin(popt.loc[:, wkey].values, self.trend_func.observations.used.w)
            )
            popt = popt.loc[tk]
            x = x[tk]

        if self.trend_logx:
            x = 10.0**x

        window_kwargs = kwargs.pop("window_kwargs", dict())

        wkey = kwargs.pop("wkey", wkey)  # For disabling errobars
        kwargs = mpl.cbook.normalize_kwargs(kwargs, mpl.lines.Line2D._alias_map)
        color = kwargs.pop("color", "cyan")
        linestyle = kwargs.pop("ls", "--")
        label = kwargs.pop("label", "1D Fits")

        if plot_window:
            if wkey is None:
                raise NotImplementedError(
                    "`wkey` must be able to index if `plot_window` is True"
                )

            window_kwargs = mpl.cbook.normalize_kwargs(
                window_kwargs, mpl.collections.Collection._alias_map
            )
            window_color = window_kwargs.pop("color", color)
            window_alpha = window_kwargs.pop("alpha", 0.15)

            y = popt.loc[:, ykey]
            w = popt.loc[:, wkey]

            line = ax.plot(x, y, label=label, color=color, **kwargs)

            y1 = y - w
            y2 = y + w
            window = ax.fill_between(
                x,
                y1,
                y2,
                color=window_color,
                alpha=window_alpha,
                **window_kwargs,
            )

            plotted = (line, window)

        else:
            plotted = ax.errorbar(
                x=x,
                y=ykey,
                yerr=wkey,
                color=color,
                linestyle=linestyle,
                label=label,
                data=popt,
                **kwargs,
            )

            pl, cl, bl = plotted

            if wkey is not None:
                bl[0].set_linestyle(linestyle)

        #         ax.set_xlabel(self.labels.x)
        #         ax.set_ylabel(self.labels.y)

        return plotted

    def plot_trend_fit_resid(self, **kwargs):
        annotate_kwargs = kwargs.pop(
            "annotate_kwargs", dict(xloc=0.5, yloc=0.1, va="bottom")
        )
        used_kwargs = kwargs.pop("used_kwargs", dict(color="k"))
        drawstyle = kwargs.pop("drawstyle", "default")
        hax, rax = self.trend_func.plotter.plot_raw_used_fit_resid(
            drawstyle=drawstyle,
            annotate_kwargs=annotate_kwargs,
            used_kwargs=used_kwargs,
        )

        if self.trend_logx:
            rax.set_xscale("log")

        return hax, rax

    def plot_trend_and_resid_on_ffuncs(self, trend_kwargs=None, fit1d_kwargs=None):
        r"""Plot the trend fit on the 1D popt and the trend fit residuals."""
        if trend_kwargs is None:
            trend_kwargs = {}
        if fit1d_kwargs is None:
            fit1d_kwargs = {}

        hax, rax = self.plot_trend_fit_resid(ax=None, **trend_kwargs)
        self.plot_all_popt_1d(hax, **fit1d_kwargs)

        hax.legend(ncol=4, loc=1, framealpha=0.5)

        if self.trend_logx:
            rax.set_xscale("log")

        return hax, rax

    def plot_1d_popt_and_trend(self, ax=None, **kwargs):
        r"""Plot the trend and 1D popt, without trend residuals, on `ax`"""
        if ax is None:
            fig, ax = subplots()

        kwargs_popt_1d = kwargs.pop("kwargs_popt_1d", dict())
        self.plot_all_popt_1d(ax, **kwargs_popt_1d)

        annotate_kwargs = kwargs.pop("annotate_kwargs", dict())
        fit_kwargs = kwargs.pop("fit_kwargs", dict(color="limegreen"))

        self.trend_func.plotter.plot_raw_used_fit(
            ax,
            annotate_kwargs=annotate_kwargs,
            #             color=color,
            fit_kwargs=fit_kwargs,
            **kwargs,
        )

        return ax

    def set_agged(self, new):
        assert isinstance(new, pd.DataFrame)
        self._agged = new

    #     def set_labels(self, **kwargs):
    #         r"""Set or update x, y, or z labels. Any label not specified in kwargs
    #         is propagated from `self.labels.<x, y, or z>`.
    #         """

    #         x = kwargs.pop("x", self.labels.x)
    #         y = kwargs.pop("y", self.labels.y)
    #         z = kwargs.pop("z", self.labels.z)

    #         if len(kwargs.keys()):
    #             extra = "\n".join(["{}: {}".format(k, v) for k, v in kwargs.items()])
    #             raise KeyError("Unexpected kwarg\n{}".format(extra))

    #         self._labels = core.AxesLabels(x, y, z)

    #         # log = logging.getLogger()
    #         try:
    #             # Update ffunc1d labels
    #             self.ffuncs.apply(lambda x: x.set_labels(x=y, y=z))
    #         #             log.warning("Set ffunc1d labels {}".format(self.ffuncs.iloc[0].labels))
    #         except AttributeError:
    #             #             log.warning("Skipping setting ffunc 1d labels")
    #             pass

    #         try:
    #             # Update trendfunc labels
    #             self.trend_func.set_labels(x=x, y=y, z=z)
    #         #             log.warning("Set trend_func labels {}".format(self.trend_func.labels))

    #         except AttributeError:
    #             #             log.warning("Skipping setting trend_func labels")
    #             pass

    def set_fitfunctions(self, ffunc1d, trendfunc):
        if ffunc1d is None:
            ffunc1d = gaussians.Gaussian

        if not issubclass(ffunc1d, core.FitFunction):
            raise TypeError
        if not issubclass(trendfunc, core.FitFunction):
            raise TypeError

        self._ffunc1d_class = ffunc1d
        self._trendfunc_class = trendfunc

    def set_shared_labels(self, **kwargs):
        r"""Axis labels are shared between the trend_func and ffuncs.

        Here, we update them according to placement in :py:meth:`trend_func`, but properly locating
        them for :py:meth:`ffuncs`.

        Parameters
        ----------
        x:
            :py:meth:`trend_func` x-label. Maps to :py:meth:`ffuncs` legend label.
        y:
            :py:meth:`trend_func` y-label. Maps to :py:meth:`ffuncs` x-label.
        z:
            :py:meth:`trend_func` z-label. Maps to :py:meth:`ffuncs` y-label.
        """

        tf = self.trend_func
        tf.plotter.set_labels(**kwargs)

        y = tf.plotter.labels.y
        z = tf.plotter.labels.z
        for k, ff in self.ffuncs.items():
            ff.plotter.set_labels(x=y, y=z)
