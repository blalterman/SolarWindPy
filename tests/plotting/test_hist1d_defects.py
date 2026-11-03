# Spent-When: PERMANENT(the repository stops shipping Hist1D)
# Supersedes: none
"""Contract tests for two Hist1D behaviours fixed together.

``construct_cdf`` returns its rows under the caller's original row labels,
sorted by x, with ``position`` taken from the row's rank in that order.
``take_data_in_yrange_across_x`` rejects a selector naming x-bins the
histogram lacks with ``ValueError``, as Hist2D does, and only warns when the
selector omits some of the histogram's bins.

Every expected value is hand-computed from the literal inputs below.
"""

import logging

import numpy as np
import pandas as pd
import pytest

from solarwindpy.plotting.hist1d import Hist1D
from tests.tolerances import exact

# ---------------------------------------------------------------------------
# construct_cdf keeps the original row labels
# ---------------------------------------------------------------------------

# x = 3, 1, 4, 2 at four hourly timestamps; sorted by x the labels run
# 01:00 (1), 03:00 (2), 00:00 (3), 02:00 (4).
TIMES = pd.date_range("2020-01-01", periods=4, freq="h")
TIME_X = pd.Series([3.0, 1.0, 4.0, 2.0], index=TIMES)


def test_cdf_keeps_timestamp_labels_sorted_by_x():
    """A timestamp-indexed sample keeps its timestamps, reordered by x.

    Hand: sorted x is 1, 2, 3, 4 at labels 01:00, 03:00, 00:00, 02:00, with
    positions 0, 1/3, 2/3, 1 (i / (n - 1), n = 4).

    ON FAILURE: the code is wrong.
    """
    cdf = Hist1D(TIME_X, nbins=np.array([0.0, 5.0])).construct_cdf()

    assert list(cdf.columns) == ["x", "position"]
    assert cdf.index.tolist() == [
        pd.Timestamp("2020-01-01 01:00"),
        pd.Timestamp("2020-01-01 03:00"),
        pd.Timestamp("2020-01-01 00:00"),
        pd.Timestamp("2020-01-01 02:00"),
    ]
    assert cdf["x"].to_numpy() == exact([1.0, 2.0, 3.0, 4.0])
    assert cdf["position"].to_numpy() == exact([0.0, 1 / 3, 2 / 3, 1.0])


# Non-contiguous integer labels. Label 20 (x = 9) is outside the single bin
# (0, 5] and is not in the CDF; the other four sort to 30, 50, 10, 40.
GAPPY_X = pd.Series([2.5, 0.5, 9.0, 1.5, 3.5], index=[10, 30, 20, 50, 40])


def test_cdf_keeps_non_contiguous_integer_labels_and_ranks_positions():
    """Positions come from rank 0..n-1 in x order, not from the row labels.

    Hand: kept labels 30, 50, 10, 40 hold x 0.5, 1.5, 2.5, 3.5, at positions
    0, 1/3, 2/3, 1. Positions taken from the labels would not be evenly
    spaced and would not start at 0.

    ON FAILURE: the code is wrong.
    """
    cdf = Hist1D(GAPPY_X, nbins=np.array([0.0, 5.0])).construct_cdf(only_plotted=False)

    assert cdf.index.tolist() == [30, 50, 10, 40]
    assert cdf["x"].to_numpy() == exact([0.5, 1.5, 2.5, 3.5])
    assert cdf["position"].to_numpy() == exact([0.0, 1 / 3, 2 / 3, 1.0])


def test_cdf_x_at_each_label_is_that_rows_measurement():
    """Each label's cdf x is the measurement the caller stored at that label.

    Identity: ``cdf.x`` at label k equals the input x at label k.

    ON FAILURE: the code is wrong.
    """
    cdf = Hist1D(GAPPY_X, nbins=np.array([0.0, 5.0])).construct_cdf(only_plotted=False)

    assert cdf["x"].to_numpy() == exact(GAPPY_X.loc[cdf.index].to_numpy())


def test_logx_cdf_keeps_labels_and_linear_x():
    """Under logx the labels survive and x is in linear units.

    Hand: x = 100, 1, 10 at labels 7, 3, 5 sort to 1, 10, 100 at labels 3,
    5, 7, positions 0, 0.5, 1.

    ON FAILURE: the code is wrong.
    """
    x = pd.Series([100.0, 1.0, 10.0], index=[7, 3, 5])

    cdf = Hist1D(x, logx=True, nbins=np.array([-1.0, 3.0])).construct_cdf()

    assert cdf.index.tolist() == [3, 5, 7]
    assert cdf["x"].to_numpy() == exact([1.0, 10.0, 100.0])
    assert cdf["position"].to_numpy() == exact([0.0, 0.5, 1.0])


# ---------------------------------------------------------------------------
# take_data_in_yrange_across_x validates the selector's x-bins
# ---------------------------------------------------------------------------

# Bins (0, 1] and (1, 2]; window (5, 6] in each. Labels 10 and 13 fall in the
# first bin's window, label 12 in the second's, label 11 sits on the bottom.
EDGE_X = pd.Series([1.0, 1.5, 2.0, 0.5], index=[10, 11, 12, 13])
EDGE_Y = pd.Series([5.5, 5.0, 6.0, 5.5], index=[10, 11, 12, 13])


def _hist():
    return Hist1D(EDGE_X, EDGE_Y, nbins=np.array([0.0, 1.0, 2.0]))


def _interval_bounds(interval, expected_logx):
    return interval.left, interval.right


def _row_bounds(row):
    return row["bottom"], row["top"]


def test_selector_naming_unavailable_bins_raises_value_error():
    """A selector indexed on x-bins the histogram lacks raises ``ValueError``.

    ON FAILURE: the code is wrong.
    """
    hist = _hist()
    foreign = pd.IntervalIndex.from_breaks([0.0, 0.5, 2.0], closed="right")
    ranges = pd.DataFrame({"bottom": 5.0, "top": 6.0}, index=foreign)

    with pytest.raises(ValueError, match="Need a way to drop values in selector"):
        hist.take_data_in_yrange_across_x(ranges, _interval_bounds, _row_bounds)


def test_selector_omitting_bins_warns_and_takes_only_the_named_bins(caplog):
    """A selector naming a subset of the bins warns and selects in those bins.

    Hand: only bin (0, 1] is named, so labels 10 and 13 are taken and label
    12, inside the unnamed bin's window, is not.

    ON FAILURE: the code is wrong.
    """
    hist = _hist()
    ranges = pd.DataFrame({"bottom": 5.0, "top": 6.0}, index=hist.agg().index[:1])

    with caplog.at_level(logging.WARNING):
        taken = hist.take_data_in_yrange_across_x(ranges, _interval_bounds, _row_bounds)

    np.testing.assert_array_equal(taken, [10, 13])
    assert "Dropping 1 intervals from available for selecting." in caplog.text
