# Spent-When: PERMANENT(plot classes stop sourcing data through BinnedData)
# Supersedes: none
"""Contract tests for four rulings on the plotting data path.

- Infinite values: a plot keeps no row whose x, y or z is +/-inf, either in
  the caller's data or after ``log10(abs())`` (``log10(0) = -inf``), and a
  ``BinnedData`` gives such a value code -1, clipped or not.
- ``set_log`` on a built plot cannot change the log of an axis its data and
  bins were built on; it raises ``ValueError``.
- Clip quantiles are computed over the finite values only, and +/-inf is
  clipped to them like any other value beyond a quantile.
- Spiral refinement stops with ``ValueError`` when more than ``min_per_bin``
  points share one (x, y), instead of splitting forever.

Every input is placed by hand; expected rows, codes and quantiles are written
from those inputs. A quantile of ``n`` sorted values at ``q`` is read at
position ``q * (n - 1)`` with linear interpolation, the default of
:meth:`pandas.Series.quantile`.
"""

import numpy as np
import pandas as pd
import pytest

from solarwindpy.plotting.base import Base, LogAxes
from solarwindpy.plotting.binned import BinnedData
from solarwindpy.plotting.hist1d import Hist1D
from solarwindpy.plotting.hist2d import Hist2D
from solarwindpy.plotting.scatter import Scatter
from solarwindpy.plotting.spiral import SpiralMesh, SpiralPlot2D
from tests.tolerances import exact

INF = np.inf


# ---------------------------------------------------------------------------
# Rows: +/-inf is excluded like NaN
# ---------------------------------------------------------------------------


def test_hist1d_keeps_no_row_whose_logged_x_is_infinite():
    """``logx`` of x = 0 is -inf; that row is not in ``data`` and not counted.

    x = 0, 1, 10, 100 gives log10|x| = -inf, 0, 1, 2; the edges put 0, 1, 2
    in one bin each.

    ON FAILURE: the code is wrong.
    """
    x = pd.Series([0.0, 1.0, 10.0, 100.0])
    h = Hist1D(x, logx=True, nbins=np.array([-0.5, 0.5, 1.5, 2.5]))
    assert list(h.data.index) == [1, 2, 3]
    assert h.data.loc[:, "x"].to_numpy() == exact([0.0, 1.0, 2.0])
    assert h.agg().to_numpy() == exact([1.0, 1.0, 1.0])


def test_hist2d_keeps_no_row_infinite_in_x_y_or_z_before_or_after_log():
    """Rows with +inf y, x = 0 on a log axis, or -inf z are all excluded.

    Rows 0 and 1 are finite after log10; row 2 has y = +inf, row 3 has
    x = 0 (log10 -inf) and row 4 has z = -inf.

    ON FAILURE: the code is wrong.
    """
    x = pd.Series([1.0, 10.0, 100.0, 0.0, 1000.0])
    y = pd.Series([1.0, 10.0, INF, 10.0, 100.0])
    z = pd.Series([2.0, 4.0, 6.0, 8.0, -INF])
    edges = np.array([-0.5, 0.5, 1.5, 2.5, 3.5])
    h = Hist2D(x, y, z, logx=True, logy=True, nbins=edges)
    assert list(h.data.index) == [0, 1]
    assert np.isfinite(h.data.to_numpy()).all()
    assert h.agg().dropna().to_numpy() == exact([2.0, 4.0])


def test_scatter_keeps_no_row_infinite_in_x_or_z():
    """Scatter excludes a row with x = +inf and a row with z = -inf.

    ON FAILURE: the code is wrong.
    """
    x = pd.Series([1.0, INF, 3.0, 4.0])
    y = pd.Series([1.0, 2.0, 3.0, 4.0])
    z = pd.Series([5.0, 6.0, -INF, 8.0])
    sc = Scatter(x, y, z)
    assert list(sc.data.index) == [0, 3]


def test_scatter_with_datetime_x_drops_nat_and_infinite_y():
    """A datetime x is tested for NaT only; y = +inf still drops its row.

    ON FAILURE: the code is wrong.
    """
    x = pd.Series(pd.to_datetime(["2020-01-01", None, "2020-01-03", "2020-01-04"]))
    y = pd.Series([1.0, 2.0, 3.0, INF])
    sc = Scatter(x, y)
    assert list(sc.data.index) == [0, 2]


def test_spiral_keeps_no_row_whose_logged_y_is_infinite():
    """``logy`` of y = 0 is -inf; SpiralPlot2D does not keep that row.

    ON FAILURE: the code is wrong.
    """
    x = pd.Series([1.0, 2.0, 3.0, 4.0])
    y = pd.Series([10.0, 0.0, 100.0, 1000.0])
    s = SpiralPlot2D(x, y, logy=True, initial_bins=1)
    assert list(s.data.index) == [0, 2, 3]
    assert s.data.loc[:, "y"].to_numpy() == exact([1.0, 2.0, 3.0])


