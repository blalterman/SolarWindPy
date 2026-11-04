# Spent-When: PERMANENT(Hist2D and SpiralPlot2D stop sharing ColorPlot)
# Supersedes: none
r"""Hist2D and SpiralPlot2D draw with the same defaults where both draw the same thing.

Both are ``ColorPlot`` subclasses. The author's rulings: contours default to
one linestyle sequence, the author's original (its eighth entry is
``(0, (7, 3, 1, 3, 1, 3))``); every contour method defaults to the colour
norm ``make_plot`` uses (``ColorPlot._default_norm``); ``alpha_fcn`` is
ignored, with a warning, on a count plot; the ``categoricals`` alias of
``intervals`` is gone; and a Spiral builds its mesh silently unless asked
for the progress table. SpiralPlot2D filters cells before it normalizes, so
its normalized values describe the cells it keeps.
"""

import logging

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from matplotlib.colors import LogNorm  # noqa: E402

from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402
from solarwindpy.plotting.spiral import SpiralPlot2D  # noqa: E402
from tests.tolerances import exact  # noqa: E402

#: The author's contour linestyles (Hist2D.plot_contours, 2025).
AUTHOR_LINESTYLES = [
    "-",
    ":",
    "--",
    (0, (7, 3, 1, 3, 1, 3, 1, 3, 1, 3)),
    "--",
    ":",
    "-",
    (0, (7, 3, 1, 3, 1, 3)),
]


def _points(n=4000, seed=7):
    rng = np.random.default_rng(seed)
    return pd.Series(rng.normal(0.0, 1.0, n)), pd.Series(rng.normal(0.0, 1.0, n))


@pytest.fixture(autouse=True)
def _close():
    yield
    plt.close("all")


@pytest.fixture()
def hist():
    x, y = _points()
    return Hist2D(x, y, nbins=12)


@pytest.fixture()
def spiral():
    x, y = _points()
    return SpiralPlot2D(x, y, min_per_bin=100)


# --- contour linestyles ------------------------------------------------------


def _contour_set(result):
    return result[-2]


@pytest.mark.parametrize(
    "draw",
    [
        pytest.param(
            lambda h, s: h.plot_contours(cbar=False), id="Hist2D.plot_contours"
        ),
        pytest.param(
            lambda h, s: h.plot_hist_with_contours(cbar=False),
            id="Hist2D.plot_hist_with_contours",
        ),
        pytest.param(
            lambda h, s: s.plot_contours(cbar=False),
            id="SpiralPlot2D.plot_contours",
        ),
    ],
)
def test_contours_default_to_the_authors_linestyles(hist, spiral, draw):
    """Every contour method draws the author's eight linestyles by default.

    ON FAILURE: the code is wrong.
    """
    assert list(_contour_set(draw(hist, spiral)).linestyles) == AUTHOR_LINESTYLES


# --- contour colour norm -----------------------------------------------------


@pytest.mark.parametrize(
    "plot",
    [
        pytest.param(lambda x, y: Hist2D(x, y, nbins=12, axnorm="d"), id="Hist2D"),
        pytest.param(
            lambda x, y: SpiralPlot2D(x, y, min_per_bin=100, axnorm="d"),
            id="SpiralPlot2D",
        ),
    ],
)
def test_density_contours_default_to_a_log_norm(plot):
    """A density ("d") spans decades, so its contours default to a LogNorm.

    This is the norm ``make_plot`` uses (``ColorPlot._default_norm``).

    ON FAILURE: the code is wrong.
    """
    x, y = _points()
    qset = _contour_set(plot(x, y).plot_contours(cbar=False))
    assert isinstance(qset.norm, LogNorm)


# --- alpha_fcn on a count plot -----------------------------------------------


_IGNORED = "Ignoring `alpha_fcn` because plotting counts"


@pytest.mark.parametrize(
    "make",
    [
        pytest.param(lambda: Hist2D(*_points(), nbins=12), id="Hist2D"),
        pytest.param(
            lambda: SpiralPlot2D(*_points(), min_per_bin=100),
            id="SpiralPlot2D",
        ),
    ],
)
def test_alpha_fcn_is_ignored_with_a_warning_on_a_count_plot(make, caplog):
    """A count plot has no z to aggregate for alpha: it is ignored, with a warning.

    The faces keep the alpha they have without ``alpha_fcn``.

    ON FAILURE: the code is wrong.
    """
    plot = make()
    _, plain, _ = plot.make_plot(cbar=False)
    plt.draw()
    expected = plain.get_facecolors()[:, 3].copy()
    with caplog.at_level(logging.WARNING):
        _, artist, _ = plot.make_plot(cbar=False, alpha_fcn="std")
    assert _IGNORED in caplog.text
    plt.draw()
    assert artist.get_facecolors()[:, 3] == exact(expected)


# --- the categoricals alias --------------------------------------------------


def test_bins_are_named_intervals_only():
    """The bins per axis are ``intervals``; the ``categoricals`` alias is gone.

    ON FAILURE: the code is wrong.
    """
    assert not hasattr(Hist2D, "categoricals")


# --- Spiral's mesh progress table --------------------------------------------

_TABLE_HEADER = " Step      N      Elapsed Time"


def test_spiral_writes_the_progress_table_when_asked(capsys):
    """``progress=True`` writes the mesh-building table to stderr.

    ON FAILURE: the code is wrong.
    """
    SpiralPlot2D(*_points(), min_per_bin=100, progress=True)
    assert _TABLE_HEADER in capsys.readouterr().err


def test_spiral_builds_its_mesh_silently_by_default(capsys):
    """By default the mesh is built without the progress table.

    The mesh of 1e6 points builds in well under a second, so the author
    ruled the table off by default.

    ON FAILURE: the code is wrong.
    """
    SpiralPlot2D(*_points(), min_per_bin=100)
    assert _TABLE_HEADER not in capsys.readouterr().err


# --- Spiral filters before it normalizes -------------------------------------


def _filtered_spiral(axnorm):
    plot = SpiralPlot2D(*_points(), min_per_bin=100, axnorm=axnorm)
    plot.mesh.set_cell_filter_thresholds(density=0.5)
    return plot


def test_spiral_density_integrates_to_one_over_the_cells_it_keeps():
    """With a cell filter, ``axnorm="d"`` is a PDF over the surviving cells.

    The filter runs before the normalization, so the kept cells' density
    times their area (on the binned scale) sums to 1.

    ON FAILURE: the code is wrong.
    """
    plot = _filtered_spiral("d")
    mesh = plot.mesh.mesh
    area = (mesh[:, 1] - mesh[:, 0]) * (mesh[:, 3] - mesh[:, 2])
    agg = plot.agg().to_numpy()
    kept = np.isfinite(agg)
    assert 0 < kept.sum() < plot.mesh.cell_filter.size
    assert np.sum(agg[kept] * area[kept]) == exact(1.0)


def test_spiral_total_norm_peaks_at_one_over_the_cells_it_keeps():
    """With a cell filter, ``axnorm="t"`` peaks at 1 over the surviving cells.

    ON FAILURE: the code is wrong.
    """
    agg = _filtered_spiral("t").agg()
    assert np.nanmax(agg.to_numpy()) == 1.0
