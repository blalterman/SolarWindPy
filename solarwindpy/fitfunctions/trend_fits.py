#!/usr/bin/env python
r""":py:mod:`~solarwindpy.fitfunctions.trend_fits`.

Fit a function in each column of a 2-D histogram (the bin level), then fit a
second function to the trend of one bin-level result across the columns (the
trend level).
"""

__all__ = [
    "TrendFit",
]

import numpy as np
import pandas as pd
import matplotlib as mpl

from ..plotting.tools import subplots
from . import core


def _bin_centers(index):
    r"""The center of each bin: an interval's midpoint, or the label itself."""
    try:
        return pd.IntervalIndex(index).mid.to_numpy()
    except TypeError:
        return np.asarray(index)


class TrendFit(object):
    r"""Fit a function in each column of a 2-D histogram, then fit the trend.

    The bin level fits ``bin_function`` to each column of ``agged``, with the
    histogram's index as its x. The trend level fits ``trend_function`` to one
    column of the bin level's results across the columns, with each column's
    center as its x. So the histogram's index is the bin fits' x and its
    columns are the trend's x.

    Parameters
    ----------
    agged : pandas.DataFrame
        The 2-D histogram: one column per trend bin, one row per bin of the
        bin fits' x. Interval labels are replaced by their midpoints.
    bin_function : type
        The :class:`~solarwindpy.fitfunctions.core.FitFunction` subclass fit
        in each column.
    trend_function : type
        The :class:`~solarwindpy.fitfunctions.core.FitFunction` subclass fit
        to the trend.
    y : tuple
        The :attr:`bin_results` column the trend fits, as ``(P, K)``: for
        example ``("mu", "value")``. Required: it is the scientific choice.
    yerr : tuple or None
        The :attr:`bin_results` column giving the trend's 1-sigma weights, for
        example ``("sigma", "value")`` (each column's width) or ``("mu",
        "uncertainty")`` (the fitted uncertainty of ``mu``). None fits the
        trend unweighted. Required, like ``y``.
    logx : bool, default False
        If True, the trend's x is :math:`10^x` of each column center, and the
        trend is plotted on a logarithmic x-axis.
    bin_kwargs, trend_kwargs : dict, optional
        Passed to the constructor of each bin fit and of the trend fit, for
        example ``xmax=`` or ``guess_xh=``. ``trend_kwargs`` cannot hold
        ``weights``, which ``yerr`` selects.

    Raises
    ------
    TypeError
        If either function is not a FitFunction subclass.
    KeyError
        If ``y`` or ``yerr`` is not a column of the bin fits' results; the
        message lists the columns.

    Examples
    --------
    The author's usual case: a Gaussian in each column, then a hinge on each
    column's ``mu``, weighted by each column's width ``sigma``, starting the
    hinge at the reference speed of 433 km/s::

        tf = TrendFit(
            agged, Gaussian, HingeAtPoint,
            y=("mu", "value"), yerr=("sigma", "value"),
            trend_kwargs={"guess_xh": 433},
        )
        tf.make_fit()
        tf.bin_results       # one row per column
        tf.trend.results     # one row for the hinge
    """

    def __init__(
        self,
        agged,
        bin_function,
        trend_function,
        *,
        y,
        yerr,
        logx=False,
        bin_kwargs=None,
        trend_kwargs=None,
    ):
        if not isinstance(agged, pd.DataFrame):
            raise TypeError(f"agged must be a DataFrame, not {type(agged).__name__}")
        for name, cls in (
            ("bin_function", bin_function),
            ("trend_function", trend_function),
        ):
            if not (isinstance(cls, type) and issubclass(cls, core.FitFunction)):
                raise TypeError(f"{name} must be a FitFunction subclass, not {cls!r}")
        trend_kwargs = dict(trend_kwargs or {})
        if "weights" in trend_kwargs:
            raise ValueError("yerr selects the trend's weights; drop weights=.")

        self._agged = agged
        self._bin_function = bin_function
        self._trend_function = trend_function
        self._logx = bool(logx)
        self._trend_kwargs = trend_kwargs

        x = _bin_centers(agged.index)
        bin_kwargs = dict(bin_kwargs or {})
        self._bin_fits = pd.Series(
            [bin_function(x, agged[k].to_numpy(), **bin_kwargs) for k in agged],
            index=agged.columns,
            dtype=object,
        )

        if len(self._bin_fits):
            available = list(self._bin_fits.iloc[0].results_columns)
            available.remove(("status", ""))
            for name, key in (("y", y), ("yerr", yerr)):
                if key is None and name == "yerr":
                    continue
                if key not in available:
                    raise KeyError(
                        f"{name}={key!r} is not a column of the "
                        f"{bin_function.__name__} results; choose one of {available}"
                    )
        self._y = y
        self._yerr = yerr
        self._bin_results = None
        self._trend = None

    def __str__(self):
        return self.__class__.__name__

    @property
    def agged(self):
        r"""The 2-D histogram the bin fits are made from."""
        return self._agged

    @property
    def bin_function(self):
        r"""The FitFunction subclass fit in each column."""
        return self._bin_function

    @property
    def trend_function(self):
        r"""The FitFunction subclass fit to the trend."""
        return self._trend_function

    @property
    def y(self):
        r"""The :attr:`bin_results` column the trend fits, as ``(P, K)``."""
        return self._y

    @property
    def yerr(self):
        r"""The :attr:`bin_results` column of the trend's weights, or None."""
        return self._yerr

    @property
    def logx(self):
        r"""If True, the trend is fit to :math:`10^x` and plotted on a log x-axis."""
        return self._logx

    @property
    def bin_fits(self):
        r"""The fit in each column, a Series indexed by ``agged``'s columns."""
        return self._bin_fits

    @property
    def bin_results(self):
        r"""Every bin fit's :attr:`~solarwindpy.fitfunctions.core.FitFunction.results`, one row per column.

        Returns
        -------
        pandas.DataFrame
            Indexed by ``agged``'s columns, with the bin fits' ``(P, K)``
            columns plus ``("in_trend", "")``, True for each bin the trend fit
            used. A bin whose fit failed keeps its row: NaN values and the
            exception's class name as its status.

        Raises
        ------
        ~solarwindpy.fitfunctions.core.NotFittedError
            Before :meth:`make_fit`.
        """
        if self._bin_results is None:
            raise core.NotFittedError(
                "TrendFit has no bin results: call make_fit first."
            )
        return self._bin_results.copy()

    @property
    def trend(self):
        r"""The trend fit, a ``trend_function`` instance.

        Raises
        ------
        ~solarwindpy.fitfunctions.core.NotFittedError
            Before :meth:`make_fit`.
        """
        if self._trend is None:
            raise core.NotFittedError("TrendFit has no trend: call make_fit first.")
        return self._trend

    def _trend_x(self):
        r"""The trend's x: each column's center, or :math:`10^x` of it under ``logx``."""
        x = _bin_centers(self.agged.columns)
        return 10.0**x if self.logx else x

    def _ok_bins(self):
        r"""The bin fits that succeeded, the only ones with a plotter."""
        return self.bin_fits[[fit.error is None for fit in self.bin_fits]]

    def make_fit(self, bin_fit_kwargs=None, trend_fit_kwargs=None):
        r"""Fit every column, then fit the trend.

        A bin whose fit fails is recorded in :attr:`bin_results` and left out
        of the trend: its NaN values do not pass the trend's selection.

        Parameters
        ----------
        bin_fit_kwargs, trend_fit_kwargs : dict, optional
            Passed to each bin fit's and to the trend fit's
            :meth:`~solarwindpy.fitfunctions.core.FitFunction.make_fit`, for
            example ``p0=``, ``bounds=`` or ``max_nfev=``.

        Raises
        ------
        InsufficientDataError, FitFailedError, ValueError, RuntimeError
            If the trend fit fails. :attr:`bin_results` and :attr:`trend` are
            set first, and the trend's results record the failure.
        """
        bin_fit_kwargs = dict(bin_fit_kwargs or {})
        for fit in self.bin_fits:
            try:
                fit.make_fit(**bin_fit_kwargs)
            except core._FIT_FAILURES:
                # Recorded in the fit's results.
                pass

        if len(self.bin_fits):
            results = pd.concat([fit.results for fit in self.bin_fits])
        else:
            results = pd.DataFrame(
                columns=pd.MultiIndex.from_tuples([], names=["P", "K"])
            )
        results.index = self.agged.columns

        y = self._column(results, self.y)
        w = None if self.yerr is None else self._column(results, self.yerr)
        trend = self.trend_function(self._trend_x(), y, weights=w, **self._trend_kwargs)
        results[("in_trend", "")] = trend.observations.tk_observed
        self._bin_results = results
        self._trend = trend

        trend.make_fit(**dict(trend_fit_kwargs or {}))

    @staticmethod
    def _column(results, key):
        r"""Column ``key`` of ``results`` as floats; NaN for every row when empty."""
        if key in results:
            return results.loc[:, key].to_numpy(dtype=float)
        return np.full(results.shape[0], np.nan)

    def plot_bin_fits(self, legend_title_fmt="%.0f", **kwargs):
        r"""Plot each successful bin fit and its residuals on a new pair of axes.

        Parameters
        ----------
        legend_title_fmt: str
            A string template for formatting the bin center in each legend
            title. Use % formatting so we can easily insert TeX.
        kwargs:
            Passed to each bin fit's
            :py:meth:`~solarwindpy.fitfunctions.plots.FFPlot.plot_raw_used_fit_resid`.

        Returns
        -------
        pandas.DataFrame
            Columns ``hax`` and ``rax``, one row per successful bin fit. Each
            legend title names the bin center and whether the trend used it.
        """
        in_trend = self.bin_results.loc[:, ("in_trend", "")]
        centers = pd.Series(_bin_centers(self.agged.columns), index=self.agged.columns)
        labels = self.trend.plotter.labels

        legend_title = r"${}={} \; {}$" + "\n{}"

        axes = {}
        for k, ff in self._ok_bins().items():
            hax, rax = ff.plotter.plot_raw_used_fit_resid(**kwargs)
            hax.legend_.set_title(
                legend_title.format(
                    labels.x.tex,
                    (legend_title_fmt % centers.loc[k]),
                    labels.x.units,
                    "In Fit" if in_trend.loc[k] else "Not In Fit",
                )
            )
            axes[k] = {"hax": hax, "rax": rax}

        axes = pd.DataFrame.from_dict(axes, orient="index")
        return axes

    def plot_bin_results(
        self, ax=None, only_in_trend=False, plot_window=True, **kwargs
    ):
        r"""Plot the trend's ``y`` and ``yerr`` from every bin on ``ax``.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            New axes when None.
        only_in_trend : bool, default False
            If True, plot only the bins the trend fit used.
        plot_window : bool, default True
            If True, draw ``y`` as a line inside a ``y - yerr`` to
            ``y + yerr`` window; otherwise draw error bars.
        window_kwargs : dict, optional
            Passed to the window's ``fill_between``.
        **kwargs
            Passed to the line or the errorbar.

        Returns
        -------
        tuple or matplotlib.container.ErrorbarContainer
            ``(lines, window)`` with ``plot_window``, else the errorbar.

        Raises
        ------
        ValueError
            If ``plot_window`` and :attr:`yerr` is None: there is no window.
        """
        if ax is None:
            fig, ax = subplots()

        results = self.bin_results
        x = self._trend_x()
        if only_in_trend:
            tk = results.loc[:, ("in_trend", "")].to_numpy(dtype=bool)
            results = results.loc[tk]
            x = x[tk]

        y = results.loc[:, self.y]
        w = None if self.yerr is None else results.loc[:, self.yerr]

        window_kwargs = kwargs.pop("window_kwargs", dict())

        kwargs = mpl.cbook.normalize_kwargs(kwargs, mpl.lines.Line2D)
        color = kwargs.pop("color", "cyan")
        # normalize_kwargs turned an ``ls`` alias into ``linestyle``. None
        # keeps matplotlib's default line style for the window's line.
        linestyle = kwargs.pop("linestyle", None)
        label = kwargs.pop("label", "1D Fits")

        if plot_window:
            if w is None:
                raise ValueError("plot_window needs yerr; this TrendFit has yerr=None.")

            window_kwargs = mpl.cbook.normalize_kwargs(
                window_kwargs, mpl.collections.Collection
            )
            window_color = window_kwargs.pop("color", color)
            window_alpha = window_kwargs.pop("alpha", 0.15)

            line = ax.plot(
                x, y, label=label, color=color, linestyle=linestyle, **kwargs
            )

            window = ax.fill_between(
                x,
                y - w,
                y + w,
                color=window_color,
                alpha=window_alpha,
                **window_kwargs,
            )

            plotted = (line, window)

        else:
            if linestyle is None:
                linestyle = "--"
            plotted = ax.errorbar(
                x=x,
                y=y,
                yerr=w,
                color=color,
                linestyle=linestyle,
                label=label,
                **kwargs,
            )

            pl, cl, bl = plotted

            if w is not None:
                bl[0].set_linestyle(linestyle)

        return plotted

    def _trend_plotter(self):
        r"""The trend fit's plotter, its x-axis set logarithmic under `logx`."""
        plotter = self.trend.plotter
        if self.logx:
            plotter.set_log(x=True)
        return plotter

    def plot_trend_fit_resid(self, **kwargs):
        r"""Plot the trend fit and its residuals on a new pair of axes.

        Parameters
        ----------
        annotate_kwargs : dict, optional
            Passed to the fit annotation. Default
            ``dict(xloc=0.5, yloc=0.1, va="bottom")``.
        used_kwargs : dict, optional
            Passed to the plot of the observations used in the trend fit.
            Default ``dict(color="k")``.
        drawstyle : str, optional
            Matplotlib drawstyle of the observations. Default ``"default"``.

        Returns
        -------
        hax, rax : matplotlib.axes.Axes
            The trend fit's axes and its residuals' axes. Under
            :attr:`logx` their x-axes are logarithmic.

        Raises
        ------
        TypeError
            If any other keyword argument is given.
        """
        annotate_kwargs = kwargs.pop(
            "annotate_kwargs", dict(xloc=0.5, yloc=0.1, va="bottom")
        )
        used_kwargs = kwargs.pop("used_kwargs", dict(color="k"))
        drawstyle = kwargs.pop("drawstyle", "default")
        if kwargs:
            raise TypeError(
                f"plot_trend_fit_resid got unexpected keyword arguments: {sorted(kwargs)}"
            )
        hax, rax = self._trend_plotter().plot_raw_used_fit_resid(
            drawstyle=drawstyle,
            annotate_kwargs=annotate_kwargs,
            used_kwargs=used_kwargs,
        )

        return hax, rax

    def plot_trend_and_resid_on_bins(
        self, trend_plot_kwargs=None, bin_plot_kwargs=None
    ):
        r"""Plot the trend fit over the bin results, with the trend's residuals.

        ``trend_plot_kwargs`` go to :meth:`plot_trend_fit_resid` and
        ``bin_plot_kwargs`` to :meth:`plot_bin_results`.
        """
        if trend_plot_kwargs is None:
            trend_plot_kwargs = {}
        if bin_plot_kwargs is None:
            bin_plot_kwargs = {}

        hax, rax = self.plot_trend_fit_resid(**trend_plot_kwargs)
        self.plot_bin_results(hax, **bin_plot_kwargs)

        hax.legend(ncol=4, loc=1, framealpha=0.5)

        return hax, rax

    def plot_bin_results_and_trend(self, ax=None, **kwargs):
        r"""Plot the bin results and the trend, without trend residuals, on `ax`.

        ``bin_plot_kwargs`` go to :meth:`plot_bin_results`; ``annotate_kwargs``,
        ``fit_kwargs`` and the rest to the trend plotter's
        :py:meth:`~solarwindpy.fitfunctions.plots.FFPlot.plot_raw_used_fit`.
        """
        if ax is None:
            fig, ax = subplots()

        bin_plot_kwargs = kwargs.pop("bin_plot_kwargs", dict())
        self.plot_bin_results(ax, **bin_plot_kwargs)

        annotate_kwargs = kwargs.pop("annotate_kwargs", dict())
        fit_kwargs = kwargs.pop("fit_kwargs", dict(color="limegreen"))

        self._trend_plotter().plot_raw_used_fit(
            ax,
            annotate_kwargs=annotate_kwargs,
            fit_kwargs=fit_kwargs,
            **kwargs,
        )

        return ax

    def set_shared_labels(self, **kwargs):
        r"""Set the axis labels the trend fit and the bin fits share.

        The trend's labels are set as given, then moved to where each
        successful bin fit plots them.

        Parameters
        ----------
        x:
            The trend's x-label: the bin fits' legend label.
        y:
            The trend's y-label: the bin fits' x-label.
        z:
            The trend's z-label: the bin fits' y-label.
        """

        tf = self.trend
        tf.plotter.set_labels(**kwargs)

        y = tf.plotter.labels.y
        z = tf.plotter.labels.z
        for ff in self._ok_bins():
            ff.plotter.set_labels(x=y, y=z)
