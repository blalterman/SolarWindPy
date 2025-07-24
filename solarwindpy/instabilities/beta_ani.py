__all__ = ["BetaRPlot"]


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
                # axnorm: "t"
        """
        x = beta
        y = ani

        logx = kwargs.pop("logx", True)
        logy = kwargs.pop("logy", True)

        super(BetaRPlot, self).__init__(x, y, logx=logx, logy=logy, **kwargs)
        self.set_labels(
            x=swp.pp.labels.TeXlabel(("beta", "par", species.replace("_bimax", ""))),
            y=swp.pp.labels.TeXlabel(
                ("R", "P" if "+" in species else "T", species.replace("_bimax", ""))
            ),
        )

        self.set_path("auto")
        self.set_clim(5, None)

    def make_plot(self, **kwargs):
        cmap = kwargs.pop("cmap", "Greens_r")
        ax, cbar = super(BetaRPlot, self).make_plot(cmap=cmap, **kwargs)

        return ax, cbar
