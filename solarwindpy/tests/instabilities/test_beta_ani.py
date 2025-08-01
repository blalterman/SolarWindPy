import matplotlib
import pandas as pd
from solarwindpy.instabilities.beta_ani import BetaRPlot

matplotlib.use("Agg")


def test_beta_r_plot_make_plot():
    beta = pd.Series([0.1, 1.0, 10.0])
    ani = pd.Series([1.1, 0.9, 1.3])
    plot = BetaRPlot(beta, ani, "p")
    ax, cbar = plot.make_plot()
    from matplotlib.axes import Axes
    from matplotlib.colorbar import Colorbar

    assert isinstance(ax, Axes)
    assert isinstance(cbar, Colorbar)
