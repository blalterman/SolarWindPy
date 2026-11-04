"""Convenience plotting helpers for anisotropy versus beta."""

__all__ = ["BetaRPlot"]


from ..plotting.binned import BinnedData
from ..plotting.hist2d import Hist2D
from ..plotting.labels.base import TeXlabel


class BetaRPlot(Hist2D):
    """Generate a beta--anisotropy histogram.

    Parameters
    ----------
    beta : pandas.Series
        Proton parallel beta.
    R : pandas.Series
        Temperature anisotropy.
    species : str
        Label used to generate axis titles.
    **kwargs
        Additional options forwarded to ``Hist2D``. Unless ``nbins`` is a
        ``BinnedData``, the x- and y-axes default to logarithmic scaling;
        with one, ``logx`` and ``logy`` default to its settings.

    Examples
    --------
    >>> import numpy as np
    >>> import pandas as pd
    >>> import matplotlib.pyplot as plt
    >>> rng = np.random.default_rng(0)
    >>> beta = pd.Series(10.0 ** rng.uniform(-1, 1, 500), name="beta")
    >>> R = pd.Series(10.0 ** rng.uniform(-0.5, 0.5, 500), name="R")
    >>> br = BetaRPlot(beta, R, "p")
    >>> ax, cbar = br.make_plot()
    >>> ax.get_xscale(), ax.get_yscale()
    ('log', 'log')
    >>> plt.close("all")
    """

    def __init__(self, beta, R, species, **kwargs):
        """Instantiate the histogram plot.

        Parameters
        ----------
        beta : pandas.Series
            Proton parallel beta.
        R : pandas.Series
            Temperature anisotropy.
        species : str
            Label used to generate axis titles.
        **kwargs
            Additional options forwarded to
            :class:`~solarwindpy.plotting.hist2d.Hist2D`, e.g. ``nbins``,
            which may be a ``BinnedData`` holding columns named like ``beta``
            and ``R``, and ``mask``. ``logx`` and ``logy`` default to True,
            or, with a ``BinnedData``, to its settings for those columns.
        """

        x = beta
        y = R

        # A shared BinnedData sets the log of its columns; see Hist2D.
        default = None if isinstance(kwargs.get("nbins"), BinnedData) else True
        logx = kwargs.pop("logx", default)
        logy = kwargs.pop("logy", default)

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
