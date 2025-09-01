#!/usr/bin/env python
r"""Plotting helpers specialized for solar wind orbits."""

import pdb  # noqa: F401

import numpy as np
import pandas as pd
import matplotlib as mpl

from abc import ABC

from . import histograms
from . import tools

# import logging

# from . import labels

# import os
# import psutil

# def log_mem_usage():
#    usage = psutil.Process(os.getpid()).memory_info()
#    usage = "\n".join(
#        ["{} {:.3f} GB".format(k, v * 1e-9) for k, v in usage._asdict().items()]
#    )
#    logging.getLogger("main").warning("Memory usage\n%s", usage)


class OrbitPlot(ABC):
    def __init__(self, orbit, *args, **kwargs):
        self.set_orbit(orbit)
        super(OrbitPlot, self).__init__(*args, **kwargs)

    @property
    def _disable_both(self):
        return True

    @property
    def orbit(self):
        return self._orbit

    @property
    def _orbit_key(self):
        r"""Central property for defining the name "Orbit".

        for use in various methods.
        """
        return "Orbit"

    @property
    def grouped(self):
        r"""`joint.groupby` with appropriate axes passes."""
        gb = self.joint.groupby(list(self._gb_axes) + [self._orbit_key])
        return gb

    def set_path(self, *args, orbit=None, **kwargs):
        r"""Set path information, accounting for orbit info."""
        super(OrbitPlot, self).set_path(*args, **kwargs)
        if orbit is not None:
            self._path = self.path / orbit.path

    def set_orbit(self, new):
        r"""`IntervalIndex` corresponding to the times we want to subset the orbit."""
        if not isinstance(new, pd.IntervalIndex):
            raise TypeError
        self._orbit = new.sort_values()

    def make_cut(self):
        super(OrbitPlot, self).make_cut()
        cut = self.cut

        time = pd.cut(self.data.index, self.orbit)

        time = time.map({self.orbit[0]: "Inbound", self.orbit[1]: "Outbound"}).astype(
            "category"
        )

        if not self._disable_both:
            time.add_categories("Both", inplace=True)

        # `name` must be distinct from `Epoch` or we end up with ambiguous group keys.
        time = pd.Series(time, index=self.data.index, name=self._orbit_key)
        cut = pd.concat([cut, time], axis=1).sort_index(axis=1)
        self._cut = cut


class OrbitHist1D(OrbitPlot, histograms.Hist1D):
    def __init__(self, orbit, x, **kwargs):
        super(OrbitHist1D, self).__init__(orbit, x, **kwargs)

    def _format_axis(self, ax):
        super(OrbitHist1D, self)._format_axis(ax)
        ax.legend(loc=0, ncol=1, framealpha=0)

    def agg(self, **kwargs):
        fcn = kwargs.pop("fcn", None)
        agg = super(OrbitHist1D, self).agg(fcn=fcn, **kwargs)

        if not self._disable_both:
            cut = self.cut.drop("Orbit", axis=1)
            tko = self.agg_axes
            gb_both = self.joint.drop("Orbit", axis=1).groupby(list(self._gb_axes))
            agg_both = self._agg_runner(cut, tko, gb_both, fcn).copy(deep=True)

            agg = agg.unstack("Orbit")
            agg_both = pd.concat({"Both": agg_both}, axis=1, names=["Orbit"])
            if agg_both.columns.nlevels == 2:
                agg_both = agg_both.swaplevel(0, 1, 1)

            agg = (
                pd.concat([agg, agg_both], axis=1)
                .sort_index(axis=1)
                .stack("Orbit")
                .sort_index(axis=0)
            )

        #         for k, v in self.intervals.items():
        #             # if > 1 intervals, pass level. Otherwise, don't as this raises a NotImplementedError. (20190619)
        #             agg = agg.reindex(index=v, level=k if agg.index.nlevels > 1 else None)

        return agg

    def make_plot(self, ax=None, fcn=None, **kwargs):
        r"""Make a plot on `ax`.

        If `ax` is None, create a `mpl.subplots` axis.

        `**kwargs` passed directly to `ax.plot`.

        `drawstyle` defaults to `steps-mid`

        `fcn` passed to `self.agg`. Only one function is allow b/c we
        don't yet handle uncertainties.
        """
        if ax is None:
            fig, ax = tools.subplots()

        agg = self.agg(fcn=fcn).unstack(self._orbit_key)
        agg = agg.reindex(index=self.intervals["x"])

        x = pd.IntervalIndex(agg.index).mid
        if self.log.x:
            x = 10.0**x

        drawstyle = kwargs.pop("drawstyle", "steps-mid")
        for k, v in agg.items():
            ax.plot(x, v, drawstyle=drawstyle, label=k, **kwargs)

        self._format_axis(ax)

        return ax


