# Spent-When: PERMANENT(color plots stop choosing a default colour scale)
# Supersedes: none
"""Tests for the default colour scale of the colour plots.

When the plotted values hold both signs, a ``Hist2D``, ``SpiralPlot2D`` or
``Scatter`` defaults to a zero-centred norm (vcenter 0) and the diverging
colormap ``RdBu_r``. Values of one sign keep the defaults they had: a
``LogNorm`` for densities, colour bands on [0, 1] for row and column norms,
matplotlib's own otherwise. A ``norm`` or ``cmap`` the caller passes always
wins. Contours use the same default.

A ``ColorScale`` holds the same settings in one object: passed as
``color_scale``, it draws what the plain keywords draw, its unset norm
following the same defaults, and it refuses to be combined with them.
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
from solarwindpy.plotting.scales import ColorScale  # noqa: E402
from solarwindpy.plotting.scatter import Scatter  # noqa: E402
from solarwindpy.plotting.spiral import SpiralPlot2D  # noqa: E402

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


@pytest.mark.parametrize("axnorm", [None, "t", "c", "d"])
def test_hist2d_of_signed_values_gets_a_centred_diverging_scale(axnorm):
    """Signed means get vcenter 0 and RdBu_r, whatever the axnorm.

    ON FAILURE: the code is wrong.
    """
    _, pc, _ = _hist2d(SIGNED, axnorm=axnorm).make_plot(cbar=False)
    assert _centred(pc)
    assert pc.get_cmap().name == "RdBu_r"


def test_spiral_and_scatter_of_signed_values_get_a_centred_scale():
    """The same default holds for a spiral mesh and for coloured points.

    ON FAILURE: the code is wrong.
    """
    _, collection, _ = _spiral(SIGNED).make_plot(cbar=False)
    assert _centred(collection)
    assert collection.get_cmap().name == "RdBu_r"
    _, points, _, _ = Scatter(X, Y, SIGNED).make_plot(cbar=False)
    assert _centred(points)
    assert points.get_cmap().name == "RdBu_r"


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


# ---------------------------------------------------------------------------
# ColorScale: the colour settings as one object.
# ---------------------------------------------------------------------------

# One plotter per colour plot, built to colour the z it is given.
COLOR_PLOTS = {
    "Hist2D": lambda z: _hist2d(z),
    "SpiralPlot2D": lambda z: _spiral(z),
    "Scatter": lambda z: Scatter(X, Y, z),
}


@pytest.mark.parametrize(
    "settings, message",
    [
        ({"norm": 3}, "norm must be"),
        ({"cbar": 1}, "cbar must be"),
        ({"cbar_kwargs": [("shrink", 0.5)]}, "cbar_kwargs must be"),
    ],
    ids=["norm", "cbar", "cbar_kwargs"],
)
def test_color_scale_rejects_invalid_settings_when_built(settings, message):
    """A norm neither a Normalize nor a scale name, a non-bool cbar, or non-mapping kwargs raise.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(TypeError, match=message):
        ColorScale(**settings)


@pytest.mark.parametrize(
    "z, settings",
    [(SIGNED, lambda: {}), (POSITIVE, lambda: {"norm": LogNorm(), "cmap": "viridis"})],
    ids=["signed-defaults", "LogNorm-viridis"],
)
@pytest.mark.parametrize("plot", COLOR_PLOTS.values(), ids=COLOR_PLOTS.keys())
def test_color_scale_draws_what_its_plain_keywords_draw(plot, z, settings):
    """``color_scale=ColorScale(...)`` and the same plain keywords give one mapping.

    The norm (its class and limits), the colormap and the colour of every
    face handed to matplotlib match. With no norm and cmap set, both paths
    take the plot's defaults, here the centred scale of signed values.

    ON FAILURE: the code is wrong.
    """
    plain = plot(z).make_plot(cbar=False, **settings())[1]
    scaled = plot(z).make_plot(color_scale=ColorScale(cbar=False, **settings()))[1]
    assert type(scaled.norm) is type(plain.norm)
    assert (scaled.norm.vmin, scaled.norm.vmax) == (plain.norm.vmin, plain.norm.vmax)
    assert scaled.get_cmap().name == plain.get_cmap().name
    assert np.array_equal(
        scaled.to_rgba(scaled.get_array()), plain.to_rgba(plain.get_array())
    )


@pytest.mark.parametrize(
    "keyword",
    [{"norm": Normalize()}, {"cmap": "viridis"}, {"cbar": True}, {"cbar_kwargs": {}}],
    ids=["norm", "cmap", "cbar", "cbar_kwargs"],
)
@pytest.mark.parametrize("plot", COLOR_PLOTS.values(), ids=COLOR_PLOTS.keys())
def test_color_scale_with_a_plain_colour_keyword_raises_type_error(plot, keyword):
    """A ``color_scale`` beside ``norm``, ``cmap``, ``cbar`` or ``cbar_kwargs`` raises.

    Even ``cbar=True``, the value a colorbar is drawn with by default, is
    refused when given: the scale carries ``cbar``.

    ON FAILURE: the code is wrong.
    """
    (name,) = keyword
    with pytest.raises(TypeError, match=f"color_scale.*{name}"):
        plot(POSITIVE).make_plot(color_scale=ColorScale(), **keyword)


def test_color_scale_str_shows_the_limits_a_plot_set():
    """``print(scale)`` shows the vmin and vmax matplotlib filled in from the data.

    Chosen input: z = 2, 5, 9, so an unset ``Normalize`` autoscales to [2, 9].

    ON FAILURE: the code is wrong.
    """
    scale = ColorScale(norm=Normalize(), cmap="viridis")
    assert "norm: Normalize(vmin=None, vmax=None)" in str(scale)
    z = pd.Series([2.0, 5.0, 9.0])
    Scatter(z, z, z).make_plot(color_scale=scale)
    text = str(scale)
    assert "norm: Normalize(vmin=2, vmax=9)" in text
    assert "cmap: viridis" in text


@pytest.mark.parametrize("plot", COLOR_PLOTS.values(), ids=COLOR_PLOTS.keys())
def test_norm_given_as_a_scale_name_is_matplotlibs_norm_for_that_scale(plot):
    """``norm="log"`` colours with a ``LogNorm``, as matplotlib's scatter and pcolormesh do.

    ON FAILURE: the code is wrong.
    """
    _, mappable, *_ = plot(POSITIVE).make_plot(cbar=False, norm="log")
    assert isinstance(mappable.norm, LogNorm)


def test_color_scale_holds_the_norm_a_scale_name_names_and_refuses_an_unknown_one():
    """``ColorScale(norm="log").norm`` is a ``LogNorm``; an unknown name is matplotlib's ValueError.

    ON FAILURE: the code is wrong.
    """
    assert isinstance(ColorScale(norm="log").norm, LogNorm)
    with pytest.raises(ValueError, match="'lgo'"):
        ColorScale(norm="lgo")
