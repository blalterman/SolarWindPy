# Spent-When: PERMANENT(BinnedData is removed from solarwindpy.plotting)
# Supersedes: none
"""Contract tests for ``solarwindpy.plotting.binned.BinnedData``.

Expected bins come from hand-placed values on a fixed grid, from
``pandas.cut`` with an ``IntervalIndex`` (which bins by the intervals
themselves, not by numeric edges), and from ``numpy.histogram``, whose last
bin also holds its right edge. Edges ``0, 1, 2, 3`` give three bins.

The plot classes' side of the contract is tested here too: a plot given a
``BinnedData`` as ``nbins`` takes its bins, codes, log and clip settings by
column name, and keeps only the rows its mask keeps; every plot constructor
checks its caller ``mask`` the way ``BinnedData`` does; ``clip`` is set per
axis, read back as a ``ClipAxes``; and every plot or selection call warns, once
per outermost call, when the data it was binned from has changed.
"""

import gc
import logging

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from solarwindpy.instabilities.beta_ani import BetaRPlot  # noqa: E402
from solarwindpy.plotting.base import (  # noqa: E402
    ClipAxes,
    LogAxes,
    methods_with_role,
)
from solarwindpy.plotting.binned import BinnedData  # noqa: E402
from solarwindpy.plotting.hist1d import Hist1D  # noqa: E402
from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402
from solarwindpy.plotting.scatter import Scatter  # noqa: E402
from solarwindpy.plotting.spiral import SpiralPlot2D  # noqa: E402
from tests.tolerances import exact  # noqa: E402

EDGES = np.array([0.0, 1.0, 2.0, 3.0])

# Values on every edge, inside every bin, beyond both ends, +/-inf and NaN.
PROBE = np.array(
    [-np.inf, -1.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, np.inf, np.nan]
)
# (a, b]: an edge belongs to the bin on its left; 0 is in no bin.
RIGHT_CODES = np.array([-1, -1, -1, 0, 0, 1, 1, 2, 2, -1, -1, -1])
# [a, b), the last bin [2, 3]: an edge belongs to the bin on its right.
LEFT_CODES = np.array([-1, -1, 0, 0, 1, 1, 2, 2, 2, -1, -1, -1])


def _frame(values, index=None):
    return pd.DataFrame({"x": values}, index=index)


class TestCodes:
    """Each row's code is the position of the bin holding its value."""

    @pytest.mark.parametrize(
        "bins, expected",
        [
            (EDGES, RIGHT_CODES),
            (pd.IntervalIndex.from_breaks(EDGES, closed="right"), RIGHT_CODES),
            (pd.IntervalIndex.from_breaks(EDGES, closed="left"), LEFT_CODES),
        ],
        ids=["edges", "right-closed", "left-closed"],
    )
    def test_codes_place_edges_infinities_and_nan_by_closure(self, bins, expected):
        """Values on edges, beyond the ends, at +/-inf and NaN get the hand codes.

        ON FAILURE: the code is wrong.
        """
        b = BinnedData(_frame(PROBE), {"x": bins})
        np.testing.assert_array_equal(b.codes("x"), expected)

    def test_right_closed_categorical_equals_pandas_cut(self):
        """Right-closed bins match ``pd.cut`` by the same intervals, index and name.

        ON FAILURE: the code is wrong.
        """
        intervals = pd.IntervalIndex.from_breaks(EDGES, closed="right")
        values = pd.Series(PROBE, index=pd.RangeIndex(10, 22), name="x")
        b = BinnedData(values.to_frame(), {"x": intervals})
        expected = pd.cut(values, intervals)
        pd.testing.assert_series_equal(b.categorical("x"), expected, check_exact=True)

    def test_left_closed_categorical_is_pandas_cut_with_the_last_edge_closed(self):
        """Left-closed bins match ``pd.cut`` except that 3 joins the last bin.

        ON FAILURE: the code is wrong.
        """
        intervals = pd.IntervalIndex.from_breaks(EDGES, closed="left")
        values = pd.Series(PROBE, name="x")
        b = BinnedData(values.to_frame(), {"x": intervals})
        expected = pd.cut(values, intervals)
        expected[values == 3.0] = intervals[-1]
        pd.testing.assert_series_equal(b.categorical("x"), expected, check_exact=True)
        assert b.categorical("x")[values == 3.0].tolist() == [intervals[-1]]

    def test_left_closed_counts_equal_numpy_histogram(self):
        """Counting codes per bin reproduces ``np.histogram`` on the finite values.

        ON FAILURE: the code is wrong.
        """
        rng = np.random.default_rng(20261102)
        # Integers on and between the edges, so many values sit on an edge.
        values = np.r_[rng.integers(-1, 5, 500).astype(float), PROBE]
        b = BinnedData(
            _frame(values), {"x": pd.IntervalIndex.from_breaks(EDGES, closed="left")}
        )
        codes = b.codes("x")
        expected, _ = np.histogram(values[np.isfinite(values)], bins=EDGES)
        got = np.bincount(codes[codes >= 0], minlength=EDGES.size - 1)
        np.testing.assert_array_equal(got, expected)

    def test_log_bins_log10_of_the_absolute_value(self):
        """With ``log``, -10, 100 and 0.5 are binned at 1, 2 and -0.30.

        ON FAILURE: the code is wrong.
        """
        frame = _frame([-10.0, 100.0, 0.5])
        b = BinnedData(frame, {"x": [-1.0, 0.0, 1.0, 2.0]}, log={"x": True})
        np.testing.assert_array_equal(b.codes("x"), [1, 2, 0])
        assert b.log_of("x") is True

    @pytest.mark.parametrize(
        "clip, expected", [(False, 2), (True, 1)], ids=["unclipped", "clipped"]
    )
    def test_clip_bins_an_outlier_at_its_quantile(self, clip, expected):
        """``clip`` bins 1000 at the 99.99th percentile, 999.009, in (5, 999.5].

        x = 0..9 and 1000; numpy's linear quantile at 0.9999 is
        9 + 0.999 * 991. The two parametrizations differ only in clipping.
        ON FAILURE: the code is wrong.
        """
        values = np.r_[np.arange(10.0), 1000.0]
        b = BinnedData(
            _frame(values), {"x": [-1.0, 5.0, 999.5, 1001.0]}, clip={"x": clip}
        )
        assert b.codes("x")[-1] == expected
        assert b.clip_of("x") is clip


