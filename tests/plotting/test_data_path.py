"""Contract tests for the rulings on the plot data path.

- ``clip`` accepts True/False, the strings ``"l"`` and ``"u"`` in any case,
  and a pair ``(lower, upper)``. Any other string, the removed ``"lower"``,
  ``"upper"`` and ``"both"`` included, raises ``ValueError`` naming the
  accepted ones, when the plot or ``BinnedData`` is built and from
  ``Base.clip_data``.
- x, y and z are aligned by label. When their indexes differ and a column
  that has to be aligned repeats labels, alignment is ambiguous: the plot
  raises ``ValueError`` naming the column. Identical indexes, repeated labels
  included, and a column with unique labels aligned onto repeated ones keep
  working.
- Edges from an integer ``nbins`` enclose every sample, also where the data
  are so large that ``10**precision`` is below their float spacing.
- An object-dtype column of numbers is treated as the numbers it holds, so a
  +/-inf in it drops the row exactly as in a float column.
- Infinite values: a plot keeps no row whose x, y or z is +/-inf, either in
  the caller's data or after ``log10(abs())`` (``log10(0) = -inf``), and a
  ``BinnedData`` gives such a value code -1, clipped or not.
- ``set_log`` on a built plot cannot change the log of an axis its data and
  bins were built on; it raises ``ValueError``.
- Clip quantiles are computed over the finite values only, and +/-inf is
  clipped to them like any other value beyond a quantile.
- Spiral refinement stops with ``ValueError`` when more than ``min_per_bin``
  points share one (x, y), instead of splitting forever.
- Every data variable (x, y, z, and a ``Scatter``'s size and alpha) holds one
  value per point. A scalar raises ``TypeError`` naming the variable; a
  constant marker size or opacity goes to ``make_plot`` as ``s`` or ``alpha``.

Every input is placed by hand. Expected counts, means, rows, codes and
quantiles are worked out from those inputs in each test's comments. A quantile
of ``n`` sorted values at ``q`` is read at position ``q * (n - 1)`` with
linear interpolation, the default of :meth:`pandas.Series.quantile`.
"""

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")

from solarwindpy.plotting.base import Base, ClipAxes, LogAxes  # noqa: E402
from solarwindpy.plotting.binned import BinnedData  # noqa: E402
from solarwindpy.plotting.hist1d import Hist1D  # noqa: E402
from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402
from solarwindpy.plotting.scatter import Scatter  # noqa: E402
from solarwindpy.plotting.spiral import SpiralMesh, SpiralPlot2D  # noqa: E402
from tests.tolerances import exact  # noqa: E402

# 1..10: the default cuts, the 0.05th and 99.95th percentiles, are
# 1 + 9 * 0.0005 = 1.0045 and 10 - 9 * 0.0005 = 9.9955 by hand.
SERIES = pd.Series(np.arange(1.0, 11.0), name="x")
LOWER = np.r_[1.0045, np.arange(2.0, 11.0)]
UPPER = np.r_[np.arange(1.0, 10.0), 9.9955]
BOTH = np.r_[1.0045, np.arange(2.0, 10.0), 9.9955]

ACCEPTED_FORMS = [
    ("l", LOWER),
    ("L", LOWER),
    ("u", UPPER),
    ("U", UPPER),
    (True, BOTH),
]
# The long strings were removed: "l", "u" and True already name each case.
REMOVED_STRINGS = ["lower", "upper", "both"]
REJECTED_FORMS = ["", "foo", "lo", "lower ", "uppr", "b", *REMOVED_STRINGS]
ACCEPTED_MESSAGE = "'l' or 'u'"

