# Spent-When: PERMANENT(BinnedPlot stops offering get_plotted_data)
# Supersedes: none
"""Tests for ``BinnedPlot.get_plotted_data``: the rows in the cells a figure shows.

A cell is shown when ``agg(fcn)`` is not NaN there, after ``clim``, ``alim``,
``axnorm`` and any cell filter. ``get_plotted_data`` returns the rows in those
cells: the caller's x, y (and z) values, sign included and never logged, on
the caller's index labels. Expected rows come from ``numpy.histogram2d`` or
``numpy.histogram`` counts on hand-chosen data that lies off every bin edge,
so the bins' closed side does not matter, never from the plot's own code.
"""

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")

from solarwindpy.plotting.hist1d import Hist1D  # noqa: E402
from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402
from solarwindpy.plotting.spiral import SpiralPlot2D  # noqa: E402
from tests.tolerances import exact  # noqa: E402

XEDGES = np.array([0.0, 1.0, 2.0, 3.0])
YEDGES = np.array([0.0, 1.0, 2.0])

# Labels 10..: cell (x-bin, y-bin) noted beside each row. Cell (0, 0) holds 3
# rows, (1, 1) 2, (2, 0) 1; label 16 has NaN y and is not kept.
ROWS = [
    (10, 0.5, 0.5, 1.0),  # (0, 0)
    (11, 0.2, 0.7, 2.0),  # (0, 0)
    (12, 0.8, 0.1, 3.0),  # (0, 0)
    (13, 1.5, 1.5, 4.0),  # (1, 1)
    (14, 1.2, 1.9, 8.0),  # (1, 1)
    (15, 2.5, 0.5, 9.0),  # (2, 0)
    (16, 2.5, np.nan, 9.0),
]
INDEX = pd.Index([r[0] for r in ROWS])
X = pd.Series([r[1] for r in ROWS], index=INDEX, name="x")
Y = pd.Series([r[2] for r in ROWS], index=INDEX, name="y")
Z = pd.Series([r[3] for r in ROWS], index=INDEX, name="z")


def _cell_counts_2d():
    """Count per row's cell, from numpy.histogram2d; NaN rows get 0."""
    kept = X.notna() & Y.notna()
    counts, _, _ = np.histogram2d(X[kept], Y[kept], bins=[XEDGES, YEDGES])
    ix = np.digitize(X[kept], XEDGES) - 1
    iy = np.digitize(Y[kept], YEDGES) - 1
    return pd.Series(counts[ix, iy], index=X.index[kept]).reindex(X.index, fill_value=0)


def _hist2d(z=None):
    return Hist2D(X, Y, z, nbins=[XEDGES, YEDGES])


@pytest.mark.parametrize("lower", [None, 2, 3])
def test_hist2d_returns_the_rows_of_cells_meeting_clim(lower):
    """With ``clim`` lower bound n, the rows of cells holding at least n rows.

    No bound keeps every non-NaN row (labels 10 to 15).

    ON FAILURE: the code is wrong.
    """
    h = _hist2d()
    h.set_clim(lower, None)
    counts = _cell_counts_2d()
    expected = counts.index[counts >= (lower or 1)]
    got = h.get_plotted_data()
    assert got.index.tolist() == expected.tolist()
    assert got.loc[:, "x"].to_numpy() == exact(X[expected].to_numpy())
    assert got.loc[:, "y"].to_numpy() == exact(Y[expected].to_numpy())


def test_alim_acts_on_the_aggregated_value_of_the_given_fcn():
    """``alim`` on z means hides cell (0, 0) (mean 2); ``fcn="max"`` keeps it (max 3).

    Means: (0, 0) 2, (1, 1) 6, (2, 0) 9. With alim lower 2.5 the default
    (mean) keeps labels 13 to 15; with ``fcn="max"`` (0, 0) is 3 and stays.

    ON FAILURE: the code is wrong.
    """
    h = _hist2d(Z)
    h.set_alim(2.5, None)
    assert h.get_plotted_data().index.tolist() == [13, 14, 15]
    assert h.get_plotted_data(fcn="max").index.tolist() == [10, 11, 12, 13, 14, 15]
    assert h.get_plotted_data().loc[:, "z"].tolist() == [4.0, 8.0, 9.0]


def test_a_log_axis_returns_the_callers_signed_values():
    """On a log x the rows hold the caller's x, negative ones included.

    x = -10, 100 bin by log10|x| = 1, 2 on edges [0, 1.5, 3].

    ON FAILURE: the code is wrong.
    """
    x = pd.Series([-10.0, 100.0], index=[5, 7])
    y = pd.Series([0.5, 0.5], index=[5, 7])
    h = Hist2D(x, y, logx=True, nbins=[np.array([0.0, 1.5, 3.0]), [0.0, 1.0]])
    got = h.get_plotted_data()
    assert got.index.tolist() == [5, 7]
    assert got.loc[:, "x"].tolist() == [-10.0, 100.0]


def test_hist1d_returns_the_rows_of_bins_meeting_clim():
    """Hist1D of x: bins hold 3, 2 and 1 rows; clim 2 keeps labels 10 to 14.

    Label 16 has x = 2.5 and no y, but a Hist1D of x alone keeps it, so the
    third bin holds 2 rows (15, 16) and is kept as well.

    ON FAILURE: the code is wrong.
    """
    h = Hist1D(X, nbins=XEDGES)
    h.set_clim(2, None)
    counts, _ = np.histogram(X, bins=XEDGES)
    per_row = counts[np.digitize(X, XEDGES) - 1]
    expected = X.index[per_row >= 2]
    got = h.get_plotted_data()
    assert got.index.tolist() == expected.tolist()
    assert got.loc[:, "x"].tolist() == X[expected].tolist()


def test_spiral_returns_as_many_rows_as_its_shown_cells_count():
    """A spiral's plotted rows number the counts of the cells ``agg`` shows.

    100 seeded points, min_per_bin=10, and clim 5 hide the sparse cells; the
    rows returned equal the sum of ``agg("count")`` over the shown cells.

    ON FAILURE: the code is wrong.
    """
    rng = np.random.default_rng(3)
    x = pd.Series(rng.normal(size=100))
    y = pd.Series(rng.normal(size=100))
    h = SpiralPlot2D(x, y, initial_bins=3, min_per_bin=10)
    h.set_clim(5, None)
    counts = h.agg(fcn="count")
    got = h.get_plotted_data()
    assert len(got) == counts[counts.notna()].sum()
    assert got.index.isin(x.index).all()
    assert got.loc[:, "x"].to_numpy() == exact(x[got.index].to_numpy())