class TestCodeType:
    """Codes take one byte per row up to 127 bins."""

    @pytest.mark.parametrize(
        "n_bins, dtype", [(127, np.int8), (128, np.int16)], ids=["127", "128"]
    )
    def test_code_dtype_widens_above_127_bins(self, n_bins, dtype):
        """127 bins give int8 codes; 128 give int16; the top bin's code survives.

        ON FAILURE: the code is wrong.
        """
        edges = np.arange(n_bins + 1.0)
        values = np.arange(n_bins) + 0.5
        b = BinnedData(_frame(values), {"x": edges})
        codes = b.codes("x")
        assert codes.dtype == dtype
        np.testing.assert_array_equal(codes, np.arange(n_bins))

    def test_writing_into_codes_raises(self):
        """Codes and edges are read-only, whole or taken on rows.

        ON FAILURE: the code is wrong.
        """
        b = BinnedData(_frame(PROBE), {"x": EDGES})
        on = np.isfinite(PROBE)
        for arr in (b.codes("x"), b.codes("x", on=on), b.edges("x")):
            with pytest.raises(ValueError, match="read-only"):
                arr[0] = 1


class TestErrors:
    """Bad bins, columns and masks raise."""

    @pytest.mark.parametrize("spec", [10, np.int64(10), "auto", "knuth"])
    def test_bin_rules_are_refused(self, spec):
        """An integer or string bin rule raises: only explicit bins are shared.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(TypeError, match="explicit bin edges or an IntervalIndex"):
            BinnedData(_frame(PROBE), {"x": spec})

    def test_unknown_column_raises_key_error(self):
        """Binning, or asking for, a column that is not there raises KeyError.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(KeyError, match="q"):
            BinnedData(_frame(PROBE), {"q": EDGES})
        b = BinnedData(_frame(PROBE), {"x": EDGES})
        for method in (b.codes, b.categorical, b.edges, b.intervals, b.log_of):
            with pytest.raises(KeyError, match="q"):
                method("q")


class TestSnapshot:
    """A BinnedData keeps the values it was built from."""

    def test_editing_the_source_in_place_changes_nothing(self):
        """After ``frame`` is edited in place, codes, bins and index are unchanged.

        Values and labels are both edited; the frame checks prove the edits
        landed.
        ON FAILURE: the code is wrong.
        """
        frame = pd.DataFrame({"x": PROBE.copy(), "y": np.arange(PROBE.size)})
        b = BinnedData(frame, {"x": EDGES})
        frame.loc[:, "x"] = 2.5
        frame.iloc[3, 0] = np.nan
        frame.index = pd.RangeIndex(100, 100 + PROBE.size)

        assert frame["x"].isna().sum() == 1
        assert frame.index[0] == 100
        np.testing.assert_array_equal(b.codes("x"), RIGHT_CODES)
        lefts = b.categorical("x").map(lambda iv: iv.left, na_action="ignore")
        expected = np.where(RIGHT_CODES >= 0, EDGES[RIGHT_CODES], np.nan)
        np.testing.assert_array_equal(lefts.astype(float).to_numpy(), expected)
        assert b.columns == ("x",)
        assert b.index.equals(pd.RangeIndex(PROBE.size))


class TestMask:
    """A mask is aligned by label; rows it excludes get code -1."""

    def test_rows_outside_the_mask_get_code_minus_one(self):
        """Masked-out rows are -1; kept rows keep their hand codes.

        The mask's index is the frame's, reversed, so it is aligned by label.
        ON FAILURE: the code is wrong.
        """
        index = pd.Index(list("abcdefghijkl"))
        keep = np.arange(PROBE.size) % 2 == 0
        mask = pd.Series(keep, index=index)[::-1]
        b = BinnedData(_frame(PROBE, index), {"x": EDGES}, mask=mask)
        np.testing.assert_array_equal(b.codes("x"), np.where(keep, RIGHT_CODES, -1))

    def test_rows_are_taken_by_label(self):
        """``on`` takes rows by label, in the order given.

        ON FAILURE: the code is wrong.
        """
        index = pd.Index(list("abcdefghijkl"))
        b = BinnedData(_frame(PROBE, index), {"x": EDGES})
        got = b.categorical("x", on=pd.Index(["h", "d"]))
        assert got.index.tolist() == ["h", "d"]
        assert got.tolist() == [pd.Interval(2.0, 3.0), pd.Interval(0.0, 1.0)]
        with pytest.raises(ValueError, match="subset"):
            b.codes("x", on=pd.Index(["z"]))

    def test_a_mask_missing_a_label_raises(self):
        """A missing label is never read as False.

        ON FAILURE: the code is wrong.
        """
        mask = pd.Series(True, index=pd.RangeIndex(PROBE.size - 1))
        with pytest.raises(ValueError, match="lacks 1 label"):
            BinnedData(_frame(PROBE), {"x": EDGES}, mask=mask)

    @pytest.mark.parametrize("dtype", [object, "boolean"])
    def test_a_mask_holding_nan_raises(self, dtype):
        """NaN in the mask is never read as False.

        ON FAILURE: the code is wrong.
        """
        values = [True] * (PROBE.size - 1) + [None]
        mask = pd.Series(values, dtype=dtype)
        with pytest.raises(ValueError, match="NaN"):
            BinnedData(_frame(PROBE), {"x": EDGES}, mask=mask)


