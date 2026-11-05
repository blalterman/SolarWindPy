# Spent-When: PERMANENT(axnorm stops depending on the aggregation)
# Supersedes: none
"""Tests for ``axnorm`` applied according to the aggregation.

Notation for one cell i: n_i rows, area A_i on the binned scale (log10 on a
log axis), aggregated value v_i; N is the number of rows in the shown cells,
N_col and N_row those in a column or row.

- A count: d = n_i / (N A_i) and w = n_i / N, as before.
- A sum of z: d = S_i / (S A_i) and w = S_i / S, each cell's share of the
  total z, S the total over the shown cells; a negative z raises.
- Any other aggregation (mean, median, a callable): d = v_i n_i / (N A_i)
  and w = v_i n_i / N, so sum(d A) and sum(w) are the count-weighted average
  of v. For a mean that is the mean z of the rows.
- cd, rd, wc and wr do the same within each column or row.
- t, c and r divide by the largest absolute value overall, per column or per
  row.

Every expected number is computed here with numpy from the inputs, which all
lie inside the grid, never from the plot's own code.
"""

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")

from solarwindpy.plotting.hist1d import Hist1D  # noqa: E402
from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402
from solarwindpy.plotting.labels.base import TeXlabel  # noqa: E402
from solarwindpy.plotting.labels.special import Count  # noqa: E402
from solarwindpy.plotting.spiral import SpiralPlot2D  # noqa: E402
from tests.tolerances import exact  # noqa: E402

RNG = np.random.default_rng(21)
N = 4000
X = pd.Series(RNG.uniform(0.0, 3.0, N))
Y = pd.Series(RNG.uniform(0.0, 2.0, N))
Z = pd.Series(RNG.normal(1.0, 2.0, N))  # signed
ZPOS = pd.Series(RNG.lognormal(0.0, 1.0, N))
XEDGES = np.linspace(0.0, 3.0, 7)  # widths 0.5
YEDGES = np.array([0.0, 0.3, 1.0, 2.0])  # unequal widths
# Log grid: x and y in (1, 1000), edges in log10.
LX = pd.Series(10 ** RNG.uniform(0.0, 3.0, N))
LY = pd.Series(10 ** RNG.uniform(0.0, 3.0, N))
LEDGES = np.array([0.0, 0.5, 1.5, 3.0])


def _cell(x, y, xedges, yedges):
    """x-bin and y-bin of each row, from numpy.digitize."""
    return np.digitize(x, xedges) - 1, np.digitize(y, yedges) - 1


def _area(xedges, yedges):
    return np.outer(np.diff(xedges), np.diff(yedges))


def _h2(z, fcn, axnorm, log=False):
    if log:
        h = Hist2D(LX, LY, z, logx=True, logy=True, nbins=[LEDGES, LEDGES])
    else:
        h = Hist2D(X, Y, z, nbins=[XEDGES, YEDGES])
    h.set_axnorm(axnorm)
    agg = h.agg(fcn=fcn)
    nx = len(h.intervals["x"])
    return agg.to_numpy().reshape(nx, -1)


def _inputs(log):
    if log:
        ix, iy = _cell(np.log10(LX), np.log10(LY), LEDGES, LEDGES)
        return ix, iy, _area(LEDGES, LEDGES), np.diff(LEDGES), np.diff(LEDGES)
    ix, iy = _cell(X, Y, XEDGES, YEDGES)
    return ix, iy, _area(XEDGES, YEDGES), np.diff(XEDGES), np.diff(YEDGES)


@pytest.mark.parametrize(
    "build, allowed",
    [
        (lambda: Hist1D(X), ("d", "t", "w")),
        (
            lambda: Hist2D(X, Y),
            ("c", "r", "t", "d", "cd", "rd", "w", "wc", "wr"),
        ),
        (
            lambda: SpiralPlot2D(X, Y, initial_bins=3, min_per_bin=500),
            ("d", "t", "w"),
        ),
    ],
    ids=["Hist1D", "Hist2D", "SpiralPlot2D"],
)
def test_allowed_axnorm_adds_the_weight_keys(build, allowed):
    """1-D and spiral allow d, t, w; the 2-D grid adds c, r, cd, rd, wc, wr.

    ON FAILURE: the code is wrong.
    """
    assert tuple(build().binning.allowed_axnorm) == allowed


@pytest.mark.parametrize("log", [False, True], ids=["linear", "log"])
def test_density_of_a_mean_integrates_to_the_mean_z(log):
    """sum(d A) over the grid is the mean z of every row.

    ON FAILURE: the code is wrong.
    """
    d = _h2(Z, "mean", "d", log)
    _, _, area, _, _ = _inputs(log)
    assert np.nansum(d * area) == exact(Z.mean())


@pytest.mark.parametrize("log", [False, True], ids=["linear", "log"])
def test_column_and_row_densities_of_a_mean_integrate_to_their_means(log):
    """cd integrates over y to each column's mean z, rd over x to each row's.

    ON FAILURE: the code is wrong.
    """
    ix, iy, _, dx, dy = _inputs(log)
    cd = _h2(Z, "mean", "cd", log)
    rd = _h2(Z, "mean", "rd", log)
    col_means = Z.groupby(ix).mean().to_numpy()
    row_means = Z.groupby(iy).mean().to_numpy()
    assert np.nansum(cd * dy, axis=1) == exact(col_means)
    assert np.nansum(rd * dx[:, None], axis=0) == exact(row_means)


