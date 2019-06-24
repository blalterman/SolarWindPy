__all__ = ["BetaRPlot"]

import pandas as pd
import numpy as np

from scipy.signal import savgol_filter
from collections import namedtuple

import solarwindpy as swp


class BetaRPlot(swp.plotting.histograms.Hist2D):
    def __init__(self, beta, ani, species, **kwargs):
        r"""Make a :math:`(\beta, R)` anisotropy plot.

        Default to a minimum of 5 counts/bin

        Parameters
        ----------
        beta, ani: pd.Series

        species: str
            Sets the species in the x-axis and y-axis labels.

        kwargs:
            Passed to :pyclass:`swp.plotting.histograms.Hist2D`.
            Defaults
                logx: True
                logy: True
                axnorm: "t"
        """
        #         x = plasma.beta(species).par
        #         y = plasma.anisotropy(species)

        #         tk = plasma.n("p2") > 1e-5
        #         tk = tk & (~plasma.n("p2", skipna=False).isna())
        #         tk = tk & (y > 1e-2) & (y < 1e2) & (x > 1e-2) & (x < 1e2)

        #         if species == "p1":
        #             tk = tk & (~plasma.aux.swapped_protons)

        #         tk = tk.where(tk).dropna().index

        x = beta  # x.loc[tk]
        y = ani  # y.loc[tk]

        logx = kwargs.pop("logx", True)
        logy = kwargs.pop("logy", True)
        axnorm = kwargs.pop("axnorm", "t")

        super(BetaRPlot, self).__init__(x, y, logx=logx, logy=logy, axnorm=axnorm)
        self.set_labels(
            x=swp.pp.labels.TeXlabel(("beta", "par", species.replace("_bimax", ""))),
            y=swp.pp.labels.TeXlabel(
                ("R", "P" if "+" in species else "T", species.replace("_bimax", ""))
            ),
        )

        self.set_path("auto")
        self.set_clim(5, None)

    def get_edges(self):
        r"""Get the top and bottom edges of the plot.

        Returns
        -------
        edges: namedtuple
            Contains "top" and "bottom" fields, each with a :py:class:`pd.Series`.
        """

        Edges = namedtuple("Edges", "top,bottom")
        top = {}
        bottom = {}
        for x, v in self.agg().unstack("x").items():
            yt = v.last_valid_index()
            if yt is not None:
                z = v.loc[yt]
                top[(yt, x)] = z

            yb = v.first_valid_index()
            if yb is not None:
                z = v.loc[yb]
                bottom[(yb, x)] = z

        top = pd.Series(top)
        bottom = pd.Series(bottom)
        for edge in (top, bottom):
            edge.index.names = ["y", "x"]

        edges = Edges(top, bottom)
        return edges

    @staticmethod
    def _plot_one_edge(ax, edge, smooth=False, sg_kwargs=None, **kwargs):
        x = edge.index.get_level_values("x").mid
        y = edge.index.get_level_values("y").mid

        if sg_kwargs is None:
            sg_kwargs = dict()

        if smooth:
            wlength = sg_kwargs.pop("window_length", int(np.floor(y.shape[0] / 10)))
            polyorder = sg_kwargs.pop("polyorder", 3)

            if not wlength % 2:
                wlength -= 1

            y = savgol_filter(y, wlength, polyorder, **sg_kwargs)

        x = 10.0 ** x
        y = 10.0 ** y
        return ax.plot(x, y, **kwargs)

    def plot_edges(self, ax, smooth=False, sg_kwargs=None, **kwargs):
        r"""Overplot the edges.

        Parameters
        ----------
        ax:
            Axis on which to plot.
        smooth: bool
            If True, apply a Savitzky-Golay filter (:py:func:`scipy.signal.savgol_filter`)
            to the y-values before plotting to smooth the curve.
        sg_kwargs: dict, None
            If not None, dict of kwargs passed to Savitzky-Golay filter. Also allows
            for setting of `window_length` and `polyorder` as kwargs. They default to
            10\% of the number of observations (`window_length`) and 3 (`polyorder`).
            Note that because `window_length` must be odd, if the 10\% value is even, we
            take 1-window_length.
        kwargs:
            Passed to `ax.plot`
        """

        top, bottom = self.get_edges()

        color = kwargs.pop("color", "cyan")
        etop = self._plot_one_edge(ax, top, smooth, sg_kwargs, color=color, **kwargs)
        ebottom = self._plot_one_edge(
            ax, bottom, smooth, sg_kwargs, color=color, **kwargs
        )

        return etop, ebottom

    def make_plot(self, **kwargs):
        ax = kwargs.pop("ax", None)
        if ax is None:
            fig, ax = swp.pp.subplots(scale_width=1.5, scale_height=1.5)

        cmap = kwargs.pop("cmap", "Greens_r")
        ax, cbar = super(BetaRPlot, self).make_plot(ax=ax, cmap=cmap, **kwargs)

        return ax, cbar