# ---------------------------------------------------------------------------
# Through the plots: a shared BinnedData via nbins, and the caller mask
# ---------------------------------------------------------------------------

# Six labelled points on the grid 0, 1, 2, 3 per axis. Point "f" has no x,
# so no plot keeps it. Points "a" and "e" share the bin (0, 1] x (0, 1].
LABELS = list("abcdef")
POINTS = pd.DataFrame(
    {
        "vx": [0.5, 1.5, 2.5, 0.5, 0.5, np.nan],
        "vy": [0.5, 0.5, 1.5, 2.5, 0.5, 0.5],
    },
    index=LABELS,
)
# Drops "b": the plot keeps a, c, d and e.
MASK = pd.Series([True, False, True, True, True, True], index=LABELS)
KEPT = ["a", "c", "d", "e"]
GRID = {"vx": EDGES, "vy": EDGES}


def _interval(i):
    return pd.Interval(EDGES[i], EDGES[i + 1], closed="right")


class TestSharedBinnedData:
    """A plot given ``nbins=BinnedData`` takes its bins and codes from it."""

    def test_shared_codes_are_taken_by_name_on_the_plots_rows(self):
        """Hist2D(vx, vy, nbins=b, mask=m) counts the kept points in their bins.

        a and e fall in (0, 1] x (0, 1]; c in (2, 3] x (1, 2]; d in
        (0, 1] x (2, 3]. Cut and data hold exactly the kept labels.
        ON FAILURE: the code is wrong.
        """
        b = BinnedData(POINTS, GRID)
        h = Hist2D(POINTS.vx, POINTS.vy, nbins=b, mask=MASK)
        assert h.data.index.tolist() == KEPT
        assert h.cut.index.tolist() == KEPT
        expected = pd.Series(
            [2, 1, 1],
            index=pd.MultiIndex.from_tuples(
                [
                    (_interval(0), _interval(0)),
                    (_interval(0), _interval(2)),
                    (_interval(2), _interval(1)),
                ],
                names=["x", "y"],
            ),
        )
        got = h.agg().dropna()
        assert got.index.tolist() == expected.index.tolist()
        assert got.to_numpy() == exact(expected.to_numpy(dtype=float))

    def test_rows_the_binned_data_excludes_are_not_the_plots_rows(self):
        """A row b's own mask drops is not kept: rows = notna & mask & b's mask.

        b drops "c" and the plot's mask drops "b", so the plot keeps a, d and
        e, the rows that can contribute to a bin (author's ruling).
        ON FAILURE: the code is wrong.
        """
        b_mask = pd.Series([label != "c" for label in LABELS], index=LABELS)
        b = BinnedData(POINTS, GRID, mask=b_mask)
        h = Hist2D(POINTS.vx, POINTS.vy, nbins=b, mask=MASK)
        assert h.data.index.tolist() == ["a", "d", "e"]
        assert h.cut.index.tolist() == ["a", "d", "e"]
        assert h.cut.notna().all().all()

    def test_a_subset_of_the_rows_is_taken_by_label(self):
        """x on labels e, a (a subset, reordered) gets the bins of e and a.

        ON FAILURE: the code is wrong.
        """
        b = BinnedData(POINTS, {"vx": EDGES})
        x = POINTS.vx.loc[["e", "c"]]
        h = Hist1D(x, nbins=b)
        assert h.cut.index.tolist() == ["e", "c"]
        assert h.cut.loc[:, "x"].tolist() == [_interval(0), _interval(2)]

    def test_a_name_the_binned_data_lacks_raises_key_error(self):
        """y named "q" is not a column of b: KeyError naming it.

        ON FAILURE: the code is wrong.
        """
        b = BinnedData(POINTS, GRID)
        with pytest.raises(KeyError, match="'q'"):
            Hist2D(POINTS.vx, POINTS.vy.rename("q"), nbins=b)

    def test_labels_outside_the_binned_data_raise_value_error(self):
        """x holding a label b lacks raises ValueError.

        ON FAILURE: the code is wrong.
        """
        b = BinnedData(POINTS.loc[["a", "b", "c"]], GRID)
        with pytest.raises(ValueError, match="not a subset"):
            Hist2D(POINTS.vx, POINTS.vy, nbins=b)

    @pytest.mark.parametrize("nbins", ["first", "second"])
    def test_a_binned_data_inside_a_per_axis_sequence_raises_type_error(self, nbins):
        """A BinnedData bins every axis, so (b, 5) or [5, b] is refused.

        ON FAILURE: the code is wrong.
        """
        b = BinnedData(POINTS, GRID)
        spec = (b, 5) if nbins == "first" else [5, b]
        with pytest.raises(TypeError, match="per-axis"):
            Hist2D(POINTS.vx, POINTS.vy, nbins=spec)

    @pytest.mark.parametrize("initial_bins", ["alone", "in a pair"])
    def test_spiral_refuses_a_binned_data(self, initial_bins):
        """SpiralPlot2D adapts its mesh to its data and raises TypeError.

        ON FAILURE: the code is wrong.
        """
        b = BinnedData(POINTS, GRID)
        spec = b if initial_bins == "alone" else (b, 3)
        with pytest.raises(TypeError, match="cannot use a shared BinnedData"):
            SpiralPlot2D(POINTS.vx, POINTS.vy, initial_bins=spec)

    @pytest.mark.parametrize(
        "binned_with, plot_with, match",
        [
            ({"log": {"vx": True}}, {"logx": False}, "logx=False conflicts"),
            ({}, {"logy": True}, "logy=True conflicts"),
            ({"clip": {"vy": True}}, {"clip": False}, "clip=False for y conflicts"),
            ({"clip": {"vx": "u", "vy": "u"}}, {"clip": "l"}, "clip='l' for x"),
            ({"clip": {"vy": "u"}}, {"clip": {"y": "l"}}, "clip='l' for y"),
        ],
        ids=["log in b", "log in plot", "clip in b", "other tail", "mapping"],
    )
    def test_an_explicit_log_or_clip_differing_from_the_binned_data_raises(
        self, binned_with, plot_with, match
    ):
        """An explicit logx, logy or clip must equal b's setting for its column.

        ON FAILURE: the code is wrong.
        """
        positive = POINTS.loc[KEPT]
        b = BinnedData(positive, GRID, **binned_with)
        with pytest.raises(ValueError, match=match):
            Hist2D(positive.vx, positive.vy, nbins=b, **plot_with)

    def test_betar_plot_takes_a_log_binned_data(self):
        """BetaRPlot bins log10 by default, so a log BinnedData is accepted.

        log10 of every kept value (0.5 to 2.5) lies in (-1, 1], so all four
        points are counted once BetaRPlot's default clim of 5 is cleared.
        ON FAILURE: the code is wrong.
        """
        positive = POINTS.loc[KEPT]
        log_edges = [-1.0, 0.0, 1.0]
        b = BinnedData(
            positive,
            {"vx": log_edges, "vy": log_edges},
            log={"vx": True, "vy": True},
        )
        h = BetaRPlot(positive.vx, positive.vy, "p", nbins=b)
        h.set_clim(None, None)
        assert h.agg(fcn="count").sum() == exact(4)


