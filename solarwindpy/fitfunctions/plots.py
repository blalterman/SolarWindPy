#!/usr/bin/env python
r"""Plotting utilities for :mod:`solarwindpy.fitfunctions`.

This module contains :class:`FFPlot`, a helper for visualizing fitted
models, residuals and associated annotations.
"""

__all__ = [
    "AxesLabels",
    "LogAxes",
    "FFPlot",
]

import logging  # noqa: F401

import numpy as np
import matplotlib as mpl

from pathlib import Path
from collections import namedtuple
from matplotlib import pyplot as plt

AxesLabels = namedtuple("AxesLabels", "x,y,z", defaults=(None,))
LogAxes = namedtuple("LogAxes", "x,y", defaults=(False,))

# The single source of FFPlot's default styles. Each plot method merges the
# caller's normalised Line2D keywords over its entry, so a caller's keyword
# always wins and an unset one falls back to this table.
_DEFAULT_STYLES = {
    "raw": {"color": "k", "label": r"$\mathrm{Obs}$"},
    "used": {
        "color": "forestgreen",
        "marker": "P",
        "markerfacecolor": "none",
        "markersize": 8,
        "label": r"$\mathrm{Used}$",
    },
    "fit": {
        "color": "darkorange",
        "linestyle": (0, (7, 3, 1, 3, 1, 3, 1, 3)),
        "label": r"$\mathrm{Fit}$",
    },
    "simple_residuals": {
        "color": "forestgreen",
        "marker": "P",
        "linestyle": "-",
        "drawstyle": "steps-mid",
        "markerfacecolor": "none",
        "markersize": 8,
    },
    "robust_residuals": {
        "color": "darkorange",
        "marker": "X",
        "linestyle": "-",
        "drawstyle": "steps-mid",
        "markerfacecolor": "none",
        "markersize": 8,
    },
}
_WINDOW_ALPHA = 0.15


def _style(kind, kwargs):
    """Merge normalised Line2D ``kwargs`` over the default style for ``kind``."""
    return {
        **_DEFAULT_STYLES[kind],
        **mpl.cbook.normalize_kwargs(dict(kwargs), mpl.lines.Line2D),
    }