def test_only_infinite_rows_raise_value_error():
    """A plot with no finite row raises, as it does with only NaN rows.

    ON FAILURE: the code is wrong.
    """
    x = pd.Series([0.0, 0.0, INF])
    with pytest.raises(ValueError, match="Hist1D.*exclusively NaNs or infinite"):
        Hist1D(x, logx=True, nbins=np.array([0.0, 1.0]))


def test_a_plot_sharing_binned_data_keeps_no_row_whose_logged_value_is_infinite():
    """The shared ``BinnedData`` codes x = 0 (log10 -inf) -1; the plot drops it.

    ON FAILURE: the code is wrong.
    """
    frame = pd.DataFrame({"a": [1.0, 10.0, 0.0, 100.0], "b": [0.5, 1.5, 2.5, 3.5]})
    b = BinnedData(
        frame,
        {"a": [-0.5, 0.5, 1.5, 2.5], "b": [0.0, 2.0, 4.0]},
        log={"a": True},
    )
    assert b.codes("a").tolist() == [0, 1, -1, 2]
    h = Hist2D(frame["a"], frame["b"], nbins=b)
    assert list(h.data.index) == [0, 1, 3]


@pytest.mark.parametrize("clip", [True, "l", "u"])
def test_binned_data_codes_an_infinite_logged_value_minus_one_when_clipped(clip):
    """Clipping never moves +/-inf into a bin: its code stays -1.

    x = 0 is -inf after log10 and x = +inf stays +inf; the finite values are
    log10 = 0, 1, 2, 3. Clipping to the finite quantiles would otherwise
    place both infinities in an edge bin.

    ON FAILURE: the code is wrong.
    """
    frame = pd.DataFrame({"a": [0.0, 1.0, 10.0, 100.0, 1000.0, INF]})
    b = BinnedData(
        frame,
        {"a": [-0.5, 0.5, 1.5, 2.5, 3.5]},
        log={"a": True},
        clip={"a": clip},
    )
    assert b.codes("a").tolist() == [-1, 0, 1, 2, 3, -1]


@pytest.mark.parametrize("closed", ["left", "right"])
def test_binned_data_codes_infinity_minus_one_even_with_infinite_edges(closed):
    """Edges reaching +/-inf still give +/-inf code -1, as the Notes promise.

    ON FAILURE: the code is wrong.
    """
    frame = pd.DataFrame({"a": [-1.0, 1.0, INF, -INF]})
    bins = pd.IntervalIndex.from_breaks([-INF, 0.0, INF], closed=closed)
    b = BinnedData(frame, {"a": bins})
    assert b.codes("a").tolist() == [0, 1, -1, -1]


# ---------------------------------------------------------------------------
# set_log on a built plot
# ---------------------------------------------------------------------------

X = pd.Series([1.0, 10.0, 100.0])
Y = pd.Series([1.0, 2.0, 3.0])
EDGES = np.array([0.0, 1.5, 3.5, 150.0])


@pytest.mark.parametrize("axis", ["x", "y"])
def test_set_log_cannot_change_a_binned_axis_of_a_built_hist2d(axis):
    """Changing the log of x or y after building raises; log and data stay.

    ON FAILURE: the code is wrong.
    """
    h = Hist2D(X, Y, nbins=EDGES)
    with pytest.raises(ValueError, match="bins depend on log"):
        h.set_log(**{axis: True})
    assert h.log == LogAxes(False, False)
    assert h.data.loc[:, "x"].to_numpy() == exact([1.0, 10.0, 100.0])


def test_set_log_cannot_change_x_of_a_built_hist1d_but_may_change_y():
    """Hist1D bins x, so its log is fixed; y is drawn, not binned, so it may change.

    ON FAILURE: the code is wrong.
    """
    h = Hist1D(X, nbins=EDGES)
    with pytest.raises(ValueError, match="build a new plot or BinnedData"):
        h.set_log(x=True)
    h.set_log(y=True)
    assert h.log == LogAxes(False, True)
    assert h.data.loc[:, "x"].to_numpy() == exact([1.0, 10.0, 100.0])


def test_set_log_cannot_change_an_axis_of_a_built_spiral():
    """SpiralPlot2D's mesh is built on its logged data; its log is fixed.

    ON FAILURE: the code is wrong.
    """
    s = SpiralPlot2D(X, Y, logx=True, initial_bins=1)
    with pytest.raises(ValueError, match="bins depend on log"):
        s.set_log(x=False)
    assert s.log == LogAxes(True, False)


def test_set_log_repeating_the_built_setting_is_allowed():
    """Passing the log a plot was built with changes nothing and does not raise.

    ON FAILURE: the code is wrong.
    """
    h = Hist2D(X, Y, logx=True, nbins=np.array([-0.5, 0.5, 1.5, 2.5]))
    h.set_log(x=True, y=False)
    assert h.log == LogAxes(True, False)


# ---------------------------------------------------------------------------
# Clip quantiles over finite values
# ---------------------------------------------------------------------------