#: Every plot class's constructor, given x and y and a mask.
MASKED_PLOTS = {
    "Hist1D": lambda x, y, mask: Hist1D(x, y, mask=mask),
    "Hist2D": lambda x, y, mask: Hist2D(x, y, mask=mask),
    "BetaRPlot": lambda x, y, mask: BetaRPlot(x, y, "p", mask=mask),
    "Scatter": lambda x, y, mask: Scatter(x, y, mask=mask),
    "SpiralPlot2D": lambda x, y, mask: SpiralPlot2D(x, y, mask=mask),
}


class TestCallerMask:
    """Every plot constructor takes a mask aligned by label, and checks it."""

    @pytest.mark.parametrize("plot", tuple(MASKED_PLOTS))
    def test_the_mask_keeps_its_rows_under_their_labels(self, plot):
        """The mask is aligned by label: given reversed, it still drops "b".

        ON FAILURE: the code is wrong.
        """
        positive = POINTS.loc[["a", "b", "c", "d", "e"]]
        h = MASKED_PLOTS[plot](positive.vx, positive.vy, MASK[::-1])
        assert h.data.index.tolist() == KEPT

    @pytest.mark.parametrize("plot", tuple(MASKED_PLOTS))
    def test_a_mask_missing_a_label_raises(self, plot):
        """A label of x absent from the mask is never read as False.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(ValueError, match="lacks 1 label"):
            MASKED_PLOTS[plot](POINTS.vx, POINTS.vy, MASK.drop("c"))

    @pytest.mark.parametrize("plot", tuple(MASKED_PLOTS))
    def test_a_mask_holding_nan_raises(self, plot):
        """NaN in the mask is never read as False.

        ON FAILURE: the code is wrong.
        """
        mask = MASK.astype("boolean")
        mask.loc["c"] = pd.NA
        with pytest.raises(ValueError, match="NaN"):
            MASKED_PLOTS[plot](POINTS.vx, POINTS.vy, mask)

    @pytest.mark.parametrize(
        "mask",
        [MASK.astype(float), MASK.to_numpy()],
        ids=["float series", "ndarray"],
    )
    @pytest.mark.parametrize("plot", tuple(MASKED_PLOTS))
    def test_a_mask_that_is_not_a_boolean_series_raises_type_error(self, plot, mask):
        """A float Series or a bare array is refused, not converted.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(TypeError, match="mask must"):
            MASKED_PLOTS[plot](POINTS.vx, POINTS.vy, mask)


@pytest.mark.parametrize(
    "cls", [Hist1D, Hist2D, BetaRPlot, Scatter, SpiralPlot2D], ids=lambda c: c.__name__
)
def test_no_plot_class_offers_set_data(cls):
    """Data is given only to the constructor: no class has a public set_data.

    To plot other data, build a new plot.
    ON FAILURE: the code is wrong.
    """
    assert not hasattr(cls, "set_data")


# ---------------------------------------------------------------------------
# Passthrough: log and clip inherited from a shared BinnedData by column name
# ---------------------------------------------------------------------------

# The kept points, all positive, so every column can be logged. Their hand
# log10 values, on labels a, c, d, e.
POSITIVE = POINTS.loc[KEPT]
LOG10_VX = [np.log10(0.5), np.log10(2.5), np.log10(0.5), np.log10(0.5)]
LOG10_VY = [np.log10(0.5), np.log10(1.5), np.log10(2.5), np.log10(0.5)]
# Edges on log10 of the kept values, which lie in (-1, 1].
LOG_EDGES = [-1.0, 0.0, 1.0]


@pytest.fixture
def ax():
    _, axis = plt.subplots()
    yield axis
    plt.close("all")


