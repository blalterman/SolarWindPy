"""Convenience plotting helpers for anisotropy versus beta."""

__all__ = ["BetaRPlot"]

import pdb  # noqa: F401

from ..plotting.histograms import Hist2D
from ..plotting import labels


class BetaRPlot(Hist2D):
    """Generate a beta--anisotropy histogram.

    Parameters
    ----------
    beta : pandas.Series
        Proton parallel beta.
    ani : pandas.Series
        Temperature anisotropy.
    species : str
        Label used to generate axis titles.
    **kwargs
        Additional options forwarded to ``Hist2D``. By default the
        x- and y-axes use logarithmic scaling.

    Examples
    --------
    >>> br = BetaRPlot(beta, ani, "p")  # doctest: +SKIP
    >>> ax, cbar = br.make_plot()  # doctest: +SKIP
    """

    def __init__(self, beta, ani, species, **kwargs):
        """Instantiate the histogram plot.

        Parameters
        ----------
        beta : pandas.Series
            Proton parallel beta.
        ani : pandas.Series
            Temperature anisotropy.
        species : str
            Label used to generate axis titles.
        **kwargs
            Additional options forwarded to :class:`Hist2D`.
        """

        x = beta
        y = ani

        logx = kwargs.pop("logx", True)
        logy = kwargs.pop("logy", True)

        super(BetaRPlot, self).__init__(x, y, logx=logx, logy=logy, **kwargs)
        self.set_labels(
            x=labels.TeXlabel(("beta", "par", species.replace("_bimax", ""))),
            y=labels.TeXlabel(
                ("R", "P" if "+" in species else "T", species.replace("_bimax", ""))
            ),
        )

        self.set_path("auto")
        self.set_clim(5, None)

    def make_plot(self, **kwargs):
        """Plot the histogram.

        Parameters
        ----------
        **kwargs
            Additional options forwarded to ``Hist2D.make_plot``.

        Returns
        -------
        matplotlib.axes.Axes
            Axis containing the plot.
        matplotlib.colorbar.Colorbar
            Colorbar associated with the plot.
        """
        cmap = kwargs.pop("cmap", "Greens_r")
        ax, cbar = super(BetaRPlot, self).make_plot(cmap=cmap, **kwargs)

        return ax, cbar