class OrbitHist2D(OrbitPlot, histograms.Hist2D):
    def __init__(self, orbit, x, y, **kwargs):
        super(OrbitHist2D, self).__init__(orbit, x, y, **kwargs)

    def _format_in_out_axes(self, inbound, outbound):
        #         logging.getLogger("main").warning("Formatting in out axes")
        #         log_mem_usage()

        xlim = np.concatenate([inbound.get_xlim(), outbound.get_xlim()])
        x0 = xlim.min()
        x1 = xlim.max()
        #         x0, x1 = outbound.get_xlim()
        inbound.set_xlim(x1, x0)
        outbound.set_xlim(x0, x1)
        outbound.yaxis.label.set_visible(False)

        # Make the Inbound/Outbound transition cyan.
        sin = inbound.spines["right"]
        sout = outbound.spines["left"]
        for spine in (sin, sout):
            spine.set_edgecolor("cyan")
            spine.set_linewidth(2.5)

        # TODO: Get top and bottom axes to line up without `tight_layout`, which
        #       puts colorbar into an unusable location.

    #         for k, ax in axes.items():
    #             au = 1.49597871e+11 # [m]
    #             rs = 695700000 # [m]
    #             conversion = au/rs
    #             if self.labels.x == labels.special.Distance2Sun("Rs"):
    #                 tax = ax.twiny()
    #                 tax.grid(False)
    #                 tax.set_xlim(* (np.array(ax.get_xlim()) / conversion))
    #                 tax.set_xlabel(labels.special.Distance2Sun("AU"))

    @staticmethod
    def _prune_lower_yaxis_ticks(ax0, ax1):
        nbins = ax0.get_yticks().size - 1
        for ax in (ax0, ax1):
            if ax.get_yscale() == "linear":
                ax.yaxis.set_major_locator(
                    mpl.ticker.MaxNLocator(nbins=nbins, prune="lower")
                )

    def _format_in_out_both_axes(self, axi, axo, axb, cbari, cbaro, cbarb):
        #         logging.getLogger("main").warning("Formatting in out both axes")
        #         log_mem_usage()

        ylim = np.concatenate([axi.get_ylim(), axi.get_ylim(), axb.get_ylim()])
        y0 = ylim.min()
        y1 = ylim.max()
        for ax in (axi, axo, axb):
            ax.set_ylim(y0, y1)

        # TODO: annotate Inbound and Outbound? Might be handled by TrendFitter
        self._prune_lower_yaxis_ticks(axi, axo)

        if not self.log.y:
            self._prune_lower_yaxis_ticks(cbari.ax, cbaro.ax)

    def agg(self, **kwargs):
        r"""Wrap Hist1D and Hist2D `agg` so that we can aggergate orbit legs.

        Legs: Inbound, Outbound, and Both."""
        #         logging.getLogger("main").warning("Starting agg")
        #         log_mem_usage()

        fcn = kwargs.pop("fcn", None)
        agg = super(OrbitHist2D, self).agg(fcn=fcn, **kwargs)

        #         logging.getLogger("main").warning("Running Both agg")
        #         log_mem_usage()

        if not self._disable_both:
            cut = self.cut.drop("Orbit", axis=1)
            tko = self.agg_axes
            gb_both = self.joint.drop("Orbit", axis=1).groupby(list(self._gb_axes))
            agg_both = self._agg_runner(cut, tko, gb_both, fcn).copy(deep=True)

            agg = agg.unstack("Orbit")
            agg_both = pd.concat({"Both": agg_both}, axis=1, names=["Orbit"])
            if agg_both.columns.nlevels == 2:
                agg_both = agg_both.swaplevel(0, 1, 1)

            agg = (
                pd.concat([agg, agg_both], axis=1)
                .sort_index(axis=1)
                .stack("Orbit")
                .sort_index(axis=0)
            )

        #         for k, v in self.intervals.items():
        #             # if > 1 intervals, pass level. Otherwise, don't as this raises a NotImplementedError. (20190619)
        #             agg = agg.reindex(index=v, level=k if agg.index.nlevels > 1 else None)

        #         logging.getLogger("main").warning("Grouping agg for axis normalization")
        #         log_mem_usage()

        grouped = agg.groupby(self._orbit_key)
        transformed = grouped.transform(self._axis_normalizer)
        return transformed

    def project_1d(self, axis, project_counts=False, **kwargs):
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

        data = self.data

        if data.loc[:, "z"].unique().size >= 2:
            # Either all 1 or 1 and NaN.
            other = "z"
        else:
            possible_axes = {"x", "y"}
            possible_axes.remove(axis)
            other = possible_axes.pop()

        logx = self.log._asdict()[axis]
        x = self.data.loc[:, axis]
        if logx:
            # Need to convert back to regular from log-space for data setting.
            x = 10.0**x

        y = self.data.loc[:, other] if not project_counts else None
        if y is not None:
            # Only select y-values plotted.
            logy = self.log._asdict()[other]
            yedges = self.edges[other].values
            y = y.where((yedges[0] <= y) & (y <= yedges[-1]))
            if logy:
                y = 10.0**y

        h1 = OrbitHist1D(
            self.orbit,
            x,
            y=y,
            logx=logx,
            clip_data=False,  # Any clipping will be addressed by bins.
            nbins=self.edges[axis].values,
            **kwargs,
        )
        h1.set_labels(x=self.labels._asdict()[axis], y=self.labels._asdict()[other])
        h1.set_path("auto")

        return h1

    def _put_agg_on_ax(self, ax, agg, cbar, limit_color_norm, cbar_kwargs, **kwargs):
        r"""Refactored putting `agg` onto `ax`.

        Python was crashing due to the way too many `agg` runs (20190731)."""
        #         logging.getLogger("main").warning("Putting agg on ax")
        #         log_mem_usage()

        x = self.edges["x"]
        y = self.edges["y"]

        if self.log.x:
            x = 10.0**x
        if self.log.y:
            y = 10.0**y

        XX, YY = np.meshgrid(x, y)

        axnorm = self.axnorm
        norm = kwargs.pop(
            "norm", mpl.colors.Normalize(0, 1) if axnorm in ("c", "r") else None
        )

        #         pdb.set_trace()

        if limit_color_norm:
            self._limit_color_norm(norm)

        #         logging.getLogger("main").warning("Reindexing agg on ax")
        #         log_mem_usage()

        # Unstacking drops some NaN bins, so we must reindex again.
        agg = agg.reindex(index=self.intervals["y"], columns=self.intervals["x"])

        #         logging.getLogger("main").warning("Do the plotting")
        #         log_mem_usage()

        C = np.ma.masked_invalid(agg.values)
        pc = ax.pcolormesh(XX, YY, C, norm=norm, **kwargs)

        if cbar:
            if cbar_kwargs is None:
                cbar_kwargs = dict()
            #             use_gridspec = kwargs.pop("use_gridspec", False)
            cbar = self._make_cbar(pc, ax, **cbar_kwargs)

        self._format_axis(ax)

        #         logging.getLogger("main").warning("Done putting agg on axis")
        #         log_mem_usage()

        return cbar

    def make_one_plot(
        self,
        kind,
        ax=None,
        fcn=None,
        cbar=True,
        limit_color_norm=False,
        cbar_kwargs=None,
        **kwargs,
    ):
        r"""Make one of "Inbound", "Outbound", or "Both" plots on `ax`.

        If `ax` is None, create a `mpl.subplots` axis.

        `**kwargs` passed directly to `ax.plot`.

        `drawstyle` defaults to `steps-mid`

        `fcn` passed to `self.agg`. Only one function is allow b/c we
        don't yet handle uncertainties.

        Viable kinds are:
            ========== ==================
               kind     allowable inputs
            ========== ==================
             Inbound    Inbound, I, i
             Outbound   Outbound, O, o
             Both       Both, B, b
            ========== ==================
        """
        trans = {"i": "Inbound", "o": "Outbound", "b": "Both"}
        try:
            kind = trans[kind.lower()[0]]
        except KeyError:
            raise ValueError("Unrecognized kind '{}'".format(kind))

        if kind == "Both" and self._disable_both:
            raise NotImplementedError(
                "Disabled both to prevent double linked list kernel crash"
            )

        if ax is None:
            fig, ax = tools.subplots()

        agg = self.agg(fcn=fcn).xs(kind, axis=0, level="Orbit").unstack("x")
        cbar = self._put_agg_on_ax(
            ax, agg, cbar, limit_color_norm, cbar_kwargs, **kwargs
        )

        return ax, cbar

    def make_in_out_plot(
        self, fcn=None, cbar=True, limit_color_norm=False, cbar_kwargs=None, **kwargs
    ):
        r"""Plot "Inbound" and "Outbound" on axes joined at perihelion.

        If `ax` is None, create a `mpl.subplots` axis.

        `**kwargs` passed directly to `ax.plot`.

        `drawstyle` defaults to `steps-mid`

        `fcn` passed to `self.agg`. Only one function is allow b/c we
        don't yet handle uncertainties.
        """
        fig, axes = tools.subplots(
            ncols=2, gridspec_kw=dict(wspace=0), sharex=False, sharey=True
        )

        agg = self.agg(fcn=fcn)
        aggi = agg.xs("Inbound", axis=0, level="Orbit").unstack("x")
        aggo = agg.xs("Outbound", axis=0, level="Orbit").unstack("x")

        cbari = self._put_agg_on_ax(
            axes[0], aggi, False, limit_color_norm, cbar_kwargs, **kwargs
        )
        cbaro = self._put_agg_on_ax(
            axes[1], aggo, cbar, limit_color_norm, cbar_kwargs, **kwargs
        )

        self._format_in_out_axes(*axes)

        # For the sake of legacy code. (20190731)
        axes = pd.Series(axes, index=("Inbound", "Outbound"))
        cbars = pd.Series([cbari, cbaro], index=("Inbound", "Outbound"))
        #         logging.getLogger("main").warning("Done with plot")
        #         log_mem_usage()

        return axes, cbars

    def make_in_out_both_plot(
        self, fcn=None, cbar=True, limit_color_norm=False, cbar_kwargs=None, **kwargs
    ):
        r"""Plot "Inbound", "Outbound", and "Both" on stacked axes.

        If `ax` is None, create a `mpl.subplots` axis.

        `**kwargs` passed directly to `ax.plot`.

        `drawstyle` defaults to `steps-mid`

        `fcn` passed to `self.agg`. Only one function is allow b/c we
        don't yet handle uncertainties.
        """

        if self._disable_both:
            raise NotImplementedError(
                "Disabled to attempt removing double-linked list kernel crash"
            )

        fig, axes = tools.subplots(
            nrows=3,
            gridspec_kw=dict(wspace=0, hspace=0),
            sharex=True,
            sharey=False,  # Can't `sharey`, because prevents pruning Inbound and Outbound lower y-ticks.
        )

        agg = self.agg(fcn=fcn)
        aggi = agg.xs("Inbound", axis=0, level="Orbit").unstack("x")
        aggo = agg.xs("Outbound", axis=0, level="Orbit").unstack("x")
        aggb = agg.xs("Both", axis=0, level="Orbit").unstack("x")

        cbar = kwargs.pop("cbar", True)

        axi, axo, axb = axes
        cbari = self._put_agg_on_ax(
            axi, aggi, cbar, limit_color_norm, cbar_kwargs, **kwargs
        )
        cbaro = self._put_agg_on_ax(
            axo, aggo, cbar, limit_color_norm, cbar_kwargs, **kwargs
        )
        cbarb = self._put_agg_on_ax(
            axb, aggb, cbar, limit_color_norm, cbar_kwargs, **kwargs
        )

        #         axi, cbari = self.make_one_plot("Inbound", axes[0], **kwargs)
        #         axo, cbaro = self.make_one_plot("Outbound", axes[1], **kwargs)
        #         axb, cbarb = self.make_one_plot("Both", axes[2], **kwargs)

        #         self._format_joint_axes(*axes)
        self._format_in_out_both_axes(axi, axo, axb, cbari, cbaro, cbarb)

        # For the sake of legacy code. (20190731)
        axes = pd.Series(axes, index=("Inbound", "Outbound", "Both"))
        cbars = pd.Series([cbari, cbaro, cbarb], index=("Inbound", "Outbound", "Both"))

        #         logging.getLogger("main").warning("Done with plot")
        #         log_mem_usage()

        return axes, cbars