# A pair (lower, upper): True is that tail's default cut, False no clip, a
# number the quantile itself. Over 1..10 the 1% quantile is 1 + 9 * 0.01 = 1.09.
PAIR_FORMS = [
    ((True, True), BOTH),
    ((True, False), LOWER),
    ((False, True), UPPER),
    ((False, False), SERIES.to_numpy()),
    ((0.01, True), np.r_[1.09, np.arange(2.0, 10.0), 9.9955]),
    ([0.01, True], np.r_[1.09, np.arange(2.0, 10.0), 9.9955]),
    ((0.0, 1.0), SERIES.to_numpy()),  # the minimum and maximum move nothing
]
# Each breaks 0 <= lower < 0.5 < upper <= 1, or is not a pair.
REJECTED_PAIRS = [
    (0.6, 0.9),
    (0.1, 0.4),
    (0.5, True),
    (True, 0.5),
    (-0.1, True),
    (True, 1.1),
    (float("nan"), True),
    (0.1,),
    (0.1, 0.5, 0.9),
]
PAIR_MESSAGE = r"\(lower, upper\) pair"
PAIR_BUILDERS = [
    lambda c: Hist1D(SERIES, clip=c, nbins=3),
    lambda c: Hist2D(SERIES, SERIES.rename("y"), clip=c, nbins=3),
    lambda c: Hist2D(SERIES, SERIES.rename("y"), clip={"y": c}, nbins=3),
    lambda c: Scatter(SERIES, SERIES.rename("y"), clip={"z": c}),
    lambda c: SpiralPlot2D(SERIES, SERIES.rename("y"), clip=c),
    lambda c: BinnedData(SERIES.to_frame(), {"x": [0, 5, 11]}, clip={"x": c}),
]
PAIR_BUILDER_IDS = [
    "Hist1D",
    "Hist2D",
    "Hist2D-mapping",
    "Scatter-z",
    "Spiral",
    "BinnedData",
]


