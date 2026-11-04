# Spent-When: PERMANENT(Hist2D stops returning every bin from agg or stops offering id_data_above_contour)
# Supersedes: none
"""Hist2D's full ``agg`` grid and contour selection on hand-placed points.

Ten points sit on round coordinates. For each bin specification the bins, the
count in every (x, y) bin and the rows ``id_data_above_contour`` labels are
worked out by hand below, from the documented binning rules:

- an integer count spans the data's min to max in equal bins closed on the
  left, the last bin also on the right (``np.histogram``);
- explicit edges give right-closed bins, ``(a, b]``;
- a left-closed ``IntervalIndex`` keeps its closure, its last bin also closed
  on the right;
- ``"knuth"`` takes its edges from ``astropy.stats.knuth_bin_width``, which on
  these values chooses 5 x bins of width 0.6 and 3 y bins of width 4/3
  (edges rounded to 5 places), right-closed.

``agg`` holds every bin, x varying slowest, NaN where no point falls. No
selected point sits on an edge of the box it is selected by, so the expected
selection does not depend on which side the comparison closes.
"""

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402
from tests.tolerances import exact  # noqa: E402

#: Points P0 to P9. P0 (x = 0), P7 (y = 4) and P8 (x = 3, y = 0) sit on the
#: outer edges; P2 to P5 fill the middle column's middle bins.
X = pd.Series([0.0, 0.5, 1.5, 1.5, 1.5, 1.5, 1.5, 2.5, 3.0, 2.5])
Y = pd.Series([0.5, 3.5, 1.5, 1.5, 2.5, 2.5, 0.5, 4.0, 0.0, 2.5])

nan = np.nan

X_BREAKS = [0.0, 1.0, 2.0, 3.0]
Y_BREAKS = [0.0, 1.0, 2.0, 3.0, 4.0]

#: Each spec: nbins, the x and y breaks and closure, the count in every bin
#: (x slowest), the x bin of the selected rows, and the rows each bin keeps.
SPECS = {
    # Edges 0..3 by 1 and 0..4 by 1, left-closed with the last bin closed on
    # both sides: every point is binned.
    "int": dict(
        nbins=(3, 4),
        x_breaks=X_BREAKS,
        y_breaks=Y_BREAKS,
        closed="left",
        grid=[
            [1, nan, nan, 1],  # x [0, 1): P0 at y0, P1 at y3
            [1, 2, 2, nan],  # x [1, 2): P6 y0, P2 P3 y1, P4 P5 y2
            [1, nan, 1, 1],  # x [2, 3]: P8 y0, P9 y2, P7 y3
        ],
        selected=pd.Interval(1.0, 2.0, closed="left"),
        plotted=[True] * 10,
    ),
    # The same edges, right-closed: P0 (x = 0) and P8 (y = 0) are in no bin.
    "edges": dict(
        nbins=(np.array(X_BREAKS), np.array(Y_BREAKS)),
        x_breaks=X_BREAKS,
        y_breaks=Y_BREAKS,
        closed="right",
        grid=[
            [nan, nan, nan, 1],  # x (0, 1]: P1 at y (3, 4]
            [1, 2, 2, nan],  # x (1, 2]: P6, P2 P3, P4 P5
            [nan, nan, 1, 1],  # x (2, 3]: P9 at y (2, 3], P7 at y (3, 4]
        ],
        selected=pd.Interval(1.0, 2.0, closed="right"),
        plotted=[False] + [True] * 7 + [False, True],
    ),
    # Left-closed intervals bin like the integer count.
    "intervals_left": dict(
        nbins=(
            pd.IntervalIndex.from_breaks(X_BREAKS, closed="left"),
            pd.IntervalIndex.from_breaks(Y_BREAKS, closed="left"),
        ),
        x_breaks=X_BREAKS,
        y_breaks=Y_BREAKS,
        closed="left",
        grid=[
            [1, nan, nan, 1],
            [1, 2, 2, nan],
            [1, nan, 1, 1],
        ],
        selected=pd.Interval(1.0, 2.0, closed="left"),
        plotted=[True] * 10,
    ),
    # x edges 0..3 by 0.6, y edges 0, 1.33333, 2.66667, 4; right-closed, so
    # P0 (x = 0) and P8 (y = 0) are in no bin.
    "knuth": dict(
        nbins="knuth",
        x_breaks=[0.0, 0.6, 1.2, 1.8, 2.4, 3.0],
        y_breaks=[0.0, 1.33333, 2.66667, 4.0],
        closed="right",
        grid=[
            [nan, nan, 1],  # x (0, 0.6]: P1 at y (2.67, 4]
            [nan, nan, nan],  # x (0.6, 1.2]: empty
            [1, 4, nan],  # x (1.2, 1.8]: P6 y0, P2 to P5 y1
            [nan, nan, nan],  # x (1.8, 2.4]: empty
            [nan, 1, 1],  # x (2.4, 3]: P9 y1, P7 y2
        ],
        selected=pd.Interval(1.2, 1.8, closed="right"),
        plotted=[False] + [True] * 7 + [False, True],
    ),
}