class TestPassthrough:
    """None means inherit from a shared BinnedData; an explicit value must agree."""

    def test_log_is_inherited_per_column_by_name(self, ax):
        """b logs vy only: Hist2D(vx, vy, nbins=b) logs y, not x.

        The stored y is log10 of the hand values, x is unchanged, and
        ``make_plot`` sets a log y-axis and a linear x-axis.
        ON FAILURE: the code is wrong.
        """
        b = BinnedData(POSITIVE, {"vx": EDGES, "vy": LOG_EDGES}, log={"vy": True})
        h = Hist2D(POSITIVE.vx, POSITIVE.vy, nbins=b)
        assert h.log == LogAxes(x=False, y=True)
        assert h.data.loc[:, "y"].tolist() == exact(LOG10_VY)
        assert h.data.loc[:, "x"].tolist() == exact([0.5, 2.5, 0.5, 0.5])
        h.make_plot(ax=ax, cbar=False)
        assert (ax.get_xscale(), ax.get_yscale()) == ("linear", "log")

    def test_hist1d_inherits_the_log_of_its_column(self):
        """Hist1D(vx, nbins=b) with b logging vx stores log10 of x.

        ON FAILURE: the code is wrong.
        """
        b = BinnedData(POSITIVE, {"vx": LOG_EDGES}, log={"vx": True})
        h = Hist1D(POSITIVE.vx, nbins=b)
        assert h.log.x is True
        assert h.data.loc[:, "x"].tolist() == exact(LOG10_VX)

    def test_clip_is_inherited_per_column_by_name(self):
        """b clips vx's upper tail only: the plot's clip is ClipAxes("u", False).

        ON FAILURE: the code is wrong.
        """
        b = BinnedData(POSITIVE, GRID, clip={"vx": "u"})
        assert Hist2D(POSITIVE.vx, POSITIVE.vy, nbins=b).clip == ClipAxes(
            x="u", y=False, z=False
        )
        assert Hist1D(POSITIVE.vx, nbins=b).clip == ClipAxes(x="u", y=False, z=False)

    def test_an_explicit_value_equal_to_the_binned_datas_is_accepted(self):
        """logy=True and clip={"x": "u"} agree with b, so the plot is built.

        ON FAILURE: the code is wrong.
        """
        b = BinnedData(
            POSITIVE,
            {"vx": EDGES, "vy": LOG_EDGES},
            log={"vy": True},
            clip={"vx": "u"},
        )
        h = Hist2D(
            POSITIVE.vx, POSITIVE.vy, nbins=b, logx=False, logy=True, clip={"x": "u"}
        )
        assert h.log == LogAxes(x=False, y=True)
        assert h.clip == ClipAxes(x="u", y=False, z=False)

    @pytest.mark.parametrize("cls", [Hist1D, Hist2D], ids=lambda c: c.__name__)
    def test_bin_precision_with_a_binned_data_raises(self, cls):
        """b's edges are fixed when it is built, so bin_precision is refused.

        ON FAILURE: the code is wrong.
        """
        b = BinnedData(POSITIVE, GRID)
        args = (POSITIVE.vx,) if cls is Hist1D else (POSITIVE.vx, POSITIVE.vy)
        with pytest.raises(ValueError, match="bin_precision=2"):
            cls(*args, nbins=b, bin_precision=2)

    def test_without_a_binned_data_none_means_linear_and_unclipped(self):
        """With integer nbins, every default is today's False.

        ON FAILURE: the code is wrong.
        """
        h = Hist2D(POSITIVE.vx, POSITIVE.vy, nbins=3)
        assert h.log == LogAxes(x=False, y=False)
        assert h.clip == ClipAxes(x=False, y=False, z=False)
        assert Hist1D(POSITIVE.vx, nbins=3).log.x is False

    @pytest.mark.parametrize(
        "binned_log, expected",
        [
            (None, LogAxes(x=True, y=True)),
            ({}, LogAxes(x=False, y=False)),
            ({"vx": True}, LogAxes(x=True, y=False)),
        ],
        ids=["no BinnedData", "linear BinnedData", "vx logged"],
    )
    def test_betar_plot_logs_by_default_only_without_a_binned_data(
        self, binned_log, expected
    ):
        """BetaRPlot logs both axes by default; a BinnedData's log wins instead.

        ON FAILURE: the code is wrong.
        """
        if binned_log is None:
            nbins = 3
        else:
            bins = {
                "vx": LOG_EDGES if binned_log.get("vx") else EDGES,
                "vy": EDGES,
            }
            nbins = BinnedData(POSITIVE, bins, log=binned_log)
        h = BetaRPlot(POSITIVE.vx, POSITIVE.vy, "p", nbins=nbins)
        assert h.log == expected