def test_weights_of_a_mean_sum_to_the_means():
    """w sums to the mean z; wc over each column and wr over each row to theirs.

    ON FAILURE: the code is wrong.
    """
    ix, iy, _, _, _ = _inputs(False)
    w = _h2(Z, "mean", "w")
    wc = _h2(Z, "mean", "wc")
    wr = _h2(Z, "mean", "wr")
    assert np.nansum(w) == exact(Z.mean())
    assert np.nansum(wc, axis=1) == exact(Z.groupby(ix).mean().to_numpy())
    assert np.nansum(wr, axis=0) == exact(Z.groupby(iy).mean().to_numpy())


def test_density_of_a_median_integrates_to_the_count_weighted_median():
    """sum(d A) is sum(median_i n_i) / N over the cells, not the overall median.

    ON FAILURE: the code is wrong.
    """
    # Positive on the left half, three times as large and negative on the
    # right: the overall median lies between the halves, far from the
    # count-weighted median of the cells.
    z = pd.Series(np.where(X < 1.5, ZPOS, -3.0 * ZPOS))
    ix, iy, area, _, _ = _inputs(False)
    cells = z.groupby([ix, iy])
    expected = (cells.median() * cells.size()).sum() / N
    d = _h2(z, "median", "d")
    assert np.nansum(d * area) == exact(expected)
    assert abs(expected - z.median()) > 0.5  # not the overall median


@pytest.mark.parametrize("fcn", ["sum", np.sum], ids=["str", "np.sum"])
def test_shares_of_a_sum_add_to_one(fcn):
    """For a sum, d A, w, cd dy per column and wr per row each add to 1.

    ON FAILURE: the code is wrong.
    """
    _, _, area, _, dy = _inputs(False)
    assert np.nansum(_h2(ZPOS, fcn, "d") * area) == exact(1.0)
    assert np.nansum(_h2(ZPOS, fcn, "w")) == exact(1.0)
    cd = np.nansum(_h2(ZPOS, fcn, "cd") * dy, axis=1)
    assert cd == exact(np.ones_like(cd))
    wr = np.nansum(_h2(ZPOS, fcn, "wr"), axis=0)
    assert wr == exact(np.ones_like(wr))


def test_a_share_of_a_sum_with_a_negative_z_raises():
    """A sum's share needs z >= 0; t is a peak normalization and still works.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(ValueError, match="negative"):
        _h2(Z, "sum", "d")
    t = _h2(Z, "sum", "t")
    assert np.nanmax(np.abs(t)) == exact(1.0)


def test_count_weights_are_count_fractions():
    """For a count, w = n_i / N, wc = n_i / N_col and wr = n_i / N_row.

    ON FAILURE: the code is wrong.
    """
    ix, iy, _, _, _ = _inputs(False)
    n, _, _ = np.histogram2d(X, Y, bins=[XEDGES, YEDGES])
    assert _h2(None, None, "w") == exact(n / N)
    assert _h2(None, None, "wc") == exact(n / n.sum(axis=1, keepdims=True))
    assert _h2(None, None, "wr") == exact(n / n.sum(axis=0))


def test_peak_norms_of_signed_values_divide_by_the_largest_magnitude():
    """t of signed means: the largest |value| becomes 1 and signs are kept.

    ON FAILURE: the code is wrong.
    """
    z = pd.Series(np.where(X < 1.5, -5.0, 1.0) + 0.1 * Z)
    raw = _h2(z, "mean", None)
    t = _h2(z, "mean", "t")
    assert t == exact(raw / np.nanmax(np.abs(raw)))
    assert np.nanmin(t) == exact(-1.0)


def test_hist1d_density_of_a_mean_integrates_to_the_mean():
    """A Hist1D of x averaging Z: sum(d width) is the mean of Z.

    ON FAILURE: the code is wrong.
    """
    h = Hist1D(X, Z, nbins=XEDGES)
    h.set_axnorm("d")
    d = h.agg().to_numpy()
    assert np.nansum(d * np.diff(XEDGES)) == exact(Z.mean())


@pytest.mark.parametrize("key", ["w", "wc", "wr"])
def test_labels_accept_the_weight_keys(key):
    """Count and TeXlabel take w, wc and wr, and name them in the path.

    ON FAILURE: the code is wrong.
    """
    count = Count(norm=key)
    assert str(count.path).endswith(key.upper() + "norm")
    label = TeXlabel(("n", "", "p1"), axnorm=key)
    assert str(label.path).endswith(key.upper() + "norm")


def test_count_plot_with_a_weight_key_relabels_its_count():
    """A Hist2D count with axnorm="w" labels z as a count fraction.

    ON FAILURE: the code is wrong.
    """
    h = Hist2D(X, Y, nbins=[XEDGES, YEDGES], axnorm="w")
    assert "Fraction" in str(h.labels.z)