class TestClipSetting:
    @pytest.mark.parametrize(
        "clip, expected", ACCEPTED_FORMS, ids=[repr(c) for c, _ in ACCEPTED_FORMS]
    )
    def test_clip_data_accepts_each_documented_form(self, clip, expected):
        """Each documented form clips the tail(s) it names, in any case.

        True and each tail string clip at the default cuts, the 0.05th and
        99.95th percentiles.
        ON FAILURE: the code is wrong.
        """
        result = Base.clip_data(SERIES, clip)
        assert result.to_numpy() == exact(expected)

    @pytest.mark.parametrize("clip", REJECTED_FORMS)
    def test_clip_data_rejects_any_other_string(self, clip):
        """An empty or unknown string raises ValueError naming the accepted ones.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(ValueError, match=ACCEPTED_MESSAGE):
            Base.clip_data(SERIES, clip)

    @pytest.mark.parametrize("clip", ["", "foo", *REMOVED_STRINGS])
    @pytest.mark.parametrize(
        "build",
        [
            lambda c: Hist1D(SERIES, clip=c, nbins=3),
            lambda c: Hist2D(SERIES, SERIES.rename("y"), clip=c, nbins=3),
            lambda c: Hist2D(SERIES, SERIES.rename("y"), clip={"y": c}, nbins=3),
            lambda c: Scatter(SERIES, SERIES.rename("y"), clip={"z": c}),
            lambda c: SpiralPlot2D(SERIES, SERIES.rename("y"), clip=c),
            lambda c: BinnedData(SERIES.to_frame(), {"x": [0, 5, 11]}, clip={"x": c}),
        ],
        ids=["Hist1D", "Hist2D", "Hist2D-mapping", "Scatter-z", "Spiral", "BinnedData"],
    )
    def test_constructors_reject_an_unknown_clip_string(self, build, clip):
        """A plot or BinnedData given an unknown clip string raises when built.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(ValueError, match=ACCEPTED_MESSAGE):
            build(clip)

    @pytest.mark.parametrize(
        "clip, expected", PAIR_FORMS, ids=[repr(c) for c, _ in PAIR_FORMS]
    )
    def test_clip_data_clips_a_pair_at_its_cuts(self, clip, expected):
        """A pair clips each tail at its own cut: True the default, False none.

        ON FAILURE: the code is wrong.
        """
        result = Base.clip_data(SERIES, clip)
        assert result.to_numpy() == exact(expected)

    @pytest.mark.parametrize(
        "pair, shorthand", [((True, False), "l"), ((False, True), "u")]
    )
    def test_a_one_tail_pair_equals_its_shorthand(self, pair, shorthand):
        """``"l"`` is ``(True, False)`` and ``"u"`` is ``(False, True)``.

        ON FAILURE: the code is wrong.
        """
        pd.testing.assert_series_equal(
            Base.clip_data(SERIES, pair),
            Base.clip_data(SERIES, shorthand),
            check_exact=True,
        )

    @pytest.mark.parametrize("clip", REJECTED_PAIRS, ids=repr)
    def test_clip_data_rejects_a_pair_outside_its_bounds(self, clip):
        """A pair needs 0 <= lower < 0.5 < upper <= 1, or it raises ValueError.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(ValueError, match=PAIR_MESSAGE):
            Base.clip_data(SERIES, clip)

    def test_clip_data_rejects_a_cut_of_another_type(self):
        """A cut that is neither a bool nor a number raises TypeError.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(TypeError, match=PAIR_MESSAGE):
            Base.clip_data(SERIES, ("l", True))

    @pytest.mark.parametrize("build", PAIR_BUILDERS, ids=PAIR_BUILDER_IDS)
    def test_constructors_reject_a_pair_outside_its_bounds(self, build):
        """A plot or BinnedData given clip=(0.6, 0.9) raises when built.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(ValueError, match=PAIR_MESSAGE):
            build((0.6, 0.9))

    def test_constructors_keep_a_pair_as_a_tuple(self):
        """A pair reads back from ``clip`` as a tuple, a list included.

        ON FAILURE: the code is wrong.
        """
        y = SERIES.rename("y")
        assert Hist1D(SERIES, clip=(0.01, True), nbins=3).clip == ClipAxes(
            (0.01, True), False, False
        )
        assert Hist2D(SERIES, y, clip=[0.01, True], nbins=3).clip == ClipAxes(
            (0.01, True), (0.01, True), False
        )
        b = BinnedData(SERIES.to_frame(), {"x": [0, 5, 11]}, clip={"x": [False, 0.9]})
        assert b.clip_of("x") == (False, 0.9)

    def test_constructors_keep_the_accepted_forms(self):
        """Accepted forms build, and ``clip`` reads back what was passed.

        ON FAILURE: the code is wrong.
        """
        y = SERIES.rename("y")
        assert Hist2D(SERIES, y, clip="L", nbins=3).clip == ClipAxes("L", "L", False)
        assert Scatter(SERIES, y, clip={"z": "U"}).clip == ClipAxes(False, False, "U")
        b = BinnedData(SERIES.to_frame(), {"x": [0, 5, 11]}, clip={"x": "u"})
        assert b.clip_of("x") == "u"


# Rows on four timestamps, the second one repeated.
REPEATED = pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-02", "2020-01-03"])
UNIQUE = pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"])


class TestAlignmentWithRepeatedLabels:
    def test_identical_repeated_indexes_keep_working(self):
        """x, y and z on one index that repeats a label are taken row by row.

        x = y = 1, 2, 3, 4 and z = 5, 6, 7, 8. nbins=2 splits 1..4 at 2.5,
        so bin (0, 0) holds rows 0 and 1 (mean z 5.5) and bin (1, 1) rows 2
        and 3 (mean z 7.5).

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([1.0, 2, 3, 4], index=REPEATED, name="x")
        z = pd.Series([5.0, 6, 7, 8], index=REPEATED, name="z")
        agg = Hist2D(x, x.rename("y"), z=z, nbins=2).agg()
        assert agg.to_numpy() == exact([5.5, np.nan, np.nan, 7.5], nan_ok=True)

    def test_unique_labels_align_onto_repeated_ones(self):
        """z with unique labels gives each repeat of a label the same value.

        x = y = 1, 2, 3, 4 on REPEATED; z = 5, 6, 7 on UNIQUE, so rows 1 and
        2 (both 2020-01-02) get z = 6. Bin (0, 0) holds rows 0, 1: mean 5.5;
        bin (1, 1) holds rows 2, 3: z 6 and 7, mean 6.5.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([1.0, 2, 3, 4], index=REPEATED, name="x")
        z = pd.Series([5.0, 6, 7], index=UNIQUE, name="z")
        agg = Hist2D(x, x.rename("y"), z=z, nbins=2).agg()
        assert agg.to_numpy() == exact([5.5, np.nan, np.nan, 6.5], nan_ok=True)

    def test_z_with_repeated_labels_on_another_index_raises(self):
        """z repeats a label and its index differs from x's: ValueError names z.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([1.0, 2, 3], index=UNIQUE, name="x")
        z = pd.Series([5.0, 6, 7, 8], index=REPEATED, name="z")
        with pytest.raises(ValueError, match=r"\['z'\] repeat.*ambiguous"):
            Hist2D(x, x.rename("y"), z=z, nbins=2)

    @pytest.mark.parametrize(
        "build",
        [
            lambda x, y: Hist2D(x, y, nbins=2),
            lambda x, y: Hist1D(x, y=y, nbins=2),
            lambda x, y: Scatter(x, y),
        ],
        ids=["Hist2D", "Hist1D", "Scatter"],
    )
    def test_coordinates_with_repeated_labels_on_different_indexes_raise(self, build):
        """x and y both repeat labels on different indexes: ValueError names them.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([1.0, 2, 3, 4], index=REPEATED, name="x")
        other = pd.to_datetime(
            ["2020-01-01", "2020-01-02", "2020-01-02", "2020-01-03", "2020-01-05"]
        )
        y = pd.Series([1.0, 2, 3, 4, 5], index=other, name="y")
        with pytest.raises(ValueError, match=r"repeat.*ambiguous"):
            build(x, y)


class TestEdgesFromACountEncloseLargeData:
    # Each pair was found by a seeded search for data whose rounded outer edge
    # lands one float spacing inside the data: at ~4e11 and ~1e12 the spacing
    # (6e-5, 1.2e-4) exceeds 10**-5, the default precision.
    @pytest.mark.parametrize(
        "lo, hi",
        [
            (440651515598.04877, 440655054132.1329),
            (988667622348.9438, 1045034220770.2701),
        ],
        ids=["lower-edge", "upper-edge"],
    )
    def test_hist1d_counts_every_sample(self, lo, hi):
        """Three samples and nbins=2: the edges enclose them and all 3 count.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([lo, (lo + hi) / 2, hi], name="x")
        h = Hist1D(x, nbins=2)
        edges = h.edges["x"]
        assert edges[0] <= lo
        assert edges[-1] >= hi
        assert h.agg().sum() == 3