class TestClipAxes:
    """``clip`` is set per axis; a record of False fields clips nothing."""

    # One low and one high outlier on each axis. Clipping to the 0.01st and
    # 99.99th percentiles moves -1000 and 1000 to about -999.1 and 999.1, from
    # an outer bin into the middle bin (-999.5, 999.5] (as in test_hist1d).
    OUTLIERS = pd.Series([-1000.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1000.0])
    OUTLIER_EDGES = np.array([-1001.0, -999.5, 999.5, 1001.0])

    def _counts(self, clip):
        """Counts per x bin and per y bin of a Hist2D of OUTLIERS on both axes."""
        h = Hist2D(
            self.OUTLIERS,
            self.OUTLIERS.copy(),
            clip=clip,
            nbins=self.OUTLIER_EDGES,
        )
        x = h.cut.loc[:, "x"].value_counts(sort=False)
        y = h.cut.loc[:, "y"].value_counts(sort=False)
        return x.tolist(), y.tolist()

    @pytest.mark.parametrize(
        "clip, expected",
        [
            (ClipAxes(False, False), ([1, 8, 1], [1, 8, 1])),
            ({"x": True}, ([0, 10, 0], [1, 8, 1])),
            ({"y": "u"}, ([1, 8, 1], [1, 9, 0])),
            (True, ([0, 10, 0], [0, 10, 0])),
        ],
        ids=["ClipAxes(False, False)", "x only", "y upper only", "scalar"],
    )
    def test_only_the_named_axes_are_clipped(self, clip, expected):
        """Each axis moves its outliers only when its own field clips.

        ``ClipAxes(False, False)`` is a truthy tuple, yet clips nothing.
        ON FAILURE: the code is wrong.
        """
        assert self._counts(clip) == expected

    def test_a_scalar_equals_the_mapping_naming_every_axis(self):
        """clip=True is clip={"x": True, "y": True}: same record, same bins.

        ON FAILURE: the code is wrong.
        """
        scalar = Hist2D(self.OUTLIERS, self.OUTLIERS, clip=True, nbins=3)
        mapping = Hist2D(
            self.OUTLIERS, self.OUTLIERS, clip={"x": True, "y": True}, nbins=3
        )
        assert scalar.clip == mapping.clip == ClipAxes(True, True, False)
        pd.testing.assert_frame_equal(scalar.cut, mapping.cut, check_exact=True)

    def test_scatter_clips_only_the_columns_it_names(self, ax):
        """Scatter(clip={"z": True}) clips the colours, not the positions.

        0..10000 with one far outlier on each end: z is clipped to numpy's
        0.01st and 99.99th percentiles; x and y are drawn as given.
        ON FAILURE: the code is wrong.
        """
        raw = np.concatenate([[-1e6], np.arange(10001.0), [1e6]])
        s = pd.Series(raw)
        Scatter(s, s, z=s, clip={"z": True}).make_plot(ax=ax, cbar=False)
        collection = ax.collections[0]
        offsets = np.asarray(collection.get_offsets())
        np.testing.assert_array_equal(offsets[:, 0], raw)
        np.testing.assert_array_equal(offsets[:, 1], raw)
        expected_z = np.clip(raw, np.quantile(raw, 1e-4), np.quantile(raw, 1 - 1e-4))
        np.testing.assert_array_equal(np.asarray(collection.get_array()), expected_z)

    @pytest.mark.parametrize(
        "clip, counts",
        [({"y": True}, [1, 99, 1]), ({"x": True}, [np.nan, 101, np.nan])],
        ids=["y only", "x only"],
    )
    def test_spiral_clips_only_the_axes_it_names(self, clip, counts):
        """Only clipping x moves the x tails into the middle cell.

        x is 1.99, 99 times 3 and 4.01 on cells [0, 2), [2, 4), [4, 6); its
        quantiles 2.0001 and 3.9999 lie in [2, 4) (worked in test_spiral). y
        is constant, so clipping y moves nothing.
        ON FAILURE: the code is wrong.
        """
        x = pd.Series([1.99] + [3.0] * 99 + [4.01])
        y = pd.Series([0.5] * 101)
        edges = (np.array([0.0, 2.0, 4.0, 6.0]), np.array([0.0, 1.0]))
        splot = SpiralPlot2D(x, y, initial_bins=edges, clip=clip)
        splot.initialize_mesh(min_per_bin=101, progress=False)
        splot.build_grouped()
        assert splot.agg().tolist() == exact(counts, nan_ok=True)

    @pytest.mark.parametrize(
        "build",
        [
            lambda: Hist1D(POSITIVE.vx, clip_data=True),
            lambda: Hist2D(POSITIVE.vx, POSITIVE.vy, clip_data=True),
            lambda: BetaRPlot(POSITIVE.vx, POSITIVE.vy, "p", clip_data=True),
            lambda: Scatter(POSITIVE.vx, POSITIVE.vy, clip_data=True),
            lambda: SpiralPlot2D(POSITIVE.vx, POSITIVE.vy, clip_data=True),
        ],
        ids=["Hist1D", "Hist2D", "BetaRPlot", "Scatter", "SpiralPlot2D"],
    )
    def test_the_old_clip_data_keyword_is_rejected(self, build):
        """The keyword is ``clip``; ``clip_data`` has no alias.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(TypeError, match="clip_data"):
            build()


class TestRowsWithASharedBinnedData:
    """Rows b's mask excludes are absent from data and every selection."""

    B_MASK = pd.Series([label != "c" for label in LABELS], index=LABELS)
    # notna drops f; b's mask drops c.
    ROWS = ["a", "b", "d", "e"]

    def _plot(self):
        b = BinnedData(POINTS, GRID, mask=self.B_MASK)
        return Hist2D(POINTS.vx, POINTS.vy, nbins=b)

    def test_data_and_cut_hold_only_rows_the_binned_data_keeps(self):
        """notna(x, y) & b's mask: a, b, d and e.

        ON FAILURE: the code is wrong.
        """
        h = self._plot()
        assert h.data.index.tolist() == self.ROWS
        assert h.cut.index.tolist() == self.ROWS

    def test_no_selection_returns_a_row_the_binned_data_excludes(self):
        """Every selection's labels are among a, b, d and e (no c).

        ``id_data_above_contour`` is left out: it raises for explicit edges
        (found defect #12, fixed in Phase D).
        ON FAILURE: the code is wrong.
        """
        h = self._plot()
        ranges = pd.DataFrame(
            {"bottom": 0.0, "top": 3.0}, index=h.agg().unstack("x").columns
        )
        subset, kept = h.get_subset_above_threshold(1)
        selected = {
            "plotted": h.get_plotted_data_boolean_series().index,
            "above": subset.index,
            "above mask": kept.index,
            "yrange": pd.Index(
                h.take_data_in_yrange_across_x(
                    ranges,
                    lambda key, expected_logx=False: (key.left, key.right),
                    lambda row, expected_logy=False: (row.bottom, row.top),
                )
            ),
            "project x": h.project_1d("x").data.index,
            "project y": h.project_1d("y").data.index,
        }
        for name, labels in selected.items():
            assert labels.tolist() == self.ROWS, name

    def test_hist1d_drops_the_rows_the_binned_data_excludes(self):
        """notna(vx) & b's mask: Hist1D drops f (NaN vx) and c, as Hist2D does.

        ON FAILURE: the code is wrong.
        """
        b = BinnedData(POINTS, GRID, mask=self.B_MASK)
        h = Hist1D(POINTS.vx, nbins=b)
        assert h.data.index.tolist() == self.ROWS