#: The rows a bin reaching 2 holds, in every spec: P2 to P5, middle column.
SELECTED_ROWS = [2, 3, 4, 5]


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


@pytest.fixture(params=sorted(SPECS))
def spec(request):
    return SPECS[request.param]


def _hist(spec):
    return Hist2D(X, Y, nbins=spec["nbins"])


def _intervals(breaks, closed):
    return pd.IntervalIndex.from_breaks(breaks, closed=closed)


def test_the_bins_are_the_hand_derived_intervals(spec):
    """``intervals`` and ``categoricals`` are the same IntervalIndex, as derived by hand.

    Guards the fixture: every expected grid below rests on these bins.

    ON FAILURE: fix the fixture if the bin rule changed on purpose (e.g.
    astropy's Knuth rule), otherwise the code is wrong.
    """
    h = _hist(spec)
    for axis, breaks in (("x", spec["x_breaks"]), ("y", spec["y_breaks"])):
        expected = _intervals(breaks, spec["closed"])
        assert isinstance(h.intervals[axis], pd.IntervalIndex)
        assert isinstance(h.categoricals[axis], pd.IntervalIndex)
        assert h.intervals[axis].equals(expected)
        assert h.categoricals[axis].equals(expected)
        assert h.edges[axis].to_numpy() == exact(breaks)


def test_agg_holds_every_bin_with_nan_where_empty(spec):
    """``agg`` is the full x-by-y grid, x slowest, with the hand counts and NaN.

    ON FAILURE: the code is wrong.
    """
    h = _hist(spec)
    agg = h.agg()
    expected_index = pd.MultiIndex.from_product(
        [
            _intervals(spec["x_breaks"], spec["closed"]),
            _intervals(spec["y_breaks"], spec["closed"]),
        ],
        names=["x", "y"],
    )
    assert agg.index.equals(expected_index)
    for level in agg.index.levels:
        assert isinstance(level, pd.IntervalIndex)
    expected = np.ravel(spec["grid"])
    assert agg.to_numpy(dtype=float) == exact(expected, nan_ok=True)


def test_the_mesh_handed_to_matplotlib_is_the_grid_with_empty_bins_masked(spec):
    """``make_plot`` draws y rows by x columns of the hand counts, empty bins masked.

    ON FAILURE: the code is wrong.
    """
    h = _hist(spec)
    _, mesh = h.make_plot(cbar=False)
    C = mesh.get_array()
    expected = np.array(spec["grid"], dtype=float).T  # rows are y bins
    assert C.shape == expected.shape
    np.testing.assert_array_equal(np.ma.getmaskarray(C), np.isnan(expected))
    assert C.compressed() == exact(expected[~np.isnan(expected)])


def test_id_data_above_contour_labels_the_rows_in_bins_reaching_the_level(spec):
    """Level 2: only the middle column clears it, so P2 to P5 get its x bin.

    The middle column's bins at 2 or more span y from the bottom of the
    lower to the top of the upper; P2 to P5 lie inside, P6 below. Every
    other column peaks at 1, so its rows stay NaN.

    ON FAILURE: the code is wrong.
    """
    h = _hist(spec)
    labelled = h.id_data_above_contour(2)
    assert labelled.index.equals(X.index)
    expected = [spec["selected"] if i in SELECTED_ROWS else None for i in X.index]
    for got, want in zip(labelled.tolist(), expected):
        if want is None:
            assert pd.isna(got)
        else:
            assert got == want


def test_the_plotted_rows_are_the_binned_rows(spec):
    """Every row in a bin is plotted; P0 and P8 are not under right-closed bins.

    ON FAILURE: the code is wrong.
    """
    h = _hist(spec)
    plotted = h.get_plotted_data_boolean_series()
    assert plotted.index.equals(X.index)
    assert plotted.tolist() == spec["plotted"]


