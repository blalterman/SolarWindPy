# Spent-When: PERMANENT(color plots stop choosing a default colour scale)
# Supersedes: none
"""Tests for the default colour scale of the colour plots.

When the plotted values hold both signs, a ``Hist2D``, ``SpiralPlot2D`` or
``Scatter`` defaults to a zero-centred norm (vcenter 0) and the diverging
colormap ``RdBu_r``. Values of one sign keep the defaults they had: a
``LogNorm`` for densities, colour bands on [0, 1] for row and column norms,
matplotlib's own otherwise. A ``norm`` or ``cmap`` the caller passes always
wins. Contours use the same default.
"""

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import (  # noqa: E402
    BoundaryNorm,
    CenteredNorm,
    LogNorm,
    Normalize,
)

from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402
from solarwindpy.plotting.scatter import Scatter  # noqa: E402
from solarwindpy.plotting.spiral import SpiralPlot2D  # noqa: E402

_NEW = pytest.mark.xfail(strict=True, reason="no signed default colour scale yet")

RNG = np.random.default_rng(4)
N = 3000
X = pd.Series(RNG.normal(size=N))
Y = pd.Series(RNG.normal(size=N))
SIGNED = pd.Series(RNG.normal(size=N))  # both signs in every cell's mean
POSITIVE = pd.Series(RNG.lognormal(size=N))


@pytest.fixture(autouse=True)
def _close():
    yield
    plt.close("all")


def _centred(mappable):
    norm = mappable.norm
    return isinstance(norm, (CenteredNorm,)) and norm.vcenter == 0


def _hist2d(z, **kw):
    return Hist2D(X, Y, z, nbins=12, **kw)


def _spiral(z):
    return SpiralPlot2D(X, Y, z, initial_bins=4, min_per_bin=100)


@_NEW
@pytest.mark.parametrize("axnorm", [None, "t", "c", "d"])
def test_hist2d_of_signed_values_gets_a_centred_diverging_scale(axnorm):
    """Signed means get vcenter 0 and RdBu_r, whatever the axnorm.

    ON FAILURE: the code is wrong.
    """
    _, pc, _ = _hist2d(SIGNED, axnorm=axnorm).make_plot(cbar=False)
    assert _centred(pc)
    assert pc.get_cmap().name == "RdBu_r"


@_NEW
def test_spiral_and_scatter_of_signed_values_get_a_centred_scale():
    """The same default holds for a spiral mesh and for coloured points.

    ON FAILURE: the code is wrong.
    """
    _, collection, _ = _spiral(SIGNED).make_plot(cbar=False)
    assert _centred(collection)
    assert collection.get_cmap().name == "RdBu_r"
    _, points, _ = Scatter(X, Y, SIGNED).make_plot(cbar=False)
    assert _centred(points)
    assert points.get_cmap().name == "RdBu_r"


@_NEW
def test_contours_of_signed_values_get_a_centred_scale():
    """Hist2D and spiral contours default to the centred norm too.

    ON FAILURE: the code is wrong.
    """
    _, qset, *_ = _hist2d(SIGNED).plot_contours(cbar=False)
    assert _centred(qset)
    _, qset, _ = _spiral(SIGNED).plot_contours(cbar=False)
    assert _centred(qset)


@pytest.mark.parametrize(
    "axnorm, kind",
    [("c", BoundaryNorm), ("d", LogNorm), (None, Normalize)],
    ids=["c", "d", "none"],
)
def test_non_negative_values_keep_todays_defaults(axnorm, kind):
    """One-signed values keep the bands, the LogNorm, or matplotlib's default.

    ON FAILURE: the code is wrong.
    """
    _, pc, _ = _hist2d(POSITIVE, axnorm=axnorm).make_plot(cbar=False)
    assert type(pc.norm) is kind
    assert pc.get_cmap().name == plt.rcParams["image.cmap"]


@pytest.mark.parametrize(
    "build",
    [lambda: _hist2d(SIGNED), lambda: _spiral(SIGNED)],
    ids=["Hist2D", "SpiralPlot2D"],
)
def test_a_callers_norm_and_cmap_win(build):
    """An explicit norm and cmap are used as given, even for signed values.

    ON FAILURE: the code is wrong.
    """
    norm = Normalize(-0.5, 0.5)
    _, mappable, _ = build().make_plot(cbar=False, norm=norm, cmap="viridis")
    assert mappable.norm is norm
    assert mappable.get_cmap().name == "viridis"
