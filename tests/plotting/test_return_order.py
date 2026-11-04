# Spent-When: PERMANENT(plot draw methods stop sharing one return order)
# Supersedes: none
"""Every plot's draw method returns its handles in one fixed order.

The order is the axis first, then the primary artists, then the colorbar,
which is None when there is none: ``(ax, artists..., cbar_or_None)``. A
contour method returns its contour set as the last artist, just before the
colorbar. A method's tuple has the same length and the same type in each
position whether or not a colorbar is drawn, whether a Scatter has z, and
whether a Hist1D draws its uncertainty window.
"""

from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.collections import (  # noqa: E402
    PathCollection,
    PolyCollection,
    QuadMesh,
)
from matplotlib.colorbar import Colorbar  # noqa: E402
from matplotlib.container import ErrorbarContainer  # noqa: E402
from matplotlib.contour import ContourSet  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from solarwindpy.instabilities.beta_ani import BetaRPlot  # noqa: E402
from solarwindpy.plotting.hist1d import Hist1D  # noqa: E402
from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402
from solarwindpy.plotting.scatter import Scatter  # noqa: E402
from solarwindpy.plotting.spiral import SpiralPlot2D  # noqa: E402
from solarwindpy.solar_activity.plots import IndicatorPlot  # noqa: E402

ORDER = "draw methods return (ax, cbar_or_mappable[, qset]) or no artist"

RNG = np.random.default_rng(11)
N = 2000
X = pd.Series(10.0 ** RNG.normal(1, 0.3, N))
Y = pd.Series(10.0 ** RNG.normal(1, 0.3, N))
Z = pd.Series(RNG.uniform(1, 2, N))
NONE = type(None)


class LinePlot(IndicatorPlot):
    """The generic indicator plotter, with its base axis format."""

    def _format_axis(self, ax):
        return super()._format_axis(ax)


def _indicator_plot():
    index = pd.date_range("2000-01-01", periods=12, freq="MS")
    data = pd.DataFrame({"ssn": np.arange(12.0)}, index=index)
    return LinePlot(SimpleNamespace(data=data), "ssn")


@pytest.fixture(autouse=True)
def _close():
    yield
    plt.close("all")


# (id, build, method, kwargs, artist types). The colorbar slot is checked
# separately, so the artist types are the positions between ax and it.
COLOR_CASES = [
    ("Hist2D.make_plot", lambda: Hist2D(X, Y), "make_plot", {}, (QuadMesh,)),
    (
        "Hist2D.plot_hist_with_contours",
        lambda: Hist2D(X, Y, nbins=11),
        "plot_hist_with_contours",
        {},
        (QuadMesh, ContourSet),
    ),
    (
        "Hist2D.plot_contours",
        lambda: Hist2D(X, Y, nbins=11),
        "plot_contours",
        {},
        (ContourSet,),
    ),
    (
        "BetaRPlot.make_plot",
        lambda: BetaRPlot(X, Y, "p"),
        "make_plot",
        {},
        (QuadMesh,),
    ),
    (
        "SpiralPlot2D.make_plot",
        lambda: SpiralPlot2D(X, Y, min_per_bin=100),
        "make_plot",
        {},
        (PolyCollection,),
    ),
    (
        "SpiralPlot2D.plot_contours",
        lambda: SpiralPlot2D(X, Y, min_per_bin=100),
        "plot_contours",
        {},
        (ContourSet,),
    ),
    (
        "Scatter.make_plot-z",
        lambda: Scatter(X, Y, Z),
        "make_plot",
        {},
        (PathCollection,),
    ),
]


@pytest.mark.xfail(strict=True, reason=ORDER)
@pytest.mark.parametrize("cbar", [True, False], ids=["cbar", "no-cbar"])
@pytest.mark.parametrize(
    "build, method, kwargs, artists",
    [pytest.param(*c[1:], id=c[0]) for c in COLOR_CASES],
)
def test_color_plot_returns_ax_then_artists_then_cbar_or_none(
    build, method, kwargs, artists, cbar
):
    """``(ax, artists..., cbar)``; the last slot is None when no colorbar is drawn.

    ON FAILURE: the code is wrong.
    """
    out = getattr(build(), method)(cbar=cbar, **kwargs)
    assert isinstance(out, tuple)
    assert len(out) == len(artists) + 2
    assert isinstance(out[0], Axes)
    for got, kind in zip(out[1:-1], artists):
        assert isinstance(got, kind)
    assert isinstance(out[-1], Colorbar if cbar else NONE)


@pytest.mark.xfail(strict=True, reason=ORDER)
def test_scatter_without_z_returns_its_collection_and_no_colorbar():
    """A Scatter without z keeps the same shape: its collection, then None.

    ON FAILURE: the code is wrong.
    """
    out = Scatter(X, Y).make_plot()
    assert len(out) == 3
    assert isinstance(out[0], Axes)
    assert isinstance(out[1], PathCollection)
    assert out[2] is None


@pytest.mark.xfail(strict=True, reason=ORDER)
@pytest.mark.parametrize(
    "kwargs, line, band",
    [
        ({}, ErrorbarContainer, NONE),
        ({"fcn": ("mean", "std"), "plot_window": True}, Line2D, PolyCollection),
    ],
    ids=["errorbar", "window"],
)
def test_hist1d_returns_ax_line_band_then_none(kwargs, line, band):
    """``(ax, line, band, None)``: the band is None without ``plot_window``.

    Hist1D draws no colorbar, so its colorbar slot is always None.

    ON FAILURE: the code is wrong.
    """
    plot = Hist1D(X, Y) if "fcn" in kwargs else Hist1D(X)
    out = plot.make_plot(**kwargs)
    assert isinstance(out, tuple)
    assert len(out) == 4
    assert isinstance(out[0], Axes)
    assert isinstance(out[1], line)
    assert isinstance(out[2], band)
    assert out[3] is None


@pytest.mark.xfail(strict=True, reason=ORDER)
def test_indicator_plot_returns_ax_line_then_none():
    """``(ax, line, None)``: an indicator plot draws no colorbar.

    ON FAILURE: the code is wrong.
    """
    out = _indicator_plot().make_plot()
    assert isinstance(out, tuple)
    assert len(out) == 3
    assert isinstance(out[0], Axes)
    assert isinstance(out[1], Line2D)
    assert out[2] is None
