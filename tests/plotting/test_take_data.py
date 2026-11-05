# Spent-When: PERMANENT(the fixed-grid plots stop offering take_data_in_yrange_across_x)
# Supersedes: none
"""Tests for the one ``take_data_in_yrange_across_x`` that Hist1D and Hist2D share.

The method selects, for each x range, the rows whose y lies in that range's
y window. Both histograms run the same code: the y-bounds callback gets
``expected_logy`` from either (False for a ``Hist1D``, whose y is never
logged), and ranges that overlap in x select a row once per range that holds
it. Expected labels are by hand on the rows written below.
"""

import re

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")

from solarwindpy.plotting.hist1d import Hist1D  # noqa: E402
from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402

# x in (0, 1], (1, 2], (2, 3] by explicit (right-closed) edges, one y each.
X = pd.Series([0.5, 1.5, 2.5, 0.9], index=[10, 11, 12, 13])
Y = pd.Series([5.0, 6.0, 7.0, 8.0], index=[10, 11, 12, 13])
EDGES = np.array([0.0, 1.0, 2.0, 3.0])


def _build(cls):
    if cls is Hist1D:
        return Hist1D(X, Y, nbins=EDGES)
    return Hist2D(X, Y, nbins=[EDGES, np.array([0.0, 10.0])])


def test_hist1d_and_hist2d_share_one_method():
    """Neither class defines its own copy; both use the fixed-grid one.

    ON FAILURE: the code is wrong.
    """
    assert "take_data_in_yrange_across_x" not in Hist1D.__dict__
    assert "take_data_in_yrange_across_x" not in Hist2D.__dict__
    assert Hist1D.take_data_in_yrange_across_x is Hist2D.take_data_in_yrange_across_x


def test_hist1d_hands_expected_logy_false_to_the_y_callback():
    """A Hist1D's y is never logged, so the y callback gets expected_logy=False.

    ON FAILURE: the code is wrong.
    """
    h = _build(Hist1D)
    ranges = pd.DataFrame({"bottom": 0.0, "top": 10.0}, index=h.intervals["x"])
    flags = []

    def get_y_bounds(row, **kw):
        flags.append(kw)
        return row.bottom, row.top

    taken = h.take_data_in_yrange_across_x(
        ranges, lambda k, expected_logx: (k.left, k.right), get_y_bounds
    )
    assert flags == [{"expected_logy": False}] * 3
    assert list(taken) == [10, 11, 12, 13]


@pytest.mark.parametrize("cls", [Hist1D, Hist2D])
def test_overlapping_x_ranges_select_a_row_once_per_range(cls):
    """Ranges widened left by 0.2 overlap; label 13 (x = 0.9) lies in two.

    Range (0, 1] holds 10 and 13, (0.8, 2] holds 13 and 11, (1.8, 3] holds
    12: label 13 is taken twice. y windows (0, 10] keep every row.

    ON FAILURE: the code is wrong.
    """
    h = _build(cls)
    ranges = pd.DataFrame({"bottom": 0.0, "top": 10.0}, index=h.intervals["x"])

    def get_x_bounds(k, expected_logx):
        return (k.left - 0.2 if k.left > 0 else k.left), k.right

    def get_y_bounds(row, expected_logy=False):
        return row.bottom, row.top

    taken = h.take_data_in_yrange_across_x(ranges, get_x_bounds, get_y_bounds)
    assert list(taken) == [10, 11, 12, 13, 13]


@pytest.mark.parametrize("cls", [Hist1D, Hist2D])
def test_each_range_keeps_its_own_y_window(cls):
    """Windows (4, 5], (5, 6.5], (6.5, 7]: labels 10, 11, 12; 13 (y = 8) is out.

    ON FAILURE: the code is wrong.
    """
    h = _build(cls)
    ranges = pd.DataFrame(
        {"bottom": [4.0, 5.0, 6.5], "top": [5.0, 6.5, 7.0]}, index=h.intervals["x"]
    )
    taken = h.take_data_in_yrange_across_x(
        ranges,
        lambda k, expected_logx: (k.left, k.right),
        lambda row, expected_logy=False: (row.bottom, row.top),
    )
    assert list(taken) == [10, 11, 12]


@pytest.mark.parametrize("cls", [Hist1D, Hist2D])
def test_the_first_invalid_range_in_the_callers_order_is_named(cls):
    """Two inverted y windows: the error names the first one as given.

    ON FAILURE: the code is wrong.
    """
    h = _build(cls)
    iv = h.intervals["x"]
    ranges = pd.DataFrame(
        {"bottom": [0.0, 9.0, 8.0], "top": [10.0, 1.0, 1.0]}, index=iv[::-1]
    )
    with pytest.raises(
        ValueError, match=re.escape(f"Need bottom < top for x-bin {iv[1]}")
    ):
        h.take_data_in_yrange_across_x(
            ranges,
            lambda k, expected_logx: (k.left, k.right),
            lambda row, expected_logy=False: (row.bottom, row.top),
        )