class FFPlot(object):
    """Plot of a fit function's observations, fit, and residuals.

    Instances are created by a fit function's
    :attr:`~solarwindpy.fitfunctions.core.FitFunction.plotter`, not
    constructed directly.
    """

    def __init__(self, observations, y_fit, TeX_info, fit_result, fitfunction_name=""):
        """Container for plotting a :class:`~solarwindpy.fitfunctions.core.FitFunction`.

        Parameters
        ----------
        observations : namedtuple
            The ``(used, raw, tk_observed)`` observations of the fit, as
            returned by ``FitFunction.observations``.
        y_fit : array-like
            Model evaluated at the observed ``x`` values.
        TeX_info : :class:`~solarwindpy.fitfunctions.tex_info.TeXinfo`
            Object describing the fit for annotation.
        fit_result : scipy.optimize.OptimizeResult
            Result object returned from the fitting routine.
        fitfunction_name : str, optional
            Name of the originating fit function.
        """

        self.set_observations(observations, y_fit)
        self.set_TeX_info(TeX_info)
        self.set_fit_result(fit_result)
        self.set_fitfunction_name(fitfunction_name)
        self._log = LogAxes(x=False, y=False)
        self._labels = AxesLabels("x", "y")

    def __str__(self):
        return self.__class__.__name__

    @property
    def labels(self):
        return self._labels

    @property
    def log(self):
        return self._log

    @property
    def observations(self):
        return self._observations

    @property
    def fitfunction_name(self):
        return self._fitfunction_name

    @property
    def fit_result(self):
        return self._fit_result

    @property
    def path(self):
        base = Path(self.__class__.__name__) / self.fitfunction_name

        try:
            base /= self.labels.x.path
        except AttributeError:
            base /= str(self.labels.x)

        try:
            base /= self.labels.y.path
        except AttributeError:
            base /= str(self.labels.y)

        if self.labels.z is not None:
            try:
                base = base / self.labels.z.path
            except AttributeError:
                base = base / str(self.labels.z)

        x_scale = "logX" if self.log.x else "linX"
        y_scale = "logY" if self.log.y else "linY"
        scale_info = "_".join([x_scale, y_scale])

        path = base / scale_info
        return path

    @property
    def TeX_info(self):
        return self._TeX_info

    @property
    def y_fit(self):
        return self._y_fit

    def set_fitfunction_name(self, new):
        """Set the descriptive name for saved plots."""

        self._fitfunction_name = str(new)

    def set_fit_result(self, new):
        """Store the optimization result object."""

        self._fit_result = new

    def set_observations(self, observations, y_fit):
        """Set raw and fitted values used for plotting."""

        assert y_fit.shape == observations.raw.x.shape
        assert y_fit[observations.tk_observed].shape == observations.used.x.shape
        self._observations = observations
        self._y_fit = y_fit

    def _estimate_markevery(self):
        """Heuristic marker spacing for large datasets."""

        try:
            # Estimate marker density for readability
            markevery = int(
                10.0 ** (np.floor(np.log10(self.observations.used.x.size) - 1))
            )
        except OverflowError:
            # Or we have a huge number of data points, so lets only
            # mark a few of them.
            markevery = 1000

        if not markevery:
            markevery = None

        return markevery

    def _format_hax(self, ax):
        r"""Format the axes of the observation and fit plots.

        Used by :py:meth:`plot_raw`, :py:meth:`plot_used`, and
        :py:meth:`plot_fit`.
        """
        ax.grid(True, which="major", axis="both")

        # Copied from plt.hist. (20161107_0112)
        x = self.observations.raw.x
        if x.size:
            ax.update_datalim([(x[0], 0), (x[-1], 0)], updatey=False)

        ax.set_xlabel(self.labels.x)
        ax.set_ylabel(self.labels.y)
        if self.log.x:
            ax.set_xscale("log")
        if self.log.y:
            ax.set_yscale("log")

        ax.label_outer()

    def _format_rax(self, ax, pct):
        ax.grid(True, which="major", axis="both")

        ax.set_xlabel(self.labels.x)
        if self.log.x:
            ax.set_xscale("log", nonpositive="clip")

        if pct:
            ax.set_ylabel(r"$\mathrm{Residual} \; [\%]$")
            ax.set_yscale("symlog", linthresh=10)
            ax.set_ylim(-100, 100)

        else:
            ax.set_ylabel(r"$\mathrm{Residual} \; [\#]$")

        x = self.observations.raw.x
        if x.size:
            ax.update_datalim([(x[0], 0), (x[-1], 0)], updatey=False)

        ax.label_outer()

        return ax

    def _get_or_create_axes(self, ax=None):
        """Get existing axes or create new figure/axes if None provided."""
        if ax is None:
            fig, ax = plt.subplots()
        return ax

    def _plot_window_edges(self, ax, x, y1, y2, color, edge_kwargs):
        """Draw the window's lower and upper edges as lines.

        ``edge_kwargs`` may use the window's (collection) vocabulary, so
        ``ec``/``edgecolor`` sets the edge lines' colour; what remains is
        normalised for the Line2D that is drawn.
        """
        kwargs = mpl.cbook.normalize_kwargs(
            dict(edge_kwargs), mpl.collections.Collection
        )
        line_color = kwargs.pop("color", color)
        line_color = kwargs.pop("edgecolor", line_color)
        kwargs = mpl.cbook.normalize_kwargs(kwargs, mpl.lines.Line2D)

        edge1 = ax.plot(x, y1, color=line_color, **kwargs)
        edge2 = ax.plot(x, y2, color=line_color, **kwargs)
        return edge1, edge2

    def _plot_observations(self, kind, ax, plot_window, edge_kwargs, kwargs):
        """Draw the ``kind`` (``"raw"`` or ``"used"``) observations.

        Shared by :py:meth:`plot_raw` and :py:meth:`plot_used`.
        """
        ax = self._get_or_create_axes(ax)

        window_kwargs = kwargs.pop("window_kwargs", dict())
        style = _style(kind, kwargs)

        obs = getattr(self.observations, kind)
        x = obs.x
        y = obs.y
        w = obs.w

        if not plot_window:
            plotted = ax.errorbar(x, y, yerr=w, **style)
            self._format_hax(ax)
            return ax, plotted

        if w is None:
            logging.getLogger().warning(
                "No weights. Need weights to plot a window for FitFunction. Setting w to 0."
            )
            w = 0

        window_kwargs = mpl.cbook.normalize_kwargs(
            window_kwargs, mpl.collections.Collection
        )
        window_color = window_kwargs.pop("color", style["color"])
        window_alpha = window_kwargs.pop("alpha", _WINDOW_ALPHA)

        line = ax.plot(x, y, **style)

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

        edges = None
        if edge_kwargs is not None:
            edges = self._plot_window_edges(ax, x, y1, y2, window_color, edge_kwargs)

        self._format_hax(ax)
        return ax, (line, window, edges)

    def plot_raw(self, ax=None, plot_window=True, edge_kwargs=None, **kwargs):
        r"""Plot the raw observations.

        Plot from ``observations.raw.x``, ``observations.raw.y``, and
        ``observations.raw.w``.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            Axes to draw on. If None, a new figure and axes are created.
        plot_window : bool, default True
            If True, draw a line with a ``y +- w`` window. Otherwise draw
            error bars.
        edge_kwargs : dict, optional
            If not None, draw the window's edges as lines with these
            keywords; ``ec`` or ``edgecolor`` sets their colour.
        **kwargs
            Line2D keywords merged over the default raw style. The
            ``window_kwargs`` keyword is passed to
            :meth:`matplotlib.axes.Axes.fill_between` for the window.

        Returns
        -------
        ax : matplotlib.axes.Axes
        plotted : tuple or matplotlib.container.ErrorbarContainer
            ``(line, window, edges)`` with a window, else the error bars.
        """
        return self._plot_observations("raw", ax, plot_window, edge_kwargs, kwargs)

    def plot_used(self, ax=None, plot_window=True, edge_kwargs=None, **kwargs):
        r"""Plot the observations used in the fit.

        Plot from ``observations.used.x``, ``observations.used.y``, and
        ``observations.used.w``. Parameters and returns are those of
        :py:meth:`plot_raw`; unless ``markevery`` is given, a marker is
        drawn on every :math:`10^{\lfloor \log_{10} N \rfloor - 1}`-th of
        the :math:`N` used points.
        """
        if kwargs.get("markevery") is None:
            kwargs["markevery"] = self._estimate_markevery()
        return self._plot_observations("used", ax, plot_window, edge_kwargs, kwargs)

    def plot_fit(self, ax=None, annotate=True, annotate_kwargs=None, **kwargs):
        r"""Plot the fit over the raw ``x`` values.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            Axes to draw on. If None, a new figure and axes are created.
        annotate : bool, default True
            If True, annotate the axes with :py:attr:`TeX_info`.
        annotate_kwargs : dict, optional
            Passed to ``TeX_info.annotate_info``.
        **kwargs
            Line2D keywords merged over the default fit style.

        Returns
        -------
        ax : matplotlib.axes.Axes
        """
        ax = self._get_or_create_axes(ax)

        if annotate_kwargs is None:
            annotate_kwargs = {}

        ax.plot(self.observations.raw.x, self.y_fit, **_style("fit", kwargs))

        if annotate:
            self.TeX_info.annotate_info(ax, **annotate_kwargs)

        self._format_hax(ax)

        return ax

    def plot_raw_used_fit(
        self,
        ax=None,
        drawstyle=None,
        annotate=True,
        raw_kwargs=None,
        used_kwargs=None,
        fit_kwargs=None,
        annotate_kwargs=None,
    ):
        r"""Make a plot of the raw observations, observations in fit, and the fit.

        Combines the outputs of :py:meth:`plot_raw`, :py:meth:`plot_used`,
        and :py:meth:`plot_fit`.

        Parameters
        ----------
        ax: None, matplotlib.axes.Axes

        drawstyle: str, None
            `mpl` `drawstyle`, shared by :py:meth:`plot_raw` and :py:meth:`plot_used`.
            If None, defaults to "steps-mid".
        annotate: True
            If True, add fit info to the annotation using ax.text.
        raw_kwargs: dict
            Passed to `ax.plot(**kwargs)` in :py:meth:`plot_raw`.
        used_kwargs: dict
            Passed to `ax.plot(**kwargs)` in :py:meth:`plot_used`.
        fit_kwargs: dict
            Passed to `ax.plot(**fit_kwargs)` for plotting fit.
        annotate_kwargs:
            Passed to `ax.text`.

        Returns
        -------
        ax: matplotlib.axes.Axes
        """

        ax = self._get_or_create_axes(ax)

        if raw_kwargs is None:
            raw_kwargs = (
                dict()
            )  # dict(color="darkgreen", markerfacecolor="none", marker="P")

        if used_kwargs is None:
            used_kwargs = dict()

        if fit_kwargs is None:
            fit_kwargs = dict(zorder=2.2)

        if drawstyle is None:
            drawstyle = "steps-mid"

        self.plot_raw(ax=ax, drawstyle=drawstyle, **raw_kwargs)
        self.plot_used(ax=ax, drawstyle=drawstyle, **used_kwargs)
        self.plot_fit(
            ax=ax, annotate=annotate, annotate_kwargs=annotate_kwargs, **fit_kwargs
        )

        ax.legend(loc=1, framealpha=0)  # loc chosen so annotation text defaults work.

        self._format_hax(ax)

        return ax

    def plot_residuals(
        self, ax=None, pct=True, subplots_kwargs=None, kind="simple", **kwargs
    ):
        r"""Plot residuals for the data used in the fit.

        Percent residuals are shown on a symlog scale with ``linthresh=10``
        within :math:`\pm 100\%`.

        Parameters
        ----------
        ax : mpl.axes.Axes, optional
            Axis to draw on. If ``None`` a new figure and axis are created.
        pct : bool, default True
            If ``True``, show simple residuals as percentages of the model.
            Robust residuals are in units of the observation uncertainty, so
            ``kind="robust"`` or ``"both"`` requires ``pct=False``.
        subplots_kwargs : dict, optional
            Passed to ``plt.subplots`` when ``ax`` is ``None``.
        kind : {'simple', 'robust', 'both'}, default "simple"
            Which residuals to plot. With ``"both"``, the robust residuals
            are skipped when the fit result holds none.
        **kwargs
            Line2D keywords merged over each residual kind's default style.
            ``label`` prefixes each line's ``Simple`` or ``Robust`` label.

        Returns
        -------
        ax : mpl.axes.Axes
            Axis with residuals plotted.

        Raises
        ------
        ValueError
            If ``kind`` is unknown, or robust residuals are requested in
            percent.
        """
        kind = kind.lower()
        kinds = {"simple": ("simple",), "robust": ("robust",)}
        kinds["both"] = ("simple", "robust")
        if kind not in kinds:
            raise ValueError(
                f"kind must be 'simple', 'robust', or 'both', not {kind!r}"
            )

        to_draw = kinds[kind]
        if kind == "both" and getattr(self.fit_result, "fun", None) is None:
            to_draw = ("simple",)

        # Compute every series before drawing, so a refused request draws nothing.
        series = [(k, self.residuals(pct=pct, robust=(k == "robust"))) for k in to_draw]

        if subplots_kwargs is None:
            subplots_kwargs = {}

        if ax is None:
            fig, ax = plt.subplots(**subplots_kwargs)

        kwargs = dict(kwargs)
        label = kwargs.pop("label", r"").strip("$")
        if kwargs.get("markevery") is None:
            kwargs["markevery"] = self._estimate_markevery()

        for k, r in series:
            ax.plot(
                self.observations.used.x,
                r,
                label=r"$\mathrm{%s \; %s}$" % (label, k.title()),
                **_style(f"{k}_residuals", kwargs),
            )

        self._format_rax(ax, pct)
        return ax

    def plot_raw_used_fit_resid(
        self,
        annotate=True,
        fit_resid_axes=None,
        figsize=(6, 4),
        resid_kwargs=None,
        **kwargs,
    ):
        """Make a stacked fit, residual plot.

        Parameters
        ----------
        annotate: bool
            If True, add fit annotation to axis.
        fit_resid_axes: None, 2-tuple of mpl.axis.Axis
            If not None, (fit, resid) axis pair to plot the (raw, used, fit)
            and residual on, respectively. Otherwise, use `GridSpec` to build
            a pair of axes where the `raw_used_fit` axis is 3 times the `resid_axis`.
            Additionally, if `fit_resid_axes` is None, the `hax` and `rax` will share
            an x-axis and `hax`'s x-ticks and label will be set invisible.
        figsize:
            Any valid ``figsize`` for :func:`matplotlib.pyplot.figure`. This code
            was developed with default size 6x4 and this size helps accomodate annotation.
            So we persist it here.
        resid_kwargs: dict, None
            Passed to :py:meth:`plot_residuals`.
        kwargs:
            Passed to :py:meth:`plot_raw_used_fit`.

        Returns
        -------
        hax: mpl.axis.Axis
            Axis with raw observations, used observations, and fit plotted on it.
        rax: mpl.axis.Axis
            Axis with residuals plotted on it.
        """

        if fit_resid_axes is not None:
            hax, rax = fit_resid_axes

        else:
            fig = plt.figure(figsize=figsize)
            gs = mpl.gridspec.GridSpec(2, 1, height_ratios=[3, 1], hspace=0.1)
            # sharex in this code requires that I pass the axis object with which the x-axis is being shared.
            # Source for sharex option: http://stackoverflow.com/questions/22511550/gridspec-with-shared-axes-in-python
            rax = fig.add_subplot(gs[1])
            hax = fig.add_subplot(gs[0], sharex=rax)

        resid_kwargs = dict() if resid_kwargs is None else dict(resid_kwargs)
        resid_pct = resid_kwargs.pop("resid_pct", True)

        self.plot_raw_used_fit(ax=hax, annotate=annotate, **kwargs)
        self.plot_residuals(ax=rax, pct=resid_pct, **resid_kwargs)

        hax.xaxis.get_label().set_visible(False)
        [t.set_visible(False) for t in hax.xaxis.get_ticklabels()]

        return hax, rax

    def residuals(self, pct=False, robust=False):
        r"""Calculate the fit residuals, model minus observation.

        Parameters
        ----------
        pct : bool, default False
            If True, express simple residuals as a percentage of the model.
            Where the model is zero the percent residual is NaN.
        robust : bool, default False
            If True, return the fit result's residual vector ``fun``, in
            units of the observation uncertainty.

        Returns
        -------
        numpy.ndarray

        Raises
        ------
        ValueError
            If both ``pct`` and ``robust`` are True: robust residuals are in
            units of the uncertainty and have no percent form.
        """

        if robust:
            if pct:
                raise ValueError(
                    "Robust residuals are in units of the observation "
                    "uncertainty and have no percent form; pass pct=False."
                )
            return self.fit_result.fun

        y_fit_used = self.y_fit[self.observations.tk_observed]
        r = y_fit_used - self.observations.used.y

        if pct:
            with np.errstate(divide="ignore", invalid="ignore"):
                r = 100.0 * (r / y_fit_used)
            r = np.where(y_fit_used == 0, np.nan, r)

        return r

    def set_labels(self, **kwargs):
        r"""Set or update x, y, or z labels.

        Any label not specified in kwargs is propagated from `self.labels.<x, y, or z>`.
        """

        x = kwargs.pop("x", self.labels.x)
        y = kwargs.pop("y", self.labels.y)
        z = kwargs.pop("z", self.labels.z)

        if len(kwargs.keys()):
            extra = "\n".join([f"{k}: {v}" for k, v in kwargs.items()])
            raise KeyError(f"Unexpected kwarg\n{extra}")

        self._labels = AxesLabels(x, y, z)

    def set_log(self, **kwargs):
        r"""Set :py:class:`LogAxes`.

        Only used for determining if weights should be :math:`w/(y \ln(10))`.
        """
        log = self._log._asdict()
        for k, v in kwargs.items():
            log[k] = v

        self._log = LogAxes(**log)

    def set_TeX_info(self, new):
        """Assign the annotation source.

        Parameters
        ----------
        new : :class:`~solarwindpy.fitfunctions.tex_info.TeXinfo`
            Formatted fit information used for annotations.
        """

        self._TeX_info = new
