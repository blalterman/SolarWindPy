# Spent-When: MARKED(tests/plotting/_legacy/beta_ani.py)
# Supersedes: none
# Legacy oracle: verbatim copy of solarwindpy/instabilities/beta_ani.py at commit 4bc1c08eb5c610151e9a4905cdb171dc26202653.
# Only the imports are rewritten; see tests/plotting/_legacy/__init__.py.
"""Convenience plotting helpers for anisotropy versus beta."""

__all__ = ["BetaRPlot"]


from .hist2d import Hist2D
from solarwindpy.plotting.labels.base import TeXlabel


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
    >>> import numpy as np
    >>> import pandas as pd
    >>> import matplotlib.pyplot as plt
    >>> rng = np.random.default_rng(0)
    >>> beta = pd.Series(10.0 ** rng.uniform(-1, 1, 500), name="beta")
    >>> ani = pd.Series(10.0 ** rng.uniform(-0.5, 0.5, 500), name="ani")
    >>> br = BetaRPlot(beta, ani, "p")
    >>> ax, cbar = br.make_plot()
    >>> ax.get_xscale(), ax.get_yscale()
    ('log', 'log')
    >>> plt.close("all")
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
            Additional options forwarded to
            :class:`~solarwindpy.plotting.hist2d.Hist2D`.
        """

        x = beta
        y = ani

        logx = kwargs.pop("logx", True)
        logy = kwargs.pop("logy", True)

        super(BetaRPlot, self).__init__(x, y, logx=logx, logy=logy, **kwargs)
        self.set_labels(
            x=TeXlabel(("beta", "par", species.replace("_bimax", ""))),
            y=TeXlabel(
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

# Spent-Mark: served; migration green under two seeds incl. real Spiral agg and drawn comparisons (d3390351); real-data comparison 90 of 90 cell-14 h2_set histograms identical on 12 objects, old vs new and shared BinnedData+mask (Session C, snapshot 6578e94a), with author-reviewed figures; condition-3 coverage audit closed by d3390351