def test_clip_quantiles_ignore_infinities_and_clip_them_to_the_finite_quantiles():
    """Quantiles come from the finite values; +/-inf is clipped to them.

    The finite values are 0, 1, ..., 10000 (n = 10001), so the 0.01st and
    99.99th percentiles sit at positions 1 and 9999: values 1 and 9999. NaN
    stays NaN.

    ON FAILURE: the code is wrong.
    """
    data = pd.Series(np.r_[np.arange(10001.0), INF, -INF, np.nan])
    clipped = Base.clip_data(data, True)
    assert clipped.iloc[[0, 1, 9999, 10000]].to_numpy() == exact(
        [1.0, 1.0, 9999.0, 9999.0]
    )
    assert clipped.iloc[[10001, 10002]].to_numpy() == exact([9999.0, 1.0])
    assert np.isnan(clipped.iloc[10003])


def test_an_infinite_value_no_longer_makes_the_upper_quantile_nan():
    """With 0, 1, 2, 3, 4 and +inf, the upper bound is 3.9996, not NaN.

    Over the finite values (n = 5) the 99.99th percentile is at position
    0.9999 * 4 = 3.9996, between 3 and 4: 3.9996. Including +inf made it
    NaN, so +inf was left unclipped.

    ON FAILURE: the code is wrong.
    """
    data = pd.Series([0.0, 1.0, 2.0, 3.0, 4.0, INF])
    clipped = Base.clip_data(data, "u")
    assert clipped.to_numpy() == exact([0.0, 1.0, 2.0, 3.0, 3.9996, 3.9996])


@pytest.mark.parametrize(
    "clip, expected",
    [("l", [1.0, 9999.0, 1.0, INF]), ("u", [1.0, 9999.0, -INF, 9999.0])],
)
def test_one_tail_clip_leaves_the_other_infinity(clip, expected):
    """``"l"`` clips -inf only, ``"u"`` clips +inf only.

    Columns of a DataFrame are clipped one by one; column ``b`` is ``a``
    shifted by 1 (finite values 1 to 10001, quantiles 2 and 10000).

    ON FAILURE: the code is wrong.
    """
    a = np.r_[np.arange(10001.0), -INF, INF]
    frame = pd.DataFrame({"a": a, "b": a + 1.0})
    clipped = Base.clip_data(frame, clip)
    picks = [1, 9999, 10001, 10002]
    assert clipped.loc[picks, "a"].to_numpy() == exact(expected)
    shifted = [v + 1.0 for v in expected]
    assert clipped.loc[picks, "b"].to_numpy() == exact(shifted)


# ---------------------------------------------------------------------------
# Spiral refinement of identical points
# ---------------------------------------------------------------------------


def test_spiral_with_more_identical_points_than_min_per_bin_raises():
    """Three points at (0.5, 0.5) with ``min_per_bin=2`` cannot be split apart.

    ON FAILURE: the code is wrong.
    """
    x = pd.Series([0.0, 1.0, 2.0, 3.0, 0.5, 0.5, 0.5])
    with pytest.raises(ValueError, match=r"3 points at \(0\.5, 0\.5\)"):
        SpiralPlot2D(x, x.copy(), initial_bins=1, min_per_bin=2)


def test_spiral_mesh_with_identical_points_raises_when_refining_by_counting():
    """The counting refinement, used for unsorted edges, stops the same way.

    The x edges 0, 4, 2 are not increasing, so cells are counted rather
    than descended; four points sit at (1, 1).

    ON FAILURE: the code is wrong.
    """
    x = pd.Series([1.0, 1.0, 1.0, 1.0, 3.0])
    y = pd.Series([1.0, 1.0, 1.0, 1.0, 3.0])
    mesh = SpiralMesh(
        x, y, np.array([0.0, 4.0, 2.0]), np.array([0.0, 4.0]), min_per_bin=3
    )
    with pytest.raises(ValueError, match="duplicated rows"):
        mesh.generate_mesh(progress=False)


@pytest.mark.parametrize(
    "a, b, edges",
    [
        (1.0, np.nextafter(1.0, 2.0), [0.0, 2.0]),
        (0.0, 5e-324, [-np.finfo(float).max / 2, np.finfo(float).max / 2]),
    ],
    ids=["adjacent-floats-at-one", "smallest-subnormal-in-widest-cell"],
)
def test_spiral_mesh_separates_two_distinct_points_however_close(a, b, edges):
    """Two distinct points end in different cells; the depth guard never trips.

    The second case is the deepest float64 allows: a cell as wide as the
    descent permits (edges at +/- half the largest float) around the two
    smallest non-negative floats, 0 and 5e-324.

    ON FAILURE: the code is wrong.
    """
    x = pd.Series([a, b])
    y = pd.Series([1.0, 1.0])
    mesh = SpiralMesh(x, y, np.array(edges), np.array([0.0, 2.0]), min_per_bin=1)
    mesh.place_spectra_in_mesh(progress=False)
    ids = mesh.bin_id.id
    assert ids[0] != ids[1]
    assert (ids != mesh.bin_id.fill).all()