# 1, 2, inf, 4 held as Python floats in an object column.
OBJECT_WITH_INF = pd.Series([1.0, 2.0, np.inf, 4.0], dtype=object)
FLOATS = pd.Series([1.0, 2.0, 3.0, 4.0])


class TestObjectDtypeColumns:
    def test_object_z_with_inf_drops_that_row(self):
        """z = 1, 2, inf, 4 as objects: the inf row is dropped, as for floats.

        x = y = 1..4 and nbins=2 (split at 2.5): bin (0, 0) holds rows 0, 1,
        mean 1.5; bin (1, 1) holds row 3 only, z = 4.

        ON FAILURE: the code is wrong.
        """
        z = OBJECT_WITH_INF.rename("z")
        h = Hist2D(FLOATS.rename("x"), FLOATS.rename("y"), z=z, nbins=2)
        assert h.agg().to_numpy() == exact([1.5, np.nan, np.nan, 4.0], nan_ok=True)
        assert list(h.data.index) == [0, 1, 3]

    def test_object_x_with_inf_bins_by_count(self):
        """x = 1, 2, inf, 4 as objects, nbins=2: edges 1, 2.5, 4; counts 2 and 1.

        ON FAILURE: the code is wrong.
        """
        agg = Hist1D(OBJECT_WITH_INF.rename("x"), nbins=2).agg()
        assert agg.to_numpy() == exact([2, 1])

    def test_object_x_takes_log(self):
        """x = 1, 10, inf, 100 as objects with logx: log10 0, 1, 2; counts 1, 2.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([1.0, 10.0, np.inf, 100.0], dtype=object, name="x")
        agg = Hist1D(x, logx=True, nbins=2).agg()
        assert agg.to_numpy() == exact([1, 2])

    def test_scatter_data_holds_no_inf_from_an_object_column(self):
        """Scatter keeps rows 0, 1, 3 of an object x holding inf at row 2.

        ON FAILURE: the code is wrong.
        """
        data = Scatter(OBJECT_WITH_INF.rename("x"), FLOATS.rename("y")).data
        assert list(data.index) == [0, 1, 3]
        assert data.loc[:, "x"].to_numpy() == exact([1.0, 2.0, 4.0])

    def test_binned_data_logs_an_object_column(self):
        """BinnedData logs objects 1, 10, inf: log10 0, 1 in (-1, 0.5], (0.5, 2].

        inf gets code -1.

        ON FAILURE: the code is wrong.
        """
        frame = pd.DataFrame({"x": pd.Series([1.0, 10.0, np.inf], dtype=object)})
        b = BinnedData(frame, {"x": [-1, 0.5, 2]}, log={"x": True})
        assert b.codes("x").tolist() == [0, 1, -1]

    def test_non_numeric_object_column_is_left_as_given(self):
        """Strings are not numbers: Scatter keeps them as given.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series(["a", "b"], dtype=object, name="x")
        data = Scatter(x, pd.Series([1.0, 2.0], name="y")).data
        assert data.loc[:, "x"].tolist() == ["a", "b"]


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

    The finite values are 0, 1, ..., 10000 (n = 10001), so the 0.05th and
    99.95th percentiles sit at positions 5 and 9995: values 5 and 9995. NaN
    stays NaN.

    ON FAILURE: the code is wrong.
    """
    data = pd.Series(np.r_[np.arange(10001.0), INF, -INF, np.nan])
    clipped = Base.clip_data(data, True)
    assert clipped.iloc[[0, 5, 9995, 10000]].to_numpy() == exact(
        [5.0, 5.0, 9995.0, 9995.0]
    )
    assert clipped.iloc[[10001, 10002]].to_numpy() == exact([9995.0, 5.0])
    assert np.isnan(clipped.iloc[10003])


def test_an_infinite_value_no_longer_makes_the_upper_quantile_nan():
    """With 0, 1, 2, 3, 4 and +inf, the upper bound is 3.998, not NaN.

    Over the finite values (n = 5) the 99.95th percentile is at position
    0.9995 * 4 = 3.998, between 3 and 4: 3.998. Including +inf made it
    NaN, so +inf was left unclipped.

    ON FAILURE: the code is wrong.
    """
    data = pd.Series([0.0, 1.0, 2.0, 3.0, 4.0, INF])
    clipped = Base.clip_data(data, "u")
    assert clipped.to_numpy() == exact([0.0, 1.0, 2.0, 3.0, 3.998, 3.998])


@pytest.mark.parametrize(
    "clip, expected",
    [("l", [5.0, 9995.0, 5.0, INF]), ("u", [5.0, 9995.0, -INF, 9995.0])],
)
def test_one_tail_clip_leaves_the_other_infinity(clip, expected):
    """``"l"`` clips -inf only, ``"u"`` clips +inf only.

    Columns of a DataFrame are clipped one by one; column ``b`` is ``a``
    shifted by 1 (finite values 1 to 10001, quantiles 6 and 9996).

    ON FAILURE: the code is wrong.
    """
    a = np.r_[np.arange(10001.0), -INF, INF]
    frame = pd.DataFrame({"a": a, "b": a + 1.0})
    clipped = Base.clip_data(frame, clip)
    picks = [5, 9995, 10001, 10002]
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


# Three points by hand; each case replaces one data variable with a scalar.
_PT = pd.Series([1.0, 2.0, 3.0])
_SCALAR_DATA_VARIABLES = [
    pytest.param(lambda: Scatter(_PT, _PT, None, True), "size", id="Scatter-size"),
    pytest.param(lambda: Scatter(_PT, _PT, alpha=0.5), "alpha", id="Scatter-alpha"),
    pytest.param(lambda: Scatter(_PT, _PT, 2.0), "z", id="Scatter-z"),
    pytest.param(lambda: Scatter(_PT, 1.0), "y", id="Scatter-y"),
    pytest.param(lambda: Hist1D(_PT, 1.0), "y", id="Hist1D-y"),
    pytest.param(lambda: Hist2D(_PT, _PT, 2.0), "z", id="Hist2D-z"),
    pytest.param(lambda: SpiralPlot2D(_PT, _PT, 2.0), "z", id="SpiralPlot2D-z"),
]


@pytest.mark.parametrize("build, name", _SCALAR_DATA_VARIABLES)
def test_a_scalar_data_variable_raises_type_error_naming_it(build, name):
    """A data variable holds one value per point, so a scalar is refused.

    ``Scatter(x, y, None, True)`` once stored True as every point's size. A
    constant marker size or opacity has its home in ``make_plot``'s ``s`` and
    ``alpha`` keywords.

    ON FAILURE: the code is wrong; a plot accepted a scalar as a data variable.
    """
    with pytest.raises(TypeError, match=rf"\b{name}\b.*one value per point"):
        build()