#: Border fixture B0 to B7, binned by right-closed edges 0..4 by 1 on both
#: axes. No point sits on an edge. Each column lists its highest point first.
#:
#: - x (0, 1]: B0 at y (3, 4].
#: - x (1, 2]: B1 at y (3, 4], then B2 and B3 at y (0, 1].
#: - x (2, 3]: B4 and B5 at y (3, 4], then B6 at y (1, 2] and B7 at y (0, 1].
#: - x (3, 4] and y (2, 3] hold no point.
#:
#: Top and bottom per occupied column, (y bin, count):
#:
#:   x (0, 1]: top y (3, 4] count 1, bottom y (3, 4] count 1
#:   x (1, 2]: top y (3, 4] count 1, bottom y (0, 1] count 2
#:   x (2, 3]: top y (3, 4] count 2, bottom y (0, 1] count 1
#:
#: Walking the bins x slowest, the y bins first appear as (3, 4] (x (0, 1]),
#: (0, 1] (x (1, 2]), (1, 2] (x (2, 3]). With y rows in that order instead of
#: sorted, ``last_valid_index`` / ``first_valid_index`` would give top (0, 1]
#: and bottom (3, 4] in x (1, 2], and top (1, 2], a middle bin, and bottom
#: (3, 4] in x (2, 3]. The empty y (2, 3] is what kept those rows unsorted
#: before ``agg`` returned the full grid.
BX = pd.Series([0.5, 1.5, 1.5, 1.5, 2.5, 2.5, 2.5, 2.5])
BY = pd.Series([3.5, 3.5, 0.5, 0.5, 3.5, 3.5, 1.5, 0.5])
B_BREAKS = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
B_BINS = pd.IntervalIndex.from_breaks(B_BREAKS, closed="right")

#: (x bin, y bin, count) for each occupied column's top and bottom.
B_TOP = [(0, 3, 1), (1, 3, 1), (2, 3, 2)]
B_BOTTOM = [(0, 3, 1), (1, 0, 2), (2, 0, 1)]


def _border_hist():
    return Hist2D(BX, BY, nbins=(B_BREAKS, B_BREAKS))


def _expected_edge(rows):
    index = pd.MultiIndex.from_arrays(
        [B_BINS[[y for _, y, _ in rows]], B_BINS[[x for x, _, _ in rows]]],
        names=["y", "x"],
    )
    return index, [float(n) for _, _, n in rows]


@pytest.mark.parametrize("which", ["top", "bottom"])
def test_get_border_is_the_highest_and_lowest_occupied_y_bin_per_column(which):
    """Per x bin, ``top`` is the highest occupied y bin and ``bottom`` the lowest.

    Expected, by hand (see the fixture comment), in x (0, 1], (1, 2],
    (2, 3]: top y (3, 4] in all three with counts 1, 1, 2; bottom y (3, 4],
    (0, 1], (0, 1] with counts 1, 2, 1. The empty x (3, 4] is absent.

    ON FAILURE: if x (1, 2] or x (2, 3] has top and bottom swapped, or a
    top of y (1, 2], the y rows of ``agg().unstack("x")`` are in order of
    first appearance rather than sorted, so ``get_border`` picks the
    last-listed bin rather than the highest; otherwise the code is wrong.
    """
    border = _border_hist().get_border()
    edge = getattr(border, which)
    index, counts = _expected_edge(B_TOP if which == "top" else B_BOTTOM)
    assert edge.index.equals(index)
    assert edge.to_numpy(dtype=float) == exact(counts)


def test_plot_edges_draws_the_border_bin_centres():
    """``plot_edges`` draws the top and bottom at their bins' midpoints.

    Unsmoothed, the top line runs through (0.5, 3.5), (1.5, 3.5),
    (2.5, 3.5) and the bottom through (0.5, 3.5), (1.5, 0.5), (2.5, 0.5):
    the midpoints of the hand-derived border bins above.

    ON FAILURE: if ``get_border`` passes, ``plot_edges`` is drawing
    something other than the border's bin midpoints; otherwise fix
    ``get_border`` first.
    """
    _, ax = plt.subplots()
    (top,), (bottom,) = _border_hist().plot_edges(ax, smooth=False)
    assert np.asarray(top.get_xdata()) == exact([0.5, 1.5, 2.5])
    assert np.asarray(top.get_ydata()) == exact([3.5, 3.5, 3.5])
    assert np.asarray(bottom.get_xdata()) == exact([0.5, 1.5, 2.5])
    assert np.asarray(bottom.get_ydata()) == exact([3.5, 0.5, 0.5])
