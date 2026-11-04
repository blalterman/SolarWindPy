# Spent-When: PERMANENT(the plotting classes stop sharing the BinnedPlot and ColorPlot bases)
# Supersedes: none
"""The plot class structure: shared bases and pluggable binning strategies.

``Base`` is the root. ``BinnedPlot`` aggregates a value in the cells of a
``Binning`` (``agg``, ``clim``, ``axnorm``); ``ColorPlot`` holds the z label,
the colorbar and ``alim``. ``Hist1D`` bins on a 1-D ``FixedGrid``, ``Hist2D``
on a 2-D one, ``SpiralPlot2D`` on an ``AdaptiveMesh``, and ``Scatter`` bins
nothing. Each strategy declares the ``axnorm`` keys its cells support: rows
and columns exist only on the 2-D grid, so the mesh supports ``t`` and ``d``.

Expected values come from the chosen inputs: counts per cell are recounted
here from the public ``mesh.mesh`` edges and ``data``.
"""

import importlib.util

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from solarwindpy.plotting import base  # noqa: E402
from solarwindpy.plotting.hist1d import Hist1D  # noqa: E402
from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402
from solarwindpy.plotting.scatter import Scatter  # noqa: E402
from solarwindpy.plotting.spiral import SpiralPlot2D  # noqa: E402
from tests.tolerances import exact  # noqa: E402

# 400 points of a correlated cloud: dense in the middle, sparse at the edges,
# so the mesh splits some cells and not others.
_RNG = np.random.default_rng(20261104)
X = pd.Series(_RNG.normal(0.0, 1.0, 400))
Y = pd.Series(0.5 * X.to_numpy() + _RNG.normal(0.0, 0.5, 400))
MIN_PER_BIN = 30


def _spiral(**kwargs):
    return SpiralPlot2D(X, Y, initial_bins=2, min_per_bin=MIN_PER_BIN, **kwargs)


def _counts_per_cell(splot):
    """Points of ``splot.data`` in each ``[x0, x1) x [y0, y1)`` row of ``mesh.mesh``."""
    d = splot.data
    x, y = d.x.to_numpy(), d.y.to_numpy()
    return np.array(
        [
            ((x0 <= x) & (x < x1) & (y0 <= y) & (y < y1)).sum()
            for x0, x1, y0, y1 in splot.mesh.mesh
        ]
    )


# ---------------------------------------------------------------------------
# The hierarchy
# ---------------------------------------------------------------------------


def test_each_plot_derives_from_the_bases_of_what_it_does():
    """Binned plots are BinnedPlots, coloured plots ColorPlots; Scatter bins nothing.

    ON FAILURE: the code is wrong.
    """
    assert issubclass(base.BinnedPlot, base.Base)
    assert issubclass(base.ColorPlot, base.Base)
    for cls in (Hist1D, Hist2D, SpiralPlot2D):
        assert issubclass(cls, base.BinnedPlot), cls
    for cls in (Hist2D, SpiralPlot2D, Scatter):
        assert issubclass(cls, base.ColorPlot), cls
    assert not issubclass(Hist1D, base.ColorPlot)
    assert not issubclass(Scatter, base.BinnedPlot)


def test_the_replaced_bases_are_gone():
    """``AggPlot``, ``PlotWithZdata`` and ``_CbarMaker`` no longer exist.

    ON FAILURE: the code is wrong.
    """
    assert importlib.util.find_spec("solarwindpy.plotting.agg_plot") is None
    for name in ("PlotWithZdata", "_CbarMaker"):
        assert name not in vars(base), name


def test_binning_is_abstract_and_a_strategy_must_declare_its_axnorms():
    """``Binning`` cannot be built, nor a strategy that omits ``allowed_axnorm``.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.plotting.binning import Binning

    class NoAxnorm(Binning):
        cells = pd.RangeIndex(1)

        def codes(self):
            return np.zeros(1, dtype=np.intp)

        def cell_measure(self):
            return np.ones(1)

    with pytest.raises(TypeError, match="abstract"):
        Binning()
    with pytest.raises(TypeError, match="allowed_axnorm"):
        NoAxnorm()


@pytest.mark.parametrize(
    "build, strategy, allowed",
    [
        (lambda: Hist1D(X), "FixedGrid", ("d", "t")),
        (lambda: Hist2D(X, Y), "FixedGrid", ("c", "r", "t", "d", "cd", "rd")),
        (_spiral, "AdaptiveMesh", ("d", "t")),
    ],
    ids=["Hist1D", "Hist2D", "SpiralPlot2D"],
)
def test_each_binned_plot_bins_with_a_strategy_declaring_its_axnorms(
    build, strategy, allowed
):
    """A plot's ``binning`` is its strategy, and ``allowed_axnorm`` lists its keys.

    Row and column norms need rows and columns, which only the 2-D grid has.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.plotting import binning, spiral

    plot = build()
    cls = getattr(binning, strategy, None) or getattr(spiral, strategy)
    assert isinstance(plot.binning, binning.Binning)
    assert isinstance(plot.binning, cls)
    assert tuple(plot.binning.allowed_axnorm) == allowed


