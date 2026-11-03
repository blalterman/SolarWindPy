# Spent-When: PERMANENT(Hist2D stops offering project_1d and its row selections)
# Supersedes: none
"""Hist2D's projection and row selections on hand-placed points.

Each expected value is worked out by hand in the test, from the documented
binning rules:

- explicit edges give right-closed bins, ``(a, b]``;
- an integer count spans the data's min to max in equal bins closed on the
  left, the last bin also on the right (``np.histogram``);
- a log axis bins ``log10(abs(v))``, while the values a selection or a
  projection hands back are the caller's own, sign included.

A projection is the parent's marginal: it bins each row where the parent
does, and averages the caller's z, or the caller's other axis.
"""

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from solarwindpy.plotting.hist1d import Hist1D  # noqa: E402
from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402
from tests.tolerances import exact  # noqa: E402

nan = np.nan


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


# ---------------------------------------------------------------------------
# project_1d: measured values, parent bins
# ---------------------------------------------------------------------------


def test_projection_on_y_of_a_logx_count_histogram_averages_the_measured_x():
    """Projecting on y averages x in linear units, the caller's own values.

    x = 2, 20, 200 on log10 edges [0, 1, 2, 3] (one decade per bin), y = 0.5,
    0.5, 1.5 on edges [0, 1, 2]. Without z the projection averages the other
    axis, x: y-bin (0, 1] holds x = 2 and 20, mean 11 (hand); (1, 2] holds
    x = 200. The display scale of the averaged axis follows the parent's logx.

    ON FAILURE: the code is wrong.
    """
    x = pd.Series([2.0, 20.0, 200.0])
    y = pd.Series([0.5, 0.5, 1.5])
    h = Hist2D(x, y, logx=True, nbins=[np.array([0.0, 1.0, 2.0, 3.0]), [0.0, 1, 2]])

    projected = h.project_1d("y")

    assert projected.data.y.to_numpy() == exact([2.0, 20.0, 200.0])  # the inputs
    assert projected.agg().to_numpy() == exact([11.0, 200.0])
    assert projected.log == (False, True)


def test_projection_keeps_the_sign_of_a_negative_x_on_a_log_axis():
    """A negative x binned as log10|x| is averaged, and handed back, with its sign.

    x = -2, -20, -200, 3 bin by log10|x| = 0.30, 1.30, 2.30, 0.48 on edges
    [0, 1, 2, 3]; y = 0.5, 0.5, 1.5, 1.5 on edges [0, 1, 2]. Projected on y,
    y-bin (0, 1] averages x = -2 and -20 to -11, (1, 2] averages -200 and 3 to
    -98.5 (hand). Projected on x, the subset of rows in bins holding at least
    one row is every row, with the caller's x.

    ON FAILURE: the code is wrong.
    """
    x = pd.Series([-2.0, -20.0, -200.0, 3.0])
    y = pd.Series([0.5, 0.5, 1.5, 1.5])
    h = Hist2D(x, y, logx=True, nbins=[np.array([0.0, 1.0, 2.0, 3.0]), [0.0, 1, 2]])

    assert h.project_1d("y").agg().to_numpy() == exact([-11.0, -98.5])

    subset, kept = h.project_1d("x", project_counts=True).get_subset_above_threshold(1)
    assert kept.to_numpy().all()
    assert subset.x.to_numpy() == exact([-2.0, -20.0, -200.0, 3.0])  # the inputs


def test_projected_counts_hold_the_row_the_parent_clipped_into_an_edge_bin():
    """A y outlier the parent clips into its lowest y-bin is counted there too.

    y = -1000 once and 0.5 ten times, on edges [-1000, 0, 1]: unclipped,
    -1000 sits on the open side of (-1000, 0] and is in no bin. The parent
    clips y to its 0.01st percentile, -1000 + 0.001 * 1000.5 = -998.9995
    (linear interpolation over 11 values), inside (-1000, 0]. x = 0.5 six
    times (the outlier's row first), then 1.5 five times, on edges [0, 1, 2];
    x clips onto itself. Parent counts by hand: one row in y-bin (-1000, 0],
    ten in (0, 1]; six in x-bin (0, 1], five in (1, 2]. The projections are
    those marginal sums.

    ON FAILURE: the code is wrong.
    """
    x = pd.Series([0.5] * 6 + [1.5] * 5)
    y = pd.Series([-1000.0] + [0.5] * 10)
    h = Hist2D(x, y, clip=True, nbins=[np.array([0.0, 1.0, 2.0]), [-1000.0, 0, 1]])

    on_y = h.project_1d("y", project_counts=True).agg()
    on_x = h.project_1d("x", project_counts=True).agg()

    assert on_y.to_numpy() == exact([1.0, 10.0])
    assert on_x.to_numpy() == exact([6.0, 5.0])
    assert on_y.index.equals(h.intervals["y"])


# ---------------------------------------------------------------------------
# get_subset_above_threshold: the caller's values, never inverted
# ---------------------------------------------------------------------------


def test_subset_above_threshold_leaves_a_linear_axis_alone():
    """A projection of a logy parent averages linear y; its subset holds that y.

    The parent bins log10(y) for y = 10, 1000 (log10 edges [0, 2, 4]); the
    projection on x sends the caller's y = 10, 1000, linear, and shows its y
    axis on a log scale. Both rows are in bins of one row, so a threshold of
    1 keeps both, with x = 0.5, 1.5 and y = 10, 1000 as passed.

    ON FAILURE: the code is wrong.
    """
    x = pd.Series([0.5, 1.5])
    y = pd.Series([10.0, 1000.0])
    h = Hist2D(x, y, logy=True, nbins=[np.array([0.0, 1.0, 2.0]), [0.0, 2, 4]])
    projected = h.project_1d("x")

    subset, kept = projected.get_subset_above_threshold(1)

    assert kept.to_numpy().all()
    assert subset.x.to_numpy() == exact([0.5, 1.5])  # the inputs
    assert subset.y.to_numpy() == exact([10.0, 1000.0])  # the inputs


