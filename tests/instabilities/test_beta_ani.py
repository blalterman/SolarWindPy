# Spent-When: PERMANENT(solarwindpy.instabilities.beta_ani is removed from the package)
# Supersedes: none
"""Tests for :class:`solarwindpy.instabilities.beta_ani.BetaRPlot`.

BetaRPlot is a Hist2D of anisotropy R against parallel beta, binned in log10 by
default, hiding cells with fewer than 5 counts. Expected counts come from
``numpy.histogram2d`` on the same inputs.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from matplotlib.collections import QuadMesh  # noqa: E402

from solarwindpy.instabilities.beta_ani import BetaRPlot  # noqa: E402
from solarwindpy.plotting.labels.base import TeXlabel  # noqa: E402
from tests.tolerances import exact  # noqa: E402

# Four populations in four distinct cells of a 2 x 2 grid:
#   5 at (beta, R) = (3, 0.3)   -> log10 cell (x0, y0), shown (5 >= 5)
#   4 at (30, 3)                -> cell (x1, y1), hidden (4 < 5)
#   1 at (1, 10) and 1 at (100, 0.1) pin the log10 ranges to [0, 2] x [-1, 1].
BETA = pd.Series([3.0] * 5 + [30.0] * 4 + [1.0, 100.0])
ANI = pd.Series([0.3] * 5 + [3.0] * 4 + [10.0, 0.1])
NBINS = 2


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def _mesh(ax):
    """The one pcolormesh on ``ax``, ignoring any other collection drawn."""
    (mesh,) = [c for c in ax.collections if isinstance(c, QuadMesh)]
    return mesh


def test_fixture_puts_one_population_on_each_side_of_the_count_floor():
    """The fixture has a 5-count cell and a 4-count cell in log10 binning.

    ON FAILURE: the fixture no longer separates shown from hidden cells; fix the
    fixture.
    """
    counts, _, _ = np.histogram2d(np.log10(BETA), np.log10(ANI), bins=NBINS)
    assert sorted(counts.ravel().tolist()) == [1.0, 1.0, 4.0, 5.0]


def test_default_plot_bins_log10_beta_and_anisotropy_and_hides_cells_below_5():
    """Cells are equal in log10, x is beta, y is R, and only counts >= 5 are drawn.

    ON FAILURE: the code is wrong.
    """
    ax, _ = BetaRPlot(BETA, ANI, "p", nbins=NBINS).make_plot()
    mesh = _mesh(ax)

    counts, xedges, yedges = np.histogram2d(np.log10(BETA), np.log10(ANI), bins=NBINS)
    expected = np.ma.masked_less(counts.T, 5)  # rows are y (R), columns x (beta)
    actual = np.ma.asarray(mesh.get_array()).reshape(expected.shape)
    np.testing.assert_array_equal(np.ma.getmaskarray(actual), expected.mask)
    np.testing.assert_array_equal(actual.compressed(), expected.compressed())

    coords = mesh.get_coordinates()
    # Edges are exact powers of ten here: log10 ranges [0, 2] and [-1, 1].
    assert np.asarray(coords[0, :, 0]) == exact(10.0**xedges)
    assert np.asarray(coords[:, 0, 1]) == exact(10.0**yedges)
    assert (ax.get_xscale(), ax.get_yscale()) == ("log", "log")


def test_logx_false_bins_beta_linearly():
    """logx=False switches beta to linear bins; R stays log10.

    ON FAILURE: the code is wrong.
    """
    ax, _ = BetaRPlot(BETA, ANI, "p", nbins=NBINS, logx=False).make_plot()
    coords = _mesh(ax).get_coordinates()
    xedges = np.histogram_bin_edges(BETA, NBINS)  # [1, 50.5, 100]
    assert np.asarray(coords[0, :, 0]) == exact(xedges)
    assert (ax.get_xscale(), ax.get_yscale()) == ("linear", "log")


@pytest.mark.parametrize(
    "species,beta_label,ani_label",
    [
        ("p", ("beta", "par", "p"), ("R", "T", "p")),
        ("p_bimax", ("beta", "par", "p"), ("R", "T", "p")),
        ("p1+p2", ("beta", "par", "p1+p2"), ("R", "P", "p1+p2")),
    ],
    ids=["single", "bimax-suffix-dropped", "summed-species-uses-pressure"],
)
def test_axes_are_labelled_parallel_beta_and_anisotropy_of_species(
    species, beta_label, ani_label
):
    """x is labelled parallel beta and y the T (or, summed, P) anisotropy of species.

    Labels are rendered by solarwindpy.plotting.labels.base.TeXlabel; wording is theirs.

    ON FAILURE: the code is wrong.
    """
    ax, _ = BetaRPlot(BETA, ANI, species, nbins=NBINS).make_plot()
    assert ax.get_xlabel() == str(TeXlabel(beta_label))
    assert ax.get_ylabel() == str(TeXlabel(ani_label))


@pytest.mark.parametrize(
    "kwargs,expected", [({}, "Greens_r"), ({"cmap": "viridis"}, "viridis")]
)
def test_colormap_defaults_to_greens_r_and_honours_caller(kwargs, expected):
    """make_plot uses Greens_r unless the caller passes cmap.

    ON FAILURE: the code is wrong.
    """
    ax, _ = BetaRPlot(BETA, ANI, "p", nbins=NBINS).make_plot(**kwargs)
    assert _mesh(ax).get_cmap().name == expected