class TestIntegerInputOnALogAxis:
    """Change f: integer x or y with a log axis gives float log10 values."""

    VALUES = [1, 10, 100, 1000]
    LOG10 = [np.log10(1), np.log10(10), np.log10(100), np.log10(1000)]

    def test_hist1d_logs_integer_x(self):
        """Hist1D(int x, logx=True) stores log10 of the hand values.

        ON FAILURE: the code is wrong.
        """
        h = Hist1D(pd.Series(self.VALUES, dtype="int64"), logx=True, nbins=3)
        assert h.data.loc[:, "x"].tolist() == exact(self.LOG10)

    def test_hist2d_logs_integer_x_and_y(self):
        """Hist2D(int x, int y, logx=True, logy=True) stores log10 of both.

        ON FAILURE: the code is wrong.
        """
        v = pd.Series(self.VALUES, dtype="int64")
        h = Hist2D(v, v[::-1].reset_index(drop=True), logx=True, logy=True, nbins=3)
        assert h.data.loc[:, "x"].tolist() == exact(self.LOG10)
        assert h.data.loc[:, "y"].tolist() == exact(self.LOG10[::-1])


# The two warnings, verbatim from the author's specification. The tests match
# them by text, because `_warn_values_outside_bins` also logs at WARNING.
CHANGED = (
    "source changed since binning; plots reflect data at binning time; "
    "rebuild BinnedData to update"
)
GONE = "source frame no longer exists; cannot verify it is unchanged since binning"


def _count(caplog, message):
    """WARNING records whose text is ``message``, from any logger."""
    return sum(
        r.levelno == logging.WARNING and r.getMessage() == message
        for r in caplog.records
    )


def _source(seed=8):
    """200 rows in [1, 2): positive, so BetaRPlot's log axes take them as is."""
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {k: rng.uniform(1.0, 2.0, 200) for k in ("a", "b", "c")},
        index=pd.RangeIndex(100, 300),
    )


SHARED_EDGES = {"a": np.linspace(1.0, 2.0, 6), "b": np.linspace(1.0, 2.0, 6)}

# A plot built on a shared BinnedData: every class that accepts one.
SHARED_BUILDERS = {
    "Hist1D": lambda f, b: Hist1D(f.a, nbins=b),
    "Hist2D": lambda f, b: Hist2D(f.a, f.b, z=f.c, nbins=b),
    "BetaRPlot": lambda f, b: BetaRPlot(f.a, f.b, "p", nbins=b),
}


def _ready(plot):
    """Spiral draws only once its mesh is built and its points grouped."""
    if isinstance(plot, SpiralPlot2D):
        plot.initialize_mesh(min_per_bin=5, progress=False)
        plot.build_grouped()
    return plot


# A plot built from columns (its private BinnedData): every plot class.
PRIVATE_BUILDERS = {
    "Hist1D": lambda x, y, z: Hist1D(x, nbins=5),
    "Hist2D": lambda x, y, z: Hist2D(x, y, z=z, nbins=5),
    "BetaRPlot": lambda x, y, z: BetaRPlot(x, y, "p", nbins=5),
    "Scatter": lambda x, y, z: Scatter(x, y, z),
    "SpiralPlot2D": lambda x, y, z: _ready(SpiralPlot2D(x, y, z, initial_bins=5)),
}


def _draw(plot):
    fig, ax = plt.subplots()
    try:
        plot.make_plot(ax=ax)
    finally:
        plt.close(fig)


class TestBinnedDataSourceStatus:
    """``BinnedData.source_status`` compares the frame now with the frame binned."""

    def test_an_unedited_frame_is_unchanged(self):
        """Nothing edited since binning: ``"unchanged"``.

        ON FAILURE: the code is wrong.
        """
        f = _source()
        assert BinnedData(f, SHARED_EDGES).source_status() == "unchanged"

    @pytest.mark.parametrize(
        "edit",
        [
            lambda f: f.loc.__setitem__((150, "a"), 1.25),
            lambda f: f.__delitem__("b"),
            lambda f: setattr(f, "index", f.index + 1000),
        ],
        ids=["value", "binned column deleted", "rows relabelled"],
    )
    def test_an_in_place_edit_of_a_binned_column_is_a_change(self, edit):
        """A new value, a deleted binned column or new labels: ``"changed"``.

        ON FAILURE: the code is wrong.
        """
        f = _source()
        b = BinnedData(f, SHARED_EDGES)
        edit(f)
        assert b.source_status() == "changed"

    def test_editing_a_column_that_is_not_binned_is_no_change(self):
        """Only the binned columns are watched: editing ``c`` leaves it unchanged.

        ON FAILURE: the code is wrong.
        """
        f = _source()
        b = BinnedData(f, SHARED_EDGES)
        f.loc[150, "c"] = 1.25
        assert b.source_status() == "unchanged"

    def test_a_deleted_frame_cannot_be_verified(self):
        """Once the frame is garbage collected: ``"unverifiable"``.

        ON FAILURE: the code is wrong, unless something else now holds a
        reference to the frame (then the fixture is wrong).
        """
        f = _source()
        b = BinnedData(f, SHARED_EDGES)
        del f
        gc.collect()
        assert b.source_status() == "unverifiable"