def test_subset_above_threshold_returns_the_callers_signed_values_on_a_log_axis():
    """On a log axis the subset holds the caller's x, negative ones included.

    x = -10, 100 bin by log10|x| = 1, 2 on edges [0, 1.5, 3]; one row per
    bin, so a threshold of 1 keeps both.

    ON FAILURE: the code is wrong.
    """
    x = pd.Series([-10.0, 100.0])
    y = pd.Series([0.5, 0.5])
    h = Hist2D(x, y, logx=True, nbins=[np.array([0.0, 1.5, 3.0]), [0.0, 1]])

    subset, _ = h.get_subset_above_threshold(1)

    assert subset.x.to_numpy() == exact([-10.0, 100.0])  # the inputs
    assert subset.y.to_numpy() == exact([0.5, 0.5])  # the inputs


# ---------------------------------------------------------------------------
# Closure: selections compare on the side the bins close
# ---------------------------------------------------------------------------


def test_hist1d_yrange_selection_follows_left_closed_integer_bins():
    """With an integer nbins, x on an edge is taken from the bin that holds it.

    x = 0, 1, 2, 3, 4 with nbins=2 gives edges [0, 2, 4] (numpy, min to max)
    and bins [0, 2), [2, 4], the last also closed on the right. y = 10, 20,
    30, 40, 50; the y-range is (0, 25] in the first x-bin and (25, 100] in
    the second. By hand: [0, 2) takes x = 0, 1 (y = 10, 20); [2, 4] takes
    x = 2, 3, 4 (y = 30, 40, 50). Every label is taken once.

    ON FAILURE: the code is wrong.
    """
    x = pd.Series([0.0, 1.0, 2.0, 3.0, 4.0])
    y = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
    h = Hist1D(x, y, nbins=2)
    assert h.edges["x"].to_numpy() == exact([0.0, 2.0, 4.0])  # numpy's rule

    ranges = pd.DataFrame(
        {"bottom": [0.0, 25.0], "top": [25.0, 100.0]}, index=h.agg().index
    )
    taken = h.take_data_in_yrange_across_x(
        ranges,
        lambda key, expected_logx: (key.left, key.right),
        lambda row: (row.bottom, row.top),
    )

    assert list(taken) == [0, 1, 2, 3, 4]


#: Five points on the diagonal, x = y = 0 to 4, and label 5 at (2, 1.5).
#: nbins=2 gives edges [0, 2, 4] on both axes, bins [0, 2), [2, 4]. Counts by
#: hand: [0, 2) x [0, 2) holds labels 0, 1; [2, 4] x [0, 2) holds label 5;
#: [2, 4] x [2, 4] holds labels 2, 3, 4.
DIAGONAL_X = pd.Series([0.0, 1.0, 2.0, 3.0, 4.0, 2.0])
DIAGONAL_Y = pd.Series([0.0, 1.0, 2.0, 3.0, 4.0, 1.5])
LOW = pd.Interval(0.0, 2.0, closed="left")
HIGH = pd.Interval(2.0, 4.0, closed="left")


def _diagonal():
    h = Hist2D(DIAGONAL_X, DIAGONAL_Y, nbins=2)
    for axis in ("x", "y"):
        assert h.edges[axis].to_numpy() == exact([0.0, 2.0, 4.0])  # numpy's rule
    return h


def test_hist2d_yrange_selection_follows_left_closed_integer_bins():
    """Both axes compare left-closed, the last bin also closed on the right.

    The y-range is [0, 2) in x-bin [0, 2) and [2, 4] in x-bin [2, 4]. By
    hand: the first takes labels 0, 1; the second takes 2, 3, 4 (4 sits on
    both outer edges). Label 5, x = 2 with y = 1.5, is in x-bin [2, 4], whose
    y-range it is below, so it is not taken.

    ON FAILURE: the code is wrong.
    """
    h = _diagonal()
    ranges = pd.DataFrame(
        {"bottom": [0.0, 2.0], "top": [2.0, 4.0]},
        index=h.agg().unstack("x").columns,
    )

    taken = h.take_data_in_yrange_across_x(
        ranges,
        lambda key, expected_logx: (key.left, key.right),
        lambda row, expected_logy: (row.bottom, row.top),
    )

    assert list(taken) == [0, 1, 2, 3, 4]


def test_contour_selection_follows_left_closed_integer_bins():
    """Rows on a bin edge are labelled with the x-bin that holds them.

    At level 2: in x-bin [0, 2) only y-bin [0, 2) reaches 2 (two rows), so
    labels 0 and 1 get [0, 2); in x-bin [2, 4] only y-bin [2, 4] does (three
    rows), so labels 2, 3 and 4 get [2, 4]. Label 5's bin holds one row: NaN.

    ON FAILURE: the code is wrong.
    """
    h = _diagonal()

    labelled = h.id_data_above_contour(2)

    got = [None if pd.isna(v) else v for v in labelled]
    assert got == [LOW, LOW, HIGH, HIGH, HIGH, None]
