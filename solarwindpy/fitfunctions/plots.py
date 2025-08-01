#!/usr/bin/env python
r""":py:mod:`~solarwindpy.fitfunctions` plotter.
"""

import pdb  # noqa: F401
import logging  # noqa: F401

import numpy as np
import matplotlib as mpl

from pathlib import Path
from collections import namedtuple
from matplotlib import pyplot as plt

AxesLabels = namedtuple("AxesLabels", "x,y,z", defaults=(None,))
LogAxes = namedtuple("LogAxes", "x,y", defaults=(False,))


class FFPlot(object):
    def __init__(self, observations, y_fit, TeX_info, fit_result, fitfunction_name=""):
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
        y_scale = "logY" if self.log.y else "logY"
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
        self._fitfunction_name = str(new)

    def set_fit_result(self, new):
        self._fit_result = new

    def set_observations(self, observations, y_fit):
        assert y_fit.shape == observations.raw.x.shape
        assert y_fit[observations.tk_observed].shape == observations.used.x.shape
        #         assert y_fit[observations.tk_observed].shape == robust_residuals.shape
        self._observations = observations
        self._y_fit = y_fit

    #         self._robust_residuals = robust_residuals

    def _estimate_markevery(self):
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

    def _format_hax(self, ax, with_rax=False):
        r"""Format the :py:meth:`plot_bins`, :py:meth:`plot_in_fit`, and
        :py:meth:`plot_fit` results.
        """
        ax.grid(True, which="major", axis="both")

        #         ax.legend(loc=1, framealpha=0)  # loc chosen so annotation text defaults work.

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

        #         if with_rax:
        #             ax.xaxis.get_label().set_visible(False)
        #             [t.set_visible(False) for t in ax.xaxis.get_ticklabels()]

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

        #         ax.legend(loc=0, framealpha=0, ncol=2)

        ax.label_outer()

        return ax

    def plot_raw(self, ax=None, plot_window=True, edge_kwargs=None, **kwargs):
        r"""Plot the observations used in the fit from :py:meth:`self.observations.raw.x`,
        :py:meth:`self.observations.raw.y`, :py:meth:`self.observations.raw.w`.

        Parameters
        ----------
        edge_kwargs: None, dict
            If not None, plot edges on the window using these kwargs.
        """
        if ax is None:
            fig, ax = plt.subplots()

        window_kwargs = kwargs.pop("window_kwargs", dict())

        kwargs = mpl.cbook.normalize_kwargs(kwargs, mpl.lines.Line2D._alias_map)
        color = kwargs.pop("color", "k")
        label = kwargs.pop("label", r"$\mathrm{Obs}$")

        x = self.observations.raw.x
        y = self.observations.raw.y
        w = self.observations.raw.w
        #         if self.log.y and w is not None:
        #             w = w / (y * np.log(10.0))
        #             w = np.log10(np.exp(1)) * w / y

        #         # Plot the raw data histograms.
        #         plotline, caplines, barlines = ax.errorbar(
        #             x, y, yerr=w, label=label, color=color, **kwargs
        #         )

        def _plot_window_edges(ax, **kwargs):
            kwargs = mpl.cbook.normalize_kwargs(
                kwargs, mpl.collections.Collection._alias_map
            )

            edge1 = ax.plot(x, y1, **kwargs)
            edge2 = ax.plot(x, y2, **kwargs)

            return edge1, edge2

        if plot_window:
            if w is None:
                logging.getLogger().warning(
                    "No weights. Need weights to plot a window for FitFunction. Setting w to 0."
                )
                w = 0

            window_kwargs = mpl.cbook.normalize_kwargs(
                window_kwargs, mpl.collections.Collection._alias_map
            )
            window_color = window_kwargs.pop("color", color)
            window_alpha = window_kwargs.pop("alpha", 0.15)

            line = ax.plot(x, y, label=label, color=color, **kwargs)

            y1 = y - w
            y2 = y + w
            window = ax.fill_between(
                x, y1, y2, color=window_color, alpha=window_alpha, **window_kwargs,
            )

            edges = None
            if edge_kwargs is not None:
                edge_kwargs = mpl.cbook.normalize_kwargs(
                    edge_kwargs, mpl.collections.Collection._alias_map
                )
                edge_color = edge_kwargs.pop("color", window_color)
                edges = _plot_window_edges(ax, color=edge_color, **edge_kwargs)

            plotted = (line, window, edges)

        else:
            # Plot the raw data histograms.
            plotted = ax.errorbar(x, y, yerr=w, label=label, color=color, **kwargs,)

        self._format_hax(ax)

        return ax, plotted

    def plot_used(self, ax=None, plot_window=True, edge_kwargs=None, **kwargs):
        r"""Plot the observations used in the fit from :py:meth:`self.observations.used.x`,
        :py:meth:`self.observations.used.y`, and :py:meth:`self.observations.used.w`.
        """
        if ax is None:
            fig, ax = plt.subplots()

        window_kwargs = kwargs.pop("window_kwargs", dict())

        kwargs = mpl.cbook.normalize_kwargs(kwargs, mpl.lines.Line2D._alias_map)
        color = kwargs.pop("color", "forestgreen")
        marker = kwargs.pop("marker", "P")
        markerfacecolor = kwargs.pop("markerfacecolor", "none")
        markersize = kwargs.pop("markersize", 8)
        markevery = kwargs.pop("markevery", None)
        label = kwargs.pop("label", r"$\mathrm{Used}$")

        x = self.observations.used.x
        y = self.observations.used.y
        w = self.observations.used.w
        #         if self.log.y and w is not None:
        #             w = w / (y * np.log(10.0))
        #             w = np.log10(np.exp(1)) * w / y

        if markevery is None:
            markevery = self._estimate_markevery()

        if plot_window:
            if w is None:
                logging.getLogger().warning(
                    "No weights. Need weights to plot a window for FitFunction. Setting w to 0."
                )
                w = 0

            window_kwargs = mpl.cbook.normalize_kwargs(
                window_kwargs, mpl.collections.Collection._alias_map
            )
            window_color = window_kwargs.pop("color", color)
            window_alpha = window_kwargs.pop("alpha", 0.15)

            line = ax.plot(
                x,
                y,
                label=label,
                color=color,
                marker=marker,
                markerfacecolor=markerfacecolor,
                markersize=markersize,
                markevery=markevery,
                **kwargs,
            )

            y1 = y - w
            y2 = y + w
            window = ax.fill_between(
                x, y1, y2, color=window_color, alpha=window_alpha, **window_kwargs,
            )

            edges = None
            if edge_kwargs is not None:

                def _plot_window_edges(ax, **kwargs):
                    kwargs = mpl.cbook.normalize_kwargs(
                        kwargs, mpl.collections.Collection._alias_map
                    )

                    edge1 = ax.plot(x, y1, **kwargs)
                    edge2 = ax.plot(x, y2, **kwargs)

                    return edge1, edge2

                edge_kwargs = mpl.cbook.normalize_kwargs(
                    edge_kwargs, mpl.collections.Collection._alias_map
                )
                edge_color = edge_kwargs.pop("color", window_color)
                edges = _plot_window_edges(ax, color=edge_color, **edge_kwargs)
            #                 edge_kwargs = mpl.cbook.normalize_kwargs(edge_kwargs, mpl.collections.Collection._alias_map)

            #                 edge1 = ax.plot(x, y1,
            #                                 color=window_color,
            #                                 **edge_kwargs)
            #                 edge2 = ax.plot(x, y2,
            #                                 color=window_color,
            #                                 **edge_kwargs)

            #                 edges = (edge1, edge2)

            plotted = (line, window, edges)

        else:
            # Plot the raw data histograms.
            plotted = ax.errorbar(
                x,
                y,
                yerr=w,
                label=label,
                color=color,
                marker=marker,
                markerfacecolor=markerfacecolor,
                markersize=markersize,
                markevery=markevery,
                **kwargs,
            )

        self._format_hax(ax)

        return ax, plotted

    def plot_fit(self, ax=None, annotate=True, annotate_kwargs=None, **kwargs):
        r"""Plot the fit."""
        if ax is None:
            fig, ax = plt.subplots()

        if annotate_kwargs is None:
            annotate_kwargs = {}

        kwargs = mpl.cbook.normalize_kwargs(kwargs, mpl.lines.Line2D._alias_map)
        color = kwargs.pop("color", "darkorange")
        label = kwargs.pop("label", r"$\mathrm{Fit}$")
        linestyle = kwargs.pop("linestyle", (0, (7, 3, 1, 3, 1, 3, 1, 3)))
        #         zorder = kwargs.pop("zorder", 2.005) # Ensure it's the top line

        # Overplot the fit.
        ax.plot(
            self.observations.raw.x,
            self.y_fit,
            label=label,
            color=color,
            linestyle=linestyle,
            #             zorder=zorder,
            **kwargs,
        )

        if annotate:
            self.TeX_info.annotate_info(ax, **annotate_kwargs)
        #             self.annotate_TeX_info(ax, **annotate_kwargs)

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

        Combines the outputs of :py:meth:`self.plot_raw`, :py:meth:`self.plot_used`,
        and :py:meth:`self.plot_fit`.

        Parameters
        ----------
        ax: None, mpl.Axes.axis_subplot

        drawstyle: str, None
            `mpl` `drawstyle`, shared by :py:meth:`self.plot_raw` and :py:meth:`self.plot_used`.
            If None, defaults to "steps-mid".
        annotate: True
            If True, add fit info to the annotation using ax.text.
        raw_kwargs: dict
            Passed to `ax.plot(**kwargs)` in :py:meth:`self.plot_raw`.
        used_kwargs: dict
            Passed to `ax.plot(**kwargs)` in :py:meth:`self.plot_used`.
        fit_kwargs: dict
            Passed to `ax.plot(**fit_kwargs)` for plotting fit.
        annotate_kwargs:
            Passed to `ax.text`.

        Returns
        -------
        ax: mpl.Axes.axis_subplot
        """

        if ax is None:
            fig, ax = plt.subplots()

        if raw_kwargs is None:
            raw_kwargs = (
                dict()
            )  # dict(color="darkgreen", markerfacecolor="none", marker="P")

        if used_kwargs is None:
            used_kwargs = dict()  # dict(color="k")

        if fit_kwargs is None:
            #             fit_kwargs = dict()  # dict(color="darkorange")
            fit_kwargs = dict(zorder=2.2)

        if drawstyle is None:
            drawstyle = "steps-mid"

        self.plot_raw(ax=ax, drawstyle=drawstyle, **raw_kwargs)
        self.plot_used(ax=ax, drawstyle=drawstyle, **used_kwargs)
        self.plot_fit(
            ax=ax, annotate=annotate, annotate_kwargs=annotate_kwargs, **fit_kwargs
        )

        ax.legend(loc=1, framealpha=0)  # loc chosen so annotation text defaults work.

        #         # Copied from plt.hist. (20161107_0112)
        #         ax.update_datalim(
        #             [(self.observations.raw.x[0], 0), (self.observations.raw.x[-1], 0)], updatey=False
        #         )

        self._format_hax(ax)

        return ax

    def plot_residuals(
        self, ax=None, pct=True, subplots_kwargs=None, kind="both", **kwargs
    ):
        r"""Make a plot of the fit function that includes the data and fit,
                but are limited to data included in the fit.

                Residuals are plotted as a percentage, both positive and negative, on
                a symlog scale with `linthresh=10`.
        <<<<<<< HEAD
        =======

                Parameters
                ----------
                ax: None, mpl.axis.Axis
                    If not None, mpl.axis.Axis.
                pct: bool
                    If True, plot in units of percent.
                subplots_kwargs: dict, None
                    If not None, passed to `plt.subplots`. Disabled if `ax` is not
                    None.
                kind: str
                    Specify type of residuals to plot.

                        ======== ======================
                         Value        Description
                        ======== ======================
                         simple   Use simple residuals
                         robust   Use robust residuals
                         both     Use both
                        ======== ======================
        >>>>>>> c8b5d9bfe4c7ce53d00e5d0773d27dcc8b8f258c
        """

        if subplots_kwargs is None:
            subplots_kwargs = {}

        if ax is None:
            fig, ax = plt.subplots(**subplots_kwargs)

        kwargs = mpl.cbook.normalize_kwargs(kwargs, mpl.lines.Line2D._alias_map)
        drawstyle = kwargs.pop("drawstyle", "steps-mid")
        #         color = kwargs.pop("color", "darkgreen")
        #         marker = kwargs.pop("marker", "P")
        markerfacecolor = kwargs.pop("markerfacecolor", "none")
        markersize = kwargs.pop("markersize", 8)
        markevery = kwargs.pop("markevery", None)
        label = kwargs.pop("label", r"").strip("$")
        kind = kind.lower()

        if markevery is None:
            markevery = self._estimate_markevery()

        if kind in ("simple", "robust"):
            residuals = self.residuals(
                pct=pct, robust=True if kind == "robust" else False
            )

            color = kwargs.pop("color", "forestgreen")
            marker = kwargs.pop("marker", "P")
            linestyle = kwargs.pop("linestyle", "-")

            label = " \; ".join([label, kind.title()]).lstrip(  # noqa: W605
                " \; "  # noqa: W605
            )
            label = r"$\mathrm{%s}$" % label
            #             label = (r"$\mathrm{%s \; %s}$" % (label, kind.title()).replace(" \; ", "")

            ax.plot(
                self.observations.used.x,
                residuals,
                label=label,
                drawstyle=drawstyle,
                color=color,
                marker=marker,
                linestyle=linestyle,
                markerfacecolor=markerfacecolor,
                markersize=markersize,
                markevery=markevery,
                **kwargs,
            )

        elif kind == "both":

            ax.plot(
                self.observations.used.x,
                self.residuals(pct=pct, robust=False),
                label=(r"$\mathrm{%s \; Simple}$" % label).lstrip(  # noqa: W605
                    " \; "  # noqa: W605
                ),
                drawstyle=drawstyle,
                color="forestgreen",
                marker="P",
                linestyle="-",
                markerfacecolor=markerfacecolor,
                markersize=markersize,
                markevery=markevery,
                **kwargs,
            )

            try:
                r = self.residuals(pct=pct, robust=True)
                ax.plot(
                    self.observations.used.x,
                    r,
                    label=(r"$\mathrm{%s \; Robust}$" % label).lstrip(  # noqa: W605
                        " \; "  # noqa: W605
                    ),
                    drawstyle=drawstyle,
                    color="darkorange",
                    marker="X",
                    linestyle="-",
                    markerfacecolor=markerfacecolor,
                    markersize=markersize,
                    markevery=markevery,
                    **kwargs,
                )
            except AttributeError as e:
                if "NoneType" in str(e):
                    pass

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
        f"""Make a stacked fit, residual plot.

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
            Any valid argument for :py:meth:`plt.figure(figsize=figsize)`. This code
            was developed with default size 6x4 and this size helps accomodate annotation.
            So we persist it here.
        resid_kwargs: dict, None
            Passed to :py:meth:`{self.__class__.__name__}.plot_residuals`.
        kwargs:
            Passed to :py:meth:`{self.__class__.__name__}.plot_raw_used_fit`.

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

        if resid_kwargs is None:
            resid_kwargs = dict()

        resid_pct = resid_kwargs.pop("resid_pct", True)

        self.plot_raw_used_fit(ax=hax, annotate=annotate, **kwargs)
        self.plot_residuals(ax=rax, pct=resid_pct, **resid_kwargs)

        #         if fit_resid_axes is None:
        hax.xaxis.get_label().set_visible(False)
        [t.set_visible(False) for t in hax.xaxis.get_ticklabels()]

        return hax, rax

    def residuals(self, pct=False, robust=False):
        r"""Calculate the fit residuals.
        If pct, normalize by fit yvalues.
        """

        y_fit_used = self.y_fit[self.observations.tk_observed]

        if robust:
            r = self.fit_result.fun
        else:
            r = y_fit_used - self.observations.used.y

        if pct:
            r = 100.0 * (r / y_fit_used)

        return r

    #     def robust_residuals(self, pct=False):
    #         r"""Return the fit residuals.
    #         If pct, normalize by fit yvalues.
    #         """
    #         r = self._robust_residuals
    #
    #         if pct:
    #             y_fit_used = self.y_fit[self.observations.tk_observed]
    #             r = 100.0 * (r / y_fit_used)
    #
    #         return r

    def set_labels(self, **kwargs):
        r"""Set or update x, y, or z labels. Any label not specified in kwargs
        is propagated from `self.labels.<x, y, or z>`.
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
        self._TeX_info = new