class TestSourceChangeWarning:
    """Each outermost plot or selection call checks the plot's source once.

    With a shared ``BinnedData`` the check re-hashes the frame that object was
    built from (held by weak reference). A plot built from columns watches the
    columns it holds: pandas copies on write, so editing the caller's frame
    never reaches them, while editing a numpy array a Series wraps without a
    copy does.
    """

    @pytest.mark.parametrize("name", sorted(SHARED_BUILDERS))
    def test_a_shared_plot_warns_once_per_outermost_call_after_an_edit(
        self, name, caplog
    ):
        """Edit the frame in place after binning: two draws log two warnings.

        ON FAILURE: the code is wrong.
        """
        f = _source()
        plot = SHARED_BUILDERS[name](f, BinnedData(f, SHARED_EDGES))
        caplog.set_level(logging.WARNING, logger=plot.logger.name)
        f.loc[150, "a"] = 1.25
        _draw(plot)
        assert _count(caplog, CHANGED) == 1
        _draw(plot)
        assert _count(caplog, CHANGED) == 2

    @pytest.mark.parametrize("name", sorted(SHARED_BUILDERS))
    def test_a_shared_plot_of_an_unchanged_frame_is_silent(self, name, caplog):
        """No edit: drawing and selecting log neither warning.

        ON FAILURE: the code is wrong.
        """
        f = _source()
        plot = SHARED_BUILDERS[name](f, BinnedData(f, SHARED_EDGES))
        caplog.set_level(logging.WARNING, logger=plot.logger.name)
        _draw(plot)
        plot.get_plotted_data_boolean_series()
        assert _count(caplog, CHANGED) == 0
        assert _count(caplog, GONE) == 0

    @pytest.mark.parametrize(
        "call",
        [
            lambda h: h.make_joint_h2_h1_plot(),
            lambda h: h.project_1d("x"),
            lambda h: h.get_subset_above_threshold(1),
            lambda h: h.plot_contours(ax=plt.subplots()[1]),
        ],
        ids=["make_joint_h2_h1_plot", "project_1d", "subset", "plot_contours"],
    )
    def test_a_call_that_makes_nested_calls_warns_once(self, call, caplog):
        """Calls that call other checked methods still log exactly one warning.

        ``make_joint_h2_h1_plot`` calls ``make_plot`` and ``project_1d``,
        which calls ``get_plotted_data_boolean_series``; the ``Hist1D``
        margins it builds hold the histogram's data, unchanged.

        ON FAILURE: the code is wrong.
        """
        f = _source()
        h = Hist2D(f.a, f.b, z=f.c, nbins=BinnedData(f, SHARED_EDGES))
        caplog.set_level(logging.WARNING, logger=h.logger.name)
        f.loc[150, "b"] = 1.25
        try:
            call(h)
        finally:
            plt.close("all")
        assert _count(caplog, CHANGED) == 1

    @pytest.mark.parametrize("name", sorted(SHARED_BUILDERS))
    def test_a_shared_plot_whose_frame_is_deleted_cannot_verify(self, name, caplog):
        """``del frame; gc.collect()``: each draw logs the "cannot verify" warning.

        Only a shared ``BinnedData`` refers to a frame the caller owns; a
        plot built from columns watches a frame it holds itself.

        ON FAILURE: the code is wrong, unless something else now holds a
        reference to the frame (then the fixture is wrong).
        """
        f = _source()
        plot = SHARED_BUILDERS[name](f, BinnedData(f, SHARED_EDGES))
        caplog.set_level(logging.WARNING, logger=plot.logger.name)
        del f
        gc.collect()
        _draw(plot)
        assert _count(caplog, GONE) == 1
        assert _count(caplog, CHANGED) == 0

    @pytest.mark.parametrize("name", sorted(PRIVATE_BUILDERS))
    def test_a_plot_from_columns_ignores_edits_to_the_callers_frame(self, name, caplog):
        """Pandas copies on write: the plot keeps the values it was built from.

        So the check passes and logs nothing; ``data`` still holds the old
        value at the edited label.

        ON FAILURE: the code is wrong.
        """
        f = _source()
        plot = PRIVATE_BUILDERS[name](f.a, f.b, f.c)
        before = plot.data.loc[150, "x"]
        caplog.set_level(logging.WARNING, logger=plot.logger.name)
        f.loc[150, "a"] = 1.25
        _draw(plot)
        assert _count(caplog, CHANGED) == 0
        assert _count(caplog, GONE) == 0
        assert plot.data.loc[150, "x"] == exact(before)

    @pytest.mark.parametrize("name", sorted(PRIVATE_BUILDERS))
    def test_a_plot_from_columns_warns_when_their_array_is_edited(self, name, caplog):
        """x wraps a numpy array without a copy; editing the array is a change.

        One warning per outermost call: two draws, two warnings.

        ON FAILURE: the code is wrong.
        """
        f = _source()
        a = f.a.to_numpy(copy=True)
        x = pd.Series(a, index=f.index, name="a", copy=False)
        plot = PRIVATE_BUILDERS[name](x, f.b, f.c)
        caplog.set_level(logging.WARNING, logger=plot.logger.name)
        _draw(plot)
        assert _count(caplog, CHANGED) == 0
        a[50] = 1.25
        _draw(plot)
        _draw(plot)
        assert _count(caplog, CHANGED) == 2


ROLES = {
    "Hist1D": (
        {"make_plot"},
        {
            "construct_cdf",
            "get_plotted_data_boolean_series",
            "get_subset_above_threshold",
            "take_data_in_yrange_across_x",
        },
    ),
    "Hist2D": (
        {
            "make_joint_h2_h1_plot",
            "make_plot",
            "plot_contours",
            "plot_edges",
            "plot_hist_with_contours",
        },
        {
            "get_plotted_data_boolean_series",
            "get_subset_above_threshold",
            "id_data_above_contour",
            "project_1d",
            "take_data_in_yrange_across_x",
        },
    ),
    "Scatter": ({"make_plot"}, set()),
    "SpiralPlot2D": ({"make_plot", "plot_contours"}, set()),
}
ROLES["BetaRPlot"] = ROLES["Hist2D"]
CLASSES = {c.__name__: c for c in (Hist1D, Hist2D, BetaRPlot, Scatter, SpiralPlot2D)}


class TestMethodsWithRole:
    """``methods_with_role`` lists each class's checked methods by role."""

    @pytest.mark.parametrize("name", sorted(ROLES))
    def test_each_class_has_the_plot_and_selection_methods_listed(self, name):
        """The sets equal the author's role assignment, inherited methods included.

        ON FAILURE: the code is wrong, unless the author changed a role
        assignment; then update ROLES.
        """
        plot, selection = ROLES[name]
        assert methods_with_role(CLASSES[name], "plot") == plot
        assert methods_with_role(CLASSES[name], "selection") == selection

    def test_an_unknown_role_raises_value_error(self):
        """Roles are "plot" and "selection" only.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(ValueError, match="role must be one of"):
            methods_with_role(Hist2D, "draw")
