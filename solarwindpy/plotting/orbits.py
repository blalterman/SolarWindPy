#!/usr/bin/env python
r"""Aggregate, create, and save 1D and 2D plots for orbits.
"""

import pdb  # noqa: F401

import numpy as np
import pandas as pd
import matplotlib as mpl

from abc import ABC

from . import histograms
from . import tools


class OrbitPlot(ABC):
    def __init__(self, orbit, *args, **kwargs):
        self.set_orbit(orbit)
        super(OrbitPlot, self).__init__(*args, **kwargs)

    @property
    def orbit(self):
        return self._orbit

    @property
    def _orbit_key(self):
        r"""Central property for defining the name "Orbit"
        for use in various methods.
        """
        return "Orbit"

    @property
    def grouped(self):
        r"""`joint.groupby` with appropriate axes passes.
        """
        gb = self.joint.groupby(list(self._gb_axes) + [self._orbit_key])
        return gb

    def set_orbit(self, new):
        r"""`IntervalIndex` corresponding to the times we want to subset the orbit.
        """
        if not isinstance(new, pd.IntervalIndex):
            raise TypeError
        self._orbit = new.sort_values()

    def make_cut(self):
        super(OrbitPlot, self).make_cut()
        cut = self.cut

        time = pd.cut(self.data.index, self.orbit)

        # Workaround for `labels=["inbound", "outbound"]` not working above. (20190605)
        time = time.map({self.orbit[0]: "Inbound", self.orbit[1]: "Outbound"})
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

        x = pd.IntervalIndex(agg.index).mid
        if self.log.x:
            x = 10.0 ** x

        drawstyle = kwargs.pop("drawstyle", "steps-mid")
        for k, v in agg.items():
            ax.plot(x, v, drawstyle=drawstyle, label=k, **kwargs)

        self._format_axis(ax)

        return ax


class OrbitHist2D(OrbitPlot, histograms.Hist2D):
    def __init__(self, orbit, x, y, **kwargs):
        super(OrbitHist2D, self).__init__(orbit, x, y, **kwargs)

    def _format_axes(self, axes):
        for ax in axes:
            self._format_axis(ax)

        inbound = axes.loc["Inbound"]
        outbound = axes.loc["Outbound"]
        x0, x1 = outbound.get_xlim()
        inbound.set_xlim(x1, x0)
        #         outbound.set_xlim(x0, x1)
        outbound.yaxis.label.set_visible(False)

        sin = inbound.spines["right"]
        sout = outbound.spines["left"]
        for spine in (sin, sout):
            spine.set_edgecolor("cyan")
            spine.set_linewidth(2.5)

    def agg(self, **kwargs):
        agg = super(OrbitHist2D, self).agg(**kwargs)
        grouped = agg.groupby(self._orbit_key)
        transformed = grouped.transform(self._axis_normalizer)
        return transformed

    def make_plot(
        self,
        axes=None,
        fcn=None,
        cbar=True,
        limit_color_norm=False,
        cbar_kwargs=None,
        **kwargs
    ):
        r"""Make a plot on `ax`.

        If `ax` is None, create a `mpl.subplots` axis.

        `**kwargs` passed directly to `ax.plot`.

        `drawstyle` defaults to `steps-mid`

        `fcn` passed to `self.agg`. Only one function is allow b/c we
        don't yet handle uncertainties.
        """
        if axes is None:
            fig, axes = tools.subplots(
                ncols=2, gridspec_kw=dict(wspace=0), sharex=False, sharey=True
            )

        x = self.edges["x"]
        y = self.edges["y"]

        if self.log.x:
            x = 10.0 ** x
        if self.log.y:
            y = 10.0 ** y

        XX, YY = np.meshgrid(x, y)

        axnorm = self.axnorm
        norm = kwargs.pop(
            "norm", mpl.colors.Normalize(0, 1) if axnorm in ("c", "r") else None
        )

        if limit_color_norm:
            self._limit_color_norm(norm)

        agg = self.agg(fcn=fcn)
        orbit_keys = agg.index.get_level_values(self._orbit_key).unique()
        gb = agg.groupby(self._orbit_key)

        axes = pd.Series(axes, index=orbit_keys)
        for k, v in gb:
            ax = axes.loc[k]
            v = v.unstack("x")
            C = np.ma.masked_invalid(v.values)
            pc = ax.pcolormesh(XX, YY, C, norm=norm, **kwargs)

        if cbar:
            if cbar_kwargs is None:
                cbar_kwargs = dict()
            cbar = self._make_cbar(pc, axes.values, **cbar_kwargs)

        self._format_axes(axes)

        return axes, cbar