@pytest.mark.parametrize(
    "build",
    [lambda: Hist1D(X), lambda: Hist2D(X, Y), _spiral],
    ids=["Hist1D", "Hist2D", "SpiralPlot2D"],
)
def test_every_binned_plot_holds_clim_as_range_limits(build):
    """``clim`` is one type on every binned plot: ``RangeLimits``.

    ON FAILURE: the code is wrong.
    """
    plot = build()
    plot.set_clim(2, None)
    assert isinstance(plot.clim, base.RangeLimits)
    assert plot.clim == base.RangeLimits(2, None)


# ---------------------------------------------------------------------------
# SpiralPlot2D on the adaptive mesh
# ---------------------------------------------------------------------------


def test_spiral_builds_its_mesh_in_the_constructor_from_min_per_bin():
    """The constructor splits every cell holding more than ``min_per_bin`` points.

    Every kept row is placed: the cells' counts, recounted here from the
    mesh edges, sum to the rows of ``data``.

    ON FAILURE: the code is wrong.
    """
    splot = _spiral()
    counts = _counts_per_cell(splot)
    assert splot.mesh.min_per_bin == MIN_PER_BIN
    assert counts.max() <= MIN_PER_BIN
    assert counts.sum() == len(splot.data)
    assert splot.mesh.mesh.shape[0] > 4  # the 2 x 2 initial grid was split


def test_spiral_has_no_separate_mesh_lifecycle():
    """``initialize_mesh``, ``build_grouped`` and ``calc_initial_bins`` are gone.

    ON FAILURE: the code is wrong.
    """
    for name in ("initialize_mesh", "build_grouped", "calc_initial_bins"):
        assert name not in dir(SpiralPlot2D), name


def test_spiral_total_normalization_divides_by_the_largest_cell():
    """``axnorm="t"`` gives each cell's count over the largest cell's count.

    ON FAILURE: the code is wrong.
    """
    counts = _counts_per_cell(_spiral())
    expected = np.where(counts > 0, counts / counts.max(), np.nan)
    agg = _spiral(axnorm="t").agg()
    assert agg.to_numpy() == exact(expected, nan_ok=True)


def test_spiral_density_integrates_to_one_over_the_cell_areas():
    """``axnorm="d"`` is the count over (N times the cell area); it sums to 1.

    The area is ``(x1 - x0) * (y1 - y0)`` of each row of ``mesh.mesh``.

    ON FAILURE: the code is wrong.
    """
    splot = _spiral(axnorm="d")
    m = splot.mesh.mesh
    area = (m[:, 1] - m[:, 0]) * (m[:, 3] - m[:, 2])
    counts = _counts_per_cell(splot)
    expected = np.where(counts > 0, counts / (counts.sum() * area), np.nan)
    agg = splot.agg().to_numpy()
    assert agg == exact(expected, nan_ok=True)
    assert np.nansum(agg * area) == exact(1.0)


def test_spiral_count_label_names_its_normalization():
    """The z ``Count`` label follows ``axnorm``, as a histogram's does.

    ON FAILURE: the code is wrong.
    """
    splot = _spiral(axnorm="t")
    assert splot.labels.z.axnorm == "t"
    splot.set_axnorm("d")
    assert splot.labels.z.axnorm == "d"


@pytest.mark.parametrize("key", ["c", "r", "cd", "rd"])
def test_spiral_refuses_row_and_column_normalizations(key):
    """The mesh has no rows or columns, so ``set_axnorm`` refuses those keys.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(ValueError, match=f"Unrecognized axnorm '{key}'"):
        _spiral().set_axnorm(key)


def test_spiral_selects_the_rows_of_the_cells_it_plots():
    """With ``clim`` set, the plotted rows are those in cells meeting it.

    ON FAILURE: the code is wrong.
    """
    splot = _spiral()
    lower = 10
    splot.set_clim(lower, None)
    d = splot.data
    x, y = d.x.to_numpy(), d.y.to_numpy()
    expected = np.zeros(len(d), dtype=bool)
    for (x0, x1, y0, y1), n in zip(splot.mesh.mesh, _counts_per_cell(splot)):
        if n >= lower:
            expected |= (x0 <= x) & (x < x1) & (y0 <= y) & (y < y1)
    plotted = splot.get_plotted_data_boolean_series()
    assert plotted.index.equals(d.index)
    assert plotted.to_numpy().tolist() == expected.tolist()
    assert 0 < expected.sum() < len(d)  # the fixture keeps some rows, not all
