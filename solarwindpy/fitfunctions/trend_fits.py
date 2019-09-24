#!/usr/bin/env python
r""":py:mod:`~solarwindpy.fitfunctions.trend_fits`.

Apply a fit along one dimention of a 2D aggregated data and then fit the
results of those 1D fits along the 2nd dimension of the aggregated data.
"""

import pdb  # noqa: F401

# import warnings
import logging  # noqa: F401
import pandas as pd
from collections import namedtuple

import solarwindpy as swp
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
        r"""Note that `TrendFit.make_1dfits` must be called by the user so that any
        kwargs may be passed to the 1D `make_fit` method, which are passed to
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
        self._labels = core.AxesLabels(x="x", y="y", z=swp.pp.labels.Count())

    @property
    def agged(self):
        return self._agged

    @property
    def ffunc1d_class(self):
        r""":py:class:`~solarwindpy.fitfunctions.core.FitFunction` to apply in each x-bin.
        """
        return self._ffunc1d_class

    @property
    def trendfunc_class(self):
        r""":py:class:`~solarwindpy.fitfunctions.core.FitFunction` to apply each `popt` of
        the `ffunc1d` along the x-axis.
        """
        return self._trendfunc_class

    @property
    def ffuncs(self):
        r"""The 1D :py:class:`~solarwindpy.fitfunctions.core.FitFunction` applied in each x-bin
        """
        return self._ffuncs

    @property
    def popt_1d(self):
        r"""Optimized parameters from 1D fits.
        """
        return self._popt_1d

    @property
    def trend_func(self):
        r"""`trendfunc_class` applied along the x-axis.
        """
        return self._trend_func

    @property
    def bad_fits(self):
        r"""Bad 1D fits identifyied when running `make_1dfits`.
        """
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

    @property
    def labels(self):
        return self._labels

    def set_agged(self, new):
        assert isinstance(new, pd.DataFrame)
        self._agged = new

    def set_labels(self, **kwargs):
        r"""Set or update x, y, or z labels. Any label not specified in kwargs
        is propagated from `self.labels.<x, y, or z>`.
        """

        x = kwargs.pop("x", self.labels.x)
        y = kwargs.pop("y", self.labels.y)
        z = kwargs.pop("z", self.labels.z)

        if len(kwargs.keys()):
            extra = "\n".join(["{}: {}".format(k, v) for k, v in kwargs.items()])
            raise KeyError("Unexpected kwarg\n{}".format(extra))

        self._labels = core.AxesLabels(x, y, z)

        # log = logging.getLogger()
        try:
            # Update ffunc1d labels
            self.ffuncs.apply(lambda x: x.set_labels(x=y, y=z))
        #             log.warning("Set ffunc1d labels {}".format(self.ffuncs.iloc[0].labels))
        except AttributeError:
            #             log.warning("Skipping setting ffunc 1d labels")
            pass

        try:
            # Update trendfunc labels
            self.trend_func.set_labels(x=x, y=y, z=z)
        #             log.warning("Set trend_func labels {}".format(self.trend_func.labels))

        except AttributeError:
            #             log.warning("Skipping setting trend_func labels")
            pass

    def set_fitfunctions(self, ffunc1d, trendfunc):
        if ffunc1d is None:
            ffunc1d = gaussians.Gaussian

        if not issubclass(ffunc1d, core.FitFunction):
            raise TypeError
        if not issubclass(trendfunc, core.FitFunction):
            raise TypeError

        self._ffunc1d_class = ffunc1d
        self._trendfunc_class = trendfunc

    def make_ffunc1ds(self, **kwargs):
        r"""kwargs passed to `self.ffunc1d(x, y, **kwargs)`.
        """
        agg = self.agged
        x = pd.IntervalIndex(agg.index).mid.values

        ylbl = self.labels.y
        zlbl = self.labels.z

        ffuncs = {}
        for k, y in agg.items():
            ff1d = self.ffunc1d_class(x, y.values, **kwargs)
            # These are slices along y traversing the x-axis, so we
            # rotate labels accordingly.
            ff1d.set_labels(x=ylbl, y=zlbl)
            ffuncs[k] = ff1d

        ffuncs = pd.Series(ffuncs)
        self._ffuncs = ffuncs

    def make_1dfits(self, **kwargs):
        r"""Removes bad fits from `ffuncs` and saves them in `bad_fits`.
        """
        # Successful fits return None, which pandas treats as NaN.
        fit_success = self.ffuncs.apply(lambda x: x.make_fit(**kwargs))
        bad_idx = fit_success.dropna().index
        bad_fits = self.ffuncs.loc[bad_idx]
        self._bad_fits = bad_fits
        self.ffuncs.drop(bad_idx, inplace=True)
        self.make_popt_frame()

    def plot_all_ffuncs(self, legend_title_fmt="%.0f", **kwargs):
        r"""`kwargs` passed to each `ffunc.plot_raw_used_fit(**kwargs)`.

        legend_title_fmt: str
            A string template for formatting the legend titles. Use % formatting so we
            can easily instert TeX into `legend_title_fmt should we desire.
        """
        axes = {}
        popt = self.popt_1d
        yk, wk = self.popt1d_keys
        yv = popt.loc[:, yk]
        wv = popt.loc[:, wk]

        y0, y1 = self.trend_func.yobs.min(), self.trend_func.yobs.max()
        y_ok = (y0 <= yv) & (yv <= y1)

        w0, w1 = self.trend_func.weights.min(), self.trend_func.weights.max()
        w_ok = (w0 <= wv) & (wv <= w1)

        in_trend = y_ok & w_ok

        legend_title = "${}={}$\n{}"

        for k, ff in self.ffuncs.items():
            hax, rax = ff.plot_raw_used_fit_resid(**kwargs)
            hax.legend_.set_title(
                legend_title.format(
                    self.labels.x.tex,
                    (legend_title_fmt % k.mid),
                    "In Fit" if in_trend.loc[k] else "Not In Fit",
                )
            )
            axes[k] = {"hax": hax, "rax": rax}

        axes = pd.DataFrame.from_dict(axes, orient="index")
        return axes

    def make_popt_frame(self):
        popt = {}
        for k, v in self.ffuncs.items():
            popt[k] = v.popt

        popt = pd.DataFrame.from_dict(popt, orient="index")
        self._popt_1d = popt

    def make_trend_func(self, **kwargs):
        r"""
        Parameters
        ----------
        kwargs:
            passed to `trendfunc_class(x, y, **kwargs)`
        """
        popt = self.popt_1d
        if not popt.shape[0]:
            raise ValueError("Insufficient 1D fits to build trend function")

        x = pd.IntervalIndex(popt.index).mid
        if self.trend_logx:
            x = 10.0 ** x

        if "weights" in kwargs:
            raise ValueError("Weights are handled by `wkey1d`")

        ykey, wkey = self.popt1d_keys
        fcn = self.trendfunc_class
        trend = fcn(
            x, popt.loc[:, ykey].values, weights=popt.loc[:, wkey].values, **kwargs
        )
        trend.set_labels(**self.labels._asdict())

        self._trend_func = trend

    def plot_all_popt_1d(self, ax=None, **kwargs):
        r"""Plot all the 1D popt appropriate for identifying the trend on
        `ax`.

        kwargs passed to `ax.errorbar`
        """
        if ax is None:
            fig, ax = swp.pp.subplots()

        popt = self.popt_1d
        ykey, wkey = self.popt1d_keys

        x = pd.IntervalIndex(popt.index).mid
        if self.trend_logx:
            x = 10.0 ** x

        color = kwargs.pop("color", "cyan")
        linestyle = kwargs.pop("ls", "--")
        label = kwargs.pop("label", "1D Fits")
        pl, cl, bl = ax.errorbar(
            x=x,
            y=ykey,
            yerr=wkey,
            color=color,
            linestyle=linestyle,
            label=label,
            data=popt,
            **kwargs,
        )

        bl[0].set_linestyle(linestyle)

        ax.set_xlabel(self.labels.x)
        ax.set_ylabel(self.labels.y)

        return pl, cl, bl

    def plot_trend_fit_resid(self, **kwargs):
        annotate_kwargs = kwargs.pop(
            "annotate_kwargs", dict(xloc=0.5, yloc=0.1, va="bottom")
        )
        used_kwargs = kwargs.pop("used_kwargs", dict(color="k"))
        drawstyle = kwargs.pop("drawstyle", "default")
        hax, rax = self.trend_func.plot_raw_used_fit_resid(
            drawstyle=drawstyle,
            annotate_kwargs=annotate_kwargs,
            used_kwargs=used_kwargs,
        )

        if self.trend_logx:
            rax.set_xscale("log")

        return hax, rax

    def plot_trend_and_resid_on_ffuncs(self, trend_kwargs=None, fit1d_kwargs=None):
        r"""Plot the trend fit on the 1D popt and the trend fit residuals.
        """
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
        r"""Plot the trend and 1D popt, without trend residuals, on `ax`
        """
        if ax is None:
            fig, ax = swp.pp.subplots()

        kwargs_popt_1d = kwargs.pop("kwargs_popt_1d", dict())
        self.plot_all_popt_1d(ax, **kwargs_popt_1d)

        annotate_kwargs = kwargs.pop("annotate_kwargs", dict())
        fit_kwargs = kwargs.pop("fit_kwargs", dict(color="limegreen"))

        self.trend_func.plot_raw_used_fit(
            ax,
            annotate_kwargs=annotate_kwargs,
            #             color=color,
            fit_kwargs=fit_kwargs,
            **kwargs,
        )
